# Extracción — familias de adquisición de evidencia

**Idioma:** español. Archivo canónico compartido (sin prefijo `sp-`).

Audiencia: research / developer. Espina: [`eti-spine.md`](eti-spine.md).

## Motivation

Llamar “extracción” a un único parse aplana diferencias metodológicas que cambian *qué cuenta como evidencia*. Un loader de Markdown, un extractor de tablas HTML, un NER sobre chunks y un modelo multimodal sobre PDF no son el mismo acto epistémico: difieren en señal de entrada, supuestos de ruido, granularidad y coste de error.

En minería de conocimiento, Extract responde: **¿qué unidades de evidencia salen de la fuente antes de featurizar y antes de proponer creencias?** Confundir Extract con Inference (IE completo) oculta si el fallo es de adquisición o de proposición de hechos.

## Theory

### Familias metodológicamente distintas

Taxonomía viva (no exhaustiva). Cada familia se distingue por *señal*, *unidad emitida* y *modo de fallo*:

| Familia | Señal / supuesto | Unidad típica | Linaje |
|---------|------------------|---------------|--------|
| **Loaders / I/O de documento** | Bytes → texto o árbol de documento | Documento, páginas, bloques | Pipelines IE Neo4j; ETL “Extract” clásico |
| **Estructura / layout** | DOM, tablas, secciones, posiciones | Celdas, captions, regiones | Fonduer multimodal KBC (I03, E17) |
| **Segmentación lingüística ligera** | Oraciones, tokens, spans sin tipar como entidades de dominio | Spans, oraciones | Preproceso hacia IE |
| **IE superficial (menciones)** | Texto tipado como entidades/menciones *antes* del slot Infer formal | Menciones candidatas | NELL/IE clásico — a menudo solapa con Inference; en Ungraph el slot Infer es el contrato medible |
| **Multimodal / visión** | Imagen + texto alineado | Regiones + OCR/caption | Fonduer; trayectoria vision embeddings (I03) |
| **Ingesta continua / never-ending** | Stream de fuentes con re-extracción | Evidencia versionada en el tiempo | NELL (I01, E18) |

**Regla de distinción:** dos extractores son *sistemáticamente diferentes* si (a) cambian la distribución de unidades de evidencia a igual corpus, y (b) eso puede alterar Y aguas abajo (Transform o Infer) bajo protocolo controlado — no solo el formato de archivo.

Extract en el whitepaper: *load and surface signals from sources* (docs, HTML, rich layouts, optional multimodal). No incluye por sí solo la calibración de creencias (eso es Inference + depuración).

### is vs will be

| | |
|--|--|
| **is** | Ingesta de documentos (p. ej. Markdown/PDF/Word según loaders del paquete); texto usable para chunking; provenance parcial hacia chunks; en la práctica, gran parte de “IE tipado” vive en el **slot Infer** (`spacy`, `lexical_pattern`, LLM) con `extraction_method` |
| **will be** | Extract multimodal layout-aware (Fonduer-like); visión; never-ending ingest con re-adquisición; separación más nítida entre adquisición de evidencia y proposición de facts |

## In Ungraph

- Extract alimenta **Transform** (chunks, embeddings, topología File–Page–Chunk). Lo tipado como Entity/Relation/Fact se mide hoy sobre el **slot Infer** — ver [`inference-slot.md`](inference-slot.md) y [`inference.md`](inference.md).
- Scorecard: bloque **E** (`chunking_quality_score`, `n_chunks`) refleja calidad de unidades tras adquisición+segmentación; no confundir con recall de entidades (bloque T/I).
- Patrones de grafo: consumidores de unidades ya adquiridas ([`sp-graph-patterns.md`](sp-graph-patterns.md)). Pasos de ingesta: [`../guides/sp-ingestion.md`](../guides/sp-ingestion.md) (no duplicar aquí).
- Programa experimental: [`../experiment/PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md), [`../experiment/BENCHMARK_ETI_DOMAINS.md`](../experiment/BENCHMARK_ETI_DOMAINS.md).

No afirmar en docs que Extract “ya depura” o que multimodal está en producción si no está medido en `main`.

## Open claims (falseables)

### Claim H_E_family_layout

- **Enunciado:** Un Extract layout-aware (tablas/secciones) cambia la distribución de evidencia respecto a texto plano y mejora Y de hechos anclados en corpus con estructura rica, a igual Transform e Infer.
- **Predicción observable:** En un fixture con tablas/HTML, `entity_recall` / `evidence_coverage` (o métrica de span gold de celdas) sube frente a loader texto-plano, con Infer y chunking fijos.
- **Protocolo mínimo:** Corpus versionado con gold de celdas/secciones; dos loaders; wipe; misma recipe Capa 0 salvo Extract. Oleada cuando el dominio lo exija: [`PLAN_MAESTRO.md`](../experiment/PLAN_MAESTRO.md) / segundo dominio en benchmark.
- **Falsación:** Si no hay diferencia significativa en unidades gold ni en Y ancladas, el layout Extract no se justifica en ese dominio (acotar).
- **Reproducibilidad:** Fixture + `ExperimentRun` + scorecard; factor `extract_family` en DoE.

### Claim H_E_vs_I_boundary

- **Enunciado:** Reportar `extraction_method` en el artefacto Infer permite atribuir errores a familia de proposición sin culpar al loader.
- **Predicción observable:** Swap solo `inference∈{ner,pattern}` a igual corpus/Transform mueve recall de grafo; swap solo loader (si no cambia texto efectivo) no.
- **Protocolo mínimo:** Oleada-3 familias Infer sobre `capa0_artifact.json`; ver [`inference-slot.md`](inference-slot.md).
- **Falsación:** Si `extraction_method` no correlaciona con diferencias de Y entre familias, la covariable no sirve para diagnóstico.
- **Reproducibilidad:** Reports de family-wave; filas DoE con `inference` etiquetado.
