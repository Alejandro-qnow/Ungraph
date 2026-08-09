"""Aplicación Typer raíz."""

from __future__ import annotations

import typer

from ungraph.cli.banner import help_requested_in_argv, render_banner
from ungraph.cli.commands.graph_cli import graph
from ungraph.cli.commands.ingest_cli import ingest
from ungraph.cli.commands.ingest_table_cli import ingest_table
from ungraph.cli.commands.infer_cli import infer
from ungraph.cli.commands.report_cli import report
from ungraph.cli.commands.setup import setup

app = typer.Typer(
    help=(
        "[bold cyan]Ungraph[/bold cyan] — CLI. Instala el extra: "
        "[dim]pip install 'ungraph[cli]'[/dim]"
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
    add_completion=False,
)


@app.callback()
def main_callback(
    ctx: typer.Context,
    no_banner: bool = typer.Option(
        False,
        "--no-banner",
        help="No mostrar el panel de bienvenida (scripts / CI).",
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["no_banner"] = no_banner
    if not no_banner and not help_requested_in_argv():
        render_banner()


app.command("setup")(setup)
app.command("ingest")(ingest)
app.command("ingest-table")(ingest_table)
app.command("graph")(graph)
app.command("infer")(infer)
app.command("report")(report)
