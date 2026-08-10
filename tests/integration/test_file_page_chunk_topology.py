"""Neo4j integration: FILE_PAGE_CHUNK counts and NEXT_CHUNK scoping."""

from __future__ import annotations

from pathlib import Path

import pytest

from ungraph.application.dependencies import create_ingest_document_use_case
from ungraph.utils.graph_topology_validate import run_file_page_chunk_checks

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _count_nodes(session, label: str) -> int:
    allowed = {"File", "Page", "Chunk"}
    if label not in allowed:
        raise ValueError(label)
    q = f"MATCH (n:{label}) RETURN count(n) AS c"
    return int(
        session.execute_read(lambda tx: tx.run(q).single()["c"])
    )


def test_two_documents_topology_and_next_chunk_scope(neo4j_clean_bundle):
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]
    settings = neo4j_clean_bundle["settings"]

    uid_a = "11111111-1111-1111-1111-111111111111"
    uid_b = "22222222-2222-2222-2222-222222222222"

    uc = create_ingest_document_use_case(
        settings=settings,
        database=database,
    )
    uc.execute(
        FIXTURES / "topology_alpha.md",
        chunk_size=4000,
        chunk_overlap=0,
        clean_text=True,
        source_document_uid=uid_a,
    )
    uc.execute(
        FIXTURES / "topology_beta.md",
        chunk_size=4000,
        chunk_overlap=0,
        clean_text=True,
        source_document_uid=uid_b,
    )

    with driver.session(database=database) as session:
        assert _count_nodes(session, "File") == 2
        assert _count_nodes(session, "Page") == 2
        n_chunks = _count_nodes(session, "Chunk")
        assert n_chunks >= 2

    rep = run_file_page_chunk_checks(
        driver,
        database,
        source_document_uid=uid_a,
        min_chunks=1,
    )
    assert rep.ok, rep.issues
    rep_b = run_file_page_chunk_checks(driver, database, source_document_uid=uid_b, min_chunks=1)
    assert rep_b.ok, rep_b.issues

    cross = run_file_page_chunk_checks(driver, database)
    assert cross.ok, cross.issues
