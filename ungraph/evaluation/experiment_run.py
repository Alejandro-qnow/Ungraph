"""
Serializable experiment runs (reproducibilidad §8 / cierre MVP medible).

Une parámetros de arquitectura, ``DomainScorecard``, stats de grafo y metadatos
de diseño DoE (``design_id`` / ``design_row_id``) en un artefacto JSON. Exporta
filas planas factores+Y para ``doekit``.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, TYPE_CHECKING

from ungraph.evaluation.graph_structural_stats import GraphStructuralStats

if TYPE_CHECKING:
    from ungraph.evaluation.scorecard import DomainScorecard


@dataclass
class ExperimentRun:
    """
    Single reproducible experiment artifact (JSON-serializable).

    Attributes:
        run_id: Unique id (default UUID4).
        created_at_utc: ISO timestamp.
        domain: Benchmark domain id (e.g. knowledge_graphs).
        architecture: Factor snapshot (chunking, inference, rag, …).
        pipeline_params: Free-form snapshot (legacy + extras).
        scorecard: Optional ``DomainScorecard`` as JSON-compatible dict.
        graph_stats: Optional structural snapshot after ingest or checkpoint.
        retrieval_metrics: Optional list of dicts (e.g. per-query DeepEval outputs).
        efficiency: Latency/tokens/cost block (also mirrored in scorecard).
        git_sha: Optional commit hash.
        seed: RNG seed used for the run/design.
        gold_path: Path to gold JSON used for evaluation.
        corpus_paths: Corpus files used for the run.
        design_id: Identifier of the DoE design table.
        design_row_id: Row index / id within that design.
        notes: Human-readable context.
    """

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    domain: str = ""
    architecture: Dict[str, Any] = field(default_factory=dict)
    pipeline_params: Dict[str, Any] = field(default_factory=dict)
    scorecard: Optional[Dict[str, Any]] = None
    graph_stats: Optional[GraphStructuralStats] = None
    retrieval_metrics: List[Dict[str, Any]] = field(default_factory=list)
    efficiency: Dict[str, Any] = field(default_factory=dict)
    git_sha: str = ""
    seed: Optional[int] = None
    gold_path: str = ""
    corpus_paths: List[str] = field(default_factory=list)
    design_id: str = ""
    design_row_id: str = ""
    notes: str = ""

    def composite_score(self) -> float:
        sc = self.scorecard or {}
        if "composite_score" in sc:
            try:
                return float(sc["composite_score"])
            except (TypeError, ValueError):
                pass
        if sc:
            from ungraph.evaluation.scorecard import DomainScorecard

            return DomainScorecard.from_json_obj(sc).composite_score()
        return 0.0

    def to_json_obj(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "run_id": self.run_id,
            "created_at_utc": self.created_at_utc,
            "domain": self.domain,
            "architecture": dict(self.architecture),
            "pipeline_params": dict(self.pipeline_params),
            "scorecard": dict(self.scorecard) if self.scorecard else None,
            "retrieval_metrics": list(self.retrieval_metrics),
            "efficiency": dict(self.efficiency),
            "git_sha": self.git_sha,
            "seed": self.seed,
            "gold_path": self.gold_path,
            "corpus_paths": list(self.corpus_paths),
            "design_id": self.design_id,
            "design_row_id": self.design_row_id,
            "notes": self.notes,
            "composite_score": self.composite_score(),
        }
        if self.graph_stats is not None:
            d["graph_stats"] = self.graph_stats.to_json_obj()
        else:
            d["graph_stats"] = None
        return d

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_json_obj(), ensure_ascii=False, indent=indent)

    def to_doe_row(self) -> Dict[str, Any]:
        """Fila plana factores + respuestas Y para pandas/doekit."""
        row: Dict[str, Any] = dict(self.architecture)
        # Prefer architecture; fill gaps from pipeline_params without overwrite.
        for k, v in (self.pipeline_params or {}).items():
            row.setdefault(k, v)
        sc = self.scorecard or {}
        for block in ("extract", "transform", "reasoning", "rag_qa", "efficiency"):
            block_data = sc.get(block) or {}
            if isinstance(block_data, dict):
                for k, v in block_data.items():
                    if isinstance(v, (int, float, bool, str)) or v is None:
                        row[k] = v
        if self.efficiency:
            for k, v in self.efficiency.items():
                row.setdefault(k, v)
        row["composite_score"] = self.composite_score()
        row["run_id"] = self.run_id
        row["design_id"] = self.design_id
        row["design_row_id"] = self.design_row_id
        row["domain"] = self.domain
        return row

    @classmethod
    def from_scorecard(
        cls,
        scorecard: "DomainScorecard",
        *,
        run_id: Optional[str] = None,
        git_sha: str = "",
        seed: Optional[int] = None,
        gold_path: str = "",
        corpus_paths: Optional[Sequence[str]] = None,
        design_id: str = "",
        design_row_id: str = "",
        graph_stats: Optional[GraphStructuralStats] = None,
        retrieval_metrics: Optional[List[Dict[str, Any]]] = None,
        pipeline_params: Optional[Dict[str, Any]] = None,
        notes: str = "",
    ) -> "ExperimentRun":
        """Build a run from a ``DomainScorecard`` (+ reproducible metadata)."""
        sc_obj = scorecard.to_json_obj()
        return cls(
            run_id=run_id or str(uuid.uuid4()),
            domain=str(scorecard.domain or ""),
            architecture=dict(scorecard.architecture or {}),
            pipeline_params=dict(pipeline_params or scorecard.architecture or {}),
            scorecard=sc_obj,
            efficiency=dict(scorecard.efficiency or {}),
            git_sha=git_sha,
            seed=seed,
            gold_path=gold_path,
            corpus_paths=list(corpus_paths or []),
            design_id=design_id,
            design_row_id=str(design_row_id),
            graph_stats=graph_stats,
            retrieval_metrics=list(retrieval_metrics or []),
            notes=notes,
        )

    @staticmethod
    def from_json_obj(data: Mapping[str, Any]) -> "ExperimentRun":
        gs_raw = data.get("graph_stats")
        gs = GraphStructuralStats.from_json_obj(gs_raw) if gs_raw else None
        sc_raw = data.get("scorecard")
        seed_raw = data.get("seed")
        seed: Optional[int]
        if seed_raw is None or seed_raw == "":
            seed = None
        else:
            seed = int(seed_raw)
        return ExperimentRun(
            run_id=str(data.get("run_id", str(uuid.uuid4()))),
            created_at_utc=str(
                data.get(
                    "created_at_utc",
                    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                )
            ),
            domain=str(data.get("domain") or ""),
            architecture=dict(data.get("architecture") or {}),
            pipeline_params=dict(data.get("pipeline_params") or {}),
            scorecard=dict(sc_raw) if isinstance(sc_raw, Mapping) else None,
            graph_stats=gs,
            retrieval_metrics=list(data.get("retrieval_metrics") or []),
            efficiency=dict(data.get("efficiency") or {}),
            git_sha=str(data.get("git_sha") or ""),
            seed=seed,
            gold_path=str(data.get("gold_path") or ""),
            corpus_paths=list(data.get("corpus_paths") or []),
            design_id=str(data.get("design_id") or ""),
            design_row_id=str(data.get("design_row_id") or ""),
            notes=str(data.get("notes") or ""),
        )

    @staticmethod
    def from_json(s: str) -> "ExperimentRun":
        return ExperimentRun.from_json_obj(json.loads(s))


def rank_experiment_runs_by_relevancy(
    runs: Sequence[ExperimentRun],
    *,
    metric_path: Sequence[str] = ("contextual_relevancy", "score"),
) -> List[tuple[float, ExperimentRun]]:
    """
    Order runs by mean score found at ``metric_path`` inside each retrieval_metrics item.

    Runs with no scores sort last (mean = -1.0). For ties, original order is preserved
    via stable sort (Python sort is stable).
    """

    def _mean_relevancy(run: ExperimentRun) -> float:
        if not run.retrieval_metrics:
            return -1.0
        scores: List[float] = []
        for item in run.retrieval_metrics:
            cur: Any = item
            try:
                for key in metric_path:
                    if cur is None or not isinstance(cur, Mapping):
                        raise KeyError
                    cur = cur[key]
                scores.append(float(cur))
            except (KeyError, TypeError, ValueError):
                continue
        if not scores:
            return -1.0
        return sum(scores) / len(scores)

    scored = [(_mean_relevancy(r), r) for r in runs]
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored


def rank_experiment_runs_by_composite_score(
    runs: Sequence[ExperimentRun],
) -> List[tuple[float, ExperimentRun]]:
    """Order runs by ``composite_score`` descending (best first)."""
    scored = [(r.composite_score(), r) for r in runs]
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored
