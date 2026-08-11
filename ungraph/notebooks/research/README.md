# Notebooks research — ETI × DoE × complejidad

**Rama:** `feature/research-eti-complexity`  
**Track:** [`docs/experiment/RESEARCH_TRACK.md`](../../../docs/experiment/RESEARCH_TRACK.md)  
**Canon:** seed + A+B cerrados en PLAN; estos notebooks producen evidencia seed bajo `benchmarks/domains/knowledge_graphs/reports/research/`. **No** cumplen PRODUCT §5 por sí solos.

## Prerrequisitos

```bash
uv sync --extra experiments --extra infer-en --extra cli
python -m spacy download en_core_web_sm
# Neo4j local (online) + .env / ungraph.configure
pip install jupyter matplotlib pandas
```

Desde la raíz del repo:

```bash
jupyter notebook ungraph/notebooks/research/
```

## Serie

| # | Notebook | Oleada track |
|---|----------|--------------|
| 01 | `01_eti_pipeline_e2e.ipynb` | Pipeline library-first |
| 02 | `02_doe_doekit_screening.ipynb` | DoE doekit vía runner |
| 03 | `03_measure_plot_scorecard.ipynb` | Medir Y + plots |
| 04 | `04_complexity_bridge.ipynb` | Export F5 / proxy complejidad |

## Contratos

1. Invocar [`scripts/run_domain_pipeline.py`](../../../scripts/run_domain_pipeline.py) — no reimplementar DoE.  
2. Wipe Neo4j entre celdas online.  
3. Escribir outputs en `reports/research/` (no pisar veredictos seed).  
4. Infer = slot; comparar por Y desagregadas.
