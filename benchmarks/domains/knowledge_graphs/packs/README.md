# Packs — knowledge_graphs

Packs versionados para el programa en [`docs/experiment/EXPERIMENTAL_DESIGN.md`](../../../docs/experiment/EXPERIMENTAL_DESIGN.md) (§8–§10).

## Reglas

1. Cada doc declara `published_at` (ISO date aproximada).  
2. `cutoff_class` se resuelve en corrida vs `model_cutoff` del modelo LLM (si aplica).  
3. Probes del gold del pack deben ser `from_text: true` con spans (salvo set blanco D0).  
4. Diseño **B limpio** no usa `inference=llm`. **B′** sí, etiquetado contaminable.

## Packs

| Pack | Rol | Estado |
|------|-----|--------|
| `pack_seed.yaml` | Mono-doc `kg_survey` (seed histórico) | **is** |
| `pack_kg_multi_v1.yaml` | Multi-doc + fechas | will be (E0) |
