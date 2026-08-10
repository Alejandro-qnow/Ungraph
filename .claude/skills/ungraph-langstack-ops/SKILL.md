---
name: ungraph-langstack-ops
description: Opera y actualiza el stack LangChain, LangGraph y Neo4j alrededor de Ungraph: dependencias en pyproject, lockfile, humo de imports y límites de capa. Usar cuando subas versiones de LangChain, depures integraciones langchain-neo4j/experimental, o aclares si LangGraph pertenece al core o a la app consumidora.
---

# Operación LangChain / LangGraph / Neo4j para Ungraph

## Dónde vive cada cosa

| Tecnología | Rol en Ungraph | Ubicación en código |
|------------|----------------|---------------------|
| **Neo4j** | Persistencia de chunks, entidades, patrones | `ungraph/infrastructure/repositories/neo4j_*.py`, servicios Neo4j |
| **LangChain** | Loaders, text splitters, embeddings HF, `LLMGraphTransformer` | `langchain_*` imports solo bajo `ungraph/infrastructure/` (y composition root) |
| **LangGraph** | Dependencia declarada para orquestación **externa** al dominio; hoy el repo puede no importarla aún en Python | Consumidores: agentes, flujos stateful; no mezclar con entidades de dominio |

Si aparece `from langchain` o `neo4j` dentro de `ungraph/domain/`, es un defecto de arquitectura.

## Dependencias del proyecto (fuente de verdad)

Revisar y acordar bumps en:

- `pyproject.toml` — versiones de `langchain`, `langchain-community`, `langchain-neo4j`, `langchain-experimental`, `langchain-huggingface`, `langchain-text-splitters`, `langchain-docling`, `neo4j`, `langgraph`
- `uv.lock` — tras cambiar deps, regenerar lock en el flujo del equipo (`uv lock` / CI esperado)

## Humo post-upgrade (orden sugerido)

Ejecutar sin red cuando sea posible; con red solo donde haga falta (LLM).

1. **Imports**: arrancar Python y ejecutar imports de los módulos frágiles:
   - `ungraph.infrastructure.services.langchain_document_loader_service`
   - `ungraph.infrastructure.services.langchain_chunking_service`
   - `ungraph.infrastructure.services.huggingface_embedding_service`
   - `ungraph.infrastructure.services.llm_inference_service` (requiere experimental + LLM configurado)
2. **Dominio limpio**: `grep` o revisión de que `ungraph/domain/` no referencia LangChain/Neo4j.
3. **Tests**: `pytest -m unit` luego integración con Neo4j si aplica (ver **ungraph-test**).

## LangChain Neo4j (`langchain-neo4j`)

Útil para prototipos y herramientas alrededor del grafo; el núcleo de Ungraph persiste vía repositorios propios. Al combinar ambos, documentar qué capa es dueña del esquema para evitar MERGE duplicados.

## LangGraph: cuándo usarlo en un MVP

- **No requerido** para validar ETI end-to-end con casos de uso existentes.
- **Sí** cuando el MVP incluye agente (ReAct, pasos condicionales, persistencia de estado) que invoque ingesta/búsqueda como herramientas.

Patrón: nodos LangGraph llaman funciones que usan factories de `ungraph/application/dependencies.py` (composition root), no lógica nueva en `infrastructure` sin interfaz en dominio.

## Referencias de alineación

- Cambios rupturistas de LangChain: contrastar con documentación oficial actual ([LangChain Python docs](https://python.langchain.com/docs/)) antes de refactors grandes.
- Para Cypher y salud del grafo: skills **cypher-craft** y **kg-schema**.
