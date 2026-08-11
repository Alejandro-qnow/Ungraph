"""
Grafo LangGraph lineal para extracción con LLMGraphTransformer.

Flujo: ``spacy_hints`` (opcional: candidatos NER) → ``context`` (opcional) → ``extract``.
"""

from __future__ import annotations

import logging
from typing import Any, NotRequired, Optional, TypedDict

from langchain_core.documents import Document as LangChainDocument
from langchain_core.language_models import BaseLanguageModel
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs.graph_document import GraphDocument
from langgraph.graph import END, START, StateGraph

from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.services.document_context_service import DocumentContextService
from ungraph.domain.services.domain_question_service import DomainQuestionService
from ungraph.infrastructure.services.llm_inference_service import LangChainAdapter
from ungraph.utils.inference_prompt import (
    build_graph_transformer_context_addon,
    build_spacy_lexical_hints_addon,
)

logger = logging.getLogger(__name__)


def log_compiled_extraction_graph(compiled: Any, *, log: Optional[logging.Logger] = None) -> None:
    """
    Escribe en log la estructura del ``StateGraph`` compilado (nodos, aristas y Mermaid).
    Útil para comprobar en consola que LangGraph refleja START → spacy_hints → context → extract → END.
    """
    lg = log or logger
    try:
        gx = compiled.get_graph()
    except Exception as exc:  # noqa: BLE001
        lg.warning("No se pudo introspectar el grafo LangGraph compilado: %s", exc)
        return
    nodes = list(getattr(gx, "nodes", []) or [])
    edges = list(getattr(gx, "edges", []) or [])
    lg.info(
        "LangGraph (inferencia LLM) compilado: nodos=%s",
        ", ".join(str(n) for n in nodes),
    )
    for e in edges:
        lg.info("  arista: %s → %s", getattr(e, "source", e), getattr(e, "target", e))
    draw = getattr(gx, "draw_mermaid", None)
    if callable(draw):
        try:
            mermaid = draw()
            if mermaid and str(mermaid).strip():
                lg.info("LangGraph Mermaid:\n%s", mermaid.strip())
        except Exception as exc:  # noqa: BLE001
            lg.debug("draw_mermaid no disponible: %s", exc)


class InferenceGraphState(TypedDict):
    chunk: Chunk
    spacy_hints: NotRequired[str]
    context_addon: NotRequired[str]
    graph_document: NotRequired[GraphDocument]


def _chunk_source_id(chunk: Chunk) -> str:
    md = chunk.metadata or {}
    for key in (
        "source_id",
        "canonical_url",
        "source_url",
        "filename",
        "source_document_uid",
    ):
        raw = md.get(key)
        if raw:
            return str(raw)
    if chunk.source_document_uid:
        return str(chunk.source_document_uid)
    return chunk.id


def build_llm_extraction_graph(
    llm: BaseLanguageModel,
    *,
    allowed_nodes: Optional[list[str]] = None,
    allowed_relationships: Optional[list[str]] = None,
    prompt: Any = None,
    strict_mode: bool = True,
    document_context_service: Optional[DocumentContextService] = None,
    domain_question_service: Optional[DomainQuestionService] = None,
    context_addon_max_chars: int = 6000,
    spacy_lexical_service: Any = None,
) -> Any:
    """
    Compila un ``StateGraph`` con flujo
    START → spacy_hints → context → extract → END.

    El nodo ``spacy_hints`` (si ``spacy_lexical_service`` tiene ``extract_entities``) inyecta
    candidatos NER antes del contexto heurístico/LLM y del texto fuente para el
    ``LLMGraphTransformer``.
    """
    adapter = LangChainAdapter()
    nodes = allowed_nodes or []
    rels = allowed_relationships or []
    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=nodes,
        allowed_relationships=rels,
        prompt=prompt,
        strict_mode=strict_mode,
    )

    use_context = (
        document_context_service is not None and domain_question_service is not None
    )
    use_spacy = spacy_lexical_service is not None and hasattr(
        spacy_lexical_service, "extract_entities"
    )

    def spacy_hints_node(state: InferenceGraphState) -> dict:
        if not use_spacy:
            return {}
        chunk = state["chunk"]
        try:
            text = (chunk.page_content or "").strip()
            if not text:
                return {}
            entities = spacy_lexical_service.extract_entities(chunk)
            pairs = [(e.name, e.type) for e in entities]
            addon = build_spacy_lexical_hints_addon(pairs)
            if not addon.strip():
                return {}
            return {"spacy_hints": addon}
        except Exception as exc:  # noqa: BLE001
            logger.warning("inference spacy_hints_node skipped: %s", exc)
            return {}

    def context_node(state: InferenceGraphState) -> dict:
        if not use_context:
            return {}
        chunk = state["chunk"]
        try:
            text = (chunk.page_content or "").strip()
            if not text:
                return {}
            src = _chunk_source_id(chunk)
            lang = (chunk.metadata or {}).get("language") if chunk.metadata else None
            doc_ctx = document_context_service.extract(
                text,
                source_id=src,
                language=lang if isinstance(lang, str) else None,
                metadata=dict(chunk.metadata or {}),
            )
            questions = domain_question_service.generate(text, doc_ctx)
            addon = build_graph_transformer_context_addon(
                doc_ctx,
                questions,
                max_chars=context_addon_max_chars,
            )
            if not addon.strip():
                return {}
            return {"context_addon": addon}
        except Exception as exc:  # noqa: BLE001
            logger.warning("inference context_node skipped: %s", exc)
            return {}

    def extract_node(state: InferenceGraphState) -> dict:
        chunk = state["chunk"]
        doc = adapter.chunk_to_langchain_document(chunk)
        blocks: list[str] = []
        spacy_add = state.get("spacy_hints")
        if spacy_add and str(spacy_add).strip():
            blocks.append(str(spacy_add).strip())
        addon = state.get("context_addon")
        if addon and str(addon).strip():
            blocks.append(
                "[Ungraph context for extraction]\n" + str(addon).strip(),
            )
        if blocks:
            doc = LangChainDocument(
                page_content="\n\n".join(blocks) + "\n\n[Source text]\n" + doc.page_content,
                metadata=doc.metadata,
            )
        graph_document = transformer.process_response(doc)
        return {"graph_document": graph_document}

    g = StateGraph(InferenceGraphState)
    g.add_node("spacy_hints", spacy_hints_node)
    g.add_node("context", context_node)
    g.add_node("extract", extract_node)
    g.add_edge(START, "spacy_hints")
    g.add_edge("spacy_hints", "context")
    g.add_edge("context", "extract")
    g.add_edge("extract", END)
    compiled = g.compile()
    log_compiled_extraction_graph(compiled, log=logger)
    if use_spacy:
        logger.info("LangGraph inferencia: nodo 'spacy_hints' activo (NER → prompt LLM).")
    else:
        logger.info(
            "LangGraph inferencia: nodo 'spacy_hints' en passthrough (sin servicio spaCy)."
        )
    if use_context:
        logger.info(
            "LangGraph inferencia: nodo 'context' activo (DocumentContext + DomainQuestion)."
        )
    else:
        logger.info(
            "LangGraph inferencia: nodo 'context' en passthrough (sin servicios de contexto)."
        )
    return compiled
