# Patrones avanzados de búsqueda

Contrato de `search_with_pattern` para patrones que requieren extras.  
Audiencia: developer. Básicos: [`sp-search-patterns.md`](sp-search-patterns.md). Interface GraphRAG: [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md).

## Instalación

```bash
pip install ungraph[gds]   # patrones GDS / graph-enhanced / local / community
# opcional viz (fuera de este contrato de búsqueda):
pip install ungraph[ynet]
```

También hace falta el plugin **Neo4j GDS** en el servidor para algoritmos de comunidad. Sin el extra Python, `pattern_type` avanzado puede fallar con `ImportError` / patrón desconocido.

## Firma (igual que básicos)

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

Resultados siempre como `SearchResult`. Contexto ampliado → `next_chunk_content` cuando aplica.

## Patrones (`is` con prerequisitos)

### `graph_enhanced` / `graph_enhanced_vector`

**Requisitos:** `ungraph[gds]`; embeddings; entidades con `(:Chunk)-[:MENTIONS]->(:Entity)` cuando el grafo las tenga (p. ej. tras Inference).

**kwargs:** `max_traversal_depth` (int); `query_vector` opcional (si no, se genera embedding de `query_text`).

```python
import ungraph

results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="graph_enhanced",
    limit=5,
    max_traversal_depth=2,
)
for r in results:
    print(r.score, r.content[:200])
    print("contexto:", (r.next_chunk_content or "")[:200])
```

Flujo (esquema): vector search → entidades `MENTIONS` → chunks relacionados → proyección a `SearchResult`.

---

### `local` / `local_retriever`

**Requisitos:** `ungraph[gds]` (mejor con GDS; el código del patrón vive en el extra avanzado).

**kwargs:** `community_threshold` (tamaño mínimo), `max_depth`.

```python
results = ungraph.search_with_pattern(
    "neural networks",
    pattern_type="local",
    limit=5,
    community_threshold=3,
    max_depth=1,
)
for r in results:
    print(r.score, r.content[:200])
    print("comunidad:", (r.next_chunk_content or "")[:200])
```

---

### `community_summary` / `community_summary_gds`

**Requisitos:** `ungraph[gds]` + plugin GDS; comunidades detectadas en el grafo (propiedad tip. `community_id`).

**kwargs:** `min_community_size` (default tip. 5).

Pre-paso (probe de servicio GDS):

```python
from ungraph.infrastructure.services.gds_service import GDSService

gds = GDSService()
stats = gds.detect_communities(
    graph_name="chunk-graph",
    algorithm="louvain",
    write_property="community_id",
)
print(stats)
```

Búsqueda:

```python
import ungraph

results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="community_summary",
    limit=3,
    min_community_size=5,
)
for r in results:
    print(r.score, r.content[:200])
    print("resumen:", (r.next_chunk_content or "")[:200])
```

## Índices y datos

| Necesidad | Artefacto |
|-----------|-----------|
| Básicos + local | full-text `chunk_content` |
| `graph_enhanced` | vector `chunk_embeddings` + `Entity`/`MENTIONS` |
| `community_summary` | `community_id` (u otra propiedad escrita por GDS) |

## Cuándo elegir qué (operativo, no scorecard)

| Patrón | Prerequisito extra | Nota de uso |
|--------|--------------------|-------------|
| `basic` / `metadata_filtering` | ninguno | primer recurso |
| `parent_child` | topología padre–hijo | contexto jerárquico léxico |
| `graph_enhanced` | `[gds]` + entidades | expansion por `MENTIONS` |
| `local` | `[gds]` | vecindario acotado |
| `community_summary` | `[gds]` + GDS + comunidades | temas agrupados |

No hay métricas de “precisión” en este contrato; evaluación medible → [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) / `validation/` bajo PRODUCT §5.

## Referencias

- [Patrones básicos](sp-search-patterns.md)
- [API pública](sp-public-api.md)
- [Guía de búsqueda](../guides/search.md)
