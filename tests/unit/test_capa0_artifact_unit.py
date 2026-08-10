"""Unit tests for Capa 0 freeze/reload helpers (no Neo4j)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ungraph.evaluation.capa0_artifact import (
    SCHEMA,
    Capa0Artifact,
    build_capa0_from_experiment_run,
    compare_gate,
    gate_metrics_from_scorecard,
    load_capa0_artifact,
    relativize_to_domain,
    save_capa0_artifact,
    select_ner_run,
    validate_capa0_artifact,
)
from ungraph.evaluation.experiment_run import ExperimentRun


@pytest.mark.unit
def test_gate_metrics_from_scorecard():
    gate = gate_metrics_from_scorecard(
        {
            "transform": {
                "entity_recall": 0.5,
                "relation_pair_recall": 0.25,
                "evidence_coverage": 1.0,
                "n_facts": 3,
            },
            "rag_qa": {"answer_correctness": 1.0},
        }
    )
    assert gate["entity_recall"] == 0.5
    assert gate["answer_correctness"] == 1.0


@pytest.mark.unit
def test_relativize_and_roundtrip(tmp_path: Path):
    domain = tmp_path / "knowledge_graphs"
    domain.mkdir()
    (domain / "corpus").mkdir()
    gold = domain / "gold.json"
    gold.write_text("{}", encoding="utf-8")
    corpus = domain / "corpus" / "kg_survey.md"
    corpus.write_text("x", encoding="utf-8")

    run = ExperimentRun(
        run_id="abc-123",
        domain="knowledge_graphs",
        architecture={
            "chunking": "recursive",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "inference": "ner",
            "rag": "text",
            "top_k": 5,
            "mode": "online",
        },
        scorecard={
            "transform": {"entity_recall": 0.47, "evidence_coverage": 1.0},
            "rag_qa": {"answer_correctness": 1.0},
        },
        gold_path=str(gold),
        corpus_paths=[str(corpus)],
        seed=0,
        git_sha="deadbeef",
    )
    art = build_capa0_from_experiment_run(run, domain_dir=domain)
    assert art.schema == SCHEMA
    assert art.gold_path == "gold.json"
    assert art.corpus_paths == ["corpus/kg_survey.md"]
    assert art.gate["entity_recall"] == 0.47

    out = domain / "reports" / "capa0_artifact.json"
    save_capa0_artifact(out, art)
    loaded = load_capa0_artifact(out)
    assert loaded.run_id == "abc-123"
    assert loaded.architecture["inference"] == "ner"


@pytest.mark.unit
def test_refuse_non_ner_freeze():
    run = ExperimentRun(
        run_id="x",
        architecture={"inference": "none"},
        corpus_paths=["corpus/a.md"],
        gold_path="gold.json",
    )
    with pytest.raises(ValueError, match="non-ner"):
        build_capa0_from_experiment_run(run, domain_dir=Path("."))


@pytest.mark.unit
def test_compare_gate_tolerance():
    frozen = {"entity_recall": 0.4737, "answer_correctness": 1.0}
    observed = {"entity_recall": 0.4737, "answer_correctness": 1.0}
    assert compare_gate(frozen, observed)["ok"] is True
    bad = compare_gate(frozen, {"entity_recall": 0.1, "answer_correctness": 1.0})
    assert bad["ok"] is False


@pytest.mark.unit
def test_select_ner_run():
    none = ExperimentRun(
        architecture={"inference": "none"},
        scorecard={"transform": {"entity_recall": 0.0}},
    )
    ner_lo = ExperimentRun(
        architecture={"inference": "ner"},
        scorecard={"transform": {"entity_recall": 0.2}},
    )
    ner_hi = ExperimentRun(
        architecture={"inference": "ner"},
        scorecard={"transform": {"entity_recall": 0.5}},
    )
    assert select_ner_run([none, ner_lo, ner_hi]).run_id == ner_hi.run_id


@pytest.mark.unit
def test_validate_requires_corpus():
    with pytest.raises(ValueError, match="corpus"):
        validate_capa0_artifact(
            {
                "schema": SCHEMA,
                "run_id": "x",
                "architecture": {"inference": "ner"},
                "corpus_paths": [],
                "gold_path": "gold.json",
            }
        )


@pytest.mark.unit
def test_relativize_windows_style(tmp_path: Path):
    domain = tmp_path / "d"
    (domain / "corpus").mkdir(parents=True)
    abs_path = domain / "corpus" / "kg_survey.md"
    abs_path.write_text("z", encoding="utf-8")
    assert relativize_to_domain(abs_path, domain) == "corpus/kg_survey.md"
