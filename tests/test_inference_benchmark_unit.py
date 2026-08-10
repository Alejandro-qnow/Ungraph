"""Tests for inference_method_benchmark helpers (no LLM / no spaCy load)."""

from __future__ import annotations

import pytest

from ungraph.domain.entities.entity import Entity
from ungraph.domain.entities.relation import Relation
from ungraph.evaluation.inference_method_benchmark import (
    _aggregate_chunk_relevancy,
    gold_entity_recall,
    gold_relation_pair_recall,
    names_align,
)

pytestmark = pytest.mark.unit


def test_names_align_containment() -> None:
    assert names_align("Alice Chen", "alice chen")
    assert names_align("Alice", "Alice Chen")


def test_gold_entity_recall() -> None:
    ex = [
        Entity(id="1", name="Acme Robotics", type="ORG", mentions=["c1"]),
        Entity(id="2", name="Mountain View", type="LOC", mentions=["c1"]),
    ]
    gold = ["Acme Robotics", "Google Ghost"]
    r = gold_entity_recall(gold, ex)
    assert r == 0.5


def test_gold_relation_pair_recall() -> None:
    e1 = Entity(id="a", name="Alice Chen", type="PERSON", mentions=["c"])
    e2 = Entity(id="b", name="Acme Robotics", type="ORG", mentions=["c"])
    rel = Relation(
        id="r1",
        source_entity_id="a",
        target_entity_id="b",
        relation_type="WORKS_FOR",
        confidence=0.9,
        provenance_ref="c",
        source_entity_name="Alice Chen",
        target_entity_name="Acme Robotics",
    )
    gold_pairs = [
        {"subject": "Alice Chen", "object": "Acme Robotics"},
        {"subject": "X", "object": "Y"},
    ]
    assert gold_relation_pair_recall(gold_pairs, [rel], [e1, e2]) == 0.5


def test_aggregate_chunk_relevancy_skipped_and_means() -> None:
    rows = [
        {"available": True, "skipped": True, "reason": "no_entities"},
        {"available": True, "mean_score": 0.8, "entities_scored": 2},
        {"available": True, "mean_score": 0.6, "entities_scored": 1},
    ]
    agg = _aggregate_chunk_relevancy(rows)
    assert agg["available"] is True
    assert agg["mean_score_across_chunks"] == pytest.approx(0.7)
    assert agg["chunks_with_mean_score"] == 2


def test_aggregate_chunk_relevancy_all_unavailable() -> None:
    agg = _aggregate_chunk_relevancy(
        [{"available": False, "reason": "deepeval not installed: x"}]
    )
    assert agg["available"] is False
