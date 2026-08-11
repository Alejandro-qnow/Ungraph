# Resumen de validación — probes Cypher (histórico)

**Idioma:** español (canónico `sp-*`).

## Estado (is / no PRODUCT §5)

| | |
|--|--|
| **is** | Nota histórica de **smoke / probe MCP Neo4j** sobre sintaxis e integridad de patrones léxicos y queries GraphRAG de ejemplo. No es un `ExperimentRun` ni scorecard versionado del programa ETI. |
| **No afirma** | Capacidad de producto “validada” ni gate H_I / DoE. Criterio de cuándo algo cuenta como validado: [`../product/PRODUCT.md`](../product/PRODUCT.md) §5. Protocolo medible: [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md). |

Fecha de la corrida original: ~2025-01 (MCP Neo4j). Conservar como rastro de ingeniería; no re-leer como medición científica.

---

## Qué se ejercitó (probe)

### Datos de prueba

| Tipo | Cantidad (aprox.) |
|------|-------------------|
| Files | 1 |
| Pages | 2 |
| Chunks | 5 |
| Entities | 2 |
| Relaciones (CONTAINS, HAS_CHUNK, NEXT_CHUNK, MENTIONS) | ~9 |

### Patrones / queries tocados

- Formas: `FILE_PAGE_CHUNK`, secuencia `NEXT_CHUNK`, `SIMPLE_CHUNK`, menciones tipo léxico+entity.
- Retrieval de ejemplo: Basic Retriever (full-text), Metadata Filtering, Parent-Child (sintaxis / OPTIONAL MATCH).
- Índices: full-text `chunk_content` operativo en esa corrida; índice vectorial **pendiente** (Neo4j 5.x+ / plugin) — Hybrid limitado.

Detalle de scores y checklists de la corrida vive en el historial git de este archivo si hace falta auditoría forense; **no** promocionar aquí a “100% validado”.

---

## Dónde medir de verdad

1. Hipótesis y DoE → [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`../experiment/BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md)
2. Criterio “validado” → [`../product/PRODUCT.md`](../product/PRODUCT.md) §5
3. Semántica léxico vs conocimiento → [`../concepts/sp-lexical-graphs.md`](../concepts/sp-lexical-graphs.md), [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md)

### Referencias de código (probe)

- Ingesta / estructura: `src/utils/graph_operations.py`
- Búsqueda: `src/infrastructure/services/neo4j_search_service.py`
- Índices: `src/infrastructure/services/index_service.py`
