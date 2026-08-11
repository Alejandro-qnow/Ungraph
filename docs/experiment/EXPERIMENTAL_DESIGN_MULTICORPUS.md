# Diseño experimental maestro — multicorpus, dificultad de probes y complejidad

**Capa ZEN:** `experiment/` — lineamientos, metas, diseños DoE, resultados esperados y pasos.  
**Audiencia:** research + developer.  
**Última revisión:** 2026-08-11  
**Rama de trabajo:** `feature/research-eti-complexity`  
**Índice operativo:** [`RESEARCH_TRACK.md`](RESEARCH_TRACK.md) · Gates seed: [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) · DoE how-to: [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md) · Fundamento $C_k$: [`../research/COMPLEXITY_UNSTRUCTURED.md`](../research/COMPLEXITY_UNSTRUCTURED.md)

| | |
|--|--|
| **is** | Seed mono-doc (`kg_survey.md`) con AC saturado; H_I PASS en grafo; staging/packs **no** implementados; complejidad exportable pero no por celda DoE. |
| **will be** | Packs multicorpus + staging pre-grafo; taxonomía de dificultad de probes; DoE multidocumento; $C_k$ covariable por celda; Y de tarea no saturada. |
| **Open claims** | Ver § Open claims (este doc + PLAN). Seed ≠ PRODUCT §5. |

Este documento **no** afirma resultados nuevos: fija el protocolo con el que se generarán. Resultados medidos viven en `benchmarks/domains/…/reports/` (y `reports/research/`); promoción a [`../validation/`](../validation/) solo bajo PRODUCT §5.

---

## 1. Motivation — por qué este diseño

### Diagnóstico (seed)

1. **AC saturado:** `answer_correctness` ≈ 1.0 con `none` y `ner` → la Y de tarea no discrimina arquitecturas.  
2. **Gold mono-anclado:** probes y entidades curados sobre un documento seed; el manifest lista más papers, pero sin gold/pack multi-doc.  
3. **Facts medidos como cobertura de grafo + provenance**, no como utilidad de razonamiento multi-hop / inter-documento.  
4. **Complejidad (F5)** existe como export, no como covariable sistemática de cada celda DoE.

### Preguntas de investigación (programa)

| Id | Pregunta |
|----|----------|
| **Q1** | ¿Cómo cambia el razonamiento (y el error) cuando el grafo se construye desde **varios documentos** frente a uno solo? |
| **Q2** | ¿De qué depende ese cambio: tamaño del grafo, solape temático, hops, patrón de recuperación, familia Infer, complejidad de la proyección $C_k$? |
| **Q3** | ¿Qué hace “difícil” una pregunta (1-hop / multi-hop / inter-grafo / contexto) y cómo calibrar probes para que Y deje de saturar? |
| **Q4** | ¿Los proxies de complejidad por celda predicen error de Infer/tarea mejor que azar en packs multicorpus? |

### Metas (producto científico, no release C)

| Meta | Criterio de hecho (mínimo) |
|------|----------------------------|
| **M1 — Packs reproducibles** | ≥1 pack multicorpus versionado con staging precargable (chunks/emb/recipe) sin re-Extract obligatorio |
| **M2 — Grafo más rico** | Tras ingest pack: crecimiento medible de nodos/rels vs seed; stats en scorecard |
| **M3 — Probes calibrados** | Taxonomía de dificultad en gold; AC@k con valores en banda no-degenerada (p.ej. media ∈ [0.3, 0.85] en baseline ET) |
| **M4 — DoE multidoc** | Diseño doekit con factor `corpus_pack` (o equivalente) + Infer/rag/chunk; analyze sobre Y desagregadas |
| **M5 — Complejidad a la par** | Cada `ExperimentRun` / celda escribe $C_k$ (al menos $\Pi_{\mathrm{emb}}$) junto a Y |
| **M6 — Evidencia, no §5** | Veredictos JSON en `reports/research/`; sin promoción a “validado” hasta confrontación §5 |

---

## 2. Theory — dificultad de pregunta y razonamiento multidocumento

### 2.1 Qué es (y no es) “pregunta difícil”

**No** es “suena técnica”. **Sí** es: exige un camino de evidencia que el sistema puede fallar de formas controladas.

| Nivel | Nombre | Definición operativa | Fallo típico si el sistema es débil |
|-------|--------|----------------------|-------------------------------------|
| **D0** | Lexical / easy | Respuesta en ventana local; keyword overlap alto | Casi nunca (satura AC) |
| **D1** | 1-hop | Un hecho / una arista documentada en **un** doc | Infer o retrieval local fallan |
| **D2** | Multi-hop intra-doc | ≥2 hechos encadenados en el mismo documento | Chunking rompe cadena; falta arista |
| **D3** | Multi-hop inter-doc | Encadenar hechos de **≥2 documentos** del pack | No hay puente entre docs; retrieval mono-doc |
| **D4** | Inter-grafo / contexto | Requiere cruzar subgrafos (p.ej. temas, patrones) o desambiguar contexto (mismo nombre, distinto doc) | Confusión de entidades; contexto equivocado |
| **D5** | Negación / contraste | Respuesta exige excluir distractor presente en top-k | Containment falso positivo |

**Calibración previa a DoE (obligatoria):**

1. Etiquetar cada probe con `difficulty ∈ {D0…D5}`, `hop_count`, `docs_required[]`, `evidence_span_ids[]` (staging).  
2. Correr baseline ET (`inference=none`) y ETI (`ner` o `pattern`) **sin** barrer factores.  
3. Aceptar el set de probes solo si:  
   - D0 no domina el set (>30% del total → recortar);  
   - media AC@k baseline ET < 0.9;  
   - al menos 30% de probes son D2+;  
   - ≥20% son D3+ cuando el pack es multicorpus.

### 2.2 Razonamiento multidocumento (objetos)

```text
Pack P = {doc_1 … doc_n}
  → staging Π (chunks, emb, recipe)
  → grafo G_P (unión / merge de entidades)
  → tarea: probes con docs_required ⊆ P
```

Dependencias candidatas del error $e$ (pre-registro; no afirmar causalidad aún):

| Factor | Hipótesis de dependencia |
|--------|---------------------------|
| $\|V\|, \|E\|$ de $G_P$ | Más grafo ≠ mejor tarea; puede subir ruido |
| Solape léxico entre docs | Alto solape → fácil D3 falso; bajo solape → D3 real más duro |
| Familia Infer | `pattern` vs `ner` vs `llm` cambian puente inter-doc |
| RAG mode + $k$ | text/vector/hybrid condicionan si llegan spans de docs distintos |
| $C_k(\Pi)$ | Proyecciones más “complejas” correlacionan con más error en D3–D4 |

### 2.3 Utilidad de Facts (criterios ampliados)

Hoy (**is**): `entity_recall`, `relation_pair_recall`, `evidence_coverage`.

**will be** (diseño; implementar por oleadas):

| Criterio | Pregunta | Métrica |
|----------|----------|---------|
| Cobertura gold | ¿Está el concepto/par en $G$? | recalls actuales |
| Anclaje | ¿El fact tiene provenance a chunk/doc? | `evidence_coverage` + `doc_id` |
| Soporte de probe | ¿Algún fact del camino del probe está en $G$? | `fact_support@probe` (nuevo) |
| Camino multi-hop | ¿Existe path documentado para D2/D3? | `path_hit` vs `expected_inferences` |
| Utilidad marginal | ¿Quitar facts de un doc tumba AC en probes D3? | ablación por `doc_id` |

---

## 3. In Ungraph — artefactos y diseños

### 3.1 Estructura de packs y staging (pre-grafo)

Evita re-Extract; permite cambiar Infer / patrón / rag sobre la misma proyección.

```text
benchmarks/domains/knowledge_graphs/
  corpus/                         # fuentes crudas (is)
  packs/
    pack_seed.yaml                # mono-doc actual (kg_survey)
    pack_kg_multi_v1.yaml         # will be — multi-doc
  staging/                        # will be — versionado
    <doc_id>/
      chunks.jsonl                # id, text, offsets, source_document_uid
      embeddings.npy              # opcional; o path en meta
      transform_meta.json         # chunk_size, strategy, model emb
      pattern_ref.yaml            # GraphPattern / recipe id
  gold/
    gold_seed.json                # actual gold.json (migrar o symlink lógico)
    gold_pack_kg_multi_v1.json    # probes D1–D4 + entities multi-doc
  reports/research/
    multicorpus/                  # veredictos de este programa
```

**Contrato de pack YAML (mínimo):**

```yaml
pack_id: pack_kg_multi_v1
docs:
  - id: kg_survey
    path: corpus/kg_survey.md
  - id: graphrag_edge
    path: corpus/2404.16130_graphrag.md
  # …
gold: gold/gold_pack_kg_multi_v1.json
default_pattern: FILE_PAGE_CHUNK
staging_root: staging/
complexity_projections: [emb, chunk_table]  # por celda
```

### 3.2 Factores DoE (diseños)

Usar **doekit** (`ungraph[experiments]`); no producto cartesiano ad-hoc. Infer = slot.

#### Diseño A — Calibración de dificultad (sin barrer arquitectura)

- **Fijo:** pack, pattern, chunk defaults, `inference=ner`.  
- **Salida:** tabla probe × AC@k × dificultad; gate de calibración §2.1.  
- **Artefacto:** `reports/research/multicorpus/probe_calibration.json`.

#### Diseño B — Multidocumento × Infer (H_multi / extensión H_I)

| Factor | Niveles (inicial) |
|--------|-------------------|
| `corpus_pack` | `pack_seed` \| `pack_kg_multi_v1` |
| `inference` | `none` \| `ner` \| `pattern` |
| `rag` | `text` \| `vector` \| `hybrid` |
| `top_k` | 3 \| 5 \| 10 |

- **Y primarias:** `answer_correctness` **estratificada por dificultad** (AC@D1, AC@D2, AC@D3…), `entity_recall`, `relation_pair_recall`, `fact_support@probe`.  
- **Y secundarias / covariables:** `latency_*`, $\|V\|$, $\|E\|`, $C_{\mathrm{emb}}$, $C_{\mathrm{chunk}}$.  
- **Prohibido** como veredicto único: `composite_score`.  
- **Wipe** Neo4j entre celdas online.

#### Diseño C — Complejidad a la par (cada celda)

Para cada fila de B (y de H_chunk si se reabre):

1. Cargar o generar staging.  
2. `complexity_export` → $\Pi_{\mathrm{emb}}$ (+ chunk_table si existe).  
3. Proxy $C_k$ (al menos $d_{\mathrm{eff}}$, normas; luego familias Complexometrum).  
4. Adjuntar a `ExperimentRun` / fila CSV.  
5. Analyze: correlación / ranking $C_k$ vs error en D3–D4 (exploratorio hasta Open claim).

### 3.3 Notebooks y runner

| Pieza | Rol |
|-------|-----|
| [`../../scripts/run_domain_pipeline.py`](../../scripts/run_domain_pipeline.py) | Orquestación DoE (extender con `--pack`) |
| [`../../ungraph/notebooks/research/`](../../ungraph/notebooks/research/) | Step-by-step; no reimplementar DoE |
| NB futuros | `05_pack_staging.ipynb`, `06_probe_difficulty.ipynb`, `06_multicorpus_doe.ipynb` |

### 3.4 Resultados — dónde y qué forma tienen

| Resultado | Path | Contenido |
|-----------|------|-----------|
| Calibración probes | `reports/research/multicorpus/probe_calibration.json` | AC por D-level; aceptación/rechazo del set |
| DoE multicorpus | `…/design_multi.json`, `results_multi.csv`, `analysis_multi_*.json` | Factores retenidos por Y estratificada |
| Complejidad por celda | columna `c_emb_deff` (etc.) en results + `complexity/` por `run_id` | Covariables |
| Veredicto programa | `multicorpus_wave_verdict.json` | PASS/FAIL parcial por claim (abajo) |
| Seed histórico | `hi_wave_verdict.json`, `pipeline_closure.json` | **No pisar**; solo lectura |

**Lectura de resultados (reglas):**

- Reportar Y desagregadas y por dificultad.  
- N pequeño → no sobreinterpretar p-valores; priorizar deltas y retención doekit.  
- “Mejor arquitectura” solo si gana en Y pre-registrada en probes calibrados.

---

## 4. Open claims (falseables) — este programa

### Claim H_probe_calibration — **OPEN**

- **Enunciado:** Un set de probes etiquetado D0–D5 con ≥30% D2+ y ≥20% D3+ (pack multi) produce media AC@k < 0.9 bajo ET (`inference=none`) con el mismo top-k del diseño B.  
- **Falsación:** Si tras dos iteraciones de curación la media ET sigue ≥ 0.9, el instrumento de tarea se declara no discriminativo en este dominio y se cambia gold/corpus.  
- **Artefacto:** `probe_calibration.json`.

### Claim H_multi_doc_reasoning — **OPEN**

- **Enunciado:** En pack multicorpus, probes D3+ tienen AC@k sistemáticamente menor que D1 bajo la misma arquitectura; Infer (`ner`/`pattern`) mejora `fact_support` o path_hit frente a `none` sin colapsar D1.  
- **Falsación:** Si D3≈D1 en AC para todas las arquitecturas, no hay señal multidocumento (o el pack no exige cruce real).  
- **Protocolo:** Diseño B + wipe + gold multi.

### Claim H_I_seed_vs_product — **OPEN** (PLAN)

- Extiende el PLAN: confrontación no es solo “otro dominio”, también **pack multi** con gold propio bajo el mismo protocolo `--hi-wave` / diseño B.

### Claim H_chunk_task_Y — **OPEN / débil** (PLAN)

- Reabrir solo tras M3 (probes calibrados); si no, se mantiene el rechazo de causalidad de tarea en seed fácil.

### Claim H_bridge_complexity — **OPEN (des-diferido condicional)**

- **Enunciado:** $C_k$ por celda correlaciona con error en D3–D4 mejor que azar en ≥1 pack multi (y idealmente ≥2 packs/dominios).  
- **Condición para activar analyze:** M1+M3+M5.  
- **Falsación:** correlación nula/establemente negativa tras N celdas pre-registradas → acotar F5.

---

## 5. Pasos a seguir (orden de consecuencia)

```text
P0  Documentar este diseño + enlazar RESEARCH_TRACK / PLAN     ← este doc
P1  Spec staging + pack_seed / pack_kg_multi_v1 (YAML + dirs)
P2  Migrar/extender gold: dificultad D0–D5, docs_required, evidence spans
P3  Calibración probes (Diseño A) → probe_calibration.json
P4  Runner: --pack + load staging + skip Extract opcional
P5  Cablear complexity_export → columna por ExperimentRun (Diseño C)
P6  DoE multicorpus (Diseño B) online; reports/research/multicorpus/
P7  Notebooks 05–06; plots Y×dificultad×pack×C_k
P8  Veredicto multicorpus_wave_verdict.json; actualizar PLAN Open claims
P9  Solo entonces: 2º dominio o §5 / validation/
```

**Stop line:** no mezclar Capa 2 (agentes) en Diseños A–C; no usar composite como gate; no pisar veredictos seed.

---

## 6. Relación con el resto del canon

| Documento | Relación |
|-----------|----------|
| [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md) | Seed + A+B cerrados; este doc es el **programa post-cierre** (ciencia) |
| [`RESEARCH_TRACK.md`](RESEARCH_TRACK.md) | Oleadas operativas; apunta aquí como diseño maestro |
| [`BENCHMARK_ETI_DOMAINS.md`](BENCHMARK_ETI_DOMAINS.md) | Scorecard / doekit how-to; packs extienden “pipeline por dominio” |
| [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) | F5/C3 horizontes; H_bridge aquí se operacionaliza sin vender C |
| [`../research/COMPLEXITY_UNSTRUCTURED.md`](../research/COMPLEXITY_UNSTRUCTURED.md) | Fundamento $C_k$; este doc define *cuándo* se mide |

---

## 7. Resumen ejecutivo

Ampliamos el programa en dos inclusiones: (1) **multicorpus** con staging pre-grafo y grafo más rico para estudiar razonamiento inter-documento; (2) **dificultad de probes** como factor de diseño (D0–D5, hops, inter-grafo, contexto), calibrada antes del DoE. La complejidad va **a la par de cada celda**. El éxito no es “más papers ingeridos”, sino Y discriminativas + claims falseables con artefactos versionados bajo `reports/research/multicorpus/`.

*Actualizar este documento al cerrar P3/P6/P8 o al recortar un claim.*
