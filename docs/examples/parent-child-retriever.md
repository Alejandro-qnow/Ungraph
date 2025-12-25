# Ejemplo: Parent-Child Retriever

Este ejemplo muestra cómo usar el **Parent-Child Retriever**, una evolución del Lexical Graph básico que mejora la calidad de los resultados cuando necesitas contexto completo.

## Contexto

El **Parent-Child Retriever** resuelve un problema común: los chunks pequeños tienen mejor representación vectorial (menos ruido), pero pueden faltar contexto para generar respuestas completas.

**Solución**: Buscar en chunks pequeños (hijos) y recuperar el chunk padre (contexto completo).

## Concepto: Estructura Padre-Hijo

En un Lexical Graph con estructura padre-hijo:

```
Page (padre) -[:HAS_CHILD]-> Chunk (hijo)
Chunk (hijo) -[:PART_OF]-> Page (padre)
```

- **Chunks pequeños (hijos)**: Mejor matching vectorial, menos ruido
- **Chunks grandes (padres)**: Contexto completo para generación

## Paso 1: Preparar Estructura Padre-Hijo

Primero, necesitamos un grafo con estructura jerárquica. En Ungraph, puedes usar el patrón `FILE_PAGE_CHUNK` donde:
- **Page** actúa como padre
- **Chunk** actúa como hijo

```python
import ungraph

# Ingerir documento (crea estructura File -> Page -> Chunk)
chunks = ungraph.ingest_document(
    "documento_largo.md",
    chunk_size=500,  # Chunks pequeños para mejor matching
    chunk_overlap=100
)

print(f"✅ Estructura padre-hijo creada con {len(chunks)} chunks")
```

## Paso 2: Usar Parent-Child Retriever

```python
from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

search_service = Neo4jSearchService()

# Buscar usando Parent-Child Retriever
results = search_service.search_with_pattern(
    query_text="explicación detallada de machine learning",
    pattern_type="parent_child",  # o "parent_child_retriever"
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=3
)

# Los resultados incluyen el padre y sus hijos
for result in results:
    print(f"\n{'='*80}")
    print(f"Page (Padre):")
    print(f"{result.parent_content[:300]}...")
    print(f"\nScore: {result.parent_score:.4f}")
    print(f"\nChunks relacionados (Hijos): {len(result.children)}")
    for i, child in enumerate(result.children[:3], 1):
        print(f"\n  Hijo {i}:")
        print(f"  {child['content'][:200]}...")
    print(f"{'='*80}\n")

search_service.close()
```

## Cómo Funciona Internamente

### 1. Búsqueda en Chunks Pequeños

Primero busca en los chunks (hijos) usando búsqueda vectorial:

```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as child_node, score as child_score
```

### 2. Recuperar Chunk Padre

Luego recupera el chunk padre relacionado:

```cypher
MATCH (child_node:Chunk)<-[:HAS_CHUNK]-(parent_node:Page)
RETURN {
    parent_content: parent_node.page_content,
    parent_score: child_score,
    children: collect(DISTINCT {
        content: child_node.page_content,
        chunk_id: child_node.chunk_id
    })
} as result
```

### 3. Retorno de Resultados

Retorna el padre con todos sus hijos relacionados.

## Ejemplo Completo

```python
import ungraph
from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

# 1. Crear estructura padre-hijo
print("📄 Ingiriendo documento largo...")
chunks = ungraph.ingest_document(
    "documento_tecnico.md",
    chunk_size=500,  # Chunks pequeños
    chunk_overlap=100
)
print(f"✅ {len(chunks)} chunks creados\n")

# 2. Buscar usando Parent-Child Retriever
query = "arquitectura de redes neuronales profundas"
print(f"🔍 Buscando: '{query}'\n")

search_service = Neo4jSearchService()
results = search_service.search_with_pattern(
    query_text=query,
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=3
)

# 3. Mostrar resultados con contexto completo
print(f"📊 Encontrados {len(results)} resultados:\n")
for i, result in enumerate(results, 1):
    print(f"{'='*80}")
    print(f"Resultado {i}")
    print(f"{'='*80}")
    print(f"📄 Page (Padre) - Score: {result.parent_score:.4f}")
    print(f"\n{result.parent_content[:400]}...")
    print(f"\n📦 Chunks relacionados: {len(result.children)}")
    
    # Mostrar primeros 3 hijos
    for j, child in enumerate(result.children[:3], 1):
        print(f"\n  Chunk {j}:")
        print(f"  {child['content'][:250]}...")
    
    print(f"\n{'='*80}\n")

search_service.close()
```

## Cuándo Usar Parent-Child Retriever

### ✅ Usa Parent-Child Retriever cuando:

- Muchos temas en un chunk afectan negativamente la calidad de los vectores
- Necesitas contexto completo de una sección para generar respuestas
- Los chunks pequeños tienen mejor representación vectorial pero falta contexto
- Quieres explorar jerarquías de conocimiento

### ❌ No uses Parent-Child Retriever cuando:

- Un chunk pequeño contiene suficiente información → Usa **Basic Retriever**
- No tienes estructura jerárquica padre-hijo en tu grafo
- La búsqueda es muy simple y no necesitas contexto adicional

## Comparación: Basic vs Parent-Child

### Basic Retriever
```python
# Retorna solo el chunk encontrado
results = ungraph.search("machine learning", limit=5)
# Resultado: Chunk con score
```

**Ventajas**:
- ⚡ Muy rápido
- 🎯 Simple de usar
- ✅ Suficiente cuando el chunk tiene toda la información

**Desventajas**:
- ❌ Puede faltar contexto
- ❌ No considera relaciones jerárquicas

### Parent-Child Retriever
```python
# Retorna el padre y todos sus hijos
results = search_service.search_with_pattern(
    "machine learning",
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk"
)
# Resultado: Page (padre) + Chunks (hijos) relacionados
```

**Ventajas**:
- ✅ Contexto completo
- ✅ Mejor para generar respuestas
- ✅ Considera estructura jerárquica

**Desventajas**:
- ⚠️ Más lento que Basic
- ⚠️ Requiere estructura padre-hijo

## Visualización del Grafo

Puedes visualizar la estructura padre-hijo:

```cypher
// Ver estructura padre-hijo completa
MATCH path = (p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN path
LIMIT 20

// Ver un Page específico con todos sus Chunks
MATCH (p:Page)-[:HAS_CHUNK]->(c:Chunk)
WHERE p.page_number = 1
RETURN p, collect(c) as chunks
```

## Mejores Prácticas

1. **Chunk size pequeño**: Usa chunks pequeños (300-500 tokens) para mejor matching vectorial
2. **Chunk overlap**: Usa overlap (100-200 tokens) para mantener continuidad
3. **Estructura clara**: Asegúrate de tener relaciones `HAS_CHUNK` entre Page y Chunk
4. **Límite razonable**: Usa `limit=3-5` para no sobrecargar el contexto

## Referencias

- [Lexical Graphs](../concepts/lexical-graphs.md)
- [Patrones de Búsqueda GraphRAG](../api/search-patterns.md)
- [GraphRAG Parent-Child Retriever](https://graphrag.com/reference/graphrag/parent-child-retriever/)



