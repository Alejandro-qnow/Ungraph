"""Unit: recall gold vs nombres de Entity (sin Neo4j)."""

from __future__ import annotations

import pytest

from ungraph.evaluation.neo4j_gold_metrics import (
    entity_recall_from_names,
    normalize_entity_name,
    relation_pair_recall_from_names,
    transform_metrics_from_graph_names,
)
from ungraph.evaluation.probe_qa_eval import evaluate_answer_containment_topk

pytestmark = pytest.mark.unit


def test_normalize_and_entity_recall():
    assert normalize_entity_name("  Neo4j ") == "neo4j"
    m = entity_recall_from_names(
        ["Neo4j", "Cypher", "Missing"],
        ["neo4j", "CYPHER", "Other"],
    )
    assert m["n_hit_entities"] == 2
    assert m["entity_recall"] == pytest.approx(2 / 3, abs=1e-3)


def test_relation_pair_recall_both_endpoints():
    pairs = [
        {"subject": "Cypher", "object": "Neo4j"},
        {"subject": "OWL", "object": "RDFS"},
    ]
    m = relation_pair_recall_from_names(pairs, ["Cypher", "Neo4j"])
    assert m["n_hit_pairs"] == 1
    assert m["relation_pair_recall"] == 0.5


def test_transform_from_gold_dict():
    gold = {
        "entities": ["A", "B"],
        "relation_pairs": [{"subject": "A", "object": "B"}],
    }
    t = transform_metrics_from_graph_names(gold, ["a"])
    assert t["entity_recall"] == 0.5
    assert t["relation_pair_recall"] == 0.0


def test_topk_containment_not_full_corpus():
    probes = [{"query": "q1", "answer": "Cypher"}]
    # top-k sin la respuesta
    m = evaluate_answer_containment_topk(probes, lambda q: ["unrelated chunk"])
    assert m["answer_correctness"] == 0.0
    assert m["eval_mode"] == "topk_retrieved"
    # top-k con respuesta
    m2 = evaluate_answer_containment_topk(probes, lambda q: ["Neo4j uses Cypher"])
    assert m2["answer_correctness"] == 1.0
