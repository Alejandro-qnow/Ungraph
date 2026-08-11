"""
OntologyResolver por presets en memoria (sin RDF remoto).
"""

from __future__ import annotations

from typing import Dict

from ungraph.domain.services.ontology_resolver import OntologyResolver
from ungraph.domain.value_objects.ontology_profile import OntologyProfile


def _general_profile() -> OntologyProfile:
    return OntologyProfile(
        profile_id="general",
        allowed_nodes=(
            "Person",
            "Organization",
            "Location",
            "Product",
            "Event",
            "Concept",
        ),
        allowed_relationships=(
            "WORKS_FOR",
            "LOCATED_IN",
            "PART_OF",
            "RELATED_TO",
            "PRODUCED_BY",
        ),
        notes="Aligned with default LLM inference schema in application.dependencies",
    )


def _minimal_profile() -> OntologyProfile:
    return OntologyProfile(
        profile_id="minimal",
        allowed_nodes=("Entity",),
        allowed_relationships=("RELATED_TO",),
        notes="Minimal open extraction",
    )


def _scientific_kg_profile() -> OntologyProfile:
    """Perfil para papers científicos de grafos de conocimiento / ML.

    Restringe la extracción a conceptos de dominio (métodos, modelos, tareas,
    datasets, métricas, sistemas) y a predicados con carga semántica, evitando el
    ruido de ``Person``/``Concept`` + ``RELATED_TO`` del perfil ``general``.
    """
    return OntologyProfile(
        profile_id="scientific_kg",
        allowed_nodes=(
            "Method",
            "Model",
            "Task",
            "Dataset",
            "Metric",
            "System",
            "Technique",
            "Framework",
            "Benchmark",
            "Concept",
        ),
        allowed_relationships=(
            "USES",
            "PROPOSES",
            "ADDRESSES",
            "EVALUATED_ON",
            "MEASURED_BY",
            "OUTPERFORMS",
            "BASED_ON",
            "EXTENDS",
            "IMPROVES",
            "RETRIEVES_FROM",
            "PART_OF",
            "APPLIES_TO",
        ),
        notes="Scientific KG/ML papers: domain concepts + semantic predicates.",
    )


_general = _general_profile()

_PRESETS: Dict[str, OntologyProfile] = {
    "default": _general,
    "general": _general,
    "minimal": _minimal_profile(),
    "scientific_kg": _scientific_kg_profile(),
    "knowledge_graphs": _scientific_kg_profile(),
}


class PresetOntologyResolver(OntologyResolver):
    """Resuelve perfiles predefinidos; extensible registrando en `_PRESETS`."""

    def resolve(self, profile_id: str) -> OntologyProfile:
        key = (profile_id or "").strip().lower()
        if key == "default":
            key = "general"
        p = _PRESETS.get(key)
        if p is None:
            raise ValueError(
                f"Unknown ontology profile_id={profile_id!r}. "
                f"Known: {sorted(_PRESETS.keys())}"
            )
        return p
