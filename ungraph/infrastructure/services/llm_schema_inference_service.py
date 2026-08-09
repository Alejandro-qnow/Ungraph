"""
Implementación: LlmSchemaInferenceService

Inferencia de esquema *híbrida*: compone el servicio heurístico y usa un LLM para
desambiguar SOLO las columnas de baja confianza. Así el LLM se invoca de forma acotada
(costo controlado) y el resultado es determinista para las columnas obvias.

Si no hay LLM disponible (sin API key), se degrada de forma transparente al resultado
heurístico puro (fallback).
"""

from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

from ungraph.domain.services.schema_inference_service import SchemaInferenceService
from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import (
    ColumnMapping,
    ColumnProfile,
    ColumnRole,
    TabularSchemaProposal,
)
from ungraph.infrastructure.services.heuristic_schema_inference_service import (
    HeuristicSchemaInferenceService,
    LOW_CONFIDENCE,
)
from ungraph.utils.llm_json import parse_llm_json_object

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Eres un arquitecto de grafos de conocimiento. Decides cómo modelar columnas de una "
    "tabla en un grafo Neo4j. Para cada columna eliges un rol: "
    "'attribute' (propiedad escalar del nodo-fila), "
    "'dimension' (categoría de baja cardinalidad que merece ser un nodo propio con una "
    "relación desde la fila), o "
    "'relation_fk' (clave foránea que referencia otra entidad). "
    "Respondes SOLO JSON válido."
)


class LlmSchemaInferenceService(SchemaInferenceService):
    """Inferencia de esquema heurística + desambiguación LLM de columnas dudosas."""

    def __init__(
        self,
        heuristic: Optional[HeuristicSchemaInferenceService] = None,
        llm: Any = None,
        confidence_threshold: float = LOW_CONFIDENCE,
    ):
        """
        Args:
            heuristic: Servicio heurístico base (se crea uno por defecto si es None).
            llm: Cliente tipo ``ChatOpenAI`` con ``.invoke(...)``. Si None ⇒ solo heurística.
            confidence_threshold: Columnas con confianza menor a este valor se envían al LLM.
        """
        self._heuristic = heuristic or HeuristicSchemaInferenceService()
        self._llm = llm
        self._threshold = confidence_threshold

    def profile(self, table: TabularData) -> List[ColumnProfile]:
        return self._heuristic.profile(table)

    def propose_schema(
        self,
        table: TabularData,
        profiles: List[ColumnProfile],
    ) -> TabularSchemaProposal:
        base = self._heuristic.propose_schema(table, profiles)
        if self._llm is None:
            return base

        prof_by_name = {p.name: p for p in profiles}
        doubtful = [c for c in base.columns if c.confidence < self._threshold]
        if not doubtful:
            logger.info("Sin columnas dudosas; se omite la desambiguación LLM.")
            return base

        logger.info(
            "Desambiguando %s columnas dudosas con LLM: %s",
            len(doubtful),
            [c.column for c in doubtful],
        )
        try:
            decisions = self._ask_llm(base, doubtful, prof_by_name)
        except Exception as e:  # el LLM no debe romper la ingesta; caemos a heurística
            logger.warning("Desambiguación LLM falló (%s); se usa la heurística.", e)
            return base

        updated = self._apply_decisions(base, decisions)
        return updated

    # ------------------------------------------------------------------ LLM
    def _ask_llm(
        self,
        base: TabularSchemaProposal,
        doubtful: List[ColumnMapping],
        prof_by_name: dict,
    ) -> dict:
        payload = {
            "table": base.source,
            "row_node_label": base.resolved_row_label,
            "columns_to_decide": [
                self._column_payload(prof_by_name[c.column])
                for c in doubtful
                if c.column in prof_by_name
            ],
        }
        user_prompt = (
            "Modela cada columna en 'columns_to_decide'. Responde un objeto JSON con la "
            "clave 'decisions': una lista de objetos "
            "{\"column\": str, \"role\": \"attribute|dimension|relation_fk\", "
            "\"target_label\": str|null, \"relationship_type\": str|null, "
            "\"rationale\": str}. "
            "Usa 'dimension' o 'relation_fk' solo si aporta poder de consulta al grafo.\n\n"
            + json.dumps(payload, ensure_ascii=False, default=str)
        )
        content = self._invoke_llm(_SYSTEM_PROMPT, user_prompt)
        data = parse_llm_json_object(content)
        result = {}
        for item in data.get("decisions", []):
            col = item.get("column")
            if col:
                result[col] = item
        return result

    def _invoke_llm(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
        response = self._llm.invoke(messages)
        return getattr(response, "content", response)

    def _column_payload(self, prof: ColumnProfile) -> dict:
        return prof.to_dict()

    def _apply_decisions(
        self, base: TabularSchemaProposal, decisions: dict
    ) -> TabularSchemaProposal:
        new_columns: List[ColumnMapping] = []
        for c in base.columns:
            decision = decisions.get(c.column)
            if not decision:
                new_columns.append(c)
                continue
            try:
                role = ColumnRole(decision.get("role", c.role.value))
            except ValueError:
                new_columns.append(c)
                continue
            new_columns.append(
                ColumnMapping(
                    column=c.column,
                    role=role,
                    confidence=0.7,
                    decided_by="llm",
                    rationale=decision.get("rationale", "Desambiguada por LLM."),
                    property_name=c.property_name,
                    target_label=decision.get("target_label") or c.target_label,
                    relationship_type=decision.get("relationship_type") or c.relationship_type,
                    target_key_property=c.target_key_property,
                )
            )
        return TabularSchemaProposal(
            source=base.source,
            row_node_label=base.row_node_label,
            row_key_columns=list(base.row_key_columns),
            columns=new_columns,
        )
