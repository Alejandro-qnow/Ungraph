"""
Cliente SPARQL mínimo (HTTP POST, resultados JSON) sin dependencias extra.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Literal, cast

logger = logging.getLogger(__name__)

PostFormat = Literal["content", "form"]


def sparql_select_bindings(
    endpoint: str,
    query: str,
    *,
    timeout_seconds: float = 60.0,
    post_format: PostFormat = "content",
) -> list[dict[str, Any]]:
    """
    Ejecuta SELECT y devuelve ``results.bindings`` del JSON estándar SPARQL 1.1.

    ``post_format``:
    - ``content``: ``Content-Type: application/sparql-query`` (Fuseki, muchos endpoints).
    - ``form``: ``application/x-www-form-urlencoded`` con clave ``query``.
    """
    ep = endpoint.strip()
    q = (query or "").strip()
    if not ep or not q:
        return []

    if post_format == "form":
        body = urllib.parse.urlencode({"query": q}).encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/sparql-results+json",
        }
    else:
        body = q.encode("utf-8")
        headers = {
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        }

    req = urllib.request.Request(ep, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"SPARQL HTTP {e.code}: {err_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"SPARQL request failed: {e}") from e

    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.debug("SPARQL non-JSON response head: %s", raw[:400])
        raise RuntimeError("SPARQL endpoint did not return JSON results") from e

    results = doc.get("results") or {}
    bindings = results.get("bindings")
    if not isinstance(bindings, list):
        return []
    return cast(list[dict[str, Any]], bindings)


def binding_text(binding: dict[str, Any], var_name: str) -> str | None:
    """Extrae el string de un término JSON SPARQL (literal o URI)."""
    cell = binding.get(var_name)
    if not isinstance(cell, dict):
        return None
    val = cell.get("value")
    if val is None:
        return None
    return str(val)
