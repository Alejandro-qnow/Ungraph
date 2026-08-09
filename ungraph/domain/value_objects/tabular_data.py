"""
Value Object: TabularData

Representación agnóstica de una tabla cargada (una hoja / un CSV), independiente de
pandas o cualquier librería. El dominio razona sobre columnas y filas, no sobre
DataFrames.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class TabularData:
    """Tabla cargada como columnas + filas normalizadas.

    Attributes:
        name: Nombre lógico de la tabla (archivo o hoja).
        columns: Nombres de columna en orden.
        rows: Filas como lista de dicts {columna: valor}. Los nulos se representan
            como ``None`` (no NaN), para que el dominio no dependa de pandas.
        source_path: Ruta del archivo de origen (trazabilidad).
    """

    name: str
    columns: List[str]
    rows: List[Dict[str, Any]] = field(default_factory=list)
    source_path: str = ""

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    def column_values(self, column: str) -> List[Any]:
        """Valores (incluyendo None) de una columna, en orden de fila."""
        return [row.get(column) for row in self.rows]
