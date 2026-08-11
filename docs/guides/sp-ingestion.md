# Ingesta de documentos

Pasos para materializar documentos en Neo4j con la API pública.  
Audiencia: developer. Argumento ETI (no duplicar aquí): [`../concepts/eti-spine.md`](../concepts/eti-spine.md) · Extract [`../concepts/extraction.md`](../concepts/extraction.md) · Transform [`../concepts/transformation.md`](../concepts/transformation.md) · slot Infer [`../concepts/inference-slot.md`](../concepts/inference-slot.md).

## Prerrequisitos

1. Neo4j configurado ([`../api/sp-configuration.md`](../api/sp-configuration.md)).
2. `pip install ungraph` (extras de formato según necesidad, p. ej. PDF vía stack Docling del paquete).
3. Archivo accesible en disco (`.md`, `.txt`, `.docx`, `.pdf`, `.html`/`.htm`).

**Resultado observable al final:** lista de `Chunk` y topología léxica File → Page → Chunk (patrón por defecto).

## Uso básico

```python
import ungraph

chunks = ungraph.ingest_document("mi_documento.md")
print(len(chunks), chunks[0].id)
```

## Parámetros (`is`)

Firma estable: [`../api/sp-public-api.md`](../api/sp-public-api.md).

```python
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=1000,
    chunk_overlap=200,
    clean_text=True,
    database=None,              # default: settings
    embedding_model=None,       # default: settings
    pattern=None,               # default: FILE_PAGE_CHUNK
    extraction_recipe=None,     # HTML: XPath/CSS opcional
    source_url=None,            # provenance HTML / crawl
    retrieval_optimization=False,
)
```

| Parámetro | Efecto observable |
|-----------|-------------------|
| `chunk_size` / `chunk_overlap` | Número y solape de chunks |
| `clean_text` | Texto normalizado antes del chunking |
| `pattern` | Topología de nodos/rels (ver [patrones personalizados](sp-custom-patterns.md)) |
| `retrieval_optimization` | Vista de recuperación derivada (`RetrievalChunk`) cuando el repo Neo4j lo soporta |
| `extraction_recipe` / `source_url` | HTML: extracción acotada + URL de provenance |

**Errores típicos:** `FileNotFoundError`, `ValueError` (archivo no procesable), `RuntimeError` (Neo4j).

## Flujo (probe, no teoría)

```text
archivo → Document → Chunks → embeddings → Neo4j
         └─ Inference (slot; según UNGRAPH_INFERENCE_MODE)
```

La recuperación GraphRAG **consume** este almacén; no define el conocimiento. Ver [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md).

## Recomendación de chunking

```python
rec = ungraph.suggest_chunking_strategy("documento.md")
print(rec.strategy, rec.chunk_size, rec.chunk_overlap)
print(rec.explanation)

chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=rec.chunk_size,
    chunk_overlap=rec.chunk_overlap,
)
```

`quality_score` / `alternatives` son salida del recomendador, no validación PRODUCT [§5](../product/PRODUCT.md).

## Formatos

```python
ungraph.ingest_document("documento.md")
ungraph.ingest_document("documento.txt")
ungraph.ingest_document("documento.docx")
ungraph.ingest_document("documento.pdf")
```

Encoding de texto: detección automática (UTF-8 y fallbacks). PDF: extracción vía Docling del stack del paquete (texto/estructura según el loader).

HTML:

```python
# opcional: ExtractionRecipe + source_url — ver API pública
chunks = ungraph.ingest_document("pagina.html", source_url="https://ejemplo.org/pagina")
```

## Varios archivos

```python
from pathlib import Path
import ungraph

for path in Path("./docs_src").glob("*.md"):
    try:
        chunks = ungraph.ingest_document(path)
        print(path.name, len(chunks))
    except Exception as e:
        print(path.name, "ERROR", e)
```

## Topología creada (patrón por defecto)

```text
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
Chunk -[:NEXT_CHUNK]-> Chunk
```

| Elemento | Propiedades habituales (`is`) |
|----------|-------------------------------|
| File | `filename`, `createdAt` |
| Page | `filename`, `page_number` |
| Chunk | `chunk_id`, `page_content`, embeddings / dimensiones |

Concepto: [`../concepts/sp-lexical-graphs.md`](../concepts/sp-lexical-graphs.md) · [`../concepts/sp-graph-patterns.md`](../concepts/sp-graph-patterns.md).

## Inference en la ingesta

| | |
|--|--|
| **is** | Slot configurado por `UNGRAPH_INFERENCE_MODE`: `ner` (default), `pattern`, `llm` (requiere OpenAI/`UNGRAPH_OPENAI_*`); ver configuración |
| **will be** | `hybrid` (NER+LLM) — `NotImplementedError` hoy; depuración EVI / beliefs first-class — [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) |

No confundir “hubo extracción NER/LLM” con “conocimiento validado” (PRODUCT §5).

## Solución de problemas

### UnicodeDecodeError

Normaliza el archivo a UTF-8 o revisa el encoding real.

### AuthError / Neo4j

```python
from ungraph.core.configuration import get_settings
s = get_settings()
print(s.neo4j_uri, s.neo4j_user, s.neo4j_database)
```

### Documento muy grande

Reduce `chunk_size` o parte el archivo antes de ingerir.

## Referencias

- [Inicio rápido](sp-quickstart.md) · [Búsqueda](search.md) · [Patrones](sp-custom-patterns.md)
- [API pública](../api/sp-public-api.md)
- [Configuración](../api/sp-configuration.md)
