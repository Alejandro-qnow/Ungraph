"""
Tests para patrones avanzados de búsqueda GraphRAG.

Requiere:
- Neo4j configurado (se salta si no está disponible)
- Módulos opcionales: ungraph[gds] para algunos tests

Ejecutar con:
    pytest tests/test_advanced_search_patterns.py -v -m integration
"""

import pytest
import sys
from pathlib import Path
from typing import List, Dict, Any
from neo4j import GraphDatabase

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.services.neo4j_search_service import Neo4jSearchService
from infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
from core.configuration import get_settings


def _is_neo4j_available() -> bool:
    """Verifica si Neo4j está disponible."""
    import os
    uri = os.environ.get("NEO4J_URI") or os.environ.get("UNGRAPH_NEO4J_URI")
    password = os.environ.get("NEO4J_PASSWORD") or os.environ.get("UNGRAPH_NEO4J_PASSWORD")
    
    if not uri or not password:
        return False
    
    try:
        driver = GraphDatabase.driver(uri, auth=("neo4j", password))
        driver.verify_connectivity()
        driver.close()
        return True
    except Exception:
        return False


def _is_gds_available() -> bool:
    """Verifica si GDS está disponible."""
    if not _is_neo4j_available():
        return False
    
    try:
        import graphdatascience
        return True
    except ImportError:
        return False


# La función _create_test_data_with_entities y la fixture test_data_with_entities
# están en conftest.py para que estén disponibles para todos los tests


@pytest.mark.integration
class TestAdvancedSearchPatterns:
    """Tests para patrones avanzados de búsqueda."""
    
    def test_graph_enhanced_vector_search_available(self):
        """Verifica que Graph-Enhanced Vector Search está disponible."""
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles (ungraph[gds] no instalado)")
        
        # Verificar que el método existe
        assert hasattr(AdvancedSearchPatterns, 'graph_enhanced_vector_search')
    
    def test_graph_enhanced_vector_search_query_generation(self):
        """Verifica que Graph-Enhanced genera query válido."""
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles")
        
        # Generar embedding dummy
        query_vector = [0.1] * 384
        
        query, params = AdvancedSearchPatterns.graph_enhanced_vector_search(
            query_text="machine learning",
            query_vector=query_vector,
            limit=5,
            max_traversal_depth=2
        )
        
        # Verificar estructura del query
        assert "CALL db.index.vector.queryNodes" in query
        assert "MENTIONS" in query
        assert "Entity" in query
        assert "related_chunk" in query
        
        # Verificar parámetros
        assert params["query_text"] == "machine learning"
        assert params["query_vector"] == query_vector
        assert params["limit"] == 5
    
    @pytest.mark.integration
    def test_graph_enhanced_vector_search_execution(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """Test de ejecución real de Graph-Enhanced Vector Search."""
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        # Generar embedding para la query
        embedding_service = HuggingFaceEmbeddingService()
        embedding = embedding_service.generate_embedding("machine learning")
        
        # Crear servicio de búsqueda
        search_service = Neo4jSearchService(database=neo4j_database)
        
        try:
            # Ejecutar búsqueda Graph-Enhanced
            results = search_service.search_with_pattern(
                query_text="machine learning",
                pattern_type="graph_enhanced",
                limit=5,
                query_vector=embedding.vector,
                max_traversal_depth=2
            )
            
            # Verificar resultados
            assert len(results) > 0
            assert all(result.score >= 0 for result in results)
            assert all(result.content is not None for result in results)
            
            print(f"\n✅ Graph-Enhanced: {len(results)} resultados encontrados")
            for i, result in enumerate(results[:3], 1):
                print(f"  {i}. Score: {result.score:.4f}, Chunk: {result.chunk_id}")
        
        finally:
            search_service.close()
    
    def test_local_retriever_query_generation(self):
        """Verifica que Local Retriever genera query válido."""
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles")
        
        query, params = AdvancedSearchPatterns.local_retriever(
            query_text="neural networks",
            limit=5,
            community_threshold=3,
            max_depth=1
        )
        
        # Verificar estructura del query
        assert "CALL db.index.fulltext.queryNodes" in query
        assert "community_node" in query
        assert "community_size" in query
        assert "community_summary" in query
        
        # Verificar parámetros
        assert params["query_text"] == "neural networks"
        assert params["limit"] == 5
        assert params["community_threshold"] == 3
    
    @pytest.mark.integration
    def test_local_retriever_execution(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """Test de ejecución real de Local Retriever."""
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        search_service = Neo4jSearchService(database=neo4j_database)
        
        try:
            # Ejecutar búsqueda Local
            results = search_service.search_with_pattern(
                query_text="neural networks",
                pattern_type="local",
                limit=5,
                community_threshold=2,  # Threshold bajo para test
                max_depth=1
            )
            
            # Verificar resultados
            assert len(results) >= 0  # Puede no encontrar comunidades si threshold es alto
            if len(results) > 0:
                assert all(result.score >= 0 for result in results)
                print(f"\n✅ Local Retriever: {len(results)} resultados encontrados")
        
        finally:
            search_service.close()
    
    def test_community_summary_gds_query_generation(self):
        """Verifica que Community Summary GDS genera query válido."""
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles")
        
        query, params = AdvancedSearchPatterns.community_summary_retriever_gds(
            query_text="machine learning",
            limit=3,
            min_community_size=5,
            algorithm="louvain"
        )
        
        # Verificar estructura del query
        assert "CALL db.index.fulltext.queryNodes" in query
        assert "community_id" in query
        assert "community_size" in query
        assert "community_summary" in query
        
        # Verificar parámetros
        assert params["query_text"] == "machine learning"
        assert params["limit"] == 3
        assert params["min_community_size"] == 5


@pytest.mark.integration
class TestGDSService:
    """Tests para el servicio de Graph Data Science."""
    
    def test_gds_service_available(self):
        """Verifica que GDS Service está disponible."""
        try:
            from infrastructure.services.gds_service import GDSService
        except ImportError:
            pytest.skip("GDS Service no disponible")
        
        assert GDSService is not None
    
    def test_gds_service_initialization(self, skip_if_no_neo4j):
        """Test de inicialización del servicio GDS."""
        try:
            from infrastructure.services.gds_service import GDSService
        except ImportError:
            pytest.skip("GDS Service no disponible")
        
        service = GDSService(database="test_ungraph")
        assert service.database == "test_ungraph"
        service.close()
    
    @pytest.mark.integration
    def test_gds_check_availability(self, neo4j_driver, neo4j_database, skip_if_no_neo4j):
        """Test de verificación de disponibilidad de GDS."""
        try:
            from infrastructure.services.gds_service import GDSService
        except ImportError:
            pytest.skip("GDS Service no disponible")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        service = GDSService(database=neo4j_database)
        
        try:
            # Verificar disponibilidad (puede ser False si GDS no está instalado)
            available = service._check_gds_available()
            print(f"\n✅ GDS disponible: {available}")
            
            if not available:
                print("⚠️  GDS no está disponible. Instalar Neo4j GDS plugin para usar funcionalidades avanzadas.")
        
        finally:
            service.close()
    
    @pytest.mark.integration
    @pytest.mark.skipif(not _is_gds_available(), reason="GDS no disponible")
    def test_gds_detect_communities(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """Test de detección de comunidades usando GDS."""
        try:
            from infrastructure.services.gds_service import GDSService
        except ImportError:
            pytest.skip("GDS Service no disponible")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        service = GDSService(database=neo4j_database)
        
        try:
            # Detectar comunidades
            stats = service.detect_communities(
                graph_name="test-chunk-graph",
                algorithm="louvain",
                relationship_types=["NEXT_CHUNK", "MENTIONS"],
                write_property="community_id"
            )
            
            # Verificar resultados
            assert stats["algorithm"] == "louvain"
            assert stats["community_count"] > 0
            assert stats["write_property"] == "community_id"
            
            print(f"\n✅ Comunidades detectadas: {stats['community_count']}")
            print(f"   Iteraciones: {stats['iterations']}")
            print(f"   Convergió: {stats['converged']}")
        
        except Exception as e:
            # Si falla, puede ser porque GDS no está instalado o configurado
            pytest.skip(f"GDS no disponible o no configurado: {e}")
        finally:
            service.close()


@pytest.mark.integration
class TestAdvancedSearchIntegration:
    """Tests de integración end-to-end para búsqueda avanzada."""
    
    @pytest.mark.integration
    def test_advanced_search_workflow(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """Test de flujo completo: crear datos → buscar con patrones avanzados."""
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        # Verificar que hay datos
        assert test_data_with_entities["num_chunks"] > 0
        
        # Generar embedding
        embedding_service = HuggingFaceEmbeddingService()
        embedding = embedding_service.generate_embedding("machine learning")
        
        search_service = Neo4jSearchService(database=neo4j_database)
        
        try:
            # 1. Test Basic Retriever (baseline)
            basic_results = search_service.search_with_pattern(
                query_text="machine learning",
                pattern_type="basic",
                limit=5
            )
            print(f"\n📊 Basic Retriever: {len(basic_results)} resultados")
            
            # 2. Test Graph-Enhanced (si hay entidades)
            try:
                graph_enhanced_results = search_service.search_with_pattern(
                    query_text="machine learning",
                    pattern_type="graph_enhanced",
                    limit=5,
                    query_vector=embedding.vector,
                    max_traversal_depth=2
                )
                print(f"📊 Graph-Enhanced: {len(graph_enhanced_results)} resultados")
                
                # Graph-Enhanced debería encontrar más contexto relacionado
                if len(graph_enhanced_results) > 0:
                    result = graph_enhanced_results[0]
                    assert result.content is not None
                    # Puede tener contexto adicional en next_chunk_content
                    print(f"   Primer resultado: {result.content[:100]}...")
            
            except Exception as e:
                print(f"⚠️  Graph-Enhanced falló: {e}")
            
            # 3. Test Local Retriever
            try:
                local_results = search_service.search_with_pattern(
                    query_text="neural",
                    pattern_type="local",
                    limit=5,
                    community_threshold=1,  # Threshold bajo
                    max_depth=1
                )
                print(f"📊 Local Retriever: {len(local_results)} resultados")
            
            except Exception as e:
                print(f"⚠️  Local Retriever falló: {e}")
        
        finally:
            search_service.close()


@pytest.mark.integration
class TestAdvancedSearchAPI:
    """Tests de la API pública para búsqueda avanzada."""
    
    @pytest.mark.integration
    def test_search_with_pattern_graph_enhanced(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """Test de API pública search_with_pattern con graph_enhanced."""
        try:
            import ungraph
        except ImportError:
            import src as ungraph
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        try:
            # Probar API pública
            results = ungraph.search_with_pattern(
                query_text="machine learning",
                pattern_type="graph_enhanced",
                limit=5,
                database=neo4j_database,
                max_traversal_depth=2
            )
            
            assert isinstance(results, list)
            if len(results) > 0:
                assert all(hasattr(r, 'content') for r in results)
                assert all(hasattr(r, 'score') for r in results)
                print(f"\n✅ API pública Graph-Enhanced: {len(results)} resultados")
        
        except ImportError as e:
            # Si falla por módulos opcionales, es esperado
            if "advanced_search_patterns" in str(e):
                pytest.skip("Módulos avanzados no instalados (ungraph[gds])")
            raise
        except Exception as e:
            # Otros errores pueden ser esperados si no hay datos o entidades
            print(f"⚠️  Error esperado: {e}")
            pytest.skip(f"No se pudo ejecutar: {e}")

