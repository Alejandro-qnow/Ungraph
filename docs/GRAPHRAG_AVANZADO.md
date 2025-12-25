# GraphRAG Avanzado: ¿Qué es y Cómo Mejorar las Inferencias?

## ¿Qué significa "Avanzado" en GraphRAG?

Según la revisión crítica, tu implementación actual es **básica pero correcta**. Esto es bueno para una primera versión, pero para ser "avanzado" necesitas implementar patrones que van más allá de la búsqueda simple.

### Niveles de GraphRAG

#### 🔵 Básico (Lo que tienes ahora)
- **Basic Retriever**: Búsqueda vectorial simple en chunks
- **Parent-Child Retriever**: Búsqueda jerárquica básica
- **Metadata Filtering**: Filtros por propiedades
- **Hybrid Search**: Combinación texto + vectorial

**Limitación**: Solo busca en chunks directamente, no aprovecha relaciones complejas del grafo.

#### 🟢 Intermedio (Próximo paso)
- **Graph-Enhanced Vector Search**: Usa entidades y relaciones para enriquecer búsqueda
- **Local Retriever**: Búsqueda en subgrafos relacionados
- **Hypothetical Question Retriever**: Genera preguntas hipotéticas para mejorar matching

**Mejora**: Aprovecha la estructura del grafo para encontrar contexto relacionado.

#### 🔴 Avanzado (Futuro)
- **Community Summary Retriever**: Detecta comunidades y genera resúmenes
- **Global Community Summary**: Resúmenes a nivel de todo el grafo
- **Dynamic Cypher Generation**: Genera queries Cypher dinámicamente con LLM
- **Text2Cypher**: Convierte preguntas naturales en queries Cypher

**Mejora**: Entiende el contexto global del conocimiento y genera respuestas más completas.

---

## ¿Qué técnicas mejorarían las inferencias?

Basado en la investigación de GraphRAG y tu objetivo de mejorar las inferencias, aquí están las técnicas más prometedoras:

### 1. Graph-Enhanced Vector Search ⭐ RECOMENDADO

**¿Qué es?**
Combina búsqueda vectorial con traversal del grafo para encontrar contexto relacionado que no está directamente en los chunks encontrados.

**Cómo funciona**:
1. Busca chunks similares usando embeddings (como Basic Retriever)
2. Extrae entidades mencionadas en esos chunks
3. Hace traversal del grafo desde esas entidades para encontrar chunks relacionados
4. Retorna contexto enriquecido

**Por qué mejora inferencias**:
- Encuentra información relacionada que no está en el chunk original
- Conecta conceptos a través de entidades
- Proporciona contexto más completo para el LLM

**Requisitos**:
- Extracción de entidades (NER) en los chunks
- Relaciones entre entidades en el grafo
- Traversal de grafo en Cypher

**Ejemplo de query**:
```cypher
// 1. Buscar chunks similares
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $query_vector)
YIELD node as chunk, score

// 2. Extraer entidades mencionadas
MATCH (chunk)-[:MENTIONS]->(entity:Entity)

// 3. Encontrar chunks relacionados a través de entidades
MATCH path=(entity)-[:RELATED_TO*1..2]-(related_entity)
MATCH (related_entity)<-[:MENTIONS]-(related_chunk:Chunk)

RETURN chunk, related_chunk, path
ORDER BY score DESC
```

### 2. Community Summary Retriever

**¿Qué es?**
Detecta comunidades de nodos relacionados y genera resúmenes de cada comunidad usando un LLM.

**Cómo funciona**:
1. Detecta comunidades en el grafo (algoritmos como Louvain)
2. Para cada comunidad, extrae todos los chunks relacionados
3. Genera un resumen de la comunidad usando un LLM
4. Busca en los resúmenes en lugar de chunks individuales

**Por qué mejora inferencias**:
- Encuentra temas relacionados aunque estén en diferentes chunks
- Resúmenes capturan el contexto completo de un tema
- Reduce ruido al buscar en resúmenes en lugar de muchos chunks

**Requisitos**:
- Algoritmo de detección de comunidades (Neo4j GDS)
- LLM para generar resúmenes
- Almacenamiento de resúmenes en el grafo

### 3. Hypothetical Question Retriever

**¿Qué es?**
Genera preguntas hipotéticas para cada chunk usando un LLM, luego busca en esas preguntas en lugar del contenido original.

**Cómo funciona**:
1. Para cada chunk, genera preguntas que el chunk podría responder
2. Embed las preguntas generadas
3. Cuando el usuario pregunta, busca similitud en las preguntas generadas
4. Retorna los chunks correspondientes

**Por qué mejora inferencias**:
- Mejora el matching entre pregunta del usuario y contenido
- Las preguntas generadas capturan mejor la intención que el texto crudo
- Útil cuando la similitud directa es baja

**Requisitos**:
- LLM para generar preguntas (una vez por chunk, no en tiempo real)
- Almacenamiento de preguntas generadas
- Embeddings de preguntas

### 4. Entity Extraction y Relationship Extraction

**¿Qué es?**
Extrae entidades (personas, lugares, conceptos) y relaciones entre ellas de los chunks usando un LLM o NER.

**Cómo funciona**:
1. Procesa cada chunk con un LLM o modelo NER
2. Extrae entidades mencionadas (Person, Location, Concept, etc.)
3. Extrae relaciones entre entidades
4. Crea nodos Entity y relaciones en el grafo

**Por qué mejora inferencias**:
- Permite Graph-Enhanced Vector Search
- Conecta chunks a través de entidades compartidas
- Facilita búsqueda por entidades específicas

**Requisitos**:
- LLM o modelo NER (spaCy, transformers)
- Pipeline de extracción (puede ser costoso computacionalmente)
- Esquema de entidades y relaciones

---

## Recomendación para Ungraph

### Fase 1: Mejoras Inmediatas (Release v0.2)

1. **Graph-Enhanced Vector Search básico**
   - Implementar extracción de entidades básica (NER con spaCy o transformers)
   - Crear relaciones MENTIONS entre Chunks y Entities
   - Implementar traversal básico en búsqueda

2. **Mejorar Parent-Child Retriever**
   - Actualmente busca en Page, pero podría buscar en Chunks pequeños y expandir
   - Agregar opción de incluir chunks hermanos

### Fase 2: Mejoras Intermedias (Release v0.3)

3. **Local Retriever**
   - Búsqueda en subgrafos relacionados
   - Útil para encontrar contexto relacionado

4. **Hypothetical Question Retriever**
   - Generar preguntas durante la ingesta (no en tiempo real)
   - Almacenar preguntas en metadatos del chunk

### Fase 3: Mejoras Avanzadas (Release v0.4+)

5. **Community Summary Retriever**
   - Requiere Neo4j GDS para detección de comunidades
   - Generación de resúmenes con LLM

6. **Dynamic Cypher Generation**
   - Usar LLM para generar queries Cypher dinámicamente
   - Útil para preguntas complejas que requieren múltiples pasos

---

## Implementación Práctica: Graph-Enhanced Vector Search

### Paso 1: Extracción de Entidades

```python
# Durante la ingesta, después de crear chunks
from spacy import load as spacy_load

nlp = spacy_load("es_core_news_sm")  # o "en_core_web_sm"

def extract_entities(chunk: Chunk) -> List[Entity]:
    """Extrae entidades de un chunk usando spaCy."""
    doc = nlp(chunk.page_content)
    entities = []
    
    for ent in doc.ents:
        entities.append(Entity(
            text=ent.text,
            label=ent.label_,  # PERSON, ORG, LOC, etc.
            start_char=ent.start_char,
            end_char=ent.end_char
        ))
    
    return entities
```

### Paso 2: Crear Nodos Entity en Neo4j

```cypher
// Crear nodo Entity si no existe
MERGE (e:Entity {text: $entity_text, label: $entity_label})

// Crear relación MENTIONS entre Chunk y Entity
MATCH (c:Chunk {chunk_id: $chunk_id})
MATCH (e:Entity {text: $entity_text})
MERGE (c)-[:MENTIONS]->(e)
```

### Paso 3: Query Graph-Enhanced

```cypher
// 1. Búsqueda vectorial inicial
CALL db.index.vector.queryNodes('chunk_embeddings', 5, $query_vector)
YIELD node as initial_chunk, score as initial_score

// 2. Encontrar entidades mencionadas
MATCH (initial_chunk)-[:MENTIONS]->(entity:Entity)

// 3. Encontrar otros chunks que mencionan las mismas entidades
MATCH (entity)<-[:MENTIONS]-(related_chunk:Chunk)
WHERE related_chunk <> initial_chunk

// 4. Retornar chunks iniciales y relacionados
RETURN DISTINCT {
    chunk: initial_chunk,
    score: initial_score,
    related_chunks: collect(DISTINCT related_chunk)
} as result
ORDER BY initial_score DESC
```

---

## Conclusión

Para mejorar las inferencias en Ungraph, la técnica más prometedora es **Graph-Enhanced Vector Search** porque:

1. ✅ Aprovecha la estructura del grafo que ya tienes
2. ✅ No requiere cambios arquitectónicos grandes
3. ✅ Mejora significativamente el contexto recuperado
4. ✅ Es el siguiente paso natural después de Basic Retriever

**Próximos pasos recomendados**:
1. Implementar extracción de entidades durante la ingesta
2. Crear relaciones MENTIONS en el grafo
3. Implementar Graph-Enhanced Vector Search como nuevo patrón de búsqueda
4. Documentar y validar con datos reales

---

**Referencias**:
- [Graph-Enhanced Vector Search](https://graphrag.com/reference/graphrag/graph-enhanced-vector-search/)
- [Community Summary Retriever](https://graphrag.com/reference/graphrag/global-community-summary-retriever/)
- [Hypothetical Question Retriever](https://graphrag.com/reference/graphrag/hypothetical-question-retriever/)

