"""`ungraph report`: generar bundle HTML del reporte ETI.

La opción global ``--no-banner`` va **antes** del subcomando, p. ej.
``ungraph --no-banner report -o ./salida``. No usar ``ungraph report --no-banner``
(Typer no la reconoce ahí). Si el navegador muestra la página en blanco al abrir un
``file://`` en Windows, sirve la carpeta con ``python -m http.server 8765`` y entra en
http://127.0.0.1:8765/
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ungraph.cli.report_link import echo_eti_report_link
from ungraph.core.configuration import configure, get_settings
from ungraph.domain.value_objects.eti_report import EtiRunCounters
from ungraph.utils.eti_report_bundler import (
    build_run_meta,
    collect_and_build_payload,
    write_eti_report_bundle,
)


def report(
    database: Optional[str] = typer.Option(
        None,
        "--database",
        "-d",
        help="Sobrescribe la base Neo4j para introspección del reporte.",
    ),
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help=(
            "Carpeta de salida (copia index.html + assets e inyecta datos). "
            "Si ya existen inference_benchmark.json o graphrag_smoke.json aquí, se fusionan al payload del HTML."
        ),
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    document_uid: Optional[str] = typer.Option(
        None,
        "--document-uid",
        help="Opcional: acotar muestra NVL a Chunk.source_document_uid.",
    ),
    sample_limit: int = typer.Option(
        400,
        "--sample-limit",
        help="Límite de nodos ancla para la muestra de instancia.",
    ),
    open_browser: bool = typer.Option(
        False,
        "--open-browser",
        help="Abrir el index.html en el navegador predeterminado tras generarlo.",
    ),
    merge_supplements: bool = typer.Option(
        True,
        "--merge-supplements/--no-merge-supplements",
        help=(
            "Fusionar inference_benchmark.json y graphrag_smoke.json presentes en la carpeta -o "
            "(evita datos obsoletos con --no-merge-supplements)."
        ),
    ),
) -> None:
    if database:
        configure(neo4j_database=database)
    settings = get_settings()
    run_meta = build_run_meta(
        settings=settings,
        pattern_name=None,
        file_path=None,
        source_document_uid=document_uid,
        inference_mode=settings.inference_mode,
        embedding_encoder_summary=None,
    )
    counters = EtiRunCounters()
    payload = collect_and_build_payload(
        settings=settings,
        run_meta=run_meta,
        run_counters=counters,
        document_uid=document_uid,
        sample_node_limit=sample_limit,
    )
    path = write_eti_report_bundle(payload, output, merge_supplements=merge_supplements)
    typer.secho(f"Reporte generado en: {path.parent}", fg=typer.colors.GREEN)
    echo_eti_report_link(path, open_browser=open_browser)
