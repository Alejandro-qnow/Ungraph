"""Multi-strategy duplicate guard executed before ingestion."""

from __future__ import annotations

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, Optional

from ungraph.domain.repositories.catalog_repository import CatalogRepository
from ungraph.domain.services.embedding_service import EmbeddingService
from ungraph.domain.value_objects.deduplication import DuplicateCheckResult, normalize_doi

logger = logging.getLogger(__name__)


def _cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class DuplicateGuardService:
    """
    Applies cheap filesystem / identity signals first, optional semantic similarity last.
    """

    def __init__(
        self,
        catalog_repository: CatalogRepository,
        *,
        semantic_similarity_threshold: float = 0.995,
        abstract_min_chars: int = 80,
        embedding_service: EmbeddingService | None = None,
    ):
        self._catalog = catalog_repository
        self._semantic_thr = semantic_similarity_threshold
        self._abstract_min = abstract_min_chars
        self._embedding = embedding_service

    def evaluate(
        self,
        file_path: Path,
        *,
        doi: Optional[str] = None,
        external_id: Optional[str] = None,
        abstract_text: Optional[str] = None,
        embedded_metadata: Optional[Dict[str, Any]] = None,
        compare_size_bytes_to_catalog: Optional[int] = None,
    ) -> DuplicateCheckResult:
        """
        Decide whether ingestion should skip as a duplicate.

        ``embedded_metadata``: dict extracted from PDF binary (Info/XMP); normalized to JSON snapshot.
        ``compare_size_bytes_to_catalog``: reserved for cohort comparisons.
        """
        data = file_path.read_bytes()
        sha_hex = hashlib.sha256(data).hexdigest()

        if self._catalog.exists_with_sha256(sha_hex):
            return DuplicateCheckResult(True, "catalog_sha256_match", sha_hex)

        n_doi = normalize_doi(doi)
        if n_doi and self._catalog.exists_with_doi_norm(n_doi):
            return DuplicateCheckResult(True, "catalog_doi_match", sha_hex)

        if external_id and self._catalog.exists_with_external_id(str(external_id)):
            return DuplicateCheckResult(True, "catalog_external_id_match", sha_hex)

        if embedded_metadata:
            _ = json.dumps(embedded_metadata, sort_keys=True, ensure_ascii=False, default=str)

        if abstract_text and len(abstract_text.strip()) >= self._abstract_min and self._embedding:
            emb = self._embedding.generate_embedding(abstract_text).vector
            best = -1.0
            rows = self._catalog.list_abstract_embedding_rows(limit=512)
            for _uid, ref_vec in rows:
                best = max(best, _cosine_sim(emb, ref_vec))
            if best >= self._semantic_thr:
                logger.info(
                    "DuplicateGuard semantic skip (best cosine=%s >= %s)",
                    best,
                    self._semantic_thr,
                )
                return DuplicateCheckResult(True, "abstract_semantic_match", sha_hex)

        if compare_size_bytes_to_catalog is not None:
            logger.debug(
                "Size narrowing placeholder: caller bytes=%s",
                compare_size_bytes_to_catalog,
            )

        return DuplicateCheckResult(False, "proceed", sha_hex)
