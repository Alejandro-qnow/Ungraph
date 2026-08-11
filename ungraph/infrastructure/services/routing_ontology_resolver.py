"""
Enruta ``profile_id`` a distintos ``OntologyResolver`` (p. ej. SPARQL vs presets).
"""

from __future__ import annotations

from typing import Dict

from ungraph.domain.services.ontology_resolver import OntologyResolver
from ungraph.domain.value_objects.ontology_profile import OntologyProfile


class RoutingOntologyResolver(OntologyResolver):
    """
    Intenta resolvers registrados por clave normalizada; si no hay match, usa ``default``.
    """

    def __init__(
        self,
        routes: Dict[str, OntologyResolver],
        *,
        default: OntologyResolver,
    ) -> None:
        self._routes = {k.strip().lower(): v for k, v in routes.items() if k.strip()}
        self._default = default

    def resolve(self, profile_id: str) -> OntologyProfile:
        key = (profile_id or "").strip().lower()
        r = self._routes.get(key)
        if r is not None:
            return r.resolve(profile_id)
        return self._default.resolve(profile_id)
