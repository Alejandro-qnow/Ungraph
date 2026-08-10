# Contrato I/O del slot Infer

Ungraph **no** define “la Inferencia” universal. Define un **slot** (`InferenceService`) donde distintas familias (NER, léxico simbólico, LLM, …) emiten el **mismo tipo de artefacto medible**, comparable bajo las Y de capa B.

Ver taxonomía y gates en [`PLAN_MAESTRO.md`](../PLAN_MAESTRO.md).

## Entrada

| Campo | Tipo | Notas |
|-------|------|--------|
| `chunk` | `Chunk` | `id`, `page_content`, `metadata` (filename, `source_document_uid`, …) |
| `entities` (opcional) | `List[Entity]` | Si se pasa a `infer_facts`, evita segunda pasada de extracción |

El pipeline de ingesta llama al slot **después** de chunking + embeddings (etapa Transform). El servicio no debe depender de Neo4j ni de LangChain en `domain/`.

## Salida obligatoria (artefacto)

Cualquier implementación debe poder producir:

1. **`Entity`** — `id`, `name`, `type`, `mentions` (chunk ids), `extraction_method`
2. **`Relation`** — extremos (`source`/`target` id + name), `relation_type`, `confidence`, `provenance_ref` (chunk id), `extraction_method`
3. **`Fact`** — tripleta `subject` / `predicate` / `object`, `confidence`, `provenance_ref`; opcional `object_entity_type`

### `extraction_method` (covariable, no veredicto)

Identifica la familia/impl que produjo el artefacto. Valores actuales en el repo:

| Valor | Familia | Modo `inference_mode` |
|-------|---------|------------------------|
| `spacy` | Transductiva NER | `ner` |
| `lexical_pattern` | Simbólica / léxica | `pattern` |
| (LLM) | Neural | `llm` |

Los internos (tokens, temperatura, hops, autocritica) son **covariables** de coste/explicación; no mueven la portería de las Y.

### Provenance

- `provenance_ref` / `mentions` → anclar al `chunk.id`
- En Neo4j: facts con `DERIVED_FROM` (y `evidence_coverage` en el scorecard)
- `curation_state`: ciclo Extracted → Curated / Invalid (ops; no es Y científica de H_I)

## API del slot

```python
class InferenceService(ABC):
    def extract_entities(self, chunk: Chunk) -> List[Entity]: ...
    def extract_relations(self, chunk: Chunk, entities: List[Entity]) -> List[Relation]: ...
    def infer_facts(self, chunk: Chunk, entities: Optional[List[Entity]] = None) -> List[Fact]: ...
```

Factory: `create_inference_service(settings, language=…)` en `ungraph.application.dependencies`.

## Qué no es el contrato

- Un mega-diseño multiagente o “verify” post-hoc (Capa 2) no sustituye este I/O.
- `hybrid` está declarado pero **no implementado** (`NotImplementedError`).
- Control ET: `inference=none` (sin servicio) — no es una familia Infer; es baseline de H_I.

## Comparación científica

Misma recipe Capa 0 (`capa0_artifact.json`) → swap solo `inference` → Y: `entity_recall`, `relation_pair_recall`, `evidence_coverage`, `answer_correctness` @ top-k.

```bash
uv run --extra experiments --extra infer-en \
  python scripts/run_domain_pipeline.py --domain knowledge_graphs \
  --design family-wave --families ner,pattern
```
