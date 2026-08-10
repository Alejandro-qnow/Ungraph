"""
Thin retrieval-eval layer over :class:`~ungraph.domain.services.search_service.SearchService`.

Install DeepEval for scored metrics: ``pip install 'ungraph[eval]'``.
LLM-based metrics need an API key configured for DeepEval (see its docs).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from ungraph.domain.services.embedding_service import EmbeddingService
from ungraph.domain.services.search_service import SearchResult, SearchService


def search_results_to_contexts(results: List[SearchResult]) -> List[str]:
    """Plain text contexts from search hits (chunk body only)."""
    out: List[str] = []
    for r in results:
        if r.content and str(r.content).strip():
            out.append(str(r.content))
    return out


def retrieve_text_contexts(
    search: SearchService,
    query: str,
    *,
    limit: int = 5,
) -> List[str]:
    return search_results_to_contexts(search.text_search(query, limit=limit))


def retrieve_vector_contexts(
    search: SearchService,
    embedding_service: EmbeddingService,
    query: str,
    *,
    limit: int = 5,
) -> List[str]:
    emb = embedding_service.generate_embedding(query)
    return search_results_to_contexts(search.vector_search(emb, limit=limit))


def retrieve_hybrid_contexts(
    search: SearchService,
    embedding_service: EmbeddingService,
    query: str,
    *,
    limit: int = 5,
    weights: Tuple[float, float] = (0.3, 0.7),
) -> List[str]:
    emb = embedding_service.generate_embedding(query)
    return search_results_to_contexts(
        search.hybrid_search(query, emb, weights=weights, limit=limit)
    )


def evaluate_retrieval_with_deepeval(
    *,
    query: str,
    retrieval_contexts: Sequence[str],
    expected_output: Optional[str] = None,
    actual_output: Optional[str] = None,
    include_precision_recall: bool = False,
    relevancy_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Run DeepEval contextual metrics on retrieved strings.

    Requires ``deepeval`` (``ungraph[eval]``). Precision/recall need ``expected_output``.
    """
    try:
        from deepeval.metrics import (
            ContextualPrecisionMetric,
            ContextualRecallMetric,
            ContextualRelevancyMetric,
        )
        from deepeval.test_case import LLMTestCase
    except ImportError as e:
        raise ImportError(
            "DeepEval is not installed. Install with: pip install 'ungraph[eval]'"
        ) from e

    tc = LLMTestCase(
        input=query,
        actual_output=actual_output or "(retrieval-only; no LLM answer)",
        expected_output=expected_output,
        retrieval_context=list(retrieval_contexts),
    )
    out: Dict[str, Any] = {}
    rel = ContextualRelevancyMetric(threshold=relevancy_threshold)
    rel.measure(tc)
    out["contextual_relevancy"] = {
        "score": rel.score,
        "reason": getattr(rel, "reason", None),
        "success": getattr(rel, "success", None),
    }
    if include_precision_recall and expected_output:
        prec = ContextualPrecisionMetric(threshold=relevancy_threshold)
        rec = ContextualRecallMetric(threshold=relevancy_threshold)
        prec.measure(tc)
        rec.measure(tc)
        out["contextual_precision"] = {"score": prec.score, "reason": getattr(prec, "reason", None)}
        out["contextual_recall"] = {"score": rec.score, "reason": getattr(rec, "reason", None)}
    return out
