# Matriz de inspiración — Ungraph

**Fuente:** whitepaper IMRaD `WHITEPAPER_UNGRAPH_IMRAD.md` (§3.3) + conversación de producto 2026-07-27.  
**Leyenda de rol:** `is` = ya reflejado · `will be` = trayectoria · `borrow` = adaptar mecanismo · `contrast` = no copiar el producto.

| ID | Inspiración | Rol | Capa | Capacidad Ungraph |
|----|-------------|-----|------|-------------------|
| I01 | NELL beliefs + confidence | will be / borrow | Inference + Depuración | `Claim` + scores + ingest continuo |
| I02 | DeepDive probs + error analysis | borrow | Inference | Diagnósticos; umbral de promoción |
| I03 | Fonduer multimodal KBC | will be | Extract | Layouts HTML/PDF; vision embeddings |
| I04 | Microsoft GraphRAG communities | is (parcial) / borrow | Transform + Interface | Summaries; local/global search |
| I05 | GraphRAG surveys | borrow | Interface | Matriz de patrones documentada |
| I06 | Self-RAG / CoVe | will be | Depuración | Protocolo de verificación |
| I07 | GraphRefine | will be | Depuración | edit/rewrite/delete de claims |
| I08 | Logic-LM / LINC | will be | Inference | Formalizar → solver |
| I09 | OWL consistency loops | will be | Inference | Ontología como validador |
| I10 | SciAgents | will be | Inference | Agentes propose/critique/novelty |
| I11 | HypoAgent / abducción | will be | Inference | Preguntas → hipótesis sobre KG |
| I12 | Graph of States | borrow | Inference | Anti-drift / anti-fabrication |
| I13 | Confidence propagation | will be | Depuración | Jobs de refinamiento |
| I14 | PROV-O | is (parcial) | All | Ampliar linaje |
| I15 | EVI / Dung AF | will be | Depuración | `supports` / `challenges` |
| I16 | CommonKADS | borrow | Product | Patrón = tarea de conocimiento |
| I17 | Ontology learning surveys | will be | Transform/Inference | Sugerir esquema |
| I18 | Chunking empirics | is / will be | Transform | Estrategias explícitas en patterns |
| I19 | KGGen aggregate+resolve | borrow | Inference | Consolidación |
| I20 | CodeGraph | contrast | Interface | Fuente de artefacto, no el core |
| I21 | context-graph-demo | borrow / contrast | Inference | Reasoning/Decision; seguir siendo librería |
| I22 | Context graphs (state vs event clock) | borrow | Product | Documentar relojes de estado/evento |
| I23 | Medallón bronce/plata/oro | will be | Depuración | `CurationState` |
| I24 | MCP + IDEs (Cursor/Claude) | will be | Interface | Tools sobre use cases |
| I25 | spaCy + LLM extractors | is | Inference | Dual engine + `extraction_method` |
| I26 | Clean Architecture | is | Product | Contratos en domain |

## Visión en una línea

Acumular creencias provisionales (ETI) → depurar con preguntas, crítica y lógica → promover bronce→oro → exponer vía GraphRAG/API/MCP.
