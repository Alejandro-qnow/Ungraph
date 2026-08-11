"""
Preguntas de dominio vía LLM; fallback a plantillas deterministas.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import HumanMessage

from ungraph.domain.services.domain_question_service import DomainQuestionService
from ungraph.domain.value_objects.document_context import DocumentContext
from ungraph.utils.llm_json import parse_llm_json_object

logger = logging.getLogger(__name__)


class LlmDomainQuestionGenerator(DomainQuestionService):
    """Genera preguntas con un LLM barato; ante error usa ``fallback``."""

    def __init__(
        self,
        llm: BaseLanguageModel,
        *,
        fallback: DomainQuestionService,
        max_text_chars: int = 6_000,
    ) -> None:
        self._llm = llm
        self._fallback = fallback
        self._max_text_chars = max_text_chars

    def generate(
        self,
        text: str,
        document_context: DocumentContext,
        *,
        max_questions: int = 8,
        max_text_chars: int = 8000,
    ) -> Tuple[str, ...]:
        cap = min(max_text_chars, self._max_text_chars)
        snippet = (text or "")[:cap]
        summary = document_context.summary or ""
        hints = ", ".join(document_context.key_entities_hint[:12])
        prompt = (
            "You help build a knowledge graph. Given document context and a text excerpt, "
            f"propose up to {max_questions} short, concrete questions an extractor should answer "
            "(entities, relationships, attributes). "
            "Reply with JSON only: {\"questions\": [\"...\", ...]}\n\n"
            f"Document summary: {summary}\n"
            f"Key terms: {hints or '(none)'}\n\n"
            f"Text excerpt:\n---\n{snippet}\n---\n"
        )
        try:
            out = self._llm.invoke([HumanMessage(content=prompt)])
            raw = getattr(out, "content", out)
            if isinstance(raw, list):
                raw = "".join(
                    str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in raw
                )
            data = parse_llm_json_object(str(raw))
            qs = data.get("questions")
            if not isinstance(qs, list):
                return self._fallback.generate(
                    text,
                    document_context,
                    max_questions=max_questions,
                    max_text_chars=max_text_chars,
                )
            cleaned = tuple(
                str(q).strip()
                for q in qs
                if q is not None and str(q).strip()
            )[:max_questions]
            if not cleaned:
                return self._fallback.generate(
                    text,
                    document_context,
                    max_questions=max_questions,
                    max_text_chars=max_text_chars,
                )
            return cleaned
        except Exception as exc:  # noqa: BLE001
            logger.debug("LlmDomainQuestionGenerator fallback: %s", exc)
            return self._fallback.generate(
                text,
                document_context,
                max_questions=max_questions,
                max_text_chars=max_text_chars,
            )
