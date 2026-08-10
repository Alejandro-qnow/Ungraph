#!/usr/bin/env python3
"""One-off sanitization: remove NEXT_CHUNK edges across distinct source_document_uid values."""

import argparse

from ungraph.core.configuration import get_settings
from ungraph.utils.graph_operations import graph_session, sanitize_illegitimate_next_chunk


def main() -> None:
    ap = argparse.ArgumentParser(description="Delete cross-document NEXT_CHUNK edges")
    ap.add_argument(
        "--database",
        default=None,
        help="Neo4j database name (default: Settings.neo4j_database)",
    )
    ns = ap.parse_args()
    settings = get_settings()
    db = ns.database or settings.neo4j_database
    driver = graph_session()
    try:
        with driver.session(database=db) as session:
            sanitize_illegitimate_next_chunk(session)
            print("Sanitize completed.")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
