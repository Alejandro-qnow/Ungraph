"""Unit: suggest_chunking_strategy expone alternativas reales (no stub) y admite semantic."""

from __future__ import annotations

import pytest

import ungraph
from ungraph.utils.chunking_master import (
    ChunkingMaster,
    ChunkingStrategy,
    DocumentType,
)

pytestmark = pytest.mark.unit


_NARRATIVE = (
    "Knowledge graphs represent information as entities and relationships. "
    "Retrieval augmented generation grounds language models in external context. "
    "GraphRAG builds a graph index and community summaries for global questions. "
    "Vector search retrieves semantically similar passages for a query. "
) * 40


def test_evaluate_all_exposes_multiple_alternatives(tmp_path) -> None:
    p = tmp_path / "doc.txt"
    p.write_text(_NARRATIVE, encoding="utf-8")

    rec = ungraph.suggest_chunking_strategy(str(p), evaluate_all=True)

    # Antes: alternatives tenía siempre 1 (stub). Ahora expone todas las evaluadas.
    assert len(rec.alternatives) >= 2
    strategies = {a["strategy"] for a in rec.alternatives}
    assert rec.strategy in strategies
    # Ordenadas por score descendente.
    scores = [a["score"] for a in rec.alternatives]
    assert scores == sorted(scores, reverse=True)


def test_semantic_becomes_candidate_with_embedding_model() -> None:
    """Con embedding_model, SEMANTIC entra como candidata para texto largo."""

    class _FakeEmb:
        def embed_documents(self, texts):
            return [[float(len(t) % 7), 1.0] for t in texts]

        def embed_query(self, text):
            return [float(len(text) % 7), 1.0]

    master = ChunkingMaster(embedding_model=_FakeEmb())
    # >10000 palabras dispara la rama semántica en _select_candidate_strategies.
    structure = {"headers": 0, "structure_density": 0.1, "words": 20000}
    cands = master._select_candidate_strategies(DocumentType.NARRATIVE, structure)
    assert ChunkingStrategy.SEMANTIC in cands
