# Notebooks de ejemplo

Índice de Jupyter notebooks versionados bajo `ungraph/notebooks/`.  
Audiencia: developer / tutorial. Snippets cortos: [`sp-basic-examples.md`](sp-basic-examples.md), [`sp-advanced-examples.md`](sp-advanced-examples.md). Guías: [`../guides/sp-quickstart.md`](../guides/sp-quickstart.md).

Los notebooks son **probes reproductibles** (celdas + Neo4j local). Ejecutar un notebook **no** cumple por sí solo el criterio de “validado” ([PRODUCT §5](../product/PRODUCT.md)); resultados confrontables van a `validation/` vía experiment.

## Prerrequisitos

1. Entorno del repo o `pip install ungraph` (+ extras que el notebook pida: `[gds]`, `[infer]`, …).
2. Neo4j configurado (`.env` / `ungraph.configure`).
3. Jupyter:

```bash
pip install jupyter notebook
# desde la raíz del repo
jupyter notebook ungraph/notebooks/
```

**Resultado observable:** el kernel importa `ungraph`; las celdas de ping/ingesta no fallan por auth.

## Fixtures / datos

Muchos notebooks generan o apuntan a paths relativos al repo. Para repro mínima fuera del notebook, usar:

- [`../../tests/fixtures/topology_alpha.md`](../../tests/fixtures/topology_alpha.md)
- Demo crawl (si el notebook lo usa): `ungraph/notebooks/_notebook_crawl_demo/`

## Notebooks estables (serie numerada)

Rutas relativas a la raíz del repositorio.

| Notebook | Enfoque | Capa how-to relacionada |
|----------|---------|-------------------------|
| `ungraph/notebooks/1.1 Document Ingestion Basics_.ipynb` | Config + ingesta básica | [quickstart](../guides/sp-quickstart.md), [ingesta](../guides/sp-ingestion.md) |
| `ungraph/notebooks/1.2 Document Formats & Metadata.ipynb` | Formatos / metadata | [ingesta](../guides/sp-ingestion.md) |
| `ungraph/notebooks/2.1 Graph Pattern Construction.ipynb` | `GraphPattern` | [patrones](../guides/sp-custom-patterns.md) |
| `ungraph/notebooks/2.2 Smart Chunking Strategies.ipynb` | Estrategias de chunking | [API](../api/sp-public-api.md) (`suggest_chunking_strategy`) |
| `ungraph/notebooks/2.3 Index Management.ipynb` | Índices Neo4j | [configuración](../api/sp-configuration.md) |
| `ungraph/notebooks/3.1 Entity Extraction & Facts (ETI).ipynb` | Slot Inference (probe) | [inference-slot](../concepts/inference-slot.md), [espina](../concepts/eti-spine.md) |
| `ungraph/notebooks/3.2 Basic Retrieval Patterns.ipynb` | Retrieval básico | [búsqueda](../guides/search.md) |
| `ungraph/notebooks/3.3 GraphRAG Retrieval Patterns.ipynb` | Patrones GraphRAG básicos | [sp-search-patterns](../api/sp-search-patterns.md) |
| `ungraph/notebooks/3.4 Advanced GraphRAG Patterns.ipynb` | Patrones con extras | [sp-advanced-search-patterns](../api/sp-advanced-search-patterns.md) |
| `ungraph/notebooks/4.1 Graph Visualization.ipynb` | Visualización (probe) | PRODUCT / ops (secundario) |
| `ungraph/notebooks/10.1_HTML_Documentation_Crawl_and_Graph.ipynb` | Crawl HTML → grafo | [ingesta](../guides/sp-ingestion.md) |

Abrir uno concreto:

```bash
jupyter notebook "ungraph/notebooks/1.1 Document Ingestion Basics_.ipynb"
```

**Resultado observable (típico 1.1):** chunks persistidos y al menos una búsqueda con hits.

## WIP / exploratorio

Prefijo `WIP_` = trayectoria o prototipo; **no** afirmar capacidad de producto.

| Notebook | Nota |
|----------|------|
| `ungraph/notebooks/WIP_11_Image_Ingestion_ETI.ipynb` | Ingesta de imagen — exploratorio |
| `ungraph/notebooks/WIP_12_Image_Constructor_Protocols.ipynb` | Protocolos de construcción — exploratorio |
| `ungraph/notebooks/WIP_13_Knowledge_Graph_as_Source.ipynb` | KG como fuente — exploratorio |

Trayectoria medible: [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [PRODUCT §5](../product/PRODUCT.md).

## Otros notebooks en el repo (fuera de esta serie)

- `tests/notebooks/Testing Graph Patterns.ipynb` — apoyo a tests.
- `article/...` — material de artículo; no es contrato de librería.

No sustituyen la API documentada en `docs/api/`.

## is / will be

| | |
|--|--|
| **is** | Serie numerada bajo `ungraph/notebooks/` ejecutable como probe local con Neo4j |
| **will be** | Notebooks como artefacto de ExperimentRun auditado en `validation/`; WIP promovidos solo tras criterio §5 |

## Open claims

N/A. Este índice no formula hipótesis nuevas.

## Referencias

- [Ejemplos básicos](sp-basic-examples.md) · [Avanzados](sp-advanced-examples.md)
- [Inicio rápido](../guides/sp-quickstart.md) · [API pública](../api/sp-public-api.md)
- [Espina ETI](../concepts/eti-spine.md) · [README docs](../README.md)
