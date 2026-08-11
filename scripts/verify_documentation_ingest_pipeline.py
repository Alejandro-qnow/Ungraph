#!/usr/bin/env python3
"""
Verificación end-to-end del pipeline documentación HTML (CLI).

La lógica vive en ``ungraph.utils.verify_doc_pipeline``.

Uso::

  uv sync --extra crawl
  uv run python scripts/verify_documentation_ingest_pipeline.py
  uv run python scripts/verify_documentation_ingest_pipeline.py --ingest-one
"""

from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("verify_doc_pipeline")


def main() -> int:
    from ungraph.utils.verify_doc_pipeline import run_verification

    ap = argparse.ArgumentParser(description="Verificar pipeline HTML documentación")
    ap.add_argument(
        "--ingest-one",
        action="store_true",
        help="Tras verificar CIR/chunking, ingerir la 1ª URL en Neo4j (requiere credenciales)",
    )
    ap.add_argument("--database", default="neo4j")
    args = ap.parse_args()

    try:
        run_verification(ingest_one=args.ingest_one, database=args.database)
    except Exception as e:
        logger.exception("Fallo: %s", e)
        return 1
    logger.info("OK: todas las verificaciones pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
