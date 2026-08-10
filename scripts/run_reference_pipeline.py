#!/usr/bin/env python3
"""
Pipeline E2E: reset Neo4j, ingesta, **inferencia agéntica (LLM + LangGraph)** en Neo4j,
benchmark NER vs LLM, smoke GraphRAG, reporte ETI con HTML.

Por defecto persiste extracción con ``UNGRAPH_INFERENCE_MODE=llm`` (LLMGraphTransformer +
grafo contexto → extracción; spaCy opcional como hints léxicos). Requiere clave OpenAI
(``UNGRAPH_OPENAI_API_KEY`` o ``OPENAI_API_KEY``). Usa ``--persist-inference ner`` solo
si quieres baseline spaCy sin LLM.

Opcional: ``--agentic-context`` (activo por defecto) enciende
``UNGRAPH_INFERENCE_ENRICH_CONTEXT_WITH_LLM`` para contexto de documento y preguntas de
dominio vía LLM además del extractor (más llamadas API).

Con ``--ingest-local-reference`` el corpus ``scripts/data/reference_corpus_en.txt`` es el mismo
que usa el benchmark offline (NER vs LLM + DeepEval contextual relevancy por chunk). Tras inferir,
se escribe además ``retrieval_deepeval.json`` (DeepEval sobre contextos recuperados desde Neo4j;
desactivar con ``--skip-retrieval-deepeval`` o si no tienes ``ungraph[eval]`` / juez LLM).

Ejemplo:
    uv run python scripts/run_reference_pipeline.py
    uv run python scripts/run_reference_pipeline.py --ingest-local-reference
    uv run python scripts/run_reference_pipeline.py --ingest-url https://reference.langchain.com/python
    uv run python scripts/run_reference_pipeline.py --persist-inference ner
    uv run python scripts/run_reference_pipeline.py --allow-ner-without-llm
    uv run python scripts/run_reference_pipeline.py --no-agentic-context
    uv run python scripts/run_reference_pipeline.py --skip-benchmark --skip-graphrag-smoke
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

# Raíz del repo (scripts/ -> padre)
REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_INGEST_URL = "https://reference.langchain.com/python"
DEFAULT_CHUNK_SIZE = 300
DEFAULT_CHUNK_OVERLAP = 120

REFERENCE_CORPUS = REPO_ROOT / "scripts" / "data" / "reference_corpus_en.txt"
REFERENCE_GOLD = REPO_ROOT / "scripts" / "data" / "reference_corpus_gold.json"


def _cli_cmd(
    database: str | None,
    command: str,
    *args: str,
    no_banner: bool = True,
) -> list[str]:
    out = [sys.executable, "-m", "ungraph.cli"]
    if no_banner:
        out.append("--no-banner")
    out.append(command)
    if database:
        out.extend(["--database", database])
    out.extend(args)
    return out


def _run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    logging.info("Ejecutando: %s", " ".join(cmd))
    merged = {**os.environ, **(env or {})}
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=merged)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def _drop_user_constraints(database: str | None) -> None:
    """
    Elimina todas las restricciones de la base configurada.
    ``ungraph setup --wipe`` solo borra nodos; los índices se quitan con ``graph --drop-indexes``.
    Las restricciones (si existen) no las gestiona Ungraph hoy; las limpiamos vía Cypher.
    """
    from ungraph.core.configuration import get_settings, reload_dotenv_files, reset_configuration
    from ungraph.utils.graph_operations import graph_session

    reload_dotenv_files()
    reset_configuration()
    if database:
        from ungraph.core.configuration import configure

        configure(neo4j_database=database)
    settings = get_settings()
    db = settings.neo4j_database or "neo4j"

    driver = graph_session()
    try:
        with driver.session(database=db) as session:
            try:
                rows = session.run("SHOW CONSTRAINTS YIELD name RETURN name AS constraint_name")
                names = [r["constraint_name"] for r in rows]
            except Exception as exc:  # noqa: BLE001
                logging.warning(
                    "No se pudieron listar/eliminar restricciones (p. ej. Neo4j < 5): %s",
                    exc,
                )
                return
            if not names:
                logging.info("No hay restricciones que eliminar en database=%s", db)
                return
            for name in names:
                safe = str(name).replace("`", "``")
                q = f"DROP CONSTRAINT `{safe}` IF EXISTS"
                logging.info("Cypher: %s", q)
                session.run(q)
            logging.info("Restricciones eliminadas: %s", len(names))
    finally:
        driver.close()


def _latest_document_uid(database: str | None) -> str | None:
    from ungraph.core.configuration import get_settings, reload_dotenv_files, reset_configuration
    from ungraph.utils.graph_operations import graph_session

    reload_dotenv_files()
    reset_configuration()
    if database:
        from ungraph.core.configuration import configure

        configure(neo4j_database=database)
    settings = get_settings()
    db = settings.neo4j_database or "neo4j"

    driver = graph_session()
    try:
        with driver.session(database=db) as session:
            row = session.run(
                """
                MATCH (b:BibliographicArticle)
                WHERE b.document_uid IS NOT NULL
                RETURN b.document_uid AS uid
                ORDER BY coalesce(b.ingested_at, 0) DESC
                LIMIT 1
                """
            ).single()
            return row["uid"] if row else None
    finally:
        driver.close()


def _preflight_inference_mode(mode: str, *, allow_ner_fallback: bool) -> str:
    """
    Resuelve modo de persistencia; en ``llm`` exige API salvo ``--allow-ner-without-llm``.
    """
    from ungraph.core.configuration import get_settings, reload_dotenv_files, reset_configuration

    reload_dotenv_files()
    reset_configuration()
    resolved = _resolve_persist_inference(mode)
    if resolved != "llm":
        return resolved
    s = get_settings()
    if s.openai_api_key and str(s.openai_api_key).strip():
        return "llm"
    if allow_ner_fallback:
        logging.warning(
            "Sin clave OpenAI: no se puede persistir extracción LLM agéntica; "
            "continuando con NER (spaCy) para el grafo. El benchmark in-memory sigue pudiendo comparar ambos."
        )
        return "ner"
    logging.error(
        "E2E agéntico requiere clave OpenAI (UNGRAPH_OPENAI_API_KEY o OPENAI_API_KEY). "
        "Usa --allow-ner-without-llm para degradar a NER, o --persist-inference ner."
    )
    raise SystemExit(2)


def _build_infer_env(
    persisted: str,
    *,
    agentic_context: bool,
) -> dict[str, str]:
    """
    Variables para el subproceso ``infer``: LangGraph + hints spaCy al extractor;
    opcionalmente contexto de documento y preguntas de dominio vía LLM auxiliar.
    """
    env: dict[str, str] = {
        "UNGRAPH_INFERENCE_MODE": persisted,
        "UNGRAPH_INFERENCE_INJECT_SPACY_HINTS": "true",
    }
    if persisted == "llm":
        env["UNGRAPH_INFERENCE_ENRICH_CONTEXT_WITH_LLM"] = (
            "true" if agentic_context else "false"
        )
    return env


def _resolve_persist_inference(mode: str) -> str:
    """auto → llm si hay API key en settings, si no ner."""
    from ungraph.core.configuration import get_settings, reload_dotenv_files, reset_configuration

    reload_dotenv_files()
    reset_configuration()
    if mode == "auto":
        s = get_settings()
        if s.openai_api_key and str(s.openai_api_key).strip():
            return "llm"
        return "ner"
    return mode


def _run_inference_benchmark(
    *,
    report_dir: Path,
    chunk_size: int,
    chunk_overlap: int,
    infer_language: str,
) -> Path:
    from ungraph.core.configuration import get_settings, reload_dotenv_files, reset_configuration
    from ungraph.evaluation.inference_method_benchmark import run_dual_inference_benchmark

    reload_dotenv_files()
    reset_configuration()
    settings = get_settings()
    if not REFERENCE_CORPUS.is_file():
        raise FileNotFoundError(f"Falta corpus de referencia: {REFERENCE_CORPUS}")

    report = run_dual_inference_benchmark(
        corpus_path=REFERENCE_CORPUS,
        gold_path=REFERENCE_GOLD if REFERENCE_GOLD.is_file() else None,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        language=infer_language,
        base_settings=settings,
    )
    out = report_dir / "inference_benchmark.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("Benchmark NER vs LLM escrito en: %s", out.resolve())
    return out


def _run_reference_retrieval_deepeval(
    *,
    database: str | None,
    report_dir: Path,
) -> Path | None:
    """
    DeepEval (contextual relevancy) sobre búsqueda texto en chunks indexados en Neo4j.

    Usa ``graphrag_probe_queries`` de ``reference_corpus_gold.json`` si existe.
    No aborta el pipeline si falta deepeval o falla el juez LLM.
    """
    from ungraph.core.configuration import configure, get_settings, reload_dotenv_files, reset_configuration
    from ungraph.evaluation.retrieval_context_eval import (
        evaluate_retrieval_with_deepeval,
        retrieve_text_contexts,
    )
    from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

    reload_dotenv_files()
    reset_configuration()
    if database:
        configure(neo4j_database=database)

    queries: list[str] = []
    if REFERENCE_GOLD.is_file():
        try:
            gold = json.loads(REFERENCE_GOLD.read_text(encoding="utf-8"))
            queries = list(gold.get("graphrag_probe_queries") or [])
        except json.JSONDecodeError as exc:
            logging.warning("Gold JSON ilegible para retrieval DeepEval: %s", exc)

    if not queries:
        queries = ["Where is Acme Robotics based?"]

    settings = get_settings()
    db_name = database or settings.neo4j_database
    rows: list[dict] = []
    search = Neo4jSearchService(database=db_name)
    try:
        for q in queries:
            try:
                ctxs = retrieve_text_contexts(search, q, limit=5)
                if not ctxs:
                    rows.append(
                        {
                            "query": q,
                            "skipped": True,
                            "reason": "no_retrieval_contexts",
                            "context_count": 0,
                        }
                    )
                    continue
                try:
                    metrics = evaluate_retrieval_with_deepeval(
                        query=q,
                        retrieval_contexts=ctxs,
                    )
                except ImportError as exc:
                    out = report_dir / "retrieval_deepeval.json"
                    payload = {
                        "available": False,
                        "reason": str(exc),
                        "hint": "pip install 'ungraph[eval]'",
                    }
                    out.write_text(
                        json.dumps(payload, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    logging.info(
                        "DeepEval recuperación no disponible (escrito aviso en %s)",
                        out.resolve(),
                    )
                    return out
                rows.append(
                    {
                        "query": q,
                        "context_count": len(ctxs),
                        "metrics": metrics,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logging.warning("DeepEval recuperación falló para %r: %s", q, exc)
                rows.append({"query": q, "error": str(exc)})
    finally:
        search.close()

    out = report_dir / "retrieval_deepeval.json"
    payload = {
        "available": True,
        "database": db_name,
        "queries": rows,
        "gold_source": str(REFERENCE_GOLD) if REFERENCE_GOLD.is_file() else None,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("DeepEval recuperación (texto) en: %s", out.resolve())
    return out


def _run_graphrag_smoke(
    *,
    database: str | None,
    report_dir: Path,
) -> Path | None:
    """
    Proxy ligero de GraphRAG: búsqueda textual sobre chunks ya indexados en Neo4j.
    Las preguntas salen de reference_corpus_gold.json cuando existe.
    """
    from ungraph.core.configuration import configure, get_settings, reload_dotenv_files, reset_configuration

    import ungraph as ungraph_pkg

    reload_dotenv_files()
    reset_configuration()
    if database:
        configure(neo4j_database=database)

    queries: list[str] = []
    if REFERENCE_GOLD.is_file():
        try:
            gold = json.loads(REFERENCE_GOLD.read_text(encoding="utf-8"))
            queries = list(gold.get("graphrag_probe_queries") or [])
        except json.JSONDecodeError as exc:
            logging.warning("No se pudo leer gold JSON para graphrag smoke: %s", exc)

    if not queries:
        queries = ["Where is Acme Robotics based?"]

    db_name = database or get_settings().neo4j_database
    rows: list[dict] = []
    for q in queries:
        try:
            hits = ungraph_pkg.search(q, limit=5, database=db_name)
            rows.append(
                {
                    "query": q,
                    "hits": len(hits),
                    "top_scores": [round(float(h.score), 4) for h in hits[:3]],
                    "top_snippets": [(h.content or "")[:200] for h in hits[:2]],
                }
            )
        except Exception as exc:  # noqa: BLE001
            logging.warning("graphrag smoke falló para %r: %s", q, exc)
            rows.append({"query": q, "error": str(exc)})

    out = report_dir / "graphrag_smoke.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("Smoke GraphRAG (text search) en: %s", out.resolve())
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "E2E: reset Neo4j + ingesta + inferencia agéntica (LLM/LangGraph por defecto) + benchmark + reporte ETI."
        ),
    )
    parser.add_argument(
        "--ingest-local-reference",
        action="store_true",
        help=(
            "Ingerir scripts/data/reference_corpus_en.txt (mismo texto que el benchmark NER/LLM y gold). "
            "Tras inferir, ejecuta también evaluación DeepEval sobre recuperación Neo4j "
            "(salvo --skip-retrieval-deepeval)."
        ),
    )
    parser.add_argument(
        "--ingest-url",
        default=DEFAULT_INGEST_URL,
        help="URL o ruta para ``ungraph ingest --path`` si no usas --ingest-local-reference.",
    )
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    parser.add_argument(
        "--database",
        "-d",
        default=None,
        help="Base Neo4j (pasa ``-d`` a todos los subcomandos ungraph).",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=REPO_ROOT / "reports" / "eti_reference_run",
        help="Carpeta de salida del bundle ``ungraph report -o`` y JSONs auxiliares.",
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Abrir el index.html del reporte al final.",
    )
    parser.add_argument(
        "--skip-reset",
        action="store_true",
        help="No borrar restricciones/índices/datos (solo ingest + infer + report).",
    )
    parser.add_argument(
        "--infer-language",
        default="en",
        choices=("en", "es"),
        help="Idioma para ``ungraph infer --language`` y para el benchmark spaCy.",
    )
    parser.add_argument(
        "--persist-inference",
        default="llm",
        choices=("auto", "ner", "llm"),
        help=(
            "Modo persistido en Neo4j (UNGRAPH_INFERENCE_MODE) para ``infer --kmining``. "
            "Por defecto llm (LangGraph + LLMGraphTransformer, hints spaCy si hay modelo). "
            "auto = llm si hay API key, si no ner."
        ),
    )
    parser.add_argument(
        "--allow-ner-without-llm",
        action="store_true",
        help=(
            "Si eliges llm/auto pero no hay API key, degradar a NER en lugar de fallar "
            "(no es E2E agéntico completo)."
        ),
    )
    parser.add_argument(
        "--agentic-context",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "En modo llm: activar UNGRAPH_INFERENCE_ENRICH_CONTEXT_WITH_LLM (contexto de documento + "
            "preguntas de dominio vía LLM auxiliar antes del extractor)."
        ),
    )
    parser.add_argument(
        "--skip-benchmark",
        action="store_true",
        help="No ejecutar benchmark offline (NER vs LLM + DeepEval por chunk) sobre scripts/data/reference_corpus_en.txt.",
    )
    parser.add_argument(
        "--skip-retrieval-deepeval",
        action="store_true",
        help=(
            "Con --ingest-local-reference: no generar retrieval_deepeval.json (DeepEval sobre hits de búsqueda en Neo4j)."
        ),
    )
    parser.add_argument(
        "--skip-graphrag-smoke",
        action="store_true",
        help="No ejecutar búsqueda textual de prueba tras infer (proxy GraphRAG).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log DEBUG.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    db = args.database

    if not args.skip_reset:
        logging.info("=== Fase 1: restricciones e índices viejos + wipe de datos ===")
        _drop_user_constraints(db)
        _run(_cli_cmd(db, "graph", "--drop-indexes"))
        _run(_cli_cmd(db, "setup", "--wipe", "--yes"))
        logging.info("=== Fase 2: índices Ungraph (init) ===")
        _run(_cli_cmd(db, "graph", "--setup-indexes"))
    else:
        logging.info("Omitido reset (--skip-reset).")

    ingest_path = (
        str(REFERENCE_CORPUS.resolve())
        if args.ingest_local_reference
        else args.ingest_url
    )
    if args.ingest_local_reference and not REFERENCE_CORPUS.is_file():
        logging.error("Falta corpus local: %s", REFERENCE_CORPUS)
        raise SystemExit(2)

    logging.info("=== Fase 3: ingesta (%s) ===", ingest_path)
    _run(
        _cli_cmd(
            db,
            "ingest",
            "--path",
            ingest_path,
            "--chunk-size",
            str(args.chunk_size),
            "--chunk-overlap",
            str(args.chunk_overlap),
        )
    )

    report_dir = args.report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    persisted = _preflight_inference_mode(
        args.persist_inference,
        allow_ner_fallback=args.allow_ner_without_llm,
    )
    infer_env = _build_infer_env(persisted, agentic_context=args.agentic_context)
    logging.info(
        "=== Fase 4: inferencia (minado + refinamiento Entity) — modo persistido=%s, "
        "agentic_context=%s, env extra: %s ===",
        persisted,
        args.agentic_context,
        {k: infer_env[k] for k in sorted(infer_env) if k.startswith("UNGRAPH_INFERENCE")},
    )
    _run(
        _cli_cmd(
            db,
            "infer",
            "--kmining",
            "--consolidate",
            "--resolve",
            "--language",
            args.infer_language,
        ),
        env=infer_env,
    )

    doc_uid = _latest_document_uid(db)
    if doc_uid:
        logging.info("Último document_uid (BibliographicArticle): %s", doc_uid)

    if not args.skip_benchmark:
        logging.info("=== Fase 5a: benchmark NER vs LLM (in-memory, mismo corpus) ===")
        try:
            _run_inference_benchmark(
                report_dir=report_dir,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                infer_language=args.infer_language,
            )
        except Exception as exc:  # noqa: BLE001
            logging.warning("Benchmark omitido o fallido: %s", exc)

    if args.ingest_local_reference and not args.skip_retrieval_deepeval:
        logging.info(
            "=== Fase 5a-ii: DeepEval contextual relevancy sobre recuperación (Neo4j, corpus local) ==="
        )
        try:
            _run_reference_retrieval_deepeval(database=db, report_dir=report_dir)
        except Exception as exc:  # noqa: BLE001
            logging.warning("Evaluación recuperación (DeepEval) omitida o fallida: %s", exc)

    if not args.skip_graphrag_smoke:
        logging.info("=== Fase 5b: smoke GraphRAG (text search Neo4j) ===")
        try:
            _run_graphrag_smoke(database=db, report_dir=report_dir)
        except Exception as exc:  # noqa: BLE001
            logging.warning("Smoke GraphRAG omitido o fallido: %s", exc)

    logging.info("=== Fase 6: reporte ETI + hipervínculo (HTML incluye benchmark/GraphRAG si hay JSON en la carpeta) ===")
    report_args = [
        "--output",
        str(report_dir),
        "--sample-limit",
        "400",
    ]
    if doc_uid:
        report_args.extend(["--document-uid", doc_uid])
    if args.open_browser:
        report_args.append("--open-browser")
    _run(_cli_cmd(db, "report", *report_args))

    index_html = report_dir / "index.html"
    try:
        from ungraph.cli.report_link import echo_eti_report_link

        echo_eti_report_link(index_html, open_browser=args.open_browser)
    except Exception as exc:  # noqa: BLE001
        logging.warning("No se pudo imprimir hipervínculo Rich: %s", exc)
        uri = index_html.resolve().as_uri()
        logging.info("Reporte (file URI): %s", uri)

    logging.info("Pipeline terminado. Reporte en: %s", index_html.resolve())


if __name__ == "__main__":
    main()
