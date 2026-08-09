"""Re-ejecutar inferencia (facts) sobre chunks que aún no tienen :Fact derivados."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from ungraph.domain.repositories.chunk_repository import ChunkRepository
from ungraph.domain.services.index_service import IndexService
from ungraph.domain.services.inference_service import InferenceService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class KnowledgeMiningResult:
    chunks_pending: int
    chunks_inferred: int
    facts_persisted: int
    relations_persisted: int
    errors: int


class KnowledgeMiningUseCase:
    """
    Minado de conocimiento sobre el grafo: chunks sin ``(:Fact)-[:DERIVED_FROM]->(:Chunk)``.
    """

    def __init__(
        self,
        chunk_repository: ChunkRepository,
        inference_service: InferenceService,
        *,
        index_service: Optional[IndexService] = None,
    ) -> None:
        self._repo = chunk_repository
        self._inference = inference_service
        self._index = index_service

    def execute(self, *, use_tqdm: bool = True) -> KnowledgeMiningResult:
        ids = self._repo.list_chunk_ids_without_derived_facts()
        facts_total = 0
        relations_total = 0
        errors = 0
        inferred = 0
        iterator: Any = ids
        if use_tqdm:
            try:
                from tqdm.auto import tqdm

                iterator = tqdm(ids, desc="kmining", unit="chunk")
            except ImportError:
                pass
        for cid in iterator:
            chunk = self._repo.find_by_id(cid)
            if not chunk or not (chunk.page_content or "").strip():
                continue
            try:
                entities = self._inference.extract_entities(chunk)
                rels = self._inference.extract_relations(chunk, entities)
                facts = self._inference.infer_facts(chunk, entities=entities)
                if facts:
                    self._repo.save_facts(facts)
                    facts_total += len(facts)
                if rels:
                    self._repo.save_relations(rels)
                    relations_total += len(rels)
                inferred += 1
            except Exception as e:
                logger.warning("Knowledge mining failed for chunk %s: %s", cid, e)
                errors += 1
        if self._index is not None:
            self._index.setup_all_indexes()
        return KnowledgeMiningResult(
            chunks_pending=len(ids),
            chunks_inferred=inferred,
            facts_persisted=facts_total,
            relations_persisted=relations_total,
            errors=errors,
        )

    def close(self) -> None:
        if hasattr(self._repo, "close"):
            self._repo.close()  # type: ignore[misc]
        if self._index is not None and hasattr(self._index, "close"):
            self._index.close()  # type: ignore[misc]
