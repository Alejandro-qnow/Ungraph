"""
Tests de integración para Fase 2: Integración de patrones con ingesta.

Estos tests verifican que:
1. Neo4jChunkRepository.save_with_pattern() funciona correctamente
2. IngestDocumentUseCase.execute() acepta parámetro pattern
3. Backward compatibility se mantiene (sin pattern funciona igual)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Importar directamente sin pasar por src.__init__.py
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.entities.chunk import Chunk
from domain.value_objects.graph_pattern import GraphPattern, NodeDefinition
from domain.value_objects.predefined_patterns import FILE_PAGE_CHUNK_PATTERN
from infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository


class TestNeo4jChunkRepositorySaveWithPattern:
    """Tests para save_with_pattern() en Neo4jChunkRepository."""
    
    @pytest.fixture
    def mock_chunk(self):
        """Crea un chunk de prueba."""
        chunk = Chunk(
            id="chunk_1",
            page_content="Test content",
            metadata={"filename": "test.md", "page_number": 1}
        )
        chunk.embeddings = [0.1, 0.2, 0.3]
        chunk.embeddings_dimensions = 3
        chunk.is_unitary = False
        chunk.chunk_id_consecutive = 1
        chunk.embedding_encoder_info = "test_encoder"
        return chunk
    
    @pytest.fixture
    def repository(self):
        """Crea un repositorio de prueba."""
        return Neo4jChunkRepository(database="test_db")
    
    def test_save_with_pattern_file_page_chunk_uses_save_batch(self, repository, mock_chunk):
        """Verifica que FILE_PAGE_CHUNK usa save_batch() existente."""
        with patch.object(repository, 'save_batch') as mock_save_batch:
            repository.save_with_pattern([mock_chunk], FILE_PAGE_CHUNK_PATTERN)
            mock_save_batch.assert_called_once_with([mock_chunk])
    
    def test_save_with_pattern_custom_pattern_uses_pattern_service(self, repository, mock_chunk):
        """Verifica que patrones personalizados usan PatternService."""
        # Crear patrón simple
        simple_pattern = GraphPattern(
            name="SIMPLE_CHUNK",
            description="Solo chunks",
            node_definitions=[
                NodeDefinition(
                    label="Chunk",
                    required_properties={
                        "chunk_id": str,
                        "page_content": str,
                        "embeddings": list,
                        "embeddings_dimensions": int
                    }
                )
            ],
            relationship_definitions=[]
        )
        
        # Mockear Neo4jPatternService antes de que se importe dentro de save_with_pattern
        # El import es lazy dentro del método, así que necesitamos mockear el módulo completo
        with patch('infrastructure.services.neo4j_pattern_service.Neo4jPatternService') as mock_pattern_service_class:
            mock_pattern_service = MagicMock()
            mock_pattern_service_class.return_value = mock_pattern_service
            
            repository.save_with_pattern([mock_chunk], simple_pattern)
            
            # Verificar que se creó PatternService
            mock_pattern_service_class.assert_called_once_with(database="test_db")
            
            # Verificar que se llamó apply_pattern
            assert mock_pattern_service.apply_pattern.called
            
            # Verificar que se cerró el servicio
            mock_pattern_service.close.assert_called_once()
    
    def test_chunk_to_pattern_data_extracts_correct_data(self, repository, mock_chunk):
        """Verifica que _chunk_to_pattern_data extrae datos correctos."""
        data = repository._chunk_to_pattern_data(mock_chunk, FILE_PAGE_CHUNK_PATTERN)
        
        # Verificar datos de Chunk
        assert data['chunk_id'] == "chunk_1"
        assert data['page_content'] == "Test content"
        assert data['embeddings'] == [0.1, 0.2, 0.3]
        assert data['embeddings_dimensions'] == 3
        
        # Verificar datos de File y Page
        assert data['filename'] == "test.md"
        assert data['page_number'] == 1


class TestIngestDocumentUseCaseWithPattern:
    """Tests para IngestDocumentUseCase con soporte de patrones."""
    
    @pytest.fixture
    def mock_services(self):
        """Crea servicios mockeados."""
        return {
            'document_loader': MagicMock(),
            'chunking': MagicMock(),
            'embedding': MagicMock(),
            'index': MagicMock(),
            'repository': MagicMock()
        }
    
    def test_execute_without_pattern_uses_file_page_chunk(self, mock_services):
        """Verifica que sin pattern se usa FILE_PAGE_CHUNK."""
        from application.use_cases.ingest_document import IngestDocumentUseCase
        from domain.entities.document import Document
        from domain.entities.chunk import Chunk
        from domain.value_objects.embedding import Embedding
        
        use_case = IngestDocumentUseCase(
            document_loader_service=mock_services['document_loader'],
            chunking_service=mock_services['chunking'],
            embedding_service=mock_services['embedding'],
            index_service=mock_services['index'],
            chunk_repository=mock_services['repository']
        )
        
        # Configurar mocks
        mock_doc = Document(
            id="doc_1",
            filename="test.md",
            file_type="markdown",
            content="Test",
            metadata={}
        )
        mock_chunk = Chunk(id="c1", page_content="Test", metadata={})
        mock_embedding = Embedding(vector=[0.1], dimensions=1, encoder_info="test")
        
        mock_services['document_loader'].load.return_value = [mock_doc]
        mock_services['chunking'].chunk.return_value = [mock_chunk]
        mock_services['embedding'].generate_embeddings_batch.return_value = [mock_embedding]
        mock_services['repository'].save_with_pattern = MagicMock()
        
        # Ejecutar sin pattern (debería usar FILE_PAGE_CHUNK por defecto)
        result = use_case.execute(Path("test.md"))
        
        # Verificar que se llamó save_with_pattern con FILE_PAGE_CHUNK
        assert mock_services['repository'].save_with_pattern.called
        call_args = mock_services['repository'].save_with_pattern.call_args
        assert call_args[0][1].name == "FILE_PAGE_CHUNK"  # Segundo argumento es el pattern
    
    def test_execute_with_custom_pattern(self, mock_services):
        """Verifica que con pattern personalizado se usa ese patrón."""
        from application.use_cases.ingest_document import IngestDocumentUseCase
        from domain.entities.document import Document
        from domain.entities.chunk import Chunk
        from domain.value_objects.embedding import Embedding
        from domain.value_objects.graph_pattern import GraphPattern, NodeDefinition
        
        use_case = IngestDocumentUseCase(
            document_loader_service=mock_services['document_loader'],
            chunking_service=mock_services['chunking'],
            embedding_service=mock_services['embedding'],
            index_service=mock_services['index'],
            chunk_repository=mock_services['repository']
        )
        
        # Crear patrón personalizado
        custom_pattern = GraphPattern(
            name="CUSTOM",
            description="Custom pattern",
            node_definitions=[
                NodeDefinition(
                    label="Chunk",
                    required_properties={"chunk_id": str, "content": str}
                )
            ],
            relationship_definitions=[]
        )
        
        # Configurar mocks
        mock_doc = Document(
            id="doc_1",
            filename="test.md",
            file_type="markdown",
            content="Test",
            metadata={}
        )
        mock_chunk = Chunk(id="c1", page_content="Test", metadata={})
        mock_embedding = Embedding(vector=[0.1], dimensions=1, encoder_info="test")
        
        mock_services['document_loader'].load.return_value = [mock_doc]
        mock_services['chunking'].chunk.return_value = [mock_chunk]
        mock_services['embedding'].generate_embeddings_batch.return_value = [mock_embedding]
        mock_services['repository'].save_with_pattern = MagicMock()
        
        # Ejecutar con pattern personalizado
        result = use_case.execute(Path("test.md"), pattern=custom_pattern)
        
        # Verificar que se llamó save_with_pattern con el patrón personalizado
        assert mock_services['repository'].save_with_pattern.called
        call_args = mock_services['repository'].save_with_pattern.call_args
        assert call_args[0][1].name == "CUSTOM"  # Segundo argumento es el pattern


class TestBackwardCompatibility:
    """Tests para verificar backward compatibility."""
    
    def test_ingest_document_without_pattern_still_works(self):
        """Verifica que ingest_document() sin pattern funciona igual que antes."""
        # Este test requiere Neo4j real, así que lo marcamos como integración
        pytest.skip("Requires Neo4j connection - integration test")
    
    def test_ingest_document_with_pattern_works(self):
        """Verifica que ingest_document() con pattern funciona."""
        # Este test requiere Neo4j real, así que lo marcamos como integración
        pytest.skip("Requires Neo4j connection - integration test")

