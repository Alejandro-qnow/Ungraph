"""Unit: harness de evaluación cognitiva (distractor injection + ablation).

Sin LLM/Neo4j: verifica que el verificador anclado separa hechos reales de
distractores mejor que el piso ``accept_all``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ungraph.evaluation.cognitive_eval import (
    CandidateFact,
    EvidenceIndex,
    accept_all_verifier,
    build_distractors,
    evaluate_verifier,
    grounded_cooccurrence_verifier,
    make_candidates,
    run_cognitive_eval,
)
from ungraph.domain.value_objects.curation_state import (
    CURATION_STATE_CURATED,
    CURATION_STATE_INVALID,
)

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parents[2]
_CORPUS = _REPO / "scripts" / "data" / "reference_corpus_en.txt"
_GOLD = _REPO / "scripts" / "data" / "reference_corpus_gold.json"

_TEXT = (
    "Alice Chen is a staff research engineer at Acme Robotics, a startup based in "
    "Mountain View, California. Acme Robotics signed a pilot contract with "
    "Northwind Logistics. Alice previously worked at Google."
)


def _evidence() -> EvidenceIndex:
    return EvidenceIndex.from_text(_TEXT)


def test_evidence_cooccurrence_and_mentions():
    ev = _evidence()
    assert ev.mentions("Alice Chen")
    assert ev.cooccur("Alice Chen", "Acme Robotics")
    # Google y Mountain View no aparecen en la misma ventana
    assert not ev.cooccur("Google", "Mountain View")


def test_grounded_accepts_real_rejects_distractor():
    ev = _evidence()
    real = CandidateFact("Acme Robotics", "Mountain View", "LOCATED_IN")
    fake = CandidateFact("Google", "Mountain View", "INJECTED", is_distractor=True)
    assert grounded_cooccurrence_verifier(real, ev).decision == CURATION_STATE_CURATED
    assert grounded_cooccurrence_verifier(fake, ev).decision == CURATION_STATE_INVALID


def test_build_distractors_excludes_gold_pairs():
    entities = ["Alice Chen", "Acme Robotics", "Google"]
    gold_pairs = [{"subject": "Alice Chen", "object": "Acme Robotics"}]
    d = build_distractors(entities, gold_pairs)
    keys = {(c.subject, c.object) for c in d}
    # el par gold (en cualquier orden) no debe aparecer como distractor
    assert ("Alice Chen", "Acme Robotics") not in keys
    assert ("Acme Robotics", "Alice Chen") not in keys
    assert all(c.is_distractor for c in d)


def test_evaluate_verifier_metrics_grounded_beats_accept_all():
    # Corpus controlado: cada relación real vive en su propia oración, de modo que
    # los pares cruzados (distractores) NO co-ocurren (ventana de 1 oración).
    text = "Alice works at Acme. Robert works at Globex. Carol lives in Paris."
    ev = EvidenceIndex.from_text(text, window_sentences=1)
    gold = {
        "entities": ["Alice", "Acme", "Robert", "Globex", "Carol", "Paris"],
        "relation_pairs": [
            {"subject": "Alice", "object": "Acme"},
            {"subject": "Robert", "object": "Globex"},
            {"subject": "Carol", "object": "Paris"},
        ],
    }
    candidates = make_candidates(gold)
    assert any(c.is_distractor for c in candidates)

    base = evaluate_verifier(candidates, accept_all_verifier, ev)
    grounded = evaluate_verifier(candidates, grounded_cooccurrence_verifier, ev)

    # accept_all acepta todo -> alucina con cada distractor
    assert base["hallucination_rate"] == 1.0
    # el anclado acepta los reales y rechaza los distractores cruzados
    assert grounded["real_recall"] == 1.0
    assert grounded["distractor_rejection_rate"] > 0.0
    assert grounded["hallucination_rate"] < base["hallucination_rate"]
    assert grounded["acceptance_precision"] > base["acceptance_precision"]


@pytest.mark.skipif(
    not (_CORPUS.is_file() and _GOLD.is_file()),
    reason="reference corpus/gold no disponible",
)
def test_run_cognitive_eval_end_to_end_with_ablation():
    report = run_cognitive_eval(_CORPUS, _GOLD)
    assert report["candidates"]["distractor"] > 0
    assert "grounded_cooccurrence" in report["verifiers"]
    # el anclado debe mejorar (o igualar) la precisión frente al piso
    assert report["ablation_delta"]["acceptance_precision"] >= 0
    assert report["ablation_delta"]["hallucination_rate"] <= 0
