"""
Tests para entidades del dominio.

Verifica que las entidades funcionan correctamente con datos reales.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.entities.document import Document
from domain.entities.chunk import Chunk
from domain.value_objects.document_type import DocumentType


def test_document_creation():
    """Test: Crear un Document válido."""
    doc = Document.create(
        content="Este es un documento de prueba",
        filename="test.md",
        file_type="markdown",
        metadata={"encoding": "utf-8"}
    )
    
    assert doc.id is not None
    assert doc.content == "Este es un documento de prueba"
    assert doc.filename == "test.md"
    assert doc.file_type == "markdown"
    assert doc.get_encoding() == "utf-8"


def test_document_validation():
    """Test: Validar que Document rechaza datos inválidos."""
    with pytest.raises(ValueError, match="content cannot be empty"):
        Document.create(
            content="",
            filename="test.md",
            file_type="markdown"
        )
    
    with pytest.raises(ValueError, match="filename cannot be empty"):
        Document.create(
            content="test",
            filename="",
            file_type="markdown"
        )


def test_chunk_creation():
    """Test: Crear un Chunk válido."""
    chunk = Chunk(
        id="chunk_1",
        page_content="Este es un chunk de prueba",
        metadata={"filename": "test.md", "page_number": 1},
        chunk_id_consecutive=1
    )
    
    assert chunk.id == "chunk_1"
    assert chunk.page_content == "Este es un chunk de prueba"
    assert chunk.get_filename() == "test.md"
    assert chunk.get_page_number() == 1


def test_chunk_validation():
    """Test: Validar que Chunk rechaza datos inválidos."""
    with pytest.raises(ValueError, match="id cannot be empty"):
        Chunk(
            id="",
            page_content="test",
            metadata={}
        )
    
    with pytest.raises(ValueError, match="content cannot be empty"):
        Chunk(
            id="chunk_1",
            page_content="",
            metadata={}
        )


def test_document_type_from_filename():
    """Test: Detectar tipo de documento desde filename."""
    assert DocumentType.from_filename("test.md") == DocumentType.MARKDOWN
    assert DocumentType.from_filename("test.txt") == DocumentType.TXT
    assert DocumentType.from_filename("test.docx") == DocumentType.DOCX
    assert DocumentType.from_filename("test.pdf") == DocumentType.PDF
    
    with pytest.raises(ValueError):
        DocumentType.from_filename("test.unknown")

