"""Composition root must honor configure()/get_settings() singleton."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ungraph.core.configuration import configure, get_settings, reset_configuration
from ungraph.infrastructure.services.lexical_pattern_inference_service import (
    LexicalPatternInferenceService,
)


@pytest.fixture(autouse=True)
def _reset_settings():
    reset_configuration()
    yield
    reset_configuration()


@pytest.mark.unit
def test_create_inference_service_uses_configured_singleton():
    from ungraph.application.dependencies import create_inference_service

    configure(inference_mode="pattern")
    svc = create_inference_service()
    assert isinstance(svc, LexicalPatternInferenceService)


@pytest.mark.unit
def test_create_ingest_use_case_uses_configured_inference_mode():
    from ungraph.application.dependencies import create_ingest_document_use_case

    configure(inference_mode="pattern")
    with (
        patch(
            "ungraph.application.dependencies.Neo4jChunkRepository",
            return_value=MagicMock(),
        ),
        patch(
            "ungraph.application.dependencies.Neo4jIndexService",
            return_value=MagicMock(),
        ),
        patch(
            "ungraph.application.dependencies.Neo4jCatalogRepository",
            return_value=MagicMock(),
        ),
        patch(
            "ungraph.application.dependencies.HuggingFaceEmbeddingService",
            return_value=MagicMock(),
        ),
    ):
        use_case = create_ingest_document_use_case()
    assert isinstance(use_case.inference_service, LexicalPatternInferenceService)


@pytest.mark.unit
def test_public_ingest_document_passes_settings_to_factory(tmp_path: Path):
    import ungraph

    configure(inference_mode="pattern")
    doc = tmp_path / "doc.md"
    doc.write_text("# Hello\n\nWorld.\n", encoding="utf-8")

    captured: dict = {}
    fake_uc = MagicMock()
    fake_uc.execute.return_value = []
    fake_uc.chunk_repository = MagicMock()
    fake_uc.index_service = MagicMock()

    def _factory(*, settings=None, database="neo4j", embedding_model=None, **_kwargs):
        captured["settings"] = settings
        captured["database"] = database
        captured["embedding_model"] = embedding_model
        return fake_uc

    with patch(
        "ungraph.application.dependencies.create_ingest_document_use_case",
        side_effect=_factory,
    ):
        ungraph.ingest_document(doc)

    assert captured["settings"] is get_settings()
    assert captured["settings"].inference_mode == "pattern"
    fake_uc.execute.assert_called_once()
