"""
Presupuesto de modelos LLM para el pipeline de inferencia en varios pasos.
"""

from __future__ import annotations

from enum import Enum


class InferenceModelBudget(str, Enum):
    """Política de coste/calidad para resumen, preguntas de dominio y extracción."""

    ECONOMY = "economy"
    BALANCED = "balanced"
    QUALITY = "quality"
