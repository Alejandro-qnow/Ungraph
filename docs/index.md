# Ungraph — documentación para desarrolladores

Framework Python para construir **grafos de conocimiento** desde texto no estructurado, con pipeline **Extract → Transform → Inference (ETI)** y recuperación **GraphRAG** sobre Neo4j.

## Empezar

1. [Inicio rápido](guides/sp-quickstart.md)
2. [Arquitectura](concepts/sp-architecture.md)
3. [API pública](api/sp-public-api.md)
4. [Flujo de trabajo del equipo](DEVELOPMENT_WORKFLOW.md)

## Vista del sitio

| Sección | Contenido |
|---------|-----------|
| Producto | Visión, niveles A/B/C, historias de usuario |
| Conceptos | Clean Architecture, [slot Infer](concepts/inference-slot.md), patrones de grafo |
| Guías | Ingesta, búsqueda, patrones personalizados |
| API | Referencia de funciones y configuración |
| Teoría | GraphRAG, Neo4j/Cypher, principios arquitectónicos |
| Tutoriales | Recorridos prácticos paso a paso |

## Vista previa local

```bash
uv sync --extra docs
uv run mkdocs serve -a 127.0.0.1:8000
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000).
