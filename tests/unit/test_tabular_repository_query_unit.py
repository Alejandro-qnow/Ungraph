"""Unit: generación de Cypher/parámetros del repositorio tabular (sin Neo4j)."""

from __future__ import annotations

import pytest

from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import (
    ColumnMapping,
    ColumnRole,
    TabularSchemaProposal,
)
from ungraph.infrastructure.repositories.neo4j_tabular_repository import (
    Neo4jTabularRepository,
    _coerce_scalar,
)

pytestmark = pytest.mark.unit


def _proposal() -> TabularSchemaProposal:
    return TabularSchemaProposal(
        source="orders",
        row_node_label="Order",
        row_key_columns=["order_id"],
        columns=[
            ColumnMapping(column="order_id", role=ColumnRole.NODE_KEY),
            ColumnMapping(column="amount", role=ColumnRole.ATTRIBUTE),
            ColumnMapping(
                column="customer_id", role=ColumnRole.RELATION_FK,
                target_label="Customer", relationship_type="PLACED_BY",
            ),
        ],
    )


def test_coerce_scalar():
    assert _coerce_scalar("5") == 5
    assert _coerce_scalar("5.5") == 5.5
    assert _coerce_scalar("abc") == "abc"
    assert _coerce_scalar(None) is None
    assert _coerce_scalar("") is None


def test_build_query_uses_unwind_merge_and_foreach():
    repo = Neo4jTabularRepository()
    query, param_keys = repo._build_query(_proposal())
    assert "UNWIND $rows AS row" in query
    assert "MERGE (n:`Order` {`order_id`: row.`order_id`})" in query
    assert "MERGE (src)-[:`HAS_ROW`]->(n)" in query
    # FK como FOREACH que salta nulos
    assert "FOREACH" in query and "`Customer`" in query and "PLACED_BY" in query
    assert set(param_keys) >= {"order_id", "amount", "customer_id"}


def test_build_rows_params_coerces_attrs_keeps_keys_as_str():
    repo = Neo4jTabularRepository()
    proposal = _proposal()
    _, param_keys = repo._build_query(proposal)
    table = TabularData(
        name="orders",
        columns=["order_id", "amount", "customer_id"],
        rows=[{"order_id": 1, "amount": "5.0", "customer_id": 10}],
    )
    params = repo._build_rows_params(proposal, table, param_keys)[0]
    assert params["order_id"] == "1"        # clave: string estable
    assert params["customer_id"] == "10"    # FK: string estable
    assert params["amount"] == 5.0          # atributo: coercionado a float


def test_constraints_include_unique_for_row_and_targets():
    repo = Neo4jTabularRepository()
    stmts = "\n".join(repo._constraint_statements(_proposal()))
    assert "TabularSource" in stmts
    assert "`Order`" in stmts and "IS UNIQUE" in stmts
    assert "`Customer`" in stmts


def test_synthetic_uid_stable_and_included_when_no_key():
    repo = Neo4jTabularRepository()
    proposal = TabularSchemaProposal(
        source="t", row_node_label="T", row_key_columns=[],
        columns=[ColumnMapping(column="x", role=ColumnRole.ATTRIBUTE)],
    )
    query, param_keys = repo._build_query(proposal)
    assert "`row_uid`: row.`row_uid`" in query
    table = TabularData(name="t", columns=["x"], rows=[{"x": "a"}])
    params = repo._build_rows_params(proposal, table, param_keys)[0]
    uid1 = params["row_uid"]
    uid2 = repo._build_rows_params(proposal, table, param_keys)[0]["row_uid"]
    assert uid1 == uid2  # determinista → idempotencia
