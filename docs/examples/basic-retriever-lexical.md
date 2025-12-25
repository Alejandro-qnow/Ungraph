# Ejemplo: Basic Retriever con Lexical Graph

Este ejemplo muestra cómo usar el **Basic Retriever** con un **Lexical Graph** en Ungraph.

## Contexto

El Basic Retriever es el patrón más básico de GraphRAG. Requiere un Lexical Graph (como `FILE_PAGE_CHUNK`) y funciona buscando similitud vectorial directamente en los chunks.

## Paso 1: Crear el Lexical Graph

Primero, necesitamos ingerir un documento para crear el Lexical Graph:

```python
import ungraph

# Ingerir documento (crea Lexical Graph automáticamente)
chunks = ungraph.ingest_document(
    "documento_tecnico.md",
    chunk_size=1000,
    chunk_overlap=200
)

print(f"✅ Lexical Graph creado con {len(chunks)} chunks")
```

**Estructura creada**:
```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
                              Chunk -[:NEXT_CHUNK]-> Chunk
```

Cada `Chunk` contiene:
- `page_content`: Texto del chunk
- `embeddings`: Representación vectorial del texto
- `chunk_id`: Identificador único

## Paso 2: Buscar usando Basic Retriever

El Basic Retriever busca directamente en los chunks usando búsqueda vectorial:

```python
# Búsqueda simple (usa Basic Retriever internamente)
results = ungraph.search("machine learning", limit=5)

for i, result in enumerate(results, 1):
    print(f"\n--- Resultado {i} ---")
    print(f"Score: {result.score:.4f}")
    print(f"Chunk ID: {result.chunk_id}")
    print(f"Contenido: {result.content[:300]}...")
```

## Paso 3: Usar Basic Retriever Explícitamente

También puedes usar el patrón explícitamente:

```python
from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

search_service = Neo4jSearchService()

# Usar Basic Retriever explícitamente
results = search_service.search_with_pattern(
    query_text="¿Qué es deep learning?",
    pattern_type="basic",  # o "basic_retriever"
    limit=5
)

for result in results:
    print(f"Score: {result.score:.4f}")
    print(f"Contenido: {result.content[:200]}...")
    print("-" * 80)

search_service.close()
```

## Cómo Funciona Internamente

### 1. Vectorización de la Pregunta

```python
from ungraph.infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService

embedding_service = HuggingFaceEmbeddingService()
query_embedding = embedding_service.generate_embedding("machine learning")
```

### 2. Búsqueda de Similitud

El Basic Retriever ejecuta una búsqueda de similitud coseno en los embeddings de los chunks:

```cypher
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $query_vector)
YIELD node, score
RETURN node.page_content as content,
       score,
       node.chunk_id as chunk_id
ORDER BY score DESC
```

### 3. Retorno de Resultados

Los chunks más similares se retornan con su contenido y score.

## Ejemplo Completo

```python
import ungraph

# 1. Crear Lexical Graph
print("📄 Ingiriendo documento...")
chunks = ungraph.ingest_document(
    "documento_tecnico.md",
    chunk_size=1000,
    chunk_overlap=200
)
print(f"✅ {len(chunks)} chunks creados en el Lexical Graph\n")

# 2. Buscar usando Basic Retriever
query = "inteligencia artificial y sus aplicaciones"
print(f"🔍 Buscando: '{query}'\n")

results = ungraph.search(query, limit=5)

# 3. Mostrar resultados
print(f"📊 Encontrados {len(results)} resultados:\n")
for i, result in enumerate(results, 1):
    print(f"{'='*80}")
    print(f"Resultado {i}")
    print(f"{'='*80}")
    print(f"Score de similitud: {result.score:.4f}")
    print(f"Chunk ID: {result.chunk_id}")
    print(f"\nContenido:")
    print(f"{result.content[:500]}...")
    print()
```

## Cuándo Usar Basic Retriever

### ✅ Usa Basic Retriever cuando:

- La información está en chunks específicos y bien definidos
- No necesitas contexto adicional más allá del chunk encontrado
- La similitud entre pregunta y contenido es alta
- Quieres la búsqueda más rápida y simple

### ❌ No uses Basic Retriever cuando:

- Necesitas contexto completo de una sección → Usa **Parent-Child Retriever**
- La información está distribuida en muchos chunks relacionados → Considera **Community Summary**
- Necesitas filtrar por metadatos → Usa **Metadata Filtering**

## Visualización del Grafo

Puedes visualizar el Lexical Graph creado:

```cypher
// Ver estructura completa
MATCH path = (f:File)-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN path
LIMIT 20

// Ver chunks encontrados en una búsqueda
MATCH (c:Chunk)
WHERE c.chunk_id IN ['chunk_1', 'chunk_2', 'chunk_3']
RETURN c
```

## Comparación con Otros Patrones

| Aspecto | Basic Retriever | Parent-Child | Metadata Filtering |
|---------|----------------|--------------|-------------------|
| **Velocidad** | ⚡⚡⚡ Muy rápida | ⚡⚡ Rápida | ⚡⚡⚡ Muy rápida |
| **Contexto** | ⭐ Solo chunk | ⭐⭐⭐ Contexto completo | ⭐ Solo chunk |
| **Precisión** | ⭐⭐ Buena | ⭐⭐⭐ Muy buena | ⭐⭐⭐ Excelente (con filtros) |
| **Uso** | Búsquedas simples | Necesitas contexto | Filtrar por metadatos |

## Referencias

- [Lexical Graphs](../concepts/lexical-graphs.md)
- [Patrones de Búsqueda GraphRAG](../api/search-patterns.md)
- [GraphRAG Basic Retriever](https://graphrag.com/reference/graphrag/basic-retriever/)



