"""
Interfaz: extracción de contexto global de documento (sin acoplar a LangChain).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ungraph.domain.value_objects.document_context import DocumentContext


class DocumentContextService(ABC):
    """Produce un DocumentContext a partir de texto largo y metadatos opcionales."""

    @abstractmethod
    def extract(
        self,
        text: str,
        *,
        source_id: str,
        language: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> DocumentContext:
        """
        Args:
            text: Contenido completo o ventana representativa del documento.
            source_id: Identificador estable (URL, path, hash).
            language: BCP-47 si se conoce.
            metadata: Metadatos adicionales (filename, etc.).
        """
        pass
