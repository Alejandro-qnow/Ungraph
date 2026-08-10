# Tutoriales Ungraph

Tutoriales paso a paso para usar `ungraph` 0.1.5+.

Cada tutorial indica su **estado**:
- **Implementado** — flujo completamente soportado por la API estable.
- **Parcial** — posible con extras o con limitaciones documentadas.
- **Exploratorio** — diseño experimental; la API puede cambiar.

---

## Índice

| # | Archivo | Estado | Descripción |
|---|---------|--------|-------------|
| 1 | [sp-01-primer-grafo.md](sp-01-primer-grafo.md) | ✅ Implementado | Configurar, ingestar y buscar en tu primer grafo |
| 2 | [sp-02-modos-de-busqueda.md](sp-02-modos-de-busqueda.md) | ✅ Implementado | Comparar búsqueda textual, vectorial, híbrida y GraphRAG |
| 3 | [sp-03-ingesta-multifuente.md](sp-03-ingesta-multifuente.md) | ✅ Implementado | Ingestar MD, PDF, TXT con chunking adaptado |
| 4 | sp-04-patrones-personalizados.md | 🔶 Parcial | `GraphPattern`, nodos/relaciones propios |
| 5 | sp-05-inferencia-spacy.md | 🔶 Parcial | Extracción de entidades con spaCy (`ungraph[infer-es]`) |
| 6 | sp-06-inferencia-llm.md | 🔬 Exploratorio | Inferencia con Ollama / API externa |

---

## Ruta de aprendizaje recomendada

```
Tutorial 1  →  Tutorial 2  →  Tutorial 3
(base)          (búsqueda)     (multi-fuente)
```

Los tutoriales 1-3 son independientes entre sí una vez que tienes Neo4j en marcha,
aunque el Tutorial 2 se apoya en los datos del Tutorial 1 para las comparaciones.

---

## Prerequisitos comunes

- Python 3.10+
- Neo4j 5.x (local o AuraDB)
- `pip install ungraph`

Para funcionalidades adicionales:

| Extra | Comando | Añade |
|-------|---------|-------|
| PDF avanzado | `pip install ungraph[docling]` | Soporte PDF con Docling |
| Inferencia spaCy | `pip install ungraph[infer-es]` | Extracción de entidades en español |
| Analítica de grafo | `pip install ungraph[gds]` | Patrones GraphRAG avanzados (GDS) |

---

## Documentación relacionada

- [Guía de búsqueda](../guides/search.md)
- [Guía de ingesta](../guides/quickstart.md)
- [Patrones personalizados](../guides/custom-patterns.md)
- [API pública](../api/public-api.md)
- [Arquitectura](../concepts/architecture.md)
