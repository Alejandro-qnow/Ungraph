# Roadmap — Horizonte nivel C

**Capa ZEN:** `experiment/` — trayectoria C e investigación; **no** promesa de cierre A+B.  
**Audiencia:** research + developer.  
**Última revisión:** 2026-08-11  
**Paquete:** `ungraph` (`pyproject.toml`)

**Referencias:** [`../product/VISION_AND_TUTORIALS.md`](../product/VISION_AND_TUTORIALS.md) §3 (nivel C), §8 (mejor grafo); [`../product/PRODUCT.md`](../product/PRODUCT.md) §2 / §5; gates seed en [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md); DoE en [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md).

| | |
|--|--|
| **is** | Instrumentación C0–C1 y C5 parcial en código (`ExperimentRun`, scorecard, doekit); oleadas seed H_I / family-wave / H_chunk **cerradas en P0** (ver PLAN — seed ≠ PRODUCT §5). |
| **will be** | C2 ampliado multi-dominio; C3 recomendación; C4 MCP/interop; C5 automejora orquestada; DQ `dq_*` ([`sp-data-quality-graph-plan.md`](sp-data-quality-graph-plan.md)); Complexometrum. |
| **Open claims** | Ver § Open claims. Nada de C se vende como capacidad B “validada”. |

**Línea roja:** Ungraph habilita medición y decisión reproducible; el integrador define políticas de memoria, gobernanza y producto cerrado. ETI nombra un **contrato de etapas**, no un único motor de inferencia. Retrieval/MCP son **consumidores** del almacén epistémico.

---

## Alcance: fuera del cierre A+B

| Nivel | Rol de este documento |
|-------|------------------------|
| **A / B** | Promesa librería + gates seed en PLAN/BENCHMARK; API/guides (tanda A). |
| **C** | Este archivo: recomendación, automejora, interop/MCP, DQ avanzada, multiagente — **horizonte**. |

No mezclar avance de C4/MCP con el cierre científico seed (H_I). El seed loop puede estar cerrado y C seguir abierto.

---

## Qué significa “llegar a C”

El nivel C incluye: recomendación de estructuras según métricas, automejora guiada por datos, interoperabilidad con KG abiertos y estándares, MCP u otras superficies opcionales, y capas avanzadas de calidad de datos. Es **trayectoria**, no un único PR.

Vía de llegada (capas experimentales; fundamento en [`../concepts/eti-spine.md`](../concepts/eti-spine.md)):

1. Artefacto ETI medible (Capa 0) — **seed is**  
2. Recuperación pareada (Capa 1) — **seed is** parcial  
3. Comparación de razonadores / agentes (Capa 2) sobre el mismo artefacto — **parcial is** (`ner`/`pattern`); LLM/multiagente **will be**

---

## Fases de producto C (orden sugerido)

| Fase | Objetivo | Criterio de hecho (mínimo) | Estado orientativo |
|------|-----------|----------------------------|--------------------|
| **C0 — Base** | Artefactos serializables + stats R/O | `ExperimentRun`, JSON round-trip, stats estructurales | **is** (seed) |
| **C1 — Eval–refinar** | Build → métricas → comparar runs | `DomainScorecard`, probes; DeepEval opcional | **is** parcial |
| **C2 — Calidad estructural** | Evidencia, duplicados, densidad por doc | Cypher versionado + `evidence_coverage` Neo4j | **is** en seed; ampliar multi-doc **will be** |
| **C3 — Recomendación** | Sugerir chunking/patrón/rag desde tablas | Heurísticas versionadas; solo factores *retenidos* por DoE multi-dominio | **will be** |
| **C4 — Interop + MCP** | Export + MCP opcional sin duplicar Neo4j genérico | Extra `mcp` o doc; tools → casos de uso | **will be** / exploratorio |
| **C5 — DoE / automejora** | Screening + orquestación `recommend→…→propose` | `ungraph[experiments]`; oleadas más allá del seed | **is** bridge; automejora **will be** |

---

## Programa de oleadas (visión científica)

Alineado al whitepaper y a PLAN. Detalle de veredictos seed: [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md) § fixtures.

### Oleada-1 — Screening offline — **hecho (seed)**

- Diseño D-optimal, dominio P0 `knowledge_graphs`.  
- Señal: factor `inference` domina frente a ET; Y RAG offline poco discriminativas.  
- Artefactos: `benchmarks/domains/knowledge_graphs/reports/`.

### Oleada-2 — H_I online — **hecho (seed); no PRODUCT §5**

Gate PASS en seed (`hi_wave_verdict.json`): `ner` > `none` en recall Neo4j; tarea @ top-k no colapsa.  
**No** reabrir como “prioridad actual” de ingeniería salvo regresión o nuevo dominio (claim H_I_seed_vs_product en PLAN).

### Oleada-3 — Familias de Infer — **hecho base (seed)**

`ner` vs `pattern` sobre Capa 0 (`family_wave_verdict.json`). Extender a `llm` / híbridos / multiagente = **will be** (Capa 2), sin mezclar knobs de agente en gates de Capa 0.

**Principio:** abstraer el **slot** ([`../concepts/inference-slot.md`](../concepts/inference-slot.md)); no generalizar “cómo se diseña Infer”.

### Oleada-4 — H_chunk / H_T — **medido (seed); claims débiles**

DoE `doe_h_chunk.yaml`; AC débil; latency retiene `chunk_size`; H_T no afirmable. Ver `pipeline_closure.json`. Siguiente rigor: probes más duros o 2º dominio — aún puede vivir en backlog B científico sin ser “release C”.

### Oleada-5+ — Multi-dominio / C3–C4 — **will be (horizonte C)**

Segundo dominio P0, screening retenido multi-dominio, recomendación (C3), MCP/interop (C4), DQ `dq_*`.

### Oleada opcional — Puente Complexometrum — **will be**

Cortes ETI como banco para proxies de complejidad no estructurada. No bloquea C0–C2 ni el gate H_I seed. Ver PLAN § Complexometrum.

### Secuencia de rigor (checklist)

```
[x] I/O Infer documentado (slot)                 ← concepts/inference-slot.md
[x] Y desde Neo4j + probes sobre top-k           ← seed
[x] Oleada-2 H_I gate seed                       ← hi_wave_verdict.json (≠ §5)
[x] Artefacto Capa 0 congelado                   ← capa0_artifact.json
[x] Oleada-3: ≥2 familias Infer                  ← ner vs pattern
[x] H_chunk/H_T DoE doekit (claims débiles)
[x] Cierre loop seed KG                          ← pipeline_closure.json
[ ] 2º dominio / confrontación externa (§5)
[ ] C3 recomendación / C4 MCP / DQ avanzada
```

---

## Dependencias entre documentos

| Documento | Rol |
|-----------|-----|
| [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) | Gates, capas 0–2, checklist is |
| [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md) | Scorecard, doekit, fixtures |
| [`sp-data-quality-graph-plan.md`](sp-data-quality-graph-plan.md) | DQ `dq_*` (C) |
| [`../archive/CHECKPOINT_INFERENCE_PIPELINE.md`](../archive/CHECKPOINT_INFERENCE_PIPELINE.md) | Infer enriquecida (histórico) |
| [`../validation/sp-validation_summary.md`](../validation/sp-validation_summary.md) | Probe ≠ §5 |
| `ungraph/evaluation/` | ExperimentRun, scorecard, doe_bridge |

---

## Cómo contribuir a C sin inflar el núcleo

1. Capacidades **medibles** antes que “mágicas”: hooks y serialización.  
2. Dependencias pesadas (DeepEval, doekit, MCP) solo en **extras**.  
3. Dominio sin drivers Neo4j/LangChain; Infer como **slot** detrás de `InferenceService`.  
4. Un factor del backlog C solo si sobrevive screening con Y discriminativa (idealmente multi-dominio).  
5. No afirmar C en guides/API como hecho; guides = A/B **is**.

---

## Open claims (falseables)

### Claim H_C3_recommend

- **Enunciado:** Una heurística versionada que sugiera `(chunking, inference_mode, rag)` a partir de factores retenidos por DoE mejora `composite_score` o Y de tarea frente a default fijo en un dominio held-out.
- **Predicción observable:** En ≥1 dominio no usado para ajustar la heurística, la arquitectura sugerida gana al default en Y pre-registrada.
- **Protocolo mínimo:** tabla de factores retenidos + notebook/script de recomendación + `ExperimentRun` held-out.
- **Falsación:** Si no hay ganancia estable o la heurística solo memoriza el seed KG, C3 se acota o pospone.
- **Reproducibilidad:** artefacto de recomendación + scorecards; no promoción a PRODUCT “validado” sin §5.

### Claim H_C4_mcp_consumer

- **Enunciado:** Una superficie MCP (u otra tool API) puede consumir el almacén epistémico (chunks/facts con provenance) sin redefinir conocimiento como retrieval.
- **Predicción observable:** Tools invocan casos de uso existentes; no aparece Cypher de producto duplicado en el adaptador.
- **Protocolo mínimo:** extra documentado + smoke test; enlace a concepts/eti-spine.
- **Falsación:** Si MCP reimplementa el grafo o afirma “validado” sin scorecard, el claim de consumidor limpio falla.
- **Reproducibilidad:** paquete/extra versionado + doc en `ops/` o API cuando estabilice.

---

*Actualizar cuando una fase C cierre o se recorte un claim. No confundir MCP/C3 con el gate H_I seed.*
