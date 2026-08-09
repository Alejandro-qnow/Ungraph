"""
Fachadas de la fase Inference/Reasoning.

Funciones puras de conveniencia que arman el composition root, ejecutan un caso de
uso/servicio existente y devuelven un dict serializable. Lanzan excepciones en fallo
(el llamador —MCP/CLI— decide cómo reportarlas).
"""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

from ungraph.core.configuration import get_settings

logger = logging.getLogger(__name__)


def _resolve_database(database: Optional[str]) -> str:
    if database:
        return database
    return get_settings().neo4j_database or "neo4j"


# ---------------------------------------------------------------- determinista
def graph_stats(database: Optional[str] = None) -> Dict[str, Any]:
    """Estadísticas estructurales del grafo (read-only): conteos por label y por
    tipo de relación. Base de graph-analytics para el razonamiento.
    """
    from ungraph.evaluation.graph_structural_stats import collect_structural_graph_stats
    from ungraph.utils.graph_operations import graph_session

    db = _resolve_database(database)
    driver = graph_session()
    try:
        stats = collect_structural_graph_stats(driver, database=db)
    finally:
        try:
            driver.close()
        except Exception:
            pass
    return stats.to_json_obj()


def validate_topology(
    database: Optional[str] = None,
    *,
    source_document_uid: Optional[str] = None,
    min_chunks: int = 1,
) -> Dict[str, Any]:
    """Valida invariantes estructurales (NEXT_CHUNK con alcance por documento, y
    opcionalmente la cadena de un documento). Regla semántica determinista.
    """
    from ungraph.utils.graph_operations import graph_session
    from ungraph.utils.graph_topology_validate import run_file_page_chunk_checks

    db = _resolve_database(database)
    driver = graph_session()
    try:
        report = run_file_page_chunk_checks(
            driver, db, source_document_uid=source_document_uid, min_chunks=min_chunks
        )
    finally:
        try:
            driver.close()
        except Exception:
            pass
    return {"ok": report.ok, "issues": list(report.issues)}


def consolidate_entities(
    database: Optional[str] = None,
    *,
    resolve_punctuation: bool = True,
) -> Dict[str, Any]:
    """Fusiona nodos :Entity duplicados (case-insensitive y, opcionalmente, sin
    puntuación). Consolidación determinista del subgrafo de entidades (I19).

    Returns:
        {'merged_case_insensitive': int, 'merged_punctuation': int}
    """
    from ungraph.application.dependencies import (
        create_entity_graph_maintenance_service,
    )

    db = _resolve_database(database)
    service = create_entity_graph_maintenance_service(database=db)
    merged_ci = service.consolidate_entities_case_insensitive()
    merged_punct = 0
    if resolve_punctuation:
        merged_punct = service.resolve_entities_strip_punctuation()
    result = {
        "merged_case_insensitive": int(merged_ci),
        "merged_punctuation": int(merged_punct),
    }
    if hasattr(service, "close"):
        try:
            service.close()  # type: ignore[misc]
        except Exception:
            pass
    return result


# ------------------------------------------------------------- no-determinista
def mine_knowledge(
    database: Optional[str] = None,
    *,
    inference_language: str = "en",
    use_tqdm: bool = False,
) -> Dict[str, Any]:
    """Re-ejecuta inferencia (facts/relations) sobre chunks aún sin :Fact derivados.

    Requiere un InferenceService disponible (spaCy con ``ungraph[infer]`` o LLM con
    ``OPENAI_API_KEY`` / ``UNGRAPH_INFERENCE_MODE=llm``); si no, lanza RuntimeError.

    Returns:
        Conteos del minado (chunks pendientes/inferidos, facts/relaciones, errores).
    """
    from ungraph.application.dependencies import create_knowledge_mining_use_case

    db = _resolve_database(database)
    settings = get_settings()
    use_case = create_knowledge_mining_use_case(
        settings=settings, database=db, inference_language=inference_language
    )
    try:
        result = use_case.execute(use_tqdm=use_tqdm)
    finally:
        use_case.close()
    return asdict(result)


def infer_over_document(
    document_path: str,
    database: Optional[str] = None,
    *,
    inference_language: str = "en",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> Dict[str, Any]:
    """Ingesta un documento ejecutando la fase Infer del patrón ETI.

    El motor de inferencia lo determina la configuración (``inference_mode``:
    ner/llm). Devuelve conteo de chunks e indica el modo usado; para ver los facts
    resultantes, usa ``graph_stats`` o ``mine_knowledge``.
    """
    from ungraph.application.dependencies import create_ingest_document_use_case

    path = Path(document_path)
    if not path.is_file():
        raise FileNotFoundError(f"Documento no encontrado: {document_path}")

    db = _resolve_database(database)
    settings = get_settings()
    use_case = create_ingest_document_use_case(
        settings=settings, database=db, inference_language=inference_language
    )
    chunks = use_case.execute(
        path, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    has_inference = use_case.inference_service is not None
    return {
        "document_path": document_path,
        "chunks_created": len(chunks),
        "inference_mode": settings.inference_mode,
        "inference_active": has_inference,
    }


def ingest_tabular(
    file_path: str,
    database: Optional[str] = None,
    *,
    apply: bool = False,
    mapping: Optional[list] = None,
    use_llm: bool = True,
    batch_size: int = 1000,
) -> Dict[str, Any]:
    """Ingesta guiada por esquema (SGI) de una fuente tabular (CSV/XLSX).

    Corre en paralelo al ETI de texto: la estructura de una tabla ya es explícita,
    así que en vez de chunkear+extraer con NLP se infiere el mapeo columna→rol y se
    materializan las filas como nodos/relaciones. Flujo de dos pasos:

    - ``apply=False`` (default, dry-run): infiere y devuelve la propuesta de esquema
      SIN escribir en el grafo. El llamador la revisa/edita y vuelve a llamar.
    - ``apply=True``: persiste al grafo. Si se pasa ``mapping`` (propuestas
      confirmadas/editadas, como lista de dicts al estilo ``TabularSchemaProposal``),
      se usan en lugar de re-inferir.

    La desambiguación LLM se activa con ``use_llm`` solo si hay ``OPENAI_API_KEY``;
    de lo contrario, inferencia heurística pura (determinista).

    Returns:
        ``{'file_path', 'persisted': bool, 'proposals': [dict...], 'stats': [dict...]}``.
        En dry-run ``persisted`` es False y ``stats`` está vacío.
    """
    from ungraph.application.dependencies import create_ingest_tabular_use_case
    from ungraph.domain.value_objects.tabular_schema import TabularSchemaProposal

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Archivo tabular no encontrado: {file_path}")

    db = _resolve_database(database)
    settings = get_settings()
    use_case = create_ingest_tabular_use_case(
        settings=settings, database=db, use_llm_disambiguation=use_llm
    )

    confirmed: Optional[list] = None
    if mapping:
        confirmed = [TabularSchemaProposal.from_dict(m) for m in mapping]

    try:
        result = use_case.execute(
            path, dry_run=not apply, mappings=confirmed, batch_size=batch_size
        )
    finally:
        repo = getattr(use_case, "tabular_repository", None)
        if repo is not None and hasattr(repo, "close"):
            try:
                repo.close()
            except Exception:
                pass

    return {
        "file_path": file_path,
        "persisted": result.persisted,
        "proposals": [p.to_dict() for p in result.proposals],
        "stats": list(result.stats),
    }
