"""Banner enriquecido (Rich) para la CLI de Ungraph."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

# Figura tipo “UNGRAPH” (estilo Bitstream/terminal)
ASCII_MARK = r"""
           __  _        _
 | | |\ | /__ |_)  /\  |_) |_|
 |_| | \| \_| | \ /--\ |   | |
"""

TAGLINE = "From Complex to Knowledge"
BYLINE = "By Qnow"
MAINTAINER = "Maintained by Alejandro Giraldo Londoño"
URL_QNOW = "https://qnow.tech"
URL_DOCS = "https://ungraph.readthedocs.io"
URL_GITHUB = "https://github.com/Alejandro-qnow/Ungraph"


def help_requested_in_argv() -> bool:
    """True si el usuario pide ayuda (--help / -h); conviene no mezclar banner con la salida de help."""
    import sys

    return "--help" in sys.argv or "-h" in sys.argv


def render_banner(console: Console | None = None) -> None:
    """Imprime el banner en un Panel Rich (logo, tagline y enlaces)."""
    from rich import box
    from rich.align import Align
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.text import Text

    console = console or Console(stderr=False)

    logo = Text(ASCII_MARK.strip("\n"), style="bold cyan", no_wrap=True)
    meta_lines = Text.assemble(
        (f"\n{TAGLINE}\n", "italic bright_white"),
        (f"{BYLINE}\n", "dim"),
        (f"{MAINTAINER}\n", "dim"),
        ("\n", ""),
        (" • ", "dim"),
        ("Qnow tech", f"link {URL_QNOW}"),
        (" • ", "dim"),
        ("Docs", f"link {URL_DOCS}"),
        (" • ", "dim"),
        ("GitHub", f"link {URL_GITHUB}"),
        "\n",
    )
    inner = Group(
        Align.center(logo),
        Align.center(meta_lines),
    )
    panel = Panel(
        inner,
        title=Text(" UNGRAPH ", style="bold white on blue"),
        subtitle="[dim]pip install 'ungraph[cli]'[/dim]",
        border_style="blue",
        box=box.ROUNDED,
        padding=(0, 1),
    )
    console.print(panel)
