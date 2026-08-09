"""Unit: value objects de esquema tabular (sin dependencias externas)."""

from __future__ import annotations

import pytest

from ungraph.domain.value_objects.document_type import DocumentType
from ungraph.domain.value_objects.tabular_schema import (
    ColumnMapping,
    ColumnRole,
    TabularSchemaProposal,
    sanitize_label,
    sanitize_property,
    sanitize_relationship_type,
)

pytestmark = pytest.mark.unit


def test_document_type_detects_tabular():
    assert DocumentType.from_filename("data.csv") == DocumentType.CSV
    assert DocumentType.from_filename("data.XLSX") == DocumentType.XLSX
    assert DocumentType.from_filename("legacy.xls") == DocumentType.XLSX
    assert DocumentType.is_tabular(DocumentType.CSV)
    assert not DocumentType.is_tabular(DocumentType.PDF)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("order id", "OrderId"),
        ("país", "PaS"),  # la 'í' no-ASCII separa tokens (determinista; el usuario puede editar)
        ("123col", "N123col"),
        ("customer_id", "CustomerId"),
    ],
)
def test_sanitize_label(raw, expected):
    label = sanitize_label(raw)
    assert label[0].isupper()
    assert label == expected


def test_sanitize_property_and_relationship():
    assert sanitize_property("Monto (USD)") == "monto_usd"
    assert sanitize_property("") == "value"
    assert sanitize_relationship_type("has customer") == "HAS_CUSTOMER"
    assert sanitize_relationship_type("") == "RELATED_TO"


def test_column_mapping_resolvers():
    m = ColumnMapping(
        column="customer_id",
        role=ColumnRole.RELATION_FK,
        target_label="Customer",
        relationship_type="PLACED_BY",
    )
    assert m.resolved_target_label() == "Customer"
    assert m.resolved_relationship_type() == "PLACED_BY"
    assert m.resolved_target_key_property() == "customer_id"


def test_to_graph_pattern_structure():
    proposal = TabularSchemaProposal(
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
            ColumnMapping(
                column="country", role=ColumnRole.DIMENSION_NODE,
                target_label="Country", relationship_type="SHIPPED_TO",
            ),
            ColumnMapping(column="notes", role=ColumnRole.IGNORE),
        ],
    )
    gp = proposal.to_graph_pattern()
    labels = {n.label for n in gp.node_definitions}
    assert labels == {"Order", "Customer", "Country"}
    rels = {(r.from_node, r.relationship_type, r.to_node) for r in gp.relationship_definitions}
    assert ("Order", "PLACED_BY", "Customer") in rels
    assert ("Order", "SHIPPED_TO", "Country") in rels
    # order_id es clave requerida; amount opcional; notes ignorada.
    order = next(n for n in gp.node_definitions if n.label == "Order")
    assert "order_id" in order.required_properties
    assert "amount" in order.optional_properties
    assert "notes" not in order.optional_properties


def test_synthetic_key_when_no_row_key():
    proposal = TabularSchemaProposal(
        source="t", row_node_label="T", row_key_columns=[],
        columns=[ColumnMapping(column="x", role=ColumnRole.ATTRIBUTE)],
    )
    assert proposal.row_key_property_names() == ["row_uid"]
    gp = proposal.to_graph_pattern()  # no debe lanzar
    row = next(n for n in gp.node_definitions if n.label == "T")
    assert "row_uid" in row.required_properties


def test_proposal_dict_roundtrip():
    proposal = TabularSchemaProposal(
        source="orders",
        row_node_label="Order",
        row_key_columns=["order_id"],
        columns=[
            ColumnMapping(column="order_id", role=ColumnRole.NODE_KEY, confidence=0.95),
            ColumnMapping(
                column="country", role=ColumnRole.DIMENSION_NODE,
                target_label="Country", relationship_type="SHIPPED_TO", confidence=0.8,
            ),
        ],
    )
    restored = TabularSchemaProposal.from_dict(proposal.to_dict())
    assert restored.to_dict() == proposal.to_dict()
    assert restored.columns[1].role == ColumnRole.DIMENSION_NODE
