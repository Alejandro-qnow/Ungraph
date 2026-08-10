"""Sanity check for optional DeepEval extra (no API calls)."""

from __future__ import annotations

import pytest


@pytest.mark.eval
def test_deepeval_metric_import_and_callable():
    pytest.importorskip("deepeval")
    from ungraph.evaluation import evaluate_retrieval_with_deepeval

    assert callable(evaluate_retrieval_with_deepeval)
