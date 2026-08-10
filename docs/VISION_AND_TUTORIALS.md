# Visión de producto y plan de tutoriales (desarrollo paralelo)

**Última revisión:** 2026-04-12  
**Paquete de referencia:** `ungraph` 0.1.5 (`pyproject.toml`, `ungraph/__init__.py`)

**Jerarquía de documentos maestros:** [`PRODUCT.md`](PRODUCT.md) define *finalidad*, historias y casos de uso; **este archivo** ancla *visión*, niveles de promesa (§3), tutoriales y aprendizaje del grafo; [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) recoge el **horizonte nivel C** (fuera del alcance de entrega prioritario A+B); [`../agent/AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md) es el *plan técnico de ejecución* (skills, prioridades §8, visualización §7).

---

## 1. Propósito de este documento

Este archivo es el **punto de anclaje** para:

- La **visión** de cómo debe crecer Ungraph como librería y como material de aprendizaje.
- La **fecha de trabajo** y el contexto que sigue al desarrollo (sin sustituir el versionado semántico del paquete).
- El **plan de tutoriales** pensado para **usar Ungraph mientras se desarrolla**: los notebooks y guías pueden adelantarse al código o marcar límites claros entre lo ya soportado y lo exploratorio.
- El **aprendizaje hacia el mejor grafo** (hipótesis de representación, ciclo de evaluación y construcción asistida; §8).

No reemplaza el changelog por versión ni los documentos de publicación del artículo; complementa la documentación técnica en `docs/` y el trabajo del agente en `agent/`.

---

## 2. Norte estratégico: ingestión, ontologías y memoria como interfaz

**Núcleo:** Ungraph es un **framework de ingestión de datos no estructurados hacia un grafo** (Neo4j), con patrón **Extract–Transform–Inference** y recuperación tipo GraphRAG. El objetivo a largo plazo no es sustituir un producto cerrado de “memoria de agente”, sino **habilitar** flujos donde el grafo sea la **fuente de verdad estructurada** y, a la vez, una **interfaz** sobre la que se evalúa y se conecta lo generado por agentes.

**Ontologías y grafo base:** A partir de **análisis previo** del contenido y del **tipo de dato**, el sistema puede **detectar** o **sugerir** ontologías (vocabularios de clases y relaciones). Con ello se construye un **grafo estructural base**; si se desea, el usuario o el pipeline puede **materializar** el grafo siguiendo **esas ontologías de entrada sugeridas**. La iteración apunta a un proceso **cada vez más autónomo** (menos delineación manual del esquema), sin perder trazabilidad.

**Patrones como “ORM” avanzado:** El **generador de patrones** (`GraphPattern` y evoluciones) es la capa de **mapeo** desde datos no estructurados (texto, conversación, documentos) a **nodos y relaciones tipados**. La analogía útil es un **ORM declarativo** para grafos: el patrón define el esquema de persistencia y las reglas de merge. Los **tipos de entidad** pueden diferenciarse (p. ej. evidencia documental vs. inferencia vs. turno de agente) para no mezclar semánticas incompatibles.

**Memoria agéntica en el sentido Ungraph:** Cuando el **conector** de ingesta es usado por un **LLM** u otra herramienta, el grafo debe poder registrar **metadatos de evaluación**, no solo contenido. Se prevé **flaggear en el grafo atributos de riesgo de alucinación** (o equivalentes de confianza / incertidumbre) para analizar qué entidades o mensajes generados por un agente son **válidos** o se **conectan correctamente** con la fuente de verdad. El resultado es un **grafo enlazado por evaluación agéntica y compromiso ontológico**: trazabilidad (p. ej. PROV-O), **temporalidad** en nodos y relaciones cuando haga falta, y vínculos explícitos a la evidencia fuente.

**Límites honestos:** Esta visión implica **gobernanza** (estados propuesto vs. confirmado, políticas de merge, contradicciones). No se promete en un solo release; puede implementarse **por fases** (flags de riesgo, tipos de entidad separados, sugerencia de ontología en notebooks) hasta estabilizar APIs públicas.

---

## 3. Niveles de la promesa (A / B / C)

Una librería **“estable”** en el sentido Ungraph no significa “implementa ya todo el horizonte de producto”, sino **contrato y comportamiento predecibles** en un subconjunto acotado, con extras y fases posteriores claramente etiquetados. La misma promesa se despliega en **tres niveles de madurez**; no confundir **nivel A** con un release semver concreto: es criterio de **alcance prometido**, alineado con [`PRODUCT.md`](PRODUCT.md).

**Promesa central (formulación única):** *Ungraph es un adaptador de datos no estructurados a grafos de conocimiento en Neo4j mediante patrones definibles, pipeline ETI, recuperación GraphRAG y extensiones opcionales; habilita capas semántica y estructural para sistemas que hagan GraphRAG sobre el grafo, sin sustituir por sí misma la política de memoria de un agente externo.*

| Nivel | Nombre | Qué incluye | Relación con “estable” |
|-------|--------|-------------|-------------------------|
| **A** | **Núcleo / mesa** | Patrones como “ladrillos” (`GraphPattern`), ingestión, persistencia en Neo4j, búsqueda (texto / vector / híbrido / patrones), **embeddings configurables** y documentación alineada con tests. Preparación de texto y chunking como **estrategias** documentadas, no como “optimizador mágico” universal. | Aquí vive la **credibilidad** de la librería: API predecible, reproducibilidad, extras explícitos (`[gds]`, `[infer]`, futuro `[viz]`). |
| **B** | **Productivo** | Extracción de **entidades y relaciones** (p. ej. spaCy, LLM / graph transformer) bajo el mismo modelo de patrones; **trazabilidad** a evidencia; **evaluación** de extracción (scores, comparadores frente a reglas o referencias); **sugerencias** de chunking/patrón como ayuda; flujos más profundos con **ontologías** y revisión de contenido bajo gobernanza (estados, riesgo). | Extiende el núcleo sin redefinirlo; puede distribuirse en extras o módulos bien acotados. |
| **C** | **Evolutivo / investigación** | **Recomendación** de estructuras de grafo más adecuadas según **mediciones** (grafo, consultas exitosas, métricas RAG/GraphRAG); **automejora** guiada por datos extraídos; interoperabilidad con **grafos de conocimiento abiertos** y estándares donde aplique; **MCP** u otras herramientas como superficie opcional; capas de **calidad**, legibilidad y **perfilado** de datos; integración agéntica avanzada (p. ej. herramienta para sistemas tipo memoria de largo plazo) **sin** prometer equivalencia con productos cerrados de terceros. | Exploratorio hasta que existan APIs mínimas, datasets de evaluación y criterios de éxito; enlazado con el §8 (aprendizaje del mejor grafo). |

**Línea roja de comunicación:** Ungraph **habilita** memoria agéntica y retrievers de alta calidad **dentro de las políticas y patrones que el integrador define**; no se afirma sustitución de soluciones completas de memoria (p. ej. productos tipo “palacio” o grafos dinámicos comerciales) salvo que exista implementación y comparación explícitas.

**Alcance priorizado del plan maestro:** el esfuerzo de producto y de releases **prioriza nivel A y nivel B**. El nivel C se documenta como **horizonte** en [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) y en §8 más abajo; no es obligatorio avanzar C en cada versión.

---

## 4. Documentos relacionados (contexto)

| Recurso | Rol |
|--------|-----|
| [PRODUCT.md](PRODUCT.md) | **Documento maestro de producto:** finalidad, niveles A/B/C (resumen), historias de usuario y casos de uso. El “qué” y “para quién”. Alcance de entrega **prioritario A+B**; C como horizonte en `ROADMAP_LEVEL_C`. |
| [ROADMAP_LEVEL_C.md](ROADMAP_LEVEL_C.md) | **Plan maestro — horizonte nivel C:** fases exploratorias (medición, MCP, recomendación); **no** compromiso de cierre simultáneo con B. |
| [../agent/AGENT_SKILLS.md](../agent/AGENT_SKILLS.md) | Prioridades técnicas (**§8**), skills, **§7** módulo de visualización (yFiles for Jupyter) y exportación de grafos. **Artefacto vivo** para quien desarrolla o asiste con agentes. |
| [../ANALYSIS_120426.md](../ANALYSIS_120426.md) | Análisis crítico del estado del paquete frente a una librería “madura” (reproducibilidad, CI, tipado, estabilidad). Sirve de **línea base honesta**, no de hoja de marketing. |
| [theory/sp-graphrag.md](theory/sp-graphrag.md) | Fundamentos y patrones GraphRAG alineados con referencias externas (p. ej. catálogo [graphrag.com](https://graphrag.com/reference/graphrag/)). |
| [guides/sp-ingestion.md](guides/sp-ingestion.md), [guides/sp-custom-patterns.md](guides/sp-custom-patterns.md) | Ingesta y patrones de grafo ya documentados en profundidad. |

---

## 5. Principios de los tutoriales “en vivo”

1. **Tres etiquetas por pieza:** cada tutorial o sección debe indicar si es **Implementado** (soportado por la API/código actual), **Parcial** (flujo posible con extras o limitaciones), o **Exploratorio** (notebook primero; la formalización en código viene después).
2. **Sin prometer API inexistente:** lo exploratorio se presenta como diseño y experimentación, enlazando issues o decisiones de diseño cuando existan.
3. **Misma verdad que el código:** si cambia `ingest_document`, `search_with_pattern` o los extras (`[gds]`, `[infer]`), se actualiza primero la referencia técnica y luego el tutorial correspondiente.
4. **Carpeta futura:** el contenido pedagógico concreto vivirá bajo `docs/tutoriales/` (por crear), con índice y, si aplica, espejo bilingüe siguiendo el criterio del resto de `docs/` (`sp-` / `en-`).

---

## 6. Mapa de tutoriales (visión)

La numeración siguiente es la **hoja de ruta pedagógica** acordada; el estado refleja el conocimiento del código y la documentación a la fecha de revisión de este documento.

### 6.1 Primer grafo

- **Contenido:** configuración (`configure`), ingesta mínima, verificación en Neo4j.
- **Estado:** **Implementado** — núcleo estable de la API pública.

### 6.2 Personalizar el patrón de ingestión

- **Contenido:** `GraphPattern`, nodos/relaciones, patrón por defecto `FILE_PAGE_CHUNK`, patrones personalizados.
- **Estado:** **Implementado** — ver `predefined_patterns`, guías de patrones personalizados.

### 6.3 Patrones GraphRAG (alineación con el ecosistema GraphRAG)

- **Contenido:** correspondencia entre patrones de referencia (p. ej. Basic, Parent-Child, Community Summary, Graph-Enhanced) y lo que expone Ungraph (`search_with_pattern`, Neo4j, GDS opcional).
- **Estado:** **Parcial** — la teoría en `docs/theory/sp-graphrag.md` puede describir más patrones de los que tienen un retriever homónimo cerrado en código; los tutoriales deben incluir una tabla patrón ↔ API ↔ prerequisitos.

### 6.4 Ingesta por tipo de fuente

- **Contenido:** un hilo por familia de fuente (p. ej. PDF, Markdown/Word, texto; en el futuro CSV, imágenes, importación desde otro grafo u ontología).
- **Estado:** **Implementado** para `.md`, `.txt`, `.doc`/`.docx`, `.pdf` (PDF vía Docling cuando esté disponible). **Exploratorio** para CSV, imágenes y fuentes de conocimiento estructurado — la interfaz de dominio ya menciona extensiones futuras; los tutoriales pueden prototipar loaders o pipelines sin afirmar que están en el wheel por defecto.

### 6.5 Inferencia y “motores de razonamiento”

| Subtema | Estado orientativo |
|--------|---------------------|
| OpenAI / Ollama / elección de modelos | **Parcial** — configuración Ollama y vías LLM existen; el tutorial cubre cableado y buenas prácticas, no un cliente propio para cada proveedor. |
| LangChain y retrievers | **Parcial** — integración natural con loaders y `LLMInferenceService`. |
| LangGraph (orquestación) | **Exploratorio** — dependencia declarada en el proyecto; integración formal como parte estable de Ungraph no asumida sin revisión explícita. |
| RDF / OWL / SHACL / razonamiento lógico “nativo” | **Exploratorio** — no hay capa ontológica en el núcleo; encaja investigación y diseño futuro. |
| Analítica de grafo (GDS, comunidades, métricas) | **Parcial** — extra `ungraph[gds]` y patrones que lo requieren; documentar prerequisitos Neo4j. |

### 6.6 MCP (herramientas, Neo4j al esquema, GDS)

- **Contenido:** uso de MCP Neo4j genérico, scripts de ejemplo, visión de herramientas que conozcan el esquema Ungraph.
- **Estado:** **Exploratorio / Parcial** — hay material de ejemplo y validación; un servidor MCP “oficial” de Ungraph sería nueva superficie y debe tratarse aparte.
- **Horizonte nivel C (plan maestro, fuera de entrega prioritaria B):** [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) — fases C0–C5 (medición, eval–refinar, MCP en fase tardía).

---

## 7. Relación con el desarrollo iterativo

- Los **tutoriales Implementados** son la verificación de que el “camino feliz” sigue siendo cierto tras cada release.
- Los **Parciales** guían prioridades (documentar límites, mejorar mensajes de error, rellenar huecos de API).
- Los **Exploratorios** alimentan decisiones de diseño y, cuando maduran, pasan a issues, PRs y eventualmente a secciones **Implementado** en este mapa.

Actualizar **este documento** cuando cambie la visión del plan de tutoriales o la lista de estados; actualizar **`agent/AGENT_SKILLS.md`** cuando cambien las prioridades de ingeniería; actualizar **`ANALYSIS_*.md`** solo cuando se quiera una nueva foto crítica del paquete (no en cada commit).

---

## 8. Aprendizaje para el mejor grafo

**Hipótesis central:** para un mismo corpus no estructurado no existe un único grafo “correcto” de antemano; la pregunta operativa es **qué grafo representa mejor esa data** según tareas downstream (recuperación, razonamiento, trazabilidad, coste). Ungraph, como constructor declarativo (`GraphPattern`, ETI, Neo4j), debería poder **iterar** no solo sobre código, sino sobre **hipótesis de modelado**: distintos cortes de texto, distintos patrones de nodos y relaciones, y distintas estrategias de recuperación, hasta converger con evidencia cuantitativa y cualitativa.

**Ciclo construir–evaluar–refinar:** la visión es cerrar un bucle en el que el “constructor” de Ungraph (ingesta + persistencia + búsqueda) se someta a **evaluación sistemática** — en el espíritu de suites tipo **DeepEval** u otras métricas de RAG/GraphRAG: relevancia, fidelidad a la fuente, cobertura de entidades, penalización por alucinación, latencia, etc. Sobre ese ciclo se pueden **comparar** configuraciones de **chunking**, variantes de **patrones** de grafo y **modos de recuperación** (texto, vector, híbrido, patrones con GDS, extensiones futuras). El resultado no es solo un número: es una **decisión reproducible** sobre qué topología y qué política de recuperación usar para ese dominio.

**Orquestación con agentes (LangChain / LangGraph):** los experimentos y la recuperación pueden apoyarse en **agentes y herramientas** que llamen a la API pública de Ungraph (ingesta, búsqueda, inferencia donde aplique). LangGraph encaja como **máquina de estados** para flujos multi-paso: probar pipelines, enrutar entre retrievers o fusionar contexto desde el grafo. Esto no sustituye el núcleo librería; **habilita** experimentación y, más adelante, productización de “mejor configuración por dataset”.

**Construcción inteligente más allá de un solo extractor:** la extracción de entidades y relaciones no tiene que quedar fijada a un único motor (p. ej. NER con spaCy). La línea **LLM / graph transformer** (extracción guiada por modelo alineada con el esquema del patrón) es coherente con el rol del generador de patrones como **mapeo estructurado** desde texto a Neo4j. La visión incluye **agentes o servicios especializados** (por dominio o por tipo de fuente) que aporten candidatos de entidades y relaciones bajo las mismas reglas de merge y trazabilidad — siempre con vínculo a evidencia y, cuando corresponda, a metadatos de riesgo o confianza descritos en el §2.

**Patrón Neo4j:** en el ecosistema Neo4j, combinar **ingesta flexible**, **vectores y grafo en el mismo motor**, **GDS** y **consultas declarativas** es el patrón habitual de “grafo como memoria analítica”. Ungraph se apoya en ese patrón: el aprendizaje del mejor grafo no es magia aparte, sino **medición y elección** sobre un sustrato Neo4j común, con gobernanza (versiones de patrón, datasets de evaluación, trazas) para no confundir experimentos con producción.

**Estado respecto al código actual:** hoy el mapa de tutoriales (§6) ya distingue lo **Implementado** de lo **Exploratorio**. Este §8 describe una **capa de producto e investigación** alineada sobre todo con el **nivel C** del §3: benchmarks, integración con herramientas de evaluación y notebooks que comparen configuraciones pueden empezar como **Exploratorio** y, al estabilizarse, exigir APIs mínimas (p. ej. hooks de métricas, export de runs) sin acoplar Ungraph a un único proveedor de evaluación.

---

*Documento introducido para unificar visión y plan de tutoriales sin duplicar el detalle de la API ni el plan histórico de publicación del artículo.*
