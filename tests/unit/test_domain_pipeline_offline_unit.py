"""Smoke offline: una arquitectura sobre kg_survey + gold (sin Neo4j)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ungraph.evaluation.domain_pipeline import run_architecture_offline

pytestmark = pytest.mark.unit

DOMAIN = Path(__file__).resolve().parents[2] / "benchmarks" / "domains" / "knowledge_graphs"


@pytest.mark.skipif(not (DOMAIN / "gold.json").exists(), reason="domain gold missing")
def test_run_architecture_offline_smoke():
    corpus = DOMAIN / "corpus" / "kg_survey.md"
    if not corpus.exists():
        pytest.skip("kg_survey.md missing")
    run, row = run_architecture_offline(
        domain="knowledge_graphs",
        architecture={
            "chunking": "recursive",
            "chunk_size": 512,
            "inference": "ner",
            "rag": "text",
        },
        corpus_paths=[corpus],
        gold_path=DOMAIN / "gold.json",
        design_id="unit",
        design_row_id="0",
        seed=0,
    )
    assert run.scorecard is not None
    assert "extract" in run.scorecard
    assert "transform" in run.scorecard
    assert run.scorecard["rag_qa"].get("answer_correctness") is not None
    assert "composite_score" in row
    assert row["latency_s"] is not None
