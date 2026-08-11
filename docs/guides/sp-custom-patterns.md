# Patrones de grafo personalizados

Cómo declarar un `GraphPattern` y usarlo en ingesta.  
Audiencia: developer. Concepto (no duplicar): [`../concepts/sp-graph-patterns.md`](../concepts/sp-graph-patterns.md) · léxicos [`../concepts/sp-lexical-graphs.md`](../concepts/sp-lexical-graphs.md).

## Prerrequisitos

1. Neo4j configurado.
2. Familiaridad con el patrón por defecto `FILE_PAGE_CHUNK` (File → Page → Chunk).
3. Imports desde el paquete `ungraph` (no rutas internas sin prefijo).

**Resultado observable:** patrón válido; `ingest_document(..., pattern=...)` materializa según esa declaración (o falla con error de validación/persistencia).

## Qué es un patrón aquí

Contrato de **forma** (labels, propiedades, relaciones) para materializar Transform. No es un motor de Inference ni un patrón de retrieval GraphRAG (esos viven en [`../api/sp-search-patterns.md`](../api/sp-search-patterns.md)).

## Patrón simple (solo Chunk)

```python
from ungraph.domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
)

chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={
        "chunk_id": str,
        "content": str,
    },
    indexes=["chunk_id"],
)

simple_pattern = GraphPattern(
    name="SIMPLE_CHUNK",
    description="Solo chunks, sin estructura File-Page",
    node_definitions=[chunk_node],
    relationship_definitions=[],
)
```

## Patrón con relaciones

```python
from ungraph.domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition,
)

entity_node = NodeDefinition(
    label="Entity",
    required_properties={"name": str, "type": str},
    optional_properties={"description": str},
    indexes=["name", "type"],
)

chunk_node = NodeDefinition(
    label="Chunk",
    required_properties={"chunk_id": str, "content": str},
    indexes=["chunk_id"],
)

mentions_rel = RelationshipDefinition(
    from_node="Chunk",
    to_node="Entity",
    relationship_type="MENTIONS",
    properties={"count": int},
    direction="OUTGOING",
)

lexical_pattern = GraphPattern(
    name="LEXICAL_GRAPH",
    description="Chunks y entidades con MENTIONS",
    node_definitions=[entity_node, chunk_node],
    relationship_definitions=[mentions_rel],
)
```

Declarar `Entity`/`MENTIONS` en el patrón **no** implica que Inference las rellene automáticamente: el slot Infer es independiente ([`../concepts/inference-slot.md`](../concepts/inference-slot.md)).

## Validar y ver Cypher (probe)

```python
from ungraph.infrastructure.services.neo4j_pattern_service import Neo4jPatternService

service = Neo4jPatternService()
ok = service.validate_pattern(simple_pattern)
print("válido:", ok)

cypher = service.generate_cypher(simple_pattern, "create")
print(cypher)
```

## Usar en ingesta (`is`)

```python
import ungraph

chunks = ungraph.ingest_document(
    "doc.md",
    pattern=simple_pattern,
)
print(len(chunks))
```

| | |
|--|--|
| **is** | `ingest_document(..., pattern=GraphPattern)` aceptado en API pública; default = `FILE_PAGE_CHUNK` |
| **will be** | Patrones tipados de *conocimiento* como salida estable de Infer; sugerencia automática de esquema — [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), PRODUCT |

## Reglas de validación (forma)

### Labels de nodos

- Empiezan con mayúscula; letras, números, underscore.
- Válidos: `File`, `Page`, `Chunk`, `Entity`
- Inválidos: `file`, `File-Name`

### Tipos de relación

- Mayúsculas, números, underscore.
- Válidos: `CONTAINS`, `HAS_CHUNK`, `NEXT_CHUNK`, `MENTIONS`
- Inválidos: `contains`, `has-chunk`

### Propiedades

- Nombres = identificadores Python válidos.
- Tipos = tipos Python (`str`, `int`, `list`, …).

## Ejemplo: Document → Section → Paragraph

```python
from ungraph.domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition,
)

document_node = NodeDefinition(
    label="Document",
    required_properties={"doc_id": str, "title": str},
    indexes=["doc_id"],
)
section_node = NodeDefinition(
    label="Section",
    required_properties={"section_id": str, "title": str},
    indexes=["section_id"],
)
paragraph_node = NodeDefinition(
    label="Paragraph",
    required_properties={"para_id": str, "content": str},
    indexes=["para_id"],
)

document_pattern = GraphPattern(
    name="DOCUMENT_SECTION_PARAGRAPH",
    description="Documento → secciones → párrafos",
    node_definitions=[document_node, section_node, paragraph_node],
    relationship_definitions=[
        RelationshipDefinition(
            from_node="Document",
            to_node="Section",
            relationship_type="HAS_SECTION",
        ),
        RelationshipDefinition(
            from_node="Section",
            to_node="Paragraph",
            relationship_type="HAS_PARAGRAPH",
        ),
    ],
)
```

Los patrones de **búsqueda** que asumen File–Page–Chunk pueden no aplicar a topologías distintas; ajusta `parent_label` / `relationship_type` o usa `search` / `hybrid_search` sobre chunks.

## Referencias

- [Patrones de grafo (concepto)](../concepts/sp-graph-patterns.md)
- [API pública](../api/sp-public-api.md)
- [Ingesta](sp-ingestion.md) · [Búsqueda](search.md)
- Catálogo externo de *retrieval* (interfaz): [GraphRAG Pattern Catalog](https://graphrag.com/reference/)
