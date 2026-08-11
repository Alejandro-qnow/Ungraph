# Tutorial 3 — Ingesta multi-fuente

**Estado:** Implementado (`.md`, `.txt`, `.docx`, `.pdf`)
**Skills:** `eti-pipeline` + `kg-schema`
**Versión mínima:** `ungraph` 0.1.5
**Tiempo estimado:** 25 min

> **Prerequisito:** Haber completado el [Tutorial 1](sp-01-primer-grafo.md).

---

## 1. Tipos de fuente soportados

| Formato | Extensión | Loader interno | Dependencia adicional |
|---------|-----------|---------------|----------------------|
| Markdown | `.md` | LangChain UnstructuredMarkdown | — |
| Texto plano | `.txt` | LangChain TextLoader | — |
| Word | `.docx` | LangChain UnstructuredWord | `python-docx` |
| PDF | `.pdf` | Docling | `ungraph[docling]` |

> **PDF:** La ingesta de PDF requiere Docling. Instálalo con:
> ```bash
> pip install ungraph[docling]
> ```
> Si no está disponible, `ingest_document()` lanzará un error informativo.

---

## 2. `suggest_chunking_strategy` — recomendación automática

Antes de ingestar, Ungraph puede analizar el documento y recomendar la estrategia
de chunking óptima según su estructura:

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
)

# Obtener recomendación para un archivo Markdown
rec = ungraph.suggest_chunking_strategy("tutorial.md")

print(f"Estrategia recomendada: {rec.strategy}")
print(f"Chunk size:             {rec.chunk_size}")
print(f"Chunk overlap:          {rec.chunk_overlap}")
print(f"Puntuación de calidad:  {rec.quality_score:.2f}/1.0")
print(f"\nExplicación:\n{rec.explanation}")
```

Salida típica para un Markdown con headers:

```
Estrategia recomendada: markdown_header
Chunk size:             800
Chunk overlap:          100
Puntuación de calidad:  0.91/1.0

Explicación:
The strategy 'markdown_header' is recommended because:
- The document is Markdown with header structure
- The strategy preserves header hierarchy
- High preservation of complete sentences (>90%)
- The document has 12 headers
- The document has 34 paragraphs
- Will generate approximately 15 chunks
- Average chunk size: 620 characters
- Quality score: 0.91/1.0
```

### Ver alternativas evaluadas

```python
rec = ungraph.suggest_chunking_strategy("documento.md", evaluate_all=True)

print("Estrategia recomendada:", rec.strategy)
print("\nAlternativas evaluadas:")
for alt in rec.alternatives:
    print(f"  - {alt['strategy']}: score {alt['score']:.2f}, "
          f"{alt['num_chunks']} chunks (avg {alt['avg_chunk_size']:.0f} chars)")
```

---

## 3. Ingesta de un archivo Markdown

Los archivos Markdown preservan la jerarquía de headers. La estrategia
`markdown_header` divide el contenido siguiendo los títulos `#`, `##`, `###`.

```python
# Recomendación y luego ingesta usando los parámetros sugeridos
rec = ungraph.suggest_chunking_strategy("guia.md")

chunks = ungraph.ingest_document(
    "guia.md",
    chunk_size=rec.chunk_size,
    chunk_overlap=rec.chunk_overlap,
)

print(f"✅ {len(chunks)} chunks desde Markdown")
print(f"   Primer chunk: {chunks[0].content[:120]}...")
```

Verificar en Neo4j:

```cypher
MATCH (f:File {file_type: "md"})-[:HAS_PAGE]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN f.filename, count(c) AS chunks
```

---

## 4. Ingesta de un PDF

```python
# Los PDFs suelen tener páginas como unidad lógica
rec_pdf = ungraph.suggest_chunking_strategy("informe.pdf")
print(f"Estrategia para PDF: {rec_pdf.strategy}")

chunks = ungraph.ingest_document(
    "informe.pdf",
    chunk_size=rec_pdf.chunk_size,
    chunk_overlap=rec_pdf.chunk_overlap,
)

print(f"✅ {len(chunks)} chunks desde PDF")
```

> **Docling** extrae estructura avanzada de los PDF (tablas, listas, secciones).
> Si el PDF es escaneado (sin texto seleccionable), necesitarás OCR — Docling lo
> soporta automáticamente cuando están disponibles los motores compatibles.

---

## 5. Ingesta de un archivo TXT

El texto plano no tiene estructura marcada. Ungraph usa `recursive_character`
por defecto, que divide respetando párrafos y frases.

```python
rec_txt = ungraph.suggest_chunking_strategy("notas.txt")
print(f"Estrategia para TXT: {rec_txt.strategy}")

chunks = ungraph.ingest_document(
    "notas.txt",
    chunk_size=rec_txt.chunk_size,
    chunk_overlap=rec_txt.chunk_overlap,
)

print(f"✅ {len(chunks)} chunks desde TXT")
```

> Los archivos `.txt` con encodings distintos de UTF-8 son detectados automáticamente
> (ISO-8859-1, Windows-1252, etc.).

---

## 6. Comparar la estructura del grafo por tipo

Después de ingestar los tres tipos, puedes comparar la estructura resultante:

```cypher
// Comparar número de chunks por tipo de archivo
MATCH (f:File)-[:HAS_PAGE]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN
    f.file_type AS tipo,
    f.filename  AS archivo,
    count(DISTINCT p) AS paginas,
    count(c) AS chunks,
    avg(size(c.content)) AS avg_chars
ORDER BY tipo
```

Resultado esperado:

```
tipo  | archivo       | paginas | chunks | avg_chars
------|---------------|---------|--------|----------
md    | guia.md       |       1 |     15 |      620
pdf   | informe.pdf   |       8 |     40 |      510
txt   | notas.txt     |       1 |     12 |      750
```

### ¿Cambia la estructura de chunks?

Sí. La estructura del grafo de chunks depende del tipo de documento:

| Tipo | Estructura típica | Relación `NEXT_CHUNK` |
|------|------------------|-----------------------|
| `.md` | Chunks agrupados por sección/header | Secuencial dentro del documento |
| `.pdf` | Chunks agrupados por página | Secuencial dentro de cada página |
| `.txt` | Chunks por párrafo/longitud | Secuencial lineal |

---

## 7. Metadatos de documento

Todos los documentos incluyen metadatos en el nodo `File`:

```python
# Ver metadatos del primer chunk ingestado
chunks = ungraph.ingest_document("guia.md")
chunk = chunks[0]
print(f"chunk_id:    {chunk.chunk_id}")
print(f"content len: {len(chunk.content)}")
```

En Neo4j puedes consultar los metadatos del nodo `File`:

```cypher
MATCH (f:File)
RETURN f.filename, f.file_path, f.file_type
LIMIT 10
```

### Propiedades del nodo File

| Propiedad | Presente en | Descripción |
|-----------|-------------|-------------|
| `filename` | todos | Nombre del archivo |
| `file_path` | todos | Ruta completa |
| `file_type` | todos | `md`, `txt`, `docx`, `pdf` |
| `source` | todos | Igual que `file_path` |
| `encoding` | `.txt` | Encoding detectado (ej. `iso-8859-1`) |

---

## Código completo: pipeline multi-fuente

```python
import ungraph
from pathlib import Path

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
)

archivos = [
    Path("guia.md"),
    Path("notas.txt"),
    Path("informe.pdf"),   # requiere ungraph[docling]
]

total_chunks = 0

for archivo in archivos:
    if not archivo.exists():
        print(f"⚠️  No encontrado: {archivo}")
        continue

    # Recomendación automática de chunking
    rec = ungraph.suggest_chunking_strategy(archivo)
    print(f"\n📄 {archivo.name}")
    print(f"   Estrategia: {rec.strategy} (score: {rec.quality_score:.2f})")
    print(f"   chunk_size={rec.chunk_size}, overlap={rec.chunk_overlap}")

    # Ingestar
    chunks = ungraph.ingest_document(
        archivo,
        chunk_size=rec.chunk_size,
        chunk_overlap=rec.chunk_overlap,
    )

    total_chunks += len(chunks)
    print(f"   ✅ {len(chunks)} chunks creados")

print(f"\n🎉 Total: {total_chunks} chunks en el grafo")
```

---

## Próximos pasos

- **Tutorial 2** — [Modos de búsqueda](sp-02-modos-de-busqueda.md): compara los 4 modos de recuperación sobre estos datos.
- **Guía de patrones personalizados** — [docs/guides/custom-patterns.md](../guides/custom-patterns.md): define tu propio esquema de nodos y relaciones.
- **Patrones predefinidos** — `ungraph.domain.value_objects.predefined_patterns`
