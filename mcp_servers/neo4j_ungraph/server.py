"""
Neo4j MCP server for Cursor (stdio).

Uses the same env vars as Ungraph: UNGRAPH_NEO4J_* with fallbacks NEO4J_*.
Do not print to stdout (MCP JSON-RPC). Logs go to stderr.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv
from neo4j import Driver, GraphDatabase
from neo4j.exceptions import Neo4jError

from mcp.server.fastmcp import FastMCP

MAX_RECORDS_DEFAULT = 500

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("neo4j_ungraph_mcp")

# Repo root = mcp_servers/neo4j_ungraph/server.py -> parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]
_UNGRAPH_ENV = _REPO_ROOT / "ungraph" / ".env"

load_dotenv(find_dotenv(), override=False)
if _UNGRAPH_ENV.is_file():
    load_dotenv(_UNGRAPH_ENV, override=False)

mcp = FastMCP("neo4j-ungraph")

_driver: Driver | None = None


def _env_first(*names: str) -> str | None:
    for n in names:
        v = os.environ.get(n)
        if v is not None and str(v).strip() != "":
            return str(v)
    return None


def _settings() -> tuple[str, str, str, str | None]:
    uri = _env_first("UNGRAPH_NEO4J_URI", "NEO4J_URI")
    user = _env_first("UNGRAPH_NEO4J_USER", "NEO4J_USER", "NEO4J_USERNAME")
    password = _env_first("UNGRAPH_NEO4J_PASSWORD", "NEO4J_PASSWORD")
    database = _env_first(
        "UNGRAPH_NEO4J_DATABASE",
        "NEO4J_DATABASE",
        "NEO4J_DB",
    )
    if not uri or not user or not password:
        raise RuntimeError(
            "Missing Neo4j config. Set UNGRAPH_NEO4J_URI, UNGRAPH_NEO4J_USER, "
            "UNGRAPH_NEO4J_PASSWORD (or NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD)."
        )
    return uri, user, password, database


def _get_driver() -> Any:
    global _driver
    if _driver is None:
        uri, user, password, _db = _settings()
        _driver = GraphDatabase.driver(uri, auth=(user, password))
        log.info("Neo4j driver created for %s", uri)
    return _driver


def _session_kw() -> dict[str, Any]:
    _uri, _u, _p, database = _settings()
    if database:
        return {"database": database}
    return {}


def _parse_params(params_json: str | None) -> dict[str, Any]:
    if params_json is None or not str(params_json).strip():
        return {}
    try:
        out = json.loads(params_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"params_json must be valid JSON object: {e}") from e
    if not isinstance(out, dict):
        raise ValueError("params_json must decode to a JSON object")
    return out


def _records_to_json(records: list[dict[str, Any]], *, truncated: bool) -> str:
    payload: dict[str, Any] = {"records": records, "count": len(records)}
    if truncated:
        payload["truncated"] = True
        payload["note"] = f"Only the first {MAX_RECORDS_DEFAULT} rows are returned."
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


@mcp.tool()
def read_neo4j_cypher(query: str, params_json: str | None = None) -> str:
    """Run a read-only Cypher query. Params are optional JSON object for $parameters.

    Example params_json: '{"id": "abc"}'
    """
    try:
        params = _parse_params(params_json)
        driver = _get_driver()

        def work2(tx: Any) -> tuple[list[dict[str, Any]], bool]:
            result = tx.run(query, params)
            rows = []
            for i, record in enumerate(result):
                if i >= MAX_RECORDS_DEFAULT:
                    return rows, True
                rows.append(dict(record))
            return rows, False

        with driver.session(**_session_kw()) as session:
            rows, truncated = session.execute_read(work2)
        return _records_to_json(rows, truncated=truncated)
    except (Neo4jError, OSError, RuntimeError, ValueError) as e:
        log.exception("read_neo4j_cypher failed")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def write_neo4j_cypher(query: str, params_json: str | None = None) -> str:
    """Run a write Cypher (CREATE/MERGE/DELETE/SET). Use with care."""
    try:
        params = _parse_params(params_json)
        driver = _get_driver()

        def work(tx: Any) -> tuple[list[dict[str, Any]], bool]:
            result = tx.run(query, params)
            rows = []
            for i, record in enumerate(result):
                if i >= MAX_RECORDS_DEFAULT:
                    return rows, True
                rows.append(dict(record))
            return rows, False

        with driver.session(**_session_kw()) as session:
            rows, truncated = session.execute_write(work)
        summary = {"records": rows, "count": len(rows)}
        if truncated:
            summary["truncated"] = True
        return json.dumps(summary, ensure_ascii=False, indent=2, default=str)
    except (Neo4jError, OSError, RuntimeError, ValueError) as e:
        log.exception("write_neo4j_cypher failed")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def get_neo4j_schema() -> str:
    """List node labels, relationship types, and property keys (db metadata procedures)."""
    try:
        driver = _get_driver()
        out: dict[str, list[str]] = {"labels": [], "relationshipTypes": [], "propertyKeys": []}

        def read_meta(tx: Any) -> None:
            out["labels"] = [r["label"] for r in tx.run("CALL db.labels() YIELD label RETURN label AS label ORDER BY label")]
            out["relationshipTypes"] = [
                r["relationshipType"]
                for r in tx.run(
                    "CALL db.relationshipTypes() YIELD relationshipType "
                    "RETURN relationshipType AS relationshipType ORDER BY relationshipType"
                )
            ]
            out["propertyKeys"] = [
                r["propertyKey"]
                for r in tx.run(
                    "CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey AS propertyKey ORDER BY propertyKey"
                )
            ]

        with driver.session(**_session_kw()) as session:
            session.execute_read(read_meta)
        return json.dumps(out, ensure_ascii=False, indent=2)
    except (Neo4jError, OSError, RuntimeError) as e:
        log.exception("get_neo4j_schema failed")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
