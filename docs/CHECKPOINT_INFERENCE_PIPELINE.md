# Checkpoint — Pipeline de inferencia enriquecida y contexto de documento

**Fecha del checkpoint:** 2026-04-13  
**Paquete:** `ungraph` (ver `pyproject.toml` para versión publicada)

Este documento es un **punto de retomada** para desarrolladores y agentes: resume **qué está hecho**, **dónde está en el código** y **qué sigue**, sin sustituir a [`PRODUCT.md`](PRODUCT.md), [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) ni [`../agent/AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md).

---

## 1. Objetivo de la línea de trabajo

Evolucionar la inferencia (nivel B del producto) hacia un **pipeline gobernado**: contexto global del documento, preguntas de dominio en el prompt del extractor, perfiles ontológicos, trazabilidad en entidades/relaciones, presupuesto explícito de modelos LLM y (más adelante) tools SPARQL / agentes.

El diseño detallado vivió en el plan interno de Cursor (`inference_ontology_architecture`); este archivo es la **foto fija en el repo**.

---

## 2. Qué ya está implementado

### 2.1 Dominio — value objects y servicios

| Pieza | Ubicación |
|-------|-----------|
| `DocumentContext` | [`ungraph/domain/value_objects/document_context.py`](../ungraph/domain/value_objects/document_context.py) |
| `OntologyProfile` | [`ungraph/domain/value_objects/ontology_profile.py`](../ungraph/domain/value_objects/ontology_profile.py) |
| `ExtractionTrace` | [`ungraph/domain/value_objects/extraction_trace.py`](../ungraph/domain/value_objects/extraction_trace.py) |
| `InferenceModelBudget` | [`ungraph/domain/value_objects/inference_model_budget.py`](../ungraph/domain/value_objects/inference_model_budget.py) |
| Alineación ontológica post-extracción | [`ungraph/domain/services/ontology_alignment.py`](../ungraph/domain/services/ontology_alignment.py) |
| Interfaces `DocumentContextService`, `DomainQuestionService`, `OntologyResolver` | [`ungraph/domain/services/`](../ungraph/domain/services/) |

### 2.2 Entidades — trazabilidad opcional

- [`Entity`](../ungraph/domain/entities/entity.py): `ontology_class_uri`, `extraction_method`, `quality_score`, `decision_log_id` (opcionales).
- [`Relation`](../ungraph/domain/entities/relation.py): `ontology_property_uri`, `extraction_method`, `decision_log_id` (opcionales).

### 2.3 Infraestructura — implementaciones por defecto (sin LLM obligatorio)

| Servicio | Rol |
|----------|-----|
| [`HeuristicDocumentContextService`](../ungraph/infrastructure/services/heuristic_document_context_service.py) | Resumen truncado + términos frecuentes como hints |
| [`TemplateDomainQuestionGenerator`](../ungraph/infrastructure/services/template_domain_question_generator.py) | Preguntas de plantilla para enriquecer prompts de extracción |
| [`LlmDocumentContextService`](../ungraph/infrastructure/services/llm_document_context_service.py) | Resumen + dominio vía LLM (JSON), fallback heurístico |
| [`LlmDomainQuestionGenerator`](../ungraph/infrastructure/services/llm_domain_question_generator.py) | Preguntas vía LLM (JSON), fallback a plantillas |
| [`PresetOntologyResolver`](../ungraph/infrastructure/services/preset_ontology_resolver.py) | Perfiles `default`/`general`, `minimal` |
| [`SparqlOntologyResolver`](../ungraph/infrastructure/services/sparql_ontology_resolver.py) | Perfil remoto: dos SELECT (`?label`, opcional `?uri`) para nodos y relaciones |
| [`RoutingOntologyResolver`](../ungraph/infrastructure/services/routing_ontology_resolver.py) | Enruta ``profile_id`` (p. ej. SPARQL) frente al preset por defecto |
| [`sparql_client`](../ungraph/infrastructure/services/sparql_client.py) | POST SPARQL 1.1 → `application/sparql-results+json` (`content` o `form`) |

### 2.4 LLM — LangGraph + LLMGraphTransformer por chunk

- [`build_llm_extraction_graph`](../ungraph/infrastructure/agents/inference_state_graph.py): grafo lineal LangGraph `START → spacy_hints → context → extract → END`. El nodo `spacy_hints`, cuando recibe un servicio con `extract_entities` (p. ej. `SpacyInferenceService` vía fábrica), antepone candidatos NER con [`build_spacy_lexical_hints_addon`](../ungraph/utils/inference_prompt.py). El nodo `context` antepone el snippet de [`build_graph_transformer_context_addon`](../ungraph/utils/inference_prompt.py) cuando hay `document_context_service` y `domain_question_service`. Si falta servicio o hay excepción, el paso correspondiente es no-op (fallback seguro).
- [`LLMInferenceService`](../ungraph/infrastructure/services/llm_inference_service.py): parámetros opcionales `spacy_lexical_service`, `document_context_service` / `domain_question_service` / `context_addon_max_chars`; caché de `GraphDocument` por `chunk.id`; la extracción pasa por el grafo compilado; `extract_entities`, `extract_relations` e `infer_facts` reutilizan la misma salida cuando el `chunk.id` coincide.
- [`create_inference_service`](../ungraph/application/dependencies.py) y [`create_llm_inference_openai`](../ungraph/application/dependencies.py): con `inference_mode=llm` y **`UNGRAPH_INFERENCE_INJECT_SPACY_HINTS`** (default true), intentan cargar `SpacyInferenceService` según el idioma de ingest; si spaCy no está disponible, la extracción LLM sigue sin hints. **`inference_ontology_profile_id`** + [`create_ontology_resolver`](../ungraph/application/dependencies.py) fijan `allowed_nodes` / `allowed_relationships` del LLM (presets o SPARQL si endpoint + dos consultas); fallo SPARQL → preset `general` con log. **`resolve_inference_ontology_profile`** construye el `OntologyProfile` completo (mapas `class_uri_by_label` / `property_uri_by_rel`) y se pasa a `LLMInferenceService` para enriquecer entidades, relaciones y facts MENTIONS con URIs; [`save_facts`](../ungraph/infrastructure/repositories/neo4j_chunk_repository.py) persiste `Entity.type` y `Entity.ontology_class_uri` en nodos `:Entity` cuando el fact lo aporta (`coalesce`); [`save_relations`](../ungraph/infrastructure/repositories/neo4j_chunk_repository.py) (tras los facts) escribe aristas entre entidades con el mismo `name` que en MENTIONS (tipo **nativo** si el nombre es seguro en Cypher, si no **`EXTRACTED_REL`**; ver bullet siguiente).
- Por defecto heurística + plantillas; con **`UNGRAPH_INFERENCE_ENRICH_CONTEXT_WITH_LLM=true`** se usan `LlmDocumentContextService` y `LlmDomainQuestionGenerator` con **uno o dos** `ChatOpenAI` auxiliares según coincidan `resolve_openai_model_for_inference_context` y `resolve_openai_model_for_inference_domain_questions` — **dos llamadas LLM por chunk** en el nodo context además de la extracción.
- `extraction_method="llm"` en entidades/relaciones LLM; spaCy rellena `"spacy"`.
- Persistencia de relaciones inferidas: [`native_neo4j_relationship_type`](../ungraph/utils/neo4j_infer_reltype.py) decide si el tipo del extractor puede ser un **tipo de arista Neo4j nativo** (p. ej. `WORKS_FOR`); si no cumple el patrón seguro, se usa **`EXTRACTED_REL`** y el significado queda en la propiedad `relation_type`. Tras [`consolidate_entities_case_insensitive`](../ungraph/infrastructure/services/neo4j_entity_maintenance_service.py), las aristas incidentes en el nodo duplicado se **re-enlazan** al nodo conservado (incl. `MENTIONS` y tipos nativos).

### 2.5 Configuración global

- [`ungraph/core/configuration.py`](../ungraph/core/configuration.py): `inference_model_budget`, `inference_enrich_context_with_llm`, `inference_inject_spacy_hints`, resolvers de modelo OpenAI por paso + alias `OPENAI_*`; `inference_ontology_profile_id` y `ontology_sparql_*` (endpoint, timeout, `post_format`, consultas inline o `*_file`, `ontology_sparql_profile_id`). Variables `ollama_model_*` reservadas.
- **OpenAI:** además de `UNGRAPH_OPENAI_API_KEY` / `UNGRAPH_OPENAI_MODEL` / `UNGRAPH_OPENAI_BASE_URL`, se admiten los nombres habituales `OPENAI_API_KEY`, `OPENAI_MODEL` y `OPENAI_BASE_URL` como *fallback* cuando no hay valor explícito `UNGRAPH_*` (prioridad `UNGRAPH_`).

### 2.6 Utilidades

- [`ungraph/utils/inference_prompt.py`](../ungraph/utils/inference_prompt.py): `build_graph_transformer_context_addon()` y `build_spacy_lexical_hints_addon()` para snippets inyectados en el `Document` del extractor.

### 2.7 Tests recomendados para retomar

```bash
# Subconjunto estable (imports ungraph)
py -m pytest tests/test_inference_domain.py tests/test_inference_pipeline_services.py tests/test_html_web_pipeline.py tests/test_retrieval_context.py -q
```

**Nota:** parte de `tests/` en el árbol puede apuntar a imports antiguos (`src.*`); el CI/local debe ejecutar el paquete instalado o `PYTHONPATH` con `ungraph`. Los tests anteriores están alineados con el layout actual.

---

## 3. Qué falta (orden sugerido)

1. **Tools** SPARQL/FIBO (y similares) curados en repo para perfiles ontológicos reproducibles.
2. **LangGraph (ampliación):** ciclo Cypher reflexivo + memoria in-process (experimental). *Base v1:* orquestación lineal en [`inference_state_graph.py`](../ungraph/infrastructure/agents/inference_state_graph.py) (extensible a más nodos y tools).
3. **Documentación de API pública** si se exponen nuevos tipos en `ungraph.__init__` (hoy parte de los value objects se importan vía `ungraph.domain.value_objects`).

## 4. Dónde enlazar este checkpoint

| Documento | Acción |
|-----------|--------|
| [`agent/AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md) | Referencia cruzada a este checkpoint |
| [`PRODUCT.md`](PRODUCT.md) | Jerarquía maestra de producto |
| [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) | Horizonte nivel C (plan maestro); entrega prioritaria = A+B |
| Plan Cursor (`.cursor/plans/`) | Diseño ampliado; **este archivo** es la verdad en git para el equipo |

---

## 5. Cómo retomar en una frase

Abre este archivo, ejecuta los tests del §2.7, luego sigue la lista **§3** desde el primer ítem que aún no esté en `main`.
