#!/usr/bin/env python3
"""
Ingesta de un HTML local al grafo Neo4j con patrón FILE_PAGE_CHUNK (por defecto).

Requisitos:
  - Neo4j ya en ejecución y accesible (no hace falta Docker si tu instancia ya está arriba).
  - URI y contraseña vía variables ``UNGRAPH_*`` o argumentos ``--uri`` / ``--password``.

Ejemplo (PowerShell) con Neo4j local ya levantado::

  $env:UNGRAPH_NEO4J_URI="bolt://localhost:7687"
  $env:UNGRAPH_NEO4J_PASSWORD="tu_password"
  uv run python scripts/ingest_html_local_demo.py

O todo en línea::

  uv run python scripts/ingest_html_local_demo.py --uri bolt://localhost:7687 --password tu_password
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_HTML = ROOT / "ungraph" / "data" / "sample_documentation.html"


def main() -> int:
    p = argparse.ArgumentParser(description="Ingesta HTML de muestra → Neo4j (FILE_PAGE_CHUNK)")
    p.add_argument(
        "--html",
        type=Path,
        default=SAMPLE_HTML,
        help="Ruta al archivo .html (default: ungraph/data/sample_documentation.html)",
    )
    p.add_argument("--uri", default=None, help="bolt://... (override env)")
    p.add_argument("--user", default="neo4j")
    p.add_argument("--password", default=None)
    p.add_argument("--database", default="neo4j")
    p.add_argument("--chunk-size", type=int, default=800)
    p.add_argument("--chunk-overlap", type=int, default=120)
    args = p.parse_args()

    import ungraph
    from ungraph.core.configuration import configure, get_settings

    uri = args.uri or get_settings().neo4j_uri
    password = args.password or get_settings().neo4j_password
    if not uri or not password:
        print(
            "Falta Neo4j: pasa --uri y --password o define "
            "UNGRAPH_NEO4J_URI y UNGRAPH_NEO4J_PASSWORD",
            file=sys.stderr,
        )
        return 2

    configure(
        neo4j_uri=uri,
        neo4j_user=args.user,
        neo4j_password=password,
        neo4j_database=args.database,
    )

    if not args.html.exists():
        print(f"No existe: {args.html}", file=sys.stderr)
        return 2

    print(f"Ingiriendo: {args.html}")
    chunks = ungraph.ingest_document(
        args.html,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        database=args.database,
    )
    print(f"Chunks creados: {len(chunks)}")

    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(uri, auth=(args.user, password))
    with driver.session(database=args.database) as session:
        fn = args.html.name
        rec = session.run(
            """
            MATCH (f:File {filename: $fn})
            OPTIONAL MATCH (f)-[:CONTAINS]->(p:Page)
            OPTIONAL MATCH (p)-[:HAS_CHUNK]->(c:Chunk)
            RETURN count(DISTINCT f) AS files, count(DISTINCT p) AS pages, count(DISTINCT c) AS chunks
            """,
            fn=fn,
        ).single()
        if rec:
            print(
                f"Grafo (filename={fn!r}): "
                f"File={rec['files']}, Page={rec['pages']}, Chunk={rec['chunks']}"
            )
        sample = session.run(
            """
            MATCH (c:Chunk)
            WHERE c.page_content CONTAINS 'Neo4j' OR c.page_content CONTAINS 'ungraph'
            RETURN c.chunk_id AS id, substring(c.page_content, 0, 120) AS preview
            LIMIT 3
            """
        )
        rows = list(sample)
        if rows:
            print("Muestra de chunks (preview):")
            for r in rows:
                print(f"  - {r['id']}: {r['preview']!r}...")
    driver.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
