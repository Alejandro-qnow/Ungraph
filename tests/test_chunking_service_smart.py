import pytest
from domain.entities.document import Document as DomainDoc
from infrastructure.services.langchain_chunking_service import LangChainChunkingService


def load_markdown_content(markdown_file):
    with open(markdown_file, 'r', encoding='utf-8') as f:
        return f.read()


def test_smart_chunk_auto_select(markdown_file):
    content = load_markdown_content(markdown_file)
    doc = DomainDoc.create(content=content, filename=markdown_file.name, file_type='markdown')

    service = LangChainChunkingService()
    chunks, metadata = service.smart_chunk(doc)

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert 'strategy' in metadata
    assert 'num_chunks' in metadata


def test_smart_chunk_force_markdown_header(markdown_file):
    # Ensure the markdown file has headers to make header-based splitting meaningful
    content = "# Title\n\n## Section 1\nText in section 1.\n\n## Section 2\nText in section 2."
    doc = DomainDoc.create(content=content, filename="test_header.md", file_type='markdown')

    service = LangChainChunkingService()
    chunks, metadata = service.smart_chunk(doc, preferred_strategy='markdown_header', evaluate_all=False)

    assert isinstance(chunks, list)
    assert len(chunks) >= 2  # At least two sections
    assert metadata.get('strategy') == 'markdown_header'


def test_smart_chunk_character_strategy(markdown_file):
    content = "Some plain text without headers. " * 50
    doc = DomainDoc.create(content=content, filename="test_char.txt", file_type='txt')

    service = LangChainChunkingService()
    chunks, metadata = service.smart_chunk(doc, preferred_strategy='character')

    assert isinstance(chunks, list)
    assert len(chunks) > 0
    assert metadata.get('strategy') == 'character'


def test_smart_chunk_semantic_requires_embeddings(markdown_file):
    content = "This is a long narrative text. " * 200
    doc = DomainDoc.create(content=content, filename="long.txt", file_type='txt')

    service = LangChainChunkingService()
    # Forcing semantic strategy without providing embeddings should raise
    with pytest.raises(ValueError):
        _ = service.smart_chunk(doc, preferred_strategy='semantic')
