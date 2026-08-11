"""Tests: normalización de tipos de relación inferidos para Neo4j."""

import pytest

from ungraph.utils.neo4j_infer_reltype import (
    EXTRACTED_REL_FALLBACK,
    native_neo4j_relationship_type,
)

pytestmark = pytest.mark.unit


def test_native_works_for():
    t, native = native_neo4j_relationship_type("WORKS_FOR")
    assert native and t == "WORKS_FOR"


def test_native_normalizes_spaces_and_case():
    t, native = native_neo4j_relationship_type("works for")
    assert native and t == "WORKS_FOR"


def test_fallback_on_invalid():
    t, native = native_neo4j_relationship_type("123_ILLEGAL")
    assert not native and t == EXTRACTED_REL_FALLBACK


def test_fallback_empty():
    t, native = native_neo4j_relationship_type("")
    assert not native and t == EXTRACTED_REL_FALLBACK
