"""
Implementación: PandasTabularLoaderService

Carga CSV/XLSX a ``TabularData`` usando pandas (+ openpyxl para XLSX). Es una
dependencia opcional: se instala con ``pip install 'ungraph[tabular]'``.

XLSX multi-hoja produce varias ``TabularData`` (una por hoja), base para relaciones
cross-tabla y para fuentes tipo base de datos.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, List

from ungraph.domain.services.tabular_loader_service import TabularLoaderService
from ungraph.domain.value_objects.tabular_data import TabularData

logger = logging.getLogger(__name__)

_SUPPORTED_SUFFIXES = {".csv", ".xlsx", ".xls"}


def _normalize_value(value: Any) -> Any:
    """Convierte NaN/NaT de pandas a ``None`` para no filtrar pandas al dominio."""
    if value is None:
        return None
    try:
        if isinstance(value, float) and math.isnan(value):
            return None
    except (TypeError, ValueError):
        pass
    # pandas.NA / NaT
    try:
        import pandas as pd

        if value is pd.NA or (pd.isna(value) and not isinstance(value, (list, dict))):
            return None
    except (ImportError, TypeError, ValueError):
        pass
    return value


class PandasTabularLoaderService(TabularLoaderService):
    """Carga fuentes tabulares con pandas."""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in _SUPPORTED_SUFFIXES

    def load(self, file_path: Path, **kwargs) -> List[TabularData]:
        if not file_path.exists():
            raise FileNotFoundError(f"El archivo no existe: {file_path}")
        suffix = file_path.suffix.lower()
        if suffix not in _SUPPORTED_SUFFIXES:
            raise ValueError(f"Tipo de archivo tabular no soportado: {suffix}")

        try:
            import pandas as pd
        except ImportError as e:  # pragma: no cover - ruta de dependencia faltante
            raise ImportError(
                "pandas no está instalado. Instala el extra tabular: "
                "pip install 'ungraph[tabular]'"
            ) from e

        if suffix == ".csv":
            return [self._load_csv(pd, file_path, **kwargs)]
        return self._load_excel(pd, file_path, **kwargs)

    def _load_csv(self, pd, file_path: Path, **kwargs) -> TabularData:
        read_kwargs = {"dtype": object, "keep_default_na": True}
        read_kwargs.update({k: v for k, v in kwargs.items() if k in ("sep", "delimiter", "encoding")})
        df = pd.read_csv(file_path, **read_kwargs)
        return self._dataframe_to_tabular(df, name=file_path.stem, source_path=str(file_path))

    def _load_excel(self, pd, file_path: Path, **kwargs) -> List[TabularData]:
        sheet = kwargs.get("sheet_name", None)  # None => todas las hojas
        sheets = pd.read_excel(file_path, sheet_name=sheet, dtype=object)
        # pandas devuelve DataFrame (una hoja) o dict {hoja: DataFrame} (todas).
        if not isinstance(sheets, dict):
            sheets = {str(sheet or file_path.stem): sheets}
        tables: List[TabularData] = []
        for sheet_name, df in sheets.items():
            tables.append(
                self._dataframe_to_tabular(
                    df, name=str(sheet_name), source_path=str(file_path)
                )
            )
        return tables

    def _dataframe_to_tabular(self, df, name: str, source_path: str) -> TabularData:
        columns = [str(c) for c in df.columns]
        rows: List[dict] = []
        for record in df.to_dict(orient="records"):
            rows.append({str(k): _normalize_value(v) for k, v in record.items()})
        logger.info(
            "Tabla '%s' cargada: %s columnas, %s filas", name, len(columns), len(rows)
        )
        return TabularData(
            name=name, columns=columns, rows=rows, source_path=source_path
        )
