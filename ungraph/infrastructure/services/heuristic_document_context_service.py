"""
Implementación sin LLM: resumen corto y términos frecuentes como pistas de dominio.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from ungraph.domain.services.document_context_service import DocumentContextService
from ungraph.domain.value_objects.document_context import DocumentContext

_STOP = frozenset(
    """
    the a an is are was were be been being to of and or for in on with at by from
    as if this that these those it its they them we you he she not but
    el la los las un una de del al y o en con por para que se es son fue
    """.split()
)


class HeuristicDocumentContextService(DocumentContextService):
    """
    Heurística local: primeros caracteres como resumen, términos frecuentes como hints.

    No detecta dominio fino; sirve de base hasta conectar un LLM opcional.
    """

    def __init__(
        self,
        summary_max_chars: int = 500,
        key_terms: int = 12,
    ) -> None:
        self._summary_max = summary_max_chars
        self._key_terms = key_terms

    def extract(
        self,
        text: str,
        *,
        source_id: str,
        language: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> DocumentContext:
        clean = (text or "").strip()
        if not clean:
            return DocumentContext(
                source_id=source_id,
                summary="(empty)",
                language=language,
                metadata=dict(metadata or {}),
            )

        summary = clean[: self._summary_max]
        if len(clean) > self._summary_max:
            summary = summary.rstrip() + "…"

        tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}", clean.lower())
        filtered = [t for t in tokens if t not in _STOP]
        top = [w for w, _ in Counter(filtered).most_common(self._key_terms)]

        md = dict(metadata or {})
        md.setdefault("extractor", "heuristic_v1")

        return DocumentContext(
            source_id=source_id,
            summary=summary,
            inferred_domain=None,
            document_kind=None,
            language=language,
            key_entities_hint=tuple(top),
            metadata=md,
        )
