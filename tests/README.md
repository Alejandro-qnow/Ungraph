# Tests para Ungraph

Los archivos en la raíz de `tests/` que aún importan el layout antiguo (`src/` + `domain.*`)
están listados en `conftest.py` (`collect_ignore`) y **no se recolectan** hasta migrarlos a `ungraph.*`.

## Estructura de Tests

```
tests/
├── conftest.py                    # Fixtures Neo4j + collect_ignore (legacy)
├── fixtures/                      # Datos mínimos (p. ej. topology_alpha.md)
├── integration/                   # Integración adicional (topología)
├── test_installation.py           # Smoke de empaquetado
├── test_knowledge_mining_unit.py  # Minado sin Neo4j (mocks)
├── test_entity_graph_integration.py  # Fusión :Entity (Neo4j)
├── test_e2e_complete.py          # Tests E2E con Neo4j real
├── ...                           # Otros tests alineados a ungraph.*
```

## Tipos de Tests

### Tests Unitarios
- **Sin dependencias externas** (mocks)
- **Rápidos** (< 1 segundo total)
- **Marcados con:** `@pytest.mark.unit` (implícito si no es integration/e2e)

### Tests de Integración
- **Requieren Neo4j** configurado
- **Marcados con:** `@pytest.mark.integration`
- **Se saltan automáticamente** si Neo4j no está disponible

### Tests E2E (End-to-End)
- **Requieren Neo4j** configurado
- **Prueban flujo completo** (ingesta → búsqueda)
- **Marcados con:** `@pytest.mark.e2e`

## Dependencias de desarrollo

Desde la raíz del repo (incluye pytest, pytest-mock, pytest-cov, pytest-timeout):

```bash
uv sync --extra dev
```

## Ejecutar Tests

### Todos los tests unitarios (sin Neo4j):
```bash
pytest tests/ -v -m "not integration and not e2e"
```

### Solo tests unitarios específicos:
```bash
pytest tests/test_unit_complete.py -v
pytest tests/test_graph_patterns.py -v
```

### Tests de integración (requieren Neo4j):
```bash
# Configurar variables de entorno primero
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_PASSWORD="your_password"
export NEO4J_USER="neo4j"  # Opcional
export NEO4J_TEST_DATABASE="test_ungraph"  # Opcional

# Ejecutar tests de integración
pytest tests/test_e2e_complete.py -v -m integration

# Ejecutar tests E2E
pytest tests/test_e2e_complete.py -v -m e2e
```

### Todos los tests (incluyendo integración):
```bash
# Con Neo4j configurado
pytest tests/ -v
```

### Con cobertura:
```bash
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

## Configuración para CI/CD

Los tests están configurados para ejecutarse automáticamente en CI/CD:

- **GitHub Actions:** `.github/workflows/ci.yml`
- **Unit tests:** Se ejecutan en múltiples versiones de Python (3.10, 3.11, 3.12)
- **Integration tests:** Se ejecutan con Neo4j en Docker

### Ejecutar localmente como en CI:

```bash
# Unit tests
pytest tests/ -v -m "not integration and not e2e"

# Integration tests (requiere Neo4j corriendo)
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_PASSWORD="testpassword123"
pytest tests/test_e2e_complete.py -v -m integration
```

## Variables de Entorno para Tests

### Requeridas para tests de integración:
- `NEO4J_URI` - URI de conexión a Neo4j (ej: `bolt://localhost:7687`)
- `NEO4J_PASSWORD` - Contraseña de Neo4j

### Opcionales:
- `NEO4J_USER` - Usuario de Neo4j (default: `neo4j`)
- `NEO4J_TEST_DATABASE` - Base de datos de prueba (default: `test_ungraph`)

### Alternativa con prefijo UNGRAPH_:
- `UNGRAPH_NEO4J_URI`
- `UNGRAPH_NEO4J_PASSWORD`
- `UNGRAPH_NEO4J_USER`

## Fixtures Disponibles

### Fixtures básicos:
- `data_dir` - Directorio de datos de prueba
- `markdown_file` - Archivo Markdown de prueba (`110225.md`)
- `txt_file` - Archivo de texto de prueba (`AnnyLetter.txt`)

### Fixtures de Neo4j:
- `neo4j_driver` - Driver de Neo4j (sesión)
- `neo4j_database` - Nombre de la base de datos de prueba
- `clean_neo4j_database` - Limpia la base de datos antes/después de cada test
- `skip_if_no_neo4j` - Helper para saltar tests si Neo4j no está disponible

## Notas

- Los tests de integración **requieren Neo4j corriendo**
- Los tests se pueden ejecutar sin Neo4j (se saltan automáticamente)
- La base de datos de prueba se limpia automáticamente antes/después de cada test
- Los tests E2E verifican el flujo completo: ingesta → búsqueda
- Los tests unitarios verifican guardias, validaciones y casos límite

## Troubleshooting

### Error: "Neo4j no disponible"
- Verificar que Neo4j está corriendo: `docker ps` o `neo4j status`
- Verificar variables de entorno: `echo $NEO4J_URI`
- Verificar conectividad: `cypher-shell -u neo4j -p password "RETURN 1"`

### Error: "Database does not exist"
- Crear la base de datos manualmente en Neo4j
- O usar la base de datos por defecto (`neo4j`)

### Tests muy lentos
- Ejecutar solo tests unitarios: `pytest -m "not integration and not e2e"`
- Usar `-x` para parar en el primer error: `pytest -x`
