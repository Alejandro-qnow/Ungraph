# API pública

Contrato estable de la superficie `import ungraph` (paquete de referencia en `main`).  
Audiencia: developer. Contexto epistémico (una línea): la espina es ETI; búsqueda/GraphRAG son interfaz — [`../concepts/eti-spine.md`](../concepts/eti-spine.md).

Configuración: [`sp-configuration.md`](sp-configuration.md). How-to: [`../guides/sp-quickstart.md`](../guides/sp-quickstart.md).

## Funciones

### `ingest_document`

```python
chunks = ungraph.ingest_document(
    file_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    clean_text: bool = True,
    database: Optional[str] = None,
    embedding_model: Optional[str] = None,
    pattern: Optional[GraphPattern] = None,
    extraction_recipe: Optional[ExtractionRecipe] = None,
    source_url: Optional[str] = None,
    retrieval_optimization: bool = False,
) -> List[Chunk]
```

| Parámetro | Descripción |
|-----------|-------------|
| `file_path` | Ruta al archivo (`.md`, `.txt`, `.docx`, `.pdf`, `.html`/`.htm`) |
| `chunk_size` / `chunk_overlap` | Tamaño y solape de chunk (caracteres) |
| `clean_text` | Limpiar texto antes de chunking |
| `database` | Base Neo4j; default = settings |
| `embedding_model` | Modelo de embedding; default = settings |
| `pattern` | `GraphPattern`; default = `FILE_PAGE_CHUNK` |
| `extraction_recipe` | HTML: receta XPath/CSS opcional |
| `source_url` | URL pública de provenance (HTML/crawl) |
| `retrieval_optimization` | Si True, rellena vista de retrieval y puede persistir `(:RetrievalChunk)` |

**Retorna:** `List[Chunk]`.

**Errores:** `FileNotFoundError`, `ValueError`, `RuntimeError` (Neo4j).

```python
import ungraph

chunks = ungraph.ingest_document("documento.md", chunk_size=500)
print(len(chunks), chunks[0].id)
```

`configure(inference_mode=...)` afecta a este camino: el composition root usa el singleton de `get_settings()`.

---

### Inferencia / reasoning (fase I)

Fachadas serializables (también en `ungraph.reasoning`):

```python
# Tras configure(inference_mode="ner"|"pattern"|"llm")
info = ungraph.infer_over_document("documento.md")
# {'document_path', 'chunks_created', 'inference_mode', 'inference_active'}

mined = ungraph.mine_knowledge()          # re-inferencia sobre chunks sin :Fact
stats = ungraph.graph_stats()             # conteos estructurales R/O
topo = ungraph.validate_topology()        # {'ok': bool, 'issues': [...]}
```

| Función | Rol |
|---------|-----|
| `infer_over_document` | Ingest + Infer según `inference_mode` |
| `mine_knowledge` | Re-minado de chunks pendientes |
| `graph_stats` | Stats estructurales |
| `validate_topology` | Invariantes File–Page–Chunk |

Equivalente: `from ungraph.reasoning import mine_knowledge, …`.

**Nota:** `inference_mode=hybrid` (NER↔LLM) sigue **will be** (`NotImplementedError`). El hybrid de **búsqueda** es otro contrato (`hybrid_search`).

---

### `search`

```python
results = ungraph.search(
    query_text: str,
    limit: int = 5,
    database: Optional[str] = None,
) -> List[SearchResult]
```

Búsqueda full-text.

**Errores:** `ValueError` (query vacío), `RuntimeError`.

```python
results = ungraph.search("computación cuántica", limit=10)
```

---

### `vector_search`

```python
results = ungraph.vector_search(
    query_text: str,
    limit: int = 5,
    database: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> List[SearchResult]
```

Embedding de la query + similitud vectorial en el grafo.

**Errores:** `ValueError`, `RuntimeError`.

```python
results = ungraph.vector_search("machine learning", limit=5)
```

---

### `hybrid_search`

```python
results = ungraph.hybrid_search(
    query_text: str,
    limit: int = 5,
    weights: Tuple[float, float] = (0.3, 0.7),
    database: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> List[SearchResult]
```

| Parámetro | Descripción |
|-----------|-------------|
| `weights` | `(text_weight, vector_weight)` |

**Errores:** `ValueError`, `RuntimeError`.

```python
results = ungraph.hybrid_search(
    "inteligencia artificial",
    limit=10,
    weights=(0.4, 0.6),
)
```

---

### `search_with_pattern`

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

Patrones de retrieval GraphRAG. Resultados normalizados a `SearchResult` (campos extra del Cypher se proyectan a `content` / `next_chunk_content` según el patrón).

**Patrones básicos (`is`):** `basic` / `basic_retriever`, `metadata_filtering`, `parent_child` / `parent_child_retriever`.

**Patrones avanzados (`is` con extras):** `local` / `local_retriever`, `graph_enhanced` / `graph_enhanced_vector`, `community_summary` / `community_summary_gds` — requieren módulos opcionales (`ungraph[gds]`, etc.).

**Errores:** `ValueError` (query vacío o `pattern_type` inválido), `RuntimeError`, `ImportError` (extra ausente).

kwargs y detalle: [`sp-search-patterns.md`](sp-search-patterns.md), [`sp-advanced-search-patterns.md`](sp-advanced-search-patterns.md).

```python
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "ai_paper.md"},
    limit=10,
)
```

---

### `suggest_chunking_strategy`

```python
recommendation = ungraph.suggest_chunking_strategy(
    file_path: str | Path,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    evaluate_all: bool = False,
    embedding_model: Any = None,
) -> ChunkingRecommendation
```

**Errores:** `FileNotFoundError`, `ValueError`.

```python
rec = ungraph.suggest_chunking_strategy("documento.md")
print(rec.strategy, rec.chunk_size, rec.chunk_overlap)
```

---

### `configure`

```python
ungraph.configure(
    neo4j_uri: Optional[str] = None,
    neo4j_user: Optional[str] = None,
    neo4j_password: Optional[str] = None,
    neo4j_database: Optional[str] = None,
    embedding_model: Optional[str] = None,
    **kwargs,
) -> None
```

Otros campos de `Settings` vía kwargs / env — [`sp-configuration.md`](sp-configuration.md). También: `ungraph.reset_configuration()`.

```python
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="mi_contraseña",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
)
```

---

## Tipos

### `Chunk`

```python
@dataclass
class Chunk:
    id: str
    page_content: str
    metadata: Dict[str, Any]
```

### `SearchResult`

```python
class SearchResult:
    content: str
    score: float
    chunk_id: str
    chunk_id_consecutive: int
    previous_chunk_content: Optional[str]
    next_chunk_content: Optional[str]
```

En patrones parent–child / comunidad / graph-enhanced, el contexto ampliado suele ir en `next_chunk_content` (no hay campos `parent_content` / `children` en el tipo público).

### `ChunkingRecommendation`

```python
@dataclass
class ChunkingRecommendation:
    strategy: str
    chunk_size: int
    chunk_overlap: int
    explanation: str
    quality_score: float
    alternatives: List[Dict[str, Any]]
    metrics: Dict[str, Any]
```

`quality_score` es heurística del recomendador, no scorecard de validación.

### Otros exportados

Desde `ungraph`: `GraphPattern`, `ExtractionRecipe`, `WebDocument`, `IngestDocumentUseCase` (uso avanzado).  
Value objects de patrón: `ungraph.domain.value_objects.graph_pattern` (`NodeDefinition`, `RelationshipDefinition`).

## Referencias

- [Inicio rápido](../guides/sp-quickstart.md) · [Ingesta](../guides/sp-ingestion.md) · [Búsqueda](../guides/search.md)
- [Configuración](sp-configuration.md)
- [Patrones de búsqueda](sp-search-patterns.md)
