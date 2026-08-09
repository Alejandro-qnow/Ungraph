"""Unit: loader pandas (usa el corpus de fixtures; skip si falta pandas)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

pd = pytest.importorskip("pandas")

from ungraph.infrastructure.services.pandas_tabular_loader_service import (  # noqa: E402
    PandasTabularLoaderService,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "tabular"


@pytest.fixture(scope="module")
def loader() -> PandasTabularLoaderService:
    return PandasTabularLoaderService()


def test_supports():
    ld = PandasTabularLoaderService()
    assert ld.supports(Path("x.csv"))
    assert ld.supports(Path("x.xlsx"))
    assert not ld.supports(Path("x.pdf"))


def test_load_csv_normalizes_nulls(loader, tmp_path):
    csv = tmp_path / "t.csv"
    csv.write_text("a,b\n1,\n2,x\n", encoding="utf-8")
    tables = loader.load(csv)
    assert len(tables) == 1
    t = tables[0]
    assert t.columns == ["a", "b"]
    assert t.rows[0]["b"] is None  # celda vacía → None (no NaN)


@pytest.mark.skipif(not (FIXTURES / "orders_fk.csv").exists(), reason="corpus no generado")
def test_load_corpus_csv(loader):
    tables = loader.load(FIXTURES / "orders_fk.csv")
    assert len(tables) == 1
    assert tables[0].n_rows == 80


@pytest.mark.skipif(not (FIXTURES / "shop_relational.xlsx").exists(), reason="corpus no generado")
def test_load_xlsx_multisheet(loader):
    tables = loader.load(FIXTURES / "shop_relational.xlsx")
    names = {t.name for t in tables}
    assert {"customers", "products", "orders", "order_items"} <= names
