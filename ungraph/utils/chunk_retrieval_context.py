"""
Utilidades para texto de recuperación / contexto LLM derivado de chunks semánticos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ungraph.domain.entities.chunk import Chunk
    from ungraph.domain.services.context_optimization_service import ContextOptimizationService


def apply_retrieval_optimization_to_chunks(
    chunks: list["Chunk"],
    optimizer: "ContextOptimizationService",
    strategy_name: str = "heuristic_v1",
) -> None:
    """
    Rellena ``retrieval_optimized_text`` en cada chunk sin modificar ``page_content``.

    Si la optimización devuelve cadena vacía, no se establece vista de recuperación.
    """
    for c in chunks:
        opt = optimizer.optimize(c.page_content, c.metadata)
        if opt and opt.strip():
            c.retrieval_optimized_text = opt.strip()
            c.retrieval_optimization_strategy = strategy_name
            c.retrieval_token_estimate = optimizer.estimate_tokens(opt.strip())
