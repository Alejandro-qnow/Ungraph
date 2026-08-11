"""Tests for retrieval-optimized chunk text and token estimates."""

from ungraph.domain.entities.chunk import Chunk
from ungraph.infrastructure.services.heuristic_context_optimization_service import (
    HeuristicContextOptimizationService,
)
from ungraph.utils.chunk_retrieval_context import apply_retrieval_optimization_to_chunks


def test_apply_retrieval_optimization_sets_text_strategy_and_tokens():
    opt = HeuristicContextOptimizationService()
    chunks = [
        Chunk(
            id="c1",
            page_content="Hello   world\n\n\n\nfoo",
            metadata={"filename": "x.txt", "page_number": 1},
        )
    ]
    apply_retrieval_optimization_to_chunks(chunks, opt)
    assert chunks[0].retrieval_optimized_text == "Hello world\n\nfoo"
    assert chunks[0].retrieval_optimization_strategy == "heuristic_v1"
    assert chunks[0].retrieval_token_estimate == opt.estimate_tokens(
        chunks[0].retrieval_optimized_text or ""
    )
