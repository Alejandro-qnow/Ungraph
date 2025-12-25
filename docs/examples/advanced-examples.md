# Ejemplos Avanzados

Ejemplos avanzados de uso de Ungraph.

## Ejemplo 1: Ingerir Múltiples Documentos

```python
import ungraph
from pathlib import Path

# Lista de archivos
archivos = ["doc1.md", "doc2.txt", "doc3.docx"]

# Ingerir todos
for archivo in archivos:
    try:
        chunks = ungraph.ingest_document(archivo)
        print(f"✅ {archivo}: {len(chunks)} chunks")
    except Exception as e:
        print(f"❌ Error con {archivo}: {e}")
```

## Ejemplo 2: Reconstruir Contexto Completo

```python
import ungraph

# Buscar
results = ungraph.hybrid_search("tema", limit=3)

# Reconstruir contexto completo para cada resultado
for result in results:
    contexto_completo = ""
    
    if result.previous_chunk_content:
        contexto_completo += f"[Anterior]\n{result.previous_chunk_content}\n\n"
    
    contexto_completo += f"[Principal]\n{result.content}\n\n"
    
    if result.next_chunk_content:
        contexto_completo += f"[Siguiente]\n{result.next_chunk_content}"
    
    print(contexto_completo)
    print("=" * 80)
```

## Ejemplo 3: Crear Patrón Personalizado

```python
from domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition
)
from infrastructure.services.neo4j_pattern_service import Neo4jPatternService

# Crear patrón simple
chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={"chunk_id": str, "content": str},
    indexes=["chunk_id"]
)

simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Solo chunks",
    node_definitions=[chunk_node],
    relationship_definitions=[]
)

# Validar
service = Neo4jPatternService()
is_valid = service.validate_pattern(simple_pattern)
print(f"Patrón válido: {is_valid}")

# Generar query Cypher
cypher = service.generate_cypher(simple_pattern, "create")
print(f"Query generado:\n{cypher}")
```

## Ejemplo 4: Análisis de Resultados

```python
import ungraph
from collections import Counter

# Buscar
results = ungraph.hybrid_search("machine learning", limit=20)

# Analizar resultados
print(f"Total de resultados: {len(results)}")
print(f"Score promedio: {sum(r.score for r in results) / len(results):.3f}")
print(f"Score máximo: {max(r.score for r in results):.3f}")
print(f"Score mínimo: {min(r.score for r in results):.3f}")

# Contar chunks con contexto
con_contexto = sum(1 for r in results if r.previous_chunk_content or r.next_chunk_content)
print(f"Resultados con contexto: {con_contexto}/{len(results)}")
```

## Ejemplo 5: Comparar Estrategias de Búsqueda

```python
import ungraph

query = "deep learning"

# Búsqueda por texto
text_results = ungraph.search(query, limit=5)

# Búsqueda híbrida con diferentes pesos
hybrid_1 = ungraph.hybrid_search(query, limit=5, weights=(0.7, 0.3))  # Más texto
hybrid_2 = ungraph.hybrid_search(query, limit=5, weights=(0.3, 0.7))  # Más vectorial

print("Búsqueda por texto:")
for r in text_results[:3]:
    print(f"  Score: {r.score:.3f}")

print("\nHíbrida (más texto):")
for r in hybrid_1[:3]:
    print(f"  Score: {r.score:.3f}")

print("\nHíbrida (más vectorial):")
for r in hybrid_2[:3]:
    print(f"  Score: {r.score:.3f}")
```

## Referencias

- [Guía de Patrones Personalizados](../guides/custom-patterns.md)
- [Patrones de Búsqueda GraphRAG](../api/search-patterns.md)




