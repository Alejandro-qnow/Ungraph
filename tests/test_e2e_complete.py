"""
End-to-end: ingest → persist → text search on Neo4j.

Requires the same env as integration tests (see tests/conftest.py).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ungraph.application.dependencies import create_ingest_document_use_case
from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService
from ungraph.utils.graph_topology_validate import run_file_page_chunk_checks

pytestmark = pytest.mark.e2e

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_ingest_small_doc_then_fulltext_search(neo4j_clean_bundle):
    """Full lexical pipeline smoke: chunks in DB + full-text index query returns hits."""
    database = neo4j_clean_bundle["database"]
    settings = neo4j_clean_bundle["settings"]
    driver = neo4j_clean_bundle["driver"]

    uid = "e2e-aaaa-bbbb-cccc-ddddeeee1111"

    uc = create_ingest_document_use_case(settings=settings, database=database)
    uc.execute(
        FIXTURES / "topology_alpha.md",
        chunk_size=4000,
        chunk_overlap=0,
        clean_text=True,
        source_document_uid=uid,
    )

    topo = run_file_page_chunk_checks(
        driver,
        database,
        source_document_uid=uid,
        min_chunks=1,
    )
    assert topo.ok, topo.issues

    search = Neo4jSearchService(database=database)
    try:
        results = search.text_search("topology", limit=5)
    except Exception as ex:
        pytest.fail(f"text_search failed (indexes may be missing): {ex!r}")
    finally:
        search.close()

    assert isinstance(results, list)
    assert len(results) >= 1
    assert results[0].content and len(results[0].content.strip()) > 0
