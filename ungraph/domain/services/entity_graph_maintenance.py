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

    @abstractmethod
    def prune_orphan_entities(self) -> int:
        """
        Elimina :Entity sin ninguna relación (huérfanos): sin MENTIONS entrante,
        sin relaciones a/desde otras entidades, sin facts. Aparecen p. ej. tras un
        re-minado forzado (``infer --kmining --force``) cuando la nueva extracción
        deja de mencionar entidades previas.

        Respeta lo revisado por humanos: NO borra entidades ``Curated``/``Invalid``.

        Returns:
            Número de nodos :Entity huérfanos eliminados.
        """
        ...
