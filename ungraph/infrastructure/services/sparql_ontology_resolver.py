"""
OntologyResolver alimentado por dos consultas SPARQL (nodos y relaciones).

Convención de variables en cada SELECT:
- ``label`` (obligatorio en cada fila): etiqueta local para tipos permitidos en extracción.
- ``uri`` (opcional): IRI de clase (nodos) o de propiedad (relaciones) para trazabilidad URI-first.
"""

from __future__ import annotations

from typing import Dict, Tuple

from ungraph.domain.services.ontology_resolver import OntologyResolver
from ungraph.domain.value_objects.ontology_profile import OntologyProfile
from ungraph.infrastructure.services.sparql_client import (
    PostFormat,
    binding_text,
    sparql_select_bindings,
)


def _labels_and_uris_from_bindings(
    bindings: list[dict],
    *,
    label_var: str = "label",
    uri_var: str = "uri",
) -> Tuple[tuple[str, ...], Dict[str, str]]:
    labels: list[str] = []
    uri_by_label: Dict[str, str] = {}
    seen: set[str] = set()
    for b in bindings:
        lab = binding_text(b, label_var)
        if not lab or not lab.strip():
            continue
        sl = lab.strip()
        if sl in seen:
            continue
        seen.add(sl)
        labels.append(sl)
        ur = binding_text(b, uri_var)
        if ur and ur.strip():
            uri_by_label.setdefault(sl, ur.strip())
    return tuple(labels), uri_by_label


class SparqlOntologyResolver(OntologyResolver):
    def __init__(
        self,
        endpoint: str,
        *,
        nodes_query: str,
        relations_query: str,
        profile_id: str = "sparql",
        timeout_seconds: float = 60.0,
        post_format: PostFormat = "content",
        use_cache: bool = True,
        notes: str | None = None,
    ) -> None:
        self._endpoint = endpoint.strip()
        self._nodes_q = (nodes_query or "").strip()
        self._rels_q = (relations_query or "").strip()
        self.profile_id = (profile_id or "sparql").strip()
        self._timeout = timeout_seconds
        self._post_format = post_format
        self._use_cache = use_cache
        self._notes = notes
        self._cached: OntologyProfile | None = None

    def resolve(self, profile_id: str) -> OntologyProfile:
        key = (profile_id or "").strip().lower()
        if key != self.profile_id.lower():
            raise ValueError(
                f"SparqlOntologyResolver only serves profile_id={self.profile_id!r}, got {profile_id!r}"
            )
        if self._use_cache and self._cached is not None:
            return self._cached

        if not self._endpoint or not self._nodes_q or not self._rels_q:
            raise ValueError("SparqlOntologyResolver: missing endpoint or queries")

        nb = sparql_select_bindings(
            self._endpoint,
            self._nodes_q,
            timeout_seconds=self._timeout,
            post_format=self._post_format,
        )
        rb = sparql_select_bindings(
            self._endpoint,
            self._rels_q,
            timeout_seconds=self._timeout,
            post_format=self._post_format,
        )

        nodes, class_uri = _labels_and_uris_from_bindings(nb)
        rels, prop_uri = _labels_and_uris_from_bindings(rb)
        if not nodes:
            raise ValueError("SPARQL nodes query returned no bindings with ?label")
        if not rels:
            raise ValueError("SPARQL relations query returned no bindings with ?label")

        prof = OntologyProfile(
            profile_id=self.profile_id,
            allowed_nodes=nodes,
            allowed_relationships=rels,
            class_uri_by_label=class_uri,
            property_uri_by_rel=prop_uri,
            notes=self._notes or "Loaded via SPARQL (SparqlOntologyResolver)",
        )
        if self._use_cache:
            self._cached = prof
        return prof
