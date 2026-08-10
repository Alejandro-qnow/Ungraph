# Roadmap — Horizonte nivel C (plan maestro)

**Referencia:** [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) §3 (nivel C), §8 (aprendizaje del mejor grafo), [`PRODUCT.md`](PRODUCT.md) §2, [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) (visión técnico-científica).  
**Paquete:** `ungraph` (ver `pyproject.toml`).  
**Última revisión:** 2026-08-10

**Alcance:** este documento expresa el nivel C como trayectoria e investigación **y** el programa de oleadas experimentales que alinean visión científica (claims falsables) con ingeniería medible. No todo C es compromiso de release; las oleadas marcadas como *cierre de claim* sí priorizan el backlog.

**Línea roja:** Ungraph habilita medición y decisión reproducible; el integrador define políticas de memoria, gobernanza y producto cerrado. ETI nombra un **contrato de etapas**, no un único motor de inferencia.

---

## Qué significa “llegar a C”

El nivel C incluye: recomendación de estructuras según métricas, automejora guiada por datos, interoperabilidad con KG abiertos y estándares, MCP u otras superficies de herramienta opcionales, y capas avanzadas de calidad de datos. Es **trayectoria**, no un único PR.

La vía de llegada pasa por **experimentos en capas** (ver plan maestro):

1. Artefacto ETI medible (Capa 0)  
2. Recuperación pareada (Capa 1)  
3. Comparación de razonadores / agentes (Capa 2) sobre el mismo artefacto  

---

## Fases de producto C (orden sugerido)

| Fase | Objetivo | Criterio de hecho (mínimo) | Ligado a claims |
|------|-----------|----------------------------|-----------------|
| **C0 — Base** | Artefactos de experimento serializables + stats de grafo R/O | `ExperimentRun`, JSON round-trip, `collect_structural_graph_stats` | Infra de medición |
| **C1 — Eval–refinar** | Build → métricas → comparar runs / scorecard E2E | `DomainScorecard`, ranking, probes; DeepEval opcional (`ungraph[eval]`) | Gates de corrida |
| **C2 — Calidad estructural** | Más allá de conteos: evidencia, duplicados, densidad por doc | Cypher versionado + tests integración; `evidence_coverage` desde Neo4j | Y de grafo para H_I |
| **C3 — Recomendación** | Sugerir chunking/patrón/rag desde tablas de métricas | Heurísticas versionadas + notebook; solo factores *retenidos* por DoE | Tras screening real |
| **C4 — Interop + MCP** | Export + MCP opcional sin duplicar Neo4j genérico | Extra `mcp` o doc; tools → casos de uso | Fuera del claim H_I |
| **C5 — DoE / automejora** | Screening y oleadas con `doekit`; luego orquestación | `ungraph[experiments]`; `recommend → run → analyze → propose` | Motor de oleadas |

**Estado orientativo (2026-08):** C0–C1 y C5 parcial (screening offline + bridge doekit) existen. **C2 real (Y desde Neo4j)** y **oleada H_I online** son el siguiente cuello de botella científico. C3–C4 sin fecha de release.

---

## Programa de oleadas experimentales (visión científica)

Alineado a [`article/ETI/EXTRACT-TRANSFORM-INFER.md`](../article/ETI/EXTRACT-TRANSFORM-INFER.md) y [`article/ungraph.md`](../article/ungraph.md).

### Oleada-1 — Screening offline (hecho)

- Diseño D-optimal (8 runs), dominio P0 `knowledge_graphs`.  
- Señal: `inference` domina (`ner` ≫ `none`); chunking/rag/chunk_size poco discriminativos.  
- Límite: Y RAG sobre corpus completo y recall léxico → **no cierra H_I**.  
- Artefactos: `benchmarks/domains/knowledge_graphs/reports/`.

### Oleada-2 — Cerrar H_I (prioridad actual)

**Objetivo:** validar que Infer aporta en **pipeline real** (Neo4j + spaCy), Transform fijo.

| Elemento | Decisión |
|----------|----------|
| Factor | `inference ∈ {none, ner}` |
| Fijos | chunking (p. ej. recursive/1024), corpus seed (+ gold), wipe Neo4j |
| RAG | `text` y/o `vector` como bloque pareado, no foco |
| Y primarias | recall entidades/rels **desde Neo4j**; probe-QA / hit@k sobre **top-k recuperado** |
| Y apoyo | `evidence_coverage`, latency; composite secundario |
| Éxito | `ner` > `none` en Y de grafo **y** tarea no colapsa |
| Fracaso honesto | recortar filosofía del artículo; no inventar más factores |

Dependencias de ingeniería: runner online mínimo, wipe, eval grafo, probes sobre contexto recuperado (no documento entero). Ver gates en [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md).

### Oleada-3 — Familias de Infer / razonadores (Capa 2)

Solo sobre artefactos que pasaron el gate de corrida + (idealmente) H_I.

**Principio:** no generalizar “cómo se diseña Infer”; **abstraer el slot** y comparar familias (ver taxonomía en [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md)). spaCy es un punto de la familia transductiva; no el patrón entero.

Tratamientos sugeridos (pocos, pre-registrados):

| Tratamiento | Familia | Rol |
|-------------|---------|-----|
| `none` / ET | control | Ya cubierto en H_I |
| `ner` (spaCy) | transductiva | Baseline Ungraph |
| verify estructural / ontología | simbólica / grounding | Determinista |
| 1× LLM extracción o QA | neural | No-det o temp=0 |
| híbrido NER→LLM o propose–critique–verify | det↔no-det | Si el código ya existe |
| (opcional) 1 diseño multiagente | conversacional | Misma Y, no más features |

- Mismo `run_id`/snapshot → todos los tratamientos.  
- Y de capa B comunes; tokens/pasos/ventana/topología consultada = covariables.  
- GraphRAG híbrido + análisis topológico (GDS) entra como **familia GraphRAG/topológica** en Capa 1–2, no como redefinición de ETI.  
- DoE/`doekit`: cribar knobs **dentro** de una familia solo si las Y discriminan.

### Oleada-4+ — H_chunk / H_T / multi-dominio

Cuando existan Y de retrieval reales y al menos un dominio P0 estable; screening de chunking y proxies de transform; ampliar dogfood (ingeniería de conocimiento, arquitecturas cognitivas).

### Oleada opcional — Puente Complexometrum

Tras Y discriminativas y (idealmente) H_I: usar cortes ETI (embeddings, grafo, facts) como banco para proxies de **complejidad de data no estructurada**. Si correlacionan con error de Infer/tarea, el adaptador validado puede **regresar como feature** a la librería Complexometrum (robustecer más allá de lo tabular). No bloquea C0–C2 ni el claim H_I. Ver [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) § Complexometrum.

### Secuencia de rigor (checklist)

```
[x] I/O Infer documentado (slot, no mega-diseño)          ← concepts/inference-slot.md
[x] Y desde Neo4j + probes sobre top-k
[x] Oleada-2 H_I cerrada o claim recortado
[x] Artefacto Capa 0 congelado (run_id)                   ← capa0_artifact.json
[x] Oleada-3: ≥2 familias de Infer, mismas Y              ← ner vs pattern
[x] H_chunk/H_T DoE doekit (AC débil; latency retiene chunk_size)
[x] Cierre loop seed KG (`pipeline_closure.json`)
[ ] Solo entonces: más agentes / MCP / recomendación (C3–C4)
```

---

## Dependencias entre documentos

| Documento | Rol |
|-----------|-----|
| [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) | Gates, capas 0–2, hipótesis pre-registradas |
| [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md) | Scorecard, doekit, cómo ejecutar |
| [`CHECKPOINT_INFERENCE_PIPELINE.md`](CHECKPOINT_INFERENCE_PIPELINE.md) | Inferencia enriquecida (sustrato medible) |
| [`agent/AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md) | Prioridades técnicas §7–8 |
| [`ungraph/evaluation/`](../ungraph/evaluation/) | ExperimentRun, scorecard, doe_bridge, cognitive_eval |

---

## Cómo contribuir a C sin inflar el núcleo

1. Capacidades **medibles** antes que “mágicas”: hooks y serialización.  
2. Dependencias pesadas (DeepEval, doekit, MCP) solo en **extras** (`eval`, `experiments`, futuro `mcp`).  
3. Dominio sin `langchain_*` ni drivers Neo4j; Infer como **slot** detrás de `InferenceService`.  
4. Un factor del backlog solo si sobrevive screening con Y discriminativa.

---

*Actualizar este roadmap cuando una oleada cierre o se recorte un claim; no confundir avance de C4/MCP con el cierre de H_I.*
