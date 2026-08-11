"""Unit: scorecard global end-to-end (agregación + composición + ranking).

Sin Neo4j/LLM: usa métricas mock (como las que producen las evaluaciones reales) y
verifica la agregación, el composite_score (desirability) y el ranking de arquitecturas.
"""

from __future__ import annotations

import pytest

from ungraph.evaluation.scorecard import (
    DomainScorecard,
    build_scorecard,
    evidence_coverage_from_counts,
    extract_from_chunking_downstream,
    rag_qa_from_probe_eval,
    rank_scorecards,
    reasoning_from_cognitive,
    transform_from_benchmark,
    transform_from_structural_stats,
)

pytestmark = pytest.mark.unit


def test_transform_from_benchmark_picks_engine_branch():
    bench = {
        "ner": {"entity_count": 10, "relation_count": 2},
        "llm": {"entity_count": 12, "relation_count": 8},
        "gold_metrics": {
            "ner": {"entity_recall": 1.0, "relation_pair_recall": 0.5},
            "llm": {"entity_recall": 1.0, "relation_pair_recall": 1.0},
        },
    }
    t = transform_from_benchmark(bench, engine="llm")
    assert t["entity_recall"] == 1.0 and t["relation_pair_recall"] == 1.0
    assert t["n_relations"] == 8


def test_transform_from_structural_stats_density():
    stats = {
        "node_counts_by_label": {"Entity": 4},
        "relationship_counts_by_type": {"RELATED_TO": 3},
    }
    t = transform_from_structural_stats(stats)
    assert t["n_nodes"] == 4 and t["n_relations"] == 3
    assert t["density"] == pytest.approx(3 / (4 * 3))


def test_reasoning_from_cognitive_filters_keys():
    m = {"f1": 0.67, "hallucination_rate": 0.12, "real_recall": 1.0, "extra": 99}
    r = reasoning_from_cognitive(m)
    assert set(r) == {"f1", "hallucination_rate", "real_recall"}


def test_composite_score_rewards_quality_penalizes_hallucination():
    good = build_scorecard(
        "kg", {"inference": "llm"},
        transform={"entity_recall": 1.0, "relation_pair_recall": 1.0},
        reasoning={"f1": 0.9, "hallucination_rate": 0.05},
    )
    bad = build_scorecard(
        "kg", {"inference": "ner"},
        transform={"entity_recall": 1.0, "relation_pair_recall": 0.4},
        reasoning={"f1": 0.3, "hallucination_rate": 0.8},
    )
    assert good.composite_score() > bad.composite_score()
    # alta alucinación debe hundir el score pese a buen recall
    assert bad.composite_score() < 0.6


def test_composite_ignores_absent_metrics():
    # solo una métrica presente -> score = esa métrica (dirección +1)
    card = build_scorecard("kg", {}, reasoning={"f1": 0.8})
    assert card.composite_score() == pytest.approx(0.8)
    # scorecard vacío -> 0.0, sin error
    assert build_scorecard("kg", {}).composite_score() == 0.0


def test_json_roundtrip_and_ranking():
    a = build_scorecard("kg", {"inference": "llm"}, reasoning={"f1": 0.9, "hallucination_rate": 0.1})
    b = build_scorecard("kg", {"inference": "ner"}, reasoning={"f1": 0.5, "hallucination_rate": 0.5})
    ranked = rank_scorecards([b, a])
    assert ranked[0].architecture["inference"] == "llm"  # mejor primero

    obj = a.to_json_obj()
    assert "composite_score" in obj
    back = DomainScorecard.from_json_obj(obj)
    assert back.composite_score() == a.composite_score()


def test_evidence_and_probe_adapters():
    cov = evidence_coverage_from_counts(n_facts=10, n_with_provenance=7)
    assert cov["evidence_coverage"] == 0.7
    rag = rag_qa_from_probe_eval({"answer_correctness": 0.5, "n_probes": 2})
    assert rag["answer_correctness"] == 0.5
    extract = extract_from_chunking_downstream(
        {"n_chunks": 3, "mrr": 0.8, "hit_rate": {"5": 1.0, "1": 0.5}, "probes_total": 2, "probes_covered": 2}
    )
    assert extract["mrr"] == 0.8 and extract["hit_at_k"] == 1.0
