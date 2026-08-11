# Patrones de búsqueda (GraphRAG)

Contrato de `ungraph.search_with_pattern` para patrones **básicos**.  
Audiencia: developer. GraphRAG = interfaz/consumidor del almacén — [`../concepts/eti-spine.md`](../concepts/eti-spine.md), [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md). Léxico base: [`../concepts/sp-lexical-graphs.md`](../concepts/sp-lexical-graphs.md).

How-to: [`../guides/search.md`](../guides/search.md). Avanzados (GDS): [`sp-advanced-search-patterns.md`](sp-advanced-search-patterns.md).

## Firma

```python
results = ungraph.search_with_pattern(
    query_text: str,
    pattern_type: str,
    limit: int = 5,
    database: Optional[str] = None,
    embedding_model: Optional[str] = None,
    **kwargs,
) -> List[SearchResult]
```

**Errores:** `ValueError` (query vacío / patrón desconocido / kwargs inválidos), `RuntimeError`, `ImportError` (solo avanzados).

Todos los patrones de esta página asumen índices full-text (`chunk_content`) creados en setup/ingesta. Topología típica: `FILE_PAGE_CHUNK`.

## Patrones básicos (`is`)

### `basic` / `basic_retriever`

Full-text sobre chunks.

```python
results = ungraph.search_with_pattern(
    "inteligencia artificial",
    pattern_type="basic",
    limit=5,
)
```

Cypher (esquema):

```cypher
CALL db.index.fulltext.queryNodes("chunk_content", $query_text)
YIELD node, score
RETURN node.page_content as content, score,
       node.chunk_id as chunk_id,
       node.chunk_id_consecutive as chunk_id_consecutive
ORDER BY score DESC
LIMIT $limit
```

---

### `metadata_filtering`

Full-text + filtros por propiedades del nodo.

**kwargs:** `metadata_filters: Dict[str, Any]` (claves = nombres de propiedad válidos `[A-Za-z_][A-Za-z0-9_]*`).

```python
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={
        "filename": "ai_paper.md",
        "page_number": 1,
    },
    limit=10,
)
```

Cypher (esquema): condiciones `node.<prop> = $<prop>` añadidas tras el `YIELD`.

---

### `parent_child` / `parent_child_retriever`

Busca nodos padre y expande hijos por relación.

**kwargs habituales:** `parent_label` (default típico `"Page"`), `child_label` (`"Chunk"`), `relationship_type` (`"HAS_CHUNK"`).

```python
results = ungraph.search_with_pattern(
    "computación cuántica",
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=5,
)
for r in results:
    # content = padre; next_chunk_content = hijos concatenados
    print(r.score, r.content[:160])
    print((r.next_chunk_content or "")[:200])
```

**Proyección a `SearchResult` (`is`):** `content` ← contenido padre; `score` ← score padre; `chunk_id` ← id padre; `next_chunk_content` ← textos de hijos unidos. No hay atributos `parent_content` / `children` en el tipo público.

## Requisitos de índices

- Full-text: `chunk_content`
- Vector (otros modos / avanzados): `chunk_embeddings`

## Referencias externas

- [GraphRAG Retrieval Patterns](https://graphrag.com/reference/)
- [Neo4j vector indexes](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)

## Referencias internas

- [API pública](sp-public-api.md)
- [Patrones avanzados](sp-advanced-search-patterns.md)
- [Guía de búsqueda](../guides/search.md)
