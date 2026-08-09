"""
Implementación: HeuristicSchemaInferenceService

Inferencia de esquema tabular *determinista* (sin LLM). Perfila cada columna y aplica
reglas basadas en cardinalidad, tipo inferido y señales del nombre para asignar un rol
(nodo / atributo / relación). Cada decisión lleva una ``confidence``; las columnas de
baja confianza quedan marcadas para que la capa híbrida (LLM) las desambigüe.

No depende de pandas ni Neo4j: opera sobre ``TabularData`` (dominio).
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime
from typing import Any, List, Optional, Tuple

from ungraph.domain.services.schema_inference_service import SchemaInferenceService
from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import (
    ColumnMapping,
    ColumnProfile,
    ColumnRole,
    TabularSchemaProposal,
    sanitize_label,
    sanitize_relationship_type,
)

logger = logging.getLogger(__name__)

# Umbrales (ajustables; documentados para el banco de evaluación).
UNIQUE_KEY_RATIO = 0.98        # unicidad para considerar clave
DIMENSION_MAX_CARDINALITY = 25  # tope absoluto de categorías para nodo dimensión
DIMENSION_MAX_RATIO = 0.10      # cardinalidad / filas para nodo dimensión
LOW_CONFIDENCE = 0.45           # < este valor ⇒ candidata a desambiguación LLM

_DATE_TOKENS = {"date", "fecha", "time", "datetime", "timestamp", "at", "on"}
_ID_TOKEN = "id"
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$")


def _tokens(name: str) -> List[str]:
    return [t for t in re.split(r"[^0-9a-zA-Z]+", str(name).strip().lower()) if t]


def _infer_scalar_type(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, (datetime, date)):
        return "date"
    s = str(value).strip()
    if _DATE_RE.match(s):
        return "date"
    # numérico embebido como texto
    try:
        int(s)
        return "int"
    except ValueError:
        pass
    try:
        float(s)
        return "float"
    except ValueError:
        pass
    return "str"


def _fk_target_label(column: str) -> str:
    """Deriva el label destino de una FK quitando el token 'id' final.

    'customer_id' → 'Customer'; 'id_pais' → 'Pais'; 'user' → 'User'.
    """
    toks = [t for t in _tokens(column) if t != _ID_TOKEN]
    if not toks:
        toks = _tokens(column)
    return sanitize_label("_".join(toks))


class HeuristicSchemaInferenceService(SchemaInferenceService):
    """Inferencia de esquema por reglas deterministas."""

    def profile(self, table: TabularData) -> List[ColumnProfile]:
        profiles: List[ColumnProfile] = []
        n_rows = table.n_rows
        for column in table.columns:
            values = table.column_values(column)
            non_null = [v for v in values if v is not None and str(v).strip() != ""]
            distinct = set(str(v) for v in non_null)
            cardinality = len(distinct)
            total_non_null = len(non_null)
            unique_ratio = (cardinality / total_non_null) if total_non_null else 0.0
            null_ratio = ((n_rows - total_non_null) / n_rows) if n_rows else 0.0
            dtype = self._infer_column_type(non_null)
            profiles.append(
                ColumnProfile(
                    name=column,
                    dtype_inferred=dtype,
                    cardinality=cardinality,
                    unique_ratio=unique_ratio,
                    null_ratio=null_ratio,
                    n_rows=n_rows,
                    sample_values=[v for v in non_null[:5]],
                    name_signals=self._name_signals(column, dtype),
                )
            )
        return profiles

    def _infer_column_type(self, non_null: List[Any]) -> str:
        if not non_null:
            return "str"
        types = {_infer_scalar_type(v) for v in non_null[:200]}
        if len(types) == 1:
            return next(iter(types))
        # int + float ⇒ float; cualquier otra mezcla ⇒ mixed
        if types <= {"int", "float"}:
            return "float"
        return "mixed"

    def _name_signals(self, column: str, dtype: str) -> dict:
        toks = _tokens(column)
        is_id_like = _ID_TOKEN in toks
        is_date_like = dtype == "date" or bool(set(toks) & _DATE_TOKENS)
        return {
            "is_id_like": is_id_like,
            "is_date_like": is_date_like,
            "is_fk_like": is_id_like,  # refinado en propose_schema según la PK
        }

    def propose_schema(
        self,
        table: TabularData,
        profiles: List[ColumnProfile],
    ) -> TabularSchemaProposal:
        pk = self._select_primary_key(table, profiles)
        columns: List[ColumnMapping] = []
        for prof in profiles:
            mapping = self._classify(prof, pk_column=pk, n_rows=table.n_rows)
            columns.append(mapping)

        row_label = sanitize_label(table.name)
        row_key_columns = [pk] if pk else []
        proposal = TabularSchemaProposal(
            source=table.name,
            row_node_label=row_label,
            row_key_columns=row_key_columns,
            columns=columns,
        )
        logger.info(
            "Propuesta heurística '%s': row=%s, pk=%s, columnas=%s",
            table.name,
            row_label,
            pk,
            {c.column: c.role.value for c in columns},
        )
        return proposal

    def _select_primary_key(
        self, table: TabularData, profiles: List[ColumnProfile]
    ) -> Optional[str]:
        """Elige la clave natural del nodo-fila.

        Preferencia: columna id-like única cuyo nombre casa con el de la tabla,
        luego cualquier id-like única, luego cualquier columna totalmente única.
        """
        table_tokens = set(_tokens(table.name))
        id_unique = [
            p for p in profiles
            if p.name_signals.get("is_id_like")
            and p.unique_ratio >= UNIQUE_KEY_RATIO
            and p.null_ratio == 0.0
        ]
        # 1) id-like única alineada con el nombre de la tabla (order → order_id)
        for p in id_unique:
            if table_tokens & (set(_tokens(p.name)) - {_ID_TOKEN}):
                return p.name
        # 2) primera id-like única
        if id_unique:
            return id_unique[0].name
        # 3) cualquier columna totalmente única y sin nulos (clave natural no-id)
        for p in profiles:
            if p.unique_ratio >= 0.999 and p.null_ratio == 0.0 and p.n_rows > 1:
                return p.name
        return None

    def _classify(
        self, prof: ColumnProfile, pk_column: Optional[str], n_rows: int
    ) -> ColumnMapping:
        col = prof.name

        # Clave primaria de la fila.
        if col == pk_column:
            return ColumnMapping(
                column=col, role=ColumnRole.NODE_KEY, confidence=0.95,
                decided_by="heuristic", rationale="Columna única id-like: clave del nodo-fila.",
            )

        # Otras columnas id-like ⇒ clave foránea (relación a otra entidad).
        if prof.name_signals.get("is_id_like"):
            target = _fk_target_label(col)
            return ColumnMapping(
                column=col, role=ColumnRole.RELATION_FK, confidence=0.85,
                decided_by="heuristic",
                target_label=target,
                relationship_type=sanitize_relationship_type(f"HAS_{target}"),
                rationale="Nombre *_id que referencia otra entidad.",
            )

        # Fechas / numéricos continuos ⇒ atributo escalar.
        if prof.name_signals.get("is_date_like") or prof.dtype_inferred in ("int", "float"):
            return ColumnMapping(
                column=col, role=ColumnRole.ATTRIBUTE, confidence=0.9,
                decided_by="heuristic",
                rationale=f"Tipo {prof.dtype_inferred}: atributo escalar.",
            )

        # Categórica de baja cardinalidad ⇒ nodo dimensión + relación.
        dim_cap = max(DIMENSION_MAX_CARDINALITY, int(DIMENSION_MAX_RATIO * n_rows))
        is_dimension = (
            prof.dtype_inferred in ("str", "bool")
            and 1 <= prof.cardinality <= dim_cap
            and prof.unique_ratio <= 0.5
            and prof.cardinality < max(n_rows, 2)
        )
        if is_dimension:
            target = sanitize_label(col)
            return ColumnMapping(
                column=col, role=ColumnRole.DIMENSION_NODE, confidence=0.8,
                decided_by="heuristic",
                target_label=target,
                relationship_type=sanitize_relationship_type(f"HAS_{col}"),
                rationale="Categórica de baja cardinalidad: nodo dimensión.",
            )

        # Texto de alta cardinalidad ⇒ atributo (probablemente texto libre / nombre único).
        if prof.unique_ratio >= UNIQUE_KEY_RATIO:
            return ColumnMapping(
                column=col, role=ColumnRole.ATTRIBUTE, confidence=0.75,
                decided_by="heuristic",
                rationale="Texto de alta unicidad: atributo (posible identificador natural).",
            )

        # Zona ambigua: string de cardinalidad media sin señal clara ⇒ baja confianza (→ LLM).
        return ColumnMapping(
            column=col, role=ColumnRole.ATTRIBUTE, confidence=LOW_CONFIDENCE - 0.05,
            decided_by="heuristic",
            rationale="Ambigua (cardinalidad media, sin señal): requiere desambiguación.",
        )
