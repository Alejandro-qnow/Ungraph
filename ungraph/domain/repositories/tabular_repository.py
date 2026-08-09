"""
Interfaz de Repositorio: TabularRepository

Define la persistencia de datos tabulares al grafo a partir de una
``TabularSchemaProposal`` (confirmada) y la ``TabularData`` correspondiente.

Se separa de ``ChunkRepository`` porque la unidad de persistencia es la *fila* (no el
Chunk) y la estructura la dicta el mapeo inferido, no un patrón de texto fijo.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import TabularSchemaProposal


class TabularRepository(ABC):
    """Persiste filas de una tabla como nodos/relaciones según el mapeo."""

    @abstractmethod
    def ensure_schema(self, proposal: TabularSchemaProposal) -> None:
        """Crea constraints/índices UNIQUE derivados del mapeo (idempotencia MERGE)."""
        raise NotImplementedError

    @abstractmethod
    def save_tabular(
        self,
        proposal: TabularSchemaProposal,
        table: TabularData,
        *,
        source_sha256: Optional[str] = None,
        batch_size: int = 1000,
    ) -> Dict[str, Any]:
        """Persiste la tabla en el grafo.

        Returns:
            Estadísticas de la operación (p. ej. filas, nodos y relaciones creados).
        """
        raise NotImplementedError
