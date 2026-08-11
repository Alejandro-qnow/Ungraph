# Clean Architecture mapeada a Ungraph / ETI

**Idioma:** español (canónico `sp-*`).

Audiencia: developer / research. Vista de arquitectura de producto: [`../concepts/sp-architecture.md`](../concepts/sp-architecture.md). Espina: [`../concepts/eti-spine.md`](../concepts/eti-spine.md).

## Motivation

Si el dominio importa Neo4j o un LLM concreto, el **contrato de conocimiento candidato** (Chunk, Entity, Fact, `InferenceService`) se vuelve inseparable del adaptador. Entonces no se puede falsar H_I ni comparar familias Infer: cada cambio de motor reescribe “la verdad”. Clean Architecture (Martin; I26) interesa aquí como **protección del slot epistémico**, no como estética de carpetas.

## Theory

Capas concéntricas: el centro define entidades y puertos; el exterior implementa. Traducción Ungraph:

```text
┌─────────────────────────────────────────┐
│ infrastructure  Neo4j, spaCy, HF, loaders│  ← adaptadores
├─────────────────────────────────────────┤
│ application     ingest / search use cases│  ← orquesta E→T→I
├─────────────────────────────────────────┤
│ domain          Chunk, Fact, InferenceService, GraphPattern │
└─────────────────────────────────────────┘
```

| Principio | Lectura ETI |
|-----------|-------------|
| Dependencias hacia adentro | Domain no conoce GraphRAG ni Cypher |
| Puertos / adaptadores | `InferenceService`, `ChunkRepository` = contratos medibles |
| Casos de uso | Orquestan slots; no crean drivers concretos |
| Composition root | Único lugar que cablea infra → application |

Linaje: I26 (*is* en producto). Contrasta con demos que acoplan LLM→Cypher→UI sin puerto de Infer (I20 contrast / I21 borrow con cuidado).

### is vs will be

| | |
|--|--|
| **is** | Separación domain/application/infrastructure; Infer como ABC; factories en application; migración gradual desde `utils/` |
| **will be** | Belief/EVI en domain; menos wrappers legacy; tools MCP como adaptadores de Interface (I24) sin contaminar el centro |

## In Ungraph

- Mapa capas ↔ ETI (sin tutorial largo): [`../concepts/sp-architecture.md`](../concepts/sp-architecture.md)
- Contrato I/O Infer: [`../concepts/inference-slot.md`](../concepts/inference-slot.md)
- Neo4j / GraphRAG como exterior: [`sp-neo4j.md`](sp-neo4j.md), [`sp-graphrag.md`](sp-graphrag.md)
- API estable: [`../api/sp-public-api.md`](../api/sp-public-api.md)

Anti-patrón documental: copiar aquí guías de “cómo ingerir”. Anti-patrón de código: `IngestDocumentUseCase` instanciando `Neo4jChunkRepository` a mano dentro del caso de uso.

## Open claims (falseables)

### Claim H_ca_commensurable_infer

- **Enunciado:** El aislamiento Clean Architecture del slot Infer es condición necesaria para que family-wave (`ner`/`pattern`/…) sea un experimento de familias y no un rewrite de persistencia.
- **Predicción observable:** Misma predicción que H_arch_slot_isolation — swap de implementación de `InferenceService` sin cambio de scorecard ni de Transform.
- **Protocolo mínimo:** Enlace a [`../concepts/sp-architecture.md`](../concepts/sp-architecture.md) Claim H_arch_slot_isolation y family-wave en [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md).
- **Falsación:** Si cada familia nueva exige un repositorio o esquema Neo4j distinto *para el mismo artefacto*, el puerto de dominio no es el contrato real.
- **Reproducibilidad:** Reports family-wave + review de imports en `domain/`.
