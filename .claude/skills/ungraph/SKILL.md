---
name: ungraph
description: Punto de entrada maestro para la cocreación de Ungraph. Enruta automáticamente al skill especializado según la necesidad del prompt. Úsalo cuando no sepas qué skill invocar o cuando la tarea cruce varias áreas.
allowed-tools: Read Grep Glob
---

Eres el coordinador principal de desarrollo de Ungraph. Tu primera tarea es analizar el prompt del usuario y determinar qué skill(s) aplicar.

## Mapa de enrutamiento

Evalúa el intent del prompt contra esta tabla. Puede activarse más de un skill si la tarea es transversal.

| Si el prompt menciona o implica… | Skill a aplicar |
|----------------------------------|-----------------|
| Cypher, query, Neo4j, índice, MERGE, MATCH, rendimiento de grafo | **cypher-craft** |
| Test, prueba, cobertura, pytest, fixture, mock, integración, e2e | **ungraph-test** |
| Curación ETI, golden file, matriz de pruebas por fase, regresión Cypher, calidad operativa | **eti-operation-curation** |
| MVP ETI, readiness, tres capas domain/application/infrastructure, checklist de salida | **eti-mvp-operativa** |
| H_I, DoE, doekit, scorecard, ExperimentRun, oleada, claim científico, ET vs ETI, Y discriminativas, checklist plan maestro, Complexometrum | **eti-experiment-science** |
| Upgrade LangChain, LangGraph, langchain-neo4j, lockfile, humo imports, stack SDK | **ungraph-langstack-ops** |
| Búsqueda, GraphRAG, patrón de recuperación, vector search, hybrid, ranking | **graphrag-pattern** |
| Release, versión, PyPI, CHANGELOG, semver, API pública, deprecar, `py.typed` | **ungraph-release** |
| Schema, modelo de grafo, nodo, relación, propiedad, constraint, índice de diseño | **kg-schema** |
| Pipeline, ETI, chunking, embedding, extracción, entidades, LLM, spaCy, ingesta | **eti-pipeline** |

## Protocolo de enrutamiento

1. **Lee el prompt completo** de `$ARGUMENTS`.
2. **Identifica el skill dominante** (el que cubre el núcleo de la tarea).
3. **Identifica skills secundarios** si la tarea es transversal (ej. nuevo patrón GraphRAG que también requiere un test).
4. **Anuncia el enrutamiento** en una línea: `→ Aplicando: <skill1> [+ <skill2>]`
5. **Ejecuta el skill dominante primero**, luego los secundarios si aplica.

## Respuesta cuando el intent es ambiguo

Si el prompt no encaja claramente en ningún skill, responde con:
- Resumen de lo que entendiste
- Dos o tres opciones de skill con una pregunta concreta para aclarar
- No intentes adivinar ni hacer todo a la vez

## Contexto siempre disponible

Proyecto: **Ungraph 0.1.5** — framework Python para grafos de conocimiento sobre Neo4j.
Patrón central: **Extract → Transform → Inference (ETI)** + recuperación **GraphRAG**.
Arquitectura: `domain / application / infrastructure` (Clean Architecture).
Brechas prioritarias (ver checklist en `docs/experiment/PLAN_MAESTRO.md`): runner online H_I · Y Neo4j/top-k · tests ETI en CI · doc I/O Infer.
Subagentes: **ungraph-dev-skills** (orquestación), **ungraph-eti-science** (rigor experimental / oleada-2).

## Ejemplo de uso

```
/ungraph quiero agregar un patrón de búsqueda multi-hop entre entidades y necesito el test correspondiente
```
→ Aplicando: **graphrag-pattern** + **ungraph-test**

```
/ungraph la query de ingesta de chunks está haciendo full scan
```
→ Aplicando: **cypher-craft**

```
/ungraph subimos langchain-neo4j y el CI rompe imports
```
→ Aplicando: **ungraph-langstack-ops** + **ungraph-test**

```
/ungraph checklist para cerrar MVP de ingesta con spaCy y Neo4j
```
→ Aplicando: **eti-mvp-operativa** + **eti-operation-curation**

```
/ungraph cerrar H_I con Neo4j y spaCy / oleada-2 DoE
```
→ Aplicando: **eti-experiment-science** + **ungraph-test** (+ **graphrag-pattern** si toca top-k)
