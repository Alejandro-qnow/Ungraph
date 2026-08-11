"""Integración: fusión de nodos :Entity (infer --consolidate / --resolve)."""

from __future__ import annotations

import pytest

from ungraph.infrastructure.services.neo4j_entity_maintenance_service import (
    Neo4jEntityGraphMaintenanceService,
)

pytestmark = pytest.mark.integration


def test_consolidate_merges_case_insensitive_entities(neo4j_clean_bundle) -> None:
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]

    with driver.session(database=database) as session:
        session.run(
            """
            CREATE (c:Chunk {chunk_id: 'eg-int-chunk', page_content: 'x', filename: 'f', page_number: 1})
            CREATE (e1:Entity {name: 'Acme'})
            CREATE (e2:Entity {name: 'acme'})
            CREATE (c)-[:MENTIONS]->(e2)
            """
        )

    svc = Neo4jEntityGraphMaintenanceService(database=database)
    removed = svc.consolidate_entities_case_insensitive()
    assert removed >= 1

    with driver.session(database=database) as session:
        n_ent = session.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
        n_ment = session.run(
            "MATCH (:Chunk {chunk_id:'eg-int-chunk'})-[:MENTIONS]->(:Entity) RETURN count(*) AS c"
        ).single()["c"]
    assert n_ent == 1
    assert n_ment >= 1


def test_resolve_merges_punctuation_variant(neo4j_clean_bundle) -> None:
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]

    with driver.session(database=database) as session:
        session.run(
            """
            CREATE (c:Chunk {chunk_id: 'eg-int-chunk2', page_content: 'x', filename: 'f', page_number: 1})
            CREATE (e1:Entity {name: 'Foo'})
            CREATE (e2:Entity {name: 'Foo.'})
            CREATE (c)-[:MENTIONS]->(e2)
            """
        )

    svc = Neo4jEntityGraphMaintenanceService(database=database)
    svc.consolidate_entities_case_insensitive()
    removed = svc.resolve_entities_strip_punctuation()
    assert removed >= 1

    with driver.session(database=database) as session:
        n_ent = session.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
    assert n_ent == 1
