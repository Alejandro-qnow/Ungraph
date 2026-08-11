# Contrato I/O del slot Infer

**Idioma:** español. Archivo canónico compartido (sin prefijo `sp-`).

Audiencia: research / developer. Argumento epistémico y taxonomía de familias: [`inference.md`](inference.md). Espina: [`eti-spine.md`](eti-spine.md).

## Motivation

Sin un **contrato de artefacto** compartido, cada motor de “inferencia” inventa su propia salida y las Y dejan de ser conmensurables. El problema epistémico no es elegir el mejor NER: es poder **comparar** proposiciones de conocimiento (entidades, relaciones, hechos anclados) bajo la misma vara, aunque cambie la familia (spaCy, patrón léxico, LLM, solver, …).

Abstraer Infer ≠ generalizar el diseño de inferir. El slot fija *qué* se emite y *cómo se ancla* a evidencia; no unifica *cómo* se razona por dentro ([`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md)).

## Theory

En KBC clásico (DeepDive, NELL) lo medible no es el parser interno sino la **creencia calibrada** o el candidato con confianza y linaje (I01, I02; whitepaper E1–E2, E18). En pipelines LLM modernos, extract → aggregate → resolve (KGGen, I19) solo es comparable si el artefacto intermedio es estable. El patrón Logic-LM / LINC (I08) separa *formular* de *inferir*: el contrato del slot es el punto donde esas familias vuelven a hablar el mismo idioma (Entity / Relation / Fact + provenance).

**Regla:** los internos (tokens, temperatura, hops, autocritica) son **covariables**; no mueven la portería de las Y de capa B (`entity_recall`, `relation_pair_recall`, `evidence_coverage`, `answer_correctness` @ top-k).

### is vs will be

| | |
|--|--|
| **is** | `InferenceService` en dominio; modos `ner` / `pattern` (+ LLM según extras); baseline `inference=none` para H_I; campos `extraction_method` y provenance a chunk; `hybrid` declarado **no implementado** |
| **will be** | Artefactos Belief/Claim first-class; `supports`/`challenges` (EVI, I15); solvers FOL/OWL como familias enchufables al mismo I/O; promoción bronze→gold como estado de curación medible (I23) — no afirmado como producción |

## In Ungraph

El pipeline de ingesta llama al slot **después** de chunking + embeddings (Transform). El servicio no debe depender de Neo4j ni de LangChain en `domain/`.

### Entrada

| Campo | Tipo | Notas |
|-------|------|--------|
| `chunk` | `Chunk` | `id`, `page_content`, `metadata` (filename, `source_document_uid`, …) |
| `entities` (opcional) | `List[Entity]` | Si se pasa a `infer_facts`, evita segunda pasada de extracción |

### Salida obligatoria (artefacto)

1. **`Entity`** — `id`, `name`, `type`, `mentions` (chunk ids), `extraction_method`
2. **`Relation`** — extremos (`source`/`target` id + name), `relation_type`, `confidence`, `provenance_ref` (chunk id), `extraction_method`
3. **`Fact`** — tripleta `subject` / `predicate` / `object`, `confidence`, `provenance_ref`; opcional `object_entity_type`

### `extraction_method` (covariable, no veredicto)

| Valor | Familia | Modo `inference_mode` |
|-------|---------|------------------------|
| `spacy` | Transductiva NER | `ner` |
| `lexical_pattern` | Simbólica / léxica | `pattern` |
| (LLM) | Neural | `llm` |

### Provenance

- `provenance_ref` / `mentions` → anclar al `chunk.id`
- En Neo4j (probe de persistencia): facts con `DERIVED_FROM`; `evidence_coverage` en el scorecard
- `curation_state`: ciclo Extracted → Curated / Invalid (ops; **no** es Y científica de H_I)

### API del slot (probe)

```python
class InferenceService(ABC):
    def extract_entities(self, chunk: Chunk) -> List[Entity]: ...
    def extract_relations(self, chunk: Chunk, entities: List[Entity]) -> List[Relation]: ...
    def infer_facts(self, chunk: Chunk, entities: Optional[List[Entity]] = None) -> List[Fact]: ...
```

Factory: `create_inference_service(settings, language=…)` en el composition root de aplicación.

### Qué no es el contrato

- Un mega-diseño multiagente o “verify” post-hoc (Capa 2) no sustituye este I/O.
- `hybrid` → `NotImplementedError` hasta que exista implementación medible.
- `inference=none` es baseline ET de H_I, no una familia Infer.

Comparación científica: misma recipe Capa 0 → swap solo `inference` → Y de capa B. Detalle de oleadas: [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`../experiment/BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md). Comando runner: ver plan / [`inference.md`](inference.md) (no how-to de ingesta aquí).

## Open claims (falseables)

### Claim H_slot_commensurable

- **Enunciado:** Familias enchufadas al mismo `InferenceService` producen artefactos conmensurables (`extraction_method` + provenance a chunk) tales que un swap de familia mueve Y de capa B de forma interpretable.
- **Predicción observable:** En family-wave `ner` vs `pattern` (y más adelante LLM), al menos una Y de recall/evidencia/tarea o latencia discrimina; no empate trivial en todas las Y con tipos rotos.
- **Protocolo mínimo:** `capa0_artifact.json`; `--design family-wave`; ver [`inference.md`](inference.md) Claim H_I_family y [`../experiment/BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md).
- **Falsación:** Si el artefacto no es comparable entre familias (campos ausentes, ids no anclados) o las Y son idénticas por fallo de contrato, el slot no sostiene comparación científica.
- **Reproducibilidad:** Reports family-wave + `ExperimentRun` / scorecard.

*Gate H_I (Infer aporta frente a ET)* está enunciado en [`inference.md`](inference.md) y cerrado PASS en seed KG en el plan maestro — no se re-diseña DoE aquí.
