"""
Implementación ligera de ContextOptimizationService: sin LLM, solo heurísticas locales.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from ungraph.domain.services.context_optimization_service import ContextOptimizationService


class HeuristicContextOptimizationService(ContextOptimizationService):
    """
    - Colapsa espacios en blanco y líneas vacías repetidas.
    - Elimina líneas que son solo separadores o muy cortas sin letras.
    - Opcionalmente trunca a ``max_chars`` para capar coste de contexto.
    """

    def __init__(self, max_chars: int | None = 12_000) -> None:
        self._max_chars = max_chars

    def optimize(self, text: str, metadata: Dict[str, Any] | None = None) -> str:
        if not text or not text.strip():
            return ""

        lines = text.replace("\r\n", "\n").split("\n")
        cleaned: list[str] = []
        prev_empty = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if not prev_empty:
                    cleaned.append("")
                prev_empty = True
                continue
            prev_empty = False
            if len(stripped) < 2 and not re.search(r"\w", stripped):
                continue
            cleaned.append(stripped)

        out = "\n".join(cleaned)
        out = re.sub(r"[ \t]+", " ", out)
        out = re.sub(r"\n{3,}", "\n\n", out).strip()

        if self._max_chars and len(out) > self._max_chars:
            out = out[: self._max_chars].rsplit("\n", 1)[0] + "\n…"

        return out
