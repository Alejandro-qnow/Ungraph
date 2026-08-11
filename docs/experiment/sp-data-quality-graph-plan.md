# Plan: calidad de datos, atributos `dq_*` y capa Pydantic sobre el grafo

**Capa ZEN:** `experiment/` (plan medible / trayectoria). **No** es guía ejecutable.

| | |
|--|--|
| **is** | Persistencia File→Page→Chunk; `Entity.quality_score` (confianza de extracción, no DQ de fuente); sin convención general `dq_*` en el núcleo. |
| **will be** | Propiedades `dq_*` consultables en grafo, perfilado de fuente, capa Pydantic de validación — nivel **C** (fuera del cierre A+B). |
| **Estado** | Plan de trabajo (no implementación completa en el núcleo). |
| **Última revisión** | 2026-08-11 (toque tanda B; relocated from `guides/` en Oleada 2 ZEN). |
| **Producto** | Nivel **C** en [PRODUCT.md](../product/PRODUCT.md); horizonte en [ROADMAP_LEVEL_C.md](ROADMAP_LEVEL_C.md). Criterio “validado”: PRODUCT §5 — este plan no es medición. |

Este documento fija **decisiones de diseño**, **convenciones** y **fases** para una capa de calidad sobre fuentes no o semiestructuradas, su proyección al grafo Ungraph y validación tipo **ORM Pydantic**. No sustituye guías de uso, el programa de gates ([PLAN_MAESTRO.md](PLAN_MAESTRO.md)) ni claims medidos en `validation/`.

---

## 1. Propósito y alcance

### 1.1 Qué problema resuelve

- Unificar **perfilado de fuente**, **integridad/usabilidad**, **análisis de texto y legibilidad** y su **materialización** en Neo4j como propiedades explícitas de calidad.
- Evitar que la calidad quede solo en logs o tablas externas: debe ser **consultable en el grafo** (filtrar, rankear, auditar chunks o documentos por DQ).
- Definir un camino hacia esquemas **generados o derivados** desde plantillas (campos obligatorios de validación) usando **Pydantic**, alineado con Clean Architecture del proyecto.

### 1.2 Fuera de alcance inicial (explícito)

- Sustituir de golpe las entidades de dominio actuales (`dataclasses`) por Pydantic en todo el núcleo (migración grande; puede ser posterior).
- Garantizar métricas de legibilidad para todos los idiomas con la misma fórmula (el plan prevé **estrategias por idioma** y campos de versión).

---

## 2. Contexto: qué existe hoy en el repositorio

### 2.1 Dónde está documentado el producto y el grafo

| Necesidad | Dónde mirar |
|-----------|-------------|
| Qué es Ungraph y niveles A/B/C | [PRODUCT.md](../product/PRODUCT.md) |
| Índice general de docs | [README.md](../README.md) |
| Patrón léxico por defecto `FILE_PAGE_CHUNK` (concepto) | [concepts/sp-graph-patterns.md](../concepts/sp-graph-patterns.md) |
| Esquema “tipo inferencia” (Document, Entity, Fact) como referencia de skill | `.claude/skills/kg-schema/SKILL.md` |
| Persistencia real del patrón File–Page–Chunk | `ungraph/utils/graph_operations.py` (`extract_document_structure`, `merge_retrieval_context_view`) |
| Repositorio Neo4j que invoca esa persistencia | `ungraph/infrastructure/repositories/neo4j_chunk_repository.py` |
| Entidades de dominio (Python) | `ungraph/domain/entities/` |

**Nota importante:** el skill `kg-schema` resume un subgrafo útil para **extracción/inferencia**; la ingesta estándar del patrón por defecto materializa **File → Page → Chunk** (y opcionalmente **RetrievalChunk**). Un documento canónico “único” en el repo debe **reconciliar** ambas vistas; la tabla de la §3 intenta ser esa referencia operativa.

### 2.2 Estado actual respecto a calidad

- No hay convención general **`dq_*`** en propiedades Neo4j como parte del núcleo.
- La entidad `Entity` ya incluye `quality_score` (dominio distinto: confianza de extracción, no perfil de fuente).
- El producto ya enmarca **evaluación y métricas** como evolución deseada ([PRODUCT.md](../product/PRODUCT.md) §6.5; criterio de validación §5).

---

## 3. Referencia canónica del grafo por defecto (persistencia relevante)

Esta sección es la **línea base** para decidir en qué nodos colgar propiedades `dq_*` y qué contratos Pydantic deben reflejar.

### 3.1 Patrón léxico `FILE_PAGE_CHUNK`

Estructura: `File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk` (y relaciones de orden entre chunks según `graph_operations`).

| Label | Claves / identidad en MERGE | Propiedades persistidas (según código de referencia) |
|-------|-----------------------------|------------------------------------------------------|
| `File` | `filename` | `createdAt` (en creación) |
| `Page` | `filename` + `page_number` | — |
| `Chunk` | `chunk_id` | `page_content`, `is_unitary`, `embeddings`, `embeddings_dimensions`, `embedding_encoder_info`, `chunk_id_consecutive` |

*Las consultas de lectura pueden esperar también `filename` / `page_number` en `Chunk` según evolución del código; al implementar DQ, alinear lectura/escritura y documentar la fuente de verdad en el mismo PR.*

### 3.2 Vista de recuperación (opcional)

| Label | Rol |
|-------|-----|
| `RetrievalChunk` | Texto optimizado para ventanas LLM/búsqueda; relacionado con `Chunk` vía `HAS_RETRIEVAL_VIEW` (`parent_chunk_id`, `text`, `strategy`, `token_estimate`, `updatedAt`). |

### 3.3 Capa de conocimiento (cuando aplica inferencia)

Nodos como `Entity`, `Fact`, relaciones `MENTIONS`, `RELATED_TO`, etc., según el flujo de inferencia y el repositorio. Las métricas `dq_*` de **fuente** suelen anclarse mejor a **File** o **Document** lógico; las de **texto** a **Chunk** (o ambas con resumen agregado en File).

---

## 4. Objetivos funcionales (checklist)

1. **Perfilado de la fuente** (no/semiestructurada): tipo detectado, tamaño, codificación, duplicados, presencia de campos obligatorios del loader, integridad (checksum opcional), señales de usabilidad (¿parseable?, ¿vaciado?, etc.).
2. **Análisis de texto y legibilidad**: métricas por chunk o por documento (longitud, tokens estimados, complejidad léxica, índices de legibilidad según idioma cuando aplique), con **puntuaciones normalizadas** y timestamp de evaluación.
3. **Grafo**: todas las métricas acordadas existen como propiedades con prefijo **`dq_`** en los nodos acordados, con semántica documentada (diccionario mantenido junto al código o a este plan).
4. **Pydantic**: plantilla(s) con campos obligatorios de validación; posibilidad de **generar** modelos o ampliar modelos base desde definición de patrón o YAML; mapeo claro a propiedades Neo4j (incluido `dq_*`).

---

## 5. Convención de nombres: prefijo `dq_`

### 5.1 Reglas

- Prefijo fijo: **`dq_`** (data quality), en minúsculas con separador de palabras `_`.
- Incluir siempre que sea posible:
  - **`dq_profile_schema_version`** o **`dq_assessment_version`**: versión del esquema de métricas (permite migrar sin romper consultas).
  - **`dq_assessed_at`**: instante de la última evaluación (epoch ms o ISO string; elegir uno y documentarlo).
- Evitar colisiones con dominio de negocio: no usar `quality_score` en nodos distintos de `Entity` sin calificar; preferir nombres explícitos (`dq_source_integrity_score`, `dq_readability_score`).

### 5.2 Diccionario inicial (propuesta, extensible)

| Propiedad sugerida | Tipo lógico | Significado breve |
|--------------------|-------------|-------------------|
| `dq_profile_schema_version` | string | Versión del contrato DQ (p. ej. `dq-v1`). |
| `dq_assessed_at` | int o string | Momento de la última corrida de evaluación. |
| `dq_source_format_detected` | string | Tipo detectado (pdf, html, md, …). |
| `dq_source_byte_length` | int | Tamaño en bytes de la fuente original si aplica. |
| `dq_source_integrity_score` | float [0,1] | Puntuación compuesta de integridad/usabilidad de la fuente. |
| `dq_text_readability_score` | float [0,1] | Legibilidad del texto evaluado (chunk o agregado). |
| `dq_text_metrics_json` | string | JSON serializado con detalle (opcional; si el grafo debe permanecer simple, omitir y guardar solo scores). |

Los nombres finales deben aprobarse al implementar el primer milestone para no multiplicar sinónimos.

---

## 6. Arquitectura propuesta (Clean Architecture)

### 6.1 Capas sugeridas

- **Dominio:** value objects p. ej. `SourceQualityProfile`, `TextQualityMetrics`, `DataQualityBundle` (inmutables donde sea posible); interfaces de servicios `SourceProfilingService`, `TextQualityService`.
- **Aplicación:** orquestación en el caso de uso de ingesta (después de cargar, antes o después de chunking según la métrica); reglas de **dónde** escribir cada métrica (File vs Chunk).
- **Infraestructura:** implementaciones (lectura de archivo, librerías de legibilidad, spaCy/regex, etc.); **persistencia** extendiendo el repositorio o transacciones Cypher que hagan `SET` de `dq_*` sin romper `MERGE` existentes.

### 6.2 Principios

- No acoplar la definición de métricas a un solo proveedor de embeddings o LLM.
- Versionar el esquema DQ para poder re-ejecutar evaluaciones y comparar runs (alineado con historias de reproducibilidad en [PRODUCT.md](../product/PRODUCT.md)).

---

## 7. Capa Pydantic (“ORM del grafo”)

### 7.1 Intención

- Un **modelo base** Pydantic por tipo lógico de nodo (`FileNodeProps`, `ChunkNodeProps`, …) que incluya:
  - propiedades de dominio ya mapeadas al grafo;
  - bloque de propiedades **`dq_*`** con validación y `Field(description=...)`.
- **Plantilla:** un fichero YAML o un `GraphPattern` enriquecido que liste propiedades requeridas/opcionales y genere o valide modelos (p. ej. `create_model` dinámico en fase avanzada).
- **Serialización hacia Neo4j:** función pura `to_cypher_params(model) -> dict` que aplique prefijos y tipos compatibles con Neo4j (float, int, string; listas acotadas para vectores no-DQ).

### 7.2 Relación con el código actual

- Las entidades actuales son **dataclasses**; la capa Pydantic puede vivir primero como **DTO de grafo** en infraestructura o en `domain/value_objects` si el equipo quiere contratos compartidos. La migración de todo el dominio a Pydantic es **opcional** y posterior.

---

## 8. Fases de implementación recomendadas

Las fases son ordenables; cada una debería cerrar con tests y una nota breve en el changelog del paquete.

| Fase | Contenido | Entregables |
|------|-----------|-------------|
| **F0** | Congelar diccionario mínimo `dq_*` + nodos objetivo (File, Chunk) | Este documento actualizado + skill `kg-schema` alineado |
| **F1** | Servicios de perfilado de fuente + VO + tests unitarios | Código dominio/aplicación; sin Neo4j obligatorio en tests |
| **F2** | Métricas de texto/legibilidad + normalización de scores | Misma capa; feature flag o config si el coste es alto |
| **F3** | Persistencia `SET dq_*` en transacción de ingesta | Cambios en repositorio/Cypher; índices si se filtra por score |
| **F4** | Modelos Pydantic base + mapeo a parámetros Cypher | Módulo dedicado; ejemplos en notebook o test de integración |
| **F5** | Generación desde plantilla (YAML/patrón) | Script o builder que emita modelos o valida en CI |

---

## 9. Criterios de aceptación (por release parcial)

- Existe al menos un **camino de ingesta** donde, tras ingerir un documento de prueba, un `MATCH` devuelve **propiedades `dq_*`** pobladas en los nodos acordados.
- El **diccionario** de propiedades `dq_*` está referenciado desde este documento o desde un único fichero en el repo sin contradicciones con Cypher real.
- Los modelos Pydantic (si están en F4) **validan** los campos obligatorios y documentan cada campo (`description`) para uso humano y tooling.
- Tests cubren fallos de validación y ausencia de regresión en `MERGE` existentes.

---

## 10. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Inflar nodos con JSON enormes | Preferir scores agregados + versión; detalle largo en almacén externo o solo en chunks seleccionados. |
| Métricas de legibilidad mal calibradas por idioma | `dq_profile_schema_version` + estrategia por locale; documentar limitaciones. |
| Duplicar fuentes de verdad (dataclass vs Pydantic) | DTO de grafo explícito hasta una migración unificada. |
| Consultas lentas por nuevas propiedades | Índices/constraint solo donde haya filtros reales; medir con EXPLAIN. |

---

## 11. Enlaces cruzados

- [PRODUCT.md](../product/PRODUCT.md) — niveles A/B/C; §5 cuándo cuenta como validado.
- [VISION_AND_TUTORIALS.md](../product/VISION_AND_TUTORIALS.md) — aprendizaje y refinamiento del grafo (§8).
- [ROADMAP_LEVEL_C.md](ROADMAP_LEVEL_C.md) — DQ como fase C, no promesa B.
- [concepts/sp-graph-patterns.md](../concepts/sp-graph-patterns.md) — patrones léxicos vs conocimiento.
- Skill `kg-schema` (`.claude/skills/kg-schema/SKILL.md`) — actualizar cuando el esquema DQ entre en DDL/índices.

---

## Open claim (falseable)

### Claim H_dq_graph_queryable

- **Enunciado:** Tras F3, un documento de prueba ingerido expone ≥3 propiedades `dq_*` acordadas en File o Chunk, consultables por Cypher sin romper `MERGE` existentes.
- **Predicción observable:** `MATCH` post-ingesta devuelve scores versionados (`dq_profile_schema_version`, `dq_assessed_at`, al menos un score de integridad o legibilidad).
- **Protocolo mínimo:** fixture de ingesta + test de integración Neo4j; diccionario §5.2 congelado en el mismo PR.
- **Falsación:** Si no hay propiedades pobladas o colisionan con `quality_score` de Entity sin calificar, F3 no cierra.
- **Reproducibilidad:** test versionado + este plan actualizado; no afirmar “validado” PRODUCT §5 hasta confrontar fuentes/métricas externas si el claim de producto lo exige.

---

**Mantenimiento:** al cerrar cada fase, actualizar la tabla de la §8, la fecha de revisión al inicio de este archivo y, si aplica, el índice [README.md](../README.md).
