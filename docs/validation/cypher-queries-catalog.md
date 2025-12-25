# Catálogo de Queries Cypher - Ungraph

Este documento cataloga todos los queries Cypher utilizados en Ungraph, organizados por categoría y funcionalidad.

## Categorías

1. [Queries de Ingesta](#queries-de-ingesta)
2. [Queries de Búsqueda GraphRAG](#queries-de-búsqueda-graphrag)
3. [Queries de Configuración](#queries-de-configuración)
4. [Queries de Validación](#queries-de-validación)

---

## Queries de Ingesta

### 1. FILE_PAGE_CHUNK Pattern

**Ubicación**: `src/utils/graph_operations.py::extract_document_structure`

**Query**:
```cypher
MERGE (f:File {filename: $filename})
ON CREATE SET f.createdAt = timestamp()

MERGE (p:Page {filename: $filename, page_number: toInteger($page_number)})

MERGE (c:Chunk {chunk_id: $chunk_id})
ON CREATE SET c.page_content = $page_content,
              c.is_unitary = $is_unitary,
              c.embeddings = $embeddings,
              c.embeddings_dimensions = toInteger($embeddings_dimensions),
              c.embedding_encoder_info = $embedding_encoder_info,
              c.chunk_id_consecutive = toInteger($chunk_id_consecutive)

MERGE (f)-[:CONTAINS]->(p)
MERGE (p)-[:HAS_CHUNK]->(c)
```

**Parámetros**:
- `filename`: str - Nombre del archivo
- `page_number`: int - Número de página
- `chunk_id`: str - ID único del chunk
- `page_content`: str - Contenido del chunk
- `is_unitary`: bool - Si el chunk es unitario
- `embeddings`: list - Vector de embeddings
- `embeddings_dimensions`: int - Dimensiones del vector
- `embedding_encoder_info`: str - Información del encoder
- `chunk_id_consecutive`: int - ID consecutivo del chunk

**Validaciones**:
- ✅ Crea File, Page, Chunk correctamente
- ✅ Establece relaciones CONTAINS y HAS_CHUNK
- ✅ Maneja propiedades opcionales con ON CREATE SET
- ✅ Timestamp automático para createdAt

---

### 2. SEQUENTIAL_CHUNKS Pattern

**Ubicación**: `src/utils/graph_operations.py::create_chunk_relationships`

**Query**:
```cypher
MATCH (c1:Chunk), (c2:Chunk)
WHERE c1.chunk_id_consecutive + 1 = c2.chunk_id_consecutive
MERGE (c1)-[:NEXT_CHUNK]->(c2)
```

**Parámetros**: Ninguno (usa datos existentes)

**Validaciones**:
- ✅ Crea relaciones NEXT_CHUNK solo entre chunks consecutivos
- ✅ Basado en chunk_id_consecutive
- ✅ No crea relaciones duplicadas (MERGE)

---

## Queries de Búsqueda GraphRAG

### 1. Basic Retriever

**Ubicación**: `src/infrastructure/services/graphrag_search_patterns.py::basic_retriever`

**Query**:
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
RETURN node.page_content as content,
       score,
       node.chunk_id as chunk_id,
       node.chunk_id_consecutive as chunk_id_consecutive
ORDER BY score DESC
LIMIT $limit
```

**Parámetros**:
- `query_text`: str - Texto a buscar
- `limit`: int - Número máximo de resultados

**Validaciones**:
- ✅ Usa índice full-text chunk_content
- ✅ Retorna score de relevancia
- ✅ Ordena por score descendente
- ✅ Respeta límite de resultados

**GraphRAG Compliance**: ✅ Compatible con Basic Retriever pattern

---

### 2. Metadata Filtering

**Ubicación**: `src/infrastructure/services/graphrag_search_patterns.py::metadata_filtering`

**Query**:
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
WHERE node.filename = $filename AND node.page_number = $page_number
RETURN node.page_content as content,
       score,
       node.chunk_id as chunk_id,
       node.chunk_id_consecutive as chunk_id_consecutive
ORDER BY score DESC
LIMIT $limit
```

**Parámetros**:
- `query_text`: str - Texto a buscar
- `filename`: str - Filename para filtrar
- `page_number`: int - Page number para filtrar
- `limit`: int - Número máximo de resultados

**Validaciones**:
- ✅ Filtros aplicados correctamente (WHERE)
- ✅ Múltiples filtros combinados (AND)
- ✅ Validación de nombres de propiedades

**GraphRAG Compliance**: ✅ Compatible con Metadata Filtering pattern

---

### 3. Parent-Child Retriever

**Ubicación**: `src/infrastructure/services/graphrag_search_patterns.py::parent_child_retriever`

**Query**:
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as parent_node, score as parent_score

OPTIONAL MATCH (parent_node:Page)-[:HAS_CHUNK]->(child_node:Chunk)

WITH parent_node, parent_score, collect(DISTINCT {
    content: child_node.page_content,
    chunk_id: child_node.chunk_id
}) as children

RETURN {
    parent_content: parent_node.page_content,
    parent_score: parent_score,
    parent_chunk_id: parent_node.chunk_id,
    children: children
} as result,
parent_score
ORDER BY parent_score DESC
LIMIT $limit
```

**Parámetros**:
- `query_text`: str - Texto a buscar
- `limit`: int - Número máximo de resultados

**Validaciones**:
- ✅ OPTIONAL MATCH para expansión a hijos
- ✅ Collect de hijos correcto
- ✅ Estructura de resultado con parent y children

**GraphRAG Compliance**: ✅ Compatible con Parent-Child Retriever pattern

---

### 4. Hybrid Search

**Ubicación**: `src/utils/graph_rags.py::hybrid_search`

**Query**:
```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node as text_node, score as text_score

CALL {
    WITH text_node
    CALL db.index.vector.queryNodes('chunk_embeddings', toInteger($top_k), $query_vector)
    YIELD node as vec_node, score as vec_score
    WHERE text_node = vec_node
    RETURN vec_node, vec_score
}

WITH text_node as node, text_score, vec_score,
     (text_score * $text_weight + vec_score * $vector_weight) as combined_score

OPTIONAL MATCH (node)<-[:NEXT_CHUNK]-(prev)
OPTIONAL MATCH (node)-[:NEXT_CHUNK]->(next)

RETURN {
    score: combined_score,
    central_node_content: node.page_content,
    central_node_chunk_id: node.chunk_id,
    central_node_chunk_id_consecutive: node.chunk_id_consecutive,
    surrounding_context: {
        previous_chunk_node_content: prev.page_content,
        previous_chunk_id: prev.chunk_id_consecutive,
        next_chunk_node_content: next.page_content,
        next_chunk_id: next.chunk_id_consecutive
    }
} as result
ORDER BY combined_score DESC
LIMIT $top_k
```

**Parámetros**:
- `query_text`: str - Texto a buscar
- `query_vector`: list - Vector de embeddings de la query
- `top_k`: int - Número de resultados
- `text_weight`: float - Peso para score de texto
- `vector_weight`: float - Peso para score vectorial

**Validaciones**:
- ✅ Combina búsqueda full-text y vectorial
- ✅ Calcula score combinado con pesos
- ✅ Recupera contexto NEXT_CHUNK

**GraphRAG Compliance**: ✅ Compatible con Hybrid Search pattern

---

## Queries de Configuración

### 1. Setup Vector Index

**Ubicación**: `src/utils/graph_operations.py::setup_advanced_indexes`

**Query**:
```cypher
CALL db.index.vector.createNodeIndex(
    'chunk_embeddings',
    'Chunk',
    'embeddings',
    384,
    'cosine'
)
```

**Validaciones**:
- ✅ Crea índice vectorial para embeddings
- ✅ Dimensiones: 384
- ✅ Similaridad: cosine

---

### 2. Setup Full-Text Index

**Ubicación**: `src/utils/graph_operations.py::setup_advanced_indexes`

**Query**:
```cypher
CREATE FULLTEXT INDEX chunk_content IF NOT EXISTS
FOR (c:Chunk)
ON EACH [c.page_content]
OPTIONS {
    indexConfig: {
        `fulltext.analyzer`: 'spanish',
        `fulltext.eventually_consistent`: false
    }
}
```

**Validaciones**:
- ✅ Crea índice full-text para page_content
- ✅ Analyzer: spanish
- ✅ Eventually consistent: false

---

### 3. Setup Regular Index

**Ubicación**: `src/utils/graph_operations.py::setup_advanced_indexes`

**Query**:
```cypher
CREATE INDEX chunk_consecutive_idx IF NOT EXISTS
FOR (c:Chunk)
ON (c.chunk_id_consecutive)
```

**Validaciones**:
- ✅ Crea índice para chunk_id_consecutive
- ✅ Mejora performance de queries secuenciales

---

## Queries de Validación

### 1. Validate Indexes

**Query**:
```cypher
CALL db.indexes() YIELD name, type, state, populationPercent
WHERE name IN ['chunk_embeddings', 'chunk_content', 'chunk_consecutive_idx']
RETURN name, type, state, populationPercent
ORDER BY name
```

**Propósito**: Verificar que todos los índices existen y están poblados

---

### 2. Count Pattern Nodes

**Query**:
```cypher
MATCH (f:File)
WITH count(f) as files
MATCH (p:Page)
WITH files, count(p) as pages
MATCH (c:Chunk)
WITH files, pages, count(c) as chunks
MATCH (e:Entity)
RETURN files, pages, chunks, count(e) as entities
```

**Propósito**: Contar nodos por tipo en el grafo

---

## Resumen de Cobertura

| Categoría | Queries | Validados | GraphRAG Compliant |
|-----------|---------|-----------|-------------------|
| Ingesta | 2 | ✅ | ✅ |
| Búsqueda | 4 | ✅ | ✅ |
| Configuración | 3 | ✅ | N/A |
| Validación | 2 | ✅ | N/A |
| **Total** | **11** | **✅** | **✅** |

## Referencias

- [Plan de Validación](./cypher-validation-plan.md)
- [Queries de Prueba](../../src/scripts/cypher_test_queries.py)
- [Script de Validación](../../src/scripts/validate_cypher_queries.py)
- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)

