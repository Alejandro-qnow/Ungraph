# Research track — ETI × DoE × complejidad

**Capa ZEN:** `experiment/` — índice ejecutable de la rama `feature/research-eti-complexity`.  
**Audiencia:** research + developer.  
**Última revisión:** 2026-08-11  
**Base:** [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) (seed + A+B **cerrados**); Open claims §5 siguen abiertos.

| | |
|--|--|
| **is** | Track documentado; runner doekit + dominio P0 KG; serie notebooks research; export F5; **[`EXPERIMENTAL_DESIGN.md`](EXPERIMENTAL_DESIGN.md)** como único contexto de diseño experimental. |
| **will be** | Packs + staging; probes D0–D5 calibrados; DoE multidoc; $C_k$ por celda; corridas NB; veredictos `reports/research/multicorpus/`. |
| **Open claims** | Ver [`EXPERIMENTAL_DESIGN.md`](EXPERIMENTAL_DESIGN.md) §3 + PLAN § Open claims. Seed ≠ PRODUCT §5. |

**Diseño experimental (hipótesis, planilla, traza, diseños A–C):** [`EXPERIMENTAL_DESIGN.md`](EXPERIMENTAL_DESIGN.md).

No sustituye fundamento ([`../research/COMPLEXITY_UNSTRUCTURED.md`](../research/COMPLEXITY_UNSTRUCTURED.md)) ni el contrato API. Notebooks **no** “validan” producto.

---

## Mapa ZEN (dónde vive cada pieza)

| Capa | Path | Rol |
|------|------|-----|
| Fundamento | [`../research/COMPLEXITY_UNSTRUCTURED.md`](../research/COMPLEXITY_UNSTRUCTURED.md), [`../research/OLEADA_COMPLEXOMETRIA_UNSTRUCTURED.md`](../research/OLEADA_COMPLEXOMETRIA_UNSTRUCTURED.md) | $C_k$, roles Ungraph↔Complexometrum |
| Experimentación | **este archivo**, [`EXPERIMENTAL_DESIGN.md`](EXPERIMENTAL_DESIGN.md), [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md), [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) | Diseño experimental, oleadas, gates, comandos |
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
| **5 Probes + multicorpus** | Calibración D0–D5 + packs/staging (Diseño A–B) | Ver [`EXPERIMENTAL_DESIGN.md`](EXPERIMENTAL_DESIGN.md) P1–P6 | will be |
| **6 Complejidad por celda** | $C_k$ covariable en cada ExperimentRun | Diseño C + analyze vs D3–D4 | will be |
| **7 2º dominio / §5** | Confrontación externa tras Y discriminativas | Fixture P0 + protocolo comparable | will be (después de P8) |

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
