# Anexo: hallazgos — oleada Complexometría unstructured

> **Rama:** `feature/complexometría-unstructured`  
> **Fecha:** 2026-08-11  
> **Plan:** [`PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) § Complexometrum / F5 / Deuda G  
> **Fundamento:** [`COMPLEXITY_UNSTRUCTURED.md`](COMPLEXITY_UNSTRUCTURED.md) · lit [`ETI_LITERATURE_ANCHOR.md`](ETI_LITERATURE_ANCHOR.md)

Cierre de la oleada que cableó deuda **G** (multi-grafo / retrieval) y el **medio puente F5** (export Ungraph + Fase A en Complexometrum). No afirma H_T ni H_bridge.

---

## Qué se cerró en Ungraph

| Ítem | Evidencia |
|------|-----------|
| G.1 Anclaje lit | este doc hermano + matriz adopt/adapt/dogfood |
| G.2 Catálogo + gold multi-grafo | `dataset_catalog.yaml` (5 `graph_id`); `gold.json` `by_graph` |
| G.3 Scope search | `dataset_scope`; `ungraph.search(..., scope=)`; ingest propaga `dataset_id`/`graph_id` |
| G.4 Retriever Global MVP | `global_topology_search` (seeds + degree + NEXT_CHUNK; **no** GDS PageRank) |
| G.5 rag-wave | `--design rag-wave`; `reports/rag_wave_verdict.json` **COMPARED** |
| F5 export | `complexity_export.export_chunk_embeddings` → `embeddings.npy` |
| H_bridge v0 (mitad Ungraph) | `scripts/run_h_bridge_v0.py` → `reports/h_bridge_v0/` (2 celdas) |
| E4/E5 CLI | smoke `tests/unit/test_cli_commands.py`; CI unit con `.[cli]` |

**Complexometrum (repo hermano, rama `feature/unstructured-adapters`):** Fase A commit `199e18f` — `from_embeddings` / `from_chunk_table`. El analyze Spearman de H_bridge queda en ese repo; aquí solo se versiona la mitad Ungraph.

---

## Hallazgos empíricos (claims permitidos / prohibidos)

### rag-wave (`ds-kg-survey`, 5 docs, 14 probes, Infer=`ner`)

| rag | AC@k | entity_recall | latency_s (aprox.) |
|-----|------|---------------|--------------------|
| text | 1.0 | 0.414 | ~14 |
| vector | 0.929 | 0.414 | ~9.3 |
| global_topology | 1.0 | 0.414 | ~9.4 |

**Sí se puede decir**

- Protocolo multi-grafo + wipe + gold `by_graph` es operable online.
- Topology MVP **no empeora** vs text en esta Y (ambos AC=1.0).
- Instrumento de corrida rag-wave es reproducible (`doe_rag_wave.yaml` + runner).

**No se puede decir**

- Topology > vector / GraphRAG “gana”.
- H_T o H_bridge validados.
- Paridad con Hotpot / Edge GraphRAG / PageRank GDS (el MVP no es PageRank).
- Que el −7 pp de vector sea efecto real (N pequeño; posible ruido).

### H_bridge v0 (2 grafos: `kg-survey-seed`, `edge-graphrag-2404.16130`)

Ambas celdas: **AC=1.0 → `error_qa=0`**. Con Y plana, cualquier correlación $C_D$↔error es **NO_SIGNAL_Y** hasta probes más duros o más grafos con error>0. Mitad Complexometrum (`analyze_cells`) no bloquea merge de esta rama; bloquea el *claim* H_bridge.

---

## Lectura científica acordada

1. Banco (G) y proyector (Fase A / export) listos para el puente.  
2. AC saturada en seed/rag-wave → no rankear arquitecturas ni inflar narrativa de complejidad.  
3. Siguiente oleada H_bridge exige **Y discriminativa** (error_qa variable) antes de Fase B (grafo no-FCG).  
4. Fuera de foco inmediato: $\tau$, QSAR, Hotpot, PageRank GDS, C7 hybrid.

---

## Artefactos a reproducir

```bash
# rag-wave
uv run --extra experiments --extra infer-en python scripts/run_domain_pipeline.py \
  --domain knowledge_graphs --design rag-wave --mode online

# celdas H_bridge (Ungraph)
uv run --extra experiments --extra infer-en python scripts/run_h_bridge_v0.py \
  --domain knowledge_graphs --graph-ids kg-survey-seed,edge-graphrag-2404.16130
```

Reports canónicos: `benchmarks/domains/knowledge_graphs/reports/rag_wave_verdict.json`, `…/h_bridge_v0/cells_summary.json`.

---

## Estado del checklist al cerrar la rama

| Checklist | Estado |
|-----------|--------|
| G1–G3, G5 | [x] |
| G4 | [~] MVP; PageRank opcional |
| F5 | [~] memo + export + Fase A CX; H_bridge empírico abierto |
| C7 / F6 / B6 | sin cambio (fuera de esta oleada) |
