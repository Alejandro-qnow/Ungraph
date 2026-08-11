# Transformación — representaciones, featurización y complejidad

**Idioma:** español. Archivo canónico compartido (sin prefijo `sp-`).

Audiencia: research / developer. Espina: [`eti-spine.md`](eti-spine.md).

## Motivation

Tras adquirir evidencia, el cuello de botella epistémico suele ser la **representación**: qué unidades se pasan al razonador, con qué vecindad y qué geometría. Chunking, embeddings y topología léxica no son detalles de ingeniería inocuos; la literatura de RAG y chunking muestra sensibilidad empírica fuerte (I18; estudios de chunking/embedding en el whitepaper E15–E16).

Queremos transformar datos brutos en formas donde se pueda *medir* si hay más **dato**, más **información** usable para una tarea, o más **conocimiento** candidato — y cuánta **complejidad** carga cada corte. Sin eso, Infer y retrieval mezclan fracaso de representación con fracaso de razonamiento.

## Theory

### Tipos de transformación (familias)

| Tipo | Qué hace | Salida típica | Por qué importa |
|------|----------|---------------|-----------------|
| **Limpieza / normalización** | Ruido, encoding, boilerplate | Texto canónico | Reduce evidencia espuria |
| **Segmentación (chunking)** | Parte en unidades recuperables/inferibles | `Chunk` + metadata | Define el átomo de provenance y de top-k |
| **Featurización densa** | Embeddings / vectores | Vectores por chunk (u otra unidad) | Espacio de similitud; ANN |
| **Topología léxica / documental** | Enlaza File–Page–Chunk (u homólogos) | Grafo de contigüidad/jerarquía | Provenance y expansión determinista |
| **Índices / resúmenes de comunidad** | Agrega para retrieval global | Summaries, clusters | GraphRAG Transform+Interface (I04) |
| **Proyectores de complejidad** | Matrices/grafos medibles desde cortes ETI | Proxies $C(D)$ u homólogos | Puente Complexometrum (trayectoria) |

### Data → información → conocimiento (lectura operativa)

No son ontologías rígidas; son **capas de pregunta medible**:

| Capa | Pregunta | Proxy en Ungraph (orientativo) |
|------|----------|--------------------------------|
| **Dato** | ¿Hay unidades persistidas y contables? | `n_chunks`, nodos/rels estructurales |
| **Información** | ¿Las unidades discriminan para recuperación/tarea? | hit@k / `answer_correctness` @ top-k; calidad de chunking |
| **Conocimiento (candidato)** | ¿Hay beliefs/facts anclados con evidencia? | `entity_recall`, `relation_pair_recall`, `evidence_coverage` |
| **Complejidad** | ¿Qué tan “difícil/inferible” es el corte? | Proxies futuros (embeddings, topología); **will be** vía Complexometrum |

**Featurización** aquí = evolución del dato hacia un estado usable por Infer o por retrieval (chunks + vectores + topología), no un feature store genérico. DeepDive trata features/evidence como entrada a inferencia probabilística (E1); Ungraph expone el corte Transform como superficie experimental (H_chunk, H_T).

### is vs will be

| | |
|--|--|
| **is** | Estrategias de chunking configurables; embeddings; grafo léxico File–Page–Chunk; patrones GraphRAG parciales; DoE H_chunk medido en seed (AC débilmente discriminativa; latency sensible a `chunk_size`); H_T **no afirmable** en seed con Infer fijo |
| **will be** | Proxies de complejidad no estructurada validados contra Y ETI; feedback a Complexometrum; community summaries más ricos; ontology learning como Transform/Inference (I17) |

## In Ungraph

- Transform ocurre **antes** del slot Infer en ingesta; el servicio Infer no debe depender de Neo4j/LangChain en `domain/`.
- Scorecard: **E** (chunking) y parte estructural; Y de retrieval en Capa 1. No mezclar factores de agente (Capa 2) en oleadas que cierran H_I o H_chunk.
- Complejidad: ver § Complexometrum en [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) — puente posterior, no bloqueante de H_I.
- Interface GraphRAG (resúmenes/comunidades como Transform+retrieve): [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md) — no redefine conocimiento.
- DoE: `ungraph[experiments]` + [`../experiment/BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md).

## Open claims (falseables)

### Claim H_T_proxy

- **Enunciado:** Proxies medibles de Transform (p. ej. estadísticos de chunks/embeddings/topología) predicen error o Y de QA aguas abajo a igual Infer.
- **Predicción observable:** Correlación estable proxy↔Y en ≥1 dominio con variación real de representación; no constante trivial.
- **Protocolo mínimo:** Infer fijo; variar chunking/embed; registrar proxies + scorecard. Estado actual: H_T no afirmable en seed KG — ver plan maestro. Ampliar dominio/probes si se retoma.
- **Falsación:** Si entity_recall u otras Y permanecen constantes o el proxy no rankea arquitecturas, el claim se rechaza o se acota.
- **Reproducibilidad:** Filas DoE + `DomainScorecard`; reports versionados.

### Claim H_chunk_disc

- **Enunciado:** Estrategia/tamaño de chunk mejora retrieval a igual presupuesto de Infer.
- **Predicción observable:** Diferencias en `answer_correctness` @ top-k (o latency como covariable) al variar `chunk_size`/`strategy` con Infer fijo.
- **Protocolo mínimo:** DoE H_chunk con doekit (`scripts/run_domain_pipeline.py`, screening/run/analyze). Ver [`PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) § H_chunk.
- **Falsación:** Si AC no discrimina en el seed y solo latency responde, el claim de *calidad de tarea* queda débil/acotado (como en la foto actual del plan).
- **Reproducibilidad:** `doe_h_chunk.yaml` + `results.csv` / `analysis.json` / `pipeline_closure.json`.
