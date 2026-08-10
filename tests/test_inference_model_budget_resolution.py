"""Resolución de modelos OpenAI para inferencia (extracción, contexto, preguntas)."""

from __future__ import annotations

import pytest

from ungraph.core.configuration import (
    Settings,
    resolve_openai_model_for_inference_domain_questions,
    resolve_openai_model_for_inference_extraction,
    resolve_openai_model_for_inference_context,
)

pytestmark = pytest.mark.unit


def test_extraction_override_wins_over_budget() -> None:
    s = Settings(
        openai_model_inference_extraction="custom-model",
        inference_model_budget="economy",
        openai_model="gpt-4o",
    )
    assert resolve_openai_model_for_inference_extraction(s) == "custom-model"


def test_economy_forces_gpt_4o_mini() -> None:
    s = Settings(openai_model="gpt-4o", inference_model_budget="economy")
    assert resolve_openai_model_for_inference_extraction(s) == "gpt-4o-mini"


def test_balanced_uses_openai_model() -> None:
    s = Settings(openai_model="gpt-4.1", inference_model_budget="balanced")
    assert resolve_openai_model_for_inference_extraction(s) == "gpt-4.1"


def test_quality_upgrades_mini_to_gpt_4o() -> None:
    s = Settings(openai_model="gpt-4o-mini", inference_model_budget="quality")
    assert resolve_openai_model_for_inference_extraction(s) == "gpt-4o"


def test_quality_keeps_non_mini_model() -> None:
    s = Settings(openai_model="gpt-4.1", inference_model_budget="quality")
    assert resolve_openai_model_for_inference_extraction(s) == "gpt-4.1"


def test_context_aux_stays_mini_for_balanced() -> None:
    s = Settings(openai_model="gpt-4o", inference_model_budget="balanced")
    assert resolve_openai_model_for_inference_context(s) == "gpt-4o-mini"


def test_context_aux_override() -> None:
    s = Settings(
        openai_model_inference_context="gpt-4.1",
        inference_model_budget="economy",
        openai_model="gpt-4o-mini",
    )
    assert resolve_openai_model_for_inference_context(s) == "gpt-4.1"


def test_context_aux_quality_upgrades_mini() -> None:
    s = Settings(openai_model="gpt-4o-mini", inference_model_budget="quality")
    assert resolve_openai_model_for_inference_context(s) == "gpt-4o"


def test_domain_questions_matches_context_when_unset() -> None:
    s = Settings(openai_model="gpt-4o-mini", inference_model_budget="quality")
    assert resolve_openai_model_for_inference_domain_questions(s) == "gpt-4o"


def test_domain_questions_override() -> None:
    s = Settings(
        openai_model_inference_domain_questions="cheap-model",
        openai_model_inference_context="gpt-4.1",
        inference_model_budget="balanced",
        openai_model="gpt-4o-mini",
    )
    assert resolve_openai_model_for_inference_context(s) == "gpt-4.1"
    assert resolve_openai_model_for_inference_domain_questions(s) == "cheap-model"
