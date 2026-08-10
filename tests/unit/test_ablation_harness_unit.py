"""Unit: harness de ablación parametrizado (base del DoE fase 3).

Sin LLM/Neo4j: verifica que run_trial mapea factores→respuestas, que variar un
factor cambia la respuesta, y que un "diseño" (filas) se evalúa de punta a punta.
"""

from __future__ import annotations

import pytest

from ungraph.domain.value_objects.ontology_profile import OntologyProfile
from ungraph.evaluation.ablation_harness import (
    RESPONSE_KEYS,
    EvalTask,
    PipelineParams,
    run_design,
    run_grid,
    run_trial,
)
from ungraph.evaluation.cognitive_eval import make_candidates

pytestmark = pytest.mark.unit

_TEXT = (
    "Alice Chen is a staff research engineer at Acme Robotics, a startup based in "
    "Mountain View, California. Acme Robotics signed a pilot contract with "
    "Northwind Logistics. Alice previously worked at Google."
)
_GOLD = {
    "entities": ["Alice Chen", "Acme Robotics", "Mountain View", "Google"],
    "relation_pairs": [
        {"subject": "Alice Chen", "object": "Acme Robotics", "predicate_hint": "WORKS_FOR"},
        {"subject": "Acme Robotics", "object": "Mountain View", "predicate_hint": "LOCATED_IN"},
        {"subject": "Alice Chen", "object": "Google", "predicate_hint": "PREVIOUS_EMPLOYMENT"},
    ],
}
_ONTO = OntologyProfile(
    profile_id="t",
    allowed_nodes=("Person", "Organization", "Location"),
    allowed_relationships=("WORKS_FOR", "LOCATED_IN", "PREVIOUS_EMPLOYMENT"),
)


def _task() -> EvalTask:
    return EvalTask(corpus_text=_TEXT, candidates=make_candidates(_GOLD), ontology=_ONTO)


def test_run_trial_returns_factors_and_responses():
    row = run_trial(PipelineParams(), _task())
    # contiene todos los factores...
    for name in PipelineParams.factor_names():
        assert name in row
    # ...y todas las respuestas
    for r in RESPONSE_KEYS:
        assert r in row and row[r] is not None


def test_threshold_is_monotone_on_rejection():
    task = _task()
    low = run_trial(PipelineParams(accept_threshold=0.4), task)
    high = run_trial(PipelineParams(accept_threshold=0.9), task)
    # umbral más alto => rechaza más (o igual) distractores
    assert high["distractor_rejection_rate"] >= low["distractor_rejection_rate"]


def test_from_record_casts_types_and_ignores_extra():
    rec = {
        "accept_threshold": "0.7",
        "window_sentences": 1.0,
        "use_ontology": "true",
        "unknown_column": 999,
    }
    p = PipelineParams.from_record(rec)
    assert p.accept_threshold == pytest.approx(0.7)
    assert p.window_sentences == 1 and isinstance(p.window_sentences, int)
    assert p.use_ontology is True


def test_run_design_end_to_end_like_doekit():
    # simula filas de un diseño (p. ej. plackett_burman): variar 2 factores binarios
    design = [
        {"ontology_gate": 0, "accept_threshold": 0.5},
        {"ontology_gate": 1, "accept_threshold": 0.5},
        {"ontology_gate": 0, "accept_threshold": 0.8},
        {"ontology_gate": 1, "accept_threshold": 0.8},
    ]
    rows = run_design(design, _task())
    assert len(rows) == 4
    # cada fila es apta para un DataFrame de doekit (factores + respuestas planos)
    assert all(set(RESPONSE_KEYS).issubset(r.keys()) for r in rows)
    assert all("accept_threshold" in r for r in rows)


def test_use_llm_false_ignores_injected_critic():
    task = _task()

    def _boom(candidate, passages):  # no debe llamarse si use_llm=False
        raise AssertionError("el crítico no debe invocarse con use_llm=False")

    row = run_trial(PipelineParams(use_llm=False), task, llm_critic=_boom)
    assert row["f1"] is not None
