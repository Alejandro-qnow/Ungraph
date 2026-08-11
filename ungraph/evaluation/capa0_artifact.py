"""
Capa 0 artifact: frozen recipe + gate Y for a reference ETI run.

Reload protocol (honest): wipe → re-ingest with pinned architecture/corpus/gold.
No Neo4j dump/restore. Same ``run_id`` is the scientific pointer; the live graph
is reconstructed from the recipe for D5 comparisons.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union

from ungraph.evaluation.experiment_run import ExperimentRun

SCHEMA = "ungraph.capa0/v1"
DEFAULT_ARTIFACT_NAME = "capa0_artifact.json"


@dataclass
class Capa0Artifact:
    """JSON-serializable Layer-0 freeze pointer."""

    run_id: str
    domain: str
    architecture: Dict[str, Any]
    corpus_paths: List[str]
    gold_path: str
    experiment_run_path: str = ""
    seed: Optional[int] = None
    git_sha: str = ""
    gate: Dict[str, Any] = field(default_factory=dict)
    graph_stats: Optional[Dict[str, Any]] = None
    schema: str = SCHEMA
    frozen_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    reload_protocol: str = "wipe_reingest_pinned"
    notes: str = ""

    def to_json_obj(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "experiment_run_path": self.experiment_run_path,
            "domain": self.domain,
            "architecture": dict(self.architecture),
            "corpus_paths": list(self.corpus_paths),
            "gold_path": self.gold_path,
            "seed": self.seed,
            "git_sha": self.git_sha,
            "gate": dict(self.gate),
            "graph_stats": dict(self.graph_stats) if self.graph_stats else None,
            "frozen_at_utc": self.frozen_at_utc,
            "reload_protocol": self.reload_protocol,
            "notes": self.notes,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_json_obj(), ensure_ascii=False, indent=2)

    @staticmethod
    def from_json_obj(data: Mapping[str, Any]) -> "Capa0Artifact":
        validate_capa0_artifact(data)
        return Capa0Artifact(
            schema=str(data.get("schema") or SCHEMA),
            run_id=str(data["run_id"]),
            experiment_run_path=str(data.get("experiment_run_path") or ""),
            domain=str(data.get("domain") or ""),
            architecture=dict(data.get("architecture") or {}),
            corpus_paths=[str(p) for p in (data.get("corpus_paths") or [])],
            gold_path=str(data.get("gold_path") or ""),
            seed=data.get("seed"),
            git_sha=str(data.get("git_sha") or ""),
            gate=dict(data.get("gate") or {}),
            graph_stats=dict(data["graph_stats"]) if data.get("graph_stats") else None,
            frozen_at_utc=str(
                data.get("frozen_at_utc")
                or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            ),
            reload_protocol=str(data.get("reload_protocol") or "wipe_reingest_pinned"),
            notes=str(data.get("notes") or ""),
        )


def validate_capa0_artifact(data: Mapping[str, Any]) -> None:
    if not isinstance(data, Mapping):
        raise ValueError("capa0 artifact must be a mapping")
    schema = str(data.get("schema") or "")
    if schema and schema != SCHEMA:
        raise ValueError(f"unsupported capa0 schema: {schema!r} (expected {SCHEMA!r})")
    if not data.get("run_id"):
        raise ValueError("capa0 artifact missing run_id")
    arch = data.get("architecture")
    if not isinstance(arch, Mapping) or not arch:
        raise ValueError("capa0 artifact missing architecture")
    if str(arch.get("inference") or "").lower() not in ("ner",):
        raise ValueError(
            "capa0 freeze expects architecture.inference='ner' "
            f"(got {arch.get('inference')!r})"
        )
    corpus = data.get("corpus_paths")
    if not isinstance(corpus, list) or not corpus:
        raise ValueError("capa0 artifact requires non-empty corpus_paths")
    if not data.get("gold_path"):
        raise ValueError("capa0 artifact missing gold_path")


def gate_metrics_from_scorecard(scorecard: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    sc = scorecard or {}
    tr = dict(sc.get("transform") or {})
    qa = dict(sc.get("rag_qa") or {})
    return {
        "entity_recall": tr.get("entity_recall"),
        "relation_pair_recall": tr.get("relation_pair_recall"),
        "evidence_coverage": tr.get("evidence_coverage"),
        "answer_correctness": qa.get("answer_correctness"),
        "n_facts": tr.get("n_facts"),
        "n_graph_entities": tr.get("n_graph_entities"),
    }


def relativize_to_domain(path: Union[str, Path], domain_dir: Path) -> str:
    p = Path(path)
    try:
        return p.resolve().relative_to(domain_dir.resolve()).as_posix()
    except ValueError:
        # already relative or outside domain
        s = str(path).replace("\\", "/")
        if s.startswith("corpus/") or s in ("gold.json",) or "/" not in s:
            return s
        name = p.name
        if name == "gold.json":
            return "gold.json"
        if "corpus" in p.parts:
            # keep corpus/<file>
            idx = list(p.parts).index("corpus")
            return "/".join(p.parts[idx:])
        return s


def resolve_under_domain(rel: str, domain_dir: Path) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p
    return (domain_dir / rel).resolve()


def build_capa0_from_experiment_run(
    run: ExperimentRun,
    *,
    domain_dir: Path,
    experiment_run_path: str = "",
    graph_stats: Optional[Mapping[str, Any]] = None,
    notes: str = "",
) -> Capa0Artifact:
    domain_dir = Path(domain_dir)
    arch = dict(run.architecture or {})
    if str(arch.get("inference") or "").lower() != "ner":
        raise ValueError(
            f"refuse to freeze non-ner run (inference={arch.get('inference')!r})"
        )
    corpus_rel = [relativize_to_domain(p, domain_dir) for p in (run.corpus_paths or [])]
    gold_rel = relativize_to_domain(run.gold_path, domain_dir) if run.gold_path else "gold.json"
    run_path = experiment_run_path or f"{run.run_id}.json"
    stats = dict(graph_stats) if graph_stats else None
    if stats is None and run.graph_stats is not None:
        stats = run.graph_stats.to_json_obj()
    return Capa0Artifact(
        run_id=run.run_id,
        experiment_run_path=run_path,
        domain=str(run.domain or domain_dir.name),
        architecture=arch,
        corpus_paths=corpus_rel,
        gold_path=gold_rel,
        seed=run.seed,
        git_sha=str(run.git_sha or ""),
        gate=gate_metrics_from_scorecard(run.scorecard),
        graph_stats=stats,
        notes=notes
        or "Capa 0 freeze: recipe + gate Y; reload=wipe→re-ingest pinned (no Neo4j dump).",
    )


def save_capa0_artifact(path: Path, artifact: Capa0Artifact) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(artifact.to_json() + "\n", encoding="utf-8")
    return path


def load_capa0_artifact(path: Path) -> Capa0Artifact:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Capa0Artifact.from_json_obj(data)


def compare_gate(
    frozen: Mapping[str, Any],
    observed: Mapping[str, Any],
    *,
    atol: float = 1e-4,
    keys: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Compare gate Y; numeric equality within atol. Missing observed → fail."""
    use = list(
        keys
        or (
            "entity_recall",
            "relation_pair_recall",
            "evidence_coverage",
            "answer_correctness",
        )
    )
    diffs: Dict[str, Any] = {}
    ok = True
    for k in use:
        a, b = frozen.get(k), observed.get(k)
        if a is None and b is None:
            continue
        if a is None or b is None:
            ok = False
            diffs[k] = {"frozen": a, "observed": b, "match": False}
            continue
        try:
            fa, fb = float(a), float(b)
            match = abs(fa - fb) <= atol
        except (TypeError, ValueError):
            match = a == b
        if not match:
            ok = False
        diffs[k] = {"frozen": a, "observed": b, "match": match}
    return {"ok": ok, "atol": atol, "diffs": diffs}


def select_ner_run(runs: Sequence[ExperimentRun]) -> ExperimentRun:
    ner = [r for r in runs if str((r.architecture or {}).get("inference")).lower() == "ner"]
    if not ner:
        raise ValueError("no ExperimentRun with architecture.inference='ner'")
    # Prefer highest entity_recall, then composite
    def _key(r: ExperimentRun) -> tuple:
        er = ((r.scorecard or {}).get("transform") or {}).get("entity_recall") or 0.0
        return (float(er), r.composite_score())

    return max(ner, key=_key)
