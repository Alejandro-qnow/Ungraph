"""
Contexto de documento vía LLM (OpenAI-compatible), con fallback heurístico.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage

from ungraph.domain.services.document_context_service import DocumentContextService
from ungraph.domain.value_objects.document_context import DocumentContext
from ungraph.utils.llm_json import parse_llm_json_object

logger = logging.getLogger(__name__)


class LlmDocumentContextService(DocumentContextService):
    """Una llamada LLM devuelve resumen breve + pistas; si falla, delega al fallback."""

    def __init__(
        self,
        llm: BaseLanguageModel,
        *,
        fallback: DocumentContextService,
        max_input_chars: int = 12_000,
    ) -> None:
        self._llm = llm
        self._fallback = fallback
        self._max_input_chars = max_input_chars

    def extract(
        self,
        text: str,
        *,
        source_id: str,
        language: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> DocumentContext:
        body = (text or "").strip()
        if not body:
            return self._fallback.extract(
                text,
                source_id=source_id,
                language=language,
                metadata=metadata,
            )
        window = body[: self._max_input_chars]
        prompt = (
            "You analyze a text excerpt for knowledge-graph extraction preparation.\n"
            "Reply with a single JSON object only, no markdown, keys:\n"
            '- "summary": string, at most 400 characters, factual overview of the excerpt;\n'
            '- "inferred_domain": string or null (short label, e.g. "biotech", "software docs");\n'
            '- "document_kind": string or null (e.g. "tutorial", "API reference", "paper abstract");\n'
            '- "key_terms": array of up to 12 short strings (salient noun phrases or names).\n\n'
            f"Excerpt:\n---\n{window}\n---\n"
        )
        try:
            out = self._llm.invoke([HumanMessage(content=prompt)])
            raw = getattr(out, "content", out)
            if isinstance(raw, list):
                raw = "".join(
                    str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in raw
                )
            data = parse_llm_json_object(str(raw))
            summary = str(data.get("summary") or "").strip() or body[:400]
            if len(summary) > 500:
                summary = summary[:497] + "…"
            dom = data.get("inferred_domain")
            kind = data.get("document_kind")
            terms = data.get("key_terms")
            hints: tuple[str, ...] = ()
            if isinstance(terms, list):
                hints = tuple(
                    str(t).strip()
                    for t in terms[:12]
                    if t is not None and str(t).strip()
                )
            md = dict(metadata or {})
            md.setdefault("extractor", "llm_v1")
            return DocumentContext(
                source_id=source_id,
                summary=summary,
                inferred_domain=str(dom).strip() if dom else None,
                document_kind=str(kind).strip() if kind else None,
                language=language,
                key_entities_hint=hints,
                metadata=md,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("LlmDocumentContextService fallback: %s", exc)
            return self._fallback.extract(
                text,
                source_id=source_id,
                language=language,
                metadata=metadata,
            )
