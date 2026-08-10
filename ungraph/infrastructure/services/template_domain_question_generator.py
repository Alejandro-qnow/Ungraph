"""
Generador determinista de preguntas de dominio (plantillas + contexto global).
"""

from __future__ import annotations

from typing import Tuple

from ungraph.domain.services.domain_question_service import DomainQuestionService
from ungraph.domain.value_objects.document_context import DocumentContext


class TemplateDomainQuestionGenerator(DomainQuestionService):
    """
    Preguntas fijas y contextuales para inyectar en prompts de extracción.

    Sin LLM: reproducible y barato; sustituible por implementación basada en modelo.
    """

    _BASE_QUESTIONS_EN = (
        "What are the main named entities (people, organizations, products, places) in this text?",
        "What explicit relationships are stated (employment, location, ownership, causation)?",
        "What attributes or properties of entities are mentioned?",
        "What events or actions are described?",
        "Are there temporal or quantitative facts worth capturing as attributes?",
    )

    def generate(
        self,
        text: str,
        document_context: DocumentContext,
        *,
        max_questions: int = 8,
        max_text_chars: int = 8000,
    ) -> Tuple[str, ...]:
        snippet = (text or "")[:max_text_chars]
        _ = snippet  # reservado para futuras plantillas condicionadas al texto

        out: list[str] = []
        dom = document_context.inferred_domain
        if dom:
            out.append(
                f"Given this document appears related to '{dom}', "
                "what domain-specific entities and relationships should be extracted?"
            )
        kind = document_context.document_kind
        if kind:
            out.append(
                f"The document is categorized as '{kind}': "
                "which entity and relation types are most relevant?"
            )

        for q in self._BASE_QUESTIONS_EN:
            if len(out) >= max_questions:
                break
            out.append(q)

        if document_context.key_entities_hint:
            hints = ", ".join(document_context.key_entities_hint[:8])
            if len(out) < max_questions:
                out.append(
                    f"The following terms appear salient: {hints}. "
                    "How should they be represented as nodes and edges?"
                )

        return tuple(out[:max_questions])
