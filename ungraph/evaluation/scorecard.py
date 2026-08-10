"""
Scorecard global end-to-end (benchmark ETI por dominio).

**Agrega** —no recalcula— las métricas de las evaluaciones existentes (chunking,
extracción vs gold, estructura del grafo, razonamiento, RAG/QA) en un objeto único,
JSON-serializable y comparable, y compone un ``composite_score`` (desirability) para
**rankear arquitecturas** del pipeline.

Puro: sin Neo4j/LLM/DeepEval en import-time. El runner calcula cada bloque de métricas
(que sí toca infraestructura) y se lo pasa a ``build_scorecard`` / los ``*_from_*``.

Ver ``docs/BENCHMARK_ETI_DOMAINS.md``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

# metric_path -> (weight, direction). direction +1 maximiza, -1 minimiza (se invierte).
# Solo se ponderan las métricas presentes; las ausentes se ignoran.
DEFAULT_METRIC_SPECS: Dict[str, Tuple[float, int]] = {
    "extract.chunking_quality_score": (0.5, +1),
    "transform.entity_recall": (1.0, +1),
    "transform.relation_pair_recall": (1.0, +1),
    "transform.evidence_coverage": (0.75, +1),
    "reasoning.f1": (1.5, +1),
    "reasoning.hallucination_rate": (1.5, -1),
    "reasoning.distractor_rejection_rate": (0.75, +1),
    "rag_qa.answer_correctness": (1.0, +1),
    "rag_qa.contextual_relevancy": (0.75, +1),
}


def _clip01(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return max(0.0, min(1.0, v))


def _dig(obj: Dict[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


@dataclass
class DomainScorecard:
    """Métricas agregadas de una corrida ETI end-to-end sobre un dominio+arquitectura."""

    domain: str
    architecture: Dict[str, Any] = field(default_factory=dict)
    extract: Dict[str, Any] = field(default_factory=dict)
    transform: Dict[str, Any] = field(default_factory=dict)
    reasoning: Dict[str, Any] = field(default_factory=dict)
    rag_qa: Dict[str, Any] = field(default_factory=dict)
    efficiency: Dict[str, Any] = field(default_factory=dict)

    def composite_score(
        self, specs: Optional[Dict[str, Tuple[float, int]]] = None
    ) -> float:
        """Desirability ponderada en [0, 1] sobre las métricas presentes.

        Cada métrica se recorta a [0, 1]; las de dirección −1 (p. ej.
        ``hallucination_rate``) se invierten (1 − x). Devuelve la media ponderada;
        0.0 si no hay ninguna métrica disponible.
        """
        specs = specs or DEFAULT_METRIC_SPECS
        flat = {
            "extract": self.extract,
            "transform": self.transform,
            "reasoning": self.reasoning,
            "rag_qa": self.rag_qa,
            "efficiency": self.efficiency,
        }
        num = 0.0
        den = 0.0
        for path, (weight, direction) in specs.items():
            val = _clip01(_dig(flat, path))
            if val is None:
                continue
            score = val if direction >= 0 else (1.0 - val)
            num += weight * score
            den += weight
        return round(num / den, 4) if den else 0.0

    def to_json_obj(self) -> Dict[str, Any]:
        d = asdict(self)
        d["composite_score"] = self.composite_score()
        return d

    @classmethod
    def from_json_obj(cls, data: Dict[str, Any]) -> "DomainScorecard":
        return cls(
            domain=str(data.get("domain", "")),
            architecture=dict(data.get("architecture", {})),
            extract=dict(data.get("extract", {})),
            transform=dict(data.get("transform", {})),
            reasoning=dict(data.get("reasoning", {})),
            rag_qa=dict(data.get("rag_qa", {})),
            efficiency=dict(data.get("efficiency", {})),
        )


# ------------------------------------------------------ adaptadores (no recalculan)
def transform_from_benchmark(
    inference_benchmark: Dict[str, Any], *, engine: str = "llm"
) -> Dict[str, Any]:
    """Extrae recall de extracción del output de ``run_dual_inference_benchmark``.

    ``engine`` selecciona la rama del gold (``gold_metrics.ner`` / ``.llm``).
    """
    gm = (inference_benchmark or {}).get("gold_metrics", {}) or {}
    branch = gm.get(engine) or gm.get("ner") or {}
    snap = (inference_benchmark or {}).get(engine) or (inference_benchmark or {}).get("ner") or {}
    out: Dict[str, Any] = {}
    if "entity_recall" in branch:
        out["entity_recall"] = branch["entity_recall"]
    if "relation_pair_recall" in branch:
        out["relation_pair_recall"] = branch["relation_pair_recall"]
    if isinstance(snap, dict):
        if "entity_count" in snap:
            out["n_entities"] = snap["entity_count"]
        if "relation_count" in snap:
            out["n_relations"] = snap["relation_count"]
    return out


def transform_from_structural_stats(stats_json: Dict[str, Any]) -> Dict[str, Any]:
    """n_nodes / n_rels / densidad desde ``GraphStructuralStats.to_json_obj``."""
    nodes = (stats_json or {}).get("node_counts_by_label", {}) or {}
    rels = (stats_json or {}).get("relationship_counts_by_type", {}) or {}
    n_nodes = sum(int(v) for v in nodes.values())
    n_rels = sum(int(v) for v in rels.values())
    # densidad dirigida sobre nodos (aristas / nodos·(nodos−1)); acotada a [0,1]
    density = (n_rels / (n_nodes * (n_nodes - 1))) if n_nodes > 1 else 0.0
    return {
        "n_nodes": n_nodes,
        "n_relations": n_rels,
        "density": round(min(1.0, density), 6),
    }


def reasoning_from_cognitive(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Toma las claves de razonamiento del output de ``evaluate_verifier``."""
    keys = ("f1", "hallucination_rate", "real_recall", "acceptance_precision", "distractor_rejection_rate")
    return {k: metrics[k] for k in keys if metrics and k in metrics}


def evidence_coverage_from_counts(
    *,
    n_facts: int,
    n_with_provenance: int,
) -> Dict[str, Any]:
    """Fracción de facts/rels con provenance (``provenance_ref`` / DERIVED_FROM)."""
    n_facts = int(n_facts or 0)
    n_with_provenance = int(n_with_provenance or 0)
    cov = (n_with_provenance / n_facts) if n_facts > 0 else 0.0
    return {
        "evidence_coverage": round(min(1.0, max(0.0, cov)), 4),
        "n_facts": n_facts,
        "n_with_provenance": n_with_provenance,
    }


def extract_from_chunking_downstream(score: Any) -> Dict[str, Any]:
    """Mapea ``StrategyRetrievalScore`` / dict al bloque extract (+ mrr/hit)."""
    if hasattr(score, "to_json_obj"):
        data = score.to_json_obj()
    elif isinstance(score, dict):
        data = score
    else:
        return {}
    out: Dict[str, Any] = {
        "n_chunks": data.get("n_chunks"),
        "mrr": data.get("mrr"),
        "probes_covered": data.get("probes_covered"),
        "probes_total": data.get("probes_total"),
    }
    hit = data.get("hit_rate") or {}
    if isinstance(hit, dict):
        # prefer hit@5 then hit@3 then first available
        for k in ("5", "3", "1"):
            if k in hit:
                out["hit_at_k"] = hit[k]
                break
        else:
            if hit:
                out["hit_at_k"] = next(iter(hit.values()))
    return {k: v for k, v in out.items() if v is not None}


def rag_qa_from_probe_eval(probe_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Bloque rag_qa desde ``evaluate_answer_containment`` (+ opc. DeepEval)."""
    out: Dict[str, Any] = {}
    if not probe_metrics:
        return out
    if "answer_correctness" in probe_metrics:
        out["answer_correctness"] = probe_metrics["answer_correctness"]
    if "n_probes" in probe_metrics:
        out["n_probes"] = probe_metrics["n_probes"]
    if "n_correct" in probe_metrics:
        out["n_correct"] = probe_metrics["n_correct"]
    if "contextual_relevancy" in probe_metrics:
        out["contextual_relevancy"] = probe_metrics["contextual_relevancy"]
    if "eval_mode" in probe_metrics:
        out["eval_mode"] = probe_metrics["eval_mode"]
    return out


def build_scorecard(
    domain: str,
    architecture: Dict[str, Any],
    *,
    extract: Optional[Dict[str, Any]] = None,
    transform: Optional[Dict[str, Any]] = None,
    reasoning: Optional[Dict[str, Any]] = None,
    rag_qa: Optional[Dict[str, Any]] = None,
    efficiency: Optional[Dict[str, Any]] = None,
) -> DomainScorecard:
    """Ensambla un ``DomainScorecard`` a partir de bloques de métricas ya calculados."""
    return DomainScorecard(
        domain=domain,
        architecture=dict(architecture or {}),
        extract=dict(extract or {}),
        transform=dict(transform or {}),
        reasoning=dict(reasoning or {}),
        rag_qa=dict(rag_qa or {}),
        efficiency=dict(efficiency or {}),
    )


def rank_scorecards(
    cards: Iterable[DomainScorecard],
    *,
    specs: Optional[Dict[str, Tuple[float, int]]] = None,
) -> List[DomainScorecard]:
    """Ordena arquitecturas por ``composite_score`` descendente (mejor primero)."""
    return sorted(cards, key=lambda c: c.composite_score(specs), reverse=True)
