"""`ungraph infer`: minado sobre chunks, consolidación y resolución de :Entity."""

from __future__ import annotations

import logging
from typing import Optional

import typer

from ungraph.application.dependencies import (
    create_entity_graph_maintenance_service,
    create_knowledge_mining_use_case,
)
from ungraph.core.configuration import configure, get_settings

logger = logging.getLogger(__name__)


def _normalize_infer_lang(value: str) -> str:
    v = (value or "en").lower()
    if v not in ("en", "es"):
        raise typer.BadParameter("Usa en o es.", param_hint="--language")
    return v


def infer(
    ctx: typer.Context,
    database: Optional[str] = typer.Option(
        None,
        "--database",
        "-d",
        help="Sobrescribe la base Neo4j para esta operación.",
    ),
    inference_language: str = typer.Option(
        "en",
        "--language",
        "-l",
        help="Idioma para inferencia NER (ner): en | es",
        callback=_normalize_infer_lang,
    ),
    no_tqdm: bool = typer.Option(
        False,
        "--no-tqdm",
        help="Sin barra de progreso en --kmining.",
    ),
    kmining: bool = typer.Option(
        False,
        "--kmining",
        help="Inferir facts sobre :Chunk sin (:Fact)-[:DERIVED_FROM]->(chunk).",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help=(
            "Con --kmining: re-minar TODOS los chunks (no solo los sin facts). "
            "Borra las derivaciones Extracted previas y re-infiere con el modo actual "
            "(p. ej. actualizar NER→LLM). Respeta lo Curated/Invalid."
        ),
    ),
    consolidate: bool = typer.Option(
        False,
        "--consolidate",
        help="Fusionar :Entity con el mismo nombre (trim + minúsculas).",
    ),
    resolve: bool = typer.Option(
        False,
        "--resolve",
        help="Segunda fusión de :Entity quitando '.' y ',' del nombre (más agresivo).",
    ),
) -> None:
    if not any((kmining, consolidate, resolve)):
        typer.echo(ctx.get_help())
        raise typer.Exit(0)

    if database:
        configure(neo4j_database=database)

    settings = get_settings()
    mode = (settings.inference_mode or "ner").strip().lower()
    logger.info(
        "infer: UNGRAPH_INFERENCE_MODE=%s "
        "(el grafo LangGraph context→extract solo se usa con modo llm + LLMInferenceService).",
        mode,
    )
    if mode == "ner":
        typer.secho(
            "[infer] Modo actual: NER (spaCy). El agente LangGraph no participa; "
            "usa UNGRAPH_INFERENCE_MODE=llm y clave OpenAI para LLMGraphTransformer.",
            fg=typer.colors.YELLOW,
        )
    else:
        typer.secho(
            f"[infer] Modo actual: {mode!r} — revisa logs INFO de "
            "`ungraph.infrastructure.agents.inference_state_graph` para el Mermaid del grafo.",
            fg=typer.colors.CYAN,
        )

    db = settings.neo4j_database
    exit_code = 0

    if kmining:
        try:
            uc = create_knowledge_mining_use_case(
                settings=settings,
                database=db,
                inference_language=inference_language,
            )
        except RuntimeError as e:
            typer.secho(str(e), fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from e
        try:
            result = uc.execute(use_tqdm=not no_tqdm, force=force)
            label = "kmining/force" if force else "kmining"
            typer.secho(
                f"[{label}] chunks={result.chunks_pending} "
                f"procesados={result.chunks_inferred} "
                f"facts={result.facts_persisted} relaciones={result.relations_persisted} "
                f"errores={result.errors}",
                fg=typer.colors.GREEN if result.errors == 0 else typer.colors.YELLOW,
            )
            if result.errors:
                exit_code = 1
        finally:
            uc.close()

    if consolidate:
        maint = create_entity_graph_maintenance_service(database=db)
        n = maint.consolidate_entities_case_insensitive()
        typer.secho(
            f"[consolidate] nodos Entity fusionados (eliminados)={n}",
            fg=typer.colors.CYAN,
        )

    if resolve:
        maint = create_entity_graph_maintenance_service(database=db)
        n = maint.resolve_entities_strip_punctuation()
        typer.secho(
            f"[resolve] nodos Entity fusionados (eliminados)={n}",
            fg=typer.colors.CYAN,
        )

    if force and kmining:
        # El re-minado forzado puede dejar entidades sin mención; limpiarlas para
        # que el grafo quede consistente tras actualizar la extracción.
        maint = create_entity_graph_maintenance_service(database=db)
        pruned = maint.prune_orphan_entities()
        typer.secho(
            f"[prune] entidades huérfanas eliminadas={pruned}",
            fg=typer.colors.CYAN,
        )

    if exit_code:
        raise typer.Exit(exit_code)
