"""
Benchmark: spaCy NER vs LLM (LangGraph + LLMGraphTransformer) on the same chunks.

No escribe en Neo4j; sirve para medir cobertura, solapamiento y recall frente a un
gold liviano (JSON). Ver ``scripts/run_reference_pipeline.py``.
"""

from __future__ import annotations

import os
import json
import logging
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ungraph.application.dependencies import create_inference_service
from ungraph.core.configuration import Settings
from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.entities.document import Document
from ungraph.domain.entities.entity import Entity
from ungraph.domain.entities.relation import Relation
from ungraph.domain.services.inference_service import InferenceService
from ungraph.evaluation.extraction_deepeval import (
    try_score_extractions_contextual_relevancy,
)
from ungraph.infrastructure.services.langchain_chunking_service import (
    LangChainChunkingService,
)

logger = logging.getLogger(__name__)


def _benchmark_deepeval_enabled() -> bool:
    v = os.environ.get("UNGRAPH_BENCHMARK_DEEPEVAL", "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _aggregate_chunk_relevancy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Resume N llamadas por chunk a ContextualRelevancy (DeepEval)."""
    if not rows:
        return {"available": False, "metric": "contextual_relevancy", "reason": "no_rows"}
    unavailable = [r for r in rows if r.get("available") is False]
    if unavailable and all(r.get("available") is False for r in rows):
        return {
            "available": False,
            "metric": "contextual_relevancy",
            "reason": unavailable[0].get("reason", "deepeval_unavailable"),
        }
    means: list[float] = []
    chunks_scored = 0
    per_chunk_summary: list[dict[str, Any]] = []
    for r in rows:
        if r.get("skipped"):
            per_chunk_summary.append(
                {"chunk_index": len(per_chunk_summary), "skipped": True, "reason": r.get("reason")}
            )
            continue
        m = r.get("mean_score")
        if m is not None:
            means.append(float(m))
            chunks_scored += 1
        per_chunk_summary.append(
            {
                "chunk_index": len(per_chunk_summary),
                "mean_score": m,
                "entities_scored": r.get("entities_scored"),
            }
        )
    out: dict[str, Any] = {
        "available": True,
        "metric": "contextual_relevancy",
        "chunks_with_metric": len(rows),
        "chunks_with_mean_score": chunks_scored,
        "per_chunk": per_chunk_summary[:24],
    }
    if means:
        out["mean_score_across_chunks"] = round(sum(means) / len(means), 4)
        out["min_chunk_mean"] = round(min(means), 4)
        out["max_chunk_mean"] = round(max(means), 4)
    else:
        out["mean_score_across_chunks"] = None
        out["note"] = (
            "No chunk-level mean scores (install ungraph[eval], API keys, or non-empty entities)."
        )
    return out


def normalize_label(name: str) -> str:
    s = (name or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def names_align(a: str, b: str, *, min_sub: int = 4) -> bool:
    """Equality or loose containment for human / NER span mismatch."""
    na, nb = normalize_label(a), normalize_label(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    if len(na) >= min_sub and (na in nb or nb in na):
        return True
    return False


def gold_entity_recall(gold_entities: list[str], extracted: list[Entity]) -> float:
    if not gold_entities:
        return 1.0
    hits = 0
    for g in gold_entities:
        if any(names_align(g, e.name) for e in extracted if e.name):
            hits += 1
    return hits / len(gold_entities)


def _relation_endpoints(rel: Relation, entities: list[Entity]) -> tuple[str, str]:
    id_to_name = {e.id: e.name for e in entities}
    s = rel.source_entity_name or id_to_name.get(rel.source_entity_id, "")
    t = rel.target_entity_name or id_to_name.get(rel.target_entity_id, "")
    return s, t


def gold_relation_pair_recall(
    gold_pairs: list[dict[str, str]],
    relations: list[Relation],
    entities: list[Entity],
) -> float:
    """
    Undirected pair match on subject/object (predicate_hint in gold is informational).
    """
    if not gold_pairs:
        return 1.0

    hits = 0
    for row in gold_pairs:
        gs, go = row.get("subject", ""), row.get("object", "")
        if not gs or not go:
            continue
        matched = any(
            (names_align(gs, a) and names_align(go, b))
            or (names_align(gs, b) and names_align(go, a))
            for a, b in (_relation_endpoints(rel, entities) for rel in relations)
            if a and b
        )
        if matched:
            hits += 1
    return hits / len(gold_pairs)


def entity_name_jaccard(a: list[Entity], b: list[Entity]) -> float:
    sa = {normalize_label(e.name) for e in a if e.name}
    sb = {normalize_label(e.name) for e in b if e.name}
    if not sa and not sb:
        return 1.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


@dataclass
class InferenceMethodSnapshot:
    method: str
    seconds: float
    chunks_processed: int
    entities: list[Entity] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    errors: int = 0
    deepeval_relevancy: Optional[dict[str, Any]] = field(default=None, repr=False)

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def relation_count(self) -> int:
        return len(self.relations)

    def unique_entity_names(self) -> int:
        return len({normalize_label(e.name) for e in self.entities if e.name})

    def to_json_safe(self) -> dict[str, Any]:
        out = {
            "method": self.method,
            "seconds": round(self.seconds, 3),
            "chunks_processed": self.chunks_processed,
            "entity_count": self.entity_count,
            "relation_count": self.relation_count,
            "unique_entity_names": self.unique_entity_names(),
            "errors": self.errors,
            "entity_names_sample": sorted(
                {e.name for e in self.entities if e.name}
            )[:80],
        }
        if self.deepeval_relevancy is not None:
            out["deepeval_contextual_relevancy"] = self.deepeval_relevancy
        return out


def chunks_from_reference_file(
    path: Path,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    text = path.read_text(encoding="utf-8")
    doc = Document.create(
        content=text,
        filename=path.name,
        file_type="txt",
        metadata={"source": "reference_benchmark"},
    )
    splitter = LangChainChunkingService()
    return splitter.chunk(doc, chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def run_service_on_chunks(
    service: InferenceService,
    chunks: list[Chunk],
    *,
    method_label: str,
    run_deepeval_relevancy: bool = True,
) -> InferenceMethodSnapshot:
    entities_acc: list[Entity] = []
    relations_acc: list[Relation] = []
    errors = 0
    relevancy_rows: list[dict[str, Any]] = []
    t0 = time.perf_counter()
    processed = 0
    for ch in chunks:
        if not (ch.page_content or "").strip():
            continue
        try:
            ent = service.extract_entities(ch)
            if run_deepeval_relevancy and _benchmark_deepeval_enabled():
                relevancy_rows.append(
                    try_score_extractions_contextual_relevancy(
                        chunk_text=ch.page_content or "",
                        entities=ent,
                    )
                )
            rel = service.extract_relations(ch, ent)
            entities_acc.extend(ent)
            relations_acc.extend(rel)
            processed += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("[%s] chunk %s failed: %s", method_label, ch.id, exc)
            errors += 1
    elapsed = time.perf_counter() - t0
    deepeval_summary: Optional[dict[str, Any]] = None
    if run_deepeval_relevancy and _benchmark_deepeval_enabled() and relevancy_rows:
        deepeval_summary = _aggregate_chunk_relevancy(relevancy_rows)
    elif run_deepeval_relevancy and not _benchmark_deepeval_enabled():
        deepeval_summary = {
            "available": False,
            "metric": "contextual_relevancy",
            "skipped": True,
            "reason": "UNGRAPH_BENCHMARK_DEEPEVAL disabled",
        }
    return InferenceMethodSnapshot(
        method=method_label,
        seconds=elapsed,
        chunks_processed=processed,
        entities=entities_acc,
        relations=relations_acc,
        errors=errors,
        deepeval_relevancy=deepeval_summary,
    )


def load_gold_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_benchmark_report(
    *,
    ner: InferenceMethodSnapshot,
    llm: Optional[InferenceMethodSnapshot],
    gold: Optional[dict[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ner": ner.to_json_safe(),
        "llm": llm.to_json_safe() if llm else None,
        "comparison": {},
        "gold_metrics": {},
    }
    if llm is not None:
        out["comparison"] = {
            "entity_jaccard_normalized": round(
                entity_name_jaccard(ner.entities, llm.entities), 4
            ),
            "delta_unique_entities": llm.unique_entity_names()
            - ner.unique_entity_names(),
            "delta_relations": llm.relation_count - ner.relation_count,
            "delta_seconds": round(llm.seconds - ner.seconds, 3),
        }
    if gold:
        ge = gold.get("entities") or []
        grp = gold.get("relation_pairs") or []
        out["gold_metrics"]["ner"] = {
            "entity_recall": round(gold_entity_recall(ge, ner.entities), 4),
            "relation_pair_recall": round(
                gold_relation_pair_recall(grp, ner.relations, ner.entities), 4
            ),
        }
        if llm is not None:
            out["gold_metrics"]["llm"] = {
                "entity_recall": round(gold_entity_recall(ge, llm.entities), 4),
                "relation_pair_recall": round(
                    gold_relation_pair_recall(grp, llm.relations, llm.entities), 4
                ),
            }
    return out


def run_dual_inference_benchmark(
    *,
    corpus_path: Path,
    gold_path: Optional[Path],
    chunk_size: int,
    chunk_overlap: int,
    language: str,
    base_settings: Optional[Settings] = None,
) -> dict[str, Any]:
    """
    Ejecuta spaCy y (si hay API key) LLM sobre el mismo texto troceado.
    """
    chunks = chunks_from_reference_file(
        corpus_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    base = base_settings or Settings()

    ner_settings = base.model_copy(update={"inference_mode": "ner"})
    ner_svc = create_inference_service(ner_settings, language=language)
    if ner_svc is None:
        raise RuntimeError(
            "create_inference_service(ner) returned None — install spaCy model "
            "and ungraph[infer]."
        )
    ner_snap = run_service_on_chunks(ner_svc, chunks, method_label="ner")

    llm_snap: Optional[InferenceMethodSnapshot] = None
    if base.openai_api_key and str(base.openai_api_key).strip():
        llm_settings = base.model_copy(update={"inference_mode": "llm"})
        llm_svc = create_inference_service(llm_settings, language=language)
        if llm_svc is not None:
            llm_snap = run_service_on_chunks(llm_svc, chunks, method_label="llm+langgraph")
        else:
            logger.warning("LLM inference service unavailable (dependencies/config).")
    else:
        logger.info("Skipping LLM benchmark: no OPENAI / UNGRAPH_OPENAI_API_KEY set.")

    gold: Optional[dict[str, Any]] = None
    if gold_path and gold_path.is_file():
        gold = load_gold_json(gold_path)

    report = build_benchmark_report(ner=ner_snap, llm=llm_snap, gold=gold)
    report["meta"] = {
        "corpus": str(corpus_path),
        "gold": str(gold_path) if gold_path else None,
        "chunks": len(chunks),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "language": language,
        "notes": (
            "Entity/recall scores are indicative only (weak gold). "
            "LLM path uses LangGraph extraction; spaCy relations are mostly CO_OCCURS_WITH. "
            "DeepEval contextual relevancy runs per chunk unless UNGRAPH_BENCHMARK_DEEPEVAL=0."
        ),
    }
    return report
