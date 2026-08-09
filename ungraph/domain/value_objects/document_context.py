"""
Contexto global de documento (DocumentContextExtractor / ingeniería de contexto).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DocumentContext:
    """Visión global del documento antes de extracción por chunk."""

    source_id: str
    summary: str
    inferred_domain: Optional[str] = None
    document_kind: Optional[str] = None
    language: Optional[str] = None
    key_entities_hint: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_prompt_snippet(self, max_chars: int = 1200) -> str:
        """Texto compacto para inyectar en prompts (GraphTransformer, few-shots)."""
        parts: List[str] = [f"Document scope: {self.summary.strip()}"]
        if self.inferred_domain:
            parts.append(f"Inferred domain: {self.inferred_domain}")
        if self.document_kind:
            parts.append(f"Document kind: {self.document_kind}")
        if self.key_entities_hint:
            parts.append("Key terms: " + ", ".join(self.key_entities_hint[:20]))
        out = "\n".join(parts)
        if len(out) > max_chars:
            return out[: max_chars - 1] + "…"
        return out
