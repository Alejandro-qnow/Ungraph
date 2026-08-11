---
name: eti-operation-curation
description: Curación rigurosa de operaciones ETI: matriz de pruebas por fase y capa, contratos dominio-infra, regresión de Cypher y humo LangChain. Usar cuando se necesite calidad de producción en ingesta, evitar regresiones silenciosas o diseñar suites que validuen el MVP entre Extract, Transform e Inference.
---

# Curación seria de operaciones ETI

Objetivo: cada operación crítica del pipeline tenga **propiedad verificable** (no solo “pasó el test feliz”).

## Matriz mínima (fase × tipo de prueba)

| Fase | Unit (mock en frontera dominio) | Integration (Neo4j real) | Notas |
|------|----------------------------------|---------------------------|--------|
| Extract | Loader + limpieza con documento sintético en memoria | Opcional: archivo fixture pequeño | No llamar red en unit |
| Transform | Chunking: tamaño, overlap, metadatos preservados | Persistir 1–2 chunks y leer con Cypher | Invariantes de `Chunk` |
| Embed | Stub de `EmbeddingService` (vector fijo dimensión conocida) | Verificar dimensión y nodo/relación en índice vectorial si aplica | Misma dimensión que modelo configurado |
| Infer | Mock `InferenceService` o spaCy con modelo mínimo en CI si se acuerda | Grafo contiene entidades/relaciones esperadas de texto fijo | Duplicados: asserts sobre MERGE |
| Orquestación (use case) | Todas las deps inyectadas falsas/reales según nivel | E2E: ingest → query de conteo/patrón | Un escenario “golden” por MVP |

## Contratos dominio ↔ infraestructura

- Tests unitarios fallan si una implementación infra **no cumple** el ABC (métodos faltantes, tipos incompatibles).
- No mockear `neo4j` dentro de dominio; mockear `ChunkRepository`, `InferenceService`, etc.

## Regresión de Cypher

Para cada query de ingesta o búsqueda que toque el MVP:

- Guardar el texto Cypher esperado **o** una query parametrizada con **asserts** sobre: cardinalidad (`COUNT`), propiedades obligatorias, ausencia de nodos huérfanos definidos por el modelo.
- Tras cambios en **kg-schema**, ejecutar suite integration asociada (skill **cypher-craft**).

## Golden paths (recomendado)

- Un documento **golden** (pequeño, estable) con salida esperada: número de chunks, lista ordenada de `entity.type` o tuplas `(source, rel, target)` para inferencia determinista (spaCy favorito para esto).
- Versionar el golden en `tests/fixtures/` cuando el equipo lo acuerde.

## Humo LangChain tras cambio de versión

Acorde con **ungraph-langstack-ops**: un test de import o un unit que construya `LangChainChunkingService` y divida un string corto evita sorpresas en CI.

## Marcadores pytest

Alinear con `pytest.ini`: `unit`, `integration`, `e2e`. No mezclar Neo4j en tests marcados solo como unit.

## Entrega al cerrar una operación nueva

1. Qué invariante de negocio protege el test
2. Nivel (unit/integration/e2e) y justificación
3. Si afecta Neo4j: script o fixture de limpieza
4. Si usa LLM: cómo se aísla (mock, grabación, o marcador `slow`/opcional)

Para convenciones generales de tests, ver **ungraph-test**.
