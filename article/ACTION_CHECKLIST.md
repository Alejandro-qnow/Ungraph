# Action Checklist: Mejoras al Artículo Ungraph

**Basado en:** `article/technical_evaluation.md`  
**Fecha:** 25 de diciembre de 2025

---

## 🔴 CRÍTICO - Hacer ANTES de Experimentos

### ✅ Tarea 1: Corregir Referencias Bibliográficas
**Tiempo estimado:** 1-2 horas  
**Archivos:** `article/ungraph.md`, `article/references.bib`

- [ ] **1.1** Corregir línea 104: cambiar `[2]` duplicado
  - Actual: "GraphRAG Patterns Catalog (Neo4j) [2]"
  - Debe ser: "GraphRAG Patterns Catalog (Neo4j) [3]"
  
- [ ] **1.2** Añadir nueva entrada en `references.bib`:
```bibtex
@misc{neo4j2024graphrag,
  title={GraphRAG Patterns Catalog},
  author={{Neo4j, Inc.}},
  year={2024},
  howpublished={\url{https://graphrag.com/reference/}},
  note={Accessed: 2025-12-25}
}
```

- [ ] **1.3** Renumerar referencias posteriores (W3C PROV será [4], Zhong será [5], etc.)

- [ ] **1.4** Completar DOIs faltantes en `references.bib`:
  - lewis2020rag: añadir DOI
  - peng2024graphrag: añadir DOI
  - zhong2023kg: añadir DOI
  - garcez2019neural: añadir DOI

- [ ] **1.5** Estandarizar formato:
  - Decidir: numérico [1], [2] O autor-año (Ackoff 1989)
  - **Recomendación:** numérico para paper científico
  - Unificar líneas 137-142 con resto del documento

- [ ] **1.6** Verificar que todos los [N] en texto tienen entrada en referencias

**Test de validación:**
```bash
# Contar referencias en texto
grep -o '\[[0-9]\+\]' article/ungraph.md | sort -u

# Contar entradas en references.bib
grep -c '^@' article/references.bib

# Deben coincidir
```

---

### ✅ Tarea 2: Reescribir Abstract
**Tiempo estimado:** 30-45 minutos  
**Archivo:** `article/ungraph.md` (líneas 3-4)

- [ ] **2.1** Expandir abstract a 150-250 palabras

- [ ] **2.2** Seguir estructura IMRAD:
  - [ ] Contexto (1 frase): "Las arquitecturas RAG enfrentan desafíos..."
  - [ ] Gap/Problema (1 frase): "Los pipelines ETL no capturan inferencia explícita..."
  - [ ] Propuesta (2 frases): "Proponemos el patrón ETI... Implementamos en Ungraph..."
  - [ ] Método (1-2 frases): "Evaluamos mediante experimentos en 4 dominios..."
  - [ ] Resultados (2 frases): "[TBD - cuando estén disponibles]"
  - [ ] Conclusión (1 frase): "ETI proporciona un marco coherente..."

- [ ] **2.3** Versión borrador para review (puede incluir "resultados pendientes")

**Template sugerido:**
```markdown
**Abstract:**

Las arquitecturas modernas de Retrieval-Augmented Generation (RAG) enfrentan 
desafíos en la construcción de grafos de conocimiento confiables y trazables. 
Los pipelines tradicionales ETL (Extract-Transform-Load) no capturan explícitamente 
la fase de inferencia necesaria para generar conocimiento justificable. Este trabajo 
propone el patrón Extract-Transform-Inference (ETI) como evolución del ETL, añadiendo 
una fase explícita de inferencia que genera hechos normalizados con trazabilidad 
PROV-O. Implementamos ETI en la librería Ungraph, que construye Lexical Graphs 
sobre Neo4j integrando chunking estratégico, embeddings vectoriales y patrones 
GraphRAG. Evaluamos la efectividad de ETI mediante experimentos reproducibles en 
cuatro dominios (financiero, biomédico, científico y general), comparando pipelines 
control (ET) versus ETI en métricas de recuperación (recall@k, MRR), calidad de QA 
(F1), precisión de inferencia y tasa de hallucination. [Resultados pendientes de 
ejecución experimental]. Los experimentos incluyen ablation studies de tres tipos 
de inferencia (LM-only, symbolic-only, neuro-symbolic) para identificar la estrategia 
óptima por dominio. El patrón ETI demuestra [conclusión pendiente tras experimentos] 
y proporciona un marco coherente para construir sistemas de conocimiento confiables, 
integrando principios de ingeniería del conocimiento, Web semántica (ontologías, PROV) 
y neuro-symbolic computing.
```

---

### ✅ Tarea 3: Formalizar Patrón ETI
**Tiempo estimado:** 2-3 horas  
**Archivo:** `article/ungraph.md` (nueva subsección en "Patrón ETI")

- [ ] **3.1** Añadir "Definición Formal" después de línea 111:

```markdown
### Definición Formal del Patrón ETI

**Definición 1 (Pipeline ETI):**
Un pipeline ETI es una tupla P = (E, T, I, O, M) donde:

- **E (Extractors):** Conjunto de extractores {e₁, e₂, ..., eₙ} donde cada 
  eᵢ: Sources → Documents produce documentos estructurados con metadatos.
  
- **T (Transformers):** Conjunto de transformadores {t₁, t₂, ..., tₘ} donde cada 
  tⱼ: Documents → Chunks produce chunks con embeddings y anotaciones semánticas.
  
- **I (Inference):** Conjunto de modelos de inferencia {i₁, i₂, ..., iₖ} donde cada 
  iₖ: Chunks → (Facts ∪ Relations ∪ Explanations) genera artefactos de conocimiento 
  con señales de confianza y trazabilidad.
  
- **O (Ontology):** Esquema formal que define tipos de entidades, relaciones permitidas, 
  constraints y mapeos a vocabularios estándar (schema.org, PROV-O).
  
- **M (Metadata):** Estructura PROV-O que registra provenance de cada artefacto, 
  incluyendo: entidades derivadas, actividades ejecutadas, agentes responsables y 
  timestamps.

**Propiedades del Pipeline ETI:**
1. **Trazabilidad:** Todo fact f ∈ Facts tiene prov:wasDerivedFrom apuntando a su chunk fuente
2. **Validabilidad:** Todo fact f puede ser verificado contra source s mediante provenance chain
3. **Composabilidad:** Pipelines ETI pueden encadenarse (salida de Iₖ → entrada de Eᵢ₊₁)
4. **Reproducibilidad:** Dado mismo input + config + seed → mismo output
```

- [ ] **3.2** Añadir tabla comparativa ETL vs ETI:

```markdown
### Comparación: ETL Tradicional vs ETI

| Aspecto | ETL Tradicional | ETI (Propuesto) |
|---------|----------------|-----------------|
| **Objetivo** | Integración de datos | Construcción de conocimiento |
| **Input** | Datos estructurados/semi-estructurados | Documentos no estructurados |
| **Output** | Tablas, esquemas relacionales | Grafos de conocimiento + facts |
| **Fases** | Extract → Transform → Load | Extract → Transform → **Inference** |
| **Inferencia** | Implícita en Transform | **Explícita y trazable** |
| **Trazabilidad** | Opcional (metadata) | Obligatoria (PROV-O) |
| **Validación** | Schema validation | Fact validation + coherencia |
| **Semántica** | Schema-level | Ontology-level (OWL, RDF) |
| **Casos de uso** | Data warehousing, BI | RAG, QA, Knowledge Management |
| **Artefactos** | Filas en tablas | Nodos, aristas, tripletas RDF |
| **Explicabilidad** | Logs de transformación | Provenance chains completas |
```

- [ ] **3.3** Especificar criterios de "inferencia":

```markdown
### ¿Qué Constituye una "Inferencia"?

Una operación I es considerada "inferencia" (no mera transformación) si cumple:

1. **Generación de conocimiento nuevo:** Produce facts/relations no explícitos en input
2. **Justificación:** Puede explicar por qué generó cada fact (reasoning chain)
3. **Confianza cuantificada:** Asigna score de confianza probabilística a cada output
4. **Trazabilidad:** Registra provenance completa (qué input, qué modelo, qué prompt)
5. **Validabilidad externa:** Output puede ser verificado contra ground truth o anotadores

**Ejemplos de inferencia:**
- ✅ LLM extrae "CompanyA posee 30% de CompanyB" de texto + normaliza entidades
- ✅ Razonador OWL deduce "PersonX es descendiente de PersonY" vía transitividad
- ✅ ML classifier predice "DocumentZ pertenece a CategoryK" con confidence=0.87

**No son inferencia (son transformación):**
- ❌ Chunking (divide texto pero no genera conocimiento nuevo)
- ❌ Embedding (representa texto pero no extrae facts)
- ❌ Normalización de texto (limpia pero no interpreta)
```

---

### ✅ Tarea 4: Research Questions e Hipótesis
**Tiempo estimado:** 1-2 horas  
**Archivo:** `article/ungraph.md` (nueva sección antes de "Metodología experimental")

- [ ] **4.1** Añadir sección "Research Questions":

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

**RQ4: Comparación de Backends Vectoriales**
¿Cómo se comparan diferentes backends de vector search (Neo4j, FAISS, Milvus, Weaviate) 
en términos de recall@k, latencia y escalabilidad para Lexical Graphs?
```

- [ ] **4.2** Formalizar hipótesis estadísticas:

```markdown
### Hipótesis Estadísticas

#### H1: ETI Mejora Recall (RQ1)
- **H₀:** μ(recall@10_ETI) ≤ μ(recall@10_ET)
- **H₁:** μ(recall@10_ETI) > μ(recall@10_ET)
- **Test:** Paired t-test, one-tailed, α = 0.05
- **Efecto mínimo:** Cohen's d ≥ 0.3 (efecto pequeño-mediano)
- **Muestra:** N ≥ 30 queries por dominio

#### H2: ETI Reduce Hallucination (RQ1)
- **H₀:** μ(hallucination_rate_ETI) ≥ μ(hallucination_rate_ET)
- **H₁:** μ(hallucination_rate_ETI) < μ(hallucination_rate_ET)
- **Test:** Paired t-test, one-tailed, α = 0.05
- **Muestra:** N = 100 facts evaluados por anotadores humanos

#### H3: Neuro-Symbolic Supera LM-only (RQ2)
- **H₀:** μ(F1_neuro-symbolic) ≤ μ(F1_LM-only)
- **H₁:** μ(F1_neuro-symbolic) > μ(F1_LM-only)
- **Test:** Wilcoxon signed-rank (si no normalidad), α = 0.05
- **Muestra:** N ≥ 30 queries por dominio × 4 dominios

#### H4: PROV No Degrada Latencia (RQ3)
- **H₀:** μ(latency_with_PROV) > μ(latency_without_PROV) + 50ms
- **H₁:** μ(latency_with_PROV) ≤ μ(latency_without_PROV) + 50ms
- **Test:** Paired t-test, α = 0.05
- **Threshold:** 50ms considerado aceptable
```

- [ ] **4.3** Definir variables:

```markdown
### Variables del Experimento

#### Variables Independientes (Factores)
1. **Pipeline:** {ET, ETI}
2. **Inference Type:** {none, LM-only, symbolic-only, neuro-symbolic}
3. **Domain:** {finance, biomedical, scientific, general}
4. **Chunking Strategy:** {fixed-512, lexical, semantic, hierarchical}
5. **Backend:** {Neo4j, FAISS, Milvus, Weaviate}

#### Variables Dependientes (Outcomes)
1. **Recuperación:**
   - recall@k (k ∈ {1, 5, 10, 20})
   - MRR (Mean Reciprocal Rank)
   - NDCG@10
   
2. **QA:**
   - F1 score (micro, macro)
   - Exact Match (EM)
   
3. **Inferencia:**
   - Precision, Recall, F1 sobre facts extraídos
   - Inference Accuracy (% facts correctos)
   
4. **Confiabilidad:**
   - Hallucination Rate (% facts no fundamentados)
   - Provenance Coverage (% facts con PROV completo)
   
5. **Performance:**
   - Latencia de query (p50, p95, p99 en ms)
   - Throughput (queries/segundo)
   - Latencia de indexación (docs/segundo)

#### Variables de Control
- Embedding model: "sentence-transformers/all-MiniLM-L6-v2"
- LLM (si aplica): GPT-4 o Claude 3
- Neo4j version: 5.x
- Python version: 3.12
- Hardware: [especificar CPU, RAM, GPU]
- Random seed: 42
```

---

### ✅ Tarea 5: Crear Figuras y Tablas Básicas
**Tiempo estimado:** 3-4 horas  
**Archivos:** `article/ungraph.md`, crear imágenes en `article/figures/`

- [ ] **5.1** Crear diagrama de arquitectura ETI (ASCII o imagen):

```
Opción 1: ASCII art (para markdown)
┌─────────────────────────────────────────────────────┐
│               ETI Pipeline Architecture              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. EXTRACT          2. TRANSFORM       3. INFERENCE│
│  ┌──────────┐       ┌──────────┐       ┌──────────┐│
│  │ Parsers  │──────▶│ Chunkers │──────▶│   LLM    ││
│  │ Loaders  │       │ Embedders│       │ Symbolic ││
│  └──────────┘       └──────────┘       │  Neuro   ││
│       │                  │              └──────────┘│
│       ▼                  ▼                   │       │
│  ┌──────────┐       ┌──────────┐            ▼       │
│  │   File   │       │  Chunk   │       ┌──────────┐│
│  │   Page   │       │ +Embeddi│       │  Facts   ││
│  │+Metadata │       │   ngs    │       │Relations ││
│  └──────────┘       └──────────┘       └──────────┘│
│                                             │        │
└─────────────────────────────────────────────┼────────┘
                                              │
                      ┌───────────────────────▼────────┐
                      │     Neo4j Graph Database       │
                      │  • Nodes (File/Page/Chunk)     │
                      │  • Relations (CONTAINS, HAS_CHUNK)│
                      │  • Vector Index (embeddings)   │
                      │  • PROV-O metadata             │
                      └────────────────────────────────┘
                                    │
                      ┌─────────────▼──────────────┐
                      │  GraphRAG Search Patterns   │
                      │  • Basic Retriever          │
                      │  • Parent-Child Retriever   │
                      │  • Hybrid Search            │
                      └────────────────────────────┘
```

- [ ] **5.2** Crear tabla de datasets:

```markdown
### Tabla 1: Datasets para Evaluación

| Dataset | Dominio | # Docs | # Tokens | # Queries | Licencia | URL |
|---------|---------|--------|----------|-----------|----------|-----|
| EDGAR 10-K (subset) | Financiero | 100 | ~5M | 50 | Public Domain | [SEC EDGAR](https://www.sec.gov/edgar) |
| BioASQ Task 11b | Biomedicina | 200 | ~8M | 100 | Academic | [BioASQ](http://bioasq.org/) |
| arXiv CS.AI (2024) | Científico | 150 | ~6M | 75 | CC BY 4.0 | [arXiv](https://arxiv.org/) |
| MS MARCO Passages | General | 500 | ~2M | 200 | MS Research License | [MS MARCO](https://microsoft.github.io/msmarco/) |

**Total:** 950 documentos, ~21M tokens, 425 queries
**Splits:** 70% train, 15% validation, 15% test (estratificado por dominio)
**Preprocesamiento:** Ver `scripts/prepare_datasets.py`
**Checksums:** Ver `experiments/datasets_manifest.json`
```

- [ ] **5.3** Crear tabla comparativa ETL vs ETI (ya incluida en Tarea 3.2)

- [ ] **5.4** Crear tabla de métricas:

```markdown
### Tabla 2: Métricas de Evaluación

| Categoría | Métrica | Definición | Rango | Objetivo |
|-----------|---------|------------|-------|----------|
| **Recuperación** | recall@10 | Proporción de docs relevantes en top-10 | [0,1] | Maximizar |
| | MRR | Media del reciproco del rank del 1er relevante | [0,1] | Maximizar |
| | NDCG@10 | Normalized Discounted Cumulative Gain | [0,1] | Maximizar |
| **QA** | F1-score | Media armónica de P y R sobre tokens | [0,1] | Maximizar |
| | Exact Match | % respuestas exactamente correctas | [0,1] | Maximizar |
| **Inferencia** | Inference Acc | % facts correctos sobre total generados | [0,1] | Maximizar |
| | Fact Precision | TP / (TP + FP) sobre facts | [0,1] | Maximizar |
| | Fact Recall | TP / (TP + FN) sobre facts | [0,1] | Maximizar |
| **Confiabilidad** | Hallucination Rate | % facts no fundamentados en sources | [0,1] | Minimizar |
| | Provenance Coverage | % facts con trazabilidad PROV completa | [0,1] | Maximizar |
| **Performance** | Query Latency (p95) | 95th percentile de tiempo de query | ms | Minimizar |
| | Throughput | Queries procesadas por segundo | qps | Maximizar |

**Evaluación Humana:**
- 2+ anotadores por fact (sampling estratificado)
- Cohen's κ ≥ 0.7 requerido para confiabilidad
- Desacuerdos resueltos por adjudicación
```

---

## 🟡 IMPORTANTE - Hacer ANTES de Publicar

### ✅ Tarea 6: Formalizar Métricas Específicas
**Tiempo estimado:** 2 horas  
**Archivo:** `article/ungraph.md` (ampliar sección de métricas)

- [ ] **6.1** Definición formal de Hallucination Rate:

```markdown
**Definición 2 (Hallucination Rate):**

Sea F = {f₁, f₂, ..., fₙ} el conjunto de facts generados por el sistema I.
Sea S = {s₁, s₂, ..., sₘ} el conjunto de source documents.

Un fact fᵢ = (subject, predicate, object) es **hallucinated** si:
  ∄ sⱼ ∈ S tal que fᵢ está explícitamente mencionado O 
  puede ser inferido deductivamente de sⱼ según anotadores humanos

**Hallucination Rate = |{fᵢ ∈ F : fᵢ es hallucinated}| / |F|**

**Protocolo de evaluación:**
1. Samplear N facts (estratificado por confidence score y dominio)
2. Presentar a K ≥ 2 anotadores: fact + source documents
3. Anotadores marcan: {grounded, inferred, hallucinated}
4. Calcular Cohen's κ para inter-annotator agreement
5. Requerir κ ≥ 0.7; si no, reentrenar anotadores
6. Resolver desacuerdos por adjudicación con 3er anotador
```

- [ ] **6.2** Definición formal de Graph Coherence:

```markdown
**Definición 3 (Graph Coherence):**

Sea G = (V, E) el knowledge graph generado por pipeline ETI.
Sea O = (C, R, A) la ontología con:
- C: conjunto de clases (tipos de nodos)
- R: conjunto de relaciones permitidas
- A: conjunto de axiomas/constraints

**Métricas de coherencia:**

1. **Inconsistency Rate:**
   IR = |{a ∈ A : a es violado en G}| / |A|
   
   Ejemplos de violaciones:
   - Constraint de cardinalidad: "File tiene máximo 1 author" pero node File:123 tiene 3
   - Constraint de tipo: "HAS_CHUNK.target debe ser Chunk" pero apunta a File
   - Constraint lógico: "author ≠ reader" pero misma persona cumple ambos roles

2. **Ontology Coverage:**
   OC = |{c ∈ C : ∃v ∈ V con type(v) = c}| / |C|
   
   Mide qué proporción de clases de la ontología están representadas en el grafo.

3. **Relation Completeness:**
   RC = |relaciones presentes| / |relaciones esperadas según O|
   
   Donde "esperadas" se define por reglas como:
   - "Si ∃ File entonces debe tener ≥1 Page"
   - "Si ∃ Chunk entonces debe tener embedding"

**Target:** IR < 0.05, OC > 0.80, RC > 0.90
```

### ✅ Tarea 7: Documentar Ontología Formalmente
**Tiempo estimado:** 3-4 horas  
**Archivos:** crear `docs/ontology.md` y `docs/ontology.owl`

- [ ] **7.1** Crear `docs/ontology.md`:

```markdown
# Ontología Ungraph: File-Page-Chunk

## Resumen
Esta ontología define la estructura de conocimiento para Lexical Graphs en Ungraph.

## Clases

### File
**Descripción:** Representa un documento completo ingestado al sistema.

**Propiedades:**
- `path`: String (URI del archivo original)
- `filename`: String
- `size`: Integer (bytes)
- `encoding`: String (e.g., "utf-8")
- `mime_type`: String (e.g., "text/markdown")
- `hash`: String (SHA256 del contenido)
- `created_at`: DateTime
- `ingested_at`: DateTime

**Relaciones salientes:**
- `CONTAINS → Page` (cardinalidad: 1..*)

**Mapeo a vocabularios:**
- `owl:equivalentClass schema:DigitalDocument`

### Page
**Descripción:** Unidad lógica dentro de un File (sección, capítulo, página física).

**Propiedades:**
- `page_number`: Integer
- `title`: String (opcional)
- `section`: String (opcional, e.g., "Introduction")
- `word_count`: Integer
- `language`: String (ISO 639-1, e.g., "en")

**Relaciones salientes:**
- `HAS_CHUNK → Chunk` (cardinalidad: 1..*)

**Relaciones entrantes:**
- `File CONTAINS → Page`

**Mapeo a vocabularios:**
- `rdfs:subClassOf schema:WebPage` (con adaptaciones)

### Chunk
**Descripción:** Fragmento de texto indexable con embedding vectorial.

**Propiedades:**
- `content`: String (texto del chunk)
- `embedding`: Float[] (vector de dimensión D)
- `position`: Integer (posición en Page)
- `chunk_size`: Integer (caracteres)
- `chunk_index`: Integer (índice global)
- `metadata`: JSON (metadata adicional flexible)

**Relaciones salientes:**
- `NEXT_CHUNK → Chunk` (cardinalidad: 0..1)
- `SIMILAR_TO → Chunk` (opcional, con property `score: Float`)

**Relaciones entrantes:**
- `Page HAS_CHUNK → Chunk`

**Constraints:**
- `embedding` debe tener dimensión D constante (e.g., 384 para MiniLM)
- `position` debe ser único dentro de la misma Page
- `NEXT_CHUNK` no debe formar ciclos

## Relaciones

### CONTAINS (File → Page)
- **Dominio:** File
- **Rango:** Page
- **Cardinalidad:** 1..* (File debe contener al menos 1 Page)
- **Inversa:** IS_PART_OF

### HAS_CHUNK (Page → Chunk)
- **Dominio:** Page
- **Rango:** Chunk
- **Cardinalidad:** 1..* (Page debe tener al menos 1 Chunk)
- **Inversa:** BELONGS_TO_PAGE

### NEXT_CHUNK (Chunk → Chunk)
- **Dominio:** Chunk
- **Rango:** Chunk
- **Cardinalidad:** 0..1 (último chunk no tiene next)
- **Propiedades:** Transitiva, no reflexiva, no simétrica
- **Uso:** Preserva secuencialidad para recuperar contexto

### SIMILAR_TO (Chunk → Chunk)
- **Dominio:** Chunk
- **Rango:** Chunk
- **Cardinalidad:** 0..*
- **Propiedades de la relación:**
  - `score`: Float [0,1] (similitud coseno)
  - `computed_at`: DateTime
- **Nota:** Simétrica (si A similar a B, entonces B similar a A con mismo score)

## Axiomas y Constraints

1. **Unicidad de File:**
   - No puede haber dos Files con mismo `hash`

2. **Orden de Chunks:**
   - `NEXT_CHUNK` define orden total dentro de cada Page
   - No ciclos: ∄ camino C₁ →* C₁ via NEXT_CHUNK

3. **Integridad referencial:**
   - Todo Chunk debe pertenecer a exactamente 1 Page
   - Todo Page debe pertenecer a exactamente 1 File

4. **Validación de embeddings:**
   - `len(embedding)` debe ser constante para todos los Chunks del mismo sistema
   - `embedding` no puede tener valores NaN o Inf

## Trazabilidad (PROV-O)

Cada entidad generada registra provenance:

```json
{
  "@context": "http://www.w3.org/ns/prov#",
  "entity": "chunk:123-1-5",
  "prov:wasDerivedFrom": "page:123-1",
  "prov:wasGeneratedBy": {
    "@type": "prov:Activity",
    "prov:used": ["page:123-1", "config:chunking-lexical"],
    "prov:startedAtTime": "2025-01-01T10:00:00Z",
    "prov:endedAtTime": "2025-01-01T10:00:05Z",
    "prov:wasAssociatedWith": {
      "@type": "prov:Agent",
      "prov:actedOnBehalfOf": "user:alejandro"
    }
  }
}
```

## Ejemplos

Ver `docs/examples/` para:
- `example_file_page_chunk.json`: Instancia completa en JSON-LD
- `example_inference_facts.json`: Facts generados por fase I
- `example_prov_bundle.json`: PROV bundle completo
```

- [ ] **7.2** Crear `docs/ontology.owl` (esqueleto):

```xml
<?xml version="1.0"?>
<rdf:RDF xmlns="http://ungraph.io/ontology#"
     xml:base="http://ungraph.io/ontology"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     xmlns:prov="http://www.w3.org/ns/prov#"
     xmlns:schema="http://schema.org/">
    
    <owl:Ontology rdf:about="http://ungraph.io/ontology">
        <rdfs:label>Ungraph Lexical Graph Ontology</rdfs:label>
        <rdfs:comment>Ontology for File-Page-Chunk structure in Ungraph</rdfs:comment>
        <owl:versionInfo>0.1.0</owl:versionInfo>
    </owl:Ontology>
    
    <!-- Classes -->
    <owl:Class rdf:about="http://ungraph.io/ontology#File">
        <rdfs:label>File</rdfs:label>
        <owl:equivalentClass rdf:resource="http://schema.org/DigitalDocument"/>
    </owl:Class>
    
    <owl:Class rdf:about="http://ungraph.io/ontology#Page">
        <rdfs:label>Page</rdfs:label>
        <rdfs:subClassOf rdf:resource="http://schema.org/WebPage"/>
    </owl:Class>
    
    <owl:Class rdf:about="http://ungraph.io/ontology#Chunk">
        <rdfs:label>Chunk</rdfs:label>
        <rdfs:comment>Text fragment with vector embedding</rdfs:comment>
    </owl:Class>
    
    <!-- Object Properties (Relations) -->
    <owl:ObjectProperty rdf:about="http://ungraph.io/ontology#contains">
        <rdfs:domain rdf:resource="http://ungraph.io/ontology#File"/>
        <rdfs:range rdf:resource="http://ungraph.io/ontology#Page"/>
        <rdfs:label>contains</rdfs:label>
    </owl:ObjectProperty>
    
    <owl:ObjectProperty rdf:about="http://ungraph.io/ontology#hasChunk">
        <rdfs:domain rdf:resource="http://ungraph.io/ontology#Page"/>
        <rdfs:range rdf:resource="http://ungraph.io/ontology#Chunk"/>
        <rdfs:label>has chunk</rdfs:label>
    </owl:ObjectProperty>
    
    <owl:ObjectProperty rdf:about="http://ungraph.io/ontology#nextChunk">
        <rdfs:domain rdf:resource="http://ungraph.io/ontology#Chunk"/>
        <rdfs:range rdf:resource="http://ungraph.io/ontology#Chunk"/>
        <rdfs:label>next chunk</rdfs:label>
        <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#TransitiveProperty"/>
    </owl:ObjectProperty>
    
    <!-- Data Properties -->
    <owl:DatatypeProperty rdf:about="http://ungraph.io/ontology#content">
        <rdfs:domain rdf:resource="http://ungraph.io/ontology#Chunk"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>
    
    <owl:DatatypeProperty rdf:about="http://ungraph.io/ontology#filename">
        <rdfs:domain rdf:resource="http://ungraph.io/ontology#File"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>
    
    <!-- More properties... -->
    
</rdf:RDF>
```

- [ ] **7.3** Crear ejemplo JSON-LD en `docs/examples/example_file_page_chunk.json`

### ✅ Tarea 8: Crear Tabla de Datasets
**Tiempo estimado:** 1 hora  
**Archivo:** crear `experiments/datasets.csv`

- [ ] **8.1** Crear CSV con estructura:

```csv
dataset,domain,n_documents,n_tokens_approx,n_queries,license,url,notes,sha256_manifest
edgar_10k_subset,financial,100,5000000,50,Public Domain,https://www.sec.gov/edgar,"Subset of 10-K filings from 2023",abc123...
bioasq_task11b,biomedical,200,8000000,100,Academic Use,http://bioasq.org/,"BioASQ Challenge Task 11b",def456...
arxiv_cs_ai_2024,scientific,150,6000000,75,CC BY 4.0,https://arxiv.org/,"arXiv papers from cs.AI category",ghi789...
msmarco_passages,general,500,2000000,200,MS Research License,https://microsoft.github.io/msmarco/,"MS MARCO passage ranking dataset",jkl012...
```

- [ ] **8.2** Añadir referencia en `article/ungraph.md` línea 34

- [ ] **8.3** Crear scripts de descarga/preparación:
  - `scripts/fetch_edgar.py`
  - `scripts/fetch_bioasq.py`
  - `scripts/fetch_arxiv.py`
  - `scripts/fetch_msmarco.py`

### ✅ Tarea 9: Añadir Sección "Related Work"
**Tiempo estimado:** 2-3 horas  
**Archivo:** `article/ungraph.md` (nueva sección después de Introducción)

- [ ] **9.1** Estructura sugerida:

```markdown
## Estado del Arte y Trabajos Relacionados

### Retrieval-Augmented Generation (RAG)

**RAG clásico (Lewis et al. 2020 [1]):**
Lewis et al. introdujeron RAG combinando retrieval denso (DPR) con generación (BART). 
Su pipeline sigue estructura Extract (DPR indexing) → Load (retrieve) → Generate (BART), 
sin fase explícita de inferencia. Limitaciones: no captura relaciones entre documentos, 
no valida consistencia de facts generados, no provee trazabilidad.

**Diferencia con ETI:** Ungraph añade fase I que genera facts verificables con PROV-O 
antes de indexar, permitiendo validación de consistencia y explicabilidad.

### GraphRAG y Knowledge Graph Construction

**GraphRAG Survey (Peng et al. 2024 [2]):**
Peng et al. revisan métodos que integran KGs con RAG. Identifican tres paradigmas:
1. Graph-enhanced retrieval (usar grafo para expansión)
2. Graph-enhanced generation (usar grafo como context)
3. Graph construction from text (IE + KG building)

ETI se posiciona en paradigma (3) pero con foco en **trazabilidad y validación**.

**KG Construction (Zhong et al. 2023 [4]):**
Zhong et al. survey métodos de construcción automática de KG: IE → KBC → KG refinement. 
Estos trabajos típicamente carecen de:
- Trazabilidad explícita de cada fact a source document
- Evaluación de hallucination en extracción con LLMs
- Integración con vector search para RAG

**Diferencia con ETI:** Ungraph unifica construcción de KG con indexación vectorial, 
asegurando que cada fact tiene provenance PROV-O y puede ser trazado a chunks específicos.

### Neuro-Symbolic Computing

**Garcez et al. 2019 [5]:**
Proponen integrar redes neuronales con razonamiento simbólico para obtener:
- Explicabilidad (symbolic rules)
- Generalización (neural learning)
- Garantías formales (logic constraints)

**Aplicación en ETI:** La fase de inferencia puede ser:
- LM-only (puramente neural)
- Symbolic-only (reglas OWL/SWRL)
- Neuro-symbolic (hybrid: LLM extrae, reasoner valida)

Nuestros experimentos evalúan cuál es más efectivo por dominio.

### Provenance y Trazabilidad

**W3C PROV-O (2013 [3]):**
Estándar para representar provenance de datos. Define:
- Entities (what)
- Activities (how)
- Agents (who)

**Uso en ETI:** Cada Chunk, Fact y Relation registra:
```turtle
:chunk123 prov:wasDerivedFrom :page45 ;
          prov:wasGeneratedBy :chunkingActivity .
:chunkingActivity prov:used :lexicalChunker ;
                  prov:wasAssociatedWith :user_alejandro .
```

**Limitación en literatura:** La mayoría de sistemas RAG/GraphRAG no registran provenance 
de forma estándar, dificultando reproducibilidad y auditoría.

### Comparación Directa con ETL

| Aspecto | ETL Tradicional | GraphRAG Actual | ETI (Ungraph) |
|---------|----------------|-----------------|---------------|
| Inferencia explícita | ❌ | Parcial | ✅ |
| Trazabilidad PROV | ❌ | ❌ | ✅ |
| Validación de facts | ❌ | ❌ | ✅ (opcional) |
| Integración vector+graph | ❌ | ✅ | ✅ |
| Reproducibilidad | Parcial | Parcial | ✅ (seeds+PROV) |

### Posicionamiento de ETI

ETI no reemplaza GraphRAG ni KG construction methods, sino que proporciona un **framework 
metodológico** que:
1. Formaliza la fase de inferencia como componente explícito
2. Requiere trazabilidad end-to-end con PROV-O
3. Integra evaluación de hallucination y coherencia de grafo
4. Soporta evaluación reproducible con experiment tracking (Opik)

**Contribuciones novedosas:**
- Primera formalización del patrón ETI con definición matemática
- Protocolo de reproducibilidad con PROV-O + Opik + OpenAI Evals
- Evaluación de tipos de inferencia (LM vs symbolic vs neuro-symbolic) por dominio
- Ontología File/Page/Chunk con mapeo a vocabularios estándar
```

### ✅ Tarea 10: Definir Variables Experimentales
**Tiempo estimado:** 1 hora  
**Archivo:** Ya cubierto en Tarea 4.3

---

## 🟢 DESEABLE - Para Pulido Final

### ✅ Tarea 11: Añadir Métricas de Eficiencia
- [ ] Especificar latencia de indexación (docs/segundo)
- [ ] Especificar query latency (p50, p95, p99)
- [ ] Especificar throughput (qps)
- [ ] Memory footprint (RAM/VRAM)
- [ ] Storage overhead (embeddings + grafo vs texto plano)

### ✅ Tarea 12: Discutir Escalabilidad
- [ ] Límites de Neo4j vector index (testear hasta N millones de vectors)
- [ ] Estrategias de batch processing
- [ ] Caching de queries frecuentes
- [ ] Comparación con arquitecturas distribuidas

### ✅ Tarea 13: Crear Archivo OWL
- [ ] Ya cubierto en Tarea 7.2

### ✅ Tarea 14: Ejemplos JSON-LD
- [ ] Crear `docs/examples/example_file_page_chunk.json`
- [ ] Crear `docs/examples/example_inference_facts.json`
- [ ] Crear `docs/examples/example_prov_bundle.json`

### ✅ Tarea 15: Containerización Docker
- [ ] Crear `Dockerfile` para entorno reproducible
- [ ] Incluir Neo4j, Python, dependencies
- [ ] Documentar en sección "Reproducibilidad"

### ✅ Tarea 16: Pre-registro Protocolo
- [ ] Crear cuenta en OSF.io
- [ ] Registrar protocolo experimental antes de ejecutar
- [ ] Obtener DOI de pre-registro
- [ ] Añadir referencia en artículo

---

## 📊 Seguimiento de Progreso

### Tareas Completadas: 0/16

- [ ] Tarea 1: Corregir referencias ⏱️ 1-2h
- [ ] Tarea 2: Reescribir abstract ⏱️ 30-45min
- [ ] Tarea 3: Formalizar ETI ⏱️ 2-3h
- [ ] Tarea 4: Research questions ⏱️ 1-2h
- [ ] Tarea 5: Figuras y tablas ⏱️ 3-4h
- [ ] Tarea 6: Formalizar métricas ⏱️ 2h
- [ ] Tarea 7: Documentar ontología ⏱️ 3-4h
- [ ] Tarea 8: Tabla de datasets ⏱️ 1h
- [ ] Tarea 9: Related Work ⏱️ 2-3h
- [ ] Tarea 10: Variables ⏱️ (cubierto en Tarea 4)
- [ ] Tarea 11: Métricas eficiencia ⏱️ 1h
- [ ] Tarea 12: Escalabilidad ⏱️ 1h
- [ ] Tarea 13: OWL ⏱️ (cubierto en Tarea 7)
- [ ] Tarea 14: JSON-LD examples ⏱️ 1-2h
- [ ] Tarea 15: Docker ⏱️ 2h
- [ ] Tarea 16: Pre-registro ⏱️ 1h

**Tiempo total estimado:** ~25-35 horas

---

## 🎯 Priorización Sugerida

### Semana 1 (8-10 horas)
1. Tarea 1 (referencias) - 2h
2. Tarea 2 (abstract) - 1h
3. Tarea 3 (ETI) - 3h
4. Tarea 4 (RQs) - 2h

### Semana 2 (10-12 horas)
5. Tarea 5 (figuras) - 4h
6. Tarea 6 (métricas) - 2h
7. Tarea 8 (datasets) - 1h
8. Tarea 9 (related work) - 3h

### Semana 3 (8-10 horas)
9. Tarea 7 (ontología) - 4h
10. Tarea 11-12 (eficiencia, escalabilidad) - 2h
11. Tarea 14 (JSON-LD) - 2h

### Opcional (4-5 horas)
12. Tarea 15 (Docker) - 2h
13. Tarea 16 (OSF pre-registro) - 1h

---

**Documento mantenido en:** `article/ACTION_CHECKLIST.md`  
**Última actualización:** 2025-12-25
