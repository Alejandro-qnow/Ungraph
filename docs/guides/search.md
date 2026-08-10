# Guía de Búsqueda en el Grafo

Esta guía explica cómo buscar información en el grafo de conocimiento usando Ungraph.

## Tipos de Búsqueda

Ungraph soporta tres tipos principales de búsqueda:

1. **Búsqueda por Texto**: Usa índice full-text de Neo4j
2. **Búsqueda Vectorial**: Usa similitud semántica con embeddings
3. **Búsqueda Híbrida**: Combina texto y vectorial

## Búsqueda por Texto

La búsqueda más simple y rápida:

```python
import ungraph

results = ungraph.search("computación cuántica", limit=5)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
    print(f"Chunk ID: {result.chunk_id}")
    print("---")
```

**Características:**
- ⚡ Muy rápida
- 🎯 Buena para búsquedas por palabras clave
- 📝 Usa índice full-text de Neo4j

## Búsqueda Vectorial

Búsqueda por similitud semántica:

```python
import ungraph
from ungraph import HuggingFaceEmbeddingService

# Generar embedding de la query
embedding_service = HuggingFaceEmbeddingService()
query_embedding = embedding_service.generate_embedding("inteligencia artificial")

# Buscar usando el embedding
from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

search_service = Neo4jSearchService()
results = search_service.vector_search(query_embedding, limit=5)
search_service.close()

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content}")
```

**Características:**
- 🧠 Entiende significado semántico
- 🎯 Mejor para conceptos abstractos
- 📊 Usa similitud de coseno entre embeddings

## Búsqueda Híbrida

Combina texto y vectorial para mejores resultados:

```python
import ungraph

results = ungraph.hybrid_search(
    "deep learning",
    limit=10,
    weights=(0.3, 0.7)  # 30% texto, 70% vectorial
)

for result in results:
    print(f"Score combinado: {result.score:.3f}")
    print(f"Contenido: {result.content}")
    
    # Contexto adicional
    if result.previous_chunk_content:
        print(f"Contexto anterior: {result.previous_chunk_content[:100]}...")
    if result.next_chunk_content:
        print(f"Contexto siguiente: {result.next_chunk_content[:100]}...")
    print("=" * 80)
```

**Características:**
- 🎯 Mejor precisión que búsqueda simple
- 🔄 Combina señales de texto y semántica
- 📈 Ajustable con pesos personalizados

## Reconstruir Contexto Completo

Los resultados incluyen contexto de chunks adyacentes:

```python
import ungraph

results = ungraph.hybrid_search("tema de interés", limit=3)

for result in results:
    contexto_completo = ""
    
    if result.previous_chunk_content:
        contexto_completo += f"[Anterior]\n{result.previous_chunk_content}\n\n"
    
    contexto_completo += f"[Principal]\n{result.content}\n\n"
    
    if result.next_chunk_content:
        contexto_completo += f"[Siguiente]\n{result.next_chunk_content}"
    
    print(contexto_completo)
    print("=" * 80)
```

## Ajustar Pesos en Búsqueda Híbrida

Los pesos determinan qué tan importante es cada tipo de búsqueda:

```python
# Más peso a texto (mejor para palabras clave exactas)
results = ungraph.hybrid_search(
    "palabra clave exacta",
    weights=(0.7, 0.3)  # 70% texto, 30% vectorial
)

# Más peso a vectorial (mejor para conceptos)
results = ungraph.hybrid_search(
    "concepto abstracto",
    weights=(0.2, 0.8)  # 20% texto, 80% vectorial
)

# Balanceado (default)
results = ungraph.hybrid_search(
    "consulta general",
    weights=(0.3, 0.7)  # Default
)
```

## Ejemplo Completo

```python
import ungraph

# 1. Buscar información
query = "machine learning applications"
results = ungraph.hybrid_search(query, limit=5)

# 2. Procesar resultados
print(f"Encontrados {len(results)} resultados para: '{query}'\n")

for i, result in enumerate(results, 1):
    print(f"Resultado {i}:")
    print(f"  Score: {result.score:.4f}")
    print(f"  Chunk ID: {result.chunk_id}")
    print(f"  Contenido: {result.content[:300]}...")
    
    # Mostrar contexto si está disponible
    if result.previous_chunk_content or result.next_chunk_content:
        print("\n  Contexto:")
        if result.previous_chunk_content:
            print(f"    Anterior: {result.previous_chunk_content[:150]}...")
        if result.next_chunk_content:
            print(f"    Siguiente: {result.next_chunk_content[:150]}...")
    
    print("\n" + "-" * 80 + "\n")
```

## Patrones de Búsqueda GraphRAG (Próximamente)

En desarrollo: patrones avanzados de búsqueda basados en GraphRAG:

- **Parent-Child Retriever**: Busca en nodos padre y expande a hijos
- **Community Summary**: Encuentra comunidades de nodos relacionados
- **Graph-Enhanced Vector Search**: Combina vectorial con estructura del grafo
- **Metadata Filtering**: Filtra por metadatos específicos

Ver [documentación de patrones GraphRAG](../api/sp-search-patterns.md) para más detalles.

## Mejores Prácticas

1. **Empezar con búsqueda híbrida**: Generalmente da mejores resultados
2. **Ajustar pesos según necesidad**: Más texto para palabras clave, más vectorial para conceptos
3. **Usar límites razonables**: `limit=5-10` suele ser suficiente
4. **Reconstruir contexto**: Usa chunks adyacentes para mejor comprensión
5. **Iterar sobre resultados**: Los primeros resultados suelen ser los más relevantes

## Referencias

- [Guía de Inicio Rápido](sp-quickstart.md)
- [Patrones de Búsqueda GraphRAG](../api/sp-search-patterns.md)
- [API Pública](../api/sp-public-api.md)








