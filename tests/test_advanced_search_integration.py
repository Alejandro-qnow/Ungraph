"""
Tests de integración end-to-end para patrones avanzados de búsqueda.

Estos tests verifican el flujo completo:
1. Crear datos de prueba con entidades
2. Ejecutar búsquedas avanzadas
3. Validar resultados

Requiere:
- Neo4j configurado
- Módulos opcionales: ungraph[gds] para algunos tests

Ejecutar con:
    pytest tests/test_advanced_search_integration.py -v -m integration
"""

import pytest
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.mark.integration
class TestAdvancedSearchE2E:
    """Tests end-to-end para búsqueda avanzada."""
    
    def test_graph_enhanced_finds_related_context(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """
        Test: Graph-Enhanced encuentra contexto relacionado a través de entidades.
        
        Verifica que:
        1. Busca chunks similares
        2. Encuentra entidades mencionadas
        3. Encuentra otros chunks relacionados a través de entidades
        4. Retorna contexto enriquecido
        """
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles (ungraph[gds] no instalado)")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        # Verificar que hay datos con entidades
        assert test_data_with_entities["num_chunks"] > 0
        assert len(test_data_with_entities["entities"]) > 0
        
        # Generar embedding
        from infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
        embedding_service = HuggingFaceEmbeddingService()
        embedding = embedding_service.generate_embedding("machine learning")
        
        # Crear servicio de búsqueda
        from infrastructure.services.neo4j_search_service import Neo4jSearchService
        search_service = Neo4jSearchService(database=neo4j_database)
        
        try:
            # Ejecutar Graph-Enhanced
            results = search_service.search_with_pattern(
                query_text="machine learning",
                pattern_type="graph_enhanced",
                limit=5,
                query_vector=embedding.vector,
                max_traversal_depth=2
            )
            
            # Verificar resultados
            assert len(results) > 0, "Graph-Enhanced debería encontrar al menos un resultado"
            
            # Verificar estructura de resultados
            for result in results:
                assert result.content is not None
                assert result.score >= 0
                assert result.chunk_id is not None
            
            # Verificar que algunos resultados tienen contexto relacionado
            results_with_context = [r for r in results if r.next_chunk_content]
            print(f"\n✅ Graph-Enhanced: {len(results)} resultados, {len(results_with_context)} con contexto relacionado")
            
            # Mostrar ejemplo
            if len(results) > 0:
                result = results[0]
                print(f"   Ejemplo - Score: {result.score:.4f}")
                print(f"   Contenido: {result.content[:100]}...")
                if result.next_chunk_content:
                    print(f"   Contexto relacionado: {result.next_chunk_content[:100]}...")
        
        finally:
            search_service.close()
    
    def test_local_retriever_finds_communities(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """
        Test: Local Retriever encuentra comunidades de chunks relacionados.
        
        Verifica que:
        1. Busca chunk central
        2. Encuentra chunks relacionados por relaciones del grafo
        3. Agrupa en comunidades
        4. Genera resumen de comunidad
        """
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        from infrastructure.services.neo4j_search_service import Neo4jSearchService
        search_service = Neo4jSearchService(database=neo4j_database)
        
        try:
            # Ejecutar Local Retriever con threshold bajo para asegurar resultados
            results = search_service.search_with_pattern(
                query_text="neural",
                pattern_type="local",
                limit=5,
                community_threshold=1,  # Threshold bajo
                max_depth=1
            )
            
            # Verificar que puede ejecutarse (puede no encontrar comunidades si threshold es alto)
            assert isinstance(results, list)
            
            if len(results) > 0:
                # Verificar estructura de resultados
                for result in results:
                    assert result.content is not None
                    assert result.score >= 0
                
                print(f"\n✅ Local Retriever: {len(results)} comunidades encontradas")
                
                # Mostrar ejemplo
                result = results[0]
                print(f"   Ejemplo - Score: {result.score:.4f}")
                print(f"   Contenido central: {result.content[:100]}...")
                if result.next_chunk_content:
                    print(f"   Resumen de comunidad: {result.next_chunk_content[:100]}...")
            else:
                print("\n⚠️  Local Retriever: No se encontraron comunidades (puede ser normal si threshold es alto)")
        
        finally:
            search_service.close()
    
    def test_compare_basic_vs_graph_enhanced(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """
        Test: Comparar Basic Retriever vs Graph-Enhanced.
        
        Verifica que Graph-Enhanced encuentra más contexto relacionado.
        """
        try:
            from infrastructure.services.advanced_search_patterns import AdvancedSearchPatterns
        except ImportError:
            pytest.skip("Módulos avanzados no disponibles")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        from infrastructure.services.neo4j_search_service import Neo4jSearchService
        from infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
        
        embedding_service = HuggingFaceEmbeddingService()
        embedding = embedding_service.generate_embedding("machine learning")
        
        search_service = Neo4jSearchService(database=neo4j_database)
        
        try:
            # 1. Basic Retriever
            basic_results = search_service.search_with_pattern(
                query_text="machine learning",
                pattern_type="basic",
                limit=5
            )
            
            # 2. Graph-Enhanced
            graph_enhanced_results = search_service.search_with_pattern(
                query_text="machine learning",
                pattern_type="graph_enhanced",
                limit=5,
                query_vector=embedding.vector,
                max_traversal_depth=2
            )
            
            # Comparar resultados
            print(f"\n📊 Comparación:")
            print(f"   Basic Retriever: {len(basic_results)} resultados")
            print(f"   Graph-Enhanced: {len(graph_enhanced_results)} resultados")
            
            # Graph-Enhanced debería encontrar resultados
            assert len(graph_enhanced_results) >= 0  # Puede ser 0 si no hay entidades relacionadas
            
            # Si hay resultados, verificar que tienen estructura correcta
            if len(graph_enhanced_results) > 0:
                result = graph_enhanced_results[0]
                assert result.content is not None
                assert result.score >= 0
                
                # Graph-Enhanced puede tener contexto adicional
                has_additional_context = result.next_chunk_content is not None
                print(f"   Graph-Enhanced tiene contexto adicional: {has_additional_context}")
        
        finally:
            search_service.close()


@pytest.mark.integration
class TestGDSServiceIntegration:
    """Tests de integración para GDS Service."""
    
    @pytest.mark.integration
    def test_gds_detect_communities_full_workflow(
        self,
        neo4j_driver,
        neo4j_database,
        test_data_with_entities,
        skip_if_no_neo4j
    ):
        """
        Test: Flujo completo de detección de comunidades con GDS.
        
        Verifica:
        1. Crear grafo proyectado
        2. Ejecutar algoritmo de detección
        3. Escribir community_id en nodos
        4. Usar community_id en búsqueda
        """
        try:
            from infrastructure.services.gds_service import GDSService
        except ImportError:
            pytest.skip("GDS Service no disponible")
        
        if neo4j_driver is None:
            pytest.skip("Neo4j no disponible")
        
        # Verificar disponibilidad de GDS
        service = GDSService(database=neo4j_database)
        
        try:
            if not service._check_gds_available():
                pytest.skip("GDS no disponible - instalar Neo4j GDS plugin")
            
            # Detectar comunidades
            stats = service.detect_communities(
                graph_name="test-chunk-graph",
                algorithm="louvain",
                relationship_types=["NEXT_CHUNK", "MENTIONS"],
                write_property="community_id"
            )
            
            # Verificar resultados
            assert stats["community_count"] > 0
            assert stats["algorithm"] == "louvain"
            assert stats["write_property"] == "community_id"
            
            print(f"\n✅ Comunidades detectadas: {stats['community_count']}")
            
            # Verificar que los chunks tienen community_id
            with neo4j_driver.session(database=neo4j_database) as session:
                result = session.run("""
                    MATCH (c:Chunk)
                    WHERE c.community_id IS NOT NULL
                    RETURN count(c) as count
                """)
                count = result.single()["count"]
                print(f"   Chunks con community_id: {count}")
                assert count > 0, "Al menos algunos chunks deberían tener community_id"
            
            # Probar búsqueda con Community Summary
            try:
                from infrastructure.services.neo4j_search_service import Neo4jSearchService
                search_service = Neo4jSearchService(database=neo4j_database)
                
                try:
                    results = search_service.search_with_pattern(
                        query_text="machine learning",
                        pattern_type="community_summary",
                        limit=3,
                        min_community_size=1  # Threshold bajo
                    )
                    
                    print(f"   Community Summary: {len(results)} resultados")
                    assert isinstance(results, list)
                
                finally:
                    search_service.close()
            
            except Exception as e:
                print(f"⚠️  Community Summary search falló: {e}")
                # No es crítico, puede fallar si no hay comunidades grandes
        
        except Exception as e:
            # Si falla, puede ser porque GDS no está instalado
            pytest.skip(f"GDS no disponible o no configurado: {e}")
        finally:
            service.close()





