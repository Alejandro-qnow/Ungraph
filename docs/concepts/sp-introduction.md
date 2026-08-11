# Introducción a Ungraph

**Idioma:** español (canónico `sp-*`).

Audiencia: developer / research que necesita *qué es* Ungraph en términos ETI — no el recorrido de instalación. Pasos ejecutables: [`../guides/sp-quickstart.md`](../guides/sp-quickstart.md).

## Motivation

Convertir texto no estructurado en un grafo consultable no basta para llamar al resultado **conocimiento**. Un índice recuperable puede devolver fragmentos útiles sin sostener creencias con evidencia, confianza ni criterio de refutación. Ungraph organiza esa tensión como pipeline **Extract → Transform → Inference (ETI)** hacia un almacén epistémico en Neo4j; GraphRAG y la búsqueda son **interfaz** sobre ese almacén, no la definición de “conocer”.

## Theory

Ungraph se ancla en la espina ETI validada como principio organizador moderno cuando Inference no se reduce a “correr un NER” y se admite depuración continua (whitepaper RQ1; NELL/DeepDive I01–I02). Tres lecturas que no deben confundirse:

| Lectura | Qué es | Qué no es |
|---------|--------|-----------|
| **Almacén epistémico** | Candidatos (hechos/entidades) con provenance y, en trayectoria, confianza/curación | Un dump de triples “limpios” one-shot |
| **Grafo léxico** | Topología documental File→Page→Chunk (Transform) | El grafo de creencias del dominio |
| **GraphRAG / búsqueda** | Consumidor (Capa 1): text / vector / hybrid / patrones | Sustituto de Extract–Transform–Inference |

Linaje y matriz: [`../research/WHITEPAPER_UNGRAPH_IMRAD.md`](../research/WHITEPAPER_UNGRAPH_IMRAD.md), [`../research/INSPIRATION_MATRIX.md`](../research/INSPIRATION_MATRIX.md).

### is vs will be

| | |
|--|--|
| **is** | Librería Python; ETI modular; patrones de grafo; persistencia Neo4j; búsqueda text/vector/hybrid; Infer enchufable (`ner`/`pattern`/+LLM); scorecards experimentales en seed |
| **will be** | Beliefs first-class, EVI, promoción bronze→gold, MCP/IDE tools como Interface — ver producto/visión y Open claims en research |

## In Ungraph

- **Espina y fases:** [`eti-spine.md`](eti-spine.md) · [`extraction.md`](extraction.md) · [`transformation.md`](transformation.md) · [`inference.md`](inference.md) · [`inference-slot.md`](inference-slot.md)
- **Arquitectura (capas ↔ ETI):** [`sp-architecture.md`](sp-architecture.md)
- **Grafo léxico / patrones:** [`sp-lexical-graphs.md`](sp-lexical-graphs.md) · [`sp-graph-patterns.md`](sp-graph-patterns.md)
- **Cómo usarlo (fuera de concepts):** [`../guides/sp-quickstart.md`](../guides/sp-quickstart.md) · [`../guides/sp-ingestion.md`](../guides/sp-ingestion.md) · [`../guides/search.md`](../guides/search.md) · [`../api/sp-public-api.md`](../api/sp-public-api.md)
- **Programa medible:** [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md)

El patrón `FILE_PAGE_CHUNK` materializa el Lexical Graph (Transform). La proposición tipada Entity/Relation/Fact vive en el **slot Infer**, no en el loader.

## Open claims (falseables)

### Claim H_intro_spine

- **Enunciado:** Presentar Ungraph como ETI + almacén epistémico (con retrieval como Interface) predice mejor discriminación ET vs ETI que presentarlo solo como “RAG sobre Neo4j”.
- **Predicción observable:** Bajo Transform fijo, `inference=ner` supera `inference=none` en recall anclado y no colapsa probe-QA @ top-k (gate H_I del plan).
- **Protocolo mínimo:** Ver Claim H_spine_ETI en [`eti-spine.md`](eti-spine.md) y [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md).
- **Falsación:** Si el framing “solo retrieval” basta para explicar las Y de Capa 0 (existencia de facts anclados) sin Infer, el claim de espina epistémica se acota.
- **Reproducibilidad:** `hi_wave_verdict.json` + scorecards del runner DoE.
