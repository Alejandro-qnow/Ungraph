# Ejemplos avanzados

Mínimos reproductibles que combinan varios documentos, patrones de grafo y `search_with_pattern`.  
Audiencia: developer. Básicos primero: [`sp-basic-examples.md`](sp-basic-examples.md). Contratos: [`../api/sp-public-api.md`](../api/sp-public-api.md), [`../api/sp-search-patterns.md`](../api/sp-search-patterns.md). How-to: [`../guides/search.md`](../guides/search.md), [`../guides/sp-custom-patterns.md`](../guides/sp-custom-patterns.md).

Retrieval / GraphRAG = **interfaz** sobre el almacén — [`../concepts/eti-spine.md`](../concepts/eti-spine.md), [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md). No son métricas PRODUCT [§5](../product/PRODUCT.md).

## Prerrequisitos

1. Los de [`sp-basic-examples.md`](sp-basic-examples.md) (Neo4j + `ungraph` configurado).
2. Fixtures del repo o archivos locales equivalentes.
3. Para el ejemplo de patrón personalizado: imports desde el paquete `ungraph` (no rutas `domain` / `infrastructure` sueltas).

**Resultado observable global:** listas `SearchResult` o `Chunk` no vacías; para patrones, campos proyectados (`content`, `score`, `next_chunk_content` cuando aplique).

## Fixture / datos

| Archivo | Uso |
|---------|-----|
| [`../../tests/fixtures/topology_alpha.md`](../../tests/fixtures/topology_alpha.md) | Documento A (término **topology**) |
| [`../../tests/fixtures/topology_beta.md`](../../tests/fixtures/topology_beta.md) | Documento B |

```python
ALPHA = "tests/fixtures/topology_alpha.md"
BETA = "tests/fixtures/topology_beta.md"
```

## 1. Ingerir varios documentos

```python
import ungraph
from pathlib import Path

for path in (ALPHA, BETA):
    chunks = ungraph.ingest_document(path, chunk_size=400, chunk_overlap=80)
    print(Path(path).name, len(chunks))
```

**Resultado observable:** dos líneas con `len(chunks) > 0`. Si un path falta: `FileNotFoundError`.

## 2. Reconstruir contexto adyacente

```python
results = ungraph.hybrid_search("topology", limit=3)
for r in results:
    parts = []
    if r.previous_chunk_content:
        parts.append(f"[Anterior]\n{r.previous_chunk_content}")
    parts.append(f"[Principal]\n{r.content}")
    if r.next_chunk_content:
        parts.append(f"[Siguiente]\n{r.next_chunk_content}")
    print("\n\n".join(parts))
    print("---")
```

**Resultado observable:** bloques con etiqueta Principal; vecinos solo si el grafo léxico los aporta.

## 3. Declarar y validar un `GraphPattern`

Patrón = forma de Transform, no motor de Inference. Guía: [`../guides/sp-custom-patterns.md`](../guides/sp-custom-patterns.md). Concepto: [`../concepts/sp-graph-patterns.md`](../concepts/sp-graph-patterns.md).

```python
from ungraph.domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
)
from ungraph.infrastructure.services.neo4j_pattern_service import Neo4jPatternService

chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={"chunk_id": str, "content": str},
    indexes=["chunk_id"],
)
simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Solo chunks",
    node_definitions=[chunk_node],
    relationship_definitions=[],
)

service = Neo4jPatternService()
print("válido:", service.validate_pattern(simple_pattern))
print(service.generate_cypher(simple_pattern, "create")[:400])
```

Uso en ingesta (`is`):

```python
import ungraph

chunks = ungraph.ingest_document(ALPHA, pattern=simple_pattern)
print(len(chunks))
```

**Resultado observable:** `válido: True` (o error de forma); Cypher no vacío; `len(chunks) > 0` si la persistencia acepta el patrón.

Declarar labels de entidad en el patrón **no** rellena Inference sola — [`../concepts/inference-slot.md`](../concepts/inference-slot.md).

## 4. Comparar modos de búsqueda (sin afirmar “mejor”)

```python
import ungraph

query = "topology"
text = ungraph.search(query, limit=5)
hybrid_text = ungraph.hybrid_search(query, limit=5, weights=(0.7, 0.3))
hybrid_vec = ungraph.hybrid_search(query, limit=5, weights=(0.3, 0.7))

print("text:", [round(r.score, 4) for r in text[:3]])
print("hybrid_text:", [round(r.score, 4) for r in hybrid_text[:3]])
print("hybrid_vec:", [round(r.score, 4) for r in hybrid_vec[:3]])
```

**Resultado observable:** tres listas de scores. Los scores son ranking relativo del modo, **no** confianza epistémica ni precisión medida.

## 5. Metadata filtering

Tras ingerir fixtures (el `filename` en nodos suele reflejar el nombre del archivo):

```python
results = ungraph.search_with_pattern(
    "topology",
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "topology_alpha.md"},
    limit=10,
)
for r in results:
    print(r.score, r.content[:160])
```

**Resultado observable:** hits acotados al archivo filtrado (o lista vacía si la propiedad/filename no coincide — comprobar metadata en Neo4j).

## 6. Parent–child (proyección pública)

API pública: `ungraph.search_with_pattern`. Tipo de retorno: `SearchResult` — padre en `content`/`score`; hijos concatenados en `next_chunk_content` (no hay `parent_content` / `children` en el tipo público).

```python
import ungraph

results = ungraph.search_with_pattern(
    "topology",
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=3,
)
for r in results:
    print(r.score, r.chunk_id, r.content[:160])
    print("hijos/contexto:", (r.next_chunk_content or "")[:200])
```

**Resultado observable:** `content` del padre y, si hay expansión, texto en `next_chunk_content`.

Topología léxica: [`../concepts/sp-lexical-graphs.md`](../concepts/sp-lexical-graphs.md).

## 7. Comparar basic vs parent–child vs filtro

```python
import ungraph

query = "topology"
basic = ungraph.search_with_pattern(query, pattern_type="basic", limit=3)
filtered = ungraph.search_with_pattern(
    query,
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "topology_alpha.md"},
    limit=3,
)
parent = ungraph.search_with_pattern(
    query,
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    relationship_type="HAS_CHUNK",
    limit=3,
)

print("basic:", len(basic), [round(r.score, 4) for r in basic])
print("filtered:", len(filtered), [round(r.score, 4) for r in filtered])
print(
    "parent_child:",
    len(parent),
    [(round(r.score, 4), bool(r.next_chunk_content)) for r in parent],
)
```

**Resultado observable:** conteos y scores por patrón. No interpretar diferencias como “ganador” sin protocolo en [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md).

## 8. Patrones avanzados (extras; opcional)

Requieren `pip install ungraph[gds]` y, según patrón, plugin GDS / entidades `MENTIONS`. Contrato: [`../api/sp-advanced-search-patterns.md`](../api/sp-advanced-search-patterns.md).

```python
# Solo si el extra y el grafo cumplen prerequisitos; si no, ImportError / RuntimeError
results = ungraph.search_with_pattern(
    "topology",
    pattern_type="graph_enhanced",
    limit=5,
    max_traversal_depth=2,
)
for r in results:
    print(r.score, r.content[:160])
    print("contexto:", (r.next_chunk_content or "")[:160])
```

**is con prerequisitos:** firmas existen en `main` bajo extras. Sin extra → no afirmar el patrón como capacidad instalada por defecto.

## is / will be

| | |
|--|--|
| **is** | Multi-ingest; `hybrid_search` con vecinos; `GraphPattern` + `ingest_document(..., pattern=)`; `search_with_pattern` básicos (`basic`, `metadata_filtering`, `parent_child`) con proyección a `SearchResult` |
| **will be** | Scorecards confrontables entre modos; depuración EVI; patrones de conocimiento estables desde Infer — [PRODUCT §5](../product/PRODUCT.md), plan maestro |

## Open claims

N/A. Claims medibles de ranking/ET vs ETI → experiment/research, no este archivo.

## Referencias

- [Básicos](sp-basic-examples.md) · [Notebooks](sp-notebooks.md)
- [Búsqueda](../guides/search.md) · [Patrones personalizados](../guides/sp-custom-patterns.md)
- [API pública](../api/sp-public-api.md) · [Patrones de búsqueda](../api/sp-search-patterns.md) · [Avanzados](../api/sp-advanced-search-patterns.md)
- [Léxicos](../concepts/sp-lexical-graphs.md) · [Patrones de grafo](../concepts/sp-graph-patterns.md)
