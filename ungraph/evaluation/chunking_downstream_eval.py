"""
Evaluación DOWNSTREAM de estrategias de chunking (efecto en retrieval).

La calidad de una estrategia de chunking NO se mide bien de forma intrínseca
(tamaño/uniformidad) ni por coherencia de embeddings (confundida por el tamaño de
chunk). Se mide por su **efecto aguas abajo**: aquí, la recuperación de la respuesta
(``answer-containment@k`` + MRR) sobre un conjunto de ``RetrievalProbe`` con
palabras-respuesta conocidas. Es la "R" de GraphRAG.

Diseño:
- Núcleo PURO y testeable (``compute_retrieval_metrics``): opera sobre vectores ya
  calculados; sin embeddings, sin red, sin chunking.
- Orquestación (``score_chunk_sets`` / ``evaluate_chunking_downstream``): calcula
  embeddings con un ``embedder`` inyectado y (opcionalmente) trocea con
  ``ChunkingMaster``. Infra lazy: nada de sentence-transformers en import-time.

Ver ``article/ETI/EXTRACT-TRANSFORM-INFER.md`` (¿cómo mido el chunking?).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class RetrievalProbe:
    """Pregunta con palabras-respuesta esperadas (cualquiera presente = acierto)."""

    query: str
    answer_keywords: Tuple[str, ...]

    @classmethod
    def make(cls, query: str, keywords: Sequence[str]) -> "RetrievalProbe":
        return cls(query=query, answer_keywords=tuple(keywords))


@dataclass
class StrategyRetrievalScore:
    """Métricas de retrieval de UNA estrategia de chunking."""

    strategy: str
    n_chunks: int
    probes_total: int
    probes_covered: int  # probes cuya respuesta existe en algún chunk de esta estrategia
    hit_rate: Dict[int, float] = field(default_factory=dict)  # k -> fracción con acierto@k
    mrr: float = 0.0

    def to_json_obj(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "n_chunks": self.n_chunks,
            "probes_total": self.probes_total,
            "probes_covered": self.probes_covered,
            "hit_rate": {str(k): round(v, 4) for k, v in sorted(self.hit_rate.items())},
            "mrr": round(self.mrr, 4),
        }


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    mat = np.asarray(mat, dtype=np.float32)
    if mat.ndim == 1:
        mat = mat[None, :]
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def gold_chunk_indices(chunk_texts: Sequence[str], keywords: Sequence[str]) -> List[int]:
    """Índices de chunks que contienen alguna palabra-respuesta (case-insensitive)."""
    kws = [k.lower() for k in keywords if k]
    out: List[int] = []
    for i, c in enumerate(chunk_texts):
        cl = (c or "").lower()
        if any(k in cl for k in kws):
            out.append(i)
    return out


def compute_retrieval_metrics(
    *,
    strategy: str,
    chunks: Sequence[str],
    chunk_vectors: np.ndarray,
    probes: Sequence[RetrievalProbe],
    query_vectors: np.ndarray,
    ks: Tuple[int, ...] = (1, 3, 5),
) -> StrategyRetrievalScore:
    """
    Núcleo PURO. Rankea chunks por similitud coseno a cada probe y mide si un chunk
    con la respuesta cae en el top-k (``hit@k``) y su rango recíproco (MRR).

    ``chunk_vectors`` (n_chunks, d) y ``query_vectors`` (n_probes, d) alineado con
    ``probes``. Se normalizan L2 internamente (coseno = producto punto). Los probes cuya
    respuesta NO aparece en ningún chunk se excluyen (no penalizan; se reportan como
    cobertura), porque no son recuperables por definición.
    """
    cv = _l2_normalize(chunk_vectors)
    qv = _l2_normalize(query_vectors)
    chunk_texts = list(chunks)

    hit_counts: Dict[int, int] = {k: 0 for k in ks}
    rr_sum = 0.0
    covered = 0
    for i, probe in enumerate(probes):
        gold = set(gold_chunk_indices(chunk_texts, probe.answer_keywords))
        if not gold:
            continue
        covered += 1
        sims = cv @ qv[i]
        order = np.argsort(-sims)  # índices de chunk por similitud desc
        # rango (1-indexado) del primer chunk-oro recuperado
        best_rank = next(
            (rank for rank, idx in enumerate(order, start=1) if int(idx) in gold),
            len(order) + 1,
        )
        for k in ks:
            if best_rank <= k:
                hit_counts[k] += 1
        rr_sum += 1.0 / best_rank

    denom = covered or 1
    return StrategyRetrievalScore(
        strategy=strategy,
        n_chunks=len(chunk_texts),
        probes_total=len(probes),
        probes_covered=covered,
        hit_rate={k: hit_counts[k] / denom for k in ks},
        mrr=(rr_sum / denom) if covered else 0.0,
    )


def score_chunk_sets(
    chunk_sets: Mapping[str, Sequence[str]],
    *,
    embedder: Any,
    probes: Sequence[RetrievalProbe],
    ks: Tuple[int, ...] = (1, 3, 5),
) -> List[StrategyRetrievalScore]:
    """
    Calcula ``StrategyRetrievalScore`` para cada conjunto de chunks (por estrategia).

    ``embedder`` debe exponer ``embed_documents(list[str]) -> list[list[float]]`` y
    ``embed_query(str) -> list[float]`` (interfaz LangChain Embeddings). Desacoplado del
    chunking: se le pasan los chunks ya troceados.
    """
    query_vecs = np.asarray([embedder.embed_query(p.query) for p in probes], dtype=np.float32)
    scores: List[StrategyRetrievalScore] = []
    for name, chunks in chunk_sets.items():
        chunk_list = [c for c in chunks if (c or "").strip()]
        if not chunk_list:
            scores.append(
                StrategyRetrievalScore(
                    strategy=name, n_chunks=0, probes_total=len(probes), probes_covered=0
                )
            )
            continue
        cvecs = np.asarray(embedder.embed_documents(chunk_list), dtype=np.float32)
        scores.append(
            compute_retrieval_metrics(
                strategy=name,
                chunks=chunk_list,
                chunk_vectors=cvecs,
                probes=probes,
                query_vectors=query_vecs,
                ks=ks,
            )
        )
    return scores


def chunk_text_with_strategies(
    text: str,
    strategies: Sequence[str],
    *,
    embedding_model: Any = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    semantic_breakpoint: int = 95,
) -> Dict[str, List[str]]:
    """
    Trocea ``text`` con cada estrategia (reutiliza ``ChunkingMaster``). Devuelve
    ``{estrategia: [chunks]}``. ``semantic`` requiere ``embedding_model``.
    """
    from ungraph.utils.chunking_master import ChunkingMaster, ChunkingStrategy

    master = ChunkingMaster(embedding_model=embedding_model)
    out: Dict[str, List[str]] = {}
    for name in strategies:
        strat = ChunkingStrategy(name)
        kw = {"breakpoint_threshold": semantic_breakpoint} if strat == ChunkingStrategy.SEMANTIC else {}
        splitter = master._create_splitter(strat, chunk_size, chunk_overlap, **kw)
        out[name] = list(splitter.split_text(text))
    return out


def evaluate_chunking_downstream(
    text: str,
    *,
    embedder: Any,
    probes: Sequence[RetrievalProbe],
    strategies: Sequence[str] = ("recursive", "semantic"),
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    semantic_breakpoint: int = 95,
    ks: Tuple[int, ...] = (1, 3, 5),
) -> List[StrategyRetrievalScore]:
    """Conveniencia end-to-end: trocea con cada estrategia y mide retrieval.

    ``embedder`` sirve para chunking semántico (si se pide) y para el retrieval.
    """
    chunk_sets = chunk_text_with_strategies(
        text,
        strategies,
        embedding_model=embedder,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        semantic_breakpoint=semantic_breakpoint,
    )
    return score_chunk_sets(chunk_sets, embedder=embedder, probes=probes, ks=ks)


def rank_by_mrr(scores: Sequence[StrategyRetrievalScore]) -> List[StrategyRetrievalScore]:
    """Ordena estrategias por MRR descendente (mejor retrieval primero)."""
    return sorted(scores, key=lambda s: s.mrr, reverse=True)
