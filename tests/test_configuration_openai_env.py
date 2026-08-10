"""Settings: alias de entorno estándar OpenAI (OPENAI_API_KEY, etc.)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_openai_api_key_from_openai_env_when_ungraph_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ungraph.core.configuration import get_settings, reset_configuration

    monkeypatch.delenv("UNGRAPH_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-openai-env")
    reset_configuration()
    assert get_settings().openai_api_key == "sk-from-openai-env"
    reset_configuration()


def test_ungraph_openai_api_key_wins_over_openai_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ungraph.core.configuration import get_settings, reset_configuration

    monkeypatch.setenv("UNGRAPH_OPENAI_API_KEY", "sk-ungraph")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    reset_configuration()
    assert get_settings().openai_api_key == "sk-ungraph"
    reset_configuration()


def test_openai_model_from_openai_model_env_when_ungraph_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ungraph.core.configuration import get_settings, reset_configuration

    monkeypatch.delenv("UNGRAPH_OPENAI_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    reset_configuration()
    assert get_settings().openai_model == "gpt-4o"
    reset_configuration()


def test_ungraph_openai_model_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    from ungraph.core.configuration import get_settings, reset_configuration

    monkeypatch.setenv("UNGRAPH_OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
    reset_configuration()
    assert get_settings().openai_model == "gpt-4o-mini"
    reset_configuration()


def test_openai_model_inference_context_from_env_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ungraph.core.configuration import get_settings, reset_configuration

    monkeypatch.delenv("UNGRAPH_OPENAI_MODEL_INFERENCE_CONTEXT", raising=False)
    monkeypatch.setenv("OPENAI_MODEL_INFERENCE_CONTEXT", "gpt-4o")
    reset_configuration()
    assert get_settings().openai_model_inference_context == "gpt-4o"
    reset_configuration()


def test_openai_model_inference_domain_questions_from_env_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ungraph.core.configuration import get_settings, reset_configuration

    monkeypatch.delenv("UNGRAPH_OPENAI_MODEL_INFERENCE_DOMAIN_QUESTIONS", raising=False)
    monkeypatch.setenv("OPENAI_MODEL_INFERENCE_DOMAIN_QUESTIONS", "gpt-4.1")
    reset_configuration()
    assert get_settings().openai_model_inference_domain_questions == "gpt-4.1"
    reset_configuration()


def test_openai_model_inference_extraction_from_env_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ungraph.core.configuration import get_settings, reset_configuration

    monkeypatch.delenv("UNGRAPH_OPENAI_MODEL_INFERENCE_EXTRACTION", raising=False)
    monkeypatch.setenv("OPENAI_MODEL_INFERENCE_EXTRACTION", "gpt-4o")
    reset_configuration()
    assert get_settings().openai_model_inference_extraction == "gpt-4o"
    reset_configuration()
