# GraphRAG como interfaz (no como definición de conocimiento)

**Idioma:** español (canónico `sp-*`).

Audiencia: research / developer. Espina ETI: [`../concepts/eti-spine.md`](../concepts/eti-spine.md). Patrones de uso: [`../guides/search.md`](../guides/search.md), [`../concepts/sp-graph-patterns.md`](../concepts/sp-graph-patterns.md).

## Motivation

GraphRAG mejora la **recuperación** sobre corpora privados al usar estructura de grafo y, a menudo, resúmenes de comunidad (Edge et al. 2024; I04). El riesgo epistémico es redefinir “conocimiento” como *mejor hit@k*. Un sistema puede recuperar bien sin mantener creencias revisables, confianza ni refutación. En Ungraph, GraphRAG es **consumidor** del almacén producido por ETI — Capa 1 (y generación en query-time), no el sustituto de Inference ni de depuración.

## Theory

La literatura distingue spines distintos:

| Spine | Énfasis | Límite para Ungraph |
|-------|---------|---------------------|
| **RAG clásico** | Chunk → embed → retrieve → generate | Transform+Interface; Inference de KG débil o ausente |
| **GraphRAG (Microsoft / surveys)** | Indexación con entidades/comunidades; local/global search (I04, I05; Peng et al.) | Fuerte en Extract+Transform(index); el “razonar” suele ser generación en consulta, no revisión de beliefs |
| **KBC / NELL / DeepDive** | Creencias con confianza, error analysis, never-ending (I01, I02) | Ciclo de depuración que GraphRAG no exige |
| **ETI Ungraph** | Acumular candidatos → proponer/verificar → (will be) depurar → exponer vía retrieval | GraphRAG = Interface sobre el store |

**Lexical graph** (File–Page–Chunk) es representación de Transform para provenance y expansión. **Knowledge graph** (entidades/relaciones tipadas) es salida de Inference. Ambos pueden alimentar patrones GraphRAG; ninguno es “GraphRAG” por sí solo.

Anclas: whitepaper §3.1 (E6–E8), matriz I04–I05. No inventar resultados de benchmark aquí.

### is vs will be

| | |
|--|--|
| **is** | Búsqueda text / vector / hybrid; `search_with_pattern` con patrones basic/parent_child/… según prerequisitos de grafo; evaluación opcional de recuperación; comunidades/GDS **parciales** según extra/entorno |
| **will be** | Community summaries ricos como Transform+Interface medidos E2E; Self-RAG/CoVe como depuración (I06); MCP tools sobre use cases (I24) — sin afirmar EVI en producción |

## In Ungraph

Orden epistémico → interfaz:

1. Materializar Capa 0 (ETI) — ver [`../concepts/eti-spine.md`](../concepts/eti-spine.md).
2. Recuperar (Capa 1) sin redefinir facts anclados.
3. Comparar Y de retrieval **aparte** de Y de Infer ([`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md)).

| Patrón (referencia) | Prerrequisito típico | Estado (honesto) |
|---------------------|----------------------|------------------|
| Basic / vector | `Chunk` + índice vector | Implementado |
| Full-text / híbrido | Índices text + vector | Implementado |
| Parent–child | Jerarquía Page–Chunk | Parcial |
| Metadata / graph-enhanced / local / community | Grafo + (opcional) GDS | Parcial / exploratorio |

Detalle de API y pasos: [`../api/`](../api/sp-public-api.md), [`../guides/search.md`](../guides/search.md). Grafo léxico: [`../concepts/sp-lexical-graphs.md`](../concepts/sp-lexical-graphs.md). Neo4j como store: [`sp-neo4j.md`](sp-neo4j.md).

## Open claims (falseables)

### Claim H_graphrag_interface

- **Enunciado:** Variar solo factores de recuperación (k, text/vector/hybrid/pattern) con artefacto ETI congelado mueve Y de Capa 1 sin alterar la *existencia* de facts anclados de Capa 0.
- **Predicción observable:** Métricas de facts/`evidence_coverage` estables ante swap de retrieval; hit@k o `answer_correctness` @ top-k pueden cambiar.
- **Protocolo mínimo:** Bloquear `capa0_artifact.json`; factorizar solo retrieval; scorecard desagregado. Enlace: Claim H_spine_interface en [`../concepts/eti-spine.md`](../concepts/eti-spine.md), [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md).
- **Falsación:** Si cambiar solo retrieval altera conteos de facts anclados sin re-ingesta, el aislamiento Interface↔ETI está roto.
- **Reproducibilidad:** Filas DoE con factores de retrieval etiquetados.
