"""Factory create_ontology_resolver."""

from __future__ import annotations

import pytest

from ungraph.application.dependencies import create_ontology_resolver
from ungraph.core.configuration import Settings
from ungraph.infrastructure.services.preset_ontology_resolver import (
    PresetOntologyResolver,
)
from ungraph.infrastructure.services.routing_ontology_resolver import (
    RoutingOntologyResolver,
)

pytestmark = pytest.mark.unit


def test_create_ontology_resolver_preset_only() -> None:
    r = create_ontology_resolver(Settings())
    assert isinstance(r, PresetOntologyResolver)


def test_create_ontology_resolver_routing_when_queries_set() -> None:
    s = Settings(
        ontology_sparql_endpoint="http://example.org/sparql",
        ontology_sparql_query_nodes="SELECT ?label WHERE { BIND(\"A\" AS ?label) }",
        ontology_sparql_query_relations="SELECT ?label WHERE { BIND(\"R\" AS ?label) }",
        ontology_sparql_profile_id="sparql",
    )
    r = create_ontology_resolver(s)
    assert isinstance(r, RoutingOntologyResolver)


@pytest.mark.parametrize("pid", ["scientific_kg", "knowledge_graphs"])
def test_scientific_kg_preset_uses_domain_schema(pid: str) -> None:
    """El preset del dominio KG gatea a predicados semánticos, no al genérico RELATED_TO."""
    p = PresetOntologyResolver().resolve(pid)
    assert p.profile_id == "scientific_kg"
    # Nodos de dominio (métodos/modelos/tareas...), no Person/Concept genéricos.
    assert {"Method", "Model", "Task", "Dataset", "Metric"} <= set(p.allowed_nodes)
    # Predicados con carga semántica presentes; RELATED_TO NO es el vocabulario.
    assert {"PROPOSES", "USES", "EVALUATED_ON", "OUTPERFORMS", "RETRIEVES_FROM"} <= set(
        p.allowed_relationships
    )
    assert "RELATED_TO" not in p.allowed_relationships
