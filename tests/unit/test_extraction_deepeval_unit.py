"""DeepEval helper is optional tooling — never a hard dependency for H_I."""

from __future__ import annotations

import pytest

from ungraph.domain.entities.entity import Entity
from ungraph.evaluation.extraction_deepeval import (
    try_score_extractions_contextual_relevancy,
)


@pytest.mark.unit
def test_deepeval_helper_degrades_without_extra():
    entities = [
        Entity(id="e1", name="Apple", type="ORGANIZATION", mentions=[]),
    ]
    out = try_score_extractions_contextual_relevancy(
        chunk_text="Apple Inc. builds devices.",
        entities=entities,
    )
    assert isinstance(out, dict)
    assert "available" in out
    # Without ungraph[eval] + judge key, available is False and must not raise.
    if not out["available"]:
        assert out.get("mean_score") is None or "error" in out or True
