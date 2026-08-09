"""Unit: fachada ``ungraph.reasoning.ingest_tabular`` (dry-run, sin Neo4j).

El dry-run infiere el esquema heurísticamente y devuelve un dict serializable SIN
tocar la base (el driver del repositorio es perezoso). Cubre el contrato que consume
la capa MCP/API pública.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import ungraph
from ungraph import reasoning

pytestmark = pytest.mark.unit

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "tabular" / "orders_fk.csv"


def test_facade_is_exported():
    assert callable(reasoning.ingest_tabular)
    assert "ingest_tabular" in reasoning.__all__
    # Re-exportada también en la API pública de alto nivel.
    assert callable(ungraph.ingest_tabular)
    assert "ingest_tabular" in ungraph.__all__


def test_dry_run_returns_serializable_proposal():
    result = reasoning.ingest_tabular(str(_FIXTURE), apply=False, use_llm=False)

    # Contrato del dict de salida.
    assert result["persisted"] is False
    assert result["stats"] == []
    assert result["file_path"] == str(_FIXTURE)
    assert len(result["proposals"]) == 1

    proposal = result["proposals"][0]
    assert proposal["source"] == "orders_fk"
    assert proposal["row_key_columns"] == ["order_id"]
    roles = {c["column"]: c["role"] for c in proposal["columns"]}
    assert roles["order_id"] == "node_key"
    assert roles["customer_id"] == "relation_fk"

    # Debe ser JSON-serializable (lo consume MCP).
    json.dumps(result, ensure_ascii=False)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        reasoning.ingest_tabular("does/not/exist.csv", apply=False, use_llm=False)


def test_public_api_delegates_to_facade():
    via_public = ungraph.ingest_tabular(str(_FIXTURE), apply=False, use_llm=False)
    via_facade = reasoning.ingest_tabular(str(_FIXTURE), apply=False, use_llm=False)
    assert via_public["proposals"] == via_facade["proposals"]
