"""Tests: servicios heurísticos de contexto, preguntas de dominio y presets ontológicos."""

from ungraph.core.configuration import Settings, reset_configuration, get_settings, configure
from ungraph.domain.value_objects.document_context import DocumentContext
from ungraph.infrastructure.services.heuristic_document_context_service import (
    HeuristicDocumentContextService,
)
from ungraph.infrastructure.services.preset_ontology_resolver import PresetOntologyResolver
from ungraph.infrastructure.services.template_domain_question_generator import (
    TemplateDomainQuestionGenerator,
)
from ungraph.utils.inference_prompt import build_graph_transformer_context_addon


def test_heuristic_document_context():
    svc = HeuristicDocumentContextService(summary_max_chars=100, key_terms=3)
    text = "Acme Corporation announced Quantum API integration. " * 5
    dc = svc.extract(text, source_id="https://x/doc")
    assert "Acme" in dc.summary or "Quantum" in dc.summary
    assert len(dc.key_entities_hint) <= 3


def test_template_questions_and_prompt_addon():
    dc = DocumentContext(
        source_id="u1",
        summary="Banking API doc.",
        inferred_domain="fintech",
    )
    gen = TemplateDomainQuestionGenerator()
    qs = gen.generate("Some long text about transfers.", dc, max_questions=5)
    assert len(qs) >= 1
    assert any("fintech" in q.lower() or "domain" in q.lower() for q in qs)

    addon = build_graph_transformer_context_addon(dc, qs, max_chars=4000)
    assert "fintech" in addon.lower() or "Banking" in addon
    assert "Domain questions" in addon


def test_preset_ontology_resolver():
    r = PresetOntologyResolver()
    p = r.resolve("default")
    assert "Person" in p.allowed_nodes
    assert "WORKS_FOR" in p.allowed_relationships
    m = r.resolve("minimal")
    assert m.profile_id == "minimal"


def test_settings_inference_budget():
    reset_configuration()
    s = get_settings()
    assert s.inference_model_budget == "balanced"
    configure(inference_model_budget="economy")
    assert get_settings().inference_model_budget == "economy"
    reset_configuration()
