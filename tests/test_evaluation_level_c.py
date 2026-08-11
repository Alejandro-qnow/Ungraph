"""Unit tests: nivel C experiment artifacts and structural stats helpers."""

from __future__ import annotations

import pytest

from ungraph.evaluation.experiment_run import ExperimentRun, rank_experiment_runs_by_relevancy
from ungraph.evaluation.graph_structural_stats import (
    GraphStructuralStats,
    diff_structural_stats,
)

pytestmark = pytest.mark.unit


def test_graph_structural_stats_json_roundtrip():
    gs = GraphStructuralStats(
        node_counts_by_label={"Chunk": 3, "Entity": 2},
        relationship_counts_by_type={"MENTIONS": 2},
        collected_at_utc="2026-05-16T12:00:00Z",
        database="neo4j",
    )
    back = GraphStructuralStats.from_json_obj(gs.to_json_obj())
    assert back == gs


def test_diff_structural_stats():
    a = GraphStructuralStats(
        node_counts_by_label={"Chunk": 5},
        relationship_counts_by_type={"NEXT_CHUNK": 4},
        collected_at_utc="t1",
    )
    b = GraphStructuralStats(
        node_counts_by_label={"Chunk": 7, "Entity": 3},
        relationship_counts_by_type={"NEXT_CHUNK": 4},
        collected_at_utc="t2",
    )
    d = diff_structural_stats(a, b)
    assert d["nodes"]["Chunk"]["delta"] == 2
    assert "Entity" in d["nodes"]
    assert d["relationships"] == {}


def test_experiment_run_json_roundtrip():
    gs = GraphStructuralStats(
        node_counts_by_label={"A": 1},
        relationship_counts_by_type={"R": 1},
        collected_at_utc="t",
    )
    run = ExperimentRun(
        pipeline_params={"chunk_size": 500},
        graph_stats=gs,
        retrieval_metrics=[{"contextual_relevancy": {"score": 0.8}}],
        notes="test",
    )
    run2 = ExperimentRun.from_json(run.to_json())
    assert run2.pipeline_params == {"chunk_size": 500}
    assert run2.graph_stats == gs
    assert run2.retrieval_metrics == [{"contextual_relevancy": {"score": 0.8}}]
    assert run2.notes == "test"


def test_rank_experiment_runs_by_relevancy():
    bad = ExperimentRun(retrieval_metrics=[])
    good = ExperimentRun(
        retrieval_metrics=[
            {"contextual_relevancy": {"score": 0.9}},
            {"contextual_relevancy": {"score": 0.5}},
        ]
    )
    mid = ExperimentRun(
        retrieval_metrics=[{"contextual_relevancy": {"score": 0.7}}]
    )
    ranked = rank_experiment_runs_by_relevancy([bad, good, mid])
    assert ranked[0][1] is good
    assert ranked[-1][1] is bad
