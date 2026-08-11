"""Unit tests for spaCy lexical hints addon (no spaCy runtime)."""

from __future__ import annotations

import pytest

from ungraph.utils.inference_prompt import build_spacy_lexical_hints_addon

pytestmark = pytest.mark.unit


def test_build_spacy_lexical_hints_empty() -> None:
    assert build_spacy_lexical_hints_addon([]) == ""


def test_build_spacy_lexical_hints_dedup_and_order() -> None:
    out = build_spacy_lexical_hints_addon(
        [
            ("Acme", "ORGANIZATION"),
            ("acme", "ORGANIZATION"),
            ("Bob", "PERSON"),
        ]
    )
    assert "Lexical entity candidates" in out
    assert "- Acme (ORGANIZATION)" in out
    assert "- Bob (PERSON)" in out
    assert out.count("Acme") == 1


def test_build_spacy_lexical_hints_max_items() -> None:
    pairs = [(f"E{i}", "X") for i in range(200)]
    out = build_spacy_lexical_hints_addon(pairs, max_items=3)
    assert sum(1 for line in out.splitlines() if line.startswith("- E")) == 3
