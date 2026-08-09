"""
Interfaz de Servicio: SchemaInferenceService

Define la *inferencia de esquema* tabular: perfilar columnas y proponer un mapeo
columna→rol (nodo / atributo / relación). Es el núcleo del modo Schema-Guided
Ingestion (SGI).

Implementaciones (infrastructure):
- Heurística determinista (cardinalidad, tipo, señales del nombre).
- Híbrida: heurística + LLM para desambiguar solo columnas de baja confianza.
"""

from abc import ABC, abstractmethod
from typing import List

from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import (
    ColumnProfile,
    TabularSchemaProposal,
)


class SchemaInferenceService(ABC):
    """Perfila columnas y propone un mapeo tabla→grafo."""

    @abstractmethod
    def profile(self, table: TabularData) -> List[ColumnProfile]:
        """Calcula el perfil determinista de cada columna de la tabla."""
        raise NotImplementedError

    @abstractmethod
    def propose_schema(
        self,
        table: TabularData,
        profiles: List[ColumnProfile],
    ) -> TabularSchemaProposal:
        """Propone el mapeo columna→rol a partir de los perfiles.

        Args:
            table: Tabla origen (para nombre/fuente y muestras adicionales).
            profiles: Perfiles calculados por ``profile``.

        Returns:
            ``TabularSchemaProposal`` editable por el usuario.
        """
        raise NotImplementedError
