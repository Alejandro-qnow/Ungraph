# Tutorial 1 — Tu primer grafo de conocimiento

**Estado:** Implementado
**Skill:** `eti-pipeline`
**Versión mínima:** `ungraph` 0.1.5
**Tiempo estimado:** 15 min

---

## Prerequisitos

| Requisito | Versión mínima | Notas |
|-----------|---------------|-------|
| Python | 3.10+ | |
| Neo4j | 5.x | Local (Desktop/Docker) o AuraDB gratuito |
| `ungraph` | 0.1.5 | `pip install ungraph` |

### Instalar ungraph

```bash
pip install ungraph
```

### Arrancar Neo4j

**Opción A — Neo4j Desktop (recomendado para desarrollo local):**
1. Descarga desde [neo4j.com/download](https://neo4j.com/download/)
2. Crea una base de datos local con contraseña (p. ej. `"password"`)
3. Inicia la base de datos → estado "Running"

**Opción B — Docker:**
```bash
docker run \
  --name neo4j \
  -p7474:7474 -p7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

**Opción C — Neo4j AuraDB (nube gratuita):**
Crea una instancia en [console.neo4j.io](https://console.neo4j.io) y guarda la URI de conexión.

---

## 1. Configuración

`ungraph` necesita saber cómo conectarse a Neo4j. Hay dos formas equivalentes:

### Forma A — Variables de entorno (recomendada para proyectos)

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="password"
```

```python
import ungraph
# No se necesita llamar configure() si las variables de entorno están definidas
```

### Forma B — `configure()` en código

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",   # ⚠️ Usa tu contraseña real
)
```

> **Nota AuraDB:** La URI tendrá la forma `neo4j+s://<id>.databases.neo4j.io`.
> Cambia `bolt://localhost:7687` por esa URI.

---

## 2. Ingestar un documento

El flujo mínimo completo es: cargar un archivo → dividirlo en chunks → generar embeddings → almacenar en Neo4j.

Todo eso ocurre dentro de `ingest_document()`:

```python
import ungraph

# Configurar conexión
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
)

# Ingestar un archivo Markdown
chunks = ungraph.ingest_document("mi_documento.md")

print(f"✅ {len(chunks)} chunks creados")
for chunk in chunks[:3]:
    print(f"  - Chunk {chunk.chunk_id[:8]}...: {chunk.content[:80]}...")
```

### Parámetros opcionales

```python
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=800,      # Tamaño de cada chunk en caracteres (por defecto 1000)
    chunk_overlap=150,   # Solapamiento entre chunks (por defecto 200)
    clean_text=True,     # Limpiar texto antes de procesar (por defecto True)
)
```

> **Formatos soportados:** `.md`, `.txt`, `.docx`, `.pdf`
> Ver Tutorial 3 para ingesta multi-fuente con estrategia adaptada por tipo.

---

## 3. Verificar en Neo4j Browser

Abre [http://localhost:7474](http://localhost:7474) en tu navegador, conéctate con tu usuario/contraseña, y ejecuta esta query Cypher:

```cypher
// Ver la estructura completa del grafo
MATCH (f:File)-[:HAS_PAGE]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN f.filename AS archivo, count(p) AS paginas, count(c) AS chunks
ORDER BY chunks DESC
```

Para ver el contenido de los primeros chunks:

```cypher
MATCH (c:Chunk)
RETURN c.chunk_id, c.content, c.chunk_index
ORDER BY c.chunk_index
LIMIT 10
```

Si prefieres una vista visual del grafo, ejecuta:

```cypher
MATCH path = (f:File)-[:HAS_PAGE]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
RETURN path LIMIT 20
```

---

## 4. Primera búsqueda

Una vez que hay datos en el grafo, puedes buscar por texto:

```python
results = ungraph.search("inteligencia artificial", limit=5)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
    print("---")
```

Cada `SearchResult` tiene:
- `result.score` — puntuación de relevancia (mayor = más relevante)
- `result.content` — texto del chunk
- `result.chunk_id` — identificador único del chunk
- `result.previous_chunk_content` — chunk anterior (contexto)
- `result.next_chunk_content` — chunk siguiente (contexto)

---

## 5. ¿Qué se creó en el grafo?

El patrón por defecto de Ungraph es `FILE_PAGE_CHUNK`. Para cada documento ingestado se crean:

```
(File) ──HAS_PAGE──> (Page) ──HAS_CHUNK──> (Chunk)
                                              │
                               NEXT_CHUNK ───▶│
                                              ▼
                                           (Chunk)
```

| Nodo | Propiedades principales |
|------|------------------------|
| `File` | `filename`, `file_path`, `file_type` |
| `Page` | `page_number`, `source` |
| `Chunk` | `chunk_id`, `content`, `chunk_index`, `embedding` |

La relación `NEXT_CHUNK` conecta chunks consecutivos del mismo documento, lo que permite recuperar contexto adyacente durante la búsqueda.

---

## Código completo de ejemplo

```python
import ungraph

# 1. Configurar
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
)

# 2. Ingestar
chunks = ungraph.ingest_document("mi_documento.md")
print(f"✅ Documento dividido en {len(chunks)} chunks")

# 3. Buscar
results = ungraph.search("tema de búsqueda", limit=3)
print(f"\n🔍 Resultados:")
for i, result in enumerate(results, 1):
    print(f"\n  {i}. Score: {result.score:.3f}")
    print(f"     {result.content[:150]}...")
```

---

## Próximos pasos

- **Tutorial 2** — [Modos de búsqueda](sp-02-modos-de-busqueda.md): compara búsqueda textual, vectorial, híbrida y por patrones GraphRAG.
- **Tutorial 3** — [Ingesta multi-fuente](sp-03-ingesta-multifuente.md): ingesta PDF, DOCX y TXT con estrategia de chunking adaptada.
- **Guía de ingesta avanzada** — [docs/guides/search.md](../guides/search.md)
