"""
Fixtures compartidas: Neo4j para integration / e2e.

Las pruebas unitarias no dependen de este módulo.

Los ``test_*.py`` en la raíz de ``tests/`` que aún importan ``domain.*`` / ``src.*``
no están migrados al paquete ``ungraph``; quedan fuera de la recolección
hasta portarlos (lista ``collect_ignore`` en este archivo).
"""

from __future__ import annotations

import pytest
from neo4j import GraphDatabase

from ungraph.core.configuration import get_settings, reset_configuration
from ungraph.infrastructure.services.neo4j_index_service import Neo4jIndexService

# Tests en la raíz aún no migrados de ``src/`` + ``domain.*`` al paquete ``ungraph``.
collect_ignore = [
    "test_advanced_search_integration.py",
    "test_advanced_search_patterns.py",
    "test_chunking_service_smart.py",
    "test_domain_entities.py",
    "test_eti_pipeline_e2e.py",
    "test_graph_patterns.py",
    "test_graphrag_search_patterns.py",
    "test_inference_service.py",
    "test_infrastructure_services.py",
    "test_integration_real.py",
    "test_llm_inference_integration.py",
    "test_llm_inference_service.py",
    "test_pattern_service.py",
    "test_phase2_integration.py",
    "test_phase3_integration.py",
    "test_predefined_patterns.py",
    "test_unit_complete.py",
    "test_use_case_integration.py",
]


@pytest.fixture
def neo4j_clean_bundle():
    """
    Conexión Neo4j + settings + grafo vacío al inicio y al final del test.

    Omite el test si no hay credenciales o el servidor no responde.
    """
    reset_configuration()
    settings = get_settings()
    uri = settings.neo4j_uri
    password = settings.neo4j_password
    user = settings.neo4j_user or "neo4j"
    database = settings.neo4j_database or "neo4j"

    if not uri or not password:
        pytest.skip("Define UNGRAPH_NEO4J_URI y UNGRAPH_NEO4J_PASSWORD (o NEO4J_*) para integration/e2e.")

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
    except Exception as exc:  # noqa: BLE001 — queremos skip legible
        driver.close()
        pytest.skip(f"Neo4j no disponible: {exc}")

    cleaner = Neo4jIndexService(database=database)
    try:
        cleaner.clean_graph()
    finally:
        cleaner.close()

    bundle = {
        "driver": driver,
        "database": database,
        "settings": settings,
    }
    yield bundle

    fin = Neo4jIndexService(database=database)
    try:
        fin.clean_graph()
    finally:
        fin.close()
    driver.close()
    reset_configuration()
