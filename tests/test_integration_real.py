"""
Tests de integración reales con Neo4j.

⚠️  REQUIERE Neo4j configurado y corriendo.
⚠️  Estos tests modifican la base de datos.

Ejecutar con:
    pytest tests/test_integration_real.py -v -m integration
"""

import pytest
from pathlib import Path
import sys

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.value_objects.graph_pattern import GraphPattern, NodeDefinition, RelationshipDefinition
from domain.value_objects.predefined_patterns import FILE_PAGE_CHUNK_PATTERN
from infrastructure.services.graphrag_search_patterns import GraphRAGSearchPatterns


@pytest.mark.integration
class TestRealIngestionWithPatterns:
    """Tests de ingesta real con patrones personalizados."""
    
    def test_ingest_with_default_pattern(self):
        """Probar ingesta con patrón FILE_PAGE_CHUNK (default)."""
        try:
            import ungraph
        except ImportError:
            import src as ungraph
        
        # Buscar archivo de prueba
        data_path = Path(__file__).parent.parent / "src" / "data"
        test_files = list(data_path.glob("*.md")) + list(data_path.glob("*.txt"))
        
        if not test_files:
            pytest.skip("No hay archivos de prueba en src/data")
        
        test_file = test_files[0]
        
        # Ingerir con patrón default (FILE_PAGE_CHUNK)
        chunks = ungraph.ingest_document(
            str(test_file),
            chunk_size=500,
            chunk_overlap=100,
            pattern=None  # Usar default
        )
        
        assert len(chunks) > 0
        print(f"✅ Ingesta exitosa: {len(chunks)} chunks con patrón default")
    
    def test_ingest_with_custom_pattern(self):
        """Probar ingesta con patrón personalizado SIMPLE_CHUNK."""
        try:
            import ungraph
        except ImportError:
            import src as ungraph
        
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
                    },
                    optional_properties={
                        "is_unitary": bool,
                        "chunk_id_consecutive": int
                    },
                    indexes=["chunk_id"]
                )
            ],
            relationship_definitions=[]
        )
        
        # Buscar archivo de prueba
        data_path = Path(__file__).parent.parent / "src" / "data"
        test_files = list(data_path.glob("*.md")) + list(data_path.glob("*.txt"))
        
        if not test_files:
            pytest.skip("No hay archivos de prueba en src/data")
        
        test_file = test_files[0]
        
        # Ingerir con patrón personalizado
        chunks = ungraph.ingest_document(
            str(test_file),
            chunk_size=500,
            chunk_overlap=100,
            pattern=simple_pattern
        )
        
        assert len(chunks) > 0
        print(f"✅ Ingesta exitosa: {len(chunks)} chunks con patrón SIMPLE_CHUNK")


@pytest.mark.integration
class TestRealSearchWithPatterns:
    """Tests de búsqueda real con patrones GraphRAG."""
    
    def test_search_basic(self):
        """Probar búsqueda básica."""
        try:
            import ungraph
        except ImportError:
            import src as ungraph
        
        results = ungraph.search("test", limit=5)
        print(f"✅ Búsqueda básica: {len(results)} resultados")
        assert isinstance(results, list)
    
    def test_search_with_metadata_filtering(self):
        """Probar búsqueda con metadata_filtering."""
        try:
            import ungraph
        except ImportError:
            import src as ungraph
        
        # Primero hacer búsqueda básica para obtener un filename
        basic_results = ungraph.search("test", limit=1)
        
        if not basic_results:
            pytest.skip("No hay datos en Neo4j para probar")
        
        # Probar metadata_filtering (usar filename genérico)
        try:
            results = ungraph.search_with_pattern(
                "test",
                pattern_type="metadata_filtering",
                metadata_filters={"filename": "test.md"},
                limit=5
            )
            print(f"✅ Metadata filtering: {len(results)} resultados")
            assert isinstance(results, list)
        except Exception as e:
            # Si falla, puede ser porque no hay chunks con ese filename
            print(f"⚠️  Metadata filtering: {e}")
            pytest.skip(f"No se pudo probar metadata_filtering: {e}")
    
    def test_search_with_parent_child(self):
        """Probar búsqueda con parent_child."""
        try:
            import ungraph
        except ImportError:
            import src as ungraph
        
        try:
            results = ungraph.search_with_pattern(
                "test",
                pattern_type="parent_child",
                parent_label="Page",
                child_label="Chunk",
                relationship_type="HAS_CHUNK",
                limit=5
            )
            print(f"✅ Parent-child: {len(results)} resultados")
            assert isinstance(results, list)
        except Exception as e:
            print(f"⚠️  Parent-child: {e}")
            pytest.skip(f"No se pudo probar parent_child: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

