"""Unit: ExperimentRun ↔ DomainScorecard ↔ fila DoE."""

from __future__ import annotations

import pytest

from ungraph.evaluation.experiment_run import (
    ExperimentRun,
    rank_experiment_runs_by_composite_score,
)
from ungraph.evaluation.scorecard import (
    build_scorecard,
    evidence_coverage_from_counts,
    rag_qa_from_probe_eval,
)

pytestmark = pytest.mark.unit


def test_from_scorecard_and_doe_row_roundtrip():
    card = build_scorecard(
        "knowledge_graphs",
        {"chunking": "recursive", "inference": "ner", "rag": "text"},
        extract={"chunking_quality_score": 0.8, "n_chunks": 4, "mrr": 0.5},
        transform={
            "entity_recall": 0.9,
            "relation_pair_recall": 0.5,
            **evidence_coverage_from_counts(n_facts=10, n_with_provenance=8),
        },
        reasoning={"f1": 0.7, "hallucination_rate": 0.1},
        rag_qa=rag_qa_from_probe_eval({"answer_correctness": 0.75, "n_probes": 4}),
        efficiency={"latency_s": 1.2},
    )
    run = ExperimentRun.from_scorecard(
        card,
        git_sha="abc123",
        seed=0,
        gold_path="gold.json",
        corpus_paths=["corpus/kg_survey.md"],
        design_id="D-optimal-b8-s0",
        design_row_id="3",
    )
    assert run.domain == "knowledge_graphs"
    assert run.architecture["inference"] == "ner"
    assert run.design_row_id == "3"
    assert run.composite_score() == card.composite_score()

    row = run.to_doe_row()
    assert row["chunking"] == "recursive"
    assert row["entity_recall"] == 0.9
    assert row["answer_correctness"] == 0.75
    assert row["composite_score"] == run.composite_score()
    assert row["design_id"] == "D-optimal-b8-s0"

    back = ExperimentRun.from_json_obj(run.to_json_obj())
    assert back.run_id == run.run_id
    assert back.composite_score() == run.composite_score()
    assert back.seed == 0


def test_rank_by_composite():
    a = ExperimentRun.from_scorecard(
        build_scorecard("kg", {"inference": "ner"}, reasoning={"f1": 0.9})
    )
    b = ExperimentRun.from_scorecard(
        build_scorecard("kg", {"inference": "none"}, reasoning={"f1": 0.2})
    )
    ranked = rank_experiment_runs_by_composite_score([b, a])
    assert ranked[0][1].architecture["inference"] == "ner"
