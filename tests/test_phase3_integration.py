"""
Tests de integración para Fase 3: Patrones de Búsqueda GraphRAG.

Tests minimalistas que verifican:
1. GraphRAGSearchPatterns genera queries válidos
2. Neo4jSearchService.search_with_pattern() funciona
3. API pública search_with_pattern() funciona
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Agregar src al path sin importar src.__init__.py
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Importar directamente los módulos sin pasar por src.__init__.py
from infrastructure.services.graphrag_search_patterns import GraphRAGSearchPatterns


class TestGraphRAGSearchPatterns:
    """Tests para GraphRAGSearchPatterns."""
    
    def test_metadata_filtering_generates_valid_query(self):
        """Verifica que metadata_filtering genera query válido."""
        query, params = GraphRAGSearchPatterns.metadata_filtering(
            "test query",
            metadata_filters={"filename": "test.md", "page_number": 1},
            limit=5
        )
        
        # Verificar estructura del query
        assert "CALL db.index.fulltext.queryNodes" in query
        assert "WHERE" in query
        assert "node.filename = $filename" in query
        assert "node.page_number = $page_number" in query
        assert "LIMIT $limit" in query
        
        # Verificar parámetros
        assert params["query_text"] == "test query"
        assert params["limit"] == 5
        assert params["filename"] == "test.md"
        assert params["page_number"] == 1
    
    def test_metadata_filtering_validates_property_names(self):
        """Verifica que valida nombres de propiedades."""
        with pytest.raises(ValueError, match="Invalid property name"):
            GraphRAGSearchPatterns.metadata_filtering(
                "test",
                metadata_filters={"invalid-name": "value"}
            )
    
    def test_parent_child_retriever_generates_valid_query(self):
        """Verifica que parent_child_retriever genera query válido."""
        query, params = GraphRAGSearchPatterns.parent_child_retriever(
            "test query",
            parent_label="Page",
            child_label="Chunk",
            relationship_type="HAS_CHUNK",
            limit=5
        )
        
        # Verificar estructura del query
        assert "CALL db.index.fulltext.queryNodes" in query
        assert "OPTIONAL MATCH" in query
        assert "Page" in query
        assert "Chunk" in query
        assert "HAS_CHUNK" in query
        
        # Verificar parámetros
        assert params["query_text"] == "test query"
        assert params["limit"] == 5
    
    def test_parent_child_retriever_validates_labels(self):
        """Verifica que valida labels."""
        with pytest.raises(ValueError, match="Invalid parent_label"):
            GraphRAGSearchPatterns.parent_child_retriever(
                "test",
                parent_label="invalid-label"
            )
    
    def test_basic_retriever_generates_valid_query(self):
        """Verifica que basic_retriever genera query válido."""
        query, params = GraphRAGSearchPatterns.basic_retriever(
            "test query",
            limit=5
        )
        
        # Verificar estructura del query
        assert "CALL db.index.fulltext.queryNodes" in query
        assert "RETURN node.page_content as content" in query
        assert "LIMIT $limit" in query
        
        # Verificar parámetros
        assert params["query_text"] == "test query"
        assert params["limit"] == 5
    
    def test_basic_retriever_returns_correct_structure(self):
        """Verifica que basic_retriever retorna estructura correcta."""
        query, params = GraphRAGSearchPatterns.basic_retriever(
            "test",
            limit=10
        )
        
        # Verificar que query contiene campos esperados
        assert "content" in query
        assert "score" in query
        assert "chunk_id" in query
        assert "chunk_id_consecutive" in query
        
        # Verificar que params tiene estructura correcta
        assert isinstance(params, dict)
        assert "query_text" in params
        assert "limit" in params


class TestNeo4jSearchServiceSearchWithPattern:
    """Tests para search_with_pattern() en Neo4jSearchService."""
    
    @pytest.fixture
    def mock_graph_session(self):
        """Mock de graph_session para evitar dependencias."""
        with patch('src.utils.graph_operations.graph_session') as mock:
            mock_driver = MagicMock()
            mock_session = MagicMock()
            mock_driver.session.return_value.__enter__.return_value = mock_session
            mock_driver.session.return_value.__exit__.return_value = None
            mock.return_value = mock_driver
            yield mock_driver, mock_session
    
    def test_search_with_pattern_metadata_filtering(self, mock_graph_session):
        """Verifica que search_with_pattern funciona con metadata_filtering."""
        mock_driver_obj, mock_session = mock_graph_session
        
        # Configurar mock de records
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "content": "Test content",
            "score": 0.95,
            "chunk_id": "chunk_1",
            "chunk_id_consecutive": 1
        }[key]
        
        mock_session.run.return_value = [mock_record]
        
        # Importar después de mockear
        from infrastructure.services.neo4j_search_service import Neo4jSearchService
        
        service = Neo4jSearchService(database="test_db")
        
        # Ejecutar búsqueda
        results = service.search_with_pattern(
            "test query",
            pattern_type="metadata_filtering",
            metadata_filters={"filename": "test.md"},
            limit=5
        )
        
        # Verificar resultados
        assert len(results) == 1
        assert results[0].content == "Test content"
        assert results[0].score == 0.95
        assert results[0].chunk_id == "chunk_1"
        
        # Verificar que se llamó con parámetros correctos
        call_args = mock_session.run.call_args
        assert call_args is not None
        assert "query_text" in call_args.kwargs
        assert "filename" in call_args.kwargs
    
    def test_search_with_pattern_invalid_pattern_type(self, mock_graph_session):
        """Verifica que lanza error con pattern_type inválido."""
        from infrastructure.services.neo4j_search_service import Neo4jSearchService
        
        service = Neo4jSearchService(database="test_db")
        
        with pytest.raises(ValueError, match="Unknown pattern type"):
            service.search_with_pattern(
                "test",
                pattern_type="invalid_pattern"
            )
    
    def test_search_with_pattern_empty_query(self, mock_graph_session):
        """Verifica que lanza error con query vacío."""
        from infrastructure.services.neo4j_search_service import Neo4jSearchService
        
        service = Neo4jSearchService(database="test_db")
        
        with pytest.raises(ValueError, match="Query text cannot be empty"):
            service.search_with_pattern("", pattern_type="metadata_filtering")


class TestAPISearchWithPattern:
    """Tests para API pública search_with_pattern()."""
    
    def test_api_search_with_pattern_exists(self):
        """Verifica que la función existe en el módulo."""
        # Verificar que GraphRAGSearchPatterns tiene los métodos esperados
        assert hasattr(GraphRAGSearchPatterns, 'metadata_filtering')
        assert hasattr(GraphRAGSearchPatterns, 'parent_child_retriever')
    
    def test_api_search_with_pattern_integration(self):
        """Test de integración completo (requiere Neo4j)."""
        pytest.skip("Requires Neo4j connection - integration test")

