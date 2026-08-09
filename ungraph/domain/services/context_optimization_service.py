"""
Interfaz para producir texto optimizado para recuperación y contexto de LLM
a partir del contenido semántico del chunk (sin sustituir la verdad documental).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ContextOptimizationService(ABC):
    """
    Reduce ruido léxico (espacios, repeticiones triviales, líneas vacías)
    y opcionalmente limita longitud para estimación de tokens de contexto.

    El resultado se guarda aparte del ``page_content`` original (p. ej. nodo RetrievalChunk).
    """

    @abstractmethod
    def optimize(self, text: str, metadata: Dict[str, Any] | None = None) -> str:
        """
        Args:
            text: Texto del chunk (contenido semántico completo).
            metadata: Metadatos del chunk (filename, headers, etc.) para heurísticas futuras.

        Returns:
            Texto derivado para recuperación / ventana de LLM (puede ser más corto).
        """
        pass

    def estimate_tokens(self, text: str) -> int:
        """Estimación barata ~ caracteres/4 (no es tokenizer exacto)."""
        if not text:
            return 0
        return max(1, len(text) // 4)
