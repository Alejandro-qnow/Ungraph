"""
Implementación: Neo4jTabularRepository

Persiste datos tabulares en Neo4j a partir de una ``TabularSchemaProposal``. Genera un
único query ``UNWIND $rows AS row ... MERGE ...`` por tabla (eficiente y por lotes) con
parámetros calificados por columna para evitar colisiones cuando dos nodos comparten un
nombre de propiedad.

Modelo resultante (ver skill kg-schema):
- (:TabularSource)-[:HAS_ROW]->(:<RowLabel>)  # provenance
- (:<RowLabel> {claves + atributos})
- (:<RowLabel>)-[:<REL>]->(:<Target>)         # dimensiones y FKs

Idempotencia: MERGE sobre claves naturales + constraints UNIQUE (``ensure_schema``).
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from ungraph.domain.repositories.tabular_repository import TabularRepository
from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import (
    ColumnMapping,
    ColumnRole,
    TabularSchemaProposal,
)

try:
    from ungraph.utils.graph_operations import graph_session
except ImportError as e:  # pragma: no cover
    logging.getLogger(__name__).error("Cannot import graph_operations: %s", e)
    raise

logger = logging.getLogger(__name__)

SOURCE_LABEL = "TabularSource"
HAS_ROW_REL = "HAS_ROW"


def _coerce_scalar(value: Any) -> Any:
    """Coerción best-effort de atributos a numérico para habilitar agregaciones.

    Solo se aplica a atributos (no a claves, que se mantienen como string para
    estabilidad del MERGE).
    """
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    s = str(value).strip()
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


class Neo4jTabularRepository(TabularRepository):
    """Persistencia tabular en Neo4j."""

    def __init__(self, database: str = "neo4j"):
        self.database = database
        self._driver = None

    def _get_driver(self) -> GraphDatabase:
        if self._driver is None:
            self._driver = graph_session()
        return self._driver

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None

    # ------------------------------------------------------------------ schema
    def ensure_schema(self, proposal: TabularSchemaProposal) -> None:
        stmts = self._constraint_statements(proposal)
        driver = self._get_driver()
        with driver.session(database=self.database) as session:
            for stmt in stmts:
                session.run(stmt)
        logger.info("Constraints aplicados: %s", len(stmts))

    def _constraint_statements(self, proposal: TabularSchemaProposal) -> List[str]:
        stmts: List[str] = [
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (s:`{SOURCE_LABEL}`) "
            f"REQUIRE s.source IS UNIQUE"
        ]
        row_label = proposal.resolved_row_label
        key_props = proposal.row_key_property_names()
        # Node key compuesta si hay >1 clave; UNIQUE simple si hay 1.
        if len(key_props) == 1:
            stmts.append(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:`{row_label}`) "
                f"REQUIRE n.`{key_props[0]}` IS UNIQUE"
            )
        elif len(key_props) > 1:
            key_list = ", ".join(f"n.`{k}`" for k in key_props)
            stmts.append(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:`{row_label}`) "
                f"REQUIRE ({key_list}) IS NODE KEY"
            )
        # Nodos destino (dimensión/FK).
        seen = {row_label, SOURCE_LABEL}
        for c in proposal.columns:
            if c.role not in (ColumnRole.DIMENSION_NODE, ColumnRole.RELATION_FK):
                continue
            label = c.resolved_target_label()
            if label in seen:
                continue
            seen.add(label)
            stmts.append(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (t:`{label}`) "
                f"REQUIRE t.`{c.resolved_target_key_property()}` IS UNIQUE"
            )
        return stmts

    # ------------------------------------------------------------------ persist
    def save_tabular(
        self,
        proposal: TabularSchemaProposal,
        table: TabularData,
        *,
        source_sha256: Optional[str] = None,
        batch_size: int = 1000,
    ) -> Dict[str, Any]:
        self.ensure_schema(proposal)
        query, param_keys = self._build_query(proposal)
        rows_params = self._build_rows_params(proposal, table, param_keys)

        driver = self._get_driver()
        persisted = 0
        with driver.session(database=self.database) as session:
            for start in range(0, len(rows_params), batch_size):
                batch = rows_params[start : start + batch_size]
                session.run(
                    query,
                    source=table.name,
                    source_path=table.source_path,
                    sha256=source_sha256,
                    rows=batch,
                )
                persisted += len(batch)
        stats = {
            "source": table.name,
            "rows_persisted": persisted,
            "row_label": proposal.resolved_row_label,
            "target_nodes": sum(
                1
                for c in proposal.columns
                if c.role in (ColumnRole.DIMENSION_NODE, ColumnRole.RELATION_FK)
            ),
        }
        logger.info("save_tabular '%s': %s", table.name, stats)
        return stats

    def _param_key(self, column: str, used: Dict[str, int]) -> str:
        from ungraph.domain.value_objects.tabular_schema import sanitize_property

        base = sanitize_property(column)
        if base not in used:
            used[base] = 0
            return base
        used[base] += 1
        return f"{base}_{used[base]}"

    def _build_query(self, proposal: TabularSchemaProposal) -> tuple[str, Dict[str, str]]:
        """Construye el query UNWIND+MERGE y el mapa columna→param_key.

        Todos los identificadores (labels, props, rel types) están sanitizados por los
        value objects; se envuelven en backticks por robustez. Los valores van siempre
        como parámetros (``row.<param_key>``).
        """
        row_label = proposal.resolved_row_label
        key_props = proposal.row_key_property_names()
        used: Dict[str, int] = {}
        param_keys: Dict[str, str] = {}

        # Claves del nodo-fila.
        if proposal.row_key_columns:
            key_pairs = []
            for col in proposal.row_key_columns:
                pk_prop = _sanitize(col)
                pkey = self._param_key(col, used)
                param_keys[col] = pkey
                key_pairs.append(f"`{pk_prop}`: row.`{pkey}`")
            key_clause = "{" + ", ".join(key_pairs) + "}"
        else:
            param_keys["__row_uid__"] = "row_uid"
            key_clause = "{`row_uid`: row.`row_uid`}"

        parts: List[str] = [
            f"MERGE (src:`{SOURCE_LABEL}` {{source: $source}})",
            "ON CREATE SET src.ingested_at = timestamp()",
            "SET src.source_path = $source_path, src.sha256 = $sha256",
            "WITH src",
            "UNWIND $rows AS row",
            f"MERGE (n:`{row_label}` {key_clause})",
        ]

        # Atributos (SET) — incluye NODE_KEY extra que no forma parte de la clave.
        set_items: List[str] = []
        for c in proposal.columns:
            if c.role == ColumnRole.ATTRIBUTE or (
                c.role == ColumnRole.NODE_KEY and c.column not in proposal.row_key_columns
            ):
                if c.column not in param_keys:
                    param_keys[c.column] = self._param_key(c.column, used)
                prop = c.resolved_property_name()
                set_items.append(f"n.`{prop}` = row.`{param_keys[c.column]}`")
        if set_items:
            parts.append("SET " + ", ".join(set_items))

        parts.append(f"MERGE (src)-[:`{HAS_ROW_REL}`]->(n)")

        # Dimensiones / FKs — nodo destino + relación, saltando nulos.
        for idx, c in enumerate(proposal.columns):
            if c.role not in (ColumnRole.DIMENSION_NODE, ColumnRole.RELATION_FK):
                continue
            if c.column not in param_keys:
                param_keys[c.column] = self._param_key(c.column, used)
            pkey = param_keys[c.column]
            target = c.resolved_target_label()
            key_prop = c.resolved_target_key_property()
            rel = c.resolved_relationship_type()
            var = f"t{idx}"
            parts.append(
                f"FOREACH (_ IN CASE WHEN row.`{pkey}` IS NULL THEN [] ELSE [1] END | "
                f"MERGE ({var}:`{target}` {{`{key_prop}`: row.`{pkey}`}}) "
                f"MERGE (n)-[:`{rel}`]->({var}))"
            )

        return "\n".join(parts), param_keys

    def _build_rows_params(
        self,
        proposal: TabularSchemaProposal,
        table: TabularData,
        param_keys: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        # Roles que mantienen el valor como string (claves estables); el resto se coerciona.
        key_roles = {ColumnRole.NODE_KEY, ColumnRole.DIMENSION_NODE, ColumnRole.RELATION_FK}
        role_by_col = {c.column: c.role for c in proposal.columns}
        rows_params: List[Dict[str, Any]] = []
        for row in table.rows:
            params: Dict[str, Any] = {}
            for col, pkey in param_keys.items():
                if col in ("__row_uid__",):
                    continue
                value = row.get(col)
                role = role_by_col.get(col)
                if role in key_roles or col in proposal.row_key_columns:
                    params[pkey] = None if value is None else str(value)
                else:
                    params[pkey] = _coerce_scalar(value)
            if not proposal.row_key_columns:
                params["row_uid"] = self._synthetic_row_uid(row, table.columns)
            rows_params.append(params)
        return rows_params

    def _synthetic_row_uid(self, row: Dict[str, Any], columns: List[str]) -> str:
        payload = "|".join(f"{c}={row.get(c)}" for c in columns)
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def _sanitize(name: str) -> str:
    from ungraph.domain.value_objects.tabular_schema import sanitize_property

    return sanitize_property(name)
