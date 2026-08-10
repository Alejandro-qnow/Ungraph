# Benchmark ETI end-to-end por dominio

> Cómo Ungraph demuestra —y mide— el patrón **Extract → Transform → Inference** sobre
> conocimiento real de un dominio, y cómo compara *arquitecturas* del pipeline de forma
> reproducible y honesta.

## 1. Motivación

Validar el pipeline sobre frases de juguete no dice si Ungraph **entiende** un dominio.
La prueba de fuego es: tomar un documento no estructurado (un *paper*), llevarlo por
E→T→I hasta el grafo, **razonar** sobre él, y medir la calidad del resultado con
métricas que permitan responder dos preguntas:

1. **¿El sistema construye conocimiento fiel?** (poco ruido, alta cobertura, respuestas ancladas)
2. **¿Qué arquitectura del pipeline es mejor para este dominio?** — cada pieza (chunking,
   motor de inferencia, patrón RAG, verify) tiene variantes cuyo efecto se mide
   **experimentalmente** (Diseño de Experimentos con `doekit`).

### Dogfooding como estrategia de validación

Priorizamos dominios que **son nuestras propias actividades**. Si Ungraph mina papers de
*grafos de conocimiento* o *arquitecturas cognitivas*, razona sobre el conocimiento que
él mismo encarna: podemos validar sus inferencias con criterio experto (gold barato) y
el sistema **se autovalida**. Un KG que no entiende papers de KGs no está listo.

## 2. Estructura "pipeline por dominio"

Cada dominio es un experimento reproducible y autocontenido:

```
benchmarks/domains/<dominio>/
  manifest.yaml   # fuentes de papers + arquitecturas a probar (chunking×inference×rag) + params
  corpus/         # papers normalizados (.md / .pdf / .html)
  gold.json       # entities, relation_pairs, graphrag_probe_queries(+answers), expected_inferences
  reports/        # scorecards por corrida/arquitectura (JSON + HTML)
```

El `gold.json` sigue el formato de `scripts/data/reference_corpus_gold.json`, extendido
con `expected_inferences` (razonamiento multi-hop) y respuestas a `probe_queries`.

## 3. Métricas globales — el *scorecard* end-to-end

Un objeto único (`ungraph.evaluation.scorecard.DomainScorecard`) **agrega** las métricas
por etapa del ETI + razonamiento, para comparar arquitecturas en una sola vista:

| Etapa | Métrica | Fuente (reutilizada) |
|---|---|---|
| **E** — ingesta+chunking | `chunking_quality_score`, `n_chunks` | `ChunkingEvaluator.score_strategy` |
| **T** — inferencia→grafo | `entity_recall`, `relation_pair_recall`, `n_nodes`, `n_rels`, `density`, `evidence_coverage` | `inference_method_benchmark`, `graph_structural_stats` |
| **I** — razonamiento | `f1`, `hallucination_rate`, `distractor_rejection_rate` | `cognitive_eval` + `reasoning.agentic` |
| **RAG/QA** | retrieval precision/recall/relevancy, `answer_correctness` | `retrieval_context_eval` (DeepEval) |
| **Eficiencia** | `tokens`, `latency_s`, `cost_usd` | instrumentación del runner |
| **Global** | `composite_score` (desirability) | `scorecard` (fase DoE: `doekit.desirability_scores`) |

El `composite_score` combina las métricas "buenas" (recall, F1, relevancy, answer
correctness) contra las "malas" (hallucination, costo) en un único número → permite
**rankear arquitecturas**.

## 4. Espacio de arquitecturas (factores del DoE)

Cada corrida fija una arquitectura = un punto en el espacio de factores. `doekit` diseña
qué puntos correr (screening → superficie de respuesta) sobre el `ablation_harness`:

- **Chunking**: `strategy` (recursive / markdown_header / semantic / token / language_specific), `chunk_size`, `chunk_overlap`.
- **Inferencia**: `engine` (ner / llm), `model`, `temperature`.
- **RAG**: `pattern` (text / vector / hybrid), `top_k`.
- **Verify** (razonamiento): pesos de señales, umbral, gates (`PipelineParams`).

## 5. Contra qué competimos — baselines *naive*

Las mejoras deben demostrarse contra líneas base honestas, no contra un espantapájaros:

- **N0 — grafo crudo**: NER sin verificación (extrae y persiste todo).
- **N1 — "LLM extrae y confía"**: extracción LLM directa sin grounding ni critique.
- **N2 — co-ocurrencia**: verify determinista sin LLM.
- **Sistema**: ETI + verify anclado parametrizado (propose→critique→verify).

## 6. Alucinaciones: DeepEval como juez **independiente**

Regla anti-circularidad: el evaluador de faithfulness/hallucination **no** debe ser el
mismo LLM que actúa de crítico en el `verify`. DeepEval (`FaithfulnessMetric`,
`HallucinationMetric`, `ContextualRelevancy`) actúa como juez externo, complementando el
recall/precisión contra gold. Así separamos "el sistema razona" de "un tercero evalúa".

## 7. Métricas que miden un sistema como éste

Calidad (P/R/F1, hallucination, rejection) · faithfulness/groundedness (DeepEval) ·
razonamiento multi-hop (probe-QA, `expected_inferences`) · eficiencia (tokens/latencia/
costo) · **calibración** (¿la `confidence` del crítico predice acierto?) · robustez
(varianza entre corridas con `temperature>0`).

## 8. Dominios y priorización (dogfooding)

| Prioridad | Dominio | Razón |
|---|---|---|
| **P0** | Grafos de conocimiento | Es literalmente Ungraph → autovalidación máxima (PoC inicial) |
| **P0** | Ingeniería de conocimiento | El marco del que ETI es una instancia |
| **P0** | Arquitecturas cognitivas | Es lo que estamos construyendo (propose/critique/verify) |
| **P1** | Machine learning | Usamos embeddings, spaCy, LLMs |
| **P1** | Álgebra lineal / matemáticas | Fundamento de embeddings/ML |
| **P2** | Computación cuántica | Dominio técnico denso |
| **P2** | Química computacional | Dominio "ajeno" → mide **generalización** (control) |

Fuentes de corpus (mix): **PubMed MCP** para química/ML-bio; **web/arxiv** vía WebFetch
para CS/quantum/math/KG.

## 9. Gold: estrategia

Silver labels generados por un LLM fuerte + **revisión experta** (factible por el
dogfooding: conocemos los dominios P0). Incluye `expected_inferences` multi-hop para
medir razonamiento, no solo extracción.

## 10. Cómo se ejecuta

```bash
# Una arquitectura, end-to-end (requiere Neo4j local + API key)
python scripts/run_domain_pipeline.py --domain knowledge_graphs --inference llm

# Comparar arquitecturas y rankear por scorecard
python scripts/run_domain_pipeline.py --domain knowledge_graphs \
    --compare "ner,llm" --chunking "recursive,semantic"
```

Salida: `benchmarks/domains/<dominio>/reports/scorecard.json` (+ HTML vía
`eti_report_bundler`). El comparativo alimenta el DoE con `doekit`.

## 11. Relación con el roadmap

Esta es la instancia end-to-end del **nivel C** (ver [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md)):
C1 (eval-refinar) + C2 (calidad estructural) + C3 (recomendación de arquitectura) unidos
por el scorecard y guiados por DoE (C5).
