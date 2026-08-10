# Cambios para v0.1.5

## 🐛 Bug Crítico Corregido

### Falta `ungraph/core/__init__.py`
- **Problema**: `import ungraph` fallaba con `ModuleNotFoundError: No module named 'ungraph.core'`
- **Solución**: Agregado `ungraph/core/__init__.py` con exports apropiados
- **Impacto**: El paquete ahora se puede importar correctamente en entornos limpios

## ✅ Mejoras de Testing

### Smoke Test de Packaging Crítico
- Agregado test crítico que valida `import ungraph; print(ungraph.configure)`
- Este test se ejecuta primero en el smoke test suite
- Agregado al CI/CD workflow para prevenir regresiones

### CI/CD Actualizado
- Agregado paso explícito de "Run critical packaging test" en GitHub Actions
- Valida que el import básico funciona antes de ejecutar otros tests

## 📝 Ajustes de Documentación

### Claims sobre Inferencia Ajustados
- **Antes**: README afirmaba "full ETI pipeline" sin aclarar estado experimental
- **Ahora**: Sección de Inferencia claramente marcada como "experimental"
- Agregada nota: "For production use, Ungraph currently provides a robust Extract-Transform pipeline with GraphRAG retrieval patterns"
- Clarifica que la fase Infer está disponible pero aún en refinamiento

### Descripción de GQL/Cypher Mejorada
- **Antes**: "Graph Query Language Standard (Cypher)"
- **Ahora**: "Neo4j Cypher (property-graph query language), with alignment toward ISO GQL standards"
- Más preciso sobre la relación entre Cypher y GQL (ISO/IEC 39075:2024)

## 📦 Archivos Modificados

1. `ungraph/core/__init__.py` - **NUEVO** - Módulo core ahora es un paquete Python válido
2. `scripts/smoke_test_installation.py` - Agregado test crítico de packaging
3. `.github/workflows/ci.yml` - Agregado test de packaging crítico en CI
4. `README.md` - Ajustados claims sobre Inferencia y descripción de GQL
5. `pyproject.toml` - Descripción actualizada sobre Cypher/GQL

## 🚀 Próximos Pasos para Publicar v0.1.5

```bash
# 1. Verificar que todo funciona
python -c "import ungraph; print('configure:', ungraph.configure)"

# 2. Ejecutar validaciones pre-build
python scripts/pre_build_validation.py

# 3. Build y publicar (el script incrementará automáticamente a 0.1.5)
python scripts/publish.py publish --prod
```

## 📋 Checklist Pre-Publicación

- [x] `ungraph/core/__init__.py` creado
- [x] Test crítico de packaging agregado
- [x] CI/CD actualizado con test de packaging
- [x] README ajustado sobre estado de Inferencia
- [x] Descripción de GQL/Cypher corregida
- [x] Test crítico funciona: `python -c "import ungraph; print(ungraph.configure)"`

## 🎯 Impacto Esperado

- ✅ El paquete se puede instalar e importar sin errores
- ✅ Los usuarios pueden seguir el Quick Start sin problemas
- ✅ Claims más honestos sobre capacidades actuales vs. planificadas
- ✅ Mejor comprensión del propósito y estado del proyecto


## 🔧 Evidencia de ingeniería (CI, topología, E2E)

- **CI**: Workflow reparado (`tests/test_installation.py`, `tests/test_e2e_complete.py`); jobs separados para tests **integration** y **e2e**; cobertura unitaria con `--cov-report=xml`; variables `UNGRAPH_NEO4J_*` y `NEO4J_*` aceptadas en fixtures.
- **Integración Neo4j**: `tests/integration/test_file_page_chunk_topology.py` valida conteos File/Page/Chunk y `NEXT_CHUNK` sin cruces de `source_document_uid`.
- **E2E**: ingest → índices → `text_search` sobre fixture sintético.
- **Infer**: tests unitarios spaCy/OpenAI/BYO condicionales; inferencia sigue marcada como experimental en documentación hasta ampliar cobertura.
- **DX**: `import ungraph` evita cargar Neo4j/HuggingFace/LangChain hasta usar APIs que los necesitan; tipos públicos (`Chunk`, `GraphPattern`, …) vía carga perezosa.
- **Etiquetas GitHub**: script opcional `scripts/sync_github_labels.py` (CLI `gh`).

*Nota: formato **black/isort** en CI aplicado a `tests/`; el paquete `ungraph/` puede ampliarse cuando se normalice estilo en todo el árbol.*
