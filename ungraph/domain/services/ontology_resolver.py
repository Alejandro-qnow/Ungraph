"""
Interfaz: resolución de OntologyProfile desde presets o fuentes externas (fase posterior).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ungraph.domain.value_objects.ontology_profile import OntologyProfile


class OntologyResolver(ABC):
    """Resuelve un perfil ontológico por identificador (preset, URI, registro)."""

    @abstractmethod
    def resolve(self, profile_id: str) -> OntologyProfile:
        """Devuelve el perfil; lanza ValueError si el id no existe."""
        pass
