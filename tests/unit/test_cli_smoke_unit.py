"""CLI smoke: help / no-args exit codes for setup|graph|ingest|infer|report."""

from __future__ import annotations

import pytest

pytest.importorskip("typer")

from typer.testing import CliRunner

from ungraph.cli.main import app

runner = CliRunner()


@pytest.mark.unit
@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["--no-banner", "--help"],
        ["setup", "--help"],
        ["graph", "--help"],
        ["ingest", "--help"],
        ["infer", "--help"],
        ["report", "--help"],
        ["ingest-table", "--help"],
    ],
)
def test_cli_help_exits_zero(args: list[str]) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Usage" in result.output or "help" in result.output.lower() or len(result.output) > 0


@pytest.mark.unit
def test_cli_root_importable() -> None:
    from ungraph.cli.main import app as cli_app

    assert cli_app is not None
    assert callable(cli_app)
