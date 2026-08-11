# Tests para Funcionalidades Avanzadas

## Estructura de Tests Avanzados

```
tests/
├── test_advanced_search_patterns.py      # Tests unitarios de patrones avanzados
├── test_advanced_search_integration.py   # Tests de integración E2E
└── conftest.py                           # Fixtures compartidas (incluye test_data_with_entities)
```

## Requisitos

### Para Tests Básicos
- Neo4j configurado (variables de entorno: `NEO4J_URI`, `NEO4J_PASSWORD`)

### Para Tests Avanzados
- Neo4j configurado
- `ungraph[gds]` instalado: `pip install ungraph[gds]`
- Neo4j GDS plugin instalado (para tests de Community Summary)

## Ejecutar Tests

### Todos los tests avanzados
```bash
pytest tests/test_advanced_search_patterns.py tests/test_advanced_search_integration.py -v -m integration
```

### Solo tests de patrones avanzados
```bash
pytest tests/test_advanced_search_patterns.py -v
```

### Solo tests de integración E2E
```bash
pytest tests/test_advanced_search_integration.py -v -m integration
```

### Test específico
```bash
pytest tests/test_advanced_search_patterns.py::TestAdvancedSearchPatterns::test_graph_enhanced_vector_search_execution -v
```

## Datos de Prueba

Los tests usan la fixture `test_data_with_entities` que crea:

- **File**: `test_document.md`
- **Page**: `page_1`
- **Chunks**: 5 chunks con contenido sobre machine learning, neural networks, deep learning
- **Entities**: `MachineLearning`, `NeuralNetwork`, `DeepLearning`
- **Relaciones**:
  - `File -[:CONTAINS]-> Page`
  - `Page -[:HAS_CHUNK]-> Chunk`
  - `Chunk -[:NEXT_CHUNK]-> Chunk`
  - `Chunk -[:MENTIONS]-> Entity`

## Tests Disponibles

### TestAdvancedSearchPatterns

1. **test_graph_enhanced_vector_search_available**: Verifica disponibilidad del patrón
2. **test_graph_enhanced_vector_search_query_generation**: Valida generación de query
3. **test_graph_enhanced_vector_search_execution**: Ejecuta búsqueda real
4. **test_local_retriever_query_generation**: Valida generación de query Local
5. **test_local_retriever_execution**: Ejecuta búsqueda Local real
6. **test_community_summary_gds_query_generation**: Valida generación de query Community Summary

### TestGDSService

1. **test_gds_service_available**: Verifica disponibilidad del servicio
2. **test_gds_service_initialization**: Test de inicialización
3. **test_gds_check_availability**: Verifica disponibilidad de GDS
4. **test_gds_detect_communities**: Test de detección de comunidades (requiere GDS)

### TestAdvancedSearchIntegration

1. **test_graph_enhanced_finds_related_context**: Verifica que encuentra contexto relacionado
2. **test_local_retriever_finds_communities**: Verifica que encuentra comunidades
3. **test_compare_basic_vs_graph_enhanced**: Compara Basic vs Graph-Enhanced

### TestGDSServiceIntegration

1. **test_gds_detect_communities_full_workflow**: Flujo completo de detección de comunidades

## Manejo de Módulos Opcionales

Los tests manejan correctamente cuando los módulos opcionales no están instalados:

- Si `ungraph[gds]` no está instalado, los tests se saltan con `pytest.skip()`
- Si GDS plugin no está disponible, los tests de GDS se saltan
- Los tests básicos siempre se ejecutan (no requieren módulos opcionales)

## Ejemplo de Salida

```
tests/test_advanced_search_patterns.py::TestAdvancedSearchPatterns::test_graph_enhanced_vector_search_execution PASSED
✅ Graph-Enhanced: 3 resultados encontrados
  1. Score: 0.8542, Chunk: test_chunk_1
  2. Score: 0.7821, Chunk: test_chunk_4
  3. Score: 0.7123, Chunk: test_chunk_2
```

## Troubleshooting

### Error: "Módulos avanzados no disponibles"
**Solución**: Instalar módulos opcionales:
```bash
pip install ungraph[gds]
```

### Error: "GDS no disponible"
**Solución**: Instalar Neo4j GDS plugin:
1. Descargar desde [Neo4j GDS](https://neo4j.com/docs/graph-data-science/)
2. Colocar en directorio `plugins/` de Neo4j
3. Reiniciar Neo4j

### Error: "Neo4j no disponible"
**Solución**: Configurar variables de entorno:
```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_PASSWORD="tu_contraseña"
```

### Tests se saltan automáticamente
**Normal**: Los tests se saltan si:
- Neo4j no está configurado
- Módulos opcionales no están instalados
- GDS plugin no está disponible

Esto es esperado y los tests informan el motivo del skip.





