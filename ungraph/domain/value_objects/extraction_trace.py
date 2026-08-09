"""
Trazabilidad de una pasada de extracción (decisiones auditables).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class ExtractionTrace:
    """Registro de contexto y perfil usados en una extracción."""

    trace_id: str
    chunk_id: str
    document_context_fingerprint: str = ""
    ontology_profile_id: str = ""
    domain_questions: Tuple[str, ...] = field(default_factory=tuple)
    extractor_route: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
