"""
Validación de alineación entre tipos extraídos y un OntologyProfile.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Set

from ungraph.domain.value_objects.ontology_profile import OntologyProfile


@dataclass
class OntologyAlignmentReport:
    """Resultado de validate_ontology_alignment."""

    orphan_labels: List[str] = field(default_factory=list)
    orphan_relations: List[str] = field(default_factory=list)
    uncovered_allowed_nodes: List[str] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)


def validate_ontology_alignment(
    *,
    extracted_node_types: Set[str],
    extracted_relation_types: Set[str],
    profile: OntologyProfile,
) -> OntologyAlignmentReport:
    """
    Compara tipos observados en una extracción con un OntologyProfile (labels de string).
    """
    allowed_n = profile.allowed_nodes_set()
    allowed_r = profile.allowed_relationships_set()

    orphan_labels = sorted(extracted_node_types - allowed_n) if allowed_n else []
    orphan_relations = sorted(extracted_relation_types - allowed_r) if allowed_r else []
    uncovered = sorted(allowed_n - extracted_node_types) if allowed_n else []

    messages: List[str] = []
    if orphan_labels:
        messages.append(f"Node types not in profile: {orphan_labels}")
    if orphan_relations:
        messages.append(f"Relation types not in profile: {orphan_relations}")

    return OntologyAlignmentReport(
        orphan_labels=orphan_labels,
        orphan_relations=orphan_relations,
        uncovered_allowed_nodes=uncovered,
        messages=messages,
    )
