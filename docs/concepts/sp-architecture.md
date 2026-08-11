# Arquitectura Ungraph (capas ↔ ETI)

**Idioma:** español (canónico `sp-*`).

Audiencia: developer / research. Espina epistémica: [`eti-spine.md`](eti-spine.md). Linaje Clean Architecture aplicado a Ungraph: [`../theory/sp-clean-architecture.md`](../theory/sp-clean-architecture.md). How-to: [`../guides/sp-quickstart.md`](../guides/sp-quickstart.md).

## Motivation

Sin una frontera clara entre *qué es conocimiento candidato* y *cómo se persiste o recupera*, el grafo se confunde con el framework. El problema no es solo mantenibilidad de software: es proteger el **contrato epistémico** (unidades de evidencia, representaciones, proposiciones ancladas) frente a Neo4j, LangChain o un motor NER concreto — para poder sustituir implementaciones y seguir midiendo las mismas Y (I26).

## Theory

Clean Architecture (Martin) y DDD sitúan entidades y puertos en el centro; los adaptadores (DB, LLM, buscadores) orbitan. En Ungraph esa regla se lee sobre la espina ETI:

| Capa software | Rol | Encaje ETI |
|---------------|-----|------------|
| **domain** | Entidades (`Chunk`, `Entity`, …), value objects (`GraphPattern`), puertos (`InferenceService`, repositorios) | Contrato de artefactos E/T/I; sin frameworks |
| **application** | Casos de uso (ingesta, búsqueda); orquestación; composition root | Secuencia Extract→Transform→Inference→persist/retrieve |
| **infrastructure** | Neo4j, spaCy/LLM, embeddings, loaders | Adaptadores; **consumidores** del contrato, no dueños del significado |
| **core / utils** | Config compartida; utilidades en migración | Soporte; no redefinir el dominio |

**Regla de dependencias:** `infrastructure` → `application` → `domain`. Nunca `domain` → Neo4j/LangChain.

GraphRAG, MCP e índices Neo4j viven como **Interface** sobre el almacén; no redefinen Inference (ver [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md), [`../theory/sp-neo4j.md`](../theory/sp-neo4j.md)).

### is vs will be

| | |
|--|--|
| **is** | Capas domain/application/infrastructure; slot Infer en dominio; wrappers de infraestructura; evaluación en `ungraph/evaluation/` como sonda experimental |
| **will be** | Objetos Belief/Claim + EVI en dominio; menos lógica en `utils/`; Interface MCP tipada sobre use cases (I24) |

## In Ungraph

Mapa mental (sin tutorial de código):

```text
Extract     → loaders / señales de fuente          (infra → puertos)
Transform   → chunking, embeddings, File–Page–Chunk
Inference   → InferenceService → Entity/Relation/Fact
Interface   → búsqueda / GraphRAG / (MCP will be) sobre Neo4j
```

- Detalle del slot: [`inference-slot.md`](inference-slot.md)
- Patrones y grafo léxico: [`sp-graph-patterns.md`](sp-graph-patterns.md), [`sp-lexical-graphs.md`](sp-lexical-graphs.md)
- Ejemplos de inyección de dependencias y anti-patrones de import: [`../theory/sp-clean-architecture.md`](../theory/sp-clean-architecture.md)
- Contrato público: [`../api/sp-public-api.md`](../api/sp-public-api.md)

Rutas de paquete solo como *probe*; la verdad del claim científico está en scorecards, no en el diagrama de carpetas.

## Open claims (falseables)

### Claim H_arch_slot_isolation

- **Enunciado:** Mantener `InferenceService` (y entidades de artefacto) libres de Neo4j/LangChain en `domain/` permite swap de familia Infer sin reescribir Transform ni el scorecard.
- **Predicción observable:** Family-wave `ner` vs `pattern` sobre la misma recipe Capa 0 cambia Y de capa B sin cambiar código de chunking/embed.
- **Protocolo mínimo:** [`inference-slot.md`](inference-slot.md); [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) (family-wave).
- **Falsación:** Si para cambiar de familia hay que tocar persistencia o el contrato de `Chunk`/scorecard, el aislamiento de capas no sostiene el slot.
- **Reproducibilidad:** Reports family-wave + inspección de dependencias de dominio (tests de arquitectura / review).
