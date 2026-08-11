# Plan maestro de ejecución (Ungraph)

**Capa ZEN:** `experiment/` — índice ejecutable del programa medible (hipótesis → gates → scorecards / `ExperimentRun`).  
**Audiencia:** research + developer.  
**Última revisión:** 2026-08-11  
**Paquete:** `ungraph` ([`pyproject.toml`](../../pyproject.toml))

No sustituye teoría ([`../concepts/eti-spine.md`](../concepts/eti-spine.md), [`../research/WHITEPAPER_UNGRAPH_IMRAD.md`](../research/WHITEPAPER_UNGRAPH_IMRAD.md)), ni el criterio de producto “validado” ([`../product/PRODUCT.md`](../product/PRODUCT.md) §5), ni resultados ya promovidos a [`../validation/`](../validation/).

| | |
|--|--|
| **is** | Contrato de corrida (`ExperimentRun` + `DomainScorecard` + bridge doekit); runner offline/online; dogfood P0 `knowledge_graphs` con corpus/gold/reports; gates seed documentados abajo; slot Infer `ner` / `pattern` / `llm` (`hybrid` no implementado); CI `eti-measurable`. |
| **will be** | 2º dominio con Y discriminativas; DeepEval como juez estable; puente Complexometrum; `inference_mode=hybrid`; promoción de scorecards a `validation/` solo si cumplen PRODUCT §5. |
| **Open claims** | Ver § Open claims. Gate PASS en seed ≠ “validado” de producto. |

---

## Jerarquía de documentos (docs-first)

| Documento | Rol |
|-----------|-----|
| [`../product/PRODUCT.md`](../product/PRODUCT.md) | Qué es Ungraph; §5 cuándo cuenta como validado. |
| [`../product/VISION_AND_TUTORIALS.md`](../product/VISION_AND_TUTORIALS.md) | Visión §3 A/B/C; §8 ciclo construir–evaluar–refinar. |
| [`../concepts/eti-spine.md`](../concepts/eti-spine.md) | Espina ETI (fundamento). |
| [`../concepts/inference-slot.md`](../concepts/inference-slot.md) | Contrato I/O del slot Infer. |
| [`../research/WHITEPAPER_UNGRAPH_IMRAD.md`](../research/WHITEPAPER_UNGRAPH_IMRAD.md) | Linaje IMRaD / claims teóricos. |
| [`../research/INSPIRATION_MATRIX.md`](../research/INSPIRATION_MATRIX.md) | IDs `Ixx`. |
| [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md) | Scorecard E2E, DoE (`doekit`), cómo ejecutar. |
| [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) | Horizonte C (fuera del cierre A+B). |
| [`sp-data-quality-graph-plan.md`](sp-data-quality-graph-plan.md) | Plan DQ `dq_*` (will be / nivel C). |
| [`../validation/sp-validation_summary.md`](../validation/sp-validation_summary.md) | Probe Cypher histórico — **no** §5. |
| [`../api/sp-configuration.md`](../api/sp-configuration.md) | `inference_mode` contrato API. |
| [`../ops/DEVELOPMENT_WORKFLOW.md`](../ops/DEVELOPMENT_WORKFLOW.md) | Ramas, commits, issues. |
| [`../archive/CHECKPOINT_INFERENCE_PIPELINE.md`](../archive/CHECKPOINT_INFERENCE_PIPELINE.md) | Checkpoint histórico Infer. |

Punteros fuera de `docs/` (skills, `article/`, `project/`) no sustituyen esta jerarquía; ver skills en § Skills.

---

## PRODUCT §5 vs gates en seed

**Probe / gate seed** (esta carpeta + `benchmarks/domains/…/reports/`): protocolo corrido, artefactos versionados, hipótesis falsables.

**Validado (PRODUCT §5):** confrontar fuentes externas/similares; razonar sin sesgo de confirmación; leer tendencias/patrones/variaciones; modelar correctamente lo medido. Hasta entonces **no** vender capacidad como “validada”.

Los veredictos H_I / family-wave / H_chunk en el dominio P0 son **evidencia de seed (dogfood)** — útiles para ingeniería y para acotar claims — no promoción automática a `validation/` ni a promesa B.

---

## Visión técnico-científica (qué queremos probar)

### ETI como contrato modular (no como un motor fijo)

Extract → Transform → Inference son **módulos sustituibles**. Lo estable es el **I/O esperado** (representaciones + hechos anclados + trazas), no el mecanismo interno. Fundamento: [`../concepts/eti-spine.md`](../concepts/eti-spine.md).

**Abstraer Infer ≠ generalizar el diseño de inferir.** spaCy/NER es *una* familia. El slot (`InferenceService` / artefacto de salida) hace familias enchufables y **comparables** bajo las mismas Y. Contrato: [`../concepts/inference-slot.md`](../concepts/inference-slot.md).

### `inference_mode` (alineado a API tanda A)

| Valor | Familia (aprox.) | Estado |
|-------|------------------|--------|
| `none` | baseline ET (sin Infer) | **is** en runner H_I (`inference_service=None`) |
| `ner` | Transductiva spaCy | **is** (default settings) |
| `pattern` | Simbólica / léxica | **is** |
| `llm` | Neural (OpenAI-compatible) | **is** experimental (extras) |
| `hybrid` | NER↔LLM | **will be** — `NotImplementedError` |

Fuente contrato: [`../api/sp-configuration.md`](../api/sp-configuration.md). Factor DoE `inference` / `pattern` RAG no confundir con `GraphPattern` de ingesta.

Familias (taxonomía viva; no normativa): simbólica, transductiva, neural/LLM, híbrida, GraphRAG/topológica, multiagente. Internos (tokens, hops, temperatura) = **covariables**, no el veredicto.

- **Capa A — Contrato ETI:** ¿cada etapa produjo un artefacto medible?  
- **Capa B — Calidad de razonamiento / tarea:** ¿qué tan bien resolvió claims/preguntas?  
- **Covariables:** coste, pasos, ventana — para explicar, no para mover la portería.

### Capas del espacio experimental

```text
Capa 0 — Artefacto ETI     chunking, embed, infer, grafo
Capa 1 — Recuperación      text / vector / hybrid, k
Capa 2 — Razonador         LLM / agente / verify weights   ← solo si Capa 0 pasó gate
```

Prohibido mezclar factores de agente (Capa 2) en la oleada que cierra H_I.

### Complexometrum ↔ Ungraph

**Complexometrum** mide $C(D)$ sobre datos tabulares. El puente a información no estructurada (documento → chunks → embeddings → grafo → facts) es **will be** / Open claim: Ungraph como banco de prueba de proxies de complejidad vs Y del scorecard. No orquesta ETI ni sustituye `DomainScorecard`. Orden: Y discriminativas + H_I seed antes de invertir en el puente. Detalle de fases: skill `eti-experiment-science`.

---

## Gates experimentales → scorecards / ExperimentRun

| Gate | Pregunta | Criterio (P0 `knowledge_graphs`) | Artefacto / métrica |
|------|----------|----------------------------------|---------------------|
| **Corrida válida** | ¿El scorecard E2E es interpretable? | Y no vacías en E, T, I/tarea, eff; E+T no rotos; si Infer≠none → facts anclados (`evidence_coverage`>0) | `DomainScorecard` / `ExperimentRun` |
| **H_I** | ¿Infer aporta frente a solo ET? | Transform fijo; Neo4j+spaCy; `ner` > `none` en recall de grafo **y** probe-QA @ top-k no colapsa | [`hi_wave_verdict.json`](../../benchmarks/domains/knowledge_graphs/reports/hi_wave_verdict.json) |
| **Familias Infer** | ¿≥2 familias comparables bajo mismas Y? | Mismo artefacto Capa 0; swap solo `inference` | [`family_wave_verdict.json`](../../benchmarks/domains/knowledge_graphs/reports/family_wave_verdict.json) |
| **H_chunk / H_T** | ¿Chunking/transform mueven Y de tarea? | DoE `doe_h_chunk.yaml`; analyze sobre Y registradas | [`pipeline_closure.json`](../../benchmarks/domains/knowledge_graphs/reports/pipeline_closure.json) |
| **Razonadores (después)** | ¿Qué motor Infer/Task es mejor? | Mismo snapshot; Y capa B; coste aparte | Capa 2 — ver ROADMAP C |

Operativa DoE: [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md). Horizonte C: [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md).

### Hipótesis en juego (pre-registro vivo)

| Id | Claim | Estado en seed P0 | Lectura PRODUCT §5 |
|----|-------|-------------------|--------------------|
| **H_I** | Infer (`ner`) > ET (`none`) en grafo anclado + tarea, Transform fijo | Gate **PASS** (`entity_recall` 0→~0.47; AC@k no colapsa) — ver `hi_wave_verdict.json` | Seed dogfood; **no** “validado” externo |
| **H_chunk** | Estrategia/tamaño de chunk mejora retrieval a igual presupuesto | **Medido débil en AC**; `chunk_size` retenido en latency (ver `analysis_h_chunk*.json`) | No inflar a causalidad de tarea |
| **H_T** | Proxies de transform predicen QA aguas abajo | **No afirmable** en seed (entity_recall plano con Infer fijo) | Claim acotado / rechazado en este corpus |
| Razonadores | Familias det/no-det comparables vía Y capa B | Oleada-3 `ner` vs `pattern` COMPARED | Extender a LLM/multiagente = will be |

No se citan aquí p-values sueltos: los efectos retenidos viven en los JSON de `reports/` generados por doekit analyze.

---

## Cierre MVP medible (loop único) — foto seed

Ungraph debe habilitar experimentos **reproducibles, falsables y parametrizables** (`GraphPattern` + chunking × inference × rag × verify).

1. **Contrato de corrida** — `ExperimentRun` + `DomainScorecard` + fila DoE (`ungraph/evaluation/`).  
2. **DoE con doekit** — extra `ungraph[experiments]`; `recommend/screening → run → analyze → propose`.  
3. **Dogfood P0** — [`benchmarks/domains/knowledge_graphs/`](../../benchmarks/domains/knowledge_graphs/).  
4. **Oleadas 1–3 + H_chunk** — hechos en seed; veredictos en `reports/`.  
5. **Capa 0 congelada** — `capa0_artifact.json` + reload wipe→re-ingest.  
6. **Siguiente (ops / ampliación)** — commit/PR del paquete medible si aplica; 2º dominio o probes más duros; F5 Complexometrum si Y de tarea varían más. **No** es horizonte C (recomendación/MCP/DQ avanzada).

---

## Checklist de estado (qué tenemos / qué no)

Leyenda: **[x]** listo · **[~]** parcial / offline / experimental · **[ ]** no listo.  
Fecha de foto: **2026-08-11**.

### A. Instrumentación medible (MVP loop)

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| A1 | `ExperimentRun` + `DomainScorecard` + `to_doe_row` | [x] | `ungraph/evaluation/experiment_run.py`, `scorecard.py` |
| A2 | Extra `ungraph[experiments]` + `doekit` | [x] | `pyproject.toml` → `experiments` |
| A3 | Bridge DoE (`recommend/screening/analyze/propose`) | [x] | `doe_bridge.py` |
| A4 | Runner `scripts/run_domain_pipeline.py` | [x] | modo `--offline` usable |
| A5 | Runner **online** Neo4j + spaCy (wipe, ingest, infer, eval) | [x] | `run_architecture_online` + `--mode online --hi-wave` |
| A6 | Dogfood P0 `knowledge_graphs` (manifest, gold, doe.yaml, corpus) | [x] | `benchmarks/domains/knowledge_graphs/` |
| A7 | Oleada-1 screening offline + reports | [x] | `reports/design.json`, `results.csv`, `analysis.json` |
| A8 | `py.typed` | [x] | `ungraph/py.typed` |
| A9 | Tests unitarios contrato/DoE/probe/scorecard | [x] | `tests/unit/test_*doe*`, `test_probe_*`, `test_scorecard_*` |
| A10 | Suite ETI/topología/e2e **versionada y en CI** | [x] | job CI `eti-measurable` |

### B. Y discriminativas (calidad de medición)

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| B1 | Probe-QA / containment offline | [x] | `probe_qa_eval.py` (sobre corpus → poco discriminativo) |
| B2 | Probe-QA / hit@k sobre **top-k recuperado** | [x] | `evaluate_answer_containment_topk` + SearchService |
| B3 | `entity_recall` / `relation_pair_recall` **desde Neo4j** | [x] | `neo4j_gold_metrics.py` |
| B4 | `evidence_coverage` desde provenance / `DERIVED_FROM` | [x] | cableado en runner online |
| B5 | Latency por fase en scorecard | [x] | `efficiency.latency_*` |
| B6 | DeepEval como juez externo (anti-circularidad) | [~] | extra `ungraph[eval]`; no es gate de H_I |

### C. Contrato Infer (slot, no mega-diseño)

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| C1 | ABC `InferenceService` | [x] | `domain/services/inference_service.py` |
| C2 | Instancia spaCy (`ner`) | [x] | `spacy_inference_service.py` |
| C2b | Instancia léxica (`pattern`) | [x] | `lexical_pattern_inference_service.py` |
| C3 | Instancia LLM (experimental) | [~] | `llm_inference_service.py` |
| C4 | Control ET `inference=none` en runner | [x] | online: `inference_service=None` |
| C5 | Doc I/O del slot | [x] | [`../concepts/inference-slot.md`](../concepts/inference-slot.md) |
| C6 | Taxonomía de familias en plan | [x] | esta página |
| C7 | `inference_mode=hybrid` | [ ] | `NotImplementedError` |

### D. Gates y claims científicos

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| D1 | Gate “corrida válida” definido | [x] | § Gates |
| D2 | Gate H_I definido (grafo + tarea) | [x] | § Gates / ROADMAP |
| D3 | **H_I** gate en Neo4j + spaCy (seed) | [x] | `hi_wave_verdict.json` — seed, no §5 |
| D4 | Artefacto Capa 0 congelado | [x] | `capa0_artifact.json`; `reload_verdict.json` |
| D5 | Oleada-3: ≥2 familias Infer | [x] | `ner` vs `pattern`; `family_wave_verdict.json` |
| D6 | H_chunk / H_T con Y reales | [x] | `doe_h_chunk.yaml`; H_T flat; ver `pipeline_closure.json` |
| D7 | Pre-registro hipótesis en docs | [x] | este plan + research |

### E. Núcleo producto / ops (A–B librería)

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| E1 | Ingest E→T→persist Neo4j | [x] | `ingest_document` + composition root |
| E2 | Búsqueda text / vector / hybrid | [x] | API pública / guides |
| E3 | Validador topología File–Page–Chunk | [x] | `graph_topology_validate` |
| E4 | CLI setup / graph / ingest | [x] | `ungraph[cli]`; humo `tests/unit/test_cli_smoke_unit.py` |
| E5 | CLI infer / report | [x] | `infer` / `report` + help smoke en CI installation |
| E6 | Claims README alineados al slot Infer | [x] | README + inference-slot |
| E7 | Docs plan/producto como fuente en git | [x] | `docs/` versionado (canon ZEN: experiment/product/ops/archive) |

### F. Fuera del cierre de claim seed (no bloquear H_I)

| # | Ítem | Estado | Nota |
|---|------|--------|------|
| F1 | MCP Ungraph | [~] | exploratorio — horizonte C |
| F2 | Report UI / yFiles | [~] | DX, no gate científico |
| F3 | Multiagente | [~] | Capa 2 / C |
| F4 | SPARQL / ontologías remotas | [~] | checkpoint; no H_I |
| F5 | Puente Complexometrum | [ ] | Tras Y más variables / más dominios |
| F6 | Recomendación automática de arquitectura (C3) | [ ] | tras factores retenidos multi-dominio |

### Lectura rápida

- Loop ExperimentRun↔scorecard↔doekit↔online **cerrado en seed KG**.  
- H_I / family-wave / H_chunk: veredictos en `reports/` — **probe seed**, no PRODUCT §5.  
- H_chunk (AC) y H_T siguen débiles — no inflar.  
- **Cierre técnico A+B (wave1):** settings→ingest, CLI humo E4/E5, reasoning en API pública, CI NER smoke.  
- Siguiente científico (después del cierre técnico): 2º dominio o probes más duros; F5 cuando Y varíen.  
- Comandos H_chunk: ver [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md).

---

## Skills y subagentes (playbook)

| Recurso | Rol |
|---------|-----|
| Skill [`eti-experiment-science`](../../.claude/skills/eti-experiment-science/SKILL.md) | DoE, gates, oleadas |
| [`checklist-gaps.md`](../../.claude/skills/eti-experiment-science/checklist-gaps.md) | Gaps operativos |
| Agente [`ungraph-eti-science`](../../.cursor/agents/ungraph-eti-science.md) | Ejecutar / auditar oleadas |
| Agente [`ungraph-dev-skills`](../../.cursor/agents/ungraph-dev-skills.md) | Orquestar skills del cluster |

Skills de implementación (no sustituyen este plan): `eti-pipeline`, `cypher-craft`, `graphrag-pattern`, `ungraph-test`, `kg-schema`.

---

## Roadmap técnico (síntesis; no es teoría)

1. **Patrones** — `GraphPattern`; invariantes `NEXT_CHUNK`; validador post-ingesta.  
2. **Tests de topología** — integración Neo4j en CI.  
3. **Evaluación + DoE** — `ungraph[eval]` + `ungraph[experiments]`; detalle en BENCHMARK.  
4. **Matriz GraphRAG** — interfaz de retrieval; linaje en [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md).  
5. **Infer** — factories `ner` / `pattern` / `llm`; evolución histórica en archive CHECKPOINT.  
6. **CLI opcional** — adaptador; no duplica reglas de negocio.

Detalle CLI y fases de producto: ops + [`../product/PRODUCT.md`](../product/PRODUCT.md); no bloquean gates ETI.

### Referencias de implementación (probe)

- Ingestión: `ungraph/application/use_cases/ingest_document.py`  
- Inferencia: `ungraph/domain/services/inference_service.py`, infra spaCy / lexical / LLM  
- Búsqueda: `ungraph/infrastructure/services/neo4j_search_service.py`  
- Composition root: `ungraph/application/dependencies.py`  
- Evaluación: `ungraph/evaluation/` (`experiment_run`, `scorecard`, `doe_bridge`)

---

## Open claims (falseables)

### Claim H_I_seed_vs_product

- **Enunciado:** El gate H_I PASS en `knowledge_graphs` / `kg_survey.md` no implica validación PRODUCT §5 hasta confrontar ≥1 corpus/fuente externa (u otro dominio P0) con el mismo protocolo.
- **Predicción observable:** Tras 2º dominio o gold externo, al menos una Y de grafo o tarea mantiene `ner`>`none` sin colapso de AC@k; o el claim se acota a “seed-only”.
- **Protocolo mínimo:** fixture versionado + wipe + `--hi-wave` online; veredicto JSON comparable a `hi_wave_verdict.json`.
- **Falsación:** Si en el nuevo dominio `ner` no mejora recall anclado o la tarea colapsa sistemáticamente, H_I queda acotado o rechazado fuera del seed.
- **Reproducibilidad:** `ExperimentRun` + scorecard + veredicto en `reports/`; promoción a `validation/` solo si cumple §5.

### Claim H_chunk_task_Y

- **Enunciado:** Con Infer fijo (`ner`), `chunk_size` / estrategia de chunk mueven Y de **tarea** (no solo latency) en un diseño doekit con probes localizados.
- **Predicción observable:** Algún factor retenido en analyze con respuesta `answer_correctness` (o hit@k), no solo `latency_s`.
- **Protocolo mínimo:** `doe_h_chunk.yaml` online; analyze dual (AC + latency); ver `pipeline_closure.json`.
- **Falsación:** Si AC permanece en banda estrecha sin factores retenidos (estado actual del seed), el claim de mejora de tarea queda rechazado en ese corpus.
- **Reproducibilidad:** `results_h_chunk.csv` / `analysis_h_chunk*.json`.

### Claim H_bridge_complexity (will be)

- **Enunciado:** Un proxy de complejidad no estructurada en cortes ETI correlaciona con error de Infer/tarea mejor que azar en ≥2 dominios.
- **Predicción / falsación / protocolo:** ver skill `eti-experiment-science` + ROADMAP oleada Complexometrum; no diseñar mega-DoE aquí.

---

*Índice entre visión (§3/§8) e ingeniería medible. Actualizar checklist al cerrar o recortar un gate.*
