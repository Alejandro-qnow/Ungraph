"""Parsing de JSON en salidas de modelo."""

from __future__ import annotations

import pytest

from ungraph.utils.llm_json import parse_llm_json_object, strip_code_fences

pytestmark = pytest.mark.unit


def test_strip_code_fences_json() -> None:
    raw = '```json\n{"a": 1}\n```'
    assert strip_code_fences(raw) == '{"a": 1}'


def test_parse_llm_json_object() -> None:
    assert parse_llm_json_object('{"x": "y"}') == {"x": "y"}
