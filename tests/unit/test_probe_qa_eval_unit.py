"""Unit: probe-QA answer containment offline."""

from __future__ import annotations

import pytest

from ungraph.evaluation.probe_qa_eval import (
    answer_contained,
    evaluate_answer_containment_corpus,
    load_probe_queries,
)

pytestmark = pytest.mark.unit


def test_answer_contained_and_corpus_eval():
    assert answer_contained("Cypher", ["Neo4j uses Cypher as query language"])
    assert not answer_contained("SPARQL", ["Neo4j uses Cypher"])

    probes = [
        {"query": "q1", "answer": "Cypher"},
        {"query": "q2", "answer": "SPARQL"},
    ]
    m = evaluate_answer_containment_corpus(probes, ["Cypher is for property graphs"])
    assert m["n_probes"] == 2
    assert m["n_correct"] == 1
    assert m["answer_correctness"] == 0.5


def test_load_probe_queries_from_dict():
    gold = {
        "graphrag_probe_queries": [
            {"query": "Which language?", "answer": "Cypher"},
            {"query": "", "answer": "x"},
        ]
    }
    probes = load_probe_queries(gold)
    assert len(probes) == 1
    assert probes[0]["answer"] == "Cypher"


def test_long_answer_requires_exact_phrase():
    phrase = "Cypher expresses traversals concisely"
    assert answer_contained(phrase, [f"… {phrase} …"])
    # token AND would match loosely; long answers must not
    assert not answer_contained(
        phrase,
        ["Cypher is used", "graphs express structure", "traversals exist", "concisely written"],
    )
