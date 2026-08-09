"""`ungraph ingest-table`: ingesta de datos tabulares (CSV/XLSX) con inferencia de esquema.

Flujo de dos pasos (Schema-Guided Ingestion):
1. Por defecto (--dry-run): infiere el mapeo columna→rol y escribe una propuesta editable
   (YAML) SIN tocar el grafo.
2. Con --apply --mapping <archivo>: aplica la propuesta confirmada/editada al grafo.
   (--apply sin --mapping aplica directamente la inferencia automática.)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

import typer

from ungraph.application.dependencies import create_ingest_tabular_use_case
from ungraph.core.configuration import configure, get_settings
from ungraph.domain.value_objects.tabular_schema import TabularSchemaProposal

logger = logging.getLogger(__name__)

_TABULAR_SUFFIXES = {".csv", ".xlsx", ".xls"}


def _dump_proposals(proposals: List[TabularSchemaProposal], path: Path) -> None:
    payload = {"tables": [p.to_dict() for p in proposals]}
    try:
        import yaml

        text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    except ImportError:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")


def _load_proposals(path: Path) -> List[TabularSchemaProposal]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml

        data = yaml.safe_load(text)
    except ImportError:
        data = json.loads(text)
    tables = data.get("tables", data if isinstance(data, list) else [])
    return [TabularSchemaProposal.from_dict(t) for t in tables]


def _print_proposal(proposal: TabularSchemaProposal) -> None:
    typer.secho(
        f"\nTabla '{proposal.source}' -> (:{proposal.resolved_row_label})"
        f"  clave={proposal.row_key_columns or '[sintetica]'}",
        fg=typer.colors.CYAN,
        bold=True,
    )
    for c in proposal.columns:
        extra = ""
        if c.target_label:
            extra = f" -> (:{c.resolved_target_label()}) [{c.resolved_relationship_type()}]"
        typer.echo(
            f"  {c.column:20s} {c.role.value:12s} conf={c.confidence:.2f} "
            f"({c.decided_by}){extra}"
        )


def ingest_table(
    ctx: typer.Context,
    path: Path = typer.Argument(
        ...,
        help="Archivo tabular (.csv/.xlsx/.xls).",
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    database: Optional[str] = typer.Option(
        None, "--database", "-d", help="Sobrescribe la base Neo4j."
    ),
    apply: bool = typer.Option(
        False,
        "--apply/--dry-run",
        help="--apply persiste al grafo; por defecto (--dry-run) solo propone el esquema.",
    ),
    mapping: Optional[Path] = typer.Option(
        None,
        "--mapping",
        help="Propuesta confirmada/editada (YAML) a aplicar (requiere --apply).",
        exists=True,
        dir_okay=False,
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        help="Ruta de salida de la propuesta en dry-run (default: <archivo>.mapping.yaml).",
    ),
    use_llm: bool = typer.Option(
        True, "--llm/--no-llm", help="Usar LLM para desambiguar columnas dudosas."
    ),
) -> None:
    if path.suffix.lower() not in _TABULAR_SUFFIXES:
        typer.secho(
            f"Extensión no soportada: {path.suffix}. Usa CSV o XLSX.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(2)

    if database:
        configure(neo4j_database=database)
    settings = get_settings()

    uc = create_ingest_tabular_use_case(
        settings=settings,
        database=settings.neo4j_database,
        use_llm_disambiguation=use_llm,
    )

    confirmed: Optional[List[TabularSchemaProposal]] = None
    if mapping is not None:
        confirmed = _load_proposals(mapping)
        typer.echo(f"Mapeo cargado desde {mapping}: {len(confirmed)} tabla(s).")

    result = uc.execute(path, dry_run=not apply, mappings=confirmed)

    for proposal in result.proposals:
        _print_proposal(proposal)

    if not apply:
        out_path = out or path.with_suffix(path.suffix + ".mapping.yaml")
        _dump_proposals(result.proposals, out_path)
        typer.secho(
            f"\nPropuesta escrita en {out_path}. Revísala/edítala y aplica con:\n"
            f"  ungraph ingest-table \"{path}\" --apply --mapping \"{out_path}\"",
            fg=typer.colors.GREEN,
        )
        return

    total_rows = sum(s.get("rows_persisted", 0) for s in result.stats)
    typer.secho(
        f"\nListo: {len(result.stats)} tabla(s), {total_rows} fila(s) persistida(s).",
        fg=typer.colors.GREEN,
    )
