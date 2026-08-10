# Flujo de trabajo, ramas y tags (Ungraph)

**Objetivo:** mantener **`main` estable y publicable**, trabajar en **ramas** acotadas, etiquetar **releases**, y clasificar trabajo por **tipo** (feature, fix, chore, docs, research, …).

---

## 1. Rama `main`

- **`main`** es la línea estable: debe pasar **CI** en GitHub Actions antes de fusionar.
- Los cambios entran solo por **pull request** (revisión + checks verdes).
- Los hotfixes críticos pueden partir de un tag de release y volver a `main` con PR pequeño y bien etiquetado.

---

## 2. Nombres de rama (convención)

Prefijo claro + descripción en `kebab-case`:

| Tipo (plan) | Prefijo de rama | Ejemplo |
|-------------|-----------------|---------|
| **feature** | `feature/` | `feature/graph-topology-validator` |
| **fix** | `fix/` | `fix/neo4j-session-leak` |
| **chore** | `chore/` | `chore/ci-codecov-path` |
| **docs** | `docs/` | `docs/graphrag-matrix-update` |
| **research** | `research/` | `research/gds-community-detection` |
| **test** | `test/` | `test/ingest-integration-matrix` |
| **refactor** | `refactor/` | `refactor/dependencies-factories` |

*Research:* rama corta o spike; el resultado suele traducirse en `docs/`, issues o un `feature/` posterior.

---

## 3. Mensajes de commit (Conventional Commits)

Formato recomendado:

```text
<type>(<scope opcional>): <descripción breve en imperativo>

[cuerpo opcional]
```

### Tipos alineados al plan de trabajo

| Categoría de plan | `type` en commit | Notas |
|-------------------|-------------------|--------|
| feature | `feat` | Nueva capacidad de producto / API. |
| fix | `fix` | Corrección de bug o regresión. |
| chore | `chore` | Herramientas, CI, deps, housekeeping. |
| docs | `docs` | Solo documentación. |
| research | `chore` o `docs` | Usar **scope**: `chore(research): …` o `docs(research): …` para espigas y notas. |
| test | `test` | Solo tests. |
| CI | `ci` | Solo cambios en pipelines. |
| refactor | `refactor` | Sin cambio de comportamiento. |
| performance | `perf` | Optimización medible. |

Ejemplos:

- `feat(search): add metadata filter to pattern map`
- `fix(ingest): scope NEXT_CHUNK when uid missing`
- `chore(ci): merge integration and e2e Neo4j job`
- `docs(theory): refresh GraphRAG matrix`
- `chore(research): spike local retriever with GDS notes`
- `test(integration): file-page-chunk topology counts`

**Breaking change:** pie del mensaje `BREAKING CHANGE: …` o `feat!:` según [Conventional Commits](https://www.conventionalcommits.org/).

---

## 4. Tags y versiones

- **Versiones semánticas:** `vMAJOR.MINOR.PATCH` (ej. `v0.1.5`, `v0.2.0`).
- **Pre-releases:** `v0.2.0-rc.1`, `v0.2.0-beta.2`.
- **Annotated tags** para releases publicados (`git tag -a v0.2.0 -m "Release 0.2.0"`).
- Tras un tag de release, actualizar changelog y publicar según los scripts y notas del repositorio.

---

## 5. Plan de trabajo por categorías

Para roadmaps, issues o tableros, **etiquetar** cada ítem (GitHub Labels recomendado):

| Etiqueta | Uso |
|----------|-----|
| `feature` | Entrega de capacidad nueva. |
| `fix` | Bug o corrección de comportamiento. |
| `chore` | Mantenimiento, deps, CI, tooling. |
| `docs` | Documentación / tutoriales. |
| `research` | Exploración, spike, prototipo no comprometido a producción. |
| `test` | Cobertura, flaky, harness. |

Así el “plan maestro” se puede **seccionar** sin mezclar research con releases estables.

---

## 6. Pull requests

- Plantilla en [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md).
- Formularios de **issue** por tipo: ver §8.
- PR pequeños, un tema principal por PR cuando sea posible.
- Referenciar issues: `Closes #123`.

---

## 7. Prácticas de código (resumen)

- El directorio **`tests/`** debe estar **versionado** con el código; no listar `tests/` en `.gitignore` (artefactos locales: `.pytest_cache/`, `__pycache__/`, ya ignorados por otras reglas).
- Seguir el estilo del módulo tocado; **tests** para lógica nueva o regresiones.
- Marcadores pytest: `unit` / `integration` / `e2e` / `eval` / `openai` según [`pytest.ini`](../pytest.ini).
- Sin secretos en el repo; variables `UNGRAPH_*` / Neo4j solo en entorno o CI.
- **CI:** `flake8` corre sobre `ungraph/` y `tests/`; `black`/`isort` sobre `tests/` hasta un PR de formateo unificado de `ungraph/`.

---

## 8. Issues (plantillas)

En [`.github/ISSUE_TEMPLATE/`](../.github/ISSUE_TEMPLATE/) hay formularios por tipo:

| Plantilla | Uso |
|-----------|-----|
| `01_feature.yml` | Nueva capacidad |
| `02_bug.yml` | Regresión / bug |
| `03_chore.yml` | CI, deps, tooling |
| `04_docs.yml` | Documentación |
| `05_research.yml` | Spikes / exploración |

**Etiquetas sugeridas** (crearlas una vez en el repo; nombres cortos, sin tildes):

| Nombre | Color (hex sugerido) | Significado |
|--------|----------------------|-------------|
| `feature` | `#0E8A16` | trabajo de producto |
| `fix` | `#D73A4A` | corrección |
| `chore` | `#FEF2C0` (texto oscuro) | mantenimiento |
| `docs` | `#0075CA` | documentación |
| `research` | `#D4C5F9` (texto oscuro) | spike |
| `test` | `#FBCA04` | solo tests |
| `triage` | `#EDEDED` | pendiente de clasificar |

Con [GitHub CLI](https://cli.github.com/) y `gh auth login`, puedes sincronizarlas desde el raíz del repo:

`python scripts/sync_github_labels.py`

Las plantillas añaden `triage` hasta que el equipo asigne prioridad / milestone.

---

## 9. Referencias cruzadas

- Plan de ejecución e índice: [`PLAN_MAESTRO.md`](PLAN_MAESTRO.md)
- Producto y prioridades: [`PRODUCT.md`](PRODUCT.md)
- Skills de agentes: [`agent/AGENT_SKILLS.md`](../agent/AGENT_SKILLS.md)
