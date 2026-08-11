# Patrones de grafo — mapeo declarativo (no tutorial API)

**Idioma:** español (canónico `sp-*`).

Audiencia: research / developer. Espina: [`eti-spine.md`](eti-spine.md).  
Pasos ejecutables: [`../guides/sp-custom-patterns.md`](../guides/sp-custom-patterns.md) (esta página **no** duplica la guía).

## Motivation

Persistir texto en Neo4j sin un **contrato de forma** deja la topología implícita en Cypher ad hoc: cada ingesta reinventar labels, direcciones y provenance. El problema epistémico no es “escribir menos código”, sino hacer **reproducible y auditable** qué unidades de evidencia existen y cómo se enlazan *antes* de Inference.

Un patrón declarativo actúa como **ORM de grafo** (esquema tipado de nodos/relaciones): fija el mapeo documento → estructura, separa *qué* se materializa de *cómo* se ejecuta Cypher, y permite comparar Transform bajo factor controlado (I16 CommonKADS: patrón ≈ tarea de conocimiento; I18 chunking/topología como superficie experimental).

GraphRAG consume esa topología (I04–I05); no la define. Confundir “patrón de recuperación” con “patrón de materialización” mezcla Interface con Transform.

## Theory

### Qué es un patrón (fenómeno)

| Concepto | Rol | No es |
|----------|-----|-------|
| **GraphPattern** | Declaración de labels, propiedades requeridas/opcionales, índices y tipos de relación | Un motor Infer ni un scorecard |
| **Nodo / relación tipados** | Contrato de forma del almacén | Ontología de dominio completa |
| **Patrón léxico** (p. ej. File–Page–Chunk) | Topología de Transform + provenance | Knowledge graph de hechos |
| **Patrón de búsqueda** | Interface GraphRAG sobre el store | Sustituto de creencias depuradas |

Linaje: esquemas tipados en KBC / DeepDive (features → creencias; whitepaper E1); catálogos GraphRAG como *consumidores* de forma (I05); PROV-O (I14) para linaje cuando el patrón fija File/Page/Chunk. Ontology learning (I17) puede *sugerir* patrones — trayectoria, no hecho.

### is vs will be

| | |
|--|--|
| **is** | Value objects `GraphPattern` / `NodeDefinition` / `RelationshipDefinition` en dominio; patrón predefinido `FILE_PAGE_CHUNK`; validación de forma; ingesta acepta `pattern=…` (probe en API/guides) |
| **will be** | Patrones tipados de *conocimiento* (entidades/rels de dominio) como salida estable de Infer; promoción bronze→gold por patrón; sugerencia automática de esquema (I17) |

## In Ungraph

- **Capa ETI:** el patrón materializa sobre todo **Transform** (topología léxica + índices). Extract entrega unidades; Infer añade candidatos de conocimiento *sobre* o *junto a* esa base — ver [`transformation.md`](transformation.md), [`inference.md`](inference.md).
- **Léxico vs conocimiento:** File–Page–Chunk es grafo léxico ([`sp-lexical-graphs.md`](sp-lexical-graphs.md)), no WordNet ni KG de dominio.
- **Interface:** patrones de retrieval (basic, parent–child, …) presuponen forma léxica/KG; detalle en [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md), contrato en [`../api/sp-search-patterns.md`](../api/sp-search-patterns.md).
- **Cómo crear/usar un patrón:** solo en [`../guides/sp-custom-patterns.md`](../guides/sp-custom-patterns.md) — aquí no hay tutorial API.
- **Programa medible:** factorizar patrón/topología en DoE vía [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) (H_chunk / Transform), no como marketing de “todos los patrones validados”.

## Open claims (falseables)

### Claim H_pattern_declarative

- **Enunciado:** Fijar topología vía `GraphPattern` (frente a Cypher ad hoc equivalente) mejora reproducibilidad de métricas de Transform/Capa 0 a igual Extract e Infer.
- **Predicción observable:** Con recipe Capa 0 congelada salvo forma del patrón, scorecards (`n_chunks`, integridad File–Page–Chunk, `evidence_coverage` estructural) coinciden entre corridas wipe/seed; la variante ad hoc sin patrón diverge o no audita propiedades requeridas.
- **Protocolo mínimo:** Fixture de dominio P0; ingesta con `FILE_PAGE_CHUNK` vs script Cypher paralelo; comparar scorecard / integridad de secuencia. Enlace: [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`transformation.md`](transformation.md).
- **Falsación:** Si ambas rutas producen grafos y Y idénticas *sin* contrato de propiedades/índices, o el patrón no bloquea formas inválidas, el claim de “ORM epistémico” queda acotado a ergonomía de código.
- **Reproducibilidad:** `ExperimentRun` + patrón versionado (nombre + hash de definiciones) en metadata del run.
