# Checklist de curación documental ETI

## Propósito

Lista operativa de **estilo y forma** para curar páginas bajo `docs/` alineadas al protocolo del subagente `eti-doc-reviewer` y a la rule `.cursor/rules/docs-scientific-canon.mdc`. Marca casillas por archivo curado.

No sustituye el programa experimental (`PLAN_MAESTRO.md`, skill `eti-experiment-science`): aquí se cuida semántica, plantilla, citas y claims falseables — no se diseñan oleadas DoE ni se inventan métricas.

Anclas de contenido: [`WHITEPAPER_UNGRAPH_IMRAD.md`](WHITEPAPER_UNGRAPH_IMRAD.md), [`INSPIRATION_MATRIX.md`](INSPIRATION_MATRIX.md), [`../PRODUCT.md`](../product/PRODUCT.md).

Estructura y depuración: [`DOCUMENTARY_ZEN.md`](DOCUMENTARY_ZEN.md).

---

## Alineación ZEN

Antes o al cerrar la curación de una página (ver [`DOCUMENTARY_ZEN.md`](DOCUMENTARY_ZEN.md)):

- [ ] ¿Está en la **capa correcta** de la secuencia (fundamento / experimentación / medición / estandarización / productivización)?
- [ ] ¿**Reduce ruido** (fusiona, archiva o evita duplicar guides↔tutoriales / concepts↔theory)?
- [ ] ¿La **raíz** de `docs/` queda limpia (sin nuevo `.md` suelto de dominio; solo `index`/`README` + carpetas)?
- [ ] ¿Nav/links siguen **library-first** y dentro de `docs/`?

---

## Ámbito por carpeta

| Carpeta / zona | Items a curar (rol) | Plantilla aplicable |
|----------------|---------------------|---------------------|
| `concepts/` | Intro, arquitectura, espina ETI, extracción, transformación, inferencia (+ slot Infer I/O), patrones, grafos léxicos | Completa: Motivation → Theory → In Ungraph → Open claims |
| `theory/` | GraphRAG, Neo4j, Clean Architecture (y piezas teóricas nuevas) | Completa (misma plantilla) |
| `research/` | Whitepaper IMRaD, matriz de inspiración, este checklist | IMRaD / matriz / protocolo; Open claims donde haya hipótesis nuevas |
| `guides/` | Quickstart, ingesta, search, patrones | Pasos ejecutables; sin narrativa teórica larga |
| `tutoriales/` | Recorridos prácticos numerados | Pasos + resultado esperado; enlace a concepts/theory si hace falta |
| `examples/` | Ejemplos y notebooks | Mínimo reproductible; no claims de capacidad no medidos |
| `api/` | API pública, configuración, patrones de búsqueda | Contrato estable; sin producto ni trayectoria |
| `validation/` | Resúmenes de validación | Solo lo medido/versionado; enlazar scorecard o fixture |
| Raíz `docs/` | Solo `index.md`, `README.md` | Entrada; sin `.md` de dominio sueltos |
| `product/`, `experiment/`, `ops/`, `archive/` | PRODUCT, VISION, PLAN_MAESTRO, BENCHMARK_*, ROADMAP_*, planes `will be` (p. ej. DQ), workflow, checkpoints | `is` vs `will be`; no plantilla teórica completa; no how-to ejecutable en experiment |
| `index.md`, `README.md` | Funnel ETI y dónde ir | Entrada; punteros válidos al árbol |
| `overrides/`, `stylesheets/` | Tema MkDocs / marca Qnow | Fuera de curación científica; paleta en `stylesheets/QNOW_BRAND.md` + `qnow-tokens.css` |

Prefijos: `sp-*` (ES), `en-*` (EN); sin prefijo = legado o compartido. Una página, un idioma (salvo glosario).

---

## Checklist de estilo y forma

Marcar al curar **cada** página. Omitir secciones marcadas N/A según el tipo de artefacto (ver abajo).

### Identidad del artefacto

- [ ] Ruta bajo `docs/`; capa correcta (claim → research/theory/concepts; pasos → guides/tutoriales/examples; contrato → api; plan medible → raíz)
- [ ] Audiencia clara (developer / research / tutorial)
- [ ] Originalidad ETI: la página no sería un rewrite genérico de “cómo hacer RAG” sin slots E/T/I y objetos epistémicos

### Estructura de página (cuando aplique plantilla completa)

- [ ] `#` título nombra el fenómeno o método (no un feature genérico)
- [ ] `## Motivation` — problema epistémico (minería/generación de conocimiento), no solo ingeniería de software
- [ ] `## Theory` — definiciones, formalismos ligeros, linaje; claim científico separado de implementación
- [ ] `## In Ungraph` — mapeo a Extract / Transform / Inference / Depuración / Interface; rutas de código solo como *probe*
- [ ] `## Open claims (falseables)` — al menos un claim con criterio de fracaso, o N/A justificado

### Semántica ETI

- [ ] No confunde *retrieval* / GraphRAG / MCP con *knowledge engineering* (aquellos son consumidores del almacén epistémico)
- [ ] Distingue creencia / evidencia / confianza / refutación / provenance / depuración / promoción (bronze→gold) donde el tema lo exige
- [ ] Inference se trata como *slot* (interfaz), no como un único motor NER
- [ ] In Ungraph no infla el código actual: no presenta trayectoria como capacidad en producción

### `is` vs `will be`

- [ ] Capacidades funcionales/medidas reflejan `main` (código + tests/benchmarks que pasan)
- [ ] Trayectoria e hipótesis van como `will be` / Open claim, no como hecho
- [ ] No hay ciencia/producto paralelo fuera de `docs/` (punteros desde otros sitios, no duplicados)

### Citas y anclaje literario

- [ ] Cada claim teórico fuerte ancla ≥1 fuente (autor/año) o ID `Ixx` de la matriz
- [ ] Preferencia por linajes ya en whitepaper / matriz (KBC/NELL/DeepDive, GraphRAG surveys, neurosymbolic, abducción, PROV-O/EVI, KG refinement, CommonKADS)
- [ ] Fuente nueva (si hay) justifica encaje ETI
- [ ] No se inventan DOIs ni resultados experimentales

### Open claims falseables

Para cada claim abierto en la página:

- [ ] **Enunciado** claro
- [ ] **Predicción observable**
- [ ] **Protocolo mínimo** (corpus/fixture, métrica, wipe/seed, comando o notebook)
- [ ] **Falsación** (si ocurre …, se rechaza o acota)
- [ ] **Reproducibilidad** (artefacto versionado: fixture, scorecard, ExperimentRun)
- [ ] Si el claim exige oleada experimental → enlace a `PLAN_MAESTRO.md` (no mega-diseño DoE en la página de theory)

### Idioma, links, voz

- [ ] Prefijo `sp-*` / `en-*` respetado; un idioma por página
- [ ] Links relativos válidos bajo `docs/` (MkDocs)
- [ ] Voz directa: creencia, evidencia, provenance, depuración, abducción, slot Inference — sin marketing vacío ni jerga ornamental
- [ ] Sin emojis ornamentales en el cuerpo

### Nav / índice (páginas nuevas o renombradas)

- [ ] Entrada en `mkdocs.yml` `nav` si debe aparecer en el sitio
- [ ] Puntero desde `docs/index.md` y/o README de carpeta cuando corresponda
- [ ] No crear carpetas científicas paralelas (`docs/science/`, whitepaper solo en `agent/`, etc.)

---

## Checklist por tipo de artefacto

### Theory / concepts / research (plantilla completa)

- [ ] Motivation / Theory / In Ungraph / Open claims presentes o equivalentes semánticos
- [ ] Theory no es tutorial de API
- [ ] In Ungraph nombra slots ETI sin afirmar depuración/EVI no medida
- [ ] ≥1 Open claim falseable **o** enlace explícito a claim ya abierto en research/plan
- [ ] Research IMRaD: métodos y resultados solo si son reproducibles/versionados; Discussion no mezcla `is` y `will be`

### API (contrato)

- [ ] Firma, parámetros, errores, configuración — estables
- [ ] Sin Motivation narrativa de producto ni Open claims de trayectoria
- [ ] Ejemplos mínimos de uso, no scorecard científico
- [ ] Si menciona Inference/Extract: comportamiento **is** verificable en `main`

### Guide / tutorial / example (pasos)

- [ ] Orden ejecutable; prerrequisitos; resultado observable
- [ ] No afirma capacidades no medidas; si alude a trayectoria, enlace a research/plan
- [ ] Theory/concepts enlazados, no duplicados
- [ ] Example/notebook: fixture o datos de ejemplo versionados cuando sea posible

### Experiment / producto / ops (`experiment/PLAN_MAESTRO`, `BENCHMARK_*`, `product/PRODUCT`, …)

- [ ] Hipótesis y gates enlazan scorecards E/T/I o ExperimentRun — no prosa suelta sin métrica
- [ ] Separación explícita `is` / `will be` / Open claims
- [ ] No sustituye páginas theory; las referencia
- [ ] No inventa p-values ni benchmarks no ejecutados
- [ ] Planes `will be` no viven en `guides/` (how-to ejecutable)

### Validation

- [ ] Resume evidencia ya corrida o artefactos en repo
- [ ] Criterio de paso/fallo observable
- [ ] Enlace a plan o fixture; sin marketing de “validado” sin artefacto

---

## Anti-patrones

```markdown
<!-- ❌ Afirmar en docs lo no medido en main -->
Inference ya depura beliefs con argumentación EVI en producción.

<!-- ✅ Separar estado e hipótesis -->
**is:** Inference extrae entidades/relaciones (spaCy/LLM) con provenance parcial.
**will be / Open claim:** depuración EVI — ver research + PLAN_MAESTRO.
```

```text
❌ Nueva carpeta docs/science/ o whitepaper solo en agent/
✅ Ampliar docs/research/ o docs/theory/ y enlazar desde index/nav MkDocs
```

```text
❌ Página theory que redefine conocimiento como “mejor retrieval GraphRAG”
✅ Retrieval/MCP como interfaz sobre creencias, evidencia y depuración
```

```text
❌ Open claim sin falsación (“mejoraremos la confianza”)
✅ Claim H_* con predicción, protocolo mínimo y criterio de fracaso
```

---

## Cómo usar

1. Identificar el artefacto (ruta + tipo de plantilla de la tabla de ámbito).
2. Invocar el subagente **eti-doc-reviewer** (`.cursor/agents/eti-doc-reviewer.md`) al editar o reescribir docs.
3. Diagnosticar gaps → editar el markdown → anclar citas/`Ixx` → abrir o acotar Open claims.
4. Recorrer este checklist y marcar casillas aplicables; dejar N/A las del tipo que no corresponde.
5. Entregar resumen al estilo del revisor: Diagnóstico, Edits, Citas ancladas, Open claims, Preguntas para conversar.

**Delegar (fuera de este checklist):** pipeline ETI → `eti-pipeline`; Cypher/schema → `cypher-craft` / `kg-schema`; suites operativas → `eti-operation-curation` / `ungraph-test`.

---

## Registro de mantenimiento (no oleada ZEN)

| Tanda | Alcance | Estado |
|-------|---------|--------|
| A — guides + API (nav) | 4 guides canónicos + 4 API `sp-*` | Curados 2026-08 (Checklist Guide/API); ver nota en [`DOCUMENTARY_ZEN.md`](DOCUMENTARY_ZEN.md) |
| B — experiment | `PLAN_MAESTRO`, `BENCHMARK_ETI_DOMAINS`, `ROADMAP_LEVEL_C` (+ toque DQ) | Curados 2026-08 (Checklist Experiment); ver nota en [`DOCUMENTARY_ZEN.md`](DOCUMENTARY_ZEN.md) |
| C — examples | `examples/sp-basic-examples`, `sp-advanced-examples`, `sp-notebooks` (+ stubs) | Curados 2026-08 (Checklist Example/notebook); ver nota en [`DOCUMENTARY_ZEN.md`](DOCUMENTARY_ZEN.md) |
| D — ops | `ops/DEVELOPMENT_WORKFLOW`, `ops/INSTALLATION_INFERENCE` | Pendiente |
| Stubs (release) | unprefixed / `en-*` fuera de nav | Mantener hasta release documental (H_DOC_ZEN_3) |
