"""Unit: perfilado y clasificación heurística + desambiguación LLM (mock)."""

from __future__ import annotations

import pytest

from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import ColumnRole
from ungraph.infrastructure.services.heuristic_schema_inference_service import (
    HeuristicSchemaInferenceService,
)
from ungraph.infrastructure.services.llm_schema_inference_service import (
    LlmSchemaInferenceService,
)

pytestmark = pytest.mark.unit


def _orders_table(n: int = 60) -> TabularData:
    rows = []
    for i in range(1, n + 1):
        rows.append(
            {
                "order_id": i,
                "customer_id": 100 + (i % 12),
                "amount": 10.5 * i,
                "order_date": "2024-01-%02d" % ((i % 28) + 1),
                "country": ["CO", "US", "MX"][i % 3],
                "status": ["paid", "pending"][i % 2],
            }
        )
    return TabularData(name="orders", columns=list(rows[0].keys()), rows=rows)


def test_profile_computes_cardinality_and_nulls():
    table = TabularData(
        name="t",
        columns=["a", "b"],
        rows=[{"a": 1, "b": None}, {"a": 1, "b": "x"}, {"a": 2, "b": "x"}],
    )
    profiles = {p.name: p for p in HeuristicSchemaInferenceService().profile(table)}
    assert profiles["a"].cardinality == 2
    assert profiles["b"].null_ratio == pytest.approx(1 / 3, rel=1e-3)


def test_heuristic_classifies_roles():
    table = _orders_table()
    svc = HeuristicSchemaInferenceService()
    proposal = svc.propose_schema(table, svc.profile(table))
    roles = {c.column: c.role for c in proposal.columns}
    assert proposal.row_key_columns == ["order_id"]
    assert roles["order_id"] == ColumnRole.NODE_KEY
    assert roles["customer_id"] == ColumnRole.RELATION_FK
    assert roles["amount"] == ColumnRole.ATTRIBUTE
    assert roles["order_date"] == ColumnRole.ATTRIBUTE
    assert roles["country"] == ColumnRole.DIMENSION_NODE
    assert roles["status"] == ColumnRole.DIMENSION_NODE


def test_fk_target_label_derivation():
    table = TabularData(
        name="t", columns=["t_id", "physician_id"],
        rows=[{"t_id": i, "physician_id": i % 3} for i in range(1, 30)],
    )
    svc = HeuristicSchemaInferenceService()
    proposal = svc.propose_schema(table, svc.profile(table))
    fk = next(c for c in proposal.columns if c.column == "physician_id")
    assert fk.role == ColumnRole.RELATION_FK
    assert fk.resolved_target_label() == "Physician"


class _FakeLLM:
    """LLM de prueba que devuelve una decisión JSON fija."""

    def __init__(self, content: str):
        self._content = content
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1

        class _Resp:
            content = self._content

        return _Resp()


def test_llm_fallback_without_client_equals_heuristic():
    table = _orders_table()
    heur = HeuristicSchemaInferenceService()
    base = heur.propose_schema(table, heur.profile(table))
    hybrid = LlmSchemaInferenceService(heuristic=heur, llm=None)
    out = hybrid.propose_schema(table, hybrid.profile(table))
    assert out.to_dict() == base.to_dict()


def test_llm_disambiguates_low_confidence_column():
    # Tabla con una columna ambigua (string, cardinalidad media, sin señal id/fecha).
    rows = []
    for i in range(1, 41):
        rows.append({"id": i, "label": f"grp{i % 8}"})  # 8 grupos: baja confianza
    table = TabularData(name="t", columns=["id", "label"], rows=rows)
    heur = HeuristicSchemaInferenceService()
    llm = _FakeLLM('{"decisions":[{"column":"label","role":"dimension","target_label":"Label","relationship_type":"HAS_LABEL","rationale":"categoría"}]}')
    hybrid = LlmSchemaInferenceService(heuristic=heur, llm=llm, confidence_threshold=0.95)
    out = hybrid.propose_schema(table, hybrid.profile(table))
    label = next(c for c in out.columns if c.column == "label")
    assert llm.calls == 1
    assert label.role == ColumnRole.DIMENSION_NODE
    assert label.decided_by == "llm"


def test_llm_error_falls_back_to_heuristic():
    class _BoomLLM:
        def invoke(self, messages):
            raise RuntimeError("boom")

    table = _orders_table()
    heur = HeuristicSchemaInferenceService()
    base = heur.propose_schema(table, heur.profile(table))
    hybrid = LlmSchemaInferenceService(heuristic=heur, llm=_BoomLLM(), confidence_threshold=1.0)
    out = hybrid.propose_schema(table, hybrid.profile(table))
    # ante error del LLM, se conserva la propuesta heurística
    assert {c.column: c.role for c in out.columns} == {c.column: c.role for c in base.columns}
