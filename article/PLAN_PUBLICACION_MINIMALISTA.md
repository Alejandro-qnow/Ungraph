# Plan de Publicación Minimalista - Ungraph v0.1.0

**Objetivo**: Preparar primera versión publicable del artículo sin crear código nuevo.

**Principio**: Ajustar documentación para reflejar lo que existe, no prometer lo que no está implementado.

---

## 📊 Análisis: Código vs Documentación

### ✅ Lo que SÍ está implementado

1. **Extract (E)**: ✅
   - `LangChainDocumentLoaderService` - carga documentos
   - Soporte Markdown, TXT, Word
   - Detección de encoding

2. **Transform (T)**: ✅
   - `ChunkingService` - múltiples estrategias
   - `EmbeddingService` - HuggingFace embeddings
   - Persistencia en Neo4j (File → Page → Chunk)

3. **Búsqueda GraphRAG básica**: ✅
   - Basic Retriever
   - Parent-Child Retriever
   - Hybrid Search
   - Metadata Filtering

4. **Arquitectura**: ✅
   - Clean Architecture implementada
   - Tests funcionando
   - API pública (`ungraph.ingest_document()`, `ungraph.search()`)

### ❌ Lo que NO está implementado

1. **Inference (I) explícita**: ❌
   - No hay servicio de inferencia
   - No hay extracción de facts/relations
   - Solo mock en `run_experiment.py`

2. **PROV-O completo**: ❌
   - Solo estructura básica en `prov_bundle.json`
   - No hay integración con código principal
   - No hay trazabilidad end-to-end

3. **Experimentos reales**: ❌
   - Solo demos con datos mock
   - No hay datasets reales (EDGAR, BioASQ, etc.)
   - No hay métricas calculadas

4. **Ontología formal**: ❌
   - No existe `docs/ontology.md`
   - No existe `docs/ontology.owl`
   - Solo estructura implícita en código

---

## 🎯 Estrategia: Ajustar Documentación, No Código

### Opción A: Artículo como "Propuesta + Implementación Parcial" (RECOMENDADO)

**Ventajas**:
- Honesto sobre estado actual
- Permite publicar sin implementar todo
- Establece roadmap claro

**Estructura del artículo**:
1. **Introducción**: ETI como patrón propuesto
2. **Estado del Arte**: Revisión de RAG/GraphRAG
3. **Patrón ETI**: Definición formal + justificación
4. **Implementación Parcial**: 
   - ✅ Extract + Transform implementado
   - ⚠️ Inference propuesta (mock/demo)
   - 🔄 PROV-O en desarrollo
5. **Experimentos Planificados**: Metodología (sin resultados)
6. **Conclusiones**: Contribución conceptual + roadmap

### Opción B: Artículo como "Sistema ET (sin I)"

**Ventajas**:
- 100% honesto sobre implementación
- Enfoque en Extract + Transform
- Menos ambicioso, más realista

**Desventajas**:
- Pierde el "hook" de ETI como innovación
- Menos impacto potencial

**Recomendación**: **Opción A** - mantiene la propuesta innovadora pero es honesto sobre implementación.

---

## 📋 Tareas Críticas (Solo Documentación)

### 🔴 PRIORIDAD 1: Corregir Referencias (2 horas)

**Problema**: Referencias duplicadas, faltantes, formato inconsistente.

**Acciones**:
1. Corregir línea 104 de `article/ungraph.md`:
   - Cambiar `[2]` duplicado → `[3]` para Neo4j GraphRAG
2. Añadir a `article/references.bib`:
   ```bibtex
   @misc{neo4j2024graphrag,
     title={GraphRAG Patterns Catalog},
     author={{Neo4j, Inc.}},
     year={2024},
     howpublished={\url{https://graphrag.com/reference/}},
     note={Accessed: 2025-12-25}
   }
   ```
3. Renumerar referencias posteriores
4. Completar DOIs faltantes (buscar en Google Scholar)
5. Estandarizar formato: numérico `[1]`, `[2]` en todo el documento

**Archivos**:
- `article/ungraph.md` (líneas 102-106, 137-142)
- `article/references.bib`

---

### 🔴 PRIORIDAD 2: Reescribir Abstract (1 hora)

**Problema**: Abstract actual es muy breve y no sigue estructura IMRAD.

**Nuevo abstract** (150-200 palabras):
```
Las arquitecturas modernas de Retrieval-Augmented Generation (RAG) enfrentan 
desafíos en la construcción de grafos de conocimiento confiables y trazables. 
Este trabajo propone el patrón Extract-Transform-Inference (ETI) como evolución 
del tradicional ETL, añadiendo una fase explícita de inferencia que genera hechos 
normalizados con trazabilidad PROV-O. 

Presentamos una implementación parcial de ETI en la librería Ungraph, que 
construye Lexical Graphs sobre Neo4j integrando chunking estratégico, embeddings 
vectoriales y patrones GraphRAG básicos. La implementación actual cubre las fases 
Extract y Transform; la fase Inference se propone conceptualmente y se valida 
mediante demos con datos mock.

[Para versión completa:] Evaluamos la efectividad mediante experimentos reproducibles 
en cuatro dominios (financiero, biomédico, científico y general), comparando pipelines 
control (ET) versus ETI en métricas de recuperación (recall@k, MRR), calidad de QA 
(F1), precisión de inferencia y tasa de hallucination. [Resultados pendientes de 
ejecución experimental].

El patrón ETI proporciona un marco coherente para construir sistemas de conocimiento 
confiables, integrando principios de ingeniería del conocimiento, Web semántica 
(ontologías, PROV) y neuro-symbolic computing.
```

**Archivo**: `article/ungraph.md` (líneas 3-4)

---

### 🟡 PRIORIDAD 3: Aclarar Estado de Implementación (2 horas)

**Problema**: El artículo no distingue entre "propuesto" y "implementado".

**Acciones**:
1. Añadir sección "Estado de Implementación" después de línea 130:
   ```markdown
   ## Estado de Implementación
   
   La librería Ungraph implementa actualmente las fases **Extract** y **Transform** 
   del patrón ETI:
   
   - ✅ **Extract**: Carga de documentos con múltiples formatos y detección de encoding
   - ✅ **Transform**: Chunking inteligente, generación de embeddings, persistencia en Neo4j
   - ⚠️ **Inference**: Propuesta conceptualmente; implementación mock disponible para demos
   
   La fase de Inferencia se implementará en futuras versiones con soporte para:
   - Extracción de facts/relations mediante LLMs
   - Razonamiento simbólico (OWL/SWRL)
   - Pipelines neuro-symbolic híbridos
   - Trazabilidad completa con PROV-O
   
   Los experimentos documentados en este artículo están planificados y se ejecutarán 
   una vez completada la implementación de la fase Inference.
   ```

2. Actualizar sección "Arquitectura propuesta" (línea 116):
   - Marcar qué está implementado vs propuesto

**Archivo**: `article/ungraph.md`

---

### 🟡 PRIORIDAD 4: Añadir Research Questions (1 hora)

**Problema**: No hay RQs explícitas (requerido para paper científico).

**Acciones**:
1. Añadir sección antes de "Metodología experimental":
   ```markdown
   ## Research Questions e Hipótesis
   
   ### Research Questions
   
   **RQ1: Efectividad de la Fase de Inferencia**
   ¿Añadir una fase explícita de inferencia (I) mejora la calidad de recuperación y 
   respuesta de preguntas comparado con pipelines que solo realizan extracción y 
   transformación (ET)?
   
   **RQ2: Tipos de Inferencia por Dominio**
   ¿Qué tipo de inferencia (LM-only, symbolic-only, neuro-symbolic) es más efectiva 
   para diferentes dominios de conocimiento (financiero, biomédico, científico, general)?
   
   **RQ3: Trade-off Trazabilidad vs Performance**
   ¿La trazabilidad completa con PROV-O mejora la confianza y explicabilidad del sistema 
   sin sacrificar significativamente el rendimiento (latencia, throughput)?
   
   **Nota**: Estas research questions guiarán los experimentos futuros una vez completada 
   la implementación de la fase Inference.
   ```

**Archivo**: `article/ungraph.md` (nueva sección)

---

### 🟡 PRIORIDAD 5: Formalizar Patrón ETI (2 horas)

**Problema**: Falta definición matemática formal.

**Acciones**:
1. Añadir después de línea 111:
   ```markdown
   ### Definición Formal del Patrón ETI
   
   **Definición 1 (Pipeline ETI):**
   Un pipeline ETI es una tupla P = (E, T, I, O, M) donde:
   
   - **E (Extractors)**: Conjunto de extractores {e₁, e₂, ..., eₙ} donde cada 
     eᵢ: Sources → Documents produce documentos estructurados con metadatos.
   
   - **T (Transformers)**: Conjunto de transformadores {t₁, t₂, ..., tₘ} donde cada 
     tⱼ: Documents → Chunks produce chunks con embeddings y anotaciones semánticas.
   
   - **I (Inference)**: Conjunto de modelos de inferencia {i₁, i₂, ..., iₖ} donde cada 
     iₖ: Chunks → (Facts ∪ Relations ∪ Explanations) genera artefactos de conocimiento 
     con señales de confianza y trazabilidad.
   
   - **O (Ontology)**: Esquema formal que define tipos de entidades, relaciones permitidas, 
     constraints y mapeos a vocabularios estándar (schema.org, PROV-O).
   
   - **M (Metadata)**: Estructura PROV-O que registra provenance de cada artefacto, 
     incluyendo: entidades derivadas, actividades ejecutadas, agentes responsables y timestamps.
   
   **Propiedades del Pipeline ETI:**
   1. **Trazabilidad**: Todo fact f ∈ Facts tiene prov:wasDerivedFrom apuntando a su chunk fuente
   2. **Validabilidad**: Todo fact f puede ser verificado contra source s mediante provenance chain
   3. **Composabilidad**: Pipelines ETI pueden encadenarse (salida de Iₖ → entrada de Eᵢ₊₁)
   4. **Reproducibilidad**: Dado mismo input + config + seed → mismo output
   ```

2. Añadir tabla comparativa ETL vs ETI (simple, en markdown)

**Archivo**: `article/ungraph.md`

---

## 🟢 Tareas Opcionales (Solo si hay tiempo)

### Opcional 1: Crear Tabla de Datasets (30 min)
- Crear `article/experiments/datasets.csv` con placeholders
- Mencionar que son datasets planificados

### Opcional 2: Añadir Diagrama ASCII (30 min)
- Diagrama simple de arquitectura ETI (ASCII art)
- Mostrar flujo Extract → Transform → Inference

### Opcional 3: Documentar Ontología Básica (1 hora)
- Crear `docs/ontology.md` mínimo
- Describir File/Page/Chunk (ya está en código)
- NO crear OWL completo (no necesario para v0.1.0)

---

## ❌ Lo que NO hacer

1. ❌ **NO implementar fase Inference** - fuera de scope para v0.1.0
2. ❌ **NO crear PROV-O completo** - solo documentar estructura básica
3. ❌ **NO ejecutar experimentos reales** - mantener como "planificados"
4. ❌ **NO crear nuevos servicios** - trabajar con lo existente
5. ❌ **NO añadir figuras complejas** - ASCII simple es suficiente

---

## 📅 Timeline Estimado

**Total: 6-8 horas de trabajo**

- Día 1 (2h): Prioridad 1 (Referencias)
- Día 1 (1h): Prioridad 2 (Abstract)
- Día 2 (2h): Prioridad 3 (Estado implementación)
- Día 2 (1h): Prioridad 4 (Research Questions)
- Día 3 (2h): Prioridad 5 (Formalización ETI)
- Día 3 (1h): Opcionales si hay tiempo

---

## ✅ Checklist Final

Antes de considerar "publicable":

- [ ] Referencias corregidas y validadas
- [ ] Abstract reescrito (150-200 palabras, IMRAD)
- [ ] Sección "Estado de Implementación" añadida
- [ ] Research Questions explícitas
- [ ] Definición formal de ETI añadida
- [ ] Tabla comparativa ETL vs ETI
- [ ] Documento revisado para consistencia
- [ ] Sin promesas de funcionalidades no implementadas

---

## 🎯 Resultado Esperado

**Artículo publicable que**:
1. ✅ Propone ETI como patrón innovador
2. ✅ Documenta implementación parcial (ET) honestamente
3. ✅ Establece roadmap para fase Inference
4. ✅ Tiene rigor científico (RQs, definiciones formales)
5. ✅ Referencias correctas y completas
6. ✅ Abstract profesional

**No promete**:
- ❌ Implementación completa de ETI
- ❌ Resultados experimentales
- ❌ PROV-O completo integrado

---

**Última actualización**: 2025-12-25
**Versión objetivo**: Artículo publicable para workshop/ArXiv (no conference con resultados)

