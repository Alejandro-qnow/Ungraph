---
name: eti-experiment-science
description: >
  Programa experimental ETI medible y falsable en Ungraph: gates H_I, scorecard E/T/I,
  DoE con doekit, oleadas, Infer como slot (no mega-diseño), puente Complexometrum.
  Usar cuando el usuario mencione H_I, DoE, doekit, scorecard, ExperimentRun, oleada,
  claim científico, ET vs ETI, Y discriminativas, o el checklist del plan maestro.
---

# ETI experiment science (Ungraph)

Fuente de verdad: [`docs/experiment/PLAN_MAESTRO.md`](../../../docs/experiment/PLAN_MAESTRO.md) (visión + **checklist de estado**) y [`docs/experiment/ROADMAP_LEVEL_C.md`](../../../docs/experiment/ROADMAP_LEVEL_C.md) (oleadas). Operativa DoE: [`docs/experiment/BENCHMARK_ETI_DOMAINS.md`](../../../docs/experiment/BENCHMARK_ETI_DOMAINS.md).

## Principios (no negociables)

1. **Abstraer Infer ≠ generalizar inferir.** spaCy/NER es *una* familia; el slot es `InferenceService` + artefacto medible.
2. **Capas:** 0 artefacto ETI → 1 recuperación → 2 razonadores. No mezclar Capa 2 en la oleada H_I.
3. **Y discriminativas:** probes/hit@k sobre **top-k recuperado**; recall desde **Neo4j**; wipe entre celdas.
4. **DoE con doekit** (`ungraph[experiments]`): `recommend → run → analyze → propose`, no producto cartesiano ad-hoc.
5. **Complexometrum** es puente posterior (complejidad no estructurada → validar en ETI → feature de vuelta); no bloquea H_I.

## Protocolo al invocar

1. Leer el **checklist** en PLAN_MAESTRO (§ Checklist de estado) y marcar gaps relevantes.
2. Identificar el **bloqueante** (hoy típico: A5 runner online, B2 top-k, B3 recall Neo4j, D3 H_I).
3. Proponer el **mínimo cambio** que desbloquea el siguiente ítem del camino riguroso (PLAN_MAESTRO § Siguiente camino).
4. Si hay código: Clean Architecture (`infrastructure → application → domain`); tests con skill **ungraph-test**.
5. Al cerrar un ítem: actualizar el checklist del plan maestro (`[x]` / `[~]` / `[ ]`).

## Camino riguroso (orden)

```
… → D5 → C5 → D6 DoE H_chunk (doekit) → pipeline_closure
→ A10/E6–E7 ops → 2º dominio → F5 Complexometrum
```

```bash
# H_chunk con doekit (Infer fijo ner)
uv run --extra experiments --extra infer-en python scripts/run_domain_pipeline.py \
  --domain knowledge_graphs --design screening --doe-path doe_h_chunk.yaml --mode online --redesign
uv run --extra experiments --extra infer-en python scripts/run_domain_pipeline.py \
  --domain knowledge_graphs --design run --mode online --doe-path doe_h_chunk.yaml
uv run --extra experiments python scripts/run_domain_pipeline.py \
  --domain knowledge_graphs --design analyze --doe-path doe_h_chunk.yaml --response answer_correctness
```

Doc slot: `docs/concepts/inference-slot.md`. Cierre: `reports/pipeline_closure.json`.

## Comandos de referencia

```bash
# Offline (ya usable)
uv run --extra experiments python scripts/run_domain_pipeline.py --domain knowledge_graphs --design screening --mode offline
uv run --extra experiments python scripts/run_domain_pipeline.py --domain knowledge_graphs --design run --mode offline
uv run --extra experiments python scripts/run_domain_pipeline.py --domain knowledge_graphs --design analyze

# Unit medibles
uv run --extra experiments pytest tests/unit/test_experiment_run_doe_unit.py tests/unit/test_doe_bridge_unit.py tests/unit/test_probe_qa_eval_unit.py tests/unit/test_scorecard_unit.py tests/unit/test_domain_pipeline_offline_unit.py -q
```

Online (cuando exista): mismo script con `--mode online`, wipe Neo4j, `inference∈{none,ner}`, Transform fijo.

## Rutas clave

| Pieza | Ruta |
|-------|------|
| Runner | `scripts/run_domain_pipeline.py` |
| DoE bridge | `ungraph/evaluation/doe_bridge.py` |
| Scorecard / ExperimentRun | `ungraph/evaluation/scorecard.py`, `experiment_run.py` |
| Probe-QA | `ungraph/evaluation/probe_qa_eval.py` |
| Offline pipeline | `ungraph/evaluation/domain_pipeline.py` |
| Dominio P0 | `benchmarks/domains/knowledge_graphs/` |
| Infer ABC | `ungraph/domain/services/inference_service.py` |

## Skills relacionados

- **eti-mvp-operativa** — readiness capas A/B librería.
- **eti-pipeline** — implementación E/T/I.
- **ungraph-test** — pytest / CI.
- **graphrag-pattern** — retrieval (Y top-k).
- **cypher-craft** — queries Neo4j para recall/evidence.

## Gaps detallados

Ver [checklist-gaps.md](checklist-gaps.md) (desarrollo, pruebas, consideraciones).
