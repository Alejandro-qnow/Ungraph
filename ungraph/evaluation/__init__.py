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
    "rank_experiment_runs_by_composite_score": "experiment_run",
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
    "DomainScorecard": "scorecard",
    "build_scorecard": "scorecard",
    "rank_scorecards": "scorecard",
    "transform_from_benchmark": "scorecard",
    "transform_from_structural_stats": "scorecard",
    "reasoning_from_cognitive": "scorecard",
    "evidence_coverage_from_counts": "scorecard",
    "extract_from_chunking_downstream": "scorecard",
    "rag_qa_from_probe_eval": "scorecard",
    "RetrievalProbe": "chunking_downstream_eval",
    "StrategyRetrievalScore": "chunking_downstream_eval",
    "compute_retrieval_metrics": "chunking_downstream_eval",
    "evaluate_chunking_downstream": "chunking_downstream_eval",
    "rank_by_mrr": "chunking_downstream_eval",
    "evaluate_answer_containment": "probe_qa_eval",
    "evaluate_answer_containment_corpus": "probe_qa_eval",
    "evaluate_answer_containment_topk": "probe_qa_eval",
    "load_probe_queries": "probe_qa_eval",
    "entity_recall_from_names": "neo4j_gold_metrics",
    "evaluate_gold_against_neo4j": "neo4j_gold_metrics",
    "ArchitectureParams": "doe_bridge",
    "DoeAnalysisResult": "doe_bridge",
    "architecture_factors_from_manifest": "doe_bridge",
    "build_screening_design": "doe_bridge",
    "analyze_results": "doe_bridge",
    "rows_to_pipeline_configs": "doe_bridge",
    "propose_next": "doe_bridge",
    "Capa0Artifact": "capa0_artifact",
    "build_capa0_from_experiment_run": "capa0_artifact",
    "load_capa0_artifact": "capa0_artifact",
    "save_capa0_artifact": "capa0_artifact",
    "compare_gate": "capa0_artifact",
    "build_family_wave_verdict": "family_wave",
    "build_chunk_wave_verdict": "chunk_wave",
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
