"""`ungraph graph`: comprobaciones Neo4j sin subcomandos."""

from __future__ import annotations

from typing import Optional

import typer

from ungraph.core.configuration import configure, get_settings
from ungraph.infrastructure.services.neo4j_index_service import Neo4jIndexService
from ungraph.utils.graph_operations import graph_session
from ungraph.utils.graph_topology_validate import run_file_page_chunk_checks


def graph(
    ctx: typer.Context,
    database: Optional[str] = typer.Option(
        None,
        "--database",
        "-d",
        help="Sobrescribe UNGRAPH_NEO4J_DATABASE / NEO4J_DB solo para este comando.",
    ),
    ping: bool = typer.Option(False, "--ping", help="verify_connectivity + RETURN 1."),
    validate_topology: bool = typer.Option(
        False,
        "--validate-topology",
        help="Validar NEXT_CHUNK por source_document_uid (+ opcional --uid).",
    ),
    setup_indexes: bool = typer.Option(
        False,
        "--setup-indexes",
        help="Crear índices estándar (sin pasar por ungraph setup).",
    ),
    drop_indexes: bool = typer.Option(
        False,
        "--drop-indexes",
        help="Eliminar índices estándar conocidos por Ungraph.",
    ),
    uid: Optional[str] = typer.Option(
        None,
        "--uid",
        help="Documento concreto para --validate-topology.",
    ),
    min_chunks: int = typer.Option(1, "--min-chunks", help="Solo con --uid."),
) -> None:
    flags = (ping, validate_topology, setup_indexes, drop_indexes)
    if not any(flags):
        typer.echo(ctx.get_help())
        raise typer.Exit(0)

    if database:
        configure(neo4j_database=database)

    settings = get_settings()

    if setup_indexes:
        svc = Neo4jIndexService(database=settings.neo4j_database)
        try:
            svc.setup_all_indexes()
        finally:
            svc.close()
        typer.secho("Índices configurados.", fg=typer.colors.GREEN)

    if drop_indexes:
        svc = Neo4jIndexService(database=settings.neo4j_database)
        try:
            svc.drop_all_indexes()
        finally:
            svc.close()
        typer.secho("Índices eliminados.", fg=typer.colors.YELLOW)

    if ping:
        driver = graph_session()
        try:
            driver.verify_connectivity()
            with driver.session(database=settings.neo4j_database) as session:
                row = session.run("RETURN 1 AS ok").single()
                if not row or row.get("ok") != 1:
                    typer.secho("RETURN 1 inválido", fg=typer.colors.RED, err=True)
                    raise typer.Exit(code=1)
        finally:
            driver.close()
        typer.secho(
            f"OK: {settings.neo4j_uri} (database={settings.neo4j_database})",
            fg=typer.colors.GREEN,
        )

    if validate_topology:
        driver = graph_session()
        try:
            report = run_file_page_chunk_checks(
                driver,
                settings.neo4j_database,
                source_document_uid=uid,
                min_chunks=min_chunks,
            )
        finally:
            driver.close()
        if report.ok:
            typer.secho("Topología lexical OK.", fg=typer.colors.GREEN)
        else:
            for issue in report.issues:
                typer.secho(issue, fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
