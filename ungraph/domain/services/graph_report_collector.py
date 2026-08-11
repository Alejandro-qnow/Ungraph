"""
Puerto: recolección de datos de introspección Neo4j para el reporte ETI.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

class GraphReportCollector(ABC):
    """Contrato para recolectar métricas y muestras del grafo vía Cypher."""

    @abstractmethod
    def collect_db_snapshot(
        self,
        *,
        document_uid: str | None,
        sample_node_limit: int,
    ) -> dict:
        """
        Devuelve un dict con claves alineadas a EtiReportPayload
        excluyendo run_meta y run_counters.
        """
        raise NotImplementedError
