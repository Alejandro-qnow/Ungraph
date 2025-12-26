# Ungraph

Python package for Knowledge graph construction using Neo4j and GraphRAG patterns.

## 🎯 Propósito

Ungraph es una librería Python que convierte datos no estructurados en **Lexical Graphs** usando Neo4j, implementando patrones de **GraphRAG** para búsqueda y recuperación mejorada. Proporciona un pipeline completo para:

1. **Cargar documentos** (Markdown, TXT, Word, PDF) con detección automática de encoding
2. **Dividirlos en chunks inteligentes** con recomendaciones automáticas de estrategia
3. **Generar embeddings** usando modelos de HuggingFace
4. **Persistirlos en un Lexical Graph** (Neo4j) con estructura configurable
5. **Buscar información** usando búsqueda híbrida y patrones GraphRAG (Basic Retriever, Parent-Child Retriever, Metadata Filtering)

**Concepto clave**: Ungraph implementa **Lexical Graphs** (según definición de GraphRAG) que organizan texto en chunks con relaciones estructurales, facilitando la búsqueda semántica y siendo compatibles con patrones básicos de GraphRAG.

## 📦 Instalación

### Requisitos

- **Python**: 3.12 o superior
- **Neo4j**: 5.x o superior (debe estar corriendo y accesible)
- **Dependencias básicas**: Se instalan automáticamente con pip

### Instalación Básica

```bash
pip install ungraph
```

### Módulos Opcionales

Para funcionalidades avanzadas, instala módulos opcionales:

```bash
# Inference - Para fase de inferencia con spaCy NER (extracción de entidades y facts)
pip install ungraph[infer]
# Luego descarga el modelo de idioma:
python -m spacy download en_core_web_sm  # Para inglés
# o
python -m spacy download es_core_news_sm  # Para español

# Graph Data Science - Para patrones avanzados de búsqueda
pip install ungraph[gds]

# Visualización de grafos en Jupyter
pip install ungraph[ynet]

# Herramientas de desarrollo
pip install ungraph[dev]

# Experimentos y evaluación
pip install ungraph[experiments]

# Todas las extensiones
pip install ungraph[all]
```

### Instalación de Neo4j

Si no tienes Neo4j instalado:

1. **Docker** (recomendado):
   ```bash
   docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password neo4j:latest
   ```

2. **Descarga directa**: [Neo4j Desktop](https://neo4j.com/download/) o [Neo4j Community Edition](https://neo4j.com/download-center/#community)

### Instalación del paquete

```bash
pip install ungraph
```

O desde el código fuente:

```bash
git clone https://github.com/tu-usuario/ungraph.git
cd ungraph
pip install -e .
```

### Configuración Inicial

Antes de usar Ungraph, configura la conexión a Neo4j:

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="tu_contraseña",
    neo4j_database="neo4j"
)
```

O usando variables de entorno:

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
export UNGRAPH_NEO4J_USER="neo4j"
export UNGRAPH_NEO4J_PASSWORD="tu_contraseña"
export UNGRAPH_NEO4J_DATABASE="neo4j"
```

## 🚀 Uso Rápido

**Nota**: Asegúrate de tener Neo4j corriendo y configurado antes de ejecutar estos ejemplos.

### Ingerir un Documento

```python
import ungraph

# Configurar conexión (si no usas variables de entorno)
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="tu_contraseña"
)

# Ingerir un documento al grafo
chunks = ungraph.ingest_document("mi_documento.md")

print(f"✅ Documento dividido en {len(chunks)} chunks")
```

### Obtener Recomendación de Chunking

```python
import ungraph

# Obtener recomendación inteligente de estrategia de chunking
recommendation = ungraph.suggest_chunking_strategy("documento.md")

print(f"Estrategia recomendada: {recommendation.strategy}")
print(f"Chunk size: {recommendation.chunk_size}")
print(f"Chunk overlap: {recommendation.chunk_overlap}")
print(f"Explicación: {recommendation.explanation}")
```

### Buscar en el Grafo

```python
import ungraph

# Búsqueda simple por texto
results = ungraph.search("computación cuántica", limit=5)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content[:200]}...")
```

### Búsqueda Híbrida

```python
import ungraph

# Búsqueda híbrida (texto + vectorial)
results = ungraph.hybrid_search(
    "inteligencia artificial",
    limit=10,
    weights=(0.4, 0.6)  # Más peso a búsqueda vectorial
)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Contenido: {result.content}")
    if result.previous_chunk_content:
        print(f"Contexto anterior: {result.previous_chunk_content}")
    if result.next_chunk_content:
        print(f"Contexto siguiente: {result.next_chunk_content}")
```

### Búsqueda con Patrones Avanzados (requiere ungraph[gds])

```python
import ungraph

# Graph-Enhanced Vector Search: Encuentra contexto relacionado a través de entidades
results = ungraph.search_with_pattern(
    "machine learning",
    pattern_type="graph_enhanced",
    limit=5,
    max_traversal_depth=2
)

# Local Retriever: Búsqueda en comunidades pequeñas
results = ungraph.search_with_pattern(
    "neural networks",
    pattern_type="local",
    limit=5,
    community_threshold=3
)
```

Ver [Patrones Avanzados de Búsqueda](docs/api/advanced-search-patterns.md) para más detalles.

## ⚙️ Configuración

### Variables de Entorno

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
export UNGRAPH_NEO4J_USER="neo4j"
export UNGRAPH_NEO4J_PASSWORD="tu_contraseña"
export UNGRAPH_NEO4J_DATABASE="neo4j"
export UNGRAPH_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

O crear un archivo `.env`:

```env
UNGRAPH_NEO4J_URI=bolt://localhost:7687
UNGRAPH_NEO4J_USER=neo4j
UNGRAPH_NEO4J_PASSWORD=tu_contraseña
UNGRAPH_NEO4J_DATABASE=neo4j
UNGRAPH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Configuración Programática

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="tu_contraseña",
    neo4j_database="neo4j",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

## 📚 Documentación Completa

La documentación completa está disponible en la carpeta [`docs/`](docs/README.md):

### Conceptos Fundamentales
- [Introducción](docs/concepts/introduction.md) - Visión general y propósito
- [Patrones de Grafo](docs/concepts/graph-patterns.md) - Sistema de patrones configurables

### Guías de Uso
- [Guía de Inicio Rápido](docs/guides/quickstart.md) - Primeros pasos
- [Patrones de Búsqueda GraphRAG](docs/api/search-patterns.md) - Referencia completa (básicos)
- [Patrones Avanzados de Búsqueda](docs/api/advanced-search-patterns.md) - Patrones avanzados (requieren módulos opcionales)
- [Lexical Graphs](docs/concepts/lexical-graphs.md) - Conceptos fundamentales

### Ejemplos Prácticos
- [Basic Retriever con Lexical Graph](docs/examples/basic-retriever-lexical.md) - Ejemplo completo
- [Parent-Child Retriever](docs/examples/parent-child-retriever.md) - Patrón avanzado

### Ejemplos
- [Notebook: Uso de la Librería](src/notebooks/1.%20Using%20Ungraph%20Library.ipynb) - Ejemplo completo
- [Notebook: Testing Graph Patterns](src/notebooks/2.%20Testing%20Graph%20Patterns.ipynb) - Pruebas sistemáticas

## 🏗️ Arquitectura

El proyecto sigue **Clean Architecture** con las siguientes capas:

```
src/
├── domain/          # Entidades, Value Objects, Interfaces
│   ├── entities/   # Chunk, Document, File, Page
│   ├── value_objects/  # GraphPattern, Embedding, DocumentType
│   └── services/    # Interfaces (ChunkingService, SearchService, etc.)
├── application/     # Casos de uso
│   └── use_cases/   # IngestDocumentUseCase, etc.
├── infrastructure/  # Implementaciones (Neo4j, LangChain)
│   ├── repositories/  # Neo4jChunkRepository
│   └── services/    # Implementaciones concretas
└── utils/           # Código legacy (en migración)
```

**Referencias:**
- [Clean Architecture Principles](docs/theory/clean-architecture.md)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

## 🧪 Tests

```bash
# Tests unitarios (sin Neo4j)
pytest tests/test_domain_entities.py -v
pytest tests/test_graph_patterns.py -v
pytest tests/test_pattern_service.py -v

# Tests de integración (requieren Neo4j)
pytest tests/test_use_case_integration.py -v -m integration
```

## 📋 Características Principales

### Pipeline de Ingesta
- ✅ Soporte para múltiples formatos (Markdown, TXT, Word, PDF)
- ✅ Detección automática de encoding
- ✅ Limpieza de texto configurable
- ✅ Chunking inteligente con recomendaciones automáticas
- ✅ Embeddings con HuggingFace (configurable)
- ✅ Persistencia en Neo4j con estructura File → Page → Chunk

### Sistema de Patrones
- ✅ Patrones de grafo configurables
- ✅ Patrón predefinido FILE_PAGE_CHUNK
- ✅ Creación de patrones personalizados
- ✅ Validación automática de patrones
- ✅ Generación dinámica de queries Cypher

### Búsqueda Avanzada
- ✅ Búsqueda por texto (full-text search)
- ✅ Búsqueda vectorial (similarity search)
- ✅ Búsqueda híbrida (combinación de ambas)
- ✅ Patrones GraphRAG básicos (Basic Retriever, Parent-Child, Metadata Filtering)
- 🔧 Patrones GraphRAG avanzados (requieren módulos opcionales):
  - Graph-Enhanced Vector Search (ungraph[gds])
  - Local Retriever (ungraph[gds])
  - Community Summary Retriever (ungraph[gds])

### Arquitectura y Calidad
- ✅ Clean Architecture para mantenibilidad
- ✅ Domain-Driven Design
- ✅ Tests con datos reales
- ✅ Documentación completa

## 🔄 Flujo del Sistema

```
1. Cargar archivo        → DocumentLoaderService
2. Limpiar texto         → TextCleaningService
3. Dividir en chunks     → ChunkingService (con recomendaciones)
4. Generar embeddings    → EmbeddingService
5. Configurar índices    → IndexService
6. Persistir en grafo    → ChunkRepository (con patrones configurables)
7. Crear relaciones     → Relaciones NEXT_CHUNK entre chunks consecutivos
```

## 📝 Ejemplo Completo

```python
import ungraph
from pathlib import Path

# 1. Configurar (opcional si usas variables de entorno)
ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_password="tu_contraseña"
)

# 2. Obtener recomendación de chunking
recommendation = ungraph.suggest_chunking_strategy("documento.md")
print(f"Usando estrategia: {recommendation.strategy}")

# 3. Ingerir documento con parámetros recomendados
chunks = ungraph.ingest_document(
    "documento.md",
    chunk_size=recommendation.chunk_size,
    chunk_overlap=recommendation.chunk_overlap
)
print(f"✅ {len(chunks)} chunks creados")

# 4. Buscar información
results = ungraph.hybrid_search(
    "tema de interés",
    limit=5
)

# 5. Procesar resultados con contexto
for result in results:
    contexto_completo = ""
    if result.previous_chunk_content:
        contexto_completo += f"[Anterior] {result.previous_chunk_content}\n\n"
    contexto_completo += f"[Principal] {result.content}\n\n"
    if result.next_chunk_content:
        contexto_completo += f"[Siguiente] {result.next_chunk_content}"
    
    print(contexto_completo)
    print("=" * 80)
```

## 🎓 Conceptos Clave

### Lexical Graphs (Grafos Léxicos)

Ungraph implementa **Lexical Graphs** que organizan texto y capturan relaciones lingüísticas. El patrón por defecto `FILE_PAGE_CHUNK` es un Lexical Graph:

```
File → Page → Chunk
```

Con relaciones:
- `File -[:CONTAINS]-> Page`
- `Page -[:HAS_CHUNK]-> Chunk`
- `Chunk -[:NEXT_CHUNK]-> Chunk` (chunks consecutivos)

**¿Por qué Lexical Graph?**
- Organiza texto estructuralmente para búsqueda semántica
- Compatible con patrones GraphRAG (Basic Retriever, Parent-Child Retriever)
- Facilita búsqueda por similitud vectorial y relaciones estructurales

Ver [Lexical Graphs](docs/concepts/lexical-graphs.md) para más detalles.

### Sistema de Patrones

Ungraph permite definir patrones de grafo configurables para estructurar el conocimiento de diferentes maneras. El patrón `FILE_PAGE_CHUNK` es un Lexical Graph compatible con GraphRAG.

Ver [documentación de patrones](docs/concepts/graph-patterns.md) para más detalles.

### Patrones GraphRAG

Ungraph implementa varios patrones de GraphRAG:
- ✅ **Basic Retriever**: Búsqueda vectorial directa en chunks
- ✅ **Parent-Child Retriever**: Busca en chunks pequeños y recupera contexto completo
- ✅ **Metadata Filtering**: Búsqueda con filtros por metadatos

Ver [Patrones de Búsqueda GraphRAG](docs/api/search-patterns.md) para más detalles.

**Referencias:**
- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
- [GraphRAG Documentation](https://graphrag.com/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)

## 🔗 Enlaces Útiles

- [Documentación Completa](docs/README.md)
- [Guía de Inicio Rápido](docs/guides/quickstart.md)
- [Plan de Patrones de Grafo](_PLAN_PATRONES_GRAFO.md)
- [GraphRAG Documentation](https://graphrag.com/)

## 📄 Licencia

MIT License

## 👤 Autor

Alejandro Giraldo Londoño - alejandro@qnow.tech
