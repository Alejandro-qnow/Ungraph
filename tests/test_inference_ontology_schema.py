"""Esquema LLM desde OntologyResolver / presets."""

from __future__ import annotations

import pytest

from ungraph.application.dependencies import _inference_llm_allowed_schema
from ungraph.core.configuration import Settings

pytestmark = pytest.mark.unit


def test_inference_llm_schema_uses_general_preset() -> None:
    nodes, rels = _inference_llm_allowed_schema(
        Settings(inference_ontology_profile_id="general")
    )
    assert "Person" in nodes
    assert "WORKS_FOR" in rels


def test_inference_llm_schema_minimal() -> None:
    nodes, rels = _inference_llm_allowed_schema(
        Settings(inference_ontology_profile_id="minimal")
    )
    assert nodes == ["Entity"]
    assert rels == ["RELATED_TO"]
