"""Unit: verificador estructural anclado (reasoning.agentic) + ablation.

Demuestra que combinar co-ocurrencia con la señal ontológica añade poder de rechazo
sobre el baseline de co-ocurrencia pura, y que el verificador se mide con la misma
vara (cognitive_eval).
"""

from __future__ import annotations

import pytest

from ungraph.domain.value_objects.curation_state import (
    CURATION_STATE_CURATED,
    CURATION_STATE_INVALID,
)
from ungraph.domain.value_objects.ontology_profile import OntologyProfile
from ungraph.evaluation.cognitive_eval import (
    CandidateFact,
    EvidenceIndex,
    accept_all_verifier,
    evaluate_verifier,
    grounded_cooccurrence_verifier,
    make_candidates,
)
from ungraph.reasoning.agentic import (
    critique_fact,
    make_structural_verifier,
)

pytestmark = pytest.mark.unit

_TEXT = (
    "Alice Chen is a staff research engineer at Acme Robotics, a startup based in "
    "Mountain View, California. Acme Robotics signed a pilot contract with "
    "Northwind Logistics. Alice previously worked at Google."
)

_ONTO = OntologyProfile(
    profile_id="test",
    allowed_nodes=("Person", "Organization", "Location"),
    allowed_relationships=("WORKS_FOR", "LOCATED_IN", "PREVIOUS_EMPLOYMENT"),
)


def _ev() -> EvidenceIndex:
    return EvidenceIndex.from_text(_TEXT)


def test_critique_score_reflects_signals():
    ev = _ev()
    real = CandidateFact("Acme Robotics", "Mountain View", "LOCATED_IN")
    rep = critique_fact(real, ev, ontology=_ONTO)
    # co-ocurren + ambas mencionadas + predicado en ontología -> score alto
    assert rep.score == pytest.approx(1.0)
    assert "evidence_cooccurrence=ok" in rep.rationale


def test_structural_verifier_accepts_real_rejects_unsupported():
    verify = make_structural_verifier(ontology=_ONTO)
    ev = _ev()
    real = CandidateFact("Acme Robotics", "Mountain View", "LOCATED_IN")
    unsupported = CandidateFact("Google", "Mountain View", "LOCATED_IN")
    assert verify(real, ev).decision == CURATION_STATE_CURATED
    # Google (S3) y Mountain View (S1) no co-ocurren en ninguna ventana -> sin soporte
    assert verify(unsupported, ev).decision == CURATION_STATE_INVALID


def test_ontology_gate_rejects_offschema_even_if_cooccurring():
    """Valor incremental de la ontología: un predicado fuera de esquema se rechaza
    aunque las entidades co-ocurran (algo que la co-ocurrencia pura aceptaría)."""
    ev = _ev()
    # Alice y Acme co-ocurren, pero el predicado no está en el esquema
    offschema = CandidateFact("Alice Chen", "Acme Robotics", "MARRIED_TO")

    grounded = grounded_cooccurrence_verifier(offschema, ev)
    gated = make_structural_verifier(ontology=_ONTO, ontology_gate=True)(offschema, ev)

    assert grounded.decision == CURATION_STATE_CURATED  # co-ocurrencia lo acepta
    assert gated.decision == CURATION_STATE_INVALID  # el gate ontológico lo rechaza


def test_structural_verifier_is_measurable_with_cognitive_eval():
    ev = _ev()
    gold = {
        "entities": [
            "Alice Chen",
            "Acme Robotics",
            "Mountain View",
            "Google",
            "Northwind Logistics",
        ],
        "relation_pairs": [
            {"subject": "Alice Chen", "object": "Acme Robotics", "predicate_hint": "WORKS_FOR"},
            {"subject": "Acme Robotics", "object": "Mountain View", "predicate_hint": "LOCATED_IN"},
            {"subject": "Alice Chen", "object": "Google", "predicate_hint": "PREVIOUS_EMPLOYMENT"},
        ],
    }
    candidates = make_candidates(gold)
    structural = make_structural_verifier(ontology=_ONTO, accept_threshold=0.6)

    base = evaluate_verifier(candidates, accept_all_verifier, ev)
    struct = evaluate_verifier(candidates, structural, ev)

    # el verificador estructural no alucina más que el piso y rechaza distractores
    assert struct["hallucination_rate"] <= base["hallucination_rate"]
    assert struct["distractor_rejection_rate"] > 0.0
