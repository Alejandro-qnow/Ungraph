# Ungraph — Documento maestro de producto

**Última revisión:** 2026-04-12  
**Paquete de referencia:** `ungraph` 0.1.5 (`pyproject.toml`)

Este documento describe la **finalidad** del producto, las **historias de usuario** que orientan el diseño y los **casos de uso** típicos. No sustituye la referencia de API ni el changelog; complementa la visión detallada en [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) (incl. **§3** niveles A/B/C) y el **plan técnico de ejecución** en [`../agent/AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md).

**Jerarquía:** `PRODUCT` → *qué y para quién*; `VISION_AND_TUTORIALS` → *visión, niveles, tutoriales, aprendizaje del grafo*; [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) → *horizonte nivel C (plan maestro; fuera del alcance de entrega prioritario B)*; `AGENT_SKILLS` → *cómo se implementa y prioriza*; [`CHECKPOINT_INFERENCE_PIPELINE.md`](CHECKPOINT_INFERENCE_PIPELINE.md) → *retomada del trabajo en curso (inferencia enriquecida)*.

### Alcance priorizado del plan maestro

- **Entrega y estabilidad** del proyecto se orientan a **nivel A (núcleo)** y **nivel B (productivo)** tal como los describe [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) §3.
- **Nivel C** no forma parte de ese compromiso de cierre por release; queda **expresado** como horizonte técnico y de producto en [`ROADMAP_LEVEL_C.md`](ROADMAP_LEVEL_C.md) y en la §8 de la visión (aprendizaje del mejor grafo). Puede existir código de apoyo exploratorio (p. ej. `ungraph.evaluation`) sin redefinir la promesa de B.

---

## 1. Finalidad del producto

**Ungraph** es un **framework en Python** para llevar **datos no estructurados** (documentos, texto; en la visión también conversación y otras fuentes) a un **grafo de conocimiento en Neo4j**, mediante un pipeline coherente **Extract–Transform–Inference (ETI)**, **patrones de grafo declarativos** (`GraphPattern`) y **recuperación tipo GraphRAG** (texto, vector, híbrido, y extensiones con analítica de grafo cuando aplica).

La finalidad no es ofrecer un producto SaaS cerrado de “memoria de agente”, sino **habilitar** sistemas donde el grafo sea **fuente de verdad estructurada**, **interfaz de evaluación** frente a fuentes y, donde se defina en el modelo, **soporte a flujos agénticos** (trazabilidad, riesgo de alucinación, ontologías sugeridas, temporalidad). El producto evoluciona por **fases** hacia mayor autonomía en el modelado y hacia **ciclos construir–evaluar–refinar** para elegir el mejor grafo para cada dominio (véase §8 de [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md)).

---

## 2. Niveles de la promesa (A / B / C)

La **misma promesa** se despliega en **tres niveles de madurez**; una versión “estable” de la librería ancla credibilidad en el **nivel A** sin exigir que B o C estén terminados. Detalle y límites de comunicación: [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) §3.

| Nivel | Enfoque de producto |
|-------|---------------------|
| **A — Núcleo** | Patrones definibles, ingestión, Neo4j, búsqueda GraphRAG, embeddings configurables; preparación de texto/chunking como **estrategias** explícitas. |
| **B — Productivo** | Extracción de entidades y relaciones, evaluación y scores, sugerencias, ontologías y gobernanza más profunda. |
| **C — Evolutivo** | Recomendación de estructuras según métricas, automejora, MCP/interoperabilidad/calidad de datos avanzada; alineado con §8 (aprendizaje del mejor grafo). |

Las historias de usuario (§5) y los casos de uso (§6) mezclan niveles: conviene leer cada ítem como **aspiración** salvo que el tutorial o la API marquen **Implementado**.

---

## 3. Problemas que resuelve

| Necesidad | Cómo ayuda Ungraph |
|-----------|-------------------|
| Pasar de “montones de documentos” a **estructura consultable** (nodos, relaciones, chunks, embeddings) | Pipeline ETI y persistencia en Neo4j con patrones reproducibles |
| Evitar esquemas ad hoc irreproducibles | Patrones como capa de mapeo (analogía “ORM” de grafo) y documentación de patrones |
| **Responder preguntas** con contexto del corpus sin ignorar la **procedencia** | GraphRAG: búsqueda y recuperación alineadas con chunks y grafo |
| Ir más allá del vector puro cuando hace falta **topología y algoritmos** | Integración opcional con capacidades de grafo (p. ej. GDS en escenarios soportados) |
| Preparar terreno para **agentes y evaluación** sin acoplar un solo proveedor | API librería + visión de metadatos de riesgo, gobernanza y evaluación por ciclos |

---

## 4. Propuesta de valor (síntesis)

1. **Un solo arco técnico:** de la fuente no estructurada al grafo y a la recuperación, con contratos claros en código.
2. **Neo4j como sistema de verdad:** consultas, relaciones reales y, cuando se use, vectores y analítica en el mismo ecosistema.
3. **Extensibilidad:** patrones personalizados, inferencia opcional, extras (`gds`, `infer`, visualización planificada como `viz`) sin obligar a un stack único de agentes.
4. **Honestidad de madurez:** separación entre lo **implementado**, lo **parcial** y lo **exploratorio** (tutoriales y roadmap alineados con el código).

---

## 5. Historias de usuario

Las formulaciones siguientes guían prioridades de producto y documentación; no implican que cada una esté completamente cubierta en la versión actual del paquete.

### 5.1 Ingesta y modelado

- **Como** desarrollador o ingeniero de datos, **quiero** configurar una vez Neo4j y Ungraph (`configure`) e **ingerir** documentos (p. ej. Markdown, PDF, Word) **para** obtener chunks y estructura en grafo de forma repetible.
- **Como** arquitecto de soluciones, **quiero** definir o reutilizar un **`GraphPattern`** (nodos, relaciones, reglas de merge) **para** que el grafo refleje mi dominio y no solo una pila de texto.
- **Como** equipo con vocabulario compartido, **quiero** que el sistema pueda **sugerir o alinearse con ontologías** según tipo de contenido **para** reducir trabajo manual de esquema (visión; despliegue por fases).

### 5.2 Búsqueda y GraphRAG

- **Como** usuario de aplicaciones RAG, **quiero** **buscar** en el grafo por texto, vector o híbrido **para** alimentar respuestas con contexto relevante.
- **Como** implementador avanzado, **quiero** **`search_with_pattern`** y patrones alineados con referencias GraphRAG **para** aproximarme a patrones del ecosistema (Basic, Parent-Child, comunidades, etc.) según prerequisitos.
- **Como** analista, **quiero** usar **analítica de grafo** donde esté soportado **para** comunidades, métricas o recorridos que el vector solo no resuelve.

### 5.3 Inferencia y extracción

- **Como** desarrollador, **quiero** combinar **NER clásico** (p. ej. spaCy) y/o **extracción vía LLM** **para** poblar entidades y relaciones según el patrón.
- **Como** integrador, **quiero** encadenar Ungraph con **LangChain** u orquestación externa **para** construir pipelines sin reescribir el núcleo de persistencia.

### 5.4 Agéntico, confianza y memoria como interfaz

- **Como** equipo que expone un LLM sobre el corpus, **quiero** **registrar** outputs candidatos con **vínculo a evidencia** y, a la larga, **metadatos de riesgo o confianza** **para** auditar alucinaciones y calidad.
- **Como** diseñador de agentes, **quiero** tratar **conversación u otros textos fluidos** como fuentes de ingesta **para** extender el grafo de forma gobernada (estados propuesto vs. confirmado; políticas de merge — visión).

### 5.5 Evaluación y mejora continua

- **Como** responsable de calidad de RAG, **quiero** **comparar** configuraciones de chunking, patrones y recuperación con **métricas** **para** elegir el mejor grafo para mi dominio (visión de ciclo construir–evaluar–refinar).
- **Como** investigador, **quiero** **reproducir** experimentos (versiones de patrón, runs) **para** no confundir prueba con producción.

### 5.6 Operación y ecosistema

- **Como** operador, **quiero** documentación clara de **configuración**, límites y extras (`[gds]`, `[infer]`) **para** desplegar con expectativas correctas.
- **Como** desarrollador de herramientas, **quiero** **integrar** Ungraph vía API y, donde exista material, **scripts o MCP** genéricos **para** conectar agentes o IDEs al grafo (parte del camino aún exploratoria).

### 5.7 Visualización y exportación

- **Como** analista o diseñador de patrones, **quiero** **visualizar rápidamente** subgrafos en el notebook con **configuraciones** (layout, profundidad, resaltado por tipo) **para** validar la estructura sin escribir Cypher en cada paso.
- **Como** responsable de corpus grande, **quiero** **filtrar la vista por documento o archivo** **para** revisar un solo insumo sin cargar todo el grafo.
- **Como** integrador, **quiero** **exportar** fragmentos del grafo a **formatos estándar** (p. ej. GraphML, GEXF, JSON node-link, CSV, NetworkX) **para** compartir con herramientas externas o pipelines offline (plan técnico: [`AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md) §7).

---

## 6. Casos de uso

### 6.1 Corpus documental y preguntas con contexto

- **Documentación interna / base de conocimiento:** ingestión de PDF, Wiki exportada, Markdown; búsqueda semántica y respuestas ancladas a pasajes y archivos.
- **Soporte y FAQs:** grafo que conecta síntomas, artículos y resoluciones si el patrón y la extracción lo modelan así.
- **Due diligence y revisión contractual:** alto volumen de texto; énfasis en citación, trazabilidad y revisión humana de inferencias.

### 6.2 Investigación y análisis de literatura

- Ingesta de papers o informes; chunks y entidades para **navegar** citas, temas y autores; GraphRAG para síntesis asistida con **procedencia** explícita.

### 6.3 Copilotos sectoriales y prototipos RAG

- Dominios regulados (salud, finanzas, legal) donde importa **no inventar**: el grafo como capa verificable entre corpus y modelo generativo.

### 6.4 Grafos analíticos y comunidades

- Cuando el valor está en **estructura** (comunidades, centralidad, caminos), además del retrieval vectorial — apoyándose en capacidades Neo4j/GDS donde el proyecto y la instalación lo permitan.

### 6.5 Habilitador de memorias agénticas (sustrato)

- Sistemas tipo asistentes de largo plazo: Ungraph como **capa de estructura y persistencia**; la política de “qué recordar” y la UX conversacional suelen vivir **encima** (integración, no sustitución del núcleo librería).

### 6.6 Ingeniería de pipelines y benchmarking

- Comparar **hipótesis de modelado** (chunking, patrones, modos de búsqueda) con datasets de evaluación; útil para equipos de ML/IA que optimizan calidad antes de producción.

### 6.7 Exploración visual y hand-off de subgrafos

- Revisión de **estructura File–Page–Chunk** y entidades en talleres con stakeholders; **exportación** de subgrafos para Gephi, informes o repositorios de figuras.
- Depuración de ingestión: ver de un vistazo si un documento quedó mal enlazado o si faltan relaciones esperadas.

---

## 7. Alcance y límites honestos

- **Qué es:** librería Python, Neo4j como destino principal del flujo documentado, API pública de ingesta y búsqueda, patrones extensibles, extras opcionales; **módulo de visualización** previsto como capa opcional (widgets Jupyter / yFiles), no como dependencia del núcleo.
- **Qué no pretende ser por sí sola:** producto completo de chat, orquestación de agentes de negocio, motor OWL/SHACL nativo, ni servidor MCP “oficial” hasta que exista decisión y superficie estables (parte de esto es **exploratorio**).
- **Evolución:** funciones descritas como visión (evaluación integrada, ontología automática avanzada, MCP propio) deben reflejarse en releases y en `VISION_AND_TUTORIALS.md` sin adelantarse al código.

---

## 8. Documentos relacionados

| Documento | Rol |
|-----------|-----|
| [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) | Visión estratégica, **§3** niveles A/B/C, tutoriales, **§8** aprendizaje del mejor grafo |
| [`../agent/AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md) | Prioridades de ingeniería, skills y **§7** módulo de visualización (yFiles for Jupyter) y exportación |
| [`../ANALYSIS_120426.md`](../ANALYSIS_120426.md) | Línea base crítica de madurez del paquete |
| [`api/public-api.md`](api/public-api.md) (y variantes `sp-`/`en-`) | Contrato técnico de la API pública |
| [`guides/quickstart.md`](guides/quickstart.md), [`guides/search.md`](guides/search.md) | Primeros pasos y búsqueda |

---

*Documento maestro de producto: finalidad, historias de usuario y casos de uso. Actualizar la fecha y la versión de referencia cuando cambie el núcleo del mensaje de producto o el paquete de anclaje.*
