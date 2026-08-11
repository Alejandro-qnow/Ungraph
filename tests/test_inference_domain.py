"""Tests: value objects de inferencia, alineación ontológica y caché LLM."""

from unittest.mock import MagicMock

from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.services.ontology_alignment import validate_ontology_alignment
from ungraph.domain.value_objects.document_context import DocumentContext
from ungraph.domain.value_objects.ontology_profile import OntologyProfile


def test_document_context_prompt_snippet():
    dc = DocumentContext(
        source_id="https://x/doc",
        summary="API de pagos.",
        inferred_domain="fintech",
        key_entities_hint=("Payment", "Ledger"),
    )
    s = dc.to_prompt_snippet()
    assert "pagos" in s or "API" in s
    assert "fintech" in s


def test_validate_ontology_alignment():
    profile = OntologyProfile(
        profile_id="p1",
        allowed_nodes=("Person", "Org"),
        allowed_relationships=("WORKS_FOR",),
    )
    report = validate_ontology_alignment(
        extracted_node_types={"Person", "Product"},
        extracted_relation_types={"WORKS_FOR", "UNKNOWN_REL"},
        profile=profile,
    )
    assert "Product" in report.orphan_labels
    assert "UNKNOWN_REL" in report.orphan_relations
    assert "Org" in report.uncovered_allowed_nodes


def test_ontology_profile_resolve_uris_case_insensitive():
    p = OntologyProfile(
        profile_id="t",
        allowed_nodes=("Person",),
        allowed_relationships=("WORKS_FOR",),
        class_uri_by_label={"Person": "http://example.org/Person"},
        property_uri_by_rel={"WORKS_FOR": "http://example.org/worksFor"},
    )
    assert p.resolve_class_uri("person") == "http://example.org/Person"
    assert p.resolve_property_uri("works_for") == "http://example.org/worksFor"


def test_llm_inference_enriches_ontology_uris_with_profile():
    from unittest.mock import patch

    from ungraph.infrastructure.services.llm_inference_service import LLMInferenceService

    class _N:
        __slots__ = ("id", "type")

        def __init__(self, id: str, type: str) -> None:
            self.id = id
            self.type = type

    class _R:
        __slots__ = ("source", "target", "type")

        def __init__(self, source: _N, target: _N, type: str) -> None:
            self.source = source
            self.target = target
            self.type = type

    n_a = _N("Alice", "Person")
    n_b = _N("Acme", "Organization")
    gd = MagicMock()
    gd.nodes = [n_a, n_b]
    gd.relationships = [_R(n_a, n_b, "WORKS_FOR")]

    llm = MagicMock()
    profile = OntologyProfile(
        profile_id="x",
        allowed_nodes=("Person", "Organization"),
        allowed_relationships=("WORKS_FOR",),
        class_uri_by_label={"Person": "http://c/P", "Organization": "http://c/O"},
        property_uri_by_rel={"WORKS_FOR": "http://c/wf"},
    )

    def fake_process(_self, _doc):
        return gd

    with patch(
        "ungraph.infrastructure.agents.inference_state_graph.LLMGraphTransformer.process_response",
        fake_process,
    ):
        service = LLMInferenceService(
            llm=llm,
            allowed_nodes=["Person", "Organization"],
            allowed_relationships=["WORKS_FOR"],
            strict_mode=True,
            ontology_profile=profile,
        )
        ch = Chunk(id="c1", page_content="x", metadata={})
        entities = service.extract_entities(ch)
        rels = service.extract_relations(ch, entities)
        facts = service.infer_facts(ch, entities=entities)

    assert entities[0].ontology_class_uri == "http://c/P"
    assert rels[0].ontology_property_uri == "http://c/wf"
    assert facts[0].object_entity_type == "Person"
    assert facts[0].object_ontology_class_uri == "http://c/P"


def test_llm_inference_single_process_response_per_chunk():
    """extract_entities + extract_relations para el mismo chunk: un solo process_response."""
    from unittest.mock import patch

    from ungraph.infrastructure.services.llm_inference_service import LLMInferenceService

    class _N:
        __slots__ = ("id", "type")

        def __init__(self, id: str, type: str) -> None:
            self.id = id
            self.type = type

    class _R:
        __slots__ = ("source", "target", "type")

        def __init__(self, source: _N, target: _N, type: str) -> None:
            self.source = source
            self.target = target
            self.type = type

    n_a = _N("Alice", "Person")
    n_b = _N("Acme", "Organization")
    gd = MagicMock()
    gd.nodes = [n_a, n_b]
    gd.relationships = [_R(n_a, n_b, "WORKS_FOR")]

    llm = MagicMock()
    calls: list[int] = []

    def fake_process(_self, _doc):
        calls.append(1)
        return gd

    with patch(
        "ungraph.infrastructure.agents.inference_state_graph.LLMGraphTransformer.process_response",
        fake_process,
    ):
        service = LLMInferenceService(
            llm=llm,
            allowed_nodes=["Person", "Organization"],
            allowed_relationships=["WORKS_FOR"],
            strict_mode=True,
        )

        chunk = Chunk(id="chunk_same", page_content="Alice works at Acme.", metadata={})
        entities = service.extract_entities(chunk)
        rels = service.extract_relations(chunk, entities)

    assert len(calls) == 1
    assert len(entities) >= 1
    assert len(rels) >= 1
    assert all(e.extraction_method == "llm" for e in entities)
    assert all(r.extraction_method == "llm" for r in rels)


def test_llm_infer_facts_with_entities_skips_second_graph_load():
    """infer_facts(chunk, entities=...) no vuelve a pedir GraphDocument al grafo."""
    from unittest.mock import patch

    from ungraph.infrastructure.services.llm_inference_service import LLMInferenceService

    class _N:
        __slots__ = ("id", "type")

        def __init__(self, id: str, type: str) -> None:
            self.id = id
            self.type = type

    gd = MagicMock()
    gd.nodes = [_N("Bob", "Person")]
    gd.relationships = []

    llm = MagicMock()
    loads: list[str] = []

    def fake_process(_self, _doc):
        loads.append("graph")
        return gd

    with patch(
        "ungraph.infrastructure.agents.inference_state_graph.LLMGraphTransformer.process_response",
        fake_process,
    ):
        service = LLMInferenceService(
            llm=llm,
            allowed_nodes=["Person"],
            allowed_relationships=["WORKS_FOR"],
            strict_mode=True,
        )
        ch = Chunk(id="c_skip", page_content="Bob spoke.", metadata={})
        entities = service.extract_entities(ch)
        assert len(loads) == 1
        facts = service.infer_facts(ch, entities=entities)
        assert len(loads) == 1
        assert facts[0].object == "Bob"
