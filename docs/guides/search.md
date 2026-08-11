# Búsqueda en el grafo

**Canónico ES (excepción de prefijo):** how-to único de búsqueda en el sitio; no existe `sp-search.md`. Stubs de tutoriales / `en-*` apuntan aquí.

Audiencia: developer. Retrieval = **interfaz** sobre el almacén (no definición de conocimiento). Espina: [`../concepts/eti-spine.md`](../concepts/eti-spine.md). Contrato: [`../api/sp-public-api.md`](../api/sp-public-api.md), patrones [`../api/sp-search-patterns.md`](../api/sp-search-patterns.md).

## Prerrequisitos

1. Documento(s) ya ingeridos ([`sp-ingestion.md`](sp-ingestion.md)).
2. Índices full-text / vector creados por la ingesta (o `ungraph setup --database-init` vía CLI).
3. Neo4j configurado.

**Resultado observable:** `List[SearchResult]` con `content`, `score`, `chunk_id` (y contexto adyacente cuando el query lo aporta).

## Modos de la API pública (`is`)

| Función | Señal | Uso típico |
|---------|-------|------------|
| `ungraph.search` | full-text Neo4j | palabras clave |
| `ungraph.vector_search` | similitud de embeddings | semántica |
| `ungraph.hybrid_search` | texto + vector con pesos | combinación |
| `ungraph.search_with_pattern` | patrón GraphRAG nombrado | topología / filtros |

GraphRAG aquí es **consumidor** del grafo léxico/KG; no sustituye Inference ni depuración de creencias ([`../theory/sp-graphrag.md`](../theory/sp-graphrag.md)).

## Búsqueda por texto

```python
import ungraph

results = ungraph.search("computación cuántica", limit=5)
for r in results:
    print(r.score, r.chunk_id, r.content[:200])
```

**Errores:** `ValueError` si `query_text` vacío; `RuntimeError` si Neo4j falla.

## Búsqueda vectorial

```python
import ungraph

results = ungraph.vector_search("inteligencia artificial", limit=5)
for r in results:
    print(r.score, r.content[:200])
```

Usa el `embedding_model` de configuración (o el argumento opcional de la firma).

## Búsqueda híbrida

```python
import ungraph

results = ungraph.hybrid_search(
    "deep learning",
    limit=10,
    weights=(0.3, 0.7),  # (texto, vector)
)
for r in results:
    print(r.score, r.content[:200])
    if r.previous_chunk_content:
        print("prev:", r.previous_chunk_content[:100])
    if r.next_chunk_content:
        print("next:", r.next_chunk_content[:100])
```

Ajuste de pesos:

```python
# más peso a texto (términos exactos)
ungraph.hybrid_search("palabra clave", weights=(0.7, 0.3))

# más peso a vector (conceptos)
ungraph.hybrid_search("concepto abstracto", weights=(0.2, 0.8))
```

Default documentado en API: `(0.3, 0.7)`.

## Contexto adyacente

Cuando el resultado trae vecinos léxicos:

```python
results = ungraph.hybrid_search("tema de interés", limit=3)
for r in results:
    parts = []
    if r.previous_chunk_content:
        parts.append(f"[Anterior]\n{r.previous_chunk_content}")
    parts.append(f"[Principal]\n{r.content}")
    if r.next_chunk_content:
        parts.append(f"[Siguiente]\n{r.next_chunk_content}")
    print("\n\n".join(parts))
```

## Patrones GraphRAG (`search_with_pattern`)

```python
import ungraph

# básico (full-text tipado como patrón)
results = ungraph.search_with_pattern(
    "inteligencia artificial",
    pattern_type="basic",
    limit=5,
)

# filtros de metadatos
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "ai_paper.md"},
    limit=10,
)

# parent–child (Page → Chunk); hijos van en next_chunk_content
results = ungraph.search_with_pattern(
    "computación cuántica",
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=5,
)
for r in results:
    print(r.score, r.content[:160])
    print("hijos/contexto:", (r.next_chunk_content or "")[:200])
```

Patrones avanzados (`graph_enhanced`, `local`, `community_summary`) requieren extras (`ungraph[gds]`, plugin GDS, entidades/`MENTIONS` según patrón). Contrato y kwargs: [`../api/sp-search-patterns.md`](../api/sp-search-patterns.md), [`../api/sp-advanced-search-patterns.md`](../api/sp-advanced-search-patterns.md).

| | |
|--|--|
| **is** | Firmas anteriores en `main`; resultados normalizados a `SearchResult` |
| **will be** | Ranking/scorecards confrontables (PRODUCT §5); más patrones de interface — [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) |

No afirmar “mejor precisión” sin ExperimentRun en `validation/`.

## Práctica operativa

1. Verificar ingesta antes de buscar.
2. Empezar por `search` o `hybrid_search`; subir a `search_with_pattern` si hace falta topología/filtros.
3. `limit` pequeño (5–10) para inspección humana.
4. Tratar scores como ranking relativo del modo, no como confianza epistémica.

## Referencias

- [Inicio rápido](sp-quickstart.md) · [Ingesta](sp-ingestion.md)
- [API pública](../api/sp-public-api.md)
- [Patrones de búsqueda](../api/sp-search-patterns.md) · [Avanzados](../api/sp-advanced-search-patterns.md)
- [Grafos léxicos](../concepts/sp-lexical-graphs.md)
