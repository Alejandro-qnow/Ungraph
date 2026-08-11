# Inferencia — slot, familias y experimentos entre sistemas

**Idioma:** español. Archivo canónico compartido (sin prefijo `sp-`).

Audiencia: research / developer. Espina: [`eti-spine.md`](eti-spine.md).

**Contrato I/O** (artefacto Entity/Relation/Fact, API del slot): [`inference-slot.md`](inference-slot.md). Esta página es el **argumento epistémico** y la taxonomía de familias; no redefine firmas.

## Motivation

“Inferir” en Ungraph no significa un NER universal. Significa: dado un contexto ya transformado, **proponer o verificar** conocimiento estructurado comparable bajo las mismas Y. spaCy es *una* familia; hay miles de formas de razonar. El error de producto es construir un mega-diseño que pretenda unificarlas; el acierto científico es un **slot** enchufable donde sistemas distintos emiten el mismo tipo de artefacto medible.

Abstraer Infer ≠ generalizar el diseño de inferir ([`PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md)).

## Theory

### Familias de Inference (taxonomía viva)

| Familia | Naturaleza | Ejemplos (horizonte) | Linaje |
|---------|------------|----------------------|--------|
| **Simbólica / reglas** | Determinista | Ontologías, constraints, verify estructural, FOL→solver | Logic-LM / LINC (I08); OWL loops (I09) |
| **Transductiva clásica** | Det. o casi | NER spaCy, patrones léxicos, co-ocurrencia | IE clásico; I25 |
| **Neural / LLM** | Estocástica o casi-det (temp=0) | Extracción LLM, graph transformers | Pan et al. LLMs+KGs; I25 |
| **Híbrida det↔no-det** | Mixta | NER hints → LLM; propose→critique→verify | Neurosymbolic surveys |
| **GDS / predictiva sobre grafo** | Sobre topología ya materializada | Link prediction, centralidad, embeddings de grafo | GraphRAG surveys; analítica Neo4j |
| **Topológica determinista** | Razonamiento por recorrido/estructura | Expansión por aristas tipadas, cierres, paths como prueba | Contrast with retrieval-only GraphRAG |
| **Multiagente / abducción** | Roles conversacionales | Propose/critique/novelty; preguntas → hipótesis | SciAgents (I10); HypoAgent (I11) |
| **Refinamiento continuo** | No one-shot | Confidence propagation, edit/delete de claims | NELL (I01); GraphRefine (I07); E19 |

Los internos (tokens, hops, temperatura, autocritica) son **covariables** de coste/explicación; no mueven la portería de las Y de capa B.

### Lógica proposicional / solvers

El patrón Logic-LM/LINC separa *formular* (LLM u otro frontal) de *inferir* (solver/prover). En ETI eso cabe en el slot como familia simbólica o híbrida: el artefacto sigue siendo facts/relations anclados (o un veredicto de consistencia con provenance). **will be** respecto a producción Ungraph; el encaje epistémico ya está en el whitepaper (E20–E22).

### Graph Data Science y topología

GDS predice o resume estructura (enlaces, comunidades, scores). La topología como instrumento **determinista** usa el grafo como espacio de prueba (paths, constraints), no solo como índice ANN. Ambos son Inference *sobre* el KG o su proyección — distintos de Capa 1 (recuperar chunks). No mezclar Capa 2 (agentes/verify weights) en la oleada que cierra H_I.

### Agentes

Agentes proponen, critican o abducen hipótesis (I10, I11). Son sistemas enchufables al slot o post-slot (Capa 2) **después** de que Capa 0 pase gate. No sustituyen el I/O medible ni el baseline `inference=none`.

### is vs will be

| | |
|--|--|
| **is** | Slot `InferenceService`; modos `ner` / `pattern` (+ LLM según extras); baseline `none` para H_I; artefacto Entity/Relation/Fact con `extraction_method` y provenance a chunk; oleadas H_I y ner vs pattern medidas en seed KG; `hybrid` declarado no implementado |
| **will be** | Solvers FOL/OWL en loop; GDS como familia Infer comparable; multiagente propose/critique; Belief/Claim + EVI; depuración continua bronze→gold |

## In Ungraph

1. Congelar o fijar Transform; swap solo `inference`.
2. Emitir artefacto Capa 0 comparable (`capa0_artifact.json` cuando aplique).
3. Medir Y: `entity_recall`, `relation_pair_recall`, `evidence_coverage`, `answer_correctness` @ top-k.
4. Coste/latencia aparte.

```bash
uv run --extra experiments --extra infer-en \
  python scripts/run_domain_pipeline.py --domain knowledge_graphs \
  --design family-wave --families ner,pattern
```

Detalle de campos y API: [`inference-slot.md`](inference-slot.md). Capas y gates: [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`../experiment/ROADMAP_LEVEL_C.md`](../experiment/ROADMAP_LEVEL_C.md), [`../experiment/BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md). Depuración EVI / Beliefs: **will be** (I15, I23) — no afirmar en producción.

## Open claims (falseables)

### Claim H_I

- **Enunciado:** Infer (`ner`) aporta frente a solo ET (`none`) en grafo anclado + tarea, con Transform fijo.
- **Predicción observable:** `ner` > `none` en recall Neo4j y probe-QA @ top-k no colapsa.
- **Protocolo mínimo:** Online Neo4j+spaCy; wipe; hi-wave. Ver plan maestro (estado: **PASS** en seed KG — no generalizar sin más dominios).
- **Falsación:** Si `ner` ≤ `none` en recall anclado bajo corrida válida, H_I se rechaza en ese dominio.
- **Reproducibilidad:** `hi_wave_verdict.json` + scorecards del runner.

### Claim H_I_family

- **Enunciado:** Familias distintas (`ner` vs `pattern`, y más adelante LLM/GDS/simbólico) son comparables vía las mismas Y de capa B a igual artefacto de entrada.
- **Predicción observable:** Diferencias interpretables en recall/evidencia/tarea o en latencia; no empate trivial en todas las Y.
- **Protocolo mínimo:** Family-wave sobre capa0; [`BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md). Ampliar familias = oleada en [`ROADMAP_LEVEL_C.md`](../experiment/ROADMAP_LEVEL_C.md), no mega-diseño en esta página.
- **Falsación:** Si tras swap de familia las Y son idénticas o el artefacto no es conmensurable (`extraction_method` ausente / tipos rotos), el slot no sostiene comparación.
- **Reproducibilidad:** Reports family-wave; filas DoE con factor `inference`.

### Claim H_I_topo_gds

- **Enunciado:** Una familia topológica/GDS, alimentada por el mismo grafo Capa 0, mejora Y de tarea o de predicción de enlaces frente a solo IE transductivo en al menos un dominio gold.
- **Predicción observable:** Mejora en métrica de tarea o link-prediction gold sin degradar `evidence_coverage` bajo umbral acordado.
- **Protocolo mínimo:** Capa 0 congelada; factor familia ∈ {ner, gds_topo, …}; gold de enlaces o probes. Exige oleada — enlazar plan/roadmap cuando se programe; no afirmar resultado hoy.
- **Falsación:** Si GDS/topo no mejora ninguna Y acordada a igual presupuesto, la familia no se prioriza en ese dominio.
- **Reproducibilidad:** ExperimentRun + gold versionado + scorecard.
