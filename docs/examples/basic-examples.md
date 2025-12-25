# Ejemplos Básicos

Ejemplos simples de uso de Ungraph.

## Ejemplo 1: Ingerir un Documento

```python
import ungraph

# Ingerir documento
chunks = ungraph.ingest_document("mi_documento.md")

print(f"✅ Documento ingerido: {len(chunks)} chunks creados")
```

## Ejemplo 2: Buscar Información

```python
import ungraph

# Buscar
results = ungraph.search("tema de interés", limit=5)

# Mostrar resultados
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
    print("---")
```

## Ejemplo 3: Búsqueda Híbrida

```python
import ungraph

# Búsqueda híbrida
results = ungraph.hybrid_search(
    "inteligencia artificial",
    limit=10,
    weights=(0.3, 0.7)
)

# Procesar resultados
for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content}")
    print("=" * 80)
```

## Ejemplo 4: Obtener Recomendación de Chunking

```python
import ungraph

# Obtener recomendación
recommendation = ungraph.suggest_chunking_strategy("documento.md")

print(f"Estrategia: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explicación: {recommendation.explanation}")

# Usar la recomendación
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)
```

## Ejemplo 5: Pipeline Completo

```python
import ungraph

# 1. Configurar
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="tu_contraseña"
)

# 2. Obtener recomendación
recommendation = ungraph.suggest_chunking_strategy("documento.md")

# 3. Ingerir
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)

# 4. Buscar
results = ungraph.hybrid_search("tema", limit=5)

# 5. Mostrar resultados
for result in results:
    print(result.content)
```

## Referencias

- [Guía de Inicio Rápido](../guides/quickstart.md)
- [Guía de Ingesta](../guides/ingestion.md)
- [Guía de Búsqueda](../guides/search.md)




