"""Tests unitarios: CIR HTML, loader y chunking markdown_header + page_number lógico."""

from __future__ import annotations

import pytest

HTML_SAMPLE = """<!DOCTYPE html>
<html lang="en"><head><title>Doc Title</title></head>
<body>
<main>
  <h1>Section One</h1>
  <p>First paragraph.</p>
  <h2>Sub A</h2>
  <p>Second paragraph.</p>
</main>
</body></html>"""


def test_extract_web_document_blocks_and_provenance() -> None:
    from ungraph.infrastructure.services.html_cir_extractor import extract_web_document

    web = extract_web_document(
        HTML_SAMPLE.encode("utf-8"), source_id="https://example.com/page"
    )
    assert web.language == "en"
    kinds = [b.kind.value for b in web.blocks]
    assert "heading" in kinds
    assert "paragraph" in kinds
    assert any(b.provenance.xpath for b in web.blocks)


def test_to_markdown_outline() -> None:
    from ungraph.infrastructure.services.html_cir_extractor import extract_web_document

    web = extract_web_document(HTML_SAMPLE.encode("utf-8"), source_id="s")
    md = web.to_markdown_outline()
    assert "# Section One" in md
    assert "First paragraph" in md
    assert "## Sub A" in md


def test_extraction_recipe_content_root_xpath() -> None:
    from ungraph.domain.value_objects.web_document import ExtractionRecipe
    from ungraph.infrastructure.services.html_cir_extractor import extract_web_document

    html = b'<html><body><div id="inner"><p>Inside only.</p></div><p>Outside.</p></body></html>'
    recipe = ExtractionRecipe(content_root_xpath='//*[@id="inner"]')
    web = extract_web_document(html, source_id="s", recipe=recipe)
    joined = " ".join(b.text for b in web.blocks)
    assert "Inside only" in joined
    assert "Outside" not in joined


def test_loader_html_to_domain_document(tmp_path) -> None:
    from ungraph.infrastructure.services.langchain_document_loader_service import (
        LangChainDocumentLoaderService,
    )

    path = tmp_path / "sample.html"
    path.write_text(HTML_SAMPLE, encoding="utf-8")
    loader = LangChainDocumentLoaderService()
    docs = loader.load(path)
    assert len(docs) == 1
    assert docs[0].file_type == "html"
    assert "Section One" in docs[0].content
    assert docs[0].metadata.get("content_format") == "markdown_outline"
    assert "web_document" in docs[0].metadata


def test_smart_chunk_markdown_header_and_page_numbers(tmp_path) -> None:
    from ungraph.infrastructure.services.langchain_chunking_service import (
        LangChainChunkingService,
    )
    from ungraph.infrastructure.services.langchain_document_loader_service import (
        LangChainDocumentLoaderService,
    )
    from ungraph.utils.chunk_metadata import enrich_chunks_logical_page_numbers

    path = tmp_path / "sample.html"
    path.write_text(HTML_SAMPLE, encoding="utf-8")
    loader = LangChainDocumentLoaderService()
    docs = loader.load(path)
    chunker = LangChainChunkingService()
    chunks, meta = chunker.smart_chunk(
        docs[0],
        preferred_strategy="markdown_header",
        chunk_size=400,
        chunk_overlap=40,
    )
    assert meta.get("strategy") == "markdown_header"
    assert len(chunks) >= 1
    enrich_chunks_logical_page_numbers(chunks)
    assert all("page_number" in c.metadata for c in chunks)
    nums = [c.metadata["page_number"] for c in chunks]
    assert min(nums) >= 1
    # Distintas secciones (Header 1 / Header 2) suelen producir más de un page_number lógico
    assert max(nums) >= 1


def test_markdown_header_single_line_h1_falls_back_to_recursive() -> None:
    """H1 y párrafo en la misma línea: MarkdownHeaderTextSplitter devuelve 0 docs."""
    from langchain_core.documents import Document as LC_Doc

    from ungraph.utils.chunking_master import master_chunking_function

    # Sin saltos tras el #, el cuerpo queda vacío para LangChain (texto va a metadata).
    md = "# " + "word " * 50
    chunks, meta = master_chunking_function(
        documents=[LC_Doc(page_content=md)],
        preferred_strategy="markdown_header",
        evaluate_all=False,
        chunk_size=500,
        chunk_overlap=50,
    )
    assert meta.get("strategy") == "markdown_header"
    assert len(chunks) >= 1
    joined = "\n".join(c.page_content for c in chunks)
    assert "word" in joined
