"""SparqlOntologyResolver sin red (mock de bindings)."""

from __future__ import annotations

import pytest

from ungraph.infrastructure.services.sparql_ontology_resolver import (
    SparqlOntologyResolver,
)

pytestmark = pytest.mark.unit


def test_sparql_resolver_builds_profile(mocker) -> None:
    bindings_nodes = [
        {"label": {"type": "literal", "value": "Person"}, "uri": {"type": "uri", "value": "http://ex/Person"}},
        {"label": {"type": "literal", "value": "Person"}},  # duplicate label ignored
    ]
    bindings_rels = [
        {"label": {"type": "literal", "value": "KNOWS"}, "uri": {"type": "uri", "value": "http://ex/knows"}},
    ]
    mock_sel = mocker.patch(
        "ungraph.infrastructure.services.sparql_ontology_resolver.sparql_select_bindings",
        side_effect=[bindings_nodes, bindings_rels],
    )
    r = SparqlOntologyResolver(
        "http://db",
        nodes_query="SELECT ...",
        relations_query="SELECT ...",
        profile_id="custom",
        use_cache=False,
    )
    p = r.resolve("custom")
    assert p.allowed_nodes == ("Person",)
    assert p.class_uri_by_label.get("Person") == "http://ex/Person"
    assert p.allowed_relationships == ("KNOWS",)
    assert mock_sel.call_count == 2
