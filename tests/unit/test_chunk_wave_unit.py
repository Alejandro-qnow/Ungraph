"""Unit: chunk-wave configs + verdict (no Neo4j)."""

from __future__ import annotations

import pytest

from ungraph.evaluation.chunk_wave import build_chunk_wave_verdict
from ungraph.evaluation.domain_pipeline import chunk_wave_configs_from_capa0
from ungraph.evaluation.experiment_run import ExperimentRun


@pytest.mark.unit
def test_chunk_wave_configs():
    cfgs = chunk_wave_configs_from_capa0(
        {"chunking": "recursive", "chunk_overlap": 200, "inference": "ner", "rag": "text"},
        chunk_sizes=(512, 1000),
    )
    assert len(cfgs) == 2
    assert {c["chunk_size"] for c in cfgs} == {512, 1000}
    assert all(c["inference"] == "ner" for c in cfgs)


@pytest.mark.unit
def test_chunk_wave_verdict_compared():
    runs = [
        ExperimentRun(
            architecture={"chunk_size": 512, "inference": "ner", "chunking": "recursive"},
            scorecard={
                "extract": {"n_chunks": 5, "hit_at_k": 0.8},
                "transform": {"entity_recall": 0.4, "evidence_coverage": 1.0},
                "rag_qa": {"answer_correctness": 0.8},
            },
        ),
        ExperimentRun(
            architecture={"chunk_size": 1000, "inference": "ner", "chunking": "recursive"},
            scorecard={
                "extract": {"n_chunks": 3, "hit_at_k": 1.0},
                "transform": {"entity_recall": 0.5, "evidence_coverage": 1.0},
                "rag_qa": {"answer_correctness": 1.0},
            },
        ),
    ]
    v = build_chunk_wave_verdict(runs, capa0_run_id="x", fixed_inference="ner")
    assert v["status"] == "COMPARED"
    assert v["pass"] is True
    assert v["h_chunk"]["answer_correctness_spread"] == pytest.approx(0.2)
