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
    FactJudgment,
    critique_fact,
    make_llm_fact_critic,
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


# --------------------------------------------------------------- crítico LLM
class _FakeLLM:
    """Chat model falso: devuelve un JSON de faithfulness fijo."""

    def __init__(self, content: str):
        self._content = content
        self.calls = 0

    def invoke(self, prompt):
        self.calls += 1

        class _R:
            content = self._content

        return _R()


def test_make_llm_fact_critic_parses_json():
    llm = _FakeLLM('{"supported": false, "confidence": 0.9, "rationale": "solo co-ocurren"}')
    critic = make_llm_fact_critic(llm)
    j = critic(CandidateFact("Alice Chen", "Mountain View", "LOCATED_IN"), ["ctx"])
    assert isinstance(j, FactJudgment)
    assert j.supported is False and j.confidence == pytest.approx(0.9)
    assert llm.calls == 1


def test_llm_signal_appears_in_report():
    ev = _ev()
    critic = lambda c, passages: FactJudgment(supported=True, confidence=0.8)
    rep = critique_fact(
        CandidateFact("Alice Chen", "Acme Robotics", "WORKS_FOR"), ev, llm_critic=critic
    )
    assert any(s.name == "llm_faithfulness" for s in rep.signals)


def test_llm_critic_failure_degrades_gracefully():
    ev = _ev()

    def _boom(c, passages):
        raise RuntimeError("llm down")

    rep = critique_fact(
        CandidateFact("Alice Chen", "Acme Robotics", "WORKS_FOR"), ev, llm_critic=_boom
    )
    # sin señal LLM, pero el critique sigue produciendo un reporte determinista
    assert not any(s.name == "llm_faithfulness" for s in rep.signals)
    assert rep.score > 0


def test_llm_gate_with_oracle_eliminates_residual_hallucination():
    """Techo de la arquitectura: un crítico que juzga bien (oráculo sobre is_distractor)
    con llm_gate lleva la alucinación a 0 sin perder recall — algo que las señales
    léxicas no lograban (36% residual por distractores que co-ocurren)."""
    ev = _ev()
    gold = {
        "entities": ["Alice Chen", "Acme Robotics", "Mountain View", "Google"],
        "relation_pairs": [
            {"subject": "Alice Chen", "object": "Acme Robotics", "predicate_hint": "WORKS_FOR"},
            {"subject": "Acme Robotics", "object": "Mountain View", "predicate_hint": "LOCATED_IN"},
            {"subject": "Alice Chen", "object": "Google", "predicate_hint": "PREVIOUS_EMPLOYMENT"},
        ],
    }
    candidates = make_candidates(gold)

    def oracle(c: CandidateFact, passages):
        return FactJudgment(supported=not c.is_distractor, confidence=0.95)

    verifier = make_structural_verifier(ontology=_ONTO, llm_critic=oracle, llm_gate=True)
    m = evaluate_verifier(candidates, verifier, ev)
    assert m["hallucination_rate"] == 0.0
    assert m["real_recall"] == 1.0
