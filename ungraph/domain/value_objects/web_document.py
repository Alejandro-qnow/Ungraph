"""
Representación intermedia canónica (CIR) para documentos HTML / web.

Contrato entre extractores (XPath/CSS, main content) y el pipeline ETI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional
import uuid


class ContentBlockKind(str, Enum):
    """Tipo lógico de bloque de contenido (no etiqueta DOM)."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    CODE = "code"
    TABLE_SUMMARY = "table_summary"
    OTHER = "other"


@dataclass(frozen=True)
class Provenance:
    """Trazabilidad hacia el DOM o el HTML serializado."""

    xpath: Optional[str] = None
    css_path: Optional[str] = None
    source_range: Optional[tuple[int, int]] = None


@dataclass
class ContentBlock:
    """Unidad de contenido ordenada dentro de un WebDocument."""

    block_id: str
    kind: ContentBlockKind
    text: str
    order_index: int
    level: Optional[int] = None
    outline_path: List[str] = field(default_factory=list)
    provenance: Provenance = field(default_factory=Provenance)

    @staticmethod
    def new(
        kind: ContentBlockKind,
        text: str,
        order_index: int,
        *,
        level: Optional[int] = None,
        outline_path: Optional[List[str]] = None,
        provenance: Optional[Provenance] = None,
    ) -> "ContentBlock":
        return ContentBlock(
            block_id=str(uuid.uuid4()),
            kind=kind,
            text=text,
            order_index=order_index,
            level=level,
            outline_path=list(outline_path or []),
            provenance=provenance or Provenance(),
        )


@dataclass
class WebDocument:
    """Documento web normalizado listo para ensamblar un Document de dominio."""

    source_id: str
    blocks: List[ContentBlock]
    title: str = ""
    language: Optional[str] = None
    retrieved_at: Optional[str] = None
    recipe_version: str = "1"
    recipe_id: str = "default"

    def to_dict(self) -> dict[str, Any]:
        """Serialización estable para metadata de Document/Chunk."""

        def block_to_dict(b: ContentBlock) -> dict[str, Any]:
            return {
                "block_id": b.block_id,
                "kind": b.kind.value,
                "text": b.text,
                "order_index": b.order_index,
                "level": b.level,
                "outline_path": list(b.outline_path),
                "provenance": {
                    "xpath": b.provenance.xpath,
                    "css_path": b.provenance.css_path,
                    "source_range": list(b.provenance.source_range)
                    if b.provenance.source_range
                    else None,
                },
            }

        return {
            "source_id": self.source_id,
            "title": self.title,
            "language": self.language,
            "retrieved_at": self.retrieved_at,
            "recipe_version": self.recipe_version,
            "recipe_id": self.recipe_id,
            "blocks": [block_to_dict(b) for b in self.blocks],
        }

    def to_markdown_outline(self) -> str:
        """
        Serializa bloques a texto con encabezados Markdown para chunking jerárquico.

        Los headings usan nivel según outline_path y level; el cuerpo sigue a cada encabezado.
        """
        lines: list[str] = []
        if self.title and not self.blocks:
            lines.append(f"# {self.title.strip()}")
            lines.append("")
        for block in sorted(self.blocks, key=lambda b: b.order_index):
            if block.kind == ContentBlockKind.HEADING and block.level is not None:
                level = max(1, min(6, block.level))
                prefix = "#" * level
                lines.append(f"{prefix} {block.text.strip()}")
                lines.append("")
            elif block.kind == ContentBlockKind.CODE:
                lines.append("```")
                lines.append(block.text.strip())
                lines.append("```")
                lines.append("")
            else:
                t = block.text.strip()
                if t:
                    lines.append(t)
                    lines.append("")
        return "\n".join(lines).strip()


@dataclass
class ExtractionRecipe:
    """
    Receta declarativa para extraer contenido de HTML.

    Si content_root_xpath y content_root_css son None, se usa la heurística main/article/body.
    """

    recipe_id: str = "default"
    recipe_version: str = "1"
    content_root_xpath: Optional[str] = None
    content_root_css: Optional[str] = None
    exclude_xpaths: List[str] = field(default_factory=list)
    exclude_css: List[str] = field(default_factory=list)
    strip_empty: bool = True
    max_heading_depth: int = 6
