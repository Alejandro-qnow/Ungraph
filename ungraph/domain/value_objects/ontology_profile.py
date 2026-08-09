"""
Perfil ontológico: tipos permitidos y referencias URI (resultado de OntologyResolver).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Optional, Tuple


@dataclass(frozen=True)
class OntologyProfile:
    """Esquema de extracción alineado a una ontología o preset de dominio."""

    profile_id: str
    allowed_nodes: Tuple[str, ...]
    allowed_relationships: Tuple[str, ...]
    class_uri_by_label: Dict[str, str] = field(default_factory=dict)
    property_uri_by_rel: Dict[str, str] = field(default_factory=dict)
    notes: Optional[str] = None

    def allowed_nodes_set(self) -> FrozenSet[str]:
        return frozenset(self.allowed_nodes)

    def allowed_relationships_set(self) -> FrozenSet[str]:
        return frozenset(self.allowed_relationships)

    def resolve_class_uri(self, entity_type: str) -> Optional[str]:
        """IRI de clase para la etiqueta de tipo extraída (coincidencia insensible a mayúsculas)."""
        if not entity_type or not self.class_uri_by_label:
            return None
        d = self.class_uri_by_label
        if entity_type in d:
            return d[entity_type]
        et = entity_type.lower()
        for k, v in d.items():
            if k.lower() == et:
                return v
        return None

    def resolve_property_uri(self, relation_type: str) -> Optional[str]:
        """IRI de propiedad para el tipo de relación extraído."""
        if not relation_type or not self.property_uri_by_rel:
            return None
        d = self.property_uri_by_rel
        if relation_type in d:
            return d[relation_type]
        rt = relation_type.lower()
        for k, v in d.items():
            if k.lower() == rt:
                return v
        return None
