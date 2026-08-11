"""
Interfaz: generación de preguntas de dominio para enriquecer el prompt de extracción.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from ungraph.domain.value_objects.document_context import DocumentContext


class DomainQuestionService(ABC):
    """Genera preguntas que se inyectan en el prompt del GraphTransformer (no solo RAG)."""

    @abstractmethod
    def generate(
        self,
        text: str,
        document_context: DocumentContext,
        *,
        max_questions: int = 8,
        max_text_chars: int = 8000,
    ) -> Tuple[str, ...]:
        """
        Args:
            text: Texto del chunk o documento (puede truncarse internamente).
            document_context: Contexto global previo.
            max_questions: Tope de preguntas.
            max_text_chars: Tope de caracteres del texto de entrada a considerar.
        """
        pass
