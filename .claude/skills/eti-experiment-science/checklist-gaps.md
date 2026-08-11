# Gaps: desarrollo, pruebas, consideraciones

Foto alineada al checklist de [`docs/experiment/PLAN_MAESTRO.md`](../../../docs/experiment/PLAN_MAESTRO.md).  
**PLAN cerrado** en seed + A+B técnico (2026-08-11). Actualizar solo al cerrar un Open claim o al des-diferir C7/F*.

## Cerrado (no reabrir salvo regresión)

Bloqueantes históricos H_I / A5–D6 / E7 / wave1 técnico: **hechos** — ver PLAN checklist A–E y `reports/` del dominio `knowledge_graphs`.

| Gap wave1 | Estado |
|-----------|--------|
| Composition root settings | Hecho |
| CLI E4/E5 humo | Hecho |
| API reasoning | Hecho |
| CI NER smoke | Hecho |
| B6 DeepEval tooling | Hecho (no gate) |
| C3 LLM experimental | Hecho (extras/API key; no gate familia seed) |

## Diferido (explícito — no bloquea cierre del PLAN)

| Ítem | Criterio |
|------|----------|
| C7 hybrid Infer | Hasta Y multi-familia estables; `NotImplementedError` |
| F1–F4 MCP / UI / multiagente / SPARQL | Horizonte C ([`ROADMAP_LEVEL_C.md`](../../../docs/experiment/ROADMAP_LEVEL_C.md)) |
| F5 Complexometrum | Tras Y más variables o ≥2 dominios |
| F6 Reco arquitectura | Tras factores retenidos multi-dominio |

## Ciencia abierta (post-cierre del PLAN)

Diseño maestro: [`docs/experiment/EXPERIMENTAL_DESIGN_MULTICORPUS.md`](../../../docs/experiment/EXPERIMENTAL_DESIGN_MULTICORPUS.md) (packs, D0–D5, $C_k$ por celda).

| Gap | Acción |
|-----|--------|
| `H_probe_calibration` OPEN | Etiquetar probes D0–D5; media AC ET < 0.9 |
| `H_multi_doc_reasoning` OPEN | Pack multicorpus + probes D3+ |
| `H_I_seed_vs_product` OPEN | Pack multi y/o 2º dominio + protocolo comparable |
| `H_chunk_task_Y` OPEN/débil | Solo tras probes calibrados (no seed fácil) |
| `H_bridge_complexity` OPEN condicional | $C_k$ por celda tras M1+M3+M5 del diseño maestro |
| DeepEval como juez-del-gate | Will be; no confundir con B6 tooling |
| Integration H_I nightly | Opcional (pesado); humo NER ya en CI |

## Pruebas recomendadas (matriz)

| Nivel | Qué | Marker / cmd |
|-------|-----|----------------|
| Unit | ExperimentRun↔scorecard↔doe_row; doe_bridge; probe; settings; CLI; deepeval degrade | `pytest.mark.unit` |
| Integration | wipe + ingest `none` vs `ner` + B2/B3; NER smoke | `pytest.mark.integration` + Neo4j |
| Smoke DoE | screening seed fijo + analyze | script offline CI sin Neo4j |
| E2E claim | oleada-2 documentada en `reports/` | manual/CI nightly con Neo4j |

## Consideraciones científicas

- No mezclar factores de agente (Capa 2) en oleada H_I.
- Composite_score es secundario; reportar Y desagregadas.
- R²≈1 con N pequeño → no sobreinterpretar p-valores; mirar ranking ET vs ETI y deltas.
- DeepEval (B6) es juez externo **opcional**; no circular con el crítico del verify; no es gate H_I.
- Complexometrum (F5) solo tras Y reales; feedback a librería original si el adaptador correlaciona.

## Fuera de foco hasta oleada-ciencia o C

MCP, report UI, multiagente completo, SPARQL curado, hybrid Infer, recomendación C3, Complexometrum — ver PLAN § F (DIFERIDO).
