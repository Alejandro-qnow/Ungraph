"""
Integration: lexical graph topology after ingest (NEXT_CHUNK scoped by source_document_uid).

Requires Neo4j (same env as tests/conftest neo4j_clean_bundle). No LLM.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ungraph.application.dependencies import create_ingest_document_use_case
from ungraph.utils.graph_topology_validate import (
    run_file_page_chunk_checks,
    validate_next_chunk_same_document_scope,
)

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_two_documents_no_cross_document_next_chunk(neo4j_clean_bundle):
    """Two ingests with distinct UIDs must not link NEXT_CHUNK across documents."""
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]
    settings = neo4j_clean_bundle["settings"]

    uid_a = "topo-int-aaaaaaaa-aaaa-aaaa-aaaaaaaaaaaa"
    uid_b = "topo-int-bbbbbbbb-bbbb-bbbb-bbbbbbbbbbbb"

    uc = create_ingest_document_use_case(settings=settings, database=database)
    uc.execute(
        FIXTURES / "topology_alpha.md",
        chunk_size=2000,
        chunk_overlap=0,
        clean_text=True,
        source_document_uid=uid_a,
    )
    uc.execute(
        FIXTURES / "topology_alpha.md",
        chunk_size=2000,
        chunk_overlap=0,
        clean_text=True,
        source_document_uid=uid_b,
    )

    r_scope = validate_next_chunk_same_document_scope(driver, database)
    assert r_scope.ok, r_scope.issues

    ra = run_file_page_chunk_checks(
        driver, database, source_document_uid=uid_a, min_chunks=1
    )
    assert ra.ok, ra.issues
    rb = run_file_page_chunk_checks(
        driver, database, source_document_uid=uid_b, min_chunks=1
    )
    assert rb.ok, rb.issues
