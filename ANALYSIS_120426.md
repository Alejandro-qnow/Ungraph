# Análisis crítico: Ungraph como librería Python (12-04-2026)

**Alcance:** Este documento es un análisis estático del repositorio y la configuración publicada. No sustituye pruebas en runtime, auditoría de seguridad ni métricas de uso en producción.

**Referencia de versión:** `ungraph` **0.1.5** según [`pyproject.toml`](pyproject.toml) y [`ungraph/__init__.py`](ungraph/__init__.py).

---

## 1. Resumen ejecutivo

Ungraph es un framework en Python (3.12+) orientado a construir **grafos de conocimiento** a partir de texto no estructurado, persistidos en **Neo4j**, con patrón **Extract–Transform–Inference (ETI)** y recuperación tipo **GraphRAG** (búsqueda textual, vectorial e híbrida, y patrones avanzados opcionales con GDS).

El paquete se declara con **Development Status :: 3 – Alpha** en PyPI, lo cual es coherente con una API aún en evolución y con partes del producto marcadas como experimentales (especialmente la fase **Infer**).

Para una librería considerada **“completa”** en el sentido habitual del ecosistema Python (reproducible, estable para integradores, superficie pública clara y señales de madurez), el proyecto combina **bases sólidas de diseño y documentación** con **brechas importantes en gobernanza del código de prueba, alineación del CI con el árbol del repo y señales de tipado/contrato público**.

---

## 2. Estado actual: fortalezas

### 2.1 API pública y documentación de uso

El módulo raíz expone una API de alto nivel bien documentada en docstrings: configuración (`configure`, `reset_configuration`), ingesta (`ingest_document`), búsqueda (`search`, `vector_search`, `hybrid_search`, `search_with_pattern`) y utilidades (`suggest_chunking_strategy`). Esto facilita el “primer contacto” del usuario sin obligar a conocer toda la arquitectura interna.

### 2.2 Arquitectura y extensibilidad

La organización en capas (dominio, aplicación, infraestructura), factories en dependencias y **extras opcionales** en [`pyproject.toml`](pyproject.toml) (`infer`, `infer-en`, `infer-es`, `gds`, `ynet`, `dev`, `experiments`, `all`) es adecuada para una librería que debe crecer sin arrastrar todas las dependencias pesadas en la instalación mínima.

### 2.3 Documentación de proyecto

Existen guías y referencia en `docs/` (incluyendo conceptos, API pública, instalación e inferencia), y un README orientado a propuesta de valor, instalación y flujo ETI. El changelog puntual [`CHANGELOG_v0.1.5.md`](CHANGELOG_v0.1.5.md) documenta correcciones recientes relevantes (por ejemplo empaquetado de `ungraph.core`).

### 2.4 Publicación y automatización

Hay scripts de build/publicación ([`scripts/publish.py`](scripts/publish.py) y relacionados) y un pipeline CI en [`.github/workflows/ci.yml`](.github/workflows/ci.yml) que incluye build de rueda, instalación desde wheel, smoke tests, pytest con cobertura, servicio Neo4j para pruebas de integración/e2e, e integración con Codecov.

---

## 3. Brechas críticas hacia una librería “completa”

### 3.1 Tests fuera del control de versiones (hallazgo grave)

En [`.gitignore`](.gitignore) figura la entrada `tests/`, de modo que el directorio de pruebas **no se versiona** en Git. En un clon limpio del repositorio, las pruebas que el mantenedor puede tener en local **no están garantizadas** para colaboradores, revisores ni CI remoto.

**Implicación:** La reproducibilidad del estándar de calidad y la confianza en el pipeline de integración continua quedan comprometidas si el contenido real de `tests/` no coincide con lo que el repositorio público puede ejecutar. Para una librería madura, lo esperable es que la suite ejecutable en CI esté **en el mismo commit** que el código que valida.

### 3.2 Desalineación del job de lint con el árbol del código

El workflow de lint ejecuta herramientas sobre `src/` y `tests/` (por ejemplo flake8, black, isort en [`.github/workflows/ci.yml`](.github/workflows/ci.yml)). El paquete instalable vive bajo `ungraph/`, no bajo `src/`. Si `src/` no existe en el repo, esos pasos pueden no analizar el código real o fallar por rutas incorrectas.

**Implicación:** El “candado” de estilo y análisis estático puede no estar aplicándose al código que realmente se publica, o el job puede ser frágil según el entorno.

### 3.3 Madurez declarada y expectativas de estabilidad

- Clasificador **Alpha** y mensajes en README sobre posibles cambios de API: adecuado para 0.x, pero incompatible con la expectativa de una “versión completa” en sentido **semver estable** sin política explícita de deprecación.
- La inferencia híbrida (`hybrid`) está documentada como no implementada en [`ungraph/application/dependencies.py`](ungraph/application/dependencies.py) (plan referido a versiones futuras). Una narrativa ETI “completa” en producto exigiría definir qué modos son soportados de forma estable y bajo qué extras.

### 3.4 Inferencia y componentes experimentales

El CHANGELOG y el código enfatizan el carácter **experimental** de partes del pipeline de inferencia (p. ej. vía LLM en [`ungraph/infrastructure/services/llm_inference_service.py`](ungraph/infrastructure/services/llm_inference_service.py)). Eso no invalida el núcleo Extract–Transform + persistencia + búsqueda, pero sí diferencia una **librería de extracción y recuperación** de una **plataforma de inferencia lista para producción** sin más trabajo.

### 3.5 Tipado para consumidores (PEP 561)

No se observa un marcador `py.typed` empaquetado en el árbol típico del paquete. Para equipos que consumen la librería con mypy/pyright, la ausencia del marcador y de una estrategia documentada de tipos reduce la sensación de “producto terminado” en el ecosistema Python moderno.

### 3.6 Deuda visible en el código

Ejemplos puntuales (no exhaustivos):

- En [`ungraph/__init__.py`](ungraph/__init__.py), `suggest_chunking_strategy` admite `evaluate_all` pero el comentario indica que una implementación completa de alternativas aún puede ampliarse.
- En [`ungraph/utils/graph_operations.py`](ungraph/utils/graph_operations.py) persisten comentarios de diseño/TODO alrededor de integración con flujos tipo Docling y patrones dinámicos.

Estos puntos son coherentes con un proyecto activo, pero refuerzan que el valor “completo” hoy está más del lado **ET + grafo + búsqueda** que de **inferencia y patrones avanzados universalmente cerrados**.

---

## 4. Criterios sugeridos para declarar “1.0” o “estable”

Sin pretender ser la única lista posible, una librería de este tipo suele necesitar:

1. **Tests versionados** en el repositorio, ejecutados en CI en cada cambio relevante, con política clara de qué requiere Neo4j (marcadores `integration` / `e2e` ya previstos en [`pytest.ini`](pytest.ini)).
2. **Jobs de CI alineados** con las rutas reales del código (`ungraph/`, `tests/`).
3. **Superficie pública explícita:** `__all__`, guía de qué es estable vs experimental, y deprecaciones con ciclo de aviso.
4. **Changelog único y versionado** (convención Keep a Changelog o similar) además de notas por versión puntuales.
5. **Compatibilidad documentada:** versiones mínimas de Neo4j, Python soportados, y comportamiento cuando faltan extras (`gds`, `infer`, etc.).
6. **Señales de tipado:** `py.typed` y/o stubs, según la ambición del proyecto.
7. **Criterios de inferencia:** definir qué modos son soportados en GA y cuáles permanecen en “labs” o extras.

---

## 5. Conclusión

Ungraph **ya funciona como librería instalable** con un núcleo claro (configuración, ingesta, embeddings, Neo4j, búsqueda y patrones opcionales) y una base de documentación sólida. Para acercarse a una **versión “completa”** en el sentido fuerte de **producto de librería** (confianza reproducible, contrato público y señales de madurez), las prioridades más urgentes son **integral el sistema de pruebas en el repositorio**, **alinear el análisis estático con el layout real del código** y **acotar con precisión qué partes del ETI son estables frente a experimentales**, complementado con política de versionado y tipado para integradores.

---

*Documento generado como entrega puntual del análisis planificado; no modifica código ni configuración del proyecto.*
