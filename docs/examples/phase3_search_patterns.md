# Ejemplos de Uso: Patrones de Búsqueda GraphRAG (Fase 3)

Ejemplos prácticos de cómo usar los patrones de búsqueda GraphRAG implementados.

## Patrón: Metadata Filtering

Búsqueda con filtros por metadatos. Útil para buscar solo en documentos específicos.

```python
import ungraph

# Buscar solo en un archivo específico
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md"
    },
    limit=10
)

# Buscar en una página específica
results = ungraph.search_with_pattern(
    "deep learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md",
        "page_number": 1
    },
    limit=5
)

# Procesar resultados
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
    print("---")
```

## Patrón: Parent-Child Retriever

Busca en nodos padre y expande a todos sus hijos. Útil para obtener contexto completo.

```python
import ungraph

# Buscar en Pages y obtener todos sus Chunks
results = ungraph.search_with_pattern(
    "inteligencia artificial",
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=5
)

# Los resultados incluyen el contenido del padre y sus hijos
for result in results:
    print(f"Page Score: {result.score:.3f}")
    print(f"Page Content: {result.content[:200]}...")
    # Nota: Los children se pueden acceder desde el resultado si se extiende SearchResult
    print("---")
```

## Comparación: Búsqueda Normal vs Con Patrones

```python
import ungraph

query = "computación cuántica"

# Búsqueda normal (sin filtros)
results_normal = ungraph.search(query, limit=5)
print(f"Búsqueda normal: {len(results_normal)} resultados")

# Búsqueda con filtro de metadatos
results_filtered = ungraph.search_with_pattern(
    query,
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "quantum_computing.md"},
    limit=5
)
print(f"Búsqueda filtrada: {len(results_filtered)} resultados")
```

## Uso Avanzado: Combinar con Otras Funcionalidades

```python
import ungraph

# 1. Ingerir documento con patrón personalizado
from ungraph.domain.value_objects.graph_pattern import GraphPattern, NodeDefinition

simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Solo chunks",
    node_definitions=[
        NodeDefinition(
            label="Chunk",
            required_properties={"chunk_id": str, "content": str}
        )
    ],
    relationship_definitions=[]
)

chunks = ungraph.ingest_document("doc.md", pattern=simple_pattern)

# 2. Buscar usando patrones GraphRAG
results = ungraph.search_with_pattern(
    "tema de interés",
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "doc.md"},
    limit=10
)
```

## Patrón: Basic Retriever

Búsqueda full-text simple. El patrón más básico y rápido.

```python
import ungraph

# Búsqueda básica usando el patrón basic_retriever
results = ungraph.search_with_pattern(
    "inteligencia artificial",
    pattern_type="basic",
    limit=5
)

# Equivalente a ungraph.search() pero usando el patrón
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
    print("---")
```

## Referencias

- [Documentación de Patrones de Búsqueda GraphRAG](../api/search-patterns.md)
- [Guía de Búsqueda](../guides/search.md)
- [Plan de Patrones de Grafo](../../_PLAN_PATRONES_GRAFO.md)


