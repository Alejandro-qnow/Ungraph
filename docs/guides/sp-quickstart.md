# Inicio rápido

Recorrido mínimo: instalar → configurar Neo4j → ingerir → buscar.  
Audiencia: developer. Espina ETI: [`../concepts/eti-spine.md`](../concepts/eti-spine.md). Contrato: [`../api/sp-public-api.md`](../api/sp-public-api.md).

## Prerrequisitos

1. Python 3.10+ y Neo4j accesible (Bolt).
2. Credenciales Neo4j (`.env` o `ungraph.configure`).
3. Paquete instalado:

```bash
pip install ungraph
# opcional: CLI
pip install ungraph[cli]
```

**Resultado observable:** `import ungraph` sin error; `ungraph.__version__` imprime la versión del paquete.

## Configuración

### Variables de entorno

```env
UNGRAPH_NEO4J_URI=bolt://localhost:7687
UNGRAPH_NEO4J_USER=neo4j
UNGRAPH_NEO4J_PASSWORD=tu_contraseña
UNGRAPH_NEO4J_DATABASE=neo4j
UNGRAPH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

También se admiten alias sin prefijo (`NEO4J_URI`, `NEO4J_PASSWORD`, …). Detalle: [`../api/sp-configuration.md`](../api/sp-configuration.md).

### Programática

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="tu_contraseña",
    neo4j_database="neo4j",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
)
```

## CLI (opcional)

Con Neo4j configurado:

```bash
ungraph --help
ungraph setup --database-init
ungraph graph --ping
ungraph ingest --path ruta/al/archivo.md
ungraph ingest --folder ./documentos
```

**Resultado observable:** `graph --ping` confirma conexión; `ingest` deja nodos File/Page/Chunk consultables en Neo4j.

## Ingerir un documento

```python
import ungraph

chunks = ungraph.ingest_document(
    "mi_documento.md",
    chunk_size=1000,
    chunk_overlap=200,
)

print(len(chunks))
print(chunks[0].id, chunks[0].page_content[:120])
```

**is:** carga → limpieza opcional → chunks → embeddings → persistencia léxica (`FILE_PAGE_CHUNK` por defecto). El slot Inference (NER/LLM/…) se activa según `UNGRAPH_INFERENCE_MODE`; ver [`../concepts/inference-slot.md`](../concepts/inference-slot.md).

**Resultado observable:** `len(chunks) > 0` y chunks con `id` / `page_content`.

## Buscar

Texto:

```python
results = ungraph.search("computación cuántica", limit=5)
for r in results:
    print(r.score, r.chunk_id, r.content[:160])
```

Híbrida (texto + vector):

```python
results = ungraph.hybrid_search(
    "inteligencia artificial",
    limit=10,
    weights=(0.3, 0.7),  # (texto, vector)
)
for r in results:
    print(r.score, r.content[:160])
    if r.previous_chunk_content:
        print("prev:", r.previous_chunk_content[:80])
    if r.next_chunk_content:
        print("next:", r.next_chunk_content[:80])
```

Vectorial:

```python
results = ungraph.vector_search("aprendizaje automático", limit=5)
```

**is:** búsqueda = **interfaz** sobre el grafo (retrieval), no definición de conocimiento. GraphRAG / patrones: [`search.md`](search.md), [`../api/sp-search-patterns.md`](../api/sp-search-patterns.md).

**Resultado observable:** lista de `SearchResult` con `score`, `content`, `chunk_id`.

## Chunking sugerido (opcional)

```python
rec = ungraph.suggest_chunking_strategy("mi_documento.md")
print(rec.strategy, rec.chunk_size, rec.chunk_overlap)
print(rec.explanation)

chunks = ungraph.ingest_document(
    "mi_documento.md",
    chunk_size=rec.chunk_size,
    chunk_overlap=rec.chunk_overlap,
)
```

`quality_score` es heurística del recomendador, no scorecard experimental (PRODUCT [§5](../product/PRODUCT.md)).

## Pipeline mínimo

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="tu_contraseña",
)

rec = ungraph.suggest_chunking_strategy("documento.md")
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=rec.chunk_size,
    chunk_overlap=rec.chunk_overlap,
)
print("chunks:", len(chunks))

results = ungraph.hybrid_search("tema de interés", limit=5)
for r in results:
    print(r.score, r.content[:200])
```

## Qué no promete este quickstart

| | |
|--|--|
| **is** | Ingesta léxica + búsqueda text/vector/hybrid vía API pública en `main` |
| **will be** | Depuración EVI, creencias first-class, validación PRODUCT §5 — ver [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`../product/PRODUCT.md`](../product/PRODUCT.md) |

## Solución de problemas

### AuthError / fallo de conexión Neo4j

1. Neo4j en ejecución; URI y puerto correctos.
2. Usuario/contraseña válidos.

```python
from ungraph.core.configuration import get_settings

s = get_settings()
print(s.neo4j_uri, s.neo4j_user, s.neo4j_database)
```

### UnicodeDecodeError al cargar archivo

La carga prueba varios encodings (utf-8, windows-1252, latin-1, …). Si falla, normaliza el archivo a UTF-8.

## Siguientes pasos

- [Ingesta](sp-ingestion.md)
- [Búsqueda](search.md)
- [Patrones personalizados](sp-custom-patterns.md)
- [API pública](../api/sp-public-api.md) · [configuración](../api/sp-configuration.md)
- Conceptos: [espina ETI](../concepts/eti-spine.md) · [patrones de grafo](../concepts/sp-graph-patterns.md)
