# Ungraph — Documento maestro de producto

**Última revisión:** 2026-08-11  
**Paquete de referencia:** `ungraph` 0.1.5 (`pyproject.toml`)  
**Norte de visión (canónico):** [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) — este archivo **no redefine** la visión; la **operacionaliza** (para quién, historias, casos, límites de promesa).

**Jerarquía**

| Documento | Rol |
|-----------|-----|
| [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) | *Norte:* §2 memoria/ontologías, §3 niveles A/B/C, §6 mapa pedagógico, §8 ciclo construir–evaluar–refinar |
| **Este archivo (`PRODUCT`)** | *Qué y para quién:* finalidad, historias, casos de uso, límites; siempre subordinado a la visión |
| [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) | Índice ejecutable técnico-científico |
| [`../experiment/ROADMAP_LEVEL_C.md`](../experiment/ROADMAP_LEVEL_C.md) | Horizonte C (fuera del cierre prioritario A+B) |
| [`../../agent/AGENT_SKILLS.md`](../../agent/AGENT_SKILLS.md) | Cómo se implementa y prioriza en ingeniería |
| [`../archive/CHECKPOINT_INFERENCE_PIPELINE.md`](../archive/CHECKPOINT_INFERENCE_PIPELINE.md) | Checkpoint histórico de inferencia enriquecida |

**Sitio MkDocs:** Producto es **secundario** (library-first; ver [`DOCUMENTARY_ZEN`](../research/DOCUMENTARY_ZEN.md)). No tab de primer nivel; puntero desde [`../README.md`](../README.md) / Inicio cuando haga falta. Pulir aquí; el release documental al VCS se hace cuando la calidad lo merezca (`docs/` puede vivir fuera del tracking hasta entonces).

### Alcance priorizado (alineado a visión §3)

- **Entrega y estabilidad** → **nivel A (núcleo)** y **nivel B (productivo)**.
- **Nivel C** → horizonte en [`ROADMAP_LEVEL_C.md`](../experiment/ROADMAP_LEVEL_C.md) y visión §8; puede existir código exploratorio (p. ej. `ungraph.evaluation`) **sin** redefinir la promesa de B.

---

## 1. Finalidad del producto

**is (promesa de librería):** Ungraph es un **framework Python** que lleva **datos no estructurados** a un **grafo de conocimiento en Neo4j** mediante el pipeline **Extract → Transform → Inference (ETI)**, **patrones declarativos** (`GraphPattern`) y **recuperación** (texto, vector, híbrido; GraphRAG/GDS como *interfaz* sobre el grafo, no como definición del conocimiento).

**will be (visión §2 / §8):** el grafo como **fuente de verdad estructurada**, interfaz de **evaluación** frente a fuentes, soporte a flujos agénticos (trazabilidad, riesgo de alucinación, ontologías sugeridas, temporalidad) y ciclos **construir–evaluar–refinar** para elegir el mejor grafo por dominio.

La finalidad **no** es un SaaS cerrado de “memoria de agente”, sino **habilitar** sistemas donde el integrador define políticas y patrones. GraphRAG, MCP y Neo4j son **consumidores** del almacén epistémico; la espina es ETI (creencias provisionales, evidencia, confianza, depuración — ver [`../concepts/eti-spine.md`](../concepts/eti-spine.md)).

---

## 2. Niveles de la promesa (A / B / C)

Detalle normativo: visión §3. Resumen operativo:

| Nivel | Enfoque de producto | Estado de promesa |
|-------|---------------------|-------------------|
| **A — Núcleo** | Patrones, ingestión, Neo4j, búsqueda, embeddings configurables; chunking como **estrategias** explícitas | Ancla de credibilidad / “estable” |
| **B — Productivo** | Extracción entidades/relaciones, evaluación y scores, sugerencias, ontologías y gobernanza más profunda | Extiende A; extras acotados |
| **C — Evolutivo** | Recomendación de estructuras según métricas, automejora, MCP/interoperabilidad, calidad de datos avanzada | Horizonte; no cierre simultáneo con B |

Historias (§5) y casos (§6) mezclan niveles: leer cada ítem como **aspiración** salvo marca **Implementado** en visión §6 o en API/guides.

---

## 3. Problemas que resuelve

| Necesidad | Cómo ayuda Ungraph |
|-----------|-------------------|
| De documentos a **estructura consultable** | Pipeline ETI + persistencia Neo4j con patrones reproducibles |
| Evitar esquemas ad hoc | `GraphPattern` como mapeo declarativo (“ORM” de grafo) |
| Preguntas con **procedencia** | Recuperación anclada a chunks/grafo (GraphRAG como interfaz) |
| Topología cuando el vector no basta | GDS / analítica opcional |
| Terreno para agentes y evaluación | API librería + visión de metadatos de riesgo, gobernanza y ciclos de evaluación |

---

## 4. Propuesta de valor (síntesis)

1. **Un arco técnico:** fuente no estructurada → grafo → recuperación, con contratos en código.
2. **Neo4j como sistema de verdad** del flujo documentado (consultas, relaciones; vectores/analítica cuando aplique).
3. **Extensibilidad:** patrones, inferencia opcional, extras (`gds`, `infer`, `viz` planificado) sin un único stack de agentes.
4. **Honestidad de madurez:** **is** (API/tests en `main`) vs **will be** / Open claims (visión, research, experiment).

---

## 5. Cuándo cuenta como “validado” (criterio de producto)

Alineado a visión §8 y a la secuencia ZEN (*experimentación → medición*).

No basta ejecutar un notebook o ver un número que confirma la intuición. En producto e investigación Ungraph, **validamos** cuando podemos:

1. **Confrontar con fuentes externas o referencias similares** (literatura, fixtures ajenos al propio sesgo de diseño, baselines ET vs ETI, scorecards comparables).
2. **Razonar sobre resultados sin sesgo de confirmación** — buscar también lo que **falsaría** la hipótesis (gates H_I, Y discriminativas; ver plan maestro).
3. **Leer tendencias, patrones y variaciones** entre hipótesis de modelado, corridas y dominios — no un único punto “bonito”.
4. **Modelar correctamente** lo que el experimento afirma medir: el scorecard/ExperimentRun refleja el claim, no un proxy conveniente.

| Capa | Vive en | Qué es |
|------|---------|--------|
| Diseño de trial, hipótesis, DoE, protocolo | `docs/experiment/` | *Cómo vamos a medir* (`will be` hasta correr) |
| Resultados confrontables, scorecards versionados, criterios de paso/fallo | `docs/validation/` | *Qué ya se midió y se puede auditar* (`is` documental) |

Hasta que un resultado cumpla el criterio de arriba, permanece en experiment/research como Open claim — no se vende como capacidad de producto.

---

## 6. Historias de usuario

Guían prioridades; no implican cobertura completa en 0.1.5.

### 6.1 Ingesta y modelado

- **Como** desarrollador, **quiero** configurar Neo4j/Ungraph e ingerir documentos **para** obtener chunks y estructura repetible.
- **Como** arquitecto, **quiero** definir un **`GraphPattern`** **para** que el grafo refleje mi dominio.
- **Como** equipo con vocabulario compartido, **quiero** sugerencia/alineación ontológica **para** reducir esquema manual (**will be**, visión §2).

### 6.2 Búsqueda y GraphRAG (interfaz)

- **Como** usuario RAG, **quiero** buscar por texto/vector/híbrido **para** contexto con procedencia.
- **Como** implementador avanzado, **quiero** `search_with_pattern` alineado a referencias GraphRAG según prerequisitos.
- **Como** analista, **quiero** analítica de grafo donde esté soportado.

### 6.3 Inferencia (slot, no un solo motor)

- **Como** desarrollador, **quiero** enchufar NER (spaCy) y/o extracción LLM **bajo el mismo contrato de slot** (**is** parcial; slot documentado en concepts).
- **Como** integrador, **quiero** encadenar LangChain u orquestación externa sin reescribir persistencia.

### 6.4 Agéntico, confianza y memoria como interfaz

- **Como** equipo sobre un LLM, **quiero** registrar outputs con vínculo a evidencia y, a la larga, metadatos de riesgo (**will be**, visión §2).
- **Como** diseñador de agentes, **quiero** conversación u otros textos fluidos como fuentes gobernadas (**will be**).

### 6.5 Evaluación y mejora continua

- **Como** responsable de calidad, **quiero** comparar chunking/patrones/recuperación con métricas **para** elegir el mejor grafo (visión §8; validación según §5 de este documento).
- **Como** investigador, **quiero** reproducir ExperimentRuns **para** no confundir prueba con producción.

### 6.6 Operación y ecosistema

- **Como** operador, **quiero** configuración, límites y extras claros (`[gds]`, `[infer]`).
- **Como** desarrollador de herramientas, **quiero** API y, donde exista, scripts/MCP (**exploratorio** hasta superficie estable).

### 6.7 Visualización y exportación

- **Como** analista, **quiero** visualizar subgrafos en notebook (**will be** / plan técnico AGENT_SKILLS §7).
- **Como** integrador, **quiero** exportar a formatos estándar (GraphML, GEXF, JSON, CSV, NetworkX).

---

## 7. Casos de uso

### 7.1 Corpus documental y preguntas con contexto

Documentación interna, FAQs/soporte, due diligence — énfasis en citación y revisión humana de inferencias.

### 7.2 Investigación y literatura

Papers/informes; navegación por entidades; GraphRAG con procedencia explícita.

### 7.3 Copilotos sectoriales

Dominios donde importa no inventar: grafo como capa verificable entre corpus y generativo.

### 7.4 Grafos analíticos

Comunidades, centralidad, caminos — Neo4j/GDS cuando la instalación lo permita.

### 7.5 Sustrato de memorias agénticas

Ungraph como capa de estructura y persistencia; la política de “qué recordar” vive encima.

### 7.6 Ingeniería de pipelines y benchmarking

Comparar hipótesis de modelado con datasets de evaluación; gates y scorecards en experiment → validation cuando cumplan §5.

### 7.7 Exploración visual y hand-off

Revisión File–Page–Chunk; exportación para Gephi/informes (**parcial / will be** según módulo viz).

---

## 8. Alcance y límites honestos

- **Qué es:** librería Python; Neo4j destino principal del flujo documentado; API de ingesta/búsqueda; patrones extensibles; extras opcionales.
- **Qué no es por sí sola:** chat completo, orquestación de negocio, motor OWL/SHACL nativo, ni MCP “oficial” sin decisión y superficie estables.
- **Evolución:** lo descrito solo en visión no se afirma en guides/API como hecho; pasa a **is** cuando código + criterio §5 lo sostienen.

---

## 9. Documentos relacionados

| Documento | Rol |
|-----------|-----|
| [`VISION_AND_TUTORIALS.md`](VISION_AND_TUTORIALS.md) | Visión canónica (norte) |
| [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) | Plan ejecutable + programa experimental |
| [`../research/DOCUMENTARY_ZEN.md`](../research/DOCUMENTARY_ZEN.md) | Gobernanza documental / capas |
| [`../concepts/eti-spine.md`](../concepts/eti-spine.md) | Espina ETI |
| [`../../agent/AGENT_SKILLS.md`](../../agent/AGENT_SKILLS.md) | Prioridades de ingeniería |
| [`../../ANALYSIS_120426.md`](../../ANALYSIS_120426.md) | Línea base crítica de madurez (fuera de `docs/`) |
| [`../api/sp-public-api.md`](../api/sp-public-api.md) | Contrato API |
| [`../guides/sp-quickstart.md`](../guides/sp-quickstart.md), [`../guides/search.md`](../guides/search.md) | How-to canónicos (tutoriales = stubs → guías) |

---

*Producto se actualiza cuando cambia el mensaje de promesa o el anclaje a la visión. La visión manda; este archivo traduce.*
