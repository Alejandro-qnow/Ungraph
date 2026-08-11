# Release Notes - Ungraph

**Última actualización**: 2025-01-XX

---

## 📦 Release v0.1.0 - Estado Actual

### ✅ Completado

**Implementación:**
- Pipeline ETI completo (Extract + Transform + Inference)
- `SpacyInferenceService` implementado (NER básico)
- `LLMInferenceService` implementado (LLM-based, experimental)
- Persistencia de facts en Neo4j
- Trazabilidad básica PROV-O (wasDerivedFrom)
- Código siguiendo Clean Architecture estricta

**Documentación:**
- Abstract profesional (150-200 palabras, IMRAD)
- Research Questions explícitas (RQ1, RQ2, RQ3)
- Definición formal de ETI
- Matriz de experimentación documentada
- Referencias correctas y completas

**Validaciones:**
- ✅ `pytest.ini` corregido
- ✅ Tests básicos funcionan
- ✅ Imports básicos verificados
- ⏳ Pendiente: Build completo, instalación desde wheel, TestPyPI

### 🧪 Experimental Features (v0.1.0)

#### LLMInferenceService (Experimental Preview)

Added LLM-based entity and relationship extraction as alternative to NER-based
extraction. This feature is experimental and serves as foundation for v0.2.0.

**Configuration:**
```bash
# In .env file
UNGRAPH_INFERENCE_MODE=llm
UNGRAPH_OLLAMA_MODEL=llama3.2
UNGRAPH_OLLAMA_BASE_URL=http://localhost:11434
```

**Usage:**
```python
from src.core.configuration import Settings
from src.application.dependencies import create_inference_service

# Configure for LLM mode
settings = Settings(inference_mode="llm")
service = create_inference_service(settings)

# Extract entities and relations
entities = service.extract_entities(chunk)
relations = service.extract_relations(chunk, entities)
facts = service.infer_facts(chunk)
```

**Supported Modes:**
- `inference_mode="ner"`: SpaCy NER-based (default, stable)
- `inference_mode="llm"`: LLM-based with OpenAI (experimental; factory in `create_inference_service`)
- `inference_mode="hybrid"`: Planned for v0.2.0

**Default Schema (LLM mode):**
- Entity types: Person, Organization, Location, Product, Event, Concept
- Relationship types: WORKS_FOR, LOCATED_IN, PART_OF, RELATED_TO, PRODUCED_BY

**Limitations:**
- Basic extraction only (no dynamic examples, confidence scoring, or evaluation)
- Higher latency than NER (~2-5s per chunk)
- Requires an OpenAI API key (`UNGRAPH_OPENAI_*` or `OPENAI_*` env); local LLM (e.g. Ollama) is not wired in the default factory today
- Not recommended for production without evaluation

**Roadmap:**
- v0.2.0: Opik evaluation, confidence scoring, dynamic example selection
- v0.3.0: Hybrid mode (NER + LLM), auto-schema detection

### ⏳ Pendiente para Release

**Validaciones PyPI:**
- Build del paquete (`python -m build`)
- Instalación desde wheel y verificación de imports
- Tests post-instalación en entorno limpio
- Upload a TestPyPI y verificación

**Consolidación de Documentación:**
- Eliminar archivos redundantes en `article/` y `docs/`
- Consolidar archivos de validación y ejemplos

---

## 📋 Archivos Markdown a Eliminar

### Eliminación Directa (4 archivos): ✅ COMPLETADO
1. ✅ `article/ANALISIS_CODIGO_REFERENCIA.md` - Eliminado
2. ✅ `article/RESUMEN_AUDITORIA_GAPS.md` - Eliminado
3. ✅ `article/_ANALISIS_CRITICO_INFERENCIA.md` - Eliminado
4. ✅ `docs/theory/GRAPHRAG_AVANZADO.md` - Eliminado

### Eliminación Después de Consolidación (8 archivos): ✅ COMPLETADO
5. ✅ `docs/validation/cypher-queries-catalog.md` - Consolidado en `validation_summary.md`
6. ✅ `docs/validation/cypher-validation-plan.md` - Consolidado en `validation_summary.md`
7. ✅ `docs/validation/graphrag-compliance.md` - Consolidado en `validation_summary.md`
8. ✅ `docs/validation/problems_resolved.md` - Consolidado en `validation_summary.md`
9. ✅ `docs/validation/validation_results.md` - Consolidado en `validation_summary.md`
10. ✅ `docs/examples/basic-retriever-lexical.md` - Consolidado en `basic-examples.md`
11. ✅ `docs/examples/parent-child-retriever.md` - Consolidado en `advanced-examples.md`
12. ✅ `docs/examples/phase3_search_patterns.md` - Consolidado en `advanced-examples.md`

### Decisión Pendiente:
- `article/CONSOLIDACION_DOCS.md` - Mantener como referencia histórica o eliminar
- `docs/_RELEASE_v0.1.0_COMPLETADO.md` - Mantener como referencia histórica o eliminar

---

## 🎯 Próximos Pasos

1. **Completar validaciones PyPI:**
   - Instalar dependencias de build
   - Ejecutar `python -m build`
   - Verificar instalación desde wheel
   - Subir a TestPyPI

2. **Consolidar documentación:**
   - Eliminar 4 archivos directos
   - Consolidar 8 archivos de validación/ejemplos
   - Decidir sobre documentos históricos

3. **Release final:**
   - Tag de versión v0.1.0
   - Build final para PyPI
   - Publicación en PyPI oficial

---

## 📚 Documentos Principales

**Plan de Release:**
- `article/PLAN_PUBLICACION.md` - Plan maestro del release v0.1.0

**Documentación Científica:**
- `article/ungraph.md` - Documento científico principal
- `article/references.bib` - Referencias bibliográficas

**Documentación Técnica:**
- `docs/README.md` - Índice principal
- `docs/api/` - Documentación de API
- `docs/concepts/` - Conceptos fundamentales
- `docs/guides/` - Guías de usuario
- `docs/theory/` - Teoría (clean-architecture, graphrag, neo4j)
- `docs/validation/README.md` y `validation_summary.md` - Validación
- `docs/examples/basic-examples.md` y `advanced-examples.md` - Ejemplos

---

**Nota**: Este es el único documento de notas para releases. Toda la información detallada está en `article/PLAN_PUBLICACION.md`.

---

## 🔭 Adelanto: Release v0.2.0 (Roadmap)

### 🎯 Objetivo general
Elevar la fase de Inferencia desde extracción transductiva (NER básico) a inferencia semántica (Level 2) con normalización de entidades, relaciones tipadas y trazabilidad avanzada.

### 🚀 Implementación prevista
- **Inferencia (Level 2)**: Extracción de relaciones semánticas con LLM (OpenAI/Claude) y reglas de dominio.
- **Entity Resolution & Linking**: Normalización de variantes ("Apple", "Apple Inc.", "AAPL") y vinculación a KB externas (Wikidata/DBpedia).
- **ConfidenceScorer**: Calibración multi‑factor (modelo, frecuencia, tipo, contexto) y reporte reproducible.
- **ProvenanceChain avanzada**: Lineage detallado (modelo/versión, método, pasos intermedios, timestamp) siguiendo PROV‑O.

### 📏 Validación y métricas
- **Inference Accuracy**: Precision/Recall/F1 sobre facts y relaciones anotadas.
- **Hallucination Rate**: Porcentaje de facts no grounded en las fuentes.
- **RAG/GraphRAG**: QA‑F1, Recall@k, MRR, NDCG en tareas downstream.
- **Calibración de confianza**: Curvas de fiabilidad y análisis de error.

### 🧩 API y compatibilidad
- Nuevos servicios: `EntityResolverService`, `LLMRelationExtractor` (infraestructura) y casos de uso asociados.
- `SpacyInferenceService` se clarifica/alias como `SpacyNERExtractionService` (sin cambios rompientes; alias de transición).
- Configuración: `settings.inference_mode = "ner" | "llm" | "hybrid"` y parámetros de control de coste/latencia.
- Sin breaking changes planificados; enfoque **aditivo** y opt‑in para LLM.

### 📚 Documentación y ejemplos
- Actualización de `article/ungraph.md` con niveles de inferencia (L1–L3) y estado de validación.
- Nuevo `docs/INFERENCE_ROADMAP.md` con arquitectura, métricas y recomendaciones.
- Notebooks y guías de ejemplos para relaciones semánticas y búsqueda Graph‑Enhanced.

### 🗓️ Cronograma tentativo
- Objetivo de salida: **v0.2.0 en Q1 2026**, sujeto a resultados experimentales y validación de métricas.

### ⚠️ Riesgos y mitigaciones
- **Coste de LLM**: Modo `ner` por defecto y banderas de control; caché y límites de uso.
- **Calidad de extracción**: Evaluaciones automáticas + calibración de confianza; revisión humana en muestras críticas.
- **Privacidad/seguridad**: Opciones para inferencia local y control de datos sensibles.

