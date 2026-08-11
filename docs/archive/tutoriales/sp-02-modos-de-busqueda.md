# Tutorial 2 — Modos de búsqueda

**Estado:** Implementado
**Skill:** `graphrag-pattern`
**Versión mínima:** `ungraph` 0.1.5
**Tiempo estimado:** 20 min

> **Prerequisito:** Haber completado el [Tutorial 1](sp-01-primer-grafo.md) o tener datos en Neo4j.

---

## Setup: datos de ejemplo

Antes de comparar los modos de búsqueda necesitamos algunos documentos en el grafo.
Si ya los tienes del Tutorial 1, puedes saltar directamente al [Paso 2](#2-búsqueda-textual-fulltext).

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
)

# Ingestar 3 documentos de ejemplo
documentos = [
    "intro_ia.md",
    "manual_tecnico.txt",
    "informe_ml.pdf",
]

for doc in documentos:
    chunks = ungraph.ingest_document(doc)
    print(f"✅ {doc}: {len(chunks)} chunks")
```

---

## 2. Búsqueda textual (`search`)

Busca por coincidencia exacta de palabras clave usando el índice full-text de Neo4j.

```python
results = ungraph.search("machine learning", limit=5)

print(f"🔍 Resultados (texto): {len(results)}\n")
for i, result in enumerate(results, 1):
    print(f"{i}. Score: {result.score:.4f}")
    print(f"   {result.content[:200]}...")
    print()
```

**Cuándo funciona mejor:**
- Términos técnicos exactos: `"LSTM"`, `"backpropagation"`, `"ReLU"`
- Nombres propios o siglas
- Cuando sabes exactamente las palabras que buscas

---

## 3. Búsqueda vectorial (`vector_search`)

Busca por similitud semántica usando embeddings. Entiende sinónimos y conceptos relacionados.

```python
results = ungraph.vector_search("aprendizaje automático", limit=5)

print(f"🔍 Resultados (vectorial): {len(results)}\n")
for i, result in enumerate(results, 1):
    print(f"{i}. Score: {result.score:.4f}")
    print(f"   {result.content[:200]}...")
    print()
```

> La primera llamada puede tardar unos segundos mientras se carga el modelo de embeddings.

**Cuándo funciona mejor:**
- Conceptos abstractos o semánticos
- Búsquedas en otro idioma (p. ej. buscar en español contenido en inglés)
- Cuando no conoces las palabras exactas del documento

---

## 4. Búsqueda híbrida (`hybrid_search`)

Combina búsqueda textual y vectorial con pesos configurables. Es el modo recomendado para uso general.

```python
# Pesos por defecto: 30% texto, 70% vectorial
results = ungraph.hybrid_search("redes neuronales profundas", limit=5)

for i, result in enumerate(results, 1):
    print(f"{i}. Score: {result.score:.4f}")
    print(f"   {result.content[:200]}...")
```

### Ajustar los pesos

```python
# Énfasis en texto: útil para términos técnicos exactos
results_text = ungraph.hybrid_search(
    "LSTM long short-term memory",
    limit=5,
    weights=(0.7, 0.3),   # 70% texto, 30% vectorial
)

# Énfasis en semántica: útil para búsquedas conceptuales
results_semantic = ungraph.hybrid_search(
    "cómo aprenden los modelos de lenguaje",
    limit=5,
    weights=(0.2, 0.8),   # 20% texto, 80% vectorial
)
```

---

## 5. Búsqueda con patrón GraphRAG (`search_with_pattern`)

Usa patrones de recuperación especializados que aprovechan la estructura del grafo.

### 5.1 — `basic` (búsqueda full-text simple)

Equivalente a `search()`, pero a través de la interfaz de patrones:

```python
results = ungraph.search_with_pattern(
    "inteligencia artificial",
    pattern_type="basic",
    limit=5
)
```

### 5.2 — `metadata_filtering` (filtrar por metadatos)

Limita la búsqueda a documentos con propiedades específicas:

```python
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "intro_ia.md"},
    limit=10
)
```

Filtros disponibles: `filename`, `page_number`, `file_type`, y cualquier propiedad
que hayas añadido al ingestar.

### 5.3 — `parent_child` (contexto jerárquico)

Busca en chunks (hijos) y expande el resultado al nodo `Page` padre para devolver
más contexto:

```python
results = ungraph.search_with_pattern(
    "transformers architecture",
    pattern_type="parent_child",
    parent_label="Page",
    child_label="Chunk",
    limit=5
)
```

Útil cuando un chunk individual no contiene suficiente contexto y necesitas la
página completa donde aparece.

---

## 6. Tabla comparativa

| Modo | Función | Índice usado | Requiere embeddings | Mejor para |
|------|---------|-------------|---------------------|-----------|
| Textual | `search()` | Full-text Neo4j | No | Palabras clave exactas |
| Vectorial | `vector_search()` | Vector index | Sí | Semántica, sinónimos |
| Híbrida | `hybrid_search()` | Ambos | Sí | Uso general (recomendado) |
| `basic` | `search_with_pattern(..., "basic")` | Full-text | No | Igual que textual |
| `metadata_filtering` | `search_with_pattern(..., "metadata_filtering")` | Full-text + filtro | No | Buscar en documentos específicos |
| `parent_child` | `search_with_pattern(..., "parent_child")` | Full-text + grafo | No | Contexto expandido (página completa) |

### Guía rápida de elección

```
¿Sabes las palabras exactas?
  └─ Sí → search() o basic
  └─ No → vector_search() o hybrid_search()

¿Necesitas filtrar por documento/tipo?
  └─ Sí → metadata_filtering

¿El chunk es demasiado corto y necesitas más contexto?
  └─ Sí → parent_child

¿Uso general sin restricciones?
  └─ hybrid_search() con pesos por defecto (0.3, 0.7)
```

---

## 7. Nota sobre `metadata_filtering`

`metadata_filtering` es especialmente útil en bases de conocimiento multi-documento
para acotar la búsqueda a una fuente específica:

```python
# Buscar solo en archivos PDF
resultados_pdf = ungraph.search_with_pattern(
    "análisis de datos",
    pattern_type="metadata_filtering",
    metadata_filters={"file_type": "pdf"},
    limit=10
)

# Buscar solo en la página 3 de un documento
resultados_p3 = ungraph.search_with_pattern(
    "conclusiones",
    pattern_type="metadata_filtering",
    metadata_filters={"filename": "informe.md", "page_number": 3},
    limit=5
)
```

---

## Código completo de comparación

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
)

query = "redes neuronales"

print("=" * 60)
print(f"Query: '{query}'\n")

# Textual
print("1. BÚSQUEDA TEXTUAL")
for r in ungraph.search(query, limit=3):
    print(f"  Score {r.score:.4f}: {r.content[:80]}...")

# Vectorial
print("\n2. BÚSQUEDA VECTORIAL")
for r in ungraph.vector_search(query, limit=3):
    print(f"  Score {r.score:.4f}: {r.content[:80]}...")

# Híbrida
print("\n3. BÚSQUEDA HÍBRIDA (30/70)")
for r in ungraph.hybrid_search(query, limit=3, weights=(0.3, 0.7)):
    print(f"  Score {r.score:.4f}: {r.content[:80]}...")

# Parent-child
print("\n4. PARENT-CHILD (contexto expandido)")
for r in ungraph.search_with_pattern(query, pattern_type="parent_child", limit=3):
    print(f"  Score {r.score:.4f}: {r.content[:80]}...")
```

---

## Próximos pasos

- **Tutorial 3** — [Ingesta multi-fuente](sp-03-ingesta-multifuente.md): adapta la estrategia de chunking según el tipo de documento.
- **Guía de búsqueda** — [docs/guides/search.md](../guides/search.md)
- **Patrones avanzados GDS** — requieren `pip install ungraph[gds]`; ver [docs/api/advanced-search-patterns.md](../api/advanced-search-patterns.md)
