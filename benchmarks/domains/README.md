# Benchmarks ETI por dominio

Pruebas end-to-end del patrón Extract→Transform→Inference sobre conocimiento real de un
dominio, con métricas globales comparables entre arquitecturas. Ver el diseño en
[`docs/experiment/BENCHMARK_ETI_DOMAINS.md`](../../docs/experiment/BENCHMARK_ETI_DOMAINS.md).

## Estructura de un dominio

```
domains/<dominio>/
  manifest.yaml   # fuentes + arquitecturas (chunking×inference×rag) + params
  corpus/         # papers normalizados (.md/.pdf/.html)
  gold.json       # entities, relation_pairs, graphrag_probe_queries(+answers), expected_inferences
  reports/        # scorecards por corrida (se generan al ejecutar)
```

## Ejecutar

```bash
# Modo offline (sin Neo4j/LLM): chunking + extracción NER vs gold + razonamiento anclado
python scripts/run_domain_pipeline.py --domain knowledge_graphs --offline

# End-to-end (Neo4j local + API key): añade grafo, RAG/QA y crítico LLM
python scripts/run_domain_pipeline.py --domain knowledge_graphs --inference llm

# Comparar arquitecturas y rankear por scorecard
python scripts/run_domain_pipeline.py --domain knowledge_graphs --compare "ner,llm"
```

## Dominios (orden dogfooding)

- **P0**: `knowledge_graphs` (PoC), ingeniería de conocimiento, arquitecturas cognitivas
- **P1**: machine learning, álgebra lineal / matemáticas
- **P2**: computación cuántica, química computacional (control de generalización)
