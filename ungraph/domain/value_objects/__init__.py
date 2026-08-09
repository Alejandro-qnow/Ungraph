"""
Value Objects del dominio.

Los Value Objects son objetos inmutables sin identidad propia.
Se comparan por valor, no por referencia.
"""

from ungraph.domain.value_objects.curation_state import (
    ALLOWED_CURATION_STATES,
    CURATION_STATE_CURATED,
    CURATION_STATE_EXTRACTED,
    CURATION_STATE_INVALID,
    normalize_curation_state,
)
from ungraph.domain.value_objects.document_context import DocumentContext
from ungraph.domain.value_objects.extraction_trace import ExtractionTrace
from ungraph.domain.value_objects.inference_model_budget import InferenceModelBudget
from ungraph.domain.value_objects.ontology_profile import OntologyProfile
from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import (
    ColumnMapping,
    ColumnProfile,
    ColumnRole,
    TabularSchemaProposal,
)

__all__ = [
    "ALLOWED_CURATION_STATES",
    "CURATION_STATE_CURATED",
    "CURATION_STATE_EXTRACTED",
    "CURATION_STATE_INVALID",
    "ColumnMapping",
    "ColumnProfile",
    "ColumnRole",
    "DocumentContext",
    "ExtractionTrace",
    "InferenceModelBudget",
    "OntologyProfile",
    "TabularData",
    "TabularSchemaProposal",
    "normalize_curation_state",
]
