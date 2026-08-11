"""`ungraph setup`: inicialización Neo4j e índices; wipe del grafo."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ungraph.core.configuration import configure, get_settings, reload_dotenv_files, reset_configuration
from ungraph.infrastructure.services.neo4j_index_service import Neo4jIndexService


def setup(
    ctx: typer.Context,
    database: Optional[str] = typer.Option(
        None,
        "--database",
        "-d",
        help="Sobrescribe la base Neo4j para esta operación.",
    ),
    database_init: bool = typer.Option(
        False,
        "--database-init",
        help="Recargar .env; si faltan datos, pedirlos; mostrar resumen y confirmar.",
    ),
    wipe: bool = typer.Option(
        False,
        "--wipe",
        help="Ejecutar DETACH DELETE (toda la base o solo --labels).",
    ),
    indexes: bool = typer.Option(
        True,
        "--indexes/--no-indexes",
        help="Tras --database-init: crear índices estándar Ungraph.",
    ),
    labels: Optional[str] = typer.Option(
        None,
        "--labels",
        help="Con --wipe: solo nodos con estas etiquetas (coma).",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="No pedir confirmación (útil en scripts; peligroso con --wipe).",
    ),
) -> None:
    if not database_init and not wipe:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)
    if database_init and wipe:
        typer.secho(
            "Usa solo una opción: --database-init o --wipe.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(2)

    if database_init:
        reload_dotenv_files()
        reset_configuration()
        if database:
            configure(neo4j_database=database)
        settings = get_settings()
        uri = settings.neo4j_uri
        pwd = settings.neo4j_password
        user = settings.neo4j_user
        db = settings.neo4j_database

        if not uri:
            uri = typer.prompt("Neo4j URI", default="bolt://localhost:7687")
        if not pwd:
            pwd = typer.prompt("Neo4j contraseña", hide_input=True)

        user = user or "neo4j"
        db = db or "neo4j"
        if database:
            db = database
        if typer.confirm("¿Editar usuario o base de datos?", default=False):
            user = typer.prompt("Usuario Neo4j", default=user or "neo4j")
            db = typer.prompt("Base de datos Neo4j", default=db or "neo4j")

        console = Console()
        table = Table(title="Resumen Neo4j (sesión)")
        table.add_column("Campo", style="cyan")
        table.add_column("Valor")
        table.add_row("URI", uri)
        table.add_row("Usuario", user)
        table.add_row("Base de datos", db)
        table.add_row("Contraseña", "***" if pwd else "(vacía)")
        console.print(table)

        if not yes and not typer.confirm("¿Aplicar esta configuración?", default=True):
            raise typer.Exit(0)

        configure(neo4j_uri=uri, neo4j_password=pwd, neo4j_user=user, neo4j_database=db)

        cfg = get_settings()
        if indexes and (yes or typer.confirm("¿Crear índices estándar ahora?", default=True)):
            svc = Neo4jIndexService(database=cfg.neo4j_database)
            try:
                svc.setup_all_indexes()
            finally:
                svc.close()
            typer.secho("Índices listos.", fg=typer.colors.GREEN)

        typer.secho("Setup completado.", fg=typer.colors.GREEN)
        return

    if database:
        configure(neo4j_database=database)

    if not yes:
        msg = (
            f"¿Eliminar nodos con labels [{labels}]?"
            if labels
            else "¿Eliminar TODOS los nodos y relaciones del grafo?"
        )
        if not typer.confirm(msg, default=False):
            raise typer.Exit(0)

    settings = get_settings()
    svc = Neo4jIndexService(database=settings.neo4j_database)
    try:
        if labels:
            parts = [p.strip() for p in labels.split(",") if p.strip()]
            if not parts:
                raise typer.BadParameter("lista de --labels vacía")
            svc.clean_graph(node_labels=parts)
        else:
            svc.clean_graph()
    finally:
        svc.close()
    typer.secho("Grafo limpiado.", fg=typer.colors.YELLOW)
