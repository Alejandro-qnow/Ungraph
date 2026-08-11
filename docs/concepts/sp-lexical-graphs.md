# Grafos léxicos — Transform y provenance (no “conocimiento”)

**Idioma:** español (canónico `sp-*`).

Audiencia: research / developer. Espina: [`eti-spine.md`](eti-spine.md).  
Relacionado: [`transformation.md`](transformation.md) · [`sp-graph-patterns.md`](sp-graph-patterns.md) · [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md).

## Motivation

Organizar un documento en File–Page–Chunk (u homólogos) resuelve un problema de **representación y linaje**: qué átomo de evidencia se recupera, en qué orden y con qué ancestro documental. Eso no es todavía *conocimiento* (hechos tipados, creencias con confianza, refutación).

El riesgo epistémico es doble: (1) llamar “knowledge graph” a una topología de chunks; (2) confundir el *lexical graph* de GraphRAG con redes léxicas lingüísticas (WordNet / sinonimia). En Ungraph el grafo léxico es **Transform + provenance**; GraphRAG lo **consume** como Interface (I04–I05). Inference, si aporta, escribe candidatos de dominio *sobre* o *junto a* esa base — no redefine el léxico como ontología.

## Theory

### Lexical (GraphRAG / Ungraph) ≠ lexical (lingüística)

| | Lexical graph (aquí) | Red léxica lingüística | Knowledge graph (dominio) |
|--|----------------------|------------------------|---------------------------|
| Unidades | Chunks / páginas / archivos | Lemas, synsets | Entidades / relaciones tipadas |
| Relaciones | `CONTAINS`, `HAS_CHUNK`, `NEXT_CHUNK` (estructura) | Sinonimia, hiperonimia, … | `AUTOR_DE`, `PARTE_DE`, … |
| Rol epistémico | Evidencia segmentada + linaje (I14 PROV-O) | Semántica léxica | Creencias / hechos candidatos |
| Consumidor típico | Retrieval GraphRAG (I04) | NLP clásico | Inferencia / depuración (I01) |

Anclas: whitepaper §3.1 (E6–E8); matriz I04, I05, I14, I18. No inventar resultados de benchmark en esta página.

### is vs will be

| | |
|--|--|
| **is** | Patrón `FILE_PAGE_CHUNK` materializa File–Page–Chunk + `NEXT_CHUNK`; chunks con texto/embeddings; búsqueda text/vector/hybrid sobre esa base; provenance parcial (filename, page, chunk_id) |
| **will be** | Linaje PROV-O más rico; parent–child / community summaries medidos E2E; no confundir con beliefs first-class (I01) |

## In Ungraph

- **Fase:** Transform — ver [`transformation.md`](transformation.md) (topología léxica / documental).
- **Declaración de forma:** [`sp-graph-patterns.md`](sp-graph-patterns.md); pasos: [`../guides/sp-custom-patterns.md`](../guides/sp-custom-patterns.md), ingesta [`../guides/sp-ingestion.md`](../guides/sp-ingestion.md).
- **Interface:** Basic / parent–child / metadata filtering *leen* el léxico; no demuestran Infer — [`../theory/sp-graphrag.md`](../theory/sp-graphrag.md), [`../guides/search.md`](../guides/search.md).
- **Probe de estructura (no validación PRODUCT §5):** notas en [`../validation/sp-validation_summary.md`](../validation/sp-validation_summary.md).

Estructura canónica (is):

```text
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
                              Chunk -[:NEXT_CHUNK]-> Chunk
```

## Open claims (falseables)

### Claim H_lexical_provenance

- **Enunciado:** Materializar File–Page–Chunk (frente a solo `Chunk` plano) mejora Y de Capa 1 que dependen de ancestro/contexto (metadata filter, parent–child) sin alterar por sí solo el recall de *hechos* de Infer (Capa 0) a igual Extract/Infer.
- **Predicción observable:** Con Infer fijo, hit@k o `answer_correctness` @ top-k con filtros `filename`/`page_number` sube o se habilita frente a SIMPLE_CHUNK; métricas de facts anclados (`entity_recall`, …) permanecen estables si no re-corre Infer.
- **Protocolo mínimo:** Wipe/seed; dos patrones (FILE_PAGE_CHUNK vs SIMPLE_CHUNK); scorecard desagregado Capa 0 vs Capa 1. Ver [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), Claim H_spine_interface en [`eti-spine.md`](eti-spine.md).
- **Falsación:** Si el léxico cambia conteos de facts anclados sin re-ingesta Infer, o no habilita filtros/parent–child medibles, el claim se rechaza o se acota a ergonomía de store.
- **Reproducibilidad:** patrón nombrado en metadata del `ExperimentRun` + scorecard versionado.
