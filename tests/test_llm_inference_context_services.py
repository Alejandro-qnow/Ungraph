"""Servicios LLM de contexto / preguntas con mocks (sin red)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ungraph.domain.value_objects.document_context import DocumentContext
from ungraph.infrastructure.services.heuristic_document_context_service import (
    HeuristicDocumentContextService,
)
from ungraph.infrastructure.services.llm_document_context_service import (
    LlmDocumentContextService,
)
from ungraph.infrastructure.services.llm_domain_question_generator import (
    LlmDomainQuestionGenerator,
)
from ungraph.infrastructure.services.template_domain_question_generator import (
    TemplateDomainQuestionGenerator,
)

pytestmark = pytest.mark.unit


def test_llm_document_context_parses_json() -> None:
    llm = SimpleNamespace(
        invoke=lambda _msgs: SimpleNamespace(
            content=(
                '{"summary": "Acme builds widgets.", '
                '"inferred_domain": "industry", "document_kind": "news", '
                '"key_terms": ["Acme", "widgets"]}'
            )
        )
    )
    svc = LlmDocumentContextService(llm, fallback=HeuristicDocumentContextService())
    ctx = svc.extract("Long text about Acme.", source_id="s1")
    assert "Acme" in ctx.summary
    assert ctx.inferred_domain == "industry"
    assert "Acme" in ctx.key_entities_hint


def test_llm_document_context_falls_back_on_bad_json() -> None:
    llm = SimpleNamespace(invoke=lambda _msgs: SimpleNamespace(content="not json"))
    heur = HeuristicDocumentContextService(summary_max_chars=80)
    svc = LlmDocumentContextService(llm, fallback=heur)
    text = "Alpha Beta Gamma delta epsilon zeta."
    ctx = svc.extract(text, source_id="s1")
    assert ctx.summary
    assert ctx.metadata.get("extractor") != "llm_v1"


def test_llm_domain_questions_parses_json() -> None:
    llm = SimpleNamespace(
        invoke=lambda _msgs: SimpleNamespace(
            content='{"questions": ["Who leads?", "Where is HQ?"]}'
        )
    )
    tmpl = TemplateDomainQuestionGenerator()
    gen = LlmDomainQuestionGenerator(llm, fallback=tmpl)
    dc = DocumentContext(source_id="s", summary="Co summary", key_entities_hint=("X",))
    qs = gen.generate("Some corp text here.", dc, max_questions=5)
    assert qs[0] == "Who leads?"
    assert len(qs) == 2


def test_llm_domain_questions_falls_back() -> None:
    llm = SimpleNamespace(invoke=lambda _msgs: SimpleNamespace(content="{}"))
    tmpl = TemplateDomainQuestionGenerator()
    gen = LlmDomainQuestionGenerator(llm, fallback=tmpl)
    dc = DocumentContext(source_id="s", summary="")
    qs = gen.generate("Hello world.", dc, max_questions=3)
    assert len(qs) >= 1
    low = qs[0].lower()
    assert "named entities" in low or "entity" in low or "relationship" in low
