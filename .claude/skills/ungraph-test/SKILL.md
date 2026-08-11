---
name: ungraph-test
description: Crea tests para Ungraph en los tres niveles (unit, integration, e2e). Úsalo cuando necesites cubrir un nuevo servicio, caso de uso, repositorio o flujo ETI completo. Prioridad alta según análisis: tests NO deben estar en .gitignore.
allowed-tools: Read Grep Glob
---

Eres el guardián de la calidad de Ungraph. Cuando crees o revises tests:

## Niveles de test y marcadores pytest

```
tests/
  unit/          # Sin Neo4j, sin red. Rápidos. Mock de repositorios y servicios de infraestructura.
  integration/   # @pytest.mark.integration — requiere Neo4j real (Docker). Prueba repositorios y servicios Neo4j.
  e2e/           # @pytest.mark.e2e — flujo ETI completo: ingest_document → search → assert nodos en grafo.
```

Usa los marcadores definidos en `pytest.ini`. Nunca mezcles niveles.

## Reglas para tests unitarios

1. **Mockea en la frontera de dominio**: el dominio no conoce Neo4j; mockea `ChunkRepository`, no `neo4j.GraphDatabase`.
2. **Un assert conceptual por test**: un test puede tener múltiples `assert` si todos verifican la misma propiedad.
3. **Nombrado**: `test_<método>_<condición>_<resultado_esperado>` — ej. `test_chunk_empty_text_raises_value_error`.
4. **Fixtures en `conftest.py`**: reutiliza fixtures de documento sintético, configuración mínima y embedding stub.

## Reglas para tests de integración

1. Usa fixture de sesión `neo4j_driver` que conecte al servicio Neo4j del CI (ver `.github/workflows/ci.yml`).
2. Limpia el grafo antes/después con `MATCH (n) DETACH DELETE n` dentro del fixture, no en el test.
3. Verifica tanto el retorno del método como el estado real del grafo con una query Cypher de verificación.

## Fixtures esenciales a crear (si no existen)

```python
# conftest.py
@pytest.fixture
def sample_document():
    """Documento sintético mínimo para tests."""

@pytest.fixture
def stub_embedding_service():
    """Devuelve vector fijo de dimensión 384 sin llamar a ningún modelo."""

@pytest.fixture
def in_memory_chunk_repo():
    """Implementación dict-based del ChunkRepository para tests unitarios."""
```

## Checklist antes de entregar un test

- [ ] El test no toca red ni Neo4j real (si es unitario)
- [ ] El archivo está bajo `tests/` (nunca en `.gitignore`)
- [ ] Existe `conftest.py` en el directorio del nivel
- [ ] El marcador pytest correcto está aplicado
- [ ] El test falla por la razón correcta antes de implementar la funcionalidad (TDD check)

## Curación de operaciones ETI (nivel producción)

Para MVP o cambios que tocan Extract/Transform/Infer y Neo4j en serie, complementar este skill con **eti-operation-curation**: matriz fase × tipo de test, golden paths, regresión de Cypher y humo tras subir LangChain/LangGraph (**ungraph-langstack-ops**).
