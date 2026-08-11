# Documentación de Ungraph

Documentación de la librería Ungraph (grafos de conocimiento, ETI, GraphRAG como interfaz).

**Principio rector de estructura:** [research/DOCUMENTARY_ZEN.md](research/DOCUMENTARY_ZEN.md)  
(secuencia: fundamento → experimentación → medición → estandarización → uso).

## Sitio MkDocs

```bash
uv sync --extra docs
uv run mkdocs serve -a 127.0.0.1:8000
```

Entrada del sitio: [index.md](index.md). Config: `mkdocs.yml`.

## Índice por capa (alineado a index)

### Empezar (usar)
- [Inicio rápido](guides/sp-quickstart.md) → [API pública](api/sp-public-api.md)
- Opcional: [ingesta](guides/sp-ingestion.md) · [búsqueda](guides/search.md) · [patrones](guides/sp-custom-patterns.md)
- [Tutoriales → guías](tutoriales/README.md)
- Ejemplos: [básicos](examples/sp-basic-examples.md) · [avanzados](examples/sp-advanced-examples.md) · [notebooks](examples/sp-notebooks.md)

### Fundamento (entender)
- [Espina ETI](concepts/eti-spine.md) · [Extracción](concepts/extraction.md) · [Transformación](concepts/transformation.md) · [Inferencia](concepts/inference.md)
- [Slot Infer](concepts/inference-slot.md) · [Arquitectura](concepts/sp-architecture.md)
- [Patrones de grafo](concepts/sp-graph-patterns.md) · [Grafos léxicos](concepts/sp-lexical-graphs.md)
- [Research](research/README.md) · [Teoría GraphRAG](theory/sp-graphrag.md)

### Experimentación
- [Plan maestro](experiment/PLAN_MAESTRO.md)
- [Benchmark ETI / DoE](experiment/BENCHMARK_ETI_DOMAINS.md)
- [Roadmap nivel C](experiment/ROADMAP_LEVEL_C.md)

### Medición
- [Validación](validation/sp-validation_summary.md) — criterio de “validado”: [PRODUCT §5](product/PRODUCT.md)

### Estandarización
- [API pública](api/sp-public-api.md) · [Configuración](api/sp-configuration.md)
- [Patrones de búsqueda](api/sp-search-patterns.md)

### Producto / ops (secundario)
- [Producto](product/PRODUCT.md) · [Visión y tutoriales](product/VISION_AND_TUTORIALS.md)
- [Flujo de trabajo](ops/DEVELOPMENT_WORKFLOW.md) · [CONTRIBUTING](../CONTRIBUTING.md)
- [Instalación e inferencia](ops/INSTALLATION_INFERENCE.md)

### Archive
- Checkpoints e históricos en [`archive/`](archive/) (fuera de nav principal).
