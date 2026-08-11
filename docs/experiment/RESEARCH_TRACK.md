# Research track — ETI × DoE × complejidad

**Capa ZEN:** `experiment/` — índice ejecutable de la rama `feature/research-eti-complexity`.  
**Audiencia:** research + developer.  
**Última revisión:** 2026-08-11  
**Base:** [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) (seed + A+B **cerrados**); Open claims §5 siguen abiertos.

| | |
|--|--|
| **is** | Track documentado; runner doekit + dominio P0 KG; serie notebooks research (esqueleto); export F5 `complexity_export` portado. |
| **will be** | Corridas NB-01…04 con figs bajo `reports/research/`; probes duros en KG; 2º dominio P0; bridge Complexometrum con Y variables. |
| **Open claims** | `H_I_seed_vs_product`, `H_chunk_task_Y`, `H_bridge_complexity` — ver PLAN § Open claims. Seed ≠ PRODUCT §5. |

No sustituye fundamento ([`../research/COMPLEXITY_UNSTRUCTURED.md`](../research/COMPLEXITY_UNSTRUCTURED.md)) ni el contrato API. Notebooks **no** “validan” producto.

---

## Mapa ZEN (dónde vive cada pieza)

| Capa | Path | Rol |
|------|------|-----|
| Fundamento | [`../research/COMPLEXITY_UNSTRUCTURED.md`](../research/COMPLEXITY_UNSTRUCTURED.md), [`../research/OLEADA_COMPLEXOMETRIA_UNSTRUCTURED.md`](../research/OLEADA_COMPLEXOMETRIA_UNSTRUCTURED.md) | $C_k$, roles Ungraph↔Complexometrum |
| Experimentación | **este archivo**, [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md), [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) | Oleadas, gates, comandos |
| Reproducibilidad | [`../../ungraph/notebooks/research/`](../../ungraph/notebooks/research/) | Step-by-step E2E |
| Medición cruda | [`../../benchmarks/domains/knowledge_graphs/reports/research/`](../../benchmarks/domains/knowledge_graphs/reports/research/) | JSON/CSV/figs de esta rama (no pisar veredictos seed) |
| Código bridge | [`../../ungraph/evaluation/complexity_export.py`](../../ungraph/evaluation/complexity_export.py) | Export proyecciones ETI → Complexometrum |
| Runner | [`../../scripts/run_domain_pipeline.py`](../../scripts/run_domain_pipeline.py) | Única orquestación DoE |

```text
fundamento (research/) → experimentación (este track + doekit)
  → notebooks/research → reports/research/
  → validation/ solo si PRODUCT §5
```

---

## Oleadas

| # | Objetivo | Criterio de hecho | Estado |
|---|----------|-------------------|--------|
| **0 Scaffold** | Rama + track + port F5 + stubs NB | Paths versionados; tests unit `complexity_export` | **is** (este commit) |
| **1 NB-01 E2E** | Pipeline library-first step-by-step | Notebook ejecutable: configure→ingest→infer/search→topology | will be |
| **2 NB-02 DoE** | Batería doekit screening→run→analyze | Artefactos en `reports/research/` vía runner | will be |
| **3 NB-03 Plots** | Y desagregadas (recall, AC@k, latency) | Figs + lectura scorecard; no composite como veredicto | will be |
| **4 NB-04 Bridge** | Export + correlación exploratoria proxy↔error | `complexity_export` + notebook; claim H_bridge sigue DEFERRED | will be |
| **5 Probes duros KG** | Bajar saturación AC@k | Gold/probes ajustados; re-leer H_chunk | will be |
| **6 2º dominio** | Confrontación `H_I_seed_vs_product` | Fixture P0 + `--hi-wave` comparable | will be (oleada siguiente) |

---

## Serie notebooks

Ver [`../../ungraph/notebooks/research/README.md`](../../ungraph/notebooks/research/README.md).

| Notebook | Qué ejemplifica |
|----------|-----------------|
| `01_eti_pipeline_e2e.ipynb` | Extract → Transform → Infer → retrieval |
| `02_doe_doekit_screening.ipynb` | doekit recommend/screening → run → analyze |
| `03_measure_plot_scorecard.ipynb` | Medir Y y graficar desde `reports/` |
| `04_complexity_bridge.ipynb` | Export embeddings/meta → proxy complejidad |

Índice how-to: [`../examples/sp-notebooks.md`](../examples/sp-notebooks.md).

---

## Comandos de referencia (DoE)

```bash
# Offline (CI / laptop sin Neo4j)
uv run --extra experiments python scripts/run_domain_pipeline.py \
  --domain knowledge_graphs --design screening --mode offline --redesign
uv run --extra experiments python scripts/run_domain_pipeline.py \
  --domain knowledge_graphs --design run --mode offline
uv run --extra experiments python scripts/run_domain_pipeline.py \
  --domain knowledge_graphs --design analyze

# Online H_I (wipe Neo4j; spaCy EN)
uv run --extra experiments --extra infer-en python scripts/run_domain_pipeline.py \
  --domain knowledge_graphs --design run --mode online --hi-wave
```

Salidas de trabajo de esta rama: escribir bajo `benchmarks/domains/knowledge_graphs/reports/research/` (crear al correr; no sobrescribir `hi_wave_verdict.json` seed).

---

## Contratos

1. DoE solo con `doekit` + `ungraph[experiments]` — no producto cartesiano ad-hoc.  
2. Infer = slot ([`../concepts/inference-slot.md`](../concepts/inference-slot.md)).  
3. Wipe Neo4j entre celdas online.  
4. No mezclar Capa 2 (agente) en DoE de Capa 0.  
5. Actualizar [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) solo al cerrar un Open claim o des-diferir F5.

---

## Relación con PLAN / ROADMAP

| Documento | Rol respecto a este track |
|-----------|---------------------------|
| [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) | Gates seed cerrados; Open claims ciencia |
| [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md) | Scorecard, fixtures, how-to doekit |
| [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) | F5 / C3–C4 horizonte; no bloquea scaffold |

*Scaffold de consecuencia ZEN. Completar oleadas 1–5 en commits sucesivos de esta feature.*
