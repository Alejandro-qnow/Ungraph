# Plan de Validación de Queries Cypher - Ungraph

## Objetivo

Validar todos los queries Cypher utilizados en Ungraph para:
1. Detectar bugs y comportamientos inesperados
2. Asegurar que los patrones sigan las especificaciones de GraphRAG
3. Crear datos de prueba que recreen diferentes patrones de grafo
4. Establecer cobertura completa de testing para queries

## Alcance

### Queries a Validar

#### 1. Queries de Ingesta (Creación de Patrones)

**1.1. FILE_PAGE_CHUNK Pattern**
- Ubicación: `src/utils/graph_operations.py::extract_document_structure`
- Query: MERGE de File, Page, Chunk con relaciones CONTAINS y HAS_CHUNK
- Validaciones:
  - ✅ Creación correcta de nodos File, Page, Chunk
  - ✅ Relaciones CONTAINS y HAS_CHUNK correctas
  - ✅ Propiedades requeridas presentes
  - ✅ Propiedades opcionales manejadas correctamente
  - ✅ Timestamps automáticos (createdAt)

**1.2. SEQUENTIAL_CHUNKS Pattern**
- Ubicación: `src/utils/graph_operations.py::create_chunk_relationships`
- Query: Creación de relaciones NEXT_CHUNK entre chunks consecutivos
- Validaciones:
  - ✅ Relaciones NEXT_CHUNK solo entre chunks consecutivos
  - ✅ Orden correcto basado en chunk_id_consecutive
  - ✅ No se crean relaciones duplicadas
  - ✅ Manejo de gaps en secuencia

**1.3. SIMPLE_CHUNK Pattern**
- Patrón: Solo Chunks sin estructura File-Page
- Query: Creación directa de Chunks
- Validaciones:
  - ✅ Chunks creados sin dependencias de File/Page
  - ✅ Propiedades mínimas requeridas
  - ✅ Embeddings y metadatos correctos

**1.4. LEXICAL_GRAPH Pattern**
- Patrón: Grafo léxico con entidades y relaciones semánticas
- Query: Estructura avanzada con entidades y menciones
- Validaciones:
  - ✅ Nodos de entidades creados
  - ✅ Relaciones MENTIONS entre Chunks y Entidades
  - ✅ Propiedades de relaciones (count, etc.)

#### 2. Queries de Búsqueda (GraphRAG Patterns)

**2.1. Basic Retriever**
- Ubicación: `src/infrastructure/services/graphrag_search_patterns.py::basic_retriever`
- Query: Full-text search usando índice chunk_content
- Validaciones:
  - ✅ Índice full-text existe y funciona
  - ✅ Parámetros correctos ($query_text, $limit)
  - ✅ Score de relevancia correcto
  - ✅ Ordenamiento DESC por score
  - ✅ Límite de resultados respetado

**2.2. Metadata Filtering**
- Ubicación: `src/infrastructure/services/graphrag_search_patterns.py::metadata_filtering`
- Query: Full-text search con filtros WHERE
- Validaciones:
  - ✅ Filtros aplicados correctamente
  - ✅ Validación de nombres de propiedades
  - ✅ Combinación de múltiples filtros (AND)
  - ✅ Performance con índices

**2.3. Parent-Child Retriever**
- Ubicación: `src/infrastructure/services/graphrag_search_patterns.py::parent_child_retriever`
- Query: Búsqueda en padre y expansión a hijos
- Validaciones:
  - ✅ OPTIONAL MATCH funciona correctamente
  - ✅ Collect de hijos correcto
  - ✅ Estructura de resultado correcta
  - ✅ Labels y relationship types validados

**2.4. Hybrid Search**
- Ubicación: `src/utils/graph_rags.py::hybrid_search`
- Query: Combinación de full-text y vectorial
- Validaciones:
  - ✅ Búsqueda full-text ejecutada
  - ✅ Búsqueda vectorial ejecutada
  - ✅ Combinación de scores correcta
  - ✅ Contexto NEXT_CHUNK recuperado
  - ✅ Pesos (weights) aplicados correctamente

#### 3. Queries de Configuración

**3.1. Setup de Índices**
- Ubicación: `src/utils/graph_operations.py::setup_advanced_indexes`
- Queries:
  - Vector index: `db.index.vector.createNodeIndex`
  - Full-text index: `CREATE FULLTEXT INDEX`
  - Regular index: `CREATE INDEX`
- Validaciones:
  - ✅ Índices creados correctamente
  - ✅ Manejo de índices existentes
  - ✅ Configuración de índices (dimensiones, analyzer, etc.)

## Estrategia de Testing

### Fase 1: Preparación de Datos de Prueba

Crear queries Cypher que generen datos de prueba para cada patrón:

1. **FILE_PAGE_CHUNK Test Data**
   - Archivo de prueba con múltiples páginas
   - Chunks con embeddings simulados
   - Metadatos completos

2. **SEQUENTIAL_CHUNKS Test Data**
   - Secuencia de chunks consecutivos
   - Validar orden y relaciones

3. **SIMPLE_CHUNK Test Data**
   - Chunks independientes
   - Sin estructura File-Page

4. **LEXICAL_GRAPH Test Data**
   - Entidades y chunks
   - Relaciones MENTIONS

### Fase 2: Validación de Queries

Para cada query:

1. **Validación de Sintaxis**
   - ✅ Query es válido Cypher
   - ✅ Parámetros correctos
   - ✅ No hay inyección Cypher (todos usan parámetros)

2. **Validación de Comportamiento**
   - ✅ Query ejecuta sin errores
   - ✅ Resultados esperados
   - ✅ Performance aceptable

3. **Validación de GraphRAG**
   - ✅ Sigue especificaciones de GraphRAG
   - ✅ Compatible con Lexical Graphs
   - ✅ Soporta patrones de búsqueda requeridos

### Fase 3: Detección de Bugs

1. **Casos Edge**
   - Datos vacíos
   - Valores nulos
   - Propiedades faltantes
   - Relaciones inexistentes

2. **Concurrencia**
   - Múltiples escrituras simultáneas
   - Lecturas durante escrituras

3. **Integridad de Datos**
   - Nodos huérfanos
   - Relaciones rotas
   - Índices desactualizados

## Criterios de Éxito

### Validación Exitosa

- ✅ Todos los queries ejecutan sin errores
- ✅ Resultados coinciden con expectativas
- ✅ Performance dentro de límites aceptables
- ✅ Cumplimiento con especificaciones GraphRAG
- ✅ No se detectan bugs críticos

### Bugs a Reportar

- ❌ Queries que fallan en ejecución
- ❌ Resultados incorrectos o inesperados
- ❌ Problemas de performance
- ❌ Desviaciones de especificaciones GraphRAG
- ❌ Problemas de integridad de datos

## Herramientas

- **MCP Neo4j**: Para ejecutar queries y validar
- **Cypher Query Validator**: Validación de sintaxis
- **Neo4j Browser**: Visualización de resultados
- **Python Scripts**: Automatización de pruebas

## Referencias

- [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [GraphRAG Research Papers](https://graphrag.com/appendices/research/)
- [Ungraph Documentation](../README.md)

