# Neo4j como almacén e interfaz del grafo epistémico

**Idioma:** español (canónico `sp-*`).

Audiencia: research / developer. Espina: [`../concepts/eti-spine.md`](../concepts/eti-spine.md). Cypher operativo y patrones: skills/`guides` — esta página no es tutorial de Cypher.

## Motivation

Una base de grafos eficiente no produce por sí sola ingeniería de conocimiento. Neo4j ofrece nodos, relaciones, índices full-text/vector y (opcional) GDS: es el **sistema de verdad persistente** del flujo documentado en Ungraph y el motor de muchas consultas de Interface. El problema epistémico es qué se escribe ahí — evidencia transformada, hechos anclados, provenance — no memorizar la sintaxis de `MATCH`.

## Theory

En pipelines IE→store (whitepaper E5), el grafo suele ser el *Load* final: menciones tipadas sin ciclo de creencia. En GraphRAG (I04), Neo4j (u otro store) indexa chunks/entidades/comunidades para retrieve. En KBC (DeepDive/NELL, I01–I02), el store sostiene hipótesis con scores y re-ingesta. Ungraph adopta Neo4j en el rol **borrow** de persistencia + recuperación, y **contrast** respecto a tratar el schema como conocimiento ya depurado.

| Rol Neo4j | Capa ETI / Interface | Nota |
|-----------|----------------------|------|
| Persistencia File–Page–Chunk | Transform | Topología léxica / provenance |
| Persistencia Entity/Relation/Fact | Inference (salida) | Anclaje `DERIVED_FROM` / mentions |
| Índices text/vector + Cypher de búsqueda | Interface (Capa 1) | Consumidor; no define Infer |
| GDS (comunidades, centralidad, link prediction) | Interface o familia Infer *sobre* grafo | Comparable solo con Y explícitas (ver [`../concepts/inference.md`](../concepts/inference.md)) |

Provenance parcial hacia PROV-O (I14): ampliar linaje es trayectoria, no hecho medido exhaustivo.

### is vs will be

| | |
|--|--|
| **is** | Destino principal documentado; índices chunk content/embeddings; relaciones léxicas; facts con provenance a chunk cuando Infer corre; búsqueda vía servicios de infraestructura |
| **will be** | Esquema de Claim/Belief + `supports`/`challenges` (I15); jobs de confidence propagation (I13); GDS como familia Infer conmensurable en scorecard |

## In Ungraph

- Capas de software: repositorios Neo4j en **infrastructure**; puertos en **domain** ([`sp-clean-architecture.md`](sp-clean-architecture.md), [`../concepts/sp-architecture.md`](../concepts/sp-architecture.md)).
- Qué se mide en grafo anclado: `entity_recall`, `relation_pair_recall`, `evidence_coverage` — ver plan/benchmark, no esta página.
- Cómo crear índices o lanzar búsquedas: [`../guides/sp-quickstart.md`](../guides/sp-quickstart.md), [`../guides/search.md`](../guides/search.md), [`../api/`](../api/sp-public-api.md).
- GraphRAG como consumidor: [`sp-graphrag.md`](sp-graphrag.md).

Ejemplos Cypher de índices o queries pertenecen a guías/API; aquí solo el rol epistémico.

## Open claims (falseables)

### Claim H_neo4j_store_not_knowledge

- **Enunciado:** Un grafo Neo4j poblado solo con Transform (chunks + topología, `inference=none`) no alcanza las Y de hechos anclados de un grafo con Infer (`ner`) a igual corpus y Transform.
- **Predicción observable:** Gate H_I — `ner` > `none` en recall anclado (seed KG).
- **Protocolo mínimo:** [`../concepts/inference.md`](../concepts/inference.md) Claim H_I; [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md).
- **Falsación:** Si `none` iguala o supera `ner` en facts anclados bajo corrida válida, “persistir en Neo4j” bastaría como conocimiento en ese dominio (acotar la tesis ETI).
- **Reproducibilidad:** `hi_wave_verdict.json` + wipe/seed del dominio P0.
