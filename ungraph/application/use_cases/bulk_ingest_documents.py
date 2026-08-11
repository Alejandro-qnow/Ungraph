"""
Bulk document ingestion with bounded concurrency, duplicate guard and catalog merge.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ungraph.application.use_cases.ingest_document import IngestDocumentUseCase
from ungraph.core.configuration import Settings, get_settings
from ungraph.domain.repositories.catalog_repository import (
    BibliographicArticleRecord,
    CatalogRepository,
)
from ungraph.domain.services.duplicate_guard_service import DuplicateGuardService
from ungraph.domain.value_objects.deduplication import normalize_doi

logger = logging.getLogger(__name__)


class BulkIngestDocumentsUseCase:
    """
    ``worker`` = un archivo: duplicate_guard → ingest → catálogo.
    """

    def __init__(
        self,
        ingest_document_use_case: IngestDocumentUseCase,
        duplicate_guard: DuplicateGuardService,
        catalog_repository: CatalogRepository,
        *,
        settings: Optional[Settings] = None,
    ):
        self._ingest = ingest_document_use_case
        self._guard = duplicate_guard
        self._catalog = catalog_repository
        self._settings = settings or get_settings()

    def execute(
        self,
        paths: List[Path],
        *,
        per_file_kwargs: Optional[Dict[Path, Dict[str, Any]]] = None,
        use_tqdm_progress: bool = False,
        **execute_kwargs: Any,
    ) -> List[Tuple[Path, str, Optional[str]]]:
        """
        Returns list of tuples ``(path, status, detail)`` where status is ``ok`` | ``skipped`` | ``error``.
        """
        per_file_kwargs = per_file_kwargs or {}
        holder_base = uuid.uuid4().hex[:12]
        max_workers = getattr(self._settings, "ingest_max_workers", 4)

        def _run_one(ix: int, file_path: Path) -> Tuple[Path, str, Optional[str]]:
            meta = dict(per_file_kwargs.get(file_path, {}))
            doi = meta.pop("doi", None)
            external_id = meta.pop("external_id", None)
            abstract_text = meta.pop("abstract_text", None)
            embedded_meta = meta.pop("embedded_metadata", None)
            title_catalog = meta.pop("title", None)
            n_doi = normalize_doi(doi)
            if n_doi and not self._catalog.try_claim_ingest(n_doi, f"bulk-{holder_base}-{ix}"):
                return (file_path, "skipped", "claim_not_acquired_same_doi")
            chk = self._guard.evaluate(
                file_path,
                doi=n_doi or doi,
                external_id=external_id,
                abstract_text=abstract_text,
                embedded_metadata=embedded_meta,
            )
            if chk.should_skip_ingest:
                return (file_path, "skipped", chk.reason)

            uid = meta.pop("source_document_uid", None) or str(uuid.uuid4())
            try:
                chunks = self._ingest.execute(
                    file_path,
                    source_document_uid=uid,
                    doi=n_doi or doi,
                    external_id=str(external_id) if external_id is not None else None,
                    abstract_text=abstract_text,
                    embedded_file_metadata_snapshot=embedded_meta,
                    persist_catalog_snapshot=False,
                    **execute_kwargs,
                    **meta,
                )
                digest = chk.source_sha256
                snapshot = (
                    json.dumps(embedded_meta, sort_keys=True, ensure_ascii=False, default=str)
                    if embedded_meta
                    else None
                )
                abs_emb = None
                embed_model = None
                if abstract_text and self._ingest.embedding_service is not None:
                    try:
                        vo = self._ingest.embedding_service.generate_embedding(abstract_text)
                        abs_emb = vo.vector
                        embed_model = vo.encoder_info
                    except Exception as ex_emb:
                        logger.debug("Bulk catalog abstract_embedding skipped: %s", ex_emb)

                stat = Path(file_path).stat()
                row = BibliographicArticleRecord(
                    document_uid=uid,
                    doi_norm=n_doi,
                    external_id=str(external_id) if external_id is not None else None,
                    title=title_catalog,
                    abstract_text=abstract_text,
                    abstract_embedding=abs_emb,
                    embedding_model=embed_model,
                    canonical_filename=file_path.name,
                    source_sha256=digest,
                    source_size_bytes=stat.st_size,
                    embedded_file_metadata_snapshot=snapshot,
                    ingested_at=None,
                )
                self._catalog.merge_article(row)
                logger.info(
                    "Bulk ingest ok %s chunks=%s doc_uid=%s", file_path, len(chunks), uid
                )
                return (file_path, "ok", uid)
            except Exception as exc:
                logger.exception("Bulk ingest failed for %s: %s", file_path, exc)
                return (file_path, "error", str(exc))

        outcomes: List[Tuple[Path, str, Optional[str]]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            futs = {pool.submit(_run_one, i, p): p for i, p in enumerate(paths)}
            iterator: Any = concurrent.futures.as_completed(futs)
            if use_tqdm_progress:
                try:
                    from tqdm import tqdm

                    iterator = tqdm(
                        iterator,
                        total=len(futs),
                        desc="Ingesta masiva",
                        unit="archivo",
                    )
                except ImportError:
                    pass
            for fut in iterator:
                outcomes.append(fut.result())
        return outcomes

    def close(self) -> None:
        """Cierra driver/sesiones del repositorio de ingesta subyacente."""
        ing = self._ingest
        if hasattr(ing.chunk_repository, "close"):
            ing.chunk_repository.close()
        if hasattr(ing.index_service, "close"):
            ing.index_service.close()
