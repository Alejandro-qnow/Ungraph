"""NER smoke for integration CI (spaCy model + factory)."""

from __future__ import annotations

import pytest

from ungraph.core.configuration import Settings
from ungraph.domain.entities.chunk import Chunk


@pytest.mark.integration
def test_spacy_inference_service_factory_ner_smoke():
    pytest.importorskip("spacy")
    from ungraph.application.dependencies import create_inference_service
    from ungraph.infrastructure.services.spacy_inference_service import (
        SpacyInferenceService,
    )

    settings = Settings(inference_mode="ner")
    try:
        svc = create_inference_service(settings=settings, language="en")
    except (OSError, ImportError) as exc:
        pytest.skip(f"spaCy NER unavailable: {exc}")

    assert isinstance(svc, SpacyInferenceService)
    chunk = Chunk(
        id="ner-smoke-1",
        page_content="Apple Inc. was founded by Steve Jobs in California.",
        metadata={"filename": "smoke.md"},
    )
    facts = svc.infer_facts(chunk)
    assert isinstance(facts, list)
