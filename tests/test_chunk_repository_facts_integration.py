"""Integración: ChunkRepository y hechos derivados."""

from __future__ import annotations

import pytest

from ungraph.infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository

pytestmark = pytest.mark.integration


def test_list_chunk_ids_without_derived_facts(neo4j_clean_bundle) -> None:
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]

    with driver.session(database=database) as session:
        session.run(
            """
            CREATE (c1:Chunk {
              chunk_id: 'pending-1',
              page_content: 'hello world',
              filename: 'f.md',
              page_number: 1
            })
            CREATE (c2:Chunk {
              chunk_id: 'with-fact',
              page_content: 'also text',
              filename: 'f.md',
              page_number: 1
            })
            CREATE (f:Fact {
              fact_id: 'fact-int-1',
              subject: 's',
              predicate: 'MENTIONS',
              object: 'o',
              confidence: 0.9,
              provenance_ref: 'with-fact'
            })
            CREATE (f)-[:DERIVED_FROM]->(c2)
            """
        )

    repo = Neo4jChunkRepository(database=database)
    try:
        ids = repo.list_chunk_ids_without_derived_facts(min_content_chars=1)
        assert "pending-1" in ids
        assert "with-fact" not in ids
    finally:
        repo.close()


def test_save_relations_creates_extracted_rel(neo4j_clean_bundle) -> None:
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]

    with driver.session(database=database) as session:
        session.run(
            """
            CREATE (:Entity {name: 'Alice', type: 'Person'})
            CREATE (:Entity {name: 'Acme', type: 'Organization'})
            """
        )

    from ungraph.domain.entities.relation import Relation

    rel = Relation(
        id="rel_integration_1",
        source_entity_id="e1",
        target_entity_id="e2",
        relation_type="WORKS_FOR",
        confidence=0.88,
        provenance_ref="rk1",
        source_entity_name="Alice",
        target_entity_name="Acme",
    )
    repo = Neo4jChunkRepository(database=database)
    try:
        repo.save_relations([rel])
        with driver.session(database=database) as session:
            row = session.run(
                """
                MATCH (a:Entity {name: 'Alice'})-[r:WORKS_FOR {relation_id: $rid}]->(b:Entity {name: 'Acme'})
                RETURN r.relation_type AS t, r.confidence AS c
                """,
                rid="rel_integration_1",
            ).single()
            assert row is not None
            assert row["t"] == "WORKS_FOR"
            assert row["c"] == 0.88
    finally:
        repo.close()


def test_collect_structural_graph_stats_counts(neo4j_clean_bundle) -> None:
    from ungraph.evaluation.graph_structural_stats import collect_structural_graph_stats

    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]
    with driver.session(database=database) as session:
        session.run(
            """
            CREATE (:Chunk {chunk_id: 's1'}), (:Chunk {chunk_id: 's2'})
            CREATE (a:Entity {name: 'x'}), (b:Entity {name: 'y'})
            MERGE (a)-[:EXTRACTED_REL {relation_id: 'r-stat-1'}]->(b)
            """
        )
    stats = collect_structural_graph_stats(driver, database=database)
    assert stats.node_counts_by_label.get("Chunk") == 2
    assert stats.node_counts_by_label.get("Entity") == 2
    assert stats.relationship_counts_by_type.get("EXTRACTED_REL") == 1


def test_entity_merge_reroutes_native_works_for(neo4j_clean_bundle) -> None:
    from ungraph.infrastructure.services.neo4j_entity_maintenance_service import (
        Neo4jEntityGraphMaintenanceService,
    )

    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]
    with driver.session(database=database) as session:
        session.run(
            """
            CREATE (keep:Entity {name: 'Same'})
            CREATE (dup:Entity {name: 'same'})
            CREATE (acme:Entity {name: 'Acme'})
            CREATE (dup)-[:WORKS_FOR {relation_id: 'r-merge-1', confidence: 0.8}]->(acme)
            """
        )
    svc = Neo4jEntityGraphMaintenanceService(database=database)
    merged = svc.consolidate_entities_case_insensitive()
    assert merged >= 1
    with driver.session(database=database) as session:
        c = session.run(
            """
            MATCH (e:Entity)-[r:WORKS_FOR]->(a:Entity {name: 'Acme'})
            WHERE toLower(trim(toString(e.name))) = 'same'
            RETURN count(r) AS c
            """
        ).single()["c"]
        assert c == 1
        dup_nodes = session.run(
            "MATCH (e:Entity) WHERE toLower(trim(toString(e.name))) = 'same' RETURN count(e) AS c"
        ).single()["c"]
        assert dup_nodes == 1
