---
name: eti-mvp-operativa
description: Define el alcance operativo de un MVP ETI en Ungraph alineado a domain/application/infrastructure, con rutas concretas del paquete y criterios de hecho. Usar cuando planifiques MVP de ingesta, auditorías de readiness, gaps por capa o alineación con Clean Architecture del repo.
---

# MVP ETI operativo (tres capas Ungraph)

Este skill cruza el pipeline **Extract → Transform → Inference** con las tres capas prometidas por la librería. Usa siempre rutas reales bajo `ungraph/` (no `src/` legacy en docs antiguos).

**Plan maestro (A / B / C):** el MVP ETI aquí descrito alinea el **nivel A** (núcleo) y buena parte del **nivel B** (inferencia productiva). El cierre **medible/falsable** (scorecard, DoE, H_I) vive en [`docs/PLAN_MAESTRO.md`](../../../docs/PLAN_MAESTRO.md) § checklist + skill **eti-experiment-science**; oleadas en [`docs/ROADMAP_LEVEL_C.md`](../../../docs/ROADMAP_LEVEL_C.md). MCP/recomendación (C3–C4) no son gate de H_I.

## Mapa de capas ↔ responsabilidad MVP

| Capa | Qué debe quedar listo para MVP | Rutas típicas |
|------|-------------------------------|---------------|
| **Domain** | Contratos estables: entidades, VOs, ABCs de repositorios y servicios; sin Neo4j ni LangChain | `ungraph/domain/entities/`, `value_objects/`, `repositories/`, `services/` |
| **Application** | Orquestación ETI: un caso de uso que componga loader → limpieza → chunking → embeddings → persistencia → inferencia opcional | `ungraph/application/use_cases/`, `ungraph/application/dependencies.py` |
| **Infrastructure** | Implementaciones concretas: Neo4j, LangChain (load/split/embed), spaCy/LLM según extras | `ungraph/infrastructure/repositories/`, `infrastructure/services/` |

**Regla de dependencias:** solo `infrastructure → application → domain`. Cualquier import inverso bloquea MVP hasta corregirse.

## Flujo ETI mínimo viable (definición operativa)

Un MVP cuenta como cerrado cuando, desde **application**, se puede:

1. **Extract**: cargar al menos un tipo de documento soportado por `LangChainDocumentLoaderService` (p. ej. TXT/MD/HTML o PDF según extras).
2. **Transform**: producir `Chunk` vía `ChunkingService` + limpieza acoplada en loader/config.
3. **Persistencia de chunks + vectores**: `ChunkRepository` hacia Neo4j con índices coherentes (ver skill **cypher-craft** / **kg-schema**).
4. **Infer (una ruta)**: spaCy (`SpacyInferenceService`) **o** LLM (`LLMInferenceService` + `LLMGraphTransformer`) sin romper el contrato `InferenceService`.

Documentar en el propio cambio qué ruta de inferencia está en el MVP (local vs remota).

## Neo4j (operativo)

- Instancia accesible (Docker/aura/local) y versión compatible con `neo4j` driver del `pyproject.toml`.
- Grafo vacío reproducible para tests de integración (fixture que limpia con `DETACH DELETE`).
- Queries de ingesta/búsqueda revisadas ante riesgo de full scan (skill **cypher-craft**).

## LangChain (dentro del core Ungraph)

Ungraph ya integra LangChain en **infrastructure** para loaders, splitters, embeddings HF y grafo experimental; el dominio no debe importar `langchain_*`.

Para MVP, verificar tras cada upgrade de dependencias: imports que rompen (`langchain_core`, `langchain_community`, `langchain_experimental`, `langchain_huggingface`, `langchain_neo4j`). Usar skill **ungraph-langstack-ops**.

## LangGraph (alcance MVP)

`langgraph` está declarado en dependencias del proyecto; el **core ETI** no obliga a un grafo LangGraph. El MVP de la **librería** es el pipeline + persistencia; LangGraph entra como capa de **aplicación consumidora** (agentes, steps, HITL) cuando se construye un producto encima de Ungraph.

Si el MVP incluye agente: definir nodos/herramientas que llamen a casos de uso o repositorios ya expuestos, sin meter LangGraph dentro de `domain/`.

## Checklist de salida MVP (copiar y marcar)

```
[ ] Domain: interfaces Inference/Chunking/Embedding/DocumentLoader cubren el flujo usado
[ ] Application: Ingest (o equivalente) inyecta solo ABCs; composition root en dependencies
[ ] Infra: Neo4j repo + al menos un embedding + chunking probados en integración
[ ] Infra: inferencia spaCy o LLM probada; extras documentados (infer-en / infer-es / API keys)
[ ] Tests: unit (sin Neo4j) + integration (Neo4j) para la ruta MVP; ver ungraph-test + eti-operation-curation
[ ] Observabilidad mínima: logs por fase (cantidad chunks, tiempo embed, entidades)
```

## Skills relacionados

- **eti-pipeline**: diagnóstico y extensión por fase.
- **ungraph-langstack-ops**: versiones LangChain/LangGraph/Neo4j y humo de compatibilidad.
- **eti-operation-curación**: matriz de pruebas y curación de operaciones.
- **ungraph-test**: niveles pytest y convenciones.
- **cypher-craft**, **kg-schema**: grafo e índices.
