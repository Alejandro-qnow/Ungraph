"""Integration/e2e: persistencia tabular en Neo4j (requiere Neo4j).

Usa la fixture ``neo4j_clean_bundle`` (skip si no hay servidor). Verifica:
- nodos/relaciones creados según el mapeo,
- idempotencia (re-ingesta no duplica),
- consultabilidad (join FK, agregación por dimensión),
- flujo e2e del use case (dry-run + apply con mapeo confirmado).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

pd = pytest.importorskip("pandas")

from ungraph.application.use_cases.ingest_tabular import IngestTabularUseCase  # noqa: E402
from ungraph.domain.value_objects.tabular_data import TabularData  # noqa: E402
from ungraph.domain.value_objects.tabular_schema import (  # noqa: E402
    ColumnMapping,
    ColumnRole,
    TabularSchemaProposal,
)
from ungraph.infrastructure.repositories.neo4j_tabular_repository import (  # noqa: E402
    Neo4jTabularRepository,
)
from ungraph.infrastructure.services.heuristic_schema_inference_service import (  # noqa: E402
    HeuristicSchemaInferenceService,
)
from ungraph.infrastructure.services.pandas_tabular_loader_service import (  # noqa: E402
    PandasTabularLoaderService,
)


def _orders_table(n: int = 30) -> TabularData:
    rows = []
    for i in range(1, n + 1):
        rows.append(
            {
                "order_id": i,
                "customer_id": 100 + (i % 5),
                "amount": 10.0 * i,
                "country": ["CO", "US", "MX"][i % 3],
            }
        )
    return TabularData(name="orders_it", columns=list(rows[0].keys()), rows=rows)


def _orders_proposal() -> TabularSchemaProposal:
    return TabularSchemaProposal(
        source="orders_it",
        row_node_label="OrderIt",
        row_key_columns=["order_id"],
        columns=[
            ColumnMapping(column="order_id", role=ColumnRole.NODE_KEY),
            ColumnMapping(column="amount", role=ColumnRole.ATTRIBUTE),
            ColumnMapping(
                column="customer_id", role=ColumnRole.RELATION_FK,
                target_label="CustomerIt", relationship_type="PLACED_BY",
            ),
            ColumnMapping(
                column="country", role=ColumnRole.DIMENSION_NODE,
                target_label="CountryIt", relationship_type="SHIPPED_TO",
            ),
        ],
    )


def _count(driver, database, cypher) -> int:
    with driver.session(database=database) as s:
        return s.run(cypher).single()[0]


def test_save_tabular_creates_nodes_and_relations(neo4j_clean_bundle):
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]
    repo = Neo4jTabularRepository(database=database)
    try:
        stats = repo.save_tabular(_orders_proposal(), _orders_table())
    finally:
        repo.close()

    assert stats["rows_persisted"] == 30
    assert _count(driver, database, "MATCH (n:OrderIt) RETURN count(n)") == 30
    # 5 clientes distintos (100..104), 3 países
    assert _count(driver, database, "MATCH (c:CustomerIt) RETURN count(c)") == 5
    assert _count(driver, database, "MATCH (c:CountryIt) RETURN count(c)") == 3
    assert _count(
        driver, database, "MATCH (:OrderIt)-[:PLACED_BY]->(:CustomerIt) RETURN count(*)"
    ) == 30
    # provenance
    assert _count(
        driver, database, "MATCH (:TabularSource)-[:HAS_ROW]->(:OrderIt) RETURN count(*)"
    ) == 30


def test_reingestion_is_idempotent(neo4j_clean_bundle):
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]
    repo = Neo4jTabularRepository(database=database)
    try:
        repo.save_tabular(_orders_proposal(), _orders_table())
        repo.save_tabular(_orders_proposal(), _orders_table())  # segunda vez
    finally:
        repo.close()
    assert _count(driver, database, "MATCH (n:OrderIt) RETURN count(n)") == 30
    assert _count(driver, database, "MATCH (c:CustomerIt) RETURN count(c)") == 5


def test_queryability_aggregation_by_dimension(neo4j_clean_bundle):
    driver = neo4j_clean_bundle["driver"]
    database = neo4j_clean_bundle["database"]
    repo = Neo4jTabularRepository(database=database)
    try:
        repo.save_tabular(_orders_proposal(), _orders_table())
    finally:
        repo.close()
    # agregación por dimensión país (amount coercionado a número)
    with driver.session(database=database) as s:
        rows = s.run(
            "MATCH (o:OrderIt)-[:SHIPPED_TO]->(c:CountryIt) "
            "RETURN c.country AS country, sum(o.amount) AS total ORDER BY country"
        ).data()
    assert len(rows) == 3
    assert all(isinstance(r["total"], (int, float)) for r in rows)


def test_use_case_dry_run_then_apply(neo4j_clean_bundle, tmp_path):
    database = neo4j_clean_bundle["database"]
    driver = neo4j_clean_bundle["driver"]
    csv = tmp_path / "orders_it.csv"
    pd.DataFrame(_orders_table().rows).to_csv(csv, index=False)

    uc = IngestTabularUseCase(
        PandasTabularLoaderService(),
        HeuristicSchemaInferenceService(),
        Neo4jTabularRepository(database=database),
    )
    # dry-run: propone, no escribe
    dry = uc.execute(csv, dry_run=True)
    assert dry.persisted is False
    assert _count(driver, database, "MATCH (n) RETURN count(n)") == 0

    # apply con la propuesta confirmada
    applied = uc.execute(csv, dry_run=False, mappings=dry.proposals)
    assert applied.persisted is True
    assert _count(driver, database, "MATCH (n:OrdersIt) RETURN count(n)") == 30
