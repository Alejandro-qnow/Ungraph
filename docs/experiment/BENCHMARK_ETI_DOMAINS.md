# Benchmark ETI end-to-end por dominio

**Capa ZEN:** `experiment/` — plan de medición / DoE (cómo medir arquitecturas ETI).  
**Audiencia:** research + developer.  
**Última revisión:** 2026-08-11

No sustituye teoría ([`../concepts/eti-spine.md`](../concepts/eti-spine.md), [`../research/WHITEPAPER_UNGRAPH_IMRAD.md`](../research/WHITEPAPER_UNGRAPH_IMRAD.md)). No inventa resultados: los números viven en JSON/CSV versionados bajo `benchmarks/…/reports/` o, tras PRODUCT §5, en [`../validation/`](../validation/).

| | |
|--|--|
| **is** | Dominio P0 `knowledge_graphs` con `manifest.yaml`, `gold.json`, corpus seed, `doe.yaml` / `doe_h_chunk.yaml`, runner `scripts/run_domain_pipeline.py`, bridge doekit, reports de oleadas (incl. `pipeline_closure.json`). |
| **will be** | Dominios P0 adicionales / P1–P2; DeepEval estable como juez; ranking multi-dominio; promoción a `validation/` solo bajo [`../product/PRODUCT.md`](../product/PRODUCT.md) §5. |
| **Open claims** | Ver § Open claims. |

Programa de gates e hipótesis: [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md). Horizonte C: [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md).

---

## 1. Motivation (por qué medir así)

Validar el pipeline solo con frases de juguete no dice si Ungraph **construye conocimiento anclado** en un dominio. La prueba útil es: documento no estructurado → E→T→I → grafo → tarea sobre **top-k recuperado**, con métricas que respondan:

1. **¿El sistema acumula hechos fieles y anclados?** (cobertura, ruido, `evidence_coverage`)
2. **¿Qué arquitectura del pipeline es mejor para este dominio?** — chunking × `inference_mode` × patrón RAG × verify, criados con DoE (`doekit`), no con un producto cartesiano ad-hoc.

ETI es un **contrato modular**: Infer puede ser `ner`, `pattern` o `llm` (API: [`../api/sp-configuration.md`](../api/sp-configuration.md)); se comparan por salidas medibles (capa A = artefacto; capa B = tarea), no por mecanismos internos.

**PRODUCT §5:** scorecard en seed ≠ “validado”. Probe Cypher histórico: [`../validation/sp-validation_summary.md`](../validation/sp-validation_summary.md).

### Dogfooding (estrategia, no prueba de verdad)

Priorizamos dominios que **son nuestras actividades** (p. ej. papers de KGs). Eso abarata gold experto y permite autocrítica; **no** sustituye confrontación con fuentes externas/similares exigida por §5.

---

## 2. Estructura “pipeline por dominio”

```
benchmarks/domains/<dominio>/
  manifest.yaml   # fuentes + arquitecturas (chunking×inference×rag) + params
  corpus/         # papers normalizados (.md / .pdf / .html)
  gold.json       # entities, relation_pairs, probes (+answers), expected_inferences
  doe.yaml        # factores / Y del DoE (si aplica)
  reports/        # scorecards, design, results, analysis, veredictos
```

### Fixture real (is) — P0 `knowledge_graphs`

| Pieza | Ruta |
|-------|------|
| README dominio | [`../../benchmarks/domains/README.md`](../../benchmarks/domains/README.md) |
| Manifest | [`../../benchmarks/domains/knowledge_graphs/manifest.yaml`](../../benchmarks/domains/knowledge_graphs/manifest.yaml) |
| Gold | [`../../benchmarks/domains/knowledge_graphs/gold.json`](../../benchmarks/domains/knowledge_graphs/gold.json) |
| Corpus seed | `corpus/kg_survey.md` (+ papers normalizados en el mismo árbol) |
| DoE base | [`../../benchmarks/domains/knowledge_graphs/doe.yaml`](../../benchmarks/domains/knowledge_graphs/doe.yaml) |
| DoE H_chunk | [`../../benchmarks/domains/knowledge_graphs/doe_h_chunk.yaml`](../../benchmarks/domains/knowledge_graphs/doe_h_chunk.yaml) |
| Cierre loop | [`../../benchmarks/domains/knowledge_graphs/reports/pipeline_closure.json`](../../benchmarks/domains/knowledge_graphs/reports/pipeline_closure.json) |
| H_I | [`…/reports/hi_wave_verdict.json`](../../benchmarks/domains/knowledge_graphs/reports/hi_wave_verdict.json) |
| Familias | [`…/reports/family_wave_verdict.json`](../../benchmarks/domains/knowledge_graphs/reports/family_wave_verdict.json) |

Otros dominios de la tabla §8: **will be** (sin árbol fixture completo en repo a la fecha de esta revisión).

---

## 3. Métricas globales — scorecard E2E

Objeto: `ungraph.evaluation.scorecard.DomainScorecard`, serializable vía `ExperimentRun` / fila DoE.

| Etapa | Métrica (contrato) | Notas is / will be |
|-------|--------------------|--------------------|
| **E** | `chunking_quality_score`, `n_chunks` | is en runner |
| **T** | `entity_recall`, `relation_pair_recall`, `n_nodes`, `n_rels`, `density`, `evidence_coverage` | is online desde Neo4j / provenance |
| **I / tarea** | probe-QA / `answer_correctness` @ top-k; F1 / hallucination cuando el eval lo cablee | hit@k is; DeepEval **[~]** |
| **RAG** | precision/recall/relevancy según eval activo | no afirmar como gate H_I |
| **Eficiencia** | `latency_s`, tokens/costo si instrumentados | latency is en oleadas |
| **Global** | `composite_score` (desirability) | útil para rankear; no sustituye Y primarias del gate |

El `composite_score` combina Y “buenas” vs “malas” para **ordenar** arquitecturas; el veredicto científico de un gate usa las Y primarias pre-registradas en [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md).

---

## 4. Espacio de arquitecturas (factores del DoE)

Cada corrida fija un punto. `doekit` diseña qué puntos correr (screening → superficie) sobre el harness:

| Factor | Niveles típicos | Alineación API / conceptos |
|--------|-----------------|----------------------------|
| Chunking | `strategy`, `chunk_size`, `chunk_overlap` | Transform |
| Inferencia | `ner` / `pattern` / `llm` / `none` | `inference_mode` (no `hybrid` aún) |
| RAG | `text` / `vector` / `hybrid`, `top_k` | Search API — interfaz, no definición de conocimiento |
| Verify | pesos / umbrales (`PipelineParams`) | Capa 2 — no mezclar en oleada H_I |

---

## 5. Baselines honestas

Las mejoras se demuestran contra líneas base, no espantapájaros:

| Id | Descripción |
|----|-------------|
| **N0** | Grafo/ET crudo: Infer `none` o NER sin verify |
| **N1** | LLM extrae y confía (sin grounding) — cuando `llm` esté en la celda |
| **N2** | Co-ocurrencia / verify determinista sin LLM |
| **Sistema** | ETI + anclaje (`evidence_coverage`) según arquitectura bajo prueba |

---

## 6. Alucinaciones y juez externo

Regla anti-circularidad: el evaluador de faithfulness/hallucination **no** debe ser el mismo LLM que actúa de crítico en verify. DeepEval (`ungraph[eval]`) es el camino **will be / parcial** para juez externo; hoy el gate H_I usa gold + containment @ top-k, no DeepEval como portería.

---

## 7. Dominios y priorización

| Prioridad | Dominio | Estado fixture |
|-----------|---------|----------------|
| **P0** | Grafos de conocimiento (`knowledge_graphs`) | **is** — ver §2 |
| **P0** | Ingeniería de conocimiento | **will be** |
| **P0** | Arquitecturas cognitivas | **will be** |
| **P1** | Machine learning; álgebra lineal | **will be** |
| **P2** | Computación cuántica; química computacional (control de generalización) | **will be** |

Fuentes candidatas (mix): arXiv/web para CS/KG; PubMed u otras para bio/química — al materializar un dominio nuevo, versionar corpus + gold + manifest juntos.

---

## 8. Gold: estrategia

Silver labels (LLM fuerte) + **revisión experta** donde el dogfooding lo permita. Incluir probes con respuestas y, cuando aplique, `expected_inferences` multi-hop. El gold del P0 actual está en `gold.json` (is); ampliar sin romper el protocolo de wipe/seed.

---

## 9. Cómo se ejecuta (DoE con doekit)

Instalación: `pip install 'ungraph[experiments]'` (o `uv run --extra experiments …`).

Camino por defecto — **no** barrer un producto cartesiano ad-hoc:

```bash
# 1) screening → diseña la oleada
python scripts/run_domain_pipeline.py --domain knowledge_graphs --design screening --mode offline

# 2) run → scorecards + results.csv
python scripts/run_domain_pipeline.py --domain knowledge_graphs --design run --mode offline

# 3) analyze → main effects / factores retenidos (artefacto JSON; no citar p-values aquí)
python scripts/run_domain_pipeline.py --domain knowledge_graphs --design analyze

# 4) propose → siguientes corridas sobre factores activos
python scripts/run_domain_pipeline.py --domain knowledge_graphs --design propose
```

Online (Neo4j + spaCy; paper / no gate CI):

```bash
python scripts/run_domain_pipeline.py --domain knowledge_graphs --design run --mode online
# H_I / family-wave / H_chunk: flags y doe-path según PLAN_MAESTRO + skill eti-experiment-science
```

| Modo | Uso |
|------|-----|
| `--mode offline` | CI / smoke; sin depender de Neo4j/API keys como gate |
| `--mode online` | Paper / gates seed; wipe entre celdas |

Salida típica bajo `reports/`: `design.json`, `results.csv`, `summary.json`, `analysis.json`, `retained_factors.json`, scorecards, veredictos de oleada.

Contrato: `ExperimentRun` ↔ `DomainScorecard` ↔ fila plana DoE (`ungraph/evaluation/doe_bridge.py`).

---

## 10. Relación con el roadmap

- Instrumentación y gates seed: [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md).  
- MCP / recomendación automática / DQ avanzada: fuera del cierre A+B — [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md).  
- Complexometrum: puente posterior; no bloquea H_I seed.

---

## Open claims (falseables)

### Claim H_doe_multi_domain

- **Enunciado:** El mismo descriptor DoE + Y primarias (recall Neo4j + AC@k) discrimina arquitecturas en ≥2 dominios P0 con fixtures versionados.
- **Predicción observable:** En el 2º dominio, al menos un factor de Infer o chunking retiene efecto en Y de grafo o tarea (no solo latency).
- **Protocolo mínimo:** nuevo `benchmarks/domains/<dom>/` con manifest/gold/corpus; screening→run→analyze; comparar con `pipeline_closure.json` del P0 KG.
- **Falsación:** Si las Y son planas o no reproducibles tras wipe, el claim de generalización DoE se acota al seed KG.
- **Reproducibilidad:** reports por dominio; promoción a `validation/` solo con criterio PRODUCT §5.

### Claim H_judge_deepeval

- **Enunciado:** Un juez DeepEval independiente correlaciona con fallo de grounding mejor que el crítico interno del verify en celdas con temperatura>0.
- **Predicción / falsación:** protocolo en PLAN (B6); no afirmar métricas hasta artefacto versionado.
- **Reproducibilidad:** scorecard con campos DeepEval + `ExperimentRun`.
