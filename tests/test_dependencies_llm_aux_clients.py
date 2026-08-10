"""ChatOpenAI auxiliar: uno o dos clientes según modelos resueltos."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_llm_inference_bundle_one_client_when_models_equal(mocker) -> None:
    from ungraph.application.dependencies import _llm_inference_context_bundle
    from ungraph.core.configuration import Settings

    ctor = mocker.MagicMock(side_effect=lambda **kw: mocker.MagicMock(name=kw.get("model")))
    mocker.patch("langchain_openai.ChatOpenAI", ctor)
    s = Settings(
        openai_api_key="sk-unit-test",
        inference_enrich_context_with_llm=True,
        openai_model_inference_context="same-model",
        openai_model_inference_domain_questions="same-model",
    )
    _llm_inference_context_bundle(s)
    assert ctor.call_count == 1


def test_llm_inference_bundle_two_clients_when_models_differ(mocker) -> None:
    from ungraph.application.dependencies import _llm_inference_context_bundle
    from ungraph.core.configuration import Settings

    ctor = mocker.MagicMock(side_effect=lambda **kw: mocker.MagicMock(name=kw.get("model")))
    mocker.patch("langchain_openai.ChatOpenAI", ctor)
    s = Settings(
        openai_api_key="sk-unit-test",
        inference_enrich_context_with_llm=True,
        openai_model_inference_context="model-a",
        openai_model_inference_domain_questions="model-b",
    )
    _llm_inference_context_bundle(s)
    assert ctor.call_count == 2
    models = [c.kwargs.get("model") for c in ctor.call_args_list]
    assert models == ["model-a", "model-b"]
