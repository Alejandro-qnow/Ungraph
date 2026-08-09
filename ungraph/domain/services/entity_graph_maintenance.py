"""
Mantenimiento del subgrafo de entidades (:Entity) tras inferencia.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class EntityGraphMaintenanceService(ABC):
    """Operaciones de limpieza / fusión sobre nodos Entity en el grafo."""

    @abstractmethod
    def consolidate_entities_case_insensitive(self) -> int:
        """
        Fusiona :Entity duplicados con el mismo nombre normalizado (trim + lower).

        Returns:
            Número de nodos Entity eliminados (fusionados en el canónico).
        """
        ...

    @abstractmethod
    def resolve_entities_strip_punctuation(self) -> int:
        """
        Segunda pasada: agrupa por nombre sin caracteres '.' ni ',' (trim + lower).

        Returns:
            Número de nodos Entity eliminados tras la fusión.
        """
        ...
