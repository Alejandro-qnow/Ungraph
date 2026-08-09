"""
Interfaz de Servicio: TabularLoaderService

Define la carga de fuentes tabulares (CSV, XLSX) a ``TabularData``. Se separa de
``DocumentLoaderService`` a propósito: la semántica filas/columnas es distinta a la de
un ``Document`` de texto, y este contrato es la base para futuras fuentes tabulares
(bases de datos relacionales, data warehouses).

Las implementaciones (infrastructure) pueden usar pandas/openpyxl u otros motores.
El dominio no conoce esas librerías.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from ungraph.domain.value_objects.tabular_data import TabularData


class TabularLoaderService(ABC):
    """Carga archivos tabulares y los normaliza a ``TabularData``."""

    @abstractmethod
    def load(self, file_path: Path, **kwargs) -> List[TabularData]:
        """Carga un archivo tabular.

        Un CSV produce una tabla; un XLSX puede producir varias (una por hoja),
        base para relaciones cross-tabla.

        Args:
            file_path: Ruta al archivo (.csv, .xlsx, .xls).
            **kwargs: Opciones específicas del motor (delimitador, hoja, etc.).

        Returns:
            Lista de ``TabularData`` (una por tabla/hoja).

        Raises:
            FileNotFoundError: Si el archivo no existe.
            ValueError: Si el archivo no puede procesarse.
        """
        raise NotImplementedError

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """Indica si este loader puede cargar el archivo dado."""
        raise NotImplementedError
