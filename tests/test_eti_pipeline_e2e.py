"""
Tests end-to-end para el pipeline ETI completo.

Verifica que el pipeline Extract-Transform-Inference funciona correctamente
con datos reales y persiste facts en Neo4j.

Este test requiere:
- Neo4j corriendo
- Variables de entorno NEO4J_URI y NEO4J_PASSWORD configuradas
- spaCy instalado (opcional, el test se salta si no está disponible)

Para ejecutar:
    pytest tests/test_eti_pipeline_e2e.py -v -m e2e
"""

import pytest
import os
from pathlib import Path
import sys
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from application.dependencies import create_ingest_document_use_case, create_inference_service
from domain.entities.chunk import Chunk
from domain.entities.fact import Fact
from neo4j import GraphDatabase


def _is_spacy_available() -> bool:
    """Verifica si spaCy está disponible."""
    try:
        import spacy
        # Intentar cargar un modelo básico
        try:
            nlp = spacy.load("en_core_web_sm")
            return True
        except OSError:
            # Modelo no descargado
            return False
    except ImportError:
        return False


@pytest.mark.e2e
def test_eti_pipeline_without_inference(markdown_file, clean_neo4j_database, neo4j_driver, neo4j_database):
    """
    Test: Pipeline ETI sin fase de inference (solo Extract + Transform).
    
    Verifica que el pipeline funciona correctamente cuando inference_service es None.
    """
    if neo4j_driver is None:
        pytest.skip("Neo4j no disponible - configurar NEO4J_URI y NEO4J_PASSWORD")
    
    if not markdown_file.exists():
        pytest.skip(f"Archivo de prueba no encontrado: {markdown_file}")
    
    # Crear caso de uso SIN inference
    use_case = create_ingest_document_use_case(enable_inference=False)
    
    assert use_case is not None
    assert use_case.inference_service is None, "Inference service debe ser None cuando enable_inference=False"
    
    try:
        # Ejecutar pipeline ET (sin Inference)
        chunks = use_case.execute(
            file_path=markdown_file,
            chunk_size=500,
            chunk_overlap=100,
            clean_text=True
        )
        
        # Verificar resultados de Extract + Transform
        assert len(chunks) > 0, "Debe generar al menos un chunk"
        assert all(chunk.embeddings is not None for chunk in chunks), "Todos los chunks deben tener embeddings"
        assert all(chunk.embeddings_dimensions == 384 for chunk in chunks), "Embeddings deben tener 384 dimensiones"
        
        # Verificar persistencia en Neo4j
        with neo4j_driver.session(database=neo4j_database) as session:
            result = session.run("""
                MATCH (c:Chunk)
                RETURN count(c) as chunk_count
            """)
            chunk_count = result.single()["chunk_count"]
            assert chunk_count == len(chunks), f"Debe haber {len(chunks)} chunks en Neo4j, pero hay {chunk_count}"
        
        print(f"\n✅ Pipeline ET (sin Inference) exitoso: {len(chunks)} chunks creados")
        
    finally:
        # Limpiar recursos
        if hasattr(use_case.chunk_repository, 'close'):
            use_case.chunk_repository.close()


@pytest.mark.e2e
def test_eti_pipeline_with_inference(markdown_file, clean_neo4j_database, neo4j_driver, neo4j_database):
    """
    Test: Pipeline ETI completo con fase de inference.
    
    Verifica:
    1. Extract: Carga de documento
    2. Transform: Chunking y embeddings
    3. Inference: Extracción de facts desde chunks
    4. Persistencia: Chunks y facts en Neo4j
    5. Trazabilidad: Facts tienen provenance_ref apuntando a chunks
    """
    if neo4j_driver is None:
        pytest.skip("Neo4j no disponible - configurar NEO4J_URI y NEO4J_PASSWORD")
    
    if not markdown_file.exists():
        pytest.skip(f"Archivo de prueba no encontrado: {markdown_file}")
    
    # Verificar si spaCy está disponible
    if not _is_spacy_available():
        pytest.skip("spaCy no disponible - instalar con: pip install spacy && python -m spacy download en_core_web_sm")
    
    # Crear caso de uso CON inference
    use_case = create_ingest_document_use_case(enable_inference=True)
    
    assert use_case is not None
    assert use_case.inference_service is not None, "Inference service debe estar configurado cuando enable_inference=True"
    
    try:
        # Ejecutar pipeline ETI completo
        chunks = use_case.execute(
            file_path=markdown_file,
            chunk_size=500,
            chunk_overlap=100,
            clean_text=True
        )
        
        # Verificar resultados de Extract + Transform
        assert len(chunks) > 0, "Debe generar al menos un chunk"
        assert all(chunk.embeddings is not None for chunk in chunks), "Todos los chunks deben tener embeddings"
        
        # Verificar persistencia de chunks en Neo4j
        with neo4j_driver.session(database=neo4j_database) as session:
            # Contar chunks
            result = session.run("""
                MATCH (c:Chunk)
                RETURN count(c) as chunk_count
            """)
            chunk_count = result.single()["chunk_count"]
            assert chunk_count == len(chunks), f"Debe haber {len(chunks)} chunks en Neo4j"
            
            # Verificar que hay facts persistidos
            result = session.run("""
                MATCH (f:Fact)
                RETURN count(f) as fact_count
            """)
            fact_count = result.single()["fact_count"]
            assert fact_count > 0, "Debe haber al menos un fact persistido en Neo4j"
            
            # Verificar trazabilidad: Facts deben tener relación DERIVED_FROM con chunks
            result = session.run("""
                MATCH (f:Fact)-[:DERIVED_FROM]->(c:Chunk)
                RETURN count(f) as facts_with_provenance
            """)
            facts_with_provenance = result.single()["facts_with_provenance"]
            assert facts_with_provenance > 0, "Al menos un fact debe tener relación DERIVED_FROM con un chunk"
            
            # Verificar estructura de facts: deben tener subject, predicate, object, confidence
            result = session.run("""
                MATCH (f:Fact)
                WHERE f.subject IS NOT NULL 
                  AND f.predicate IS NOT NULL 
                  AND f.object IS NOT NULL
                  AND f.confidence IS NOT NULL
                RETURN count(f) as valid_facts
            """)
            valid_facts = result.single()["valid_facts"]
            assert valid_facts == fact_count, "Todos los facts deben tener subject, predicate, object y confidence"
            
            # Obtener algunos facts de ejemplo para verificación
            result = session.run("""
                MATCH (f:Fact)
                RETURN f.subject as subject, f.predicate as predicate, f.object as object, f.confidence as confidence
                LIMIT 5
            """)
            sample_facts = list(result)
            assert len(sample_facts) > 0, "Debe haber facts de ejemplo"
            
            print(f"\n✅ Pipeline ETI completo exitoso:")
            print(f"   - {len(chunks)} chunks creados")
            print(f"   - {fact_count} facts persistidos")
            print(f"   - {facts_with_provenance} facts con trazabilidad (DERIVED_FROM)")
            print(f"\n   Ejemplos de facts:")
            for fact in sample_facts[:3]:
                print(f"     - ({fact['subject']}, {fact['predicate']}, {fact['object']}) [conf: {fact['confidence']:.2f}]")
        
    finally:
        # Limpiar recursos
        if hasattr(use_case.chunk_repository, 'close'):
            use_case.chunk_repository.close()


@pytest.mark.e2e
def test_fact_provenance_chain(markdown_file, clean_neo4j_database, neo4j_driver, neo4j_database):
    """
    Test: Verificar cadena de trazabilidad completa (Fact → Chunk → Page → File).
    
    Verifica que la trazabilidad PROV-O funciona correctamente:
    - Fact DERIVED_FROM Chunk
    - Chunk pertenece a Page
    - Page pertenece a File
    """
    if neo4j_driver is None:
        pytest.skip("Neo4j no disponible")
    
    if not markdown_file.exists():
        pytest.skip(f"Archivo de prueba no encontrado: {markdown_file}")
    
    if not _is_spacy_available():
        pytest.skip("spaCy no disponible")
    
    use_case = create_ingest_document_use_case(enable_inference=True)
    
    try:
        # Ejecutar pipeline ETI
        chunks = use_case.execute(
            file_path=markdown_file,
            chunk_size=500,
            chunk_overlap=100,
            clean_text=True
        )
        
        # Verificar cadena de trazabilidad en Neo4j
        with neo4j_driver.session(database=neo4j_database) as session:
            # Verificar que existe al menos una cadena completa: Fact → Chunk → Page → File
            result = session.run("""
                MATCH (f:Fact)-[:DERIVED_FROM]->(c:Chunk)-[:HAS_CHUNK]-(p:Page)-[:CONTAINS]-(file:File)
                RETURN count(f) as complete_chains
            """)
            complete_chains = result.single()["complete_chains"]
            assert complete_chains > 0, "Debe haber al menos una cadena completa de trazabilidad: Fact → Chunk → Page → File"
            
            # Obtener ejemplo de cadena completa
            result = session.run("""
                MATCH (fact:Fact)-[:DERIVED_FROM]->(chunk:Chunk)-[:HAS_CHUNK]-(page:Page)-[:CONTAINS]-(file:File)
                RETURN fact.subject as fact_subject, 
                       fact.predicate as fact_predicate,
                       fact.object as fact_object,
                       chunk.chunk_id as chunk_id,
                       page.filename as page_filename,
                       file.filename as file_filename
                LIMIT 1
            """)
            chain = result.single()
            if chain:
                print(f"\n✅ Cadena de trazabilidad verificada:")
                print(f"   Fact: ({chain['fact_subject']}, {chain['fact_predicate']}, {chain['fact_object']})")
                print(f"   → Chunk: {chain['chunk_id']}")
                print(f"   → Page: {chain['page_filename']}")
                print(f"   → File: {chain['file_filename']}")
        
    finally:
        if hasattr(use_case.chunk_repository, 'close'):
            use_case.chunk_repository.close()





