"""
ungraph.reasoning — Fachadas de conveniencia para la fase Inference ("I" del ETI).

Este subpaquete expone la inferencia y el razonamiento del grafo como funciones
simples y serializables (dict), pensadas para ser consumidas indistintamente desde la
API Python, la CLI o el servidor MCP. Cada función **delega** en casos de uso y
servicios existentes (composition root en ``ungraph.application.dependencies``); no
duplica lógica de negocio (regla del roadmap C4).

Orquestación determinista → no-determinista:
- Determinista/estructural: ``graph_stats``, ``validate_topology``, ``consolidate_entities``.
- No-determinista/LLM: ``mine_knowledge``, ``infer_over_document``, ``ingest_tabular``
  (esta última es determinista en dry-run heurístico; usa LLM solo para desambiguar).

La capa agentic (propose/critique/verify) se compone ORQUESTANDO estas fachadas desde
un agente (p. ej. Claude vía MCP) o, en el futuro, un grafo LangGraph interno.
"""

from ungraph.reasoning.facade import (
    consolidate_entities,
    graph_stats,
    infer_over_document,
    ingest_tabular,
    mine_knowledge,
    validate_topology,
)

__all__ = [
    "consolidate_entities",
    "graph_stats",
    "infer_over_document",
    "ingest_tabular",
    "mine_knowledge",
    "validate_topology",
]
