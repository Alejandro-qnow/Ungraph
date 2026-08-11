# Ejemplos básicos

Mínimos reproductibles sobre la API pública (`import ungraph`).  
Audiencia: developer. How-to narrado: [`../guides/sp-quickstart.md`](../guides/sp-quickstart.md). Contrato: [`../api/sp-public-api.md`](../api/sp-public-api.md). Espina: [`../concepts/eti-spine.md`](../concepts/eti-spine.md).

Estos snippets demuestran **ingesta léxica + búsqueda como interfaz**. No son scorecard ni validación PRODUCT [§5](../product/PRODUCT.md).

## Prerrequisitos

1. Python 3.10+, paquete instalado (`pip install ungraph` o entorno del repo).
2. Neo4j accesible; `.env` o `ungraph.configure` ([`../api/sp-configuration.md`](../api/sp-configuration.md)).
3. Índices creados (ingesta o `ungraph setup --database-init` vía CLI).

**Resultado observable global:** `import ungraph` ok; tras cada ejemplo, `len(...) > 0` o impresión de `score` / `chunk_id` / `content`.

## Fixture / datos de ejemplo

Usar un fixture versionado del repo (preferido):

| Archivo | Rol |
|---------|-----|
| [`../../tests/fixtures/topology_alpha.md`](../../tests/fixtures/topology_alpha.md) | Texto corto con término **topology** para asserts full-text |
| [`../../tests/fixtures/topology_beta.md`](../../tests/fixtures/topology_beta.md) | Segundo documento mínimo |

Desde la raíz del repo:

```python
FIXTURE = "tests/fixtures/topology_alpha.md"
```

Si no tienes el árbol de tests, genera un `.md` local UTF-8 con ≥2 párrafos y un término único que luego busques.

## 1. Configurar e ingerir

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="tu_contraseña",
)

FIXTURE = "tests/fixtures/topology_alpha.md"
chunks = ungraph.ingest_document(
    FIXTURE,
    chunk_size=400,
    chunk_overlap=80,
)
print(len(chunks), chunks[0].id, chunks[0].page_content[:120])
```

**Resultado observable:** `len(chunks) > 0`; cada `Chunk` tiene `id` y `page_content`.

**is:** Extract → Transform léxico (`FILE_PAGE_CHUNK` por defecto) + embeddings según settings. El slot Inference depende de `UNGRAPH_INFERENCE_MODE` — [`../concepts/inference-slot.md`](../concepts/inference-slot.md).

## 2. Búsqueda por texto

```python
results = ungraph.search("topology", limit=5)
for r in results:
    print(r.score, r.chunk_id, r.content[:160])
```

**Resultado observable:** lista de `SearchResult` con `score`, `chunk_id`, `content` (tras ingerir el fixture que contiene “topology”).

## 3. Búsqueda híbrida

```python
results = ungraph.hybrid_search(
    "topology",
    limit=5,
    weights=(0.3, 0.7),  # (texto, vector)
)
for r in results:
    print(r.score, r.content[:160])
    if r.previous_chunk_content:
        print("prev:", r.previous_chunk_content[:80])
    if r.next_chunk_content:
        print("next:", r.next_chunk_content[:80])
```

**Resultado observable:** mismos campos; vecinos opcionales en `previous_chunk_content` / `next_chunk_content`.

Vectorial sola: `ungraph.vector_search("topology", limit=5)` — firma en API.

## 4. Chunking sugerido (opcional)

```python
rec = ungraph.suggest_chunking_strategy(FIXTURE)
print(rec.strategy, rec.chunk_size, rec.chunk_overlap)
print(rec.explanation)

chunks = ungraph.ingest_document(
    FIXTURE,
    chunk_size=rec.chunk_size,
    chunk_overlap=rec.chunk_overlap,
)
print("chunks:", len(chunks))
```

`quality_score` del recomendador es heurística local, **no** scorecard experimental ([PRODUCT §5](../product/PRODUCT.md)).

## 5. Pipeline mínimo (configure → ingest → search)

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="tu_contraseña",
)

FIXTURE = "tests/fixtures/topology_alpha.md"
chunks = ungraph.ingest_document(FIXTURE, chunk_size=400, chunk_overlap=80)
print("chunks:", len(chunks))

results = ungraph.hybrid_search("topology", limit=5)
for r in results:
    print(r.score, r.content[:200])
```

**Resultado observable:** `len(chunks) > 0` y al menos un hit con “topology” (o score listado).

## 6. Basic retriever como patrón nombrado

Equivalente tipado a full-text vía `search_with_pattern` (mismo tipo `SearchResult`):

```python
results = ungraph.search_with_pattern(
    "topology",
    pattern_type="basic",
    limit=5,
)
for r in results:
    print(r.score, r.chunk_id, r.content[:160])
```

Concepto léxico (no duplicar aquí): [`../concepts/sp-lexical-graphs.md`](../concepts/sp-lexical-graphs.md). Contrato de patrones: [`../api/sp-search-patterns.md`](../api/sp-search-patterns.md). How-to: [`../guides/search.md`](../guides/search.md).

## is / will be

| | |
|--|--|
| **is** | `configure`, `ingest_document`, `search` / `vector_search` / `hybrid_search`, `suggest_chunking_strategy`, `search_with_pattern(..., pattern_type="basic")` en `main` |
| **will be** | Depuración EVI, creencias first-class, ranking confrontable — [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [PRODUCT §5](../product/PRODUCT.md) |

No afirmar “mejor retrieval” ni precisión sin ExperimentRun en `validation/`.

## Open claims

N/A (página de mínimos reproductibles). Hipótesis medibles: plan maestro / research.

## Siguiente

- Avanzados: [`sp-advanced-examples.md`](sp-advanced-examples.md)
- Notebooks: [`sp-notebooks.md`](sp-notebooks.md)
- Guías: [quickstart](../guides/sp-quickstart.md) · [ingesta](../guides/sp-ingestion.md) · [búsqueda](../guides/search.md)
