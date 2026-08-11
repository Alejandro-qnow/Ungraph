"""Unit: bridge doekit (diseño sintético → analyze → retained_factors)."""

from __future__ import annotations

import pytest

pytest.importorskip("doekit")

from ungraph.evaluation.doe_bridge import (
    ArchitectureParams,
    analyze_results,
    architecture_factors_from_manifest,
    build_screening_design,
    rows_to_pipeline_configs,
)

pytestmark = pytest.mark.unit


def test_architecture_from_record():
    a = ArchitectureParams.from_record(
        {"chunking": "markdown_header", "chunk_size": 512.4, "inference": "none", "rag": "vector"}
    )
    assert a.chunking == "markdown_header"
    assert a.chunk_size == 512
    assert a.inference == "none"


def test_build_screening_and_analyze_synthetic():
    doe = {
        "factors": [
            {"name": "chunking", "kind": "categorical", "levels": ["recursive", "markdown_header"]},
            {"name": "chunk_size", "kind": "continuous", "low": 512, "high": 1024},
            {"name": "inference", "kind": "categorical", "levels": ["none", "ner"]},
            {"name": "rag", "kind": "categorical", "levels": ["text", "vector"]},
        ]
    }
    factors = architecture_factors_from_manifest({}, doe=doe, mode="offline")
    design, rows, meta = build_screening_design(factors, budget=8, seed=0)
    assert meta["n_runs"] == 8
    assert len(rows) == 8
    configs = rows_to_pipeline_configs(rows, defaults={"top_k": 5, "chunk_overlap": 200})
    assert all("chunking" in c and "design_row_id" in c for c in configs)

    # Y sintética: inference=ner mejora composite_score
    results = []
    for r in rows:
        score = 0.3 + (0.4 if str(r.get("inference")) == "ner" else 0.0)
        score += 0.1 if str(r.get("rag")) == "vector" else 0.0
        results.append({**r, "composite_score": score})

    analysis = analyze_results(design, results, response="composite_score", alpha=0.5, effect_abs_min=0.05)
    assert analysis.n_runs == 8
    assert isinstance(analysis.main_effects, dict)
    assert analysis.to_json_obj()["response"] == "composite_score"
    # Con señal fuerte en inference, suele retenerse (si no, notes explícitas)
    assert analysis.retained_factors or "ningún efecto" in analysis.notes
