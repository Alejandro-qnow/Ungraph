"""LangGraph de extracción: smoke con LLMGraphTransformer mockeado."""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_community.graphs.graph_document import GraphDocument

import pytest

from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.services.document_context_service import DocumentContextService
from ungraph.domain.services.domain_question_service import DomainQuestionService
from ungraph.domain.value_objects.document_context import DocumentContext
from ungraph.infrastructure.agents.inference_state_graph import build_llm_extraction_graph

pytestmark = pytest.mark.unit


def test_extraction_graph_invoke_calls_transformer_once(mocker) -> None:
    src = Document(page_content="x")
    fake_gd = GraphDocument(nodes=[], relationships=[], source=src)
    mock_proc = mocker.patch(
        "ungraph.infrastructure.agents.inference_state_graph.LLMGraphTransformer.process_response",
        return_value=fake_gd,
    )
    llm = mocker.MagicMock()
    compiled = build_llm_extraction_graph(
        llm, allowed_nodes=["Person"], allowed_relationships=["REL"], strict_mode=True
    )
    chunk = Chunk(id="c1", page_content="hello world", metadata={})
    out = compiled.invoke({"chunk": chunk})
    assert out.get("graph_document") is fake_gd
    mock_proc.assert_called_once()


def test_extraction_graph_context_prefixes_document_when_services_set(mocker) -> None:
    captured: dict[str, str] = {}

    def capture_process(doc):
        captured["page_content"] = doc.page_content
        return GraphDocument(nodes=[], relationships=[], source=doc)

    mocker.patch(
        "ungraph.infrastructure.agents.inference_state_graph.LLMGraphTransformer.process_response",
        side_effect=capture_process,
    )
    doc_ctx = mocker.Mock(spec_set=DocumentContextService)
    doc_ctx.extract.return_value = DocumentContext(
        source_id="doc-1",
        summary="Scoped summary",
        key_entities_hint=("Acme",),
    )
    dom_q = mocker.Mock(spec_set=DomainQuestionService)
    dom_q.generate.return_value = ("Who is the main actor?",)

    compiled = build_llm_extraction_graph(
        mocker.MagicMock(),
        allowed_nodes=["Person"],
        allowed_relationships=["REL"],
        document_context_service=doc_ctx,
        domain_question_service=dom_q,
    )
    chunk = Chunk(
        id="c1",
        page_content="Alice works at Acme.",
        metadata={"source_id": "src/doc.md"},
    )
    compiled.invoke({"chunk": chunk})

    text = captured["page_content"]
    assert "[Ungraph context for extraction]" in text
    assert "Scoped summary" in text
    assert "Who is the main actor?" in text
    assert "[Source text]" in text
    assert "Alice works at Acme." in text
    doc_ctx.extract.assert_called_once()
    dom_q.generate.assert_called_once()


def test_extraction_graph_spacy_hints_prefix_when_service_provided(mocker) -> None:
    captured: dict[str, str] = {}

    def capture_process(doc):
        captured["page_content"] = doc.page_content
        return GraphDocument(nodes=[], relationships=[], source=doc)

    mocker.patch(
        "ungraph.infrastructure.agents.inference_state_graph.LLMGraphTransformer.process_response",
        side_effect=capture_process,
    )

    from ungraph.domain.entities.entity import Entity

    class FakeSpacy:
        def extract_entities(self, chunk):
            return [
                Entity(id="e1", name="Acme Corp", type="ORGANIZATION", mentions=[chunk.id]),
            ]

    compiled = build_llm_extraction_graph(
        mocker.MagicMock(),
        allowed_nodes=["Organization"],
        allowed_relationships=["REL"],
        spacy_lexical_service=FakeSpacy(),
    )
    chunk = Chunk(id="c1", page_content="We use Acme Corp.", metadata={})
    compiled.invoke({"chunk": chunk})

    text = captured["page_content"]
    assert "Lexical entity candidates" in text
    assert "- Acme Corp (ORGANIZATION)" in text
    assert "[Source text]" in text
    assert "We use Acme Corp." in text
    assert text.index("Lexical entity") < text.index("[Source text]")
