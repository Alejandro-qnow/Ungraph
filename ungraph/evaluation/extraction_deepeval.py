"""
Métricas DeepEval sobre extracciones vs. texto fuente (context awareness / relevancia).

Usa ``ContextualRelevancyMetric``: evalúa si el contexto de recuperación (aquí, el chunk)
es relevante respecto a la pregunta formulada sobre cada entidad candidata.

Requiere ``pip install 'ungraph[eval]'`` y variables de entorno que DeepEval use para
su juez LLM (p. ej. OPENAI_API_KEY) según su documentación.

Si DeepEval no está instalado o la medición falla, se devuelve un dict con
``available: false`` sin romper el benchmark.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Sequence

from ungraph.domain.entities.entity import Entity

logger = logging.getLogger(__name__)


def try_score_extractions_contextual_relevancy(
    *,
    chunk_text: str,
    entities: Sequence[Entity],
    relevancy_threshold: float = 0.5,
    max_entities: int = 40,
) -> dict[str, Any]:
    """
    Para cada entidad extraída, puntuación contextual de apoyo en el pasaje.

    Returns:
        Dict con ``available``, ``mean_score`` (si hay éxitos), ``per_entity`` (muestra),
        y metadatos de error si aplica.
    """
    text = (chunk_text or "").strip()
    if not text:
        return {
            "available": True,
            "metric": "contextual_relevancy",
            "skipped": True,
            "reason": "empty_chunk",
        }
    if not entities:
        return {
            "available": True,
            "metric": "contextual_relevancy",
            "skipped": True,
            "reason": "no_entities",
        }

    try:
        from deepeval.metrics import ContextualRelevancyMetric
        from deepeval.test_case import LLMTestCase
    except ImportError as e:
        return {
            "available": False,
            "metric": "contextual_relevancy",
            "reason": f"deepeval not installed: {e}",
        }

    per_entity: list[dict[str, Any]] = []
    scores_ok: list[float] = []
    cap = min(len(entities), max_entities)

    for e in entities[:cap]:
        inp = (
            f'Named entity candidate: "{e.name}" with type {e.type}. '
            f"Assess whether the source passage supports this extraction."
        )
        tc = LLMTestCase(
            input=inp,
            actual_output="Candidate entity for the knowledge graph.",
            retrieval_context=[text],
        )
        m = ContextualRelevancyMetric(threshold=relevancy_threshold)
        row: dict[str, Any] = {"name": e.name, "type": e.type}
        try:
            m.measure(tc)
            sc = m.score
            row["score"] = float(sc) if sc is not None else None
            row["success"] = getattr(m, "success", None)
            if row["score"] is not None:
                scores_ok.append(row["score"])
        except Exception as exc:  # noqa: BLE001
            logger.debug("DeepEval relevancy failed for %s: %s", e.name, exc)
            row["score"] = None
            row["error"] = str(exc)
        per_entity.append(row)

    out: dict[str, Any] = {
        "available": True,
        "metric": "contextual_relevancy",
        "entities_scored": len(per_entity),
        "per_entity": per_entity,
    }
    if scores_ok:
        out["mean_score"] = round(sum(scores_ok) / len(scores_ok), 4)
        out["min_score"] = round(min(scores_ok), 4)
        out["max_score"] = round(max(scores_ok), 4)
    else:
        out["mean_score"] = None
        out["note"] = "No successful scores (check DeepEval / API configuration)."
    return out
