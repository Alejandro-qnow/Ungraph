"""Conditional checks for OpenAI LLM inference wiring (no network unless env set)."""

from __future__ import annotations

import os

import pytest

from ungraph.application.dependencies import create_inference_service, create_llm_inference_openai
from ungraph.core.configuration import Settings, reset_configuration


@pytest.mark.unit
def test_create_llm_inference_openai_none_without_key(monkeypatch):
    for k in (
        "OPENAI_API_KEY",
        "UNGRAPH_OPENAI_API_KEY",
        "OPENAI_MODEL",
        "UNGRAPH_OPENAI_MODEL",
        "OPENAI_BASE_URL",
        "UNGRAPH_OPENAI_BASE_URL",
    ):
        monkeypatch.delenv(k, raising=False)
    reset_configuration()
    s = Settings()
    assert s.openai_api_key is None
    assert create_llm_inference_openai(s) is None


@pytest.mark.openai
def test_create_llm_inference_openai_with_key():
    key = os.environ.get("UNGRAPH_OPENAI_API_KEY")
    if not key:
        pytest.skip("UNGRAPH_OPENAI_API_KEY not set")

    reset_configuration()
    s = Settings(openai_api_key=key, inference_mode="llm")
    inf = create_llm_inference_openai(s)
    assert inf is not None


@pytest.mark.unit
def test_inference_mode_llm_with_openai_key(monkeypatch):
    """LLM path builds when an OpenAI key is available."""
    reset_configuration()
    monkeypatch.setenv("UNGRAPH_OPENAI_API_KEY", "sk-dummy-key-for-construct-only")
    monkeypatch.setenv("UNGRAPH_INFERENCE_MODE", "llm")
    monkeypatch.delenv("UNGRAPH_OLLAMA_MODEL", raising=False)
    s = Settings()
    assert s.inference_mode == "llm"
    inf = create_inference_service(s)
    assert inf is not None
