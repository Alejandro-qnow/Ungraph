"""
Modelo de payload para el reporte HTML post-ETI (serializable a JSON).

Compatible con props de @neo4j-nvl/react (nodes / rels con id, from, to).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EtiRunCounters(BaseModel):
    """Conteos de la corrida ETI (memoria de aplicación, no solo agregados globales en Neo4j)."""

    chunks_created: int = 0
    facts_inferred: int = 0
    relations_inferred: int = 0


class EtiRunMeta(BaseModel):
    """Metadatos de la corrida mostrados en cabecera del reporte."""

    ungraph_version: str
    generated_at_utc: str
    neo4j_database: str
    neo4j_uri_host: str  # sin credenciales
    pattern_name: str | None = None
    document_filename: str | None = None
    document_path: str | None = None
    source_document_uid: str | None = None
    embedding_encoder_summary: str | None = None
    inference_mode: str | None = None


class NvlNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    caption: str | None = None
    labels: list[str] | None = None
    size: float | None = None


class NvlRel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    id: str
    from_: str = Field(alias="from")
    to: str
    caption: str | None = None


class EtiReportPayload(BaseModel):
    """Snapshot completo embebido en window.__UNGRAPH_ETI_REPORT__."""

    run_meta: EtiRunMeta
    run_counters: EtiRunCounters
    label_counts: dict[str, int]
    rel_type_counts: dict[str, int]
    entity_type_counts: dict[str, int]
    related_to_relation_type_counts: dict[str, int]
    node_schema_rows: list[dict[str, Any]]
    rel_schema_rows: list[dict[str, Any]]
    indexes: list[dict[str, Any]]
    constraints: list[dict[str, Any]]
    schema_visualization: dict[str, Any]
    """{'nodes': [...], 'rels': [...] } en formato NVL."""
    instance_sample: dict[str, Any]
    """Subgrafo acotado: {'nodes': [...], 'rels': [...] }."""
    reference_model_ascii: str
    inference_benchmark: dict[str, Any] | None = None
    """Salida de ``run_dual_inference_benchmark`` (NER vs LLM in-memory)."""
    graphrag_smoke: list[dict[str, Any]] | None = None
    """Proxy GraphRAG: resultados de búsqueda textual por consulta."""
