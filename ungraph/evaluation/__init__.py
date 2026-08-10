"""Evaluation helpers: retrieval metrics (DeepEval optional) + nivel C experiment artifacts.

Carga perezosa (PEP 562): importar un submódulo concreto —p. ej.
``ungraph.evaluation.graph_structural_stats``, que consume la capa de razonamiento— no
arrastra el stack de evaluación (DeepEval, benchmarks). Los símbolos del paquete se
resuelven bajo demanda al accederlos.
"""

from __future__ import annotations

import importlib
from typing import Any

# símbolo -> submódulo que lo define
_EXPORTS = {
    "ExperimentRun": "experiment_run",
    "rank_experiment_runs_by_relevancy": "experiment_run",
    "GraphStructuralStats": "graph_structural_stats",
    "collect_structural_graph_stats": "graph_structural_stats",
    "collect_structural_graph_stats_from_settings": "graph_structural_stats",
    "diff_structural_stats": "graph_structural_stats",
    "evaluate_retrieval_with_deepeval": "retrieval_context_eval",
    "retrieve_hybrid_contexts": "retrieval_context_eval",
    "retrieve_text_contexts": "retrieval_context_eval",
    "retrieve_vector_contexts": "retrieval_context_eval",
    "search_results_to_contexts": "retrieval_context_eval",
    "try_score_extractions_contextual_relevancy": "extraction_deepeval",
    "run_dual_inference_benchmark": "inference_method_benchmark",
    "run_cognitive_eval": "cognitive_eval",
    "evaluate_verifier": "cognitive_eval",
    "make_candidates": "cognitive_eval",
    "build_distractors": "cognitive_eval",
    "EvidenceIndex": "cognitive_eval",
    "CandidateFact": "cognitive_eval",
    "grounded_cooccurrence_verifier": "cognitive_eval",
    "accept_all_verifier": "cognitive_eval",
    "PipelineParams": "ablation_harness",
    "EvalTask": "ablation_harness",
    "run_trial": "ablation_harness",
    "run_grid": "ablation_harness",
    "run_design": "ablation_harness",
    "RESPONSE_KEYS": "ablation_harness",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    submod = _EXPORTS.get(name)
    if submod is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f"{__name__}.{submod}")
    obj = getattr(module, name)
    globals()[name] = obj
    return obj


def __dir__() -> list[str]:
    return sorted(__all__)
