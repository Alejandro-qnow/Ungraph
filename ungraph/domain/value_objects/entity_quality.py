"""Filtro de calidad de entidades (value object de dominio, puro).

Decide si un nombre de entidad es "ruido" que NO debería persistirse como
``:Entity`` en el grafo de conocimiento. Es lógica de dominio (qué cuenta como
conocimiento útil), sin dependencias de infraestructura, reutilizada por los
servicios de inferencia spaCy y LLM para no ensuciar el grafo con:

- artefactos de markdown / cadenas de solo símbolos (``##``, ``---``),
- tokens puramente numéricos o cantidades (``2404.16130``, ``1 million``, ``2022``),
- palabras-número y ordinales (``two``, ``first``),
- cadenas sin ninguna letra.

Diseñado para papers en inglés (dominio actual del corpus).
"""

from __future__ import annotations

import re
from typing import Iterable, List, TypeVar

# Solo símbolos de markdown / puntuación (heredado del filtro spaCy previo).
_MD_HASH_ONLY_LINE = re.compile(r"^#+$")
_SYMBOLS_ONLY = re.compile(r"^#{1,6}\s*$|^[#\s\-_*]+$")
# Token puramente numérico o cantidad: 12  2.5  2404.16130  1,000  10%  $5  3rd  4th
_NUMERIC_TOKEN = re.compile(r"^[$€£]?\d[\d.,]*\s*(%|st|nd|rd|th)?$", re.IGNORECASE)
_HAS_LETTER = re.compile(r"[A-Za-zÀ-ÿ]")
_SPLIT = re.compile(r"[\s\-]+")

# Palabras-número y ordinales (inglés).
_NUMBER_WORDS = frozenset(
    {
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen", "twenty", "thirty",
        "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
        "hundred", "thousand", "million", "billion", "trillion",
        "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
        "eighth", "ninth", "tenth",
    }
)


def _token_is_numeric_like(token: str) -> bool:
    t = token.strip().strip(".,;:")
    if not t:
        return True  # separadores vacíos no invalidan el conjunto
    if t.lower() in _NUMBER_WORDS:
        return True
    return bool(_NUMERIC_TOKEN.match(t))


def is_low_value_entity_name(name: str, *, min_chars: int = 2) -> bool:
    """``True`` si ``name`` es ruido y no debería persistirse como :Entity.

    Conserva nombres con al menos una letra y algún token no numérico
    (p. ej. ``GraphRAG``, ``RAG``, ``GPT-4``, ``Query-Focused Summarization``,
    ``Darren Edge``). Descarta ``2404.16130``, ``1 million``, ``two``, ``first``,
    ``##`` y cadenas < ``min_chars``.
    """
    s = (name or "").strip()
    if len(s) < min_chars:
        return True
    if _SYMBOLS_ONLY.match(s) or _MD_HASH_ONLY_LINE.fullmatch(s.lstrip()):
        return True
    if not _HAS_LETTER.search(s):
        return True
    tokens = [tok for tok in _SPLIT.split(s) if tok]
    if tokens and all(_token_is_numeric_like(tok) for tok in tokens):
        return True
    return False


_T = TypeVar("_T")


def filter_low_value_entities(
    items: Iterable[_T],
    *,
    name_getter=lambda e: getattr(e, "name", ""),
    min_chars: int = 2,
) -> List[_T]:
    """Devuelve solo los ``items`` cuyo nombre NO es ruido (ver ``is_low_value_entity_name``)."""
    return [it for it in items if not is_low_value_entity_name(name_getter(it), min_chars=min_chars)]
