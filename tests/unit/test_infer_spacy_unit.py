"""Unit-level inference tests (spaCy optional)."""

from __future__ import annotations

import pytest

from ungraph.domain.entities.chunk import Chunk
from ungraph.infrastructure.services.spacy_inference_service import (
    SpacyInferenceService,
    _is_noise_entity_span,
    _normalize_markdown_for_ner,
)


@pytest.mark.unit
def test_normalize_markdown_for_ner_strips_heading_marks() -> None:
    raw = "## Reference Docs\n\n### Community forum\nLangChain and LangGraph."
    out = _normalize_markdown_for_ner(raw)
    assert "##" not in out
    assert "###" not in out
    assert "Community forum" in out
    assert "LangChain" in out


@pytest.mark.unit
def test_is_noise_entity_span() -> None:
    assert _is_noise_entity_span("###")
    assert _is_noise_entity_span("#")
    assert _is_noise_entity_span("a")
    assert _is_noise_entity_span("ab") is False
    assert _is_noise_entity_span("LangChain") is False


@pytest.mark.unit
def test_spacy_infer_facts_finds_entity():
    pytest.importorskip("spacy")
    try:
        svc = SpacyInferenceService("en_core_web_sm")
    except OSError:
        pytest.skip("Run: python -m spacy download en_core_web_sm")

    chunk = Chunk(
        id="unit-chunk-1",
        page_content="Apple Inc. is headquartered in Cupertino.",
        metadata={"filename": "x.md", "page_number": 1},
    )
    facts = svc.infer_facts(chunk)
    objs = [f.object for f in facts]
    assert any("Apple" in o for o in objs) or len(facts) > 0
    apple_fact = next((f for f in facts if "Apple" in f.object), None)
    if apple_fact is not None:
        assert apple_fact.object_entity_type == "ORGANIZATION"


@pytest.mark.unit
def test_spacy_infer_outline_avoids_hash_only_objects():
    pytest.importorskip("spacy")
    try:
        svc = SpacyInferenceService("en_core_web_sm")
    except OSError:
        pytest.skip("Run: python -m spacy download en_core_web_sm")

    chunk = Chunk(
        id="unit-chunk-md",
        page_content=(
            "# Reference Docs\n\n"
            "### Community forum\n\n"
            "LangChain and LangGraph are frameworks.\n"
        ),
        metadata={"filename": "page.md", "page_number": 1},
    )
    facts = svc.infer_facts(chunk)
    assert not any(f.object.strip() in {"#", "##", "###"} for f in facts)
    assert not any(f.object.strip() == "###" for f in facts)
