# Documentación de Ungraph

Documentación completa de la librería Ungraph para construcción de grafos de conocimiento.

## Sitio MkDocs (preview local)

```bash
uv sync --extra docs
uv run mkdocs serve -a 127.0.0.1:8000
```

Abre http://127.0.0.1:8000. Configuración en `mkdocs.yml` (tema Material + overrides en `docs/overrides/` y `docs/stylesheets/extra.css`).

## 📚 Índice

### Producto
- [Documento maestro de producto](PRODUCT.md) — Finalidad, niveles A/B/C (resumen), historias de usuario y casos de uso  
  *Encaje con la visión:* [VISION_AND_TUTORIALS.md](VISION_AND_TUTORIALS.md) (§3 niveles, §8 aprendizaje); *plan técnico:* [../agent/AGENT_SKILLS.md](../agent/AGENT_SKILLS.md) (prioridades §8, visualización §7).

### Desarrollo (equipo / contribuciones)
- [Flujo de trabajo: ramas, tags, commits y etiquetas (feature / fix / chore / docs / research)](DEVELOPMENT_WORKFLOW.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md) (entrada corta; el detalle está en el documento anterior)
- Plantillas GitHub: `.github/ISSUE_TEMPLATE/` y `.github/PULL_REQUEST_TEMPLATE.md`

### Visión y plan de tutoriales
- [Visión de producto y plan de tutoriales (desarrollo paralelo)](VISION_AND_TUTORIALS.md) — Anclaje de visión, fechas de trabajo y mapa de tutoriales (implementado / parcial / exploratorio)

### Conceptos Fundamentales
- [Introducción a Ungraph](concepts/sp-introduction.md) - Visión general y propósito
- [Arquitectura del Sistema](concepts/sp-architecture.md) - Clean Architecture y estructura
- [Patrones de Grafo](concepts/sp-graph-patterns.md) - Sistema de patrones configurables

### Guías de Uso
- [Guía de Inicio Rápido](guides/sp-quickstart.md) - Primeros pasos
- [Ingesta de Documentos](guides/sp-ingestion.md) - Cómo ingerir documentos
- [Búsqueda en el Grafo](guides/search.md) - Patrones de búsqueda disponibles
- [Patrones Personalizados](guides/sp-custom-patterns.md) - Crear patrones propios
- [Plan: calidad de datos, atributos `dq_*` y capa Pydantic sobre el grafo](guides/sp-data-quality-graph-plan.md) — Plan detallado para retomar el trabajo de forma coherente (nivel C, roadmap en repo)

### Referencia de API
- [API Pública](api/sp-public-api.md) - Funciones principales de la librería
- [Patrones de Búsqueda GraphRAG](api/sp-search-patterns.md) - Referencia completa
- [Configuración](api/sp-configuration.md) - Gestión de configuración

### Ejemplos
- [Ejemplos Básicos](examples/basic-examples.md) - Ejemplos simples
- [Ejemplos Avanzados](examples/advanced-examples.md) - Casos de uso complejos
- [Notebooks](examples/notebooks.md) - Jupyter notebooks disponibles

### Teoría y Referencias
- [GraphRAG](theory/sp-graphrag.md) - Fundamentos teóricos de GraphRAG
- [Neo4j y Cypher](theory/sp-neo4j.md) - Conceptos de Neo4j y queries Cypher
- [Clean Architecture](theory/sp-clean-architecture.md) - Principios arquitectónicos aplicados

---

**Última actualización:** 2026-04-13




