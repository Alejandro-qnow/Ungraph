"""Pruebas unitarias del filtro de calidad de entidades (value object de dominio)."""

from __future__ import annotations

import pytest

from ungraph.domain.value_objects.entity_quality import (
    filter_low_value_entities,
    is_low_value_entity_name,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "name",
    [
        "2404.16130",   # id arXiv (sin letras)
        "1 Million",    # cantidad
        "1,000",        # numérico con coma
        "2022",         # año
        "two",          # palabra-número
        "First",        # ordinal
        "3rd",          # ordinal numérico
        "10%",          # porcentaje
        "##",           # artefacto markdown
        "---",          # solo símbolos
        "A",            # demasiado corto
        "   ",          # vacío
    ],
)
def test_low_value_names_are_noise(name: str) -> None:
    assert is_low_value_entity_name(name) is True


@pytest.mark.parametrize(
    "name",
    [
        "GraphRAG",
        "RAG",
        "LLM",
        "GPT-4",                        # letra + número → válido
        "Query-Focused Summarization",
        "Darren Edge",                  # persona
        "Neo4j",
        "Section 3",                    # token no numérico presente
        "COVID-19",
    ],
)
def test_meaningful_names_are_kept(name: str) -> None:
    assert is_low_value_entity_name(name) is False


def test_filter_low_value_entities_on_objects() -> None:
    class _E:
        def __init__(self, name: str) -> None:
            self.name = name

    items = [_E("GraphRAG"), _E("1 Million"), _E("LLM"), _E("2404.16130"), _E("two")]
    kept = filter_low_value_entities(items)
    assert [e.name for e in kept] == ["GraphRAG", "LLM"]
