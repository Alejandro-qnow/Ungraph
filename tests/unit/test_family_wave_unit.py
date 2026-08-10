"""Unit: family-wave verdict builder."""

from __future__ import annotations

import pytest

from ungraph.evaluation.experiment_run import ExperimentRun
from ungraph.evaluation.family_wave import build_family_wave_verdict


def _run(inf: str, er: float, ac: float = 1.0) -> ExperimentRun:
    return ExperimentRun(
        domain="knowledge_graphs",
        architecture={"inference": inf, "chunk_size": 1000},
        scorecard={
            "transform": {
                "entity_recall": er,
                "relation_pair_recall": 0.3,
                "evidence_coverage": 1.0,
            },
            "rag_qa": {"answer_correctness": ac},
            "efficiency": {"latency_s": 1.0},
        },
        efficiency={"latency_s": 1.0},
    )


@pytest.mark.unit
def test_family_wave_compared_with_deltas():
    v = build_family_wave_verdict(
        [_run("ner", 0.47), _run("pattern", 0.2)],
        capa0_run_id="capa0",
        families=["ner", "pattern"],
    )
    assert v["status"] == "COMPARED"
    assert v["pass"] is True
    assert v["n_families"] == 2
    assert v["deltas_vs_baseline"]["pattern"]["delta"]["entity_recall"] == pytest.approx(
        -0.27
    )


@pytest.mark.unit
def test_family_wave_incomplete():
    v = build_family_wave_verdict([_run("ner", 0.5)], families=["ner", "pattern"])
    assert v["status"] == "INCOMPLETE"
    assert v["pass"] is False
