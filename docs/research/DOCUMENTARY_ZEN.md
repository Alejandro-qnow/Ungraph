# Principio rector ZEN — documentación Ungraph

**Rol:** gobernanza de estructura bajo `docs/`. No es teoría ETI ni plan experimental; define *dónde* vive cada escritura y *cómo* se depura sin big-bang.

**Canon de contenido:** sigue vigente `.cursor/rules/docs-scientific-canon.mdc` (`is` vs `will be`, plantilla Motivation → Theory → In Ungraph → Open claims). Este documento añade la **secuencia rectora** y la **raíz limpia**.

---

## Diagnóstico (baseline pre-oleadas; histórico)

1. **Raíz hinchada.** En `docs/` convivían entrada del sitio (`index`, `README`) con producto, visión, plan maestro, benchmarks, roadmaps, checkpoints, workflow, instalación y notas de release.
2. **Overlaps de capa.** Guías / Tutoriales / Ejemplos repetían “cómo usar”; Conceptos / Teoría / Research competían por el mismo argumento epistémico.
3. **Triplicados de idioma.** Temas como `sp-*`, `en-*` y sin prefijo (legado).
4. **Nav library-last.** Producto y marca antes del contrato API y la espina ETI.
5. **Gobernanza dispersa.** Planes medibles en raíz sin carpeta de experimentación.
6. **Fuera de foco.** Tema MkDocs necesario, pero no ciencia ni API.

Depurar > acumular. Cada página nueva debe justificar su capa o fusionarse.

**Estado post Oleada 4 (2026-08):** secuencia ZEN nav/index **cerrada**. Funnel Empezar → Espina → Ciencia en `index.md`; README alineado; Conceptos con Espina temprana; `sp-graph-patterns` / `sp-lexical-graphs` con plantilla; validation recortada a probe `is` + PRODUCT §5. Tab Producto **omitido**. Stubs unprefixed/`en-*` **mantenidos** hasta release documental. Post-ZEN = mantenimiento (links, stubs, claims medidos), no nueva oleada de reorganización.

---

## Principio rector ZEN (reglas accionables)

1. **Una página, una capa, un trabajo.** Si dos archivos responden la misma pregunta, se fusionan o uno pasa a legacy.
2. **Secuencia rectora obligatoria.** El árbol y la nav siguen: **fundamento → experimentación/creación → medición → estandarización → productivización/reproducibilidad**.
3. **Raíz mínima.** En la raíz de `docs/` solo: `index.md`, `README.md` (puntero). Todo lo demás tiene carpeta. Tema del sitio (`overrides/`, `stylesheets/`, `assets/`) no cuenta como documentación de dominio.
4. **Library-first.** Nav y `index.md` priorizan: qué es Ungraph/ETI → contrato API → cómo usarlo → fundamento → programa experimental. Producto, marca y ops de equipo son secundarios.
5. **ETI es la espina; retrieval es interfaz.** GraphRAG/MCP/Neo4j se documentan como consumidores del almacén epistémico, no como definición de conocimiento.
6. **Menos docs.** Preferir fusionar o marcar legacy antes de crear carpeta/página.
7. **Oleadas pequeñas.** Mover/fusionar por lote con nav e índices coherentes; nunca reorganizar todo el árbol de un golpe.
8. **Links dentro de `docs/`.** Punteros a `agent/`, `.claude/`, `project/` no sustituyen contenido canónico.

---

## Arquitectura objetivo por capas

| Orden | Capa | Carpeta | Qué va | Qué no va |
|------:|------|---------|--------|-----------|
| 0 | Entrada | raíz (`index.md`, `README.md`) | Funnel ETI, “dónde ir”, vista previa MkDocs | Planes, producto, API, teoría |
| 1 | Fundamento | `concepts/` | Espina ETI, Extract/Transform/Inference, slot Infer, intro/arquitectura | Tutoriales paso a paso; contratos; DoE |
| 1 | Fundamento (linaje) | `theory/` | GraphRAG, Neo4j, Clean Architecture *mapeados a Ungraph* | Rewrite genérico de RAG; claims medidos como hechos |
| 1 | Fundamento (ciencia) | `research/` | Whitepaper IMRaD, matriz, anclas, ZEN, checklist | Benchmarks ejecutables; guías de uso |
| 2 | Experimentación | `experiment/` | `PLAN_MAESTRO`, `ROADMAP_*`, `BENCHMARK_*`, planes `will be` (p. ej. `sp-data-quality-graph-plan`) | Resultados ya corridos (→ `validation/`); API |
| 3 | Medición | `validation/` | Resúmenes con artefacto versionado | Marketing “validado”; p-values inventados |
| 4 | Estandarización | `api/` | Contrato público, configuración, patrones de búsqueda | Narrativa de producto; Open claims de trayectoria |
| 5 | Productivización | `guides/` | Recorridos cortos ejecutables (quickstart, ingesta, search) | Teoría larga; planes `will be` |
| 5 | Productivización (viajes) | `tutoriales/` *legacy stubs* | Solo redirects a `guides/` | Duplicar el mismo how-to ya en guides |
| 5 | Reproducibilidad | `examples/` | Mínimos reproductibles | Claims de capacidad no medidos |
| — | Producto (secundario) | `product/` | `PRODUCT`, visión | Sustituir research o API |
| — | Ops equipo | `ops/` | Workflow, instalación inferencia | Paleta de marca como “desarrollo” científico |
| — | Legacy | `archive/` | Checkpoints, release notes, cuerpos históricos de guides | Contenido vivo en nav principal |
| — | Tema sitio | `overrides/`, `stylesheets/`, `assets/` | MkDocs / tokens | Curación ETI; nav de primer nivel |

**Guías vs tutoriales:** guide = una tarea + pasos + API; tutorial narrado que solo repite una guide → stub → guide.

**Excepción de prefijo:** `guides/search.md` es el canónico ES de búsqueda (sin `sp-`). Resto de how-to canónicos: `sp-quickstart`, `sp-ingestion`, `sp-custom-patterns`.

---

## Tabla tarea how-to → path canónico (Oleada 2)

| Tarea | Canónico en nav | Stubs / legacy |
|-------|-----------------|----------------|
| Quickstart / primer grafo | `guides/sp-quickstart.md` | `guides/quickstart.md`, `guides/en-quickstart.md`, `tutoriales/sp-01-*` |
| Ingesta | `guides/sp-ingestion.md` | `guides/ingestion.md`, `guides/en-ingestion.md`, `tutoriales/sp-03-*` |
| Búsqueda | `guides/search.md` | `tutoriales/sp-02-*` |
| Patrones personalizados | `guides/sp-custom-patterns.md` | `guides/custom-patterns.md`, `guides/en-custom-patterns.md` |
| Plan DQ / `dq_*` (no how-to) | `experiment/sp-data-quality-graph-plan.md` | (sacado de `guides/`) |

---

## Mapa de migración (raíz → destino) — aplicado

| Origen | Destino | Estado |
|--------|---------|--------|
| `PRODUCT.md` | `product/PRODUCT.md` | Hecho (raíz sin copia) |
| `VISION_AND_TUTORIALS.md` | `product/VISION_AND_TUTORIALS.md` | Hecho |
| `PLAN_MAESTRO.md` | `experiment/PLAN_MAESTRO.md` | Hecho |
| `BENCHMARK_ETI_DOMAINS.md` | `experiment/BENCHMARK_ETI_DOMAINS.md` | Hecho |
| `ROADMAP_LEVEL_C.md` | `experiment/ROADMAP_LEVEL_C.md` | Hecho |
| `CHECKPOINT_INFERENCE_PIPELINE.md` | `archive/` | Hecho |
| `DEVELOPMENT_WORKFLOW.md` | `ops/` | Hecho |
| `INSTALLATION_INFERENCE.md` | `ops/` | Hecho |
| `_RELEASE_v0.1.0_COMPLETADO.md` | `archive/` | Hecho |
| Unprefixed / `en-*` (guides, concepts, theory, api, examples, validation) | stub → `sp-*` | Hecho (Oleada 2); cuerpos EN/unprefixed de **guides** (+ tutoriales) en `archive/`; resto de capas: stub in-place (cuerpo previo recuperable en git history; no bulk-archive por alcance de oleada) |
| `guides/sp-data-quality-graph-plan.md` | `experiment/sp-data-quality-graph-plan.md` | Hecho |
| `tutoriales/sp-01..03` | stubs → guides | Hecho |

**Nota:** algunos punteros *fuera* de `docs/` (`agent/`, módulos Python) pueden seguir citando paths de raíz antiguos — fuera del alcance de esta oleada; actualizar en PR de ops/código.

---

## Nav MkDocs (library-first) — alineada post Oleada 4

Ver `mkdocs.yml`. Criterios:

- Primeras pestañas = Guías (`Tutoriales → guías` bajo Guías), API, Conceptos.
- Conceptos: Intro → Espina ETI → Extracción → Transformación → Inferencia → Slot → Arquitectura → Patrones → Léxicos.
- Research / Experimentación / Validación = secuencia ciencia; Theory = linaje (GraphRAG/Neo4j/CA).
- Sin tab Producto ni Qnow; Ops al final.
- `index.md`: Empezar (usar) → Espina (entender) → Ciencia (medir).

---

## Estrategia de ejecución (oleadas)

### Oleada 0 — Gobernanza — **HECHA**

- ZEN + checklist + punteros research/canon.

### Oleada 1 — Raíz → carpetas — **HECHA** (residuales cerrados)

1. Carpetas `experiment/`, `product/`, `ops/`, `archive/`.
2. Planes → `experiment/`; producto → `product/`; ops → `ops/`; checkpoint/release → `archive/`.
3. Raíz de dominio = `index.md` + `README.md` (verificado en working tree).
4. Nav library-first; Ops al final.
5. Links internos bajo `docs/` actualizados a destinos canónicos.

### Oleada 2 — Deduplicar idioma y how-to — **HECHA**

- Canónico ES (`sp-*`); `guides/search.md` excepción documentada.
- Unprefixed / `en-*` → stubs cortos (guides: cuerpos EN archivados en `archive/guides/`).
- Tutoriales 1–3 → stubs; nav bajo Guías; ≤1 canónico por tarea how-to.
- Plan DQ movido a `experiment/` con `is` / `will be`.
- Concepts/theory/api/examples/validation: stubs de idioma (sin reescribir theory — Oleada 3).

### Oleada 3 — Concepts / theory / research — **HECHA**

- Plantilla completa (o equivalentes) en: `eti-spine`, `extraction`, `transformation`, `inference`, `inference-slot`.
- Alineados a ETI (recortados de guide-like): `sp-introduction`, `sp-architecture`.
- Theory `sp-graphrag`, `sp-neo4j`, `sp-clean-architecture`: linaje + consumidores del almacén; Open claim ≥1 o enlace a claim en concepts/plan; sin redefinir conocimiento como retrieval.
- `research/README.md`: punteros ZEN/whitepaper/matriz/checklist + concepts/theory; tabla “dónde no buscar pasos”.
- Stubs unprefixed/`en-*`: **no borrados** (default provisional → mantener hasta release documental).

### Oleada 4 — Nav e index finales — **HECHA**

- Funnel `index.md`: Empezar (usar) → Espina ETI (entender) → Ciencia (medir); mapa ZEN como tabla secundaria.
- `README.md` alineado (Empezar → Fundamento → Experimentación → Medición → …); producto secundario.
- Nav Conceptos reordenada (Espina temprana); etiqueta `Tutoriales → guías`; comentario oleada 4; **sin** tab Producto.
- Curados: `concepts/sp-graph-patterns.md`, `concepts/sp-lexical-graphs.md` (plantilla; sin duplicar guides).
- Validation: `sp-validation_summary.md` recortado a probe `is` + enlace PRODUCT §5 / experiment.
- Secuencia de oleadas ZEN **cerrada** → modo mantenimiento.

**Mantenimiento post-ZEN (no oleada):** grep stubs al release documental; links rotos; actualizar claims cuando haya ExperimentRun real en `validation/`; no reabrir tab Producto sin decisión explícita.

**Mantenimiento — tanda A (guides + API, 2026-08):** curación Checklist Guide/API sobre canónicos en nav (`sp-quickstart`, `sp-ingestion`, `search`, `sp-custom-patterns`, `sp-public-api`, `sp-configuration`, `sp-search-patterns`, `sp-advanced-search-patterns`). Depurar > acumular; `is`/`will be`; sin reorg de árbol ni borrado de stubs.

**Mantenimiento — tanda B (experiment, 2026-08):** curación Checklist Experiment sobre canónicos en nav (`PLAN_MAESTRO`, `BENCHMARK_ETI_DOMAINS`, `ROADMAP_LEVEL_C`) + toque `sp-data-quality-graph-plan`. Gates → scorecards/`ExperimentRun`; `is`/`will be`/Open claims; probe seed ≠ PRODUCT §5; sin mega-DoE nuevo ni nav tocada.

**Mantenimiento — tanda C (examples, 2026-08):** curación Checklist Example/notebook sobre `examples/sp-basic-examples`, `sp-advanced-examples`, `sp-notebooks`. Mínimos reproductibles + fixtures `tests/fixtures/topology_*.md`; firmas alineadas a tanda A (`ungraph.*`, `SearchResult`); `is`/`will be` → PRODUCT §5 / experiment; sin nav nueva (puntero Empezar + mapa ZEN en `index`/`README`); stubs unprefixed/`en-*` mantenidos. Siguiente mantenimiento sugerido: Prioridad D (`ops/`) + limpieza de stubs en release documental.

---

## Criterio “menos docs”: fusionar vs borrar vs legacy

| Situación | Acción |
|-----------|--------|
| Dos páginas enseñan lo mismo | **Fusionar** en capa correcta; otra → stub o `archive/` |
| Checkpoint / release obsoleto | **Archivar** |
| Duplicado sin prefijo tras `sp-*` | **Stub** → canónico (esta oleada); borrar stub en oleada siguiente si no hay links externos críticos |
| `will be` como manual de uso | Recortar / mover a `experiment/` o `product/` |

---

## Open claims (sobre la propia depuración documental)

### Claim H_DOC_ZEN_1

- **Enunciado:** Tras oleadas 1–2, la raíz de `docs/` contiene solo `index.md` + `README.md` (más carpetas), y la nav principal no incluye marca ni Producto como tab de primer nivel.
- **Predicción observable:** conteo de `*.md` en raíz = 2; `mkdocs.yml` sin `QNOW_BRAND` ni tab Producto dominante.
- **Protocolo mínimo:** `Get-ChildItem docs -File -Filter *.md`; servir MkDocs; comprobar tabs.
- **Falsación:** si la raíz sigue con ≥5 `.md` sueltos de dominio, el ZEN no se aplicó.
- **Reproducibilidad:** PR por oleada + este documento versionado.
- **Estado:** predicción de raíz = 2 satisfecha en working tree post Oleada 1 residual + Oleada 2.

### Claim H_DOC_ZEN_2

- **Enunciado:** Fusionar guides/tutoriales redundantes deja ≤1 página canónica por tarea how-to en nav (ingesta, search, quickstart, patrones).
- **Predicción observable:** tabla tarea → path (arriba); nav Guías sin entradas duplicadas para la misma tarea.
- **Falsación:** si alguna tarea queda sin página o con dos canónicas en nav, acotar el claim.
- **Reproducibilidad:** esta tabla + `mkdocs.yml`.
- **Estado:** predicción satisfecha para las cuatro tareas; tutoriales solo como índice legacy bajo Guías.

### Claim H_DOC_ZEN_3

- **Enunciado:** Stubs unprefixed/`en-*` en concepts/theory/api no degradan la lectura library-first si la nav solo enlaza `sp-*` / páginas ETI nativas.
- **Predicción observable:** ninguna entrada de nav apunta a un stub de idioma; `mkdocs build` sin warnings de página nav faltante.
- **Falsación:** si el sitio enlaza un stub como canónico o el lector no encuentra el `sp-*` en ≤2 clics desde Inicio, acotar.
- **Protocolo mínimo:** revisar `mkdocs.yml`; grep nav paths; `uv run mkdocs build`.
- **Reproducibilidad:** nav versionada + este claim.
- **Estado:** nav O4 solo canónicos; stubs fuera de nav (mantenimiento hasta release documental).

### Claim H_DOC_ZEN_4

- **Enunciado:** Tras Oleada 4, `index.md` expone Empezar → Espina → Ciencia en la primera pantalla, y Conceptos lista Espina ETI antes de Arquitectura/Patrones/Léxicos.
- **Predicción observable:** tres bloques H2 en ese orden en `index.md`; en `mkdocs.yml`, `concepts/eti-spine.md` aparece antes de `sp-architecture` / patterns / lexical; sin tab Producto.
- **Protocolo mínimo:** leer `docs/index.md` + sección Conceptos de `mkdocs.yml`; `uv run mkdocs build`.
- **Falsación:** si el funnel exige >1 pantalla para hallar API+espina+plan, o Espina queda bajo Arquitectura otra vez, acotar.
- **Reproducibilidad:** este documento + `index.md` + `mkdocs.yml` versionados.
- **Estado:** predicción satisfecha en working tree post O4.

---

## Preguntas abiertas (mantenimiento post-ZEN)

### 1. Stubs unprefixed — ¿borrar en release documental?

| Opción | Implica |
|--------|---------|
| **Mantener stubs** | Links viejos y bookmarks no 404; ruido en árbol; no listarlos en nav (H_DOC_ZEN_3). |
| **Borrar en release** | Árbol limpio; riesgo de 404 fuera de `docs/`; mitigar con grep repo + redirects. |
| **Default** | **Mantener** hasta primer *release documental* al VCS; luego borrar si grep no encuentra links externos críticos. |

### 2. ¿`experiment/` vs `validation/`? (criterio epistémico)

No es solo “¿corrimos el script?”. **Validamos** cuando podemos confrontar con **fuentes externas/similares**, razonar resultados **sin sesgo de confirmación**, leer **tendencias/patrones/variaciones** entre hipótesis y corridas, y **modelar correctamente** lo medido. Hasta entonces: protocolo e hipótesis en `experiment/`; scorecards auditables que cumplan ese criterio → `validation/`. Detalle en [`PRODUCT.md`](../product/PRODUCT.md) §5. El resumen Cypher histórico es probe, no §5.

### 3. Producto en nav MkDocs

| Opción | Implica |
|--------|---------|
| **Tab Producto** | Visibilidad comercial; rompe library-first; compite con API/ETI. |
| **Solo puntero** | Nav = librería; producto vivo en `product/` alineado a visión. |
| **Decisión (cerrada O4)** | **Solo puntero.** No reabrir sin decisión explícita. |

### 4. Bilingüe `en-*`

| Opción | Implica |
|--------|---------|
| **Bilingüe real** | Doble mantenimiento; cada claim en dos idiomas; coste alto. |
| **ES canónico + archive EN** | Un idioma vivo; EN histórico en archive/git. |
| **Default** | ES canónico; reintroducir `en-*` vivos solo bajo demanda explícita.
