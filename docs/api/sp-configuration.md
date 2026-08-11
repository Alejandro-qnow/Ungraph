# Configuración

Contrato de settings (`ungraph.core.configuration`).  
Audiencia: developer. Slot Infer (contexto): [`../concepts/inference-slot.md`](../concepts/inference-slot.md).

## Métodos

1. Variables de entorno / `.env` (prefijo `UNGRAPH_`; aliases Neo4j/OpenAI sin prefijo donde aplique).
2. `ungraph.configure(**kwargs)` (prioridad sobre env para los campos que pases).

## Variables frecuentes

| Variable | Descripción | Default / notas |
|----------|-------------|-----------------|
| `UNGRAPH_NEO4J_URI` | URI Bolt | sin default estricto; alias `NEO4J_URI` |
| `UNGRAPH_NEO4J_USER` | Usuario | `neo4j` (alias `NEO4J_USER`) |
| `UNGRAPH_NEO4J_PASSWORD` | Contraseña | requerido en práctica; alias `NEO4J_PASSWORD` |
| `UNGRAPH_NEO4J_DATABASE` | Base | `neo4j` (alias `NEO4J_DB` / `NEO4J_DATABASE`) |
| `UNGRAPH_EMBEDDING_MODEL` | Modelo embedding | `sentence-transformers/all-MiniLM-L6-v2` |
| `UNGRAPH_STORAGE_PROVIDER` | Store | `neo4j` |
| `UNGRAPH_INFERENCE_MODE` | Slot Infer | `ner` |
| `UNGRAPH_OPENAI_API_KEY` | LLM Infer | opcional; alias `OPENAI_API_KEY` |
| `UNGRAPH_OPENAI_MODEL` | Modelo chat | `gpt-4o-mini` |
| `UNGRAPH_OPENAI_BASE_URL` | Endpoint compatible | opcional |
| `UNGRAPH_INFERENCE_MODEL_BUDGET` | `economy` \| `balanced` \| `quality` | `balanced` |
| `UNGRAPH_INGEST_MAX_WORKERS` | Paralelismo bulk | `4` |

Hay más campos (ontología SPARQL, hints spaCy, modelos por paso de Infer, Ollama reservado). Fuente de verdad: clase `Settings` en `ungraph/core/configuration.py`.

### Ejemplo `.env`

```env
UNGRAPH_NEO4J_URI=bolt://localhost:7687
UNGRAPH_NEO4J_USER=neo4j
UNGRAPH_NEO4J_PASSWORD=mi_contraseña_segura
UNGRAPH_NEO4J_DATABASE=neo4j
UNGRAPH_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
UNGRAPH_INFERENCE_MODE=ner
```

### Shell

```bash
export UNGRAPH_NEO4J_URI="bolt://localhost:7687"
export UNGRAPH_NEO4J_USER="neo4j"
export UNGRAPH_NEO4J_PASSWORD="mi_contraseña"
export UNGRAPH_NEO4J_DATABASE="neo4j"
```

## Configuración programática

```python
import ungraph

ungraph.configure(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="mi_contraseña",
    neo4j_database="neo4j",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    inference_mode="ner",
)
```

```python
from ungraph.core.configuration import get_settings

s = get_settings()
print(s.neo4j_uri, s.neo4j_user, s.neo4j_database, s.embedding_model, s.inference_mode)
```

## Prioridad

1. Valores pasados a `ungraph.configure(...)` (y estado global de settings).
2. Variables de entorno / `.env` (`UNGRAPH_*`, con aliases documentados).
3. Defaults de `Settings`.

## `inference_mode` (`is`)

| Valor | Comportamiento en `main` |
|-------|---------------------------|
| `ner` | spaCy NER (default) |
| `pattern` | inferencia léxica simbólica |
| `llm` | extracción LLM vía OpenAI-compatible (`UNGRAPH_OPENAI_*` / `OPENAI_*`) |
| `hybrid` | **no implementado** — `NotImplementedError` |

Ollama (`UNGRAPH_OLLAMA_*`) está reservado; `inference_mode=llm` usa el cliente OpenAI-compatible hoy.

## Errores de configuración

```python
import ungraph

try:
    ungraph.ingest_document("doc.md")
except Exception as e:
    print(type(e).__name__, e)
```

Casos frecuentes:

| Síntoma | Acción |
|---------|--------|
| URI / password ausentes | `configure` o env |
| `AuthError` Neo4j | revisar URI/usuario/password |
| `NotImplementedError` con `hybrid` | usar `ner`, `pattern` o `llm` |
| Fallo LLM | clave/modelo/base_url; modo `ner` como fallback operativo |

```python
from ungraph.core.configuration import get_settings

s = get_settings()
print(s.neo4j_uri, s.neo4j_user)  # password no se imprime por diseño
```

## Multi-database

```python
import ungraph

chunks1 = ungraph.ingest_document("doc1.md", database="db1")
chunks2 = ungraph.ingest_document("doc2.md", database="db2")
```

## Referencias

- [API pública](sp-public-api.md)
- [Inicio rápido](../guides/sp-quickstart.md)
- [Slot Infer](../concepts/inference-slot.md)
