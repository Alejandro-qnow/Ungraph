# Research — Ungraph

**Rol de esta carpeta:** fundamento científico y gobernanza documental (claims, linaje, plantillas). **No** es how-to de ingesta, búsqueda ni API.

**Principio rector de estructura:** [`DOCUMENTARY_ZEN.md`](DOCUMENTARY_ZEN.md) — menos docs, raíz limpia, secuencia fundamento → experimentación → medición → estandarización → productivización. Curar según ese mapa; no acumular en la raíz de `docs/`.

| Artefacto | Rol |
|-----------|-----|
| [`DOCUMENTARY_ZEN.md`](DOCUMENTARY_ZEN.md) | Principio ZEN: capas, migración, nav, oleadas |
| [`WHITEPAPER_UNGRAPH_IMRAD.md`](WHITEPAPER_UNGRAPH_IMRAD.md) | Whitepaper IMRaD (lectura principal) |
| [`INSPIRATION_MATRIX.md`](INSPIRATION_MATRIX.md) | Matriz papers/productos → capacidades (`is` / `will be` / Ixx) |
| [`CURATION_CHECKLIST.md`](CURATION_CHECKLIST.md) | Checklist operativo de curación documental ETI |

## Conceptos canónicos (espina ETI)

Argumento epistémico por fase (Motivation → Theory → In Ungraph → Open claims). Idioma: español.

| Página | Rol |
|--------|-----|
| [`../concepts/eti-spine.md`](../concepts/eti-spine.md) | Espina ETI vs ETL / vs solo retrieval |
| [`../concepts/extraction.md`](../concepts/extraction.md) | Familias de Extract |
| [`../concepts/transformation.md`](../concepts/transformation.md) | Transform, featurización, complejidad |
| [`../concepts/inference.md`](../concepts/inference.md) | Inferencia (argumento) |
| [`../concepts/inference-slot.md`](../concepts/inference-slot.md) | Contrato I/O del slot Infer |

## Teoría (linaje; no redefine la espina)

| Página | Rol |
|--------|-----|
| [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md) | GraphRAG = Interface / consumidor |
| [`../theory/sp-neo4j.md`](../theory/sp-neo4j.md) | Neo4j = store + Interface |
| [`../theory/sp-clean-architecture.md`](../theory/sp-clean-architecture.md) | CA mapeada a capas ↔ ETI |

## Dónde *no* buscar pasos

| Necesidad | Ir a |
|-----------|------|
| Quickstart / ingesta / search | [`../guides/`](../guides/sp-quickstart.md) |
| Contrato de librería | [`../api/sp-public-api.md`](../api/sp-public-api.md) |
| Hipótesis medibles, DoE, oleadas | [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`../experiment/BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md), [`../experiment/ROADMAP_LEVEL_C.md`](../experiment/ROADMAP_LEVEL_C.md) |
| Resultados confrontables (criterio PRODUCT §5) | [`../validation/`](../validation/sp-validation_summary.md) |
| Promesa de producto | [`../product/PRODUCT.md`](../product/PRODUCT.md), [`../product/VISION_AND_TUTORIALS.md`](../product/VISION_AND_TUTORIALS.md) |
