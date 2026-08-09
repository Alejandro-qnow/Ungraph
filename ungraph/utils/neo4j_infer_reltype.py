"""
Normalización de tipos de relación inferidos para Cypher (Neo4j).

Tipos válidos como arista nativa: ``UPPER_SNAKE`` (regex neo4j-friendly).
En caso contrario se usa el tipo de retén ``EXTRACTED_REL`` + propiedad ``relation_type``.
"""

from __future__ import annotations

import re

_MAX_TYPE_LEN = 64
# Relaciones inferidas no normalizables → tipo de retén + propiedad ``relation_type``.
EXTRACTED_REL_FALLBACK = "EXTRACTED_REL"
_FALLBACK_TYPE = EXTRACTED_REL_FALLBACK
_NATIVE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def native_neo4j_relationship_type(semantic_type: str) -> tuple[str, bool]:
    """
    Returns ``(cypher_relationship_type, is_native)``.

    ``is_native`` False → usar siempre ``EXTRACTED_REL`` y guardar el significado
    en la propiedad ``relation_type`` (texto original del extractor).
    """
    if semantic_type is None:
        return _FALLBACK_TYPE, False
    raw = str(semantic_type).strip()
    if not raw:
        return _FALLBACK_TYPE, False
    s = raw.upper().replace(" ", "_").replace("-", "_")
    s = re.sub(r"[^A-Z0-9_]+", "_", s)
    while "__" in s:
        s = s.replace("__", "_")
    s = s.strip("_")
    if not s or len(s) > _MAX_TYPE_LEN or not _NATIVE.match(s):
        return _FALLBACK_TYPE, False
    return s, True


def is_safe_interpolated_reltype(t: str) -> bool:
    """True si ``t`` puede interpolarse literalmente en Cypher como tipo de relación."""
    return bool(t and _NATIVE.match(t) and len(t) <= _MAX_TYPE_LEN)
