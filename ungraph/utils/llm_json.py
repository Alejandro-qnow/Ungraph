"""Helpers to parse JSON often returned by chat models (incl. fences)."""

from __future__ import annotations

import json
from typing import Any


def strip_code_fences(text: str) -> str:
    s = (text or "").strip()
    if not s.startswith("```"):
        return s
    lines = s.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_llm_json_object(content: str) -> dict[str, Any]:
    """Parse a single JSON object from model output; raises JSONDecodeError on failure."""
    return json.loads(strip_code_fences(content))
