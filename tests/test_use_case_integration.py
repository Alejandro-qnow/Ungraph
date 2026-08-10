"""
Tests de integración para el caso de uso completo.

Verifica el flujo completo usando datos reales.
Estos tests pueden requerir Neo4j corriendo (se pueden marcar como skip si no está disponible).
"""

import pytest
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.dependencies import create_ingest_document_use_case


def test_ingest_document_use_case_creation():
    """Test: Crear el caso de uso usando el Composition Root."""
    use_case = create_ingest_document_use_case()
    
    assert use_case is not None
    assert use_case.document_loader_service is not None
    assert use_case.chunking_service is not None
    assert use_case.embedding_service is not None
    assert use_case.index_service is not None
    assert use_case.chunk_repository is not None


@pytest.mark.integration
def test_full_ingestion_flow(markdown_file):
    """
    Test: Flujo completo de ingestión con datos reales.
    
    Este test requiere:
    - Neo4j corriendo
    - Variables de entorno NEO4J_URI y NEO4J_PASSWORD configuradas
    
    Para ejecutar solo este test:
        pytest tests/test_use_case_integration.py::test_full_ingestion_flow -v
    """
    # Verificar que Neo4j está disponible
    if not os.environ.get("NEO4J_URI") or not os.environ.get("NEO4J_PASSWORD"):
        pytest.skip("Neo4j no configurado (NEO4J_URI o NEO4J_PASSWORD no están definidas)")
    
    if not markdown_file.exists():
        pytest.skip(f"Archivo de prueba no encontrado: {markdown_file}")
    
    # Crear caso de uso
    use_case = create_ingest_document_use_case()
    
    try:
        # Ejecutar ingestión
        chunks = use_case.execute(
            file_path=markdown_file,
            chunk_size=500,  # Chunks pequeños para test rápido
            chunk_overlap=100,
            clean_text=True
        )
        
        # Verificar resultados
        assert len(chunks) > 0
        assert all(chunk.embeddings is not None for chunk in chunks)
        assert all(chunk.embeddings_dimensions == 384 for chunk in chunks)
        assert all(chunk.chunk_id_consecutive is not None for chunk in chunks)
        
        print(f"\n✅ Ingestión exitosa: {len(chunks)} chunks creados")
        
    finally:
        # Limpiar recursos
        if hasattr(use_case.chunk_repository, 'close'):
            use_case.chunk_repository.close()
        if hasattr(use_case.index_service, 'close'):
            use_case.index_service.close()

