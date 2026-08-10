"""
Impresión del enlace al reporte ETI (file URI + hipervínculo Rich cuando está disponible).
"""

from __future__ import annotations

import webbrowser
from pathlib import Path

import typer


def echo_eti_report_link(index_html: Path, *, open_browser: bool = False) -> None:
    """
    Muestra un hipervínculo al index.html del reporte y, opcionalmente, abre el navegador.

    En terminales compatibles con Rich (p. ej. la que usa Typer), el texto es clicable.
    """
    resolved = index_html.resolve()
    if not resolved.is_file():
        typer.secho(
            f"No se encontró el reporte en {resolved} (¿falló la generación?).",
            fg=typer.colors.YELLOW,
            err=True,
        )
        return
    uri = resolved.as_uri()
    if open_browser:
        webbrowser.open(uri)
    try:
        from rich.console import Console

        console = Console()
        console.print(
            "[bold green]Reporte ETI:[/bold green] "
            f"[link={uri}]Abrir en el navegador[/link] "
            "[dim](clic o Ctrl+clic según la terminal)[/dim]",
        )
        console.print(f"[dim]{uri}[/dim]")
        console.print(
            "[dim]Si la página sale en blanco con file://, sirve el directorio: "
            "`python -m http.server 8765` dentro de la carpeta del reporte y abre "
            "http://127.0.0.1:8765/[/dim]",
        )
    except ImportError:
        typer.secho(f"Reporte ETI (abre en el navegador): {uri}", fg=typer.colors.GREEN)
        typer.secho(
            "Si ves página en blanco con file://: cd a la carpeta del reporte y "
            "`python -m http.server 8765`, luego http://127.0.0.1:8765/",
            fg=typer.colors.CYAN,
        )
