# Gaps: desarrollo, pruebas, consideraciones

Foto alineada al checklist de [`docs/PLAN_MAESTRO.md`](../../../docs/PLAN_MAESTRO.md). Actualizar junto con ese checklist.

## Bloqueantes H_I (prioridad)

| Gap | Desarrollo | Pruebas | Consideración |
|-----|------------|---------|---------------|
| A5 Runner online | **Hecho:** `run_architecture_online` + `--mode online --hi-wave` | `tests/integration/test_hi_wave_online_unit_gate.py` | Neo4j + `ungraph[infer-en]` |
| B2 Probes top-k | **Hecho:** `evaluate_answer_containment_topk` | unit en `test_neo4j_gold_metrics_unit.py` | Nunca corpus completo |
| B3 Recall desde Neo4j | **Hecho:** `neo4j_gold_metrics.py` | unit + integration | Normalización case/espacios |
| B4 evidence_coverage Neo4j | **Hecho:** `fetch_fact_provenance_counts` en online | vía evaluate_gold_against_neo4j | DERIVED_FROM |
| D3 Cerrar H_I | **Hecho (PASS):** `entity_recall` none=0 / ner≈0.47; AC@k estable | `hi_wave_verdict.json` | seed KG; no generalizar aún |
| D4 Capa 0 freeze | **Hecho:** `capa0_artifact.py` + `freeze/reload-capa0`; gate match | `capa0_artifact.json`, `reload_verdict.json` | reload ≠ dump Neo4j |
| D5 Oleada-3 | **Hecho:** `ner` vs `pattern` COMPARED | `family_wave_verdict.json` | LLM opcional (`--families ner,llm`) |
| C5 Doc I/O Infer | **Hecho:** `docs/concepts/inference-slot.md` + nav mkdocs | — | slot ≠ mega-diseño |
| D6 H_chunk/H_T | **Hecho (DoE):** `doe_h_chunk.yaml` + online 7 celdas | `results_h_chunk.csv`, `analysis_h_chunk*.json` | AC débil; latency retiene chunk_size |
| Instrumento probes | **Hecho:** gold localizado + exact≥4 tokens | unit probe | evita saturación AC |
| Cierre loop | **Hecho:** `pipeline_closure.json` | reports/ | seed KG |

## Desarrollo pendiente (orden siguiente)

| Gap | Acción |
|-----|--------|
| E7 commit | `git add` PLAN, suite ETI, `run_domain_pipeline.py`, doe_h_chunk, reports clave, CI |
| 2º dominio / probes más duros | Para afirmar H_chunk en AC (no solo latency) y H_T |
| F5 Complexometrum | Tras Y de tarea más variables |
| Integration H_I en CI | Opcional nightly: Neo4j + spaCy model (pesado) |

## Pruebas recomendadas (matriz)

| Nivel | Qué | Marker / cmd |
|-------|-----|----------------|
| Unit | ExperimentRun↔scorecard↔doe_row; doe_bridge sintético; probe containment | `pytest.mark.unit` (ya) |
| Unit | Mapeo gold→recall puro (sin Neo4j) | nuevo si se extrae lógica pura |
| Integration | wipe + ingest `none` vs `ner` + B2/B3 | `pytest.mark.integration` + Neo4j |
| Smoke DoE | screening seed fijo + analyze | script offline CI sin Neo4j |
| E2E claim | oleada-2 documentada en `reports/` | manual/CI nightly con Neo4j |

## Consideraciones científicas

- No mezclar factores de agente (Capa 2) en oleada H_I.
- Composite_score es secundario; reportar Y desagregadas.
- R²≈1 con N pequeño → no sobreinterpretar p-valores; mirar ranking ET vs ETI y deltas.
- DeepEval (B6) es juez externo opcional; no circular con el crítico del verify.
- Complexometrum (F5) solo tras Y reales; feedback a librería original si el adaptador correlaciona.

## Fuera de foco (Capa 2 / producto amplio)

MCP, report UI, multiagente completo, SPARQL curado, hybrid Infer, recomendación C3, Complexometrum — hasta probes/Y más discriminativos o A10.
