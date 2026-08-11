"""
Tests para servicios de infrastructure.

Verifica que los servicios funcionan correctamente con datos reales.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.services.simple_text_cleaning_service import SimpleTextCleaningService
from infrastructure.services.langchain_document_loader_service import LangChainDocumentLoaderService
from infrastructure.services.langchain_chunking_service import LangChainChunkingService


def test_text_cleaning_service():
    """Test: Limpiar texto con SimpleTextCleaningService."""
    service = SimpleTextCleaningService()
    
    dirty_text = "Este   es   un   texto   con   espacios   extra"
    clean_text = service.clean(dirty_text)
    
    assert "  " not in clean_text  # No debe tener espacios dobles
    assert clean_text == "Este es un texto con espacios extra"


def test_document_loader_markdown(markdown_file):
    """Test: Cargar archivo Markdown real."""
    if not markdown_file.exists():
        pytest.skip(f"Archivo de prueba no encontrado: {markdown_file}")
    
    cleaning_service = SimpleTextCleaningService()
    loader = LangChainDocumentLoaderService(text_cleaning_service=cleaning_service)
    
    documents = loader.load(markdown_file, clean=True)
    
    assert len(documents) > 0
    assert documents[0].filename == markdown_file.name
    assert documents[0].file_type == "markdown"
    assert len(documents[0].content) > 0


def test_document_loader_txt(txt_file):
    """Test: Cargar archivo de texto real."""
    if not txt_file.exists():
        pytest.skip(f"Archivo de prueba no encontrado: {txt_file}")
    
    cleaning_service = SimpleTextCleaningService()
    loader = LangChainDocumentLoaderService(text_cleaning_service=cleaning_service)
    
    documents = loader.load(txt_file, clean=True)
    
    assert len(documents) > 0
    assert documents[0].filename == txt_file.name
    assert documents[0].file_type == "txt"
    assert len(documents[0].content) > 0


def test_chunking_service(markdown_file):
    """Test: Dividir documento en chunks."""
    if not markdown_file.exists():
        pytest.skip(f"Archivo de prueba no encontrado: {markdown_file}")
    
    # Cargar documento
    cleaning_service = SimpleTextCleaningService()
    loader = LangChainDocumentLoaderService(text_cleaning_service=cleaning_service)
    documents = loader.load(markdown_file, clean=True)
    
    # Dividir en chunks
    chunking_service = LangChainChunkingService()
    chunks = chunking_service.chunk(
        documents[0],
        chunk_size=500,  # Chunks pequeños para test
        chunk_overlap=100
    )
    
    assert len(chunks) > 0
    assert all(chunk.chunk_id_consecutive is not None for chunk in chunks)
    assert all(len(chunk.page_content) > 0 for chunk in chunks)
    
    # Verificar que los chunks son consecutivos
    consecutive_numbers = [chunk.chunk_id_consecutive for chunk in chunks]
    assert consecutive_numbers == list(range(1, len(chunks) + 1))


def test_document_loader_pdf(pdf_file):
    """Test: Cargar archivo PDF real."""
    if not pdf_file.exists():
        pytest.skip(f"Archivo PDF no encontrado: {pdf_file}")
    
    # Verificar que langchain-docling está disponible
    try:
        from langchain_docling import DoclingLoader
    except ImportError:
        pytest.skip("langchain-docling no está instalado. Instala con: pip install langchain-docling")
    
    cleaning_service = SimpleTextCleaningService()
    loader = LangChainDocumentLoaderService(text_cleaning_service=cleaning_service)
    
    # Verificar que el loader soporta PDF
    assert loader.supports(pdf_file), "El loader debe soportar archivos PDF"
    
    # Cargar PDF
    documents = loader.load(pdf_file, clean=True)
    
    assert len(documents) > 0, "Debe haber al menos un documento cargado"
    assert documents[0].filename == pdf_file.name, "El filename debe coincidir"
    assert documents[0].file_type == "pdf", "El tipo debe ser PDF"
    assert len(documents[0].content) > 0, "El contenido no debe estar vacío"
    
    # Verificar que el contenido tiene texto relevante del artículo
    content_lower = documents[0].content.lower()
    # El artículo menciona estos términos, así que deberían estar en el contenido
    expected_terms = ["qsar", "pubchem", "screening"]
    found_terms = [term for term in expected_terms if term in content_lower]
    assert len(found_terms) > 0, f"El contenido debe contener términos del artículo. Encontrados: {found_terms}"
