"""
Extracción HTML → WebDocument (CIR) con lxml, XPath/CSS y heurística main content.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from lxml import html as lxml_html

from ungraph.domain.value_objects.web_document import (
    ContentBlock,
    ContentBlockKind,
    ExtractionRecipe,
    Provenance,
    WebDocument,
)

logger = logging.getLogger(__name__)

_HEADING_TAGS = {f"h{i}" for i in range(1, 7)}


def _local_tag(el) -> str:
    tag = el.tag
    if isinstance(tag, str) and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return str(tag) if tag else ""


def _normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pick_content_root(tree, recipe: ExtractionRecipe):
    root = tree.getroot() if hasattr(tree, "getroot") else tree  # Element vs ElementTree
    if recipe.content_root_xpath:
        found = root.xpath(recipe.content_root_xpath)
        if found:
            return found[0]
        logger.warning("content_root_xpath sin coincidencias; usando heurística por defecto")
    if recipe.content_root_css:
        try:
            from cssselect import GenericTranslator

            xpath = GenericTranslator().css_to_xpath(recipe.content_root_css)
            found = root.xpath(xpath)
            if found:
                return found[0]
        except Exception as e:
            logger.warning("CSS a XPath falló: %s", e)
    for xp in ("//main", "//article", "//*[@role='main']", "//body"):
        found = root.xpath(xp)
        if found:
            return found[0]
    return root


def _exclude_elements(root, recipe: ExtractionRecipe) -> None:
    default_xpath = ("//script", "//style", "//noscript", "//template")
    for xp in default_xpath:
        for el in list(root.xpath(xp)):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
    for xp in recipe.exclude_xpaths:
        for el in list(root.xpath(xp)):
            parent = el.getparent()
            if parent is not None:
                parent.remove(el)
    for sel in recipe.exclude_css:
        try:
            from cssselect import GenericTranslator

            xp = GenericTranslator().css_to_xpath(sel)
            for el in list(root.xpath(xp)):
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)
        except Exception as e:
            logger.warning("exclude_css omitido (%s): %s", sel, e)


def _heading_level(tag: str) -> Optional[int]:
    if tag in _HEADING_TAGS:
        return int(tag[1])
    return None


def _xpath_for(el) -> Optional[str]:
    try:
        return el.getroottree().getpath(el)
    except Exception:
        return None


def _is_descendant_of_pre(el) -> bool:
    p = el.getparent()
    while p is not None:
        if _local_tag(p) == "pre":
            return True
        p = p.getparent()
    return False


def _walk_emit_blocks(root, recipe: ExtractionRecipe) -> List[ContentBlock]:
    """
    Recorre el subárbol y emite bloques con outline_path derivado de headings.
    """
    blocks: List[ContentBlock] = []
    order = 0
    stack: List[Tuple[int, str]] = []

    def outline_titles() -> List[str]:
        return [t for _, t in stack]

    def push_heading(level: int, title: str) -> None:
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title))

    iterator = root.iter()

    for el in iterator:
        tag = _local_tag(el)
        if _is_descendant_of_pre(el) and tag != "pre":
            continue
        if tag == "p" and el.getparent() is not None and _local_tag(el.getparent()) == "li":
            continue
        if tag in _HEADING_TAGS:
            lev = _heading_level(tag)
            if lev is None:
                continue
            lev = max(1, min(recipe.max_heading_depth, lev))
            title = _normalize_text("".join(el.itertext()))
            if recipe.strip_empty and not title:
                continue
            push_heading(lev, title)
            prov = Provenance(xpath=_xpath_for(el))
            blocks.append(
                ContentBlock.new(
                    ContentBlockKind.HEADING,
                    title,
                    order,
                    level=lev,
                    outline_path=outline_titles(),
                    provenance=prov,
                )
            )
            order += 1
            continue

        if tag == "p":
            text = _normalize_text("".join(el.itertext()))
            if recipe.strip_empty and not text:
                continue
            prov = Provenance(xpath=_xpath_for(el))
            blocks.append(
                ContentBlock.new(
                    ContentBlockKind.PARAGRAPH,
                    text,
                    order,
                    outline_path=outline_titles(),
                    provenance=prov,
                )
            )
            order += 1
        elif tag == "li":
            text = _normalize_text("".join(el.itertext()))
            if recipe.strip_empty and not text:
                continue
            prov = Provenance(xpath=_xpath_for(el))
            blocks.append(
                ContentBlock.new(
                    ContentBlockKind.LIST_ITEM,
                    text,
                    order,
                    outline_path=outline_titles(),
                    provenance=prov,
                )
            )
            order += 1
        elif tag == "pre":
            text = _normalize_text(el.text_content())
            if recipe.strip_empty and not text:
                continue
            prov = Provenance(xpath=_xpath_for(el))
            blocks.append(
                ContentBlock.new(
                    ContentBlockKind.CODE,
                    text,
                    order,
                    outline_path=outline_titles(),
                    provenance=prov,
                )
            )
            order += 1

    return blocks


def extract_web_document(
    html_bytes: bytes,
    source_id: str,
    recipe: Optional[ExtractionRecipe] = None,
    title: Optional[str] = None,
    language: Optional[str] = None,
) -> WebDocument:
    """
    Parsea HTML y produce un WebDocument (CIR).

    Args:
        html_bytes: HTML en bytes (se intenta UTF-8; lxml recupera HTML malformado).
        source_id: Identificador estable (p. ej. ruta canónica o URL).
        recipe: Receta de extracción; None usa valores por defecto.
        title: Título opcional si ya se conoce (si no, se intenta <title>).
        language: Idioma opcional (p. ej. atributo lang del html).
    """
    recipe = recipe or ExtractionRecipe()
    parser = lxml_html.HTMLParser(encoding="utf-8", recover=True)
    tree = lxml_html.document_fromstring(html_bytes, parser=parser)
    _exclude_elements(tree, recipe)
    root_el = _pick_content_root(tree, recipe)

    if title is None:
        titles = tree.xpath("//title/text()")
        title = _normalize_text(titles[0]) if titles else ""

    if language is None:
        html_nodes = tree.xpath("//html[@lang]/@lang")
        if html_nodes:
            language = html_nodes[0]

    blocks = _walk_emit_blocks(root_el, recipe)

    return WebDocument(
        source_id=source_id,
        blocks=blocks,
        title=title,
        language=language,
        recipe_version=recipe.recipe_version,
        recipe_id=recipe.recipe_id,
    )
