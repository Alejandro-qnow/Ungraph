"""
Ensambla el payload del reporte ETI y escribe el bundle estático (HTML + assets).
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ungraph.core.configuration import Settings
from ungraph.domain.value_objects.eti_report import (
    EtiReportPayload,
    EtiRunCounters,
    EtiRunMeta,
)
from ungraph.infrastructure.services.neo4j_graph_report_collector import (
    Neo4jGraphReportCollector,
    neo4j_uri_host,
)

logger = logging.getLogger(__name__)


def resolve_report_static_dir() -> Path:
    """
    Orden: UNGRAPH_REPORT_STATIC_DIR, ungraph/report_static/, repo/report-ui/dist/.
    """
    env = os.environ.get("UNGRAPH_REPORT_STATIC_DIR")
    if env:
        return Path(env).expanduser().resolve()
    pkg_root = Path(__file__).resolve().parent.parent
    candidate = pkg_root / "report_static"
    if (candidate / "index.html").is_file():
        return candidate
    repo_root = pkg_root.parent
    dist = repo_root / "report-ui" / "dist"
    if (dist / "index.html").is_file():
        return dist
    return candidate


def build_run_meta(
    *,
    settings: Settings,
    pattern_name: Optional[str],
    file_path: Optional[Path],
    source_document_uid: Optional[str],
    inference_mode: Optional[str],
    embedding_encoder_summary: Optional[str],
) -> EtiRunMeta:
    from ungraph import __version__ as uv

    fp = str(file_path.resolve()) if file_path else None
    return EtiRunMeta(
        ungraph_version=uv,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        neo4j_database=settings.neo4j_database,
        neo4j_uri_host=neo4j_uri_host(settings.neo4j_uri),
        pattern_name=pattern_name,
        document_filename=file_path.name if file_path else None,
        document_path=fp,
        source_document_uid=source_document_uid,
        embedding_encoder_summary=embedding_encoder_summary,
        inference_mode=inference_mode,
    )


def collect_and_build_payload(
    *,
    settings: Optional[Settings] = None,
    run_meta: EtiRunMeta,
    run_counters: EtiRunCounters,
    document_uid: Optional[str],
    sample_node_limit: int,
    collector: Optional[Neo4jGraphReportCollector] = None,
) -> EtiReportPayload:
    if settings is None:
        from ungraph.core.configuration import get_settings

        settings = get_settings()
    own = collector is None
    if collector is None:
        collector = Neo4jGraphReportCollector(database=settings.neo4j_database)
    try:
        db = collector.collect_db_snapshot(
            document_uid=document_uid,
            sample_node_limit=sample_node_limit,
        )
    finally:
        if own:
            collector.close()
    return EtiReportPayload(
        run_meta=run_meta,
        run_counters=run_counters,
        **db,
    )


def load_report_supplement_payloads(output_dir: Path) -> dict[str, Any]:
    """
    Si existen JSON auxiliares en la carpeta del reporte, se fusionan al payload.

    - ``inference_benchmark.json``: benchmark NER vs LLM (p. ej. ``run_reference_pipeline``).
    - ``graphrag_smoke.json``: resultados de smoke textual tipo GraphRAG.
    """
    out: dict[str, Any] = {}
    bench = output_dir / "inference_benchmark.json"
    if bench.is_file():
        try:
            out["inference_benchmark"] = json.loads(bench.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.warning("No se pudo leer inference_benchmark.json: %s", exc)
    smoke = output_dir / "graphrag_smoke.json"
    if smoke.is_file():
        try:
            parsed = json.loads(smoke.read_text(encoding="utf-8"))
            if isinstance(parsed, list):
                out["graphrag_smoke"] = parsed
            else:
                logger.warning("graphrag_smoke.json debe ser una lista JSON; se omite.")
        except json.JSONDecodeError as exc:
            logger.warning("No se pudo leer graphrag_smoke.json: %s", exc)
    return out


def merge_supplements_into_payload(
    payload: EtiReportPayload,
    output_dir: Path,
    *,
    use_supplements: bool = True,
) -> EtiReportPayload:
    if not use_supplements:
        return payload
    extra = load_report_supplement_payloads(output_dir)
    if not extra:
        return payload
    return payload.model_copy(update=extra)


def write_eti_report_bundle(
    payload: EtiReportPayload,
    output_dir: Path,
    *,
    static_dir: Optional[Path] = None,
    merge_supplements: bool = True,
) -> Path:
    """
    Copia assets del build de report-ui y escribe index.html con datos inyectados.
    Devuelve la ruta al index.html generado.
    """
    static = static_dir or resolve_report_static_dir()
    index_src = static / "index.html"
    if not index_src.is_file():
        raise FileNotFoundError(
            f"No se encontró el build del reporte en {static}. "
            "Ejecuta `npm ci && npm run build` en report-ui/ o define UNGRAPH_REPORT_STATIC_DIR."
        )
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = merge_supplements_into_payload(
        payload, output_dir, use_supplements=merge_supplements
    )
    shutil.copytree(static, output_dir, dirs_exist_ok=True)
    index_out = output_dir / "index.html"
    html = index_out.read_text(encoding="utf-8")
    data = payload.model_dump(mode="json")
    json_inner = json.dumps(data, ensure_ascii=False)
    injection = (
        '<script type="application/json" id="__ungraph_eti_json__">'
        f"{json_inner}"
        "</script>\n"
        "<script>"
        "window.__UNGRAPH_ETI_REPORT__=JSON.parse("
        "document.getElementById('__ungraph_eti_json__').textContent);"
        "</script>\n"
    )
    lowered = html.lower()
    mod_idx = lowered.find('<script type="module"')
    if mod_idx != -1:
        html = html[:mod_idx] + injection + html[mod_idx:]
    elif "</head>" in lowered:
        idx = lowered.find("</head>")
        html = html[:idx] + injection + html[idx:]
    else:
        html = injection + html
    index_out.write_text(html, encoding="utf-8")
    logger.info("Reporte ETI escrito en %s", index_out)
    return index_out


def emit_eti_report_after_ingest(
    *,
    settings: Optional[Settings] = None,
    output_dir: Path,
    file_path: Path,
    source_document_uid: str,
    pattern_name: str,
    chunks: list[Any],
    facts_count: int,
    relations_count: int,
    inference_mode: Optional[str],
    sample_node_limit: int = 400,
    static_dir: Optional[Path] = None,
) -> Path:
    if settings is None:
        from ungraph.core.configuration import get_settings

        settings = get_settings()
    emb = None
    if chunks:
        emb = getattr(chunks[0], "embedding_encoder_info", None)
        if emb is not None and not isinstance(emb, str):
            emb = json.dumps(emb, ensure_ascii=False, default=str)
    run_meta = build_run_meta(
        settings=settings,
        pattern_name=pattern_name,
        file_path=file_path,
        source_document_uid=source_document_uid,
        inference_mode=inference_mode,
        embedding_encoder_summary=emb,
    )
    counters = EtiRunCounters(
        chunks_created=len(chunks),
        facts_inferred=facts_count,
        relations_inferred=relations_count,
    )
    payload = collect_and_build_payload(
        settings=settings,
        run_meta=run_meta,
        run_counters=counters,
        document_uid=source_document_uid,
        sample_node_limit=sample_node_limit,
    )
    return write_eti_report_bundle(payload, output_dir, static_dir=static_dir)
