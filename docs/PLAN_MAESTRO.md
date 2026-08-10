# Plan maestro de ejecución (Ungraph)

**Última revisión:** 2026-08-10  
**Paquete:** `ungraph` ([`pyproject.toml`](../pyproject.toml))

Este documento es el **índice ejecutable** del trabajo de producto e ingeniería: enlaza la visión, el producto, los skills de agentes, los hitos de pipeline ETI (incluida **Infer**), la **CLI opcional** (`ungraph[cli]`), la evaluación GraphRAG y el **programa experimental** (visión técnica + científica). No sustituye el changelog ni la API pública.

## Jerarquía de documentos

| Documento | Rol |
|-----------|-----|
| [`PRODUCT.md`](PRODUCT.md) | Qué es Ungraph, para quién, historias de usuario, niveles A/B/C. |
| [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) | Visión, §3 promesa, tutoriales, §8 ciclo construir–evaluar–refinar. |
| [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md) | Scorecard E2E, DoE (`doekit`), dogfooding, gates de corrida. |
| [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) | Horizonte C + oleadas experimentales (H_I, razonadores). |
| [`CHANGELOG_v0.1.5.md`](CHANGELOG_v0.1.5.md) | Registro de cambios de la versión publicable actual. |
| [`agent/AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md) | Prioridades técnicas, skills (`eti-pipeline`, `cypher-craft`, `graphrag-pattern`, `ungraph-test`, …). |
| [`CHECKPOINT_INFERENCE_PIPELINE.md`](CHECKPOINT_INFERENCE_PIPELINE.md) | Retomada del trabajo en inferencia enriquecida. |
| [`article/ETI/EXTRACT-TRANSFORM-INFER.md`](../article/ETI/EXTRACT-TRANSFORM-INFER.md) | Claims falsables H_T / H_I / H_chunk; puente Complexometrum. |
| [`article/ungraph.md`](../article/ungraph.md) | Artículo: RQs, protocolo, ET vs ETI. |
| [`project/Agent_Instructions.md`](../project/Agent_Instructions.md) | Backlog de producto: operaciones de grafo, pipeline, init, minería, consolidate, agente. |
| Esta página | **Roadmap integrado** + alineación técnico-científica de lo que se prueba. |
| [`DEVELOPMENT_WORKFLOW.md`](DEVELOPMENT_WORKFLOW.md) | Ramas, tags, Conventional Commits, etiquetas, plantillas de issue/PR. |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Entrada corta para colaboradores; el detalle está en `DEVELOPMENT_WORKFLOW`. |

---

## Visión técnico-científica (qué queremos probar)

### ETI como contrato modular (no como un motor fijo)

Extract → Transform → Inference son **módulos sustituibles** bajo un mismo patrón de procesamiento de información. Lo estable es el **I/O esperado** (representaciones + hechos anclados + trazas), no el mecanismo interno.

**Abstraer Infer ≠ generalizar el diseño de inferir.** spaCy/NER (u otra implementación en Ungraph) es *una de miles* de formas de razonar sobre un contexto. No aspiramos a un mega-diseño que unifique todos los modos de razonamiento; aspiramos a un **slot** (`InferenceService` / artefacto de salida) donde familias distintas son enchufables y **comparables** bajo las mismas Y.

Familias de Infer (taxonomía viva; no exhaustiva ni normativa):

| Familia | Naturaleza | Ejemplos (horizonte) |
|---------|------------|----------------------|
| Simbólica / reglas | Determinista | Ontologías, grounding, constraints, verify estructural |
| Transductiva clásica | Det. o casi | NER spaCy, patrones léxicos, co-ocurrencia |
| Neural / LLM | No determinista (temp>0) o casi-det (temp=0) | Extracción LLM, graph transformer |
| Híbrida det↔no-det | Mixta | NER hints → LLM; propose→critique→verify |
| GraphRAG / topológica | Sobre el grafo | Híbrido semántico + expansión; GDS / métricas de red |
| Multiagente | Conversacional / roles | *n* agentes sobre el mismo contexto o artefacto |

Cada familia puede emitir el mismo tipo de artefacto medible (facts/rels/trazas o respuestas a tarea). Los internos (tokens, hops, autocritica, ranking) son **covariables**, no el veredicto.

- **Capa A — Contrato ETI:** ¿cada etapa produjo un artefacto medible?  
- **Capa B — Calidad de razonamiento / tarea:** ¿qué tan bien resolvió claims/preguntas? (misma vara det / no-det / híbrido / multiagente).  
- **Covariables:** coste, pasos, ventana, novedad percibida — para explicar, no para mover la portería.

Frase de gobierno: *primero un ETI medible y falsable end-to-end; luego, sobre artefactos que pasan el gate, comparar cómo distintos sistemas razonan —sin pretender que hay una única forma correcta de Infer.*

### Siguiente camino riguroso (orden científico)

No ampliar superficie (MCP, más agentes, más UI) hasta cerrar la evidencia mínima del patrón:

1. **Contrato I/O de Infer** — ✅ [`concepts/inference-slot.md`](concepts/inference-slot.md) (slot, no mega-diseño).  
2. **Y discriminativas** — ✅ recall Neo4j + probes top-k.  
3. **Oleada-2 = H_I** — ✅ PASS seed KG.  
4. **Congelar Capa 0** — ✅ `capa0_artifact.json`.  
5. **Oleada-3 = familias de Infer** — ✅ `ner` vs `pattern` (LLM opcional).  
6. **H_chunk / H_T** — ✅ doekit online; AC débilmente discriminativa; latency sí; H_T no afirmable en seed.  
7. **Complejidad / Complexometrum** — pendiente; requiere Y de tarea más variables / más dominios.

### Complexometrum ↔ Ungraph (complejidad de data no estructurada)

**Complexometrum** (*Data-Complexity-Representations*) mide hoy $C(D)$ sobre datos **tabulares/supervisados**. El planteamiento en [`article/ETI/EXTRACT-TRANSFORM-INFER.md`](../article/ETI/EXTRACT-TRANSFORM-INFER.md) es extender esa idea a **información no estructurada** (documento → chunks → embeddings → grafo → facts): ¿qué tan “difícil / inferible / útil” es un corpus tras E→T, y cómo correlaciona eso con error de Infer o de tarea?

| Dirección | Qué significa |
|-----------|----------------|
| **Ungraph como banco de prueba** | Los puntos de corte del pipeline ETI (matriz de embeddings de chunks, topología File–Page–Chunk, facts grounded/ungrounded) son *proyectores* donde se puede validar si un proxy de complejidad predice Y del scorecard (H_T / H_bridge del artículo). |
| **Feedback a la librería original** | Si aquí se valida un adaptador “unstructured → measurable matrix/graph” (p. ej. `from_embeddings`, features de chunks, métricas de grafo no-FCG), ese diseño puede **volver como feature** a Complexometrum para robustecer el instrumento más allá de lo tabular — sin romper su DoD v0.1. |
| **Qué no es** | Complexometrum no orquesta ETI ni sustituye `DomainScorecard` / DoE de arquitecturas. Es **diagnóstico de representación** en cortes del pipeline. |

**Orden:** cerrar H_I y Y discriminativas antes de invertir en el puente; luego oleada de screening (doekit) sobre proxies de complejidad vs error ETI. Detalle de fases A–D del instrumento: nota ETI + repo Complexometrum (`project/future/ISSUE_ETI_UNSTRUCTURED_BRIDGES.md` si existe en ese árbol).

### Gates experimentales (criterio mínimo sensato)

| Gate | Pregunta | Criterio (P0 `knowledge_graphs`) |
|------|----------|----------------------------------|
| **Corrida válida** | ¿El scorecard E2E es interpretable? | Y no vacías en E, T, I/tarea, eff; E+T no rotos; si Infer≠none → facts anclados (`evidence_coverage`>0) |
| **H_I (claim científico)** | ¿Infer aporta frente a solo ET? | Transform fijado; Neo4j+spaCy real; `ner` > `none` en recall de grafo **y** probe-QA sobre **top-k recuperado** no colapsa |
| **Razonadores (después)** | ¿Qué motor Infer/Task es mejor? | Mismo artefacto (`run_id`/snapshot); mismas Y de capa B; coste aparte |

Detalle operativo y DoE: [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md). Oleadas y horizonte C: [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md).

### Capas del espacio experimental (no un megafactorial)

```text
Capa 0 — Artefacto ETI     chunking, embed, infer, grafo     ← H_I ahora (Neo4j + spaCy)
Capa 1 — Recuperación      text / vector / hybrid, k         ← pareado o bloqueado
Capa 2 — Razonador         LLM / agente / verify weights     ← solo si Capa 0 pasó gate
```

Prohibido mezclar factores de agente (Capa 2) en la oleada que cierra H_I. Aún no sabemos qué knobs mejoran el razonamiento; el DoE (`doekit`) cribárá factores **cuando** las Y discriminen.

### Hipótesis en juego (pre-registro vivo)

| Id | Claim | Estado |
|----|-------|--------|
| **H_I** | Infer (`ner`) > ET (`none`) en grafo anclado + tarea, Transform fijo | **Cerrada (PASS)** seed KG; ver `hi_wave_verdict.json` |
| **H_chunk** | Estrategia/tamaño de chunk mejora retrieval a igual presupuesto | **Medido (débil en AC)**; doekit retiene `chunk_size` en latency (R²≈0.98); AC solo cae en 256+vector+k=1 |
| **H_T** | Proxies de transform predicen QA aguas abajo | **No afirmable** en seed (entity_recall constante con Infer fijo) |
| Razonadores | Variaciones det/no-det / multiagente son comparables vía Y de capa B | Oleada-3 base (`ner`/`pattern`); LLM/multiagente opcionales |

### Cierre MVP medible (loop único)

El cierre priorizado no separa “A sin C”: Ungraph debe habilitar experimentos **reproducibles, falsables y parametrizables** por arquitectura (`GraphPattern` + chunking × inference × rag × verify).

1. **Contrato de corrida** — `ExperimentRun` + `DomainScorecard` + fila plana DoE (`ungraph/evaluation/`).  
2. **DoE con doekit** — extra `ungraph[experiments]`; `recommend/screening → run → analyze → propose` ([`scripts/run_domain_pipeline.py`](../scripts/run_domain_pipeline.py)).  
3. **Dogfood P0** — [`benchmarks/domains/knowledge_graphs/`](../benchmarks/domains/knowledge_graphs/).  
4. **Oleada-1 (hecho, offline)** — screening D-optimal; señal dominante ET vs ETI; Y RAG aún no discriminativa.  
5. **Oleada-2 (hecho)** — **H_I** PASS en Neo4j + spaCy; wipe reproducible; Y desagregadas (grafo + tarea).  
6. **Capa 0 congelada (hecho)** — `capa0_artifact.json` + reload wipe→re-ingest.  
7. **Oleada-3 (hecho)** — `ner` vs `pattern` sobre capa0; Y capa B + latencia; LLM opcional vía `--families ner,llm`.  
8. **C5 + D6 + cierre loop (hecho)** — slot Infer documentado; DoE H_chunk con doekit; `pipeline_closure.json`.  
9. **Siguiente (ops / ampliación)** — A10 CI; E6–E7 git; 2º dominio o probes más duros; F5 si Y de tarea varían más.

---

## Checklist de estado (qué tenemos / qué no)

Leyenda: **[x]** listo · **[~]** parcial / offline / experimental · **[ ]** no listo.  
Actualizar esta sección cuando cierre una oleada o un gate. Fecha de foto: **2026-08-10** (A10 CI ETI + E6 README).

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
| A10 | Suite ETI/topología/e2e **versionada y en CI** | [x] | job CI `eti-measurable`; `tests/suites/eti_unit.txt` + offline DoE smoke; `.gitignore` ya no tapa `scripts/*.py` |

### B. Y discriminativas (calidad de medición)

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| B1 | Probe-QA / containment offline | [x] | `probe_qa_eval.py` (hoy sobre corpus → poco discriminativo) |
| B2 | Probe-QA / hit@k sobre **top-k recuperado** (SearchService) | [x] | `evaluate_answer_containment_topk` + SearchService |
| B3 | `entity_recall` / `relation_pair_recall` **desde Neo4j** | [x] | `neo4j_gold_metrics.py` |
| B4 | `evidence_coverage` desde provenance / `DERIVED_FROM` en grafo | [x] | cableado en runner online |
| B5 | Latency por fase en scorecard | [x] | `efficiency.latency_*` en offline |
| B6 | DeepEval como juez externo (anti-circularidad) | [~] | extra `ungraph[eval]`; no es gate de H_I |

### C. Contrato Infer (slot, no mega-diseño)

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| C1 | ABC `InferenceService` (entities/rels/facts) | [x] | `domain/services/inference_service.py` |
| C2 | Instancia transductiva spaCy (`ner`) | [x] | `spacy_inference_service.py` + extras `infer*` |
| C2b | Instancia simbólica léxica (`pattern`) | [x] | `lexical_pattern_inference_service.py` (oleada-3) |
| C3 | Instancia LLM (experimental) | [~] | `llm_inference_service.py` + LangGraph lineal |
| C4 | Control ET `inference=none` en factories/runner | [x] | online: `inference_service=None` tras factory |
| C5 | Doc I/O del slot (qué debe emitir cualquier módulo + `extraction_method`) | [x] | [`concepts/inference-slot.md`](concepts/inference-slot.md) |
| C6 | Taxonomía de familias Infer en plan (simbólica, neural, híbrida, …) | [x] | esta página § visión |
| C7 | Hybrid `inference_mode=hybrid` | [ ] | `NotImplementedError` explícito |

### D. Gates y claims científicos

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| D1 | Gate “corrida válida” definido | [x] | § Gates experimentales |
| D2 | Gate H_I definido (grafo + tarea) | [x] | § Gates / ROADMAP oleada-2 |
| D3 | **H_I cerrado** en Neo4j + spaCy (éxito o recorte) | [x] | oleada-2 PASS: `entity_recall` 0→0.47; AC@k=1.0; ver `reports/hi_wave_verdict.json` |
| D4 | Artefacto Capa 0 congelado (`run_id`/snapshot reutilizable) | [x] | `capa0_artifact.json`; reload=`wipe→re-ingest` pinned; gate match en `reload_verdict.json` |
| D5 | Oleada-3: ≥2 familias Infer, mismas Y capa B | [x] | `ner` vs `pattern` sobre capa0; `family_wave_verdict.json` COMPARED |
| D6 | H_chunk / H_T ejecutables con Y reales | [x] | doekit `doe_h_chunk.yaml` online; AC∈[0.875,1.0]; `chunk_size` retenido en **latency**; H_T flat (Infer fijo) |
| D7 | Pre-registro hipótesis en docs | [x] | PLAN_MAESTRO + article ETI |

### E. Núcleo producto / ops (A–B librería)

| # | Ítem | Estado | Evidencia / nota |
|---|------|--------|------------------|
| E1 | Ingest E→T→persist Neo4j | [x] | `ingest_document` + composition root |
| E2 | Búsqueda text / vector / hybrid | [x] | `neo4j_search_service` / API pública |
| E3 | Validador topología File–Page–Chunk / NEXT_CHUNK | [x] | `graph_topology_validate` |
| E4 | CLI setup / graph / ingest | [~] | existe; parte del paquete aún dispersa en git |
| E5 | CLI infer / report | [~] | parcial / stub según comando |
| E6 | Claims README alineados (Infer MVP = spaCy; LLM experimental) | [x] | README: slot Infer + `ner`/`pattern`/`llm`; apunta a PLAN + inference-slot |
| E7 | Docs plan/producto versionados como fuente de verdad en git | [~] | `scripts/` un-ignore; falta `git add`+commit de PLAN/suite/runner (pedir commit) |

### F. Fuera del cierre de claim (no bloquear H_I)

| # | Ítem | Estado | Nota |
|---|------|--------|------|
| F1 | MCP Ungraph | [~] | exploratorio (`mcp_servers/`) — C4 |
| F2 | Report UI / yFiles | [~] | DX, no gate científico |
| F3 | Multiagente / AGENT_ARCHITECTURE | [~] | propuesta; Capa 2 |
| F4 | SPARQL tools curados / ontologías remotas | [~] | CHECKPOINT; no H_I |
| F5 | Puente Complexometrum (complejidad no estructurada → validar en ETI → feature de vuelta) | [ ] | Tras H_I + Y reales; ver § Complexometrum |
| F6 | Recomendación automática de arquitectura (C3) | [ ] | tras factores retenidos reales |

### Lectura rápida del checklist

- **Listo para medir offline + online (código):** A1–A9, B2–B4, C1–C2, C4, D1–D2, D7.  
- **Claim H_I (oleada-2):** cerrado con PASS en seed `knowledge_graphs` / `kg_survey.md` (Neo4j + spaCy NER).  
- **Capa 0 (D4):** congelada en `reports/capa0_artifact.json` (`run_id` NER H_I); reload = wipe→re-ingest pinned (sin dump Neo4j).  
- **Oleada-3 (D5):** `ner` vs `pattern` COMPARED (`family_wave_verdict.json`).  
- **C5:** contrato I/O en [`concepts/inference-slot.md`](concepts/inference-slot.md).  
- **D6 / DoE:** probes localizados + containment estricto; `doe_h_chunk.yaml` → screening online → analyze; ver `pipeline_closure.json`.  
- **Cierre científico seed KG:** loop ExperimentRun↔scorecard↔doekit↔online **cerrado**; claims H_chunk (AC) y H_T siguen débiles — no inflar.  
- **A10:** CI `eti-measurable` (unit ETI + offline DoE smoke).  
- **E6:** README alineado al slot Infer. **E7:** listo para track; pendiente commit explícito.  
- **Siguiente:** commit/PR del paquete medible; o 2º dominio / F5 cuando Y de tarea varíen más.  
- **Comandos H_chunk:**  
  ```bash
  … --design screening --doe-path doe_h_chunk.yaml --mode online --redesign
  … --design run --mode online --doe-path doe_h_chunk.yaml
  … --design analyze --doe-path doe_h_chunk.yaml --response answer_correctness
  … --design analyze --doe-path doe_h_chunk.yaml --response latency_s
  ```

### Skills y subagentes (playbook)

| Recurso | Rol |
|---------|-----|
| Skill [`eti-experiment-science`](../.claude/skills/eti-experiment-science/SKILL.md) | DoE, gates, oleadas, gaps |
| [`checklist-gaps.md`](../.claude/skills/eti-experiment-science/checklist-gaps.md) | Desarrollo / pruebas / consideraciones faltantes |
| Agente [`ungraph-eti-science`](../.cursor/agents/ungraph-eti-science.md) | Ejecutar oleada-2 / auditar checklist científico |
| Agente [`ungraph-dev-skills`](../.cursor/agents/ungraph-dev-skills.md) | Orquestar cualquier skill del cluster |

## Roadmap técnico (síntesis)

1. **Patrones limpios** — Un solo contrato declarativo (`GraphPattern`); alinear [`predefined_patterns.py`](../ungraph/domain/value_objects/predefined_patterns.py) con propiedades reales en Neo4j; invariantes `NEXT_CHUNK` por `source_document_uid`; validador post-ingesta (`ungraph.utils.graph_topology_validate`).
2. **Tests de topología** — Integración Neo4j en CI (`Integration & E2E`): N documentos sintéticos, conteos `File`/`Page`/`Chunk`, validación `NEXT_CHUNK`; E2E ingest → `text_search`. Variables `UNGRAPH_NEO4J_*` o `NEO4J_*` en [`tests/conftest.py`](../tests/conftest.py).
3. **Evaluación + DoE** — `ungraph[eval]` (DeepEval) + `ungraph[experiments]` (doekit); métricas E/T/I/RAG y screening de factores ([`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md)).
4. **Matriz GraphRAG** — Tabla patrón de referencia ↔ API Ungraph ↔ prerequisitos Neo4j ([`theory/sp-graphrag.md`](theory/sp-graphrag.md) y guías).
5. **Infer (ETI)** — Factories claras: spaCy (`infer`), Ollama/LLM existente, **OpenAI/BYO** vía env (`UNGRAPH_OPENAI_*`); tests condicionales; evolución alineada con [`CHECKPOINT_INFERENCE_PIPELINE.md`](CHECKPOINT_INFERENCE_PIPELINE.md) (contexto de documento, preguntas de dominio, presupuesto de modelo).
6. **CLI operativa (`ungraph[cli]`)** — Typer; dependencia opcional; **sin acoplar** el núcleo: comandos delegan en [`dependencies.py`](../ungraph/application/dependencies.py), [`Neo4jIndexService`](../ungraph/infrastructure/services/neo4j_index_service.py), casos de uso y [`graph_topology_validate`](../ungraph/utils/graph_topology_validate.py). El binario `ungraph` requiere instalar el extra; sin él, mensaje explícito al ejecutar.

## CLI (`ungraph[cli]`)

- **Instalación:** `pip install 'ungraph[cli]'` — registra el comando `ungraph` ([`pyproject.toml`](../pyproject.toml) `[project.scripts]`).
- **Principio:** la CLI es **adaptador de orquestación**. No duplica reglas de negocio ni Cypher de producto salvo glue mínimo; la misma orientación aplicará a futuros comandos de inferencia (“minar”, “consolidate”, agente): deben **invocar** casos de uso o servicios de aplicación, no sustituirlos.
- **Implementación:** paquete [`ungraph/cli/`](../ungraph/cli/); entrada [`entrypoint.py`](../ungraph/cli/entrypoint.py); comandos en [`commands/setup.py`](../ungraph/cli/commands/setup.py), [`graph_cli.py`](../ungraph/cli/commands/graph_cli.py), [`ingest_cli.py`](../ungraph/cli/commands/ingest_cli.py), [`infer_cli.py`](../ungraph/cli/commands/infer_cli.py).
- **Comandos actuales (MVP):** `ungraph setup --database-init [--indexes]` / `ungraph setup --wipe`; `ungraph graph --ping` / `--validate-topology` / `--setup-indexes` / `--drop-indexes`; `ungraph ingest --path` (archivo o URL) / `--folder` (paralelo + **tqdm**); `ungraph infer --kmining|...` (stub); `add_completion=False` (sin opciones Typer de *completion*). Opción `--database/-d` en `setup` / `graph` / `ingest` para la base Neo4j.
- **Constraints / DDL avanzado:** hasta acordar DDL versionado (skill **kg-schema**), la CLI no aplica `CREATE CONSTRAINT` masivo; índices estándar vía `Neo4jIndexService` o `ungraph setup --database-init`.

### Fases CLI ↔ Agent_Instructions ↔ Infer

Orden sugerido de desarrollo (tabla viva; detalle en [`project/Agent_Instructions.md`](../project/Agent_Instructions.md)):

| Fase | Comandos / entregable | Neo4j | Infer / LLM | Notas |
|------|------------------------|-------|---------------|--------|
| 1 (hecho) | `setup` (init + wipe), `graph` (--ping, índices, topología), `ingest` (--path / --folder con tqdm) | Sí | No obligatorio | Ver `ungraph/cli/commands/`. |
| 2 | Presets GraphRAG / patrones (`predefined_patterns`, docs sp-graphrag) | Sí | No | Documentación y ejemplos por patrón. |
| 3 | `init` batch, informes de sanity (conteos, conectividad), validación Cypher de patrón | Sí | Opcional | Ampliar reportes junto a [`graph_topology_validate`](../ungraph/utils/graph_topology_validate.py). |
| 4 | `config` (documentar / editar `.env`, alineado a `Settings`) | — | — | No duplicar modelo de settings. |
| 5 | Minería de conocimiento, consolidate, agente conversacional | Sí | Sí (típico) | Comparte línea con CHECKPOINT (preguntas de dominio, contexto de documento, [`create_inference_service`](../ungraph/application/dependencies.py)); la CLI solo dispara casos de uso. |

### Referencias cruzadas

- **Infer:** mismas factories y políticas que el API Python; extensiones futuras de la CLI deben pasar por el composition root cuando exista caso de uso.
- **Skills:** `eti-pipeline`, `cypher-craft`, `graphrag-pattern`, `ungraph-test`, `kg-schema` siguen siendo la guía técnica; la CLI no sustituye a los skills, los **expone** en terminal cuando tiene sentido.

## Skills recomendados (desarrollo asistido)

- **eti-pipeline** — chunking, ingest, embeddings, inferencia.  
- **cypher-craft** — consultas Neo4j, índices, saneamiento.  
- **graphrag-pattern** — retrievers y patrones de búsqueda.  
- **ungraph-test** — niveles unit / integration / e2e, marcadores pytest.  
- **kg-schema** — nodos, relaciones, constraints.

Para orquestación entre skills del repo, usar el agente **`ungraph-dev-skills`** cuando la tarea cruce esquema + ETI + Cypher.

## Referencias de implementación clave

- Ingestión: [`ungraph/application/use_cases/ingest_document.py`](../ungraph/application/use_cases/ingest_document.py).  
- Grafo lexical + linaje: [`ungraph/utils/graph_operations.py`](../ungraph/utils/graph_operations.py).  
- Inferencia: [`ungraph/domain/services/inference_service.py`](../ungraph/domain/services/inference_service.py), [`spacy_inference_service.py`](../ungraph/infrastructure/services/spacy_inference_service.py), [`llm_inference_service.py`](../ungraph/infrastructure/services/llm_inference_service.py).  
- Búsqueda: [`ungraph/infrastructure/services/neo4j_search_service.py`](../ungraph/infrastructure/services/neo4j_search_service.py).  
- Composition root: [`ungraph/application/dependencies.py`](../ungraph/application/dependencies.py).  
- CLI opcional (Typer): [`ungraph/cli/`](../ungraph/cli/).

---

*Documento introducido para cerrar la brecha entre visión (§6.3 / §8 de VISION) y tareas de ingeniería concretas.*
