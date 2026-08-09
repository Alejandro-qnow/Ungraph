"""
Utilidades para enriquecer metadatos de chunks tras chunking jerárquico (Markdown/HTML).
"""

from __future__ import annotations

from typing import List

from ungraph.domain.entities.chunk import Chunk


def enrich_chunks_logical_page_numbers(chunks: List[Chunk]) -> None:
    """
    Asigna page_number según grupos de encabezados (Header 1..6) en metadata de LangChain.

    Interpreta Page del patrón FILE_PAGE_CHUNK como sección lógica (outline), no folio PDF.
    """
    if not chunks:
        return
    prev_key: tuple | None = None
    page = 0
    for c in chunks:
        md = c.metadata
        key = tuple(md.get(f"Header {i}") for i in range(1, 7))
        if key != prev_key:
            page += 1
            prev_key = key
        md["page_number"] = page
