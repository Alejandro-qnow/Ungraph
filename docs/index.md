# Ungraph — documentación para desarrolladores

Librería Python: texto no estructurado → grafo en Neo4j vía **Extract → Transform → Inference (ETI)**. GraphRAG / búsqueda / MCP son **interfaz** sobre el almacén; no definen “conocimiento”.

## Empezar (usar)

1. [Inicio rápido](guides/sp-quickstart.md)
2. [API pública](api/sp-public-api.md)
3. Guías opcionales: [ingesta](guides/sp-ingestion.md) · [búsqueda](guides/search.md) · [patrones](guides/sp-custom-patterns.md)
4. Repro: [ejemplos básicos](examples/sp-basic-examples.md) · [avanzados](examples/sp-advanced-examples.md) · [notebooks](examples/sp-notebooks.md)

## Espina ETI (entender)

1. [Espina ETI](concepts/eti-spine.md)
2. [Extracción](concepts/extraction.md) · [Transformación](concepts/transformation.md) · [Inferencia](concepts/inference.md) · [Slot Infer](concepts/inference-slot.md)
3. Contexto: [introducción](concepts/sp-introduction.md) · [arquitectura](concepts/sp-architecture.md) · [patrones](concepts/sp-graph-patterns.md) · [léxicos](concepts/sp-lexical-graphs.md)

## Ciencia (medir)

1. [Research](research/README.md)
2. [Plan maestro](experiment/PLAN_MAESTRO.md)
3. [Validación](validation/sp-validation_summary.md) (solo con artefactos auditables; criterio: [PRODUCT §5](product/PRODUCT.md))

## Mapa ZEN (capas)

| Orden | Capa | Entrada |
|------:|------|---------|
| 1 | Fundamento | [ETI](concepts/eti-spine.md) · [Research](research/README.md) · [Teoría GraphRAG](theory/sp-graphrag.md) |
| 2 | Experimentación | [Plan maestro](experiment/PLAN_MAESTRO.md) · [Benchmark](experiment/BENCHMARK_ETI_DOMAINS.md) |
| 3 | Medición | [Validación](validation/sp-validation_summary.md) |
| 4 | Estandarización | [API](api/sp-public-api.md) |
| 5 | Uso / repro | [Guías](guides/sp-quickstart.md) · [Tutoriales → guías](tutoriales/README.md) · [Ejemplos básicos](examples/sp-basic-examples.md) · [avanzados](examples/sp-advanced-examples.md) · [notebooks](examples/sp-notebooks.md) |

Gobernanza de estructura: [DOCUMENTARY_ZEN](research/DOCUMENTARY_ZEN.md). Producto / ops (secundario, sin tab): [PRODUCT](product/PRODUCT.md) · [ops](ops/DEVELOPMENT_WORKFLOW.md).

## Vista previa local

```bash
uv sync --extra docs
uv run mkdocs serve -a 127.0.0.1:8000
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000).
