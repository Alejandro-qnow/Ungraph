"""`ungraph ingest`: archivo local, URL o carpeta (paralelo + tqdm)."""

from __future__ import annotations

import logging
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import typer

from ungraph.application.dependencies import (
    create_bulk_ingest_documents_use_case,
    create_ingest_document_use_case,
)
from ungraph.cli.report_link import echo_eti_report_link
from ungraph.core.configuration import configure, get_settings

logger = logging.getLogger(__name__)

_DOC_SUFFIXES = frozenset(
    {
        ".md",
        ".markdown",
        ".txt",
        ".html",
        ".htm",
        ".pdf",
        ".doc",
        ".docx",
    }
)


def _collect_folder_paths(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise typer.BadParameter(f"No es una carpeta: {folder}")
    paths: list[Path] = []
    for p in sorted(folder.rglob("*")):
        if p.is_file() and p.suffix.lower() in _DOC_SUFFIXES:
            paths.append(p)
    return paths


def _download_url_to_temp_html(url: str) -> Path:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "UngraphCLI/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as ex:
        raise typer.BadParameter(f"No se pudo descargar la URL: {ex}") from ex
    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
    try:
        tmp.write(raw)
        tmp.flush()
        return Path(tmp.name)
    finally:
        tmp.close()


def ingest(
    ctx: typer.Context,
    database: Optional[str] = typer.Option(
        None,
        "--database",
        "-d",
        help="Sobrescribe la base Neo4j para esta ingesta.",
    ),
    path: Optional[str] = typer.Option(
        None,
        "--path",
        help="Ruta a archivo local o URL http(s).",
    ),
    folder: Optional[Path] = typer.Option(
        None,
        "--folder",
        help="Carpeta: ingesta en paralelo (barra tqdm).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    chunk_size: int = typer.Option(1000, help="Tamaño de chunk (archivo único / bulk)."),
    chunk_overlap: int = typer.Option(200, help="Solapamiento entre chunks."),
    clean_text: bool = typer.Option(True, help="Limpiar texto antes de chunking."),
    uid: Optional[str] = typer.Option(None, "--uid", help="UID documento (solo --path archivo)."),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        help="Carpeta donde escribir el bundle HTML del reporte ETI al terminar (--path).",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    report_sample_limit: int = typer.Option(
        400,
        "--report-sample-limit",
        help="Límite de nodos ancla para la muestra NVL del reporte.",
    ),
    report_open_browser: bool = typer.Option(
        False,
        "--report-open-browser",
        help="Tras --report, abrir index.html en el navegador.",
    ),
) -> None:
    if (path is None) == (folder is None):
        if path is None and folder is None:
            typer.echo(ctx.get_help())
            raise typer.Exit(0)
        typer.secho("Indica exactamente uno de: --path o --folder.", fg=typer.colors.RED, err=True)
        raise typer.Exit(2)

    if database:
        configure(neo4j_database=database)

    settings = get_settings()

    if folder is not None:
        paths = _collect_folder_paths(folder)
        if not paths:
            typer.secho("No se encontraron documentos compatibles en la carpeta.", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
        typer.echo(
            f"Archivos a procesar: {len(paths)} (workers={settings.ingest_max_workers}; "
            f"duración aproximada depende del tamaño y del modelo de embeddings)."
        )
        bulk = create_bulk_ingest_documents_use_case(settings=settings)
        try:
            outcomes = bulk.execute(
                paths,
                use_tqdm_progress=True,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                clean_text=clean_text,
            )
        finally:
            bulk.close()
        ok = sum(1 for _p, st, _d in outcomes if st == "ok")
        skipped = sum(1 for _p, st, _d in outcomes if st == "skipped")
        err = sum(1 for _p, st, _d in outcomes if st == "error")
        typer.secho(
            f"Listo: ok={ok} skipped={skipped} error={err}",
            fg=typer.colors.GREEN if err == 0 else typer.colors.YELLOW,
        )
        if err:
            raise typer.Exit(1)
        return

    assert path is not None
    tmp_download: Optional[Path] = None
    try:
        if path.startswith("http://") or path.startswith("https://"):
            typer.echo("Descargando URL…")
            tmp_download = _download_url_to_temp_html(path)
            local_path = tmp_download
            source_url = path
        else:
            local_path = Path(path)
            if not local_path.is_file():
                raise typer.BadParameter(f"No existe el archivo: {local_path}")
            source_url = None

        uc = create_ingest_document_use_case(
            settings=settings,
            database=settings.neo4j_database,
        )
        try:
            kw: dict = {
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "clean_text": clean_text,
                "source_document_uid": uid,
            }
            if report is not None:
                kw["report_output_dir"] = report
                kw["report_sample_limit"] = report_sample_limit
            if source_url:
                kw["source_url"] = source_url
            chunks = uc.execute(local_path, **kw)
        finally:
            if hasattr(uc.chunk_repository, "close"):
                uc.chunk_repository.close()
            if hasattr(uc.index_service, "close"):
                uc.index_service.close()
        typer.secho(f"Ingesta completada: {len(chunks)} chunks.", fg=typer.colors.GREEN)
        if report is not None:
            echo_eti_report_link(
                report / "index.html",
                open_browser=report_open_browser,
            )
    finally:
        if tmp_download is not None and tmp_download.exists():
            try:
                tmp_download.unlink(missing_ok=True)
            except OSError as ex:
                logger.debug("temp download cleanup: %s", ex)
