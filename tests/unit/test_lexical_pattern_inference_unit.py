"""Unit: LexicalPatternInferenceService (no Neo4j / no spaCy)."""

from __future__ import annotations

import pytest

from ungraph.domain.entities.chunk import Chunk
from ungraph.infrastructure.services.lexical_pattern_inference_service import (
    EXTRACTION_METHOD,
    LexicalPatternInferenceService,
)


@pytest.mark.unit
def test_lexical_pattern_extracts_title_case_and_facts():
    svc = LexicalPatternInferenceService()
    chunk = Chunk(
        id="c1",
        page_content=(
            "Knowledge Graphs enable GraphRAG. "
            "The system uses Neo4j for storage."
        ),
        metadata={"filename": "x.md"},
    )
    ents = svc.extract_entities(chunk)
    names = {e.name for e in ents}
    assert "Knowledge Graphs" in names
    assert all(e.extraction_method == EXTRACTION_METHOD for e in ents)
    facts = svc.infer_facts(chunk, entities=ents)
    assert len(facts) == len(ents)
    assert all(f.predicate == "MENTIONS" for f in facts)
    rels = svc.extract_relations(chunk, ents)
    assert all(r.extraction_method == EXTRACTION_METHOD for r in rels)


@pytest.mark.unit
def test_lexical_pattern_empty_chunk_raises():
    svc = LexicalPatternInferenceService()
    with pytest.raises(ValueError):
        svc.extract_entities(Chunk(id="c", page_content="", metadata={}))
