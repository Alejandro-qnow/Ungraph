"""Unit: núcleo puro de la evaluación downstream de chunking (sin red/embeddings reales)."""

from __future__ import annotations

import numpy as np
import pytest

from ungraph.evaluation.chunking_downstream_eval import (
    RetrievalProbe,
    StrategyRetrievalScore,
    compute_retrieval_metrics,
    gold_chunk_indices,
    rank_by_mrr,
    score_chunk_sets,
)

pytestmark = pytest.mark.unit


CHUNKS = [
    "Cypher queries Neo4j property graphs",   # 0
    "TransE embeds relations as translations",  # 1
    "GraphRAG uses an LLM to build the graph",  # 2
]


def test_gold_chunk_indices_case_insensitive() -> None:
    assert gold_chunk_indices(CHUNKS, ["cypher"]) == [0]
    assert gold_chunk_indices(CHUNKS, ["TRANSE", "translations"]) == [1]
    assert gold_chunk_indices(CHUNKS, ["quantum"]) == []


def test_compute_retrieval_metrics_exact() -> None:
    # Vectores controlados: chunk0=[1,0], chunk1=[0,1], chunk2=[0.7,0.7].
    chunk_vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]])
    probes = [
        RetrievalProbe.make("what queries neo4j", ["cypher"]),         # gold {0}
        RetrievalProbe.make("relation embedding model", ["transe"]),   # gold {1}
        RetrievalProbe.make("unrelated", ["quantum"]),                 # sin cobertura
    ]
    # probe0 -> [1,0]: orden [0,2,1] => chunk0 rank 1 (hit@1)
    # probe1 -> [0.9,0.1]: sims c0=.9 c2=.7 c1=.1 => orden [0,2,1] => chunk1 rank 3 (hit@3)
    # probe2 -> irrelevante (no cubierto)
    query_vectors = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 0.0]])

    s = compute_retrieval_metrics(
        strategy="test",
        chunks=CHUNKS,
        chunk_vectors=chunk_vectors,
        probes=probes,
        query_vectors=query_vectors,
        ks=(1, 3, 5),
    )
    assert isinstance(s, StrategyRetrievalScore)
    assert s.n_chunks == 3
    assert s.probes_total == 3
    assert s.probes_covered == 2  # el probe "quantum" no es recuperable
    assert s.hit_rate[1] == pytest.approx(0.5)   # 1 de 2
    assert s.hit_rate[3] == pytest.approx(1.0)   # 2 de 2
    assert s.mrr == pytest.approx((1.0 + 1.0 / 3.0) / 2.0)  # 0.6667


def test_uncovered_probes_do_not_penalize() -> None:
    chunk_vectors = np.array([[1.0, 0.0], [0.0, 1.0]])
    probes = [RetrievalProbe.make("q", ["nothing-here"])]
    s = compute_retrieval_metrics(
        strategy="t", chunks=["a b", "c d"], chunk_vectors=chunk_vectors,
        probes=probes, query_vectors=np.array([[1.0, 0.0]]),
    )
    assert s.probes_covered == 0
    assert s.mrr == 0.0
    assert s.hit_rate[1] == 0.0


def test_score_chunk_sets_coverage_and_json() -> None:
    class _FakeEmb:
        def embed_documents(self, texts):
            return [[float(len(t)), 1.0] for t in texts]

        def embed_query(self, text):
            return [float(len(text)), 1.0]

    probes = [
        RetrievalProbe.make("q1", ["cypher"]),      # presente en set A
        RetrievalProbe.make("q2", ["absent-kw"]),   # no presente
    ]
    scores = score_chunk_sets(
        {"recursive": CHUNKS, "semantic": ["Cypher only chunk"]},
        embedder=_FakeEmb(),
        probes=probes,
    )
    by = {s.strategy: s for s in scores}
    assert by["recursive"].n_chunks == 3
    assert by["recursive"].probes_covered == 1  # solo "cypher"
    # JSON-serializable
    obj = by["recursive"].to_json_obj()
    assert obj["strategy"] == "recursive" and "hit_rate" in obj

    ranked = rank_by_mrr(scores)
    assert [s.mrr for s in ranked] == sorted([s.mrr for s in scores], reverse=True)
