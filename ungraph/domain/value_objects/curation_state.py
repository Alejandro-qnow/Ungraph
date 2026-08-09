"""
Estado del ciclo de vida de artefactos inferidos (entidades, hechos, relaciones).

Valores previstos alineados con validación humana / pipelines de curación.
"""

from __future__ import annotations

from typing import Literal

# Cabecera de propiedad en Neo4j / dominio: evita colisión con palabra reservada "state"
CURATION_STATE_EXTRACTED = "Extracted"
CURATION_STATE_CURATED = "Curated"
CURATION_STATE_INVALID = "Invalid"

CurationStateLiteral = Literal["Extracted", "Curated", "Invalid"]

ALLOWED_CURATION_STATES: frozenset[str] = frozenset(
    {CURATION_STATE_EXTRACTED, CURATION_STATE_CURATED, CURATION_STATE_INVALID}
)


def normalize_curation_state(value: str | None, *, default: str = CURATION_STATE_EXTRACTED) -> str:
    if value is None or not str(value).strip():
        return default
    v = str(value).strip()
    # Aceptar capitalización flexible
    for allowed in ALLOWED_CURATION_STATES:
        if v.lower() == allowed.lower():
            return allowed
    raise ValueError(
        f"curation_state must be one of {sorted(ALLOWED_CURATION_STATES)}, got {value!r}"
    )
