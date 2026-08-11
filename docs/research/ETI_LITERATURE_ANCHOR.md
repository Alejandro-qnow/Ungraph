# Anclaje bibliográfico ETI (deuda G.1)

> **Estado:** cerrado como *decisión de método* (no como implementación de bancos públicos).  
> **Criterio PLAN:** lista citada + decisión **adoptamos / adaptamos / dogfood-only** por familia.  
> **Consecuencia:** no inflar claims de tarea (AC, H_chunk, inter-doc, H_bridge) más allá de esta matriz.

Índice vivo de datasets dogfood: [`PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) § Deuda técnica G.2 · catálogo P0: [`benchmarks/domains/knowledge_graphs/dataset_catalog.yaml`](../../benchmarks/domains/knowledge_graphs/dataset_catalog.yaml).

---

## Matriz familia → decisión

| Familia | Tareas típicas | Bancos / refs | Métricas habituales | Mapeo Ungraph hoy | Decisión | Justificación breve |
|---------|----------------|---------------|---------------------|-------------------|----------|---------------------|
| **GraphRAG / RAG multi-hop** | QA multi-hop, summarization, local/global | HotpotQA, MuSiQue, 2WikiMultihopQA, MultiHop-RAG, GraphRAG-Bench; Edge et al. GraphRAG (arXiv:2404.16130) | EM, F1, Recall@k, nDCG, LLM-judge | AC containment @ top-k (proxy débil); rag∈{text,vector,hybrid} | **adaptamos** | Comparabilidad plena exige qrels/EM; de momento dogfood + probes; adoptar *protocolo* (top-k, multi-hop) sin clonar el leaderboard hasta `ds-public-qa` |
| **KG construction / IE** | entidad, relación, triples | DocRED, NYT, WebNLG, REBEL; surveys Hogan/Ji | P/R/F1 | `entity_recall` / `relation_pair_recall` vs gold curado | **dogfood-only** (corto plazo) → **adaptamos** (medio) | Gold experto en papers KG es barato y alinea autovalidación; DocRED-scale queda fuera del cierre seed |
| **Link prediction / KGE** | LP, embeddings KG | FB15k-237, WN18RR | MRR, Hits@k | *sin familia Infer dedicada* | **dogfood-only / fuera de foco** | No bloquea H_I ni F5; solo si aparece Infer KGE explícito |
| **Chunking / long-context RAG** | retrieval+QA, coste | LongBench, NarrativeQA; empirics chunking (p. ej. hallazgos coste vs semantic) | nDCG, EM/F1, latency | DoE `chunk_size` (señal fuerte en **latency**, débil en AC seed) | **adaptamos** | Reusar DoE Ungraph; no afirmar superioridad de estrategia sin Y variable / más docs |
| **Data complexity (tabular → proyección)** | dificultad de representación | Ho & Basu; $d_{\mathrm{eff}}$; Complexometrum $C(D)$ | $C(D)$, corr con error | covariable $C_k=C(\Pi_k(U))$ | **adoptamos** (instrumento) + **adaptamos** (proyección) | DoD tabular intacto; puente F5 vía [`COMPLEXITY_UNSTRUCTURED.md`](COMPLEXITY_UNSTRUCTURED.md) |

Leyenda de decisión:

- **adoptamos** — usamos el instrumento/protocolo tal cual (o casi) en el camino experimental.  
- **adaptamos** — tomamos tarea/métrica/idea de evaluación; el banco o el proxy es propio.  
- **dogfood-only** — no perseguimos paridad con el banco público en esta fase; corpus propio ≥5 grafos.

---

## Implicaciones para claims

| Claim | ¿Permitido con G.1 solo? | Requisito adicional |
|-------|--------------------------|---------------------|
| H_I en seed KG | sí (ya PASS) | — |
| “Mejor que Hotpot/GraphRAG-Bench” | **no** | `ds-public-qa` + métricas EM/F1 o protocolo declarado |
| H_chunk / H_T “fuertes” | **no** | G.2+ Y variable; no solo latency |
| Inter-documento / Retriever Global | **no** | G.2–G.4 |
| H_bridge Complexometrum | **no** | Fase A + ≥2 corpora con Y variable |

---

## Referencias mínimas (ancla, no bibliografía exhaustiva)

1. Edge et al., *From Local to Global* (GraphRAG), arXiv:2404.16130.  
2. Hogan et al., *Knowledge Graphs*, ACM Comput. Surv. / arXiv:2003.02320.  
3. Ji et al., *A Survey on Knowledge Graphs*, arXiv:2002.00388.  
4. Pan et al., *Unifying Large Language Models and Knowledge Graphs*, arXiv:2306.08302.  
5. Ho & Basu, measures of classification complexity (data complexity).  
6. Yang et al., HotpotQA; Trivedi et al., MuSiQue; MultiHop-RAG / GraphRAG-Bench (bancos multi-hop — *adaptamos* protocolo, no adoptamos aún el dump).

Corpus dogfood alineado a (1)–(4): `benchmarks/domains/knowledge_graphs/corpus/`.

---

## Siguiente (G.2)

Completar catálogo con `dataset_id` / `graph_id` por fuente (≥5 grafos), gold/probes etiquetados, y contrato de metadatos de ingest — sin eso G.3/G.4 y F5 Fase A siguen bloqueados por Y.
