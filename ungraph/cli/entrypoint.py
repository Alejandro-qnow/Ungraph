"""Console script entry: avoids importing Typer until the extra is installed."""

from __future__ import annotations


def run() -> None:
    try:
        import typer  # noqa: F401
    except ImportError:
        raise SystemExit(
            "The Ungraph CLI requires the optional Typer dependency. "
            "Install with: pip install 'ungraph[cli]'"
        ) from None
    from ungraph.cli.main import app

    app()


if __name__ == "__main__":
    run()
