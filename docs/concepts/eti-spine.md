# Espina ETI (Extract → Transform → Inference)

**Idioma:** español. Archivo canónico compartido (sin prefijo `sp-`).

Audiencia: research / developer que necesita el *porqué* epistémico del marco, no el contrato de API.

## Motivation

Minerar conocimiento desde texto no es “indexar mejor”. Un índice recuperable puede devolver fragmentos útiles sin sostener **creencias** con evidencia, confianza ni criterio de refutación. El problema epistémico es acumular candidatos (incluidos espurios), representarlos de forma usable, y **proponer o validar** estructura que el texto no entrega ya hecha — luego depurar.

ETL clásico termina en *Load* (persistir). Para una librería de ingeniería de conocimiento, persistir no basta: hace falta un estadio que *cree y revise* creencias. Por eso Ungraph organiza el trabajo como **Extract → Transform → Inference (ETI)** — una *espina*, no un pipeline fijo ni un sinónimo de GraphRAG.

GraphRAG, búsqueda y MCP son **consumidores** del almacén epistémico (capa de interfaz), no la definición de “conocer”.

## Theory

### Tres fases con roles distintos

| Fase | Rol epistémico | No es |
|------|----------------|-------|
| **Extract** | Adquirir unidades de evidencia desde fuentes (texto, layout, señales multimodales) | Un único parser ni “todo lo que parece IE” |
| **Transform** | Normalizar a representaciones reutilizables (limpieza, chunks, embeddings, topología léxica) | Solo featurización opaca hacia un modelo |
| **Inference** | Proponer y/o verificar conocimiento estructurado (entidades, hechos, hipótesis, consecuencias, refinamiento) | Un solo motor NER/LLM ni *Load* de ETL |

La literatura reinventa esta tríada con otros nombres. En DeepDive, la evidencia/features alimenta inferencia probabilística hacia creencias calibradas (Shin et al. / línea DeepDive; whitepaper E1). NELL mantiene creencias con confianza en un ciclo nunca-ending (I01, E18). GraphRAG enfatiza Extract+Transform(index) y deja gran parte del “razonar” en query-time (Edge et al. 2024; I04) — útil como interfaz, insuficiente como ciclo de creencias revisables.

**Síntesis (RQ1 del whitepaper):** ETI sigue siendo un principio organizador moderno *si* Inference no se reduce a una llamada `extract_entities`, y si se admite un bucle de **depuración** (confianza, provenance, promoción bronze→gold) como continuo, no one-shot.

### Capas experimentales (no un megafactorial)

```text
Capa 0 — Artefacto ETI     chunking, embed, infer, grafo
Capa 1 — Recuperación      text / vector / hybrid, k
Capa 2 — Razonadores       LLM / agente / verify (solo tras gate de Capa 0)
```

Las Y discriminativas miden calidad sobre artefactos y top-k recuperado; no sustituyen el contrato de cada slot. Ver [`PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md).

### is vs will be (espina)

| | |
|--|--|
| **is** | Pipeline modular E→T→I en `main`; slot Infer documentado; scorecard E/T/I + DoE; H_I cerrado en seed `knowledge_graphs`; familias `ner`/`pattern` comparables; GraphRAG como recuperación |
| **will be** | Creencias first-class tipo NELL; depuración EVI/Dung; Inference neurosimbólica y multiagente como oleadas Capa 2; puente Complexometrum para complejidad no estructurada |

## In Ungraph

- **Argumento E/T/I por fase:** [`extraction.md`](extraction.md) · [`transformation.md`](transformation.md) · [`inference.md`](inference.md)
- **Contrato I/O del slot Infer** (no duplicar aquí): [`inference-slot.md`](inference-slot.md)
- **Intro / arquitectura (capas ↔ ETI):** [`sp-introduction.md`](sp-introduction.md) · [`sp-architecture.md`](sp-architecture.md)
- **Linaje (consumidores, no espina):** [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md) · [`../theory/sp-neo4j.md`](../theory/sp-neo4j.md) · [`../theory/sp-clean-architecture.md`](../theory/sp-clean-architecture.md)
- **Linaje y matriz:** [`../research/WHITEPAPER_UNGRAPH_IMRAD.md`](../research/WHITEPAPER_UNGRAPH_IMRAD.md), [`../research/INSPIRATION_MATRIX.md`](../research/INSPIRATION_MATRIX.md)
- **Programa medible:** [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`../experiment/BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md), skill `eti-experiment-science`
- **Curación documental:** [`../research/CURATION_CHECKLIST.md`](../research/CURATION_CHECKLIST.md)

Rutas de código solo como *probe*: `InferenceService` en dominio; orquestación de ingesta; `ungraph/evaluation/` (ExperimentRun, DomainScorecard, doe_bridge).

Orden de lectura epistémico → justificativo → falseable → medido:

1. Esta página (espina)
2. Extracción / Transformación / Inferencia (argumento por fase)
3. Open claims + plan/benchmark (protocolo)
4. Scorecards / reports versionados (evidencia)

## Open claims (falseables)

### Claim H_spine_ETI

- **Enunciado:** Organizar el pipeline como ETI (con Inference ≠ Load) produce artefactos Capa 0 medibles que discriminan ET vs ETI bajo Transform fijo.
- **Predicción observable:** Con recipe Capa 0 congelada, `inference=ner` supera `inference=none` en recall de grafo anclado y no colapsa probe-QA @ top-k (gate H_I).
- **Protocolo mínimo:** Dominio P0 `benchmarks/domains/knowledge_graphs/`; wipe; runner online; veredicto H_I. Detalle: [`PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md).
- **Falsación:** Si, con Transform fijo y corrida válida, `ner` no mejora recall anclado frente a `none`, o las Y de tarea colapsan de forma no interpretable, el claim de espina “Inference aporta conocimiento” queda rechazado o acotado a ese seed.
- **Reproducibilidad:** `ExperimentRun` + scorecard + artefacto `hi_wave_verdict.json` / reports bajo el runner DoE.

### Claim H_spine_interface

- **Enunciado:** Tratar GraphRAG/MCP como Interface (Capa 1+) no como definición de conocimiento evita confundir hit@k con depuración de creencias.
- **Predicción observable:** Oleadas que solo varían recuperación (k, modo text/vector/hybrid) mueven Y de Capa 1 sin alterar el veredicto de Capa 0 si el artefacto ETI está congelado.
- **Protocolo mínimo:** Bloquear Capa 0 (`capa0_artifact.json`); factorizar solo retrieval; comparar Y top-k. Oleada: plan maestro / benchmark.
- **Falsación:** Si cambiar solo retrieval altera métricas de *existencia* de facts anclados (Capa 0) sin re-ingesta, el aislamiento de capas está roto.
- **Reproducibilidad:** Filas DoE con factores de retrieval etiquetados; scorecard desagregado E/T/I vs tarea.
