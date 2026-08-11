"""
Oleada-3: comparar ≥2 familias Infer bajo las mismas Y de capa B.

No es un ranking de “mejor modelo”; es un contraste falsable sobre recipe Capa 0.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from ungraph.evaluation.capa0_artifact import gate_metrics_from_scorecard
from ungraph.evaluation.experiment_run import ExperimentRun


FAMILY_LABELS = {
    "ner": "transductive_ner",
    "pattern": "symbolic_lexical",
    "llm": "neural_llm",
    "none": "et_control",
}


def build_family_wave_verdict(
    runs: Sequence[ExperimentRun],
    *,
    capa0_run_id: str = "",
    families: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Verdict JSON: Y por familia + deltas vs baseline ``ner`` si existe.

    ``status``:
      - ``COMPARED`` si ≥2 familias con scorecard
      - ``INCOMPLETE`` si faltan corridas
    """
    by_inf: Dict[str, ExperimentRun] = {}
    for r in runs:
        inf = str((r.architecture or {}).get("inference") or "").lower()
        if inf:
            by_inf[inf] = r

    wanted = [str(f).lower() for f in (families or list(by_inf.keys()))]
    rows: List[Dict[str, Any]] = []
    for fam in wanted:
        run = by_inf.get(fam)
        if run is None:
            rows.append({"inference": fam, "missing": True})
            continue
        gate = gate_metrics_from_scorecard(run.scorecard)
        eff = dict(run.efficiency or (run.scorecard or {}).get("efficiency") or {})
        rows.append(
            {
                "inference": fam,
                "family": FAMILY_LABELS.get(fam, fam),
                "run_id": run.run_id,
                "missing": False,
                "gate": gate,
                "latency_s": eff.get("latency_s"),
                "composite_score": run.composite_score(),
            }
        )

    present = [r for r in rows if not r.get("missing")]
    status = "COMPARED" if len(present) >= 2 else "INCOMPLETE"

    baseline = next((r for r in present if r["inference"] == "ner"), present[0] if present else None)
    deltas: Dict[str, Any] = {}
    if baseline is not None:
        b_gate = baseline["gate"]
        for r in present:
            if r["inference"] == baseline["inference"]:
                continue
            d: Dict[str, Any] = {}
            for k in (
                "entity_recall",
                "relation_pair_recall",
                "evidence_coverage",
                "answer_correctness",
            ):
                a, b = b_gate.get(k), r["gate"].get(k)
                if a is None or b is None:
                    d[k] = None
                else:
                    try:
                        d[k] = round(float(b) - float(a), 4)
                    except (TypeError, ValueError):
                        d[k] = None
            deltas[r["inference"]] = {
                "vs": baseline["inference"],
                "delta": d,
            }

    # Scientific note: D5 does not require pattern > ner; it requires comparable Y
    note = (
        "Oleada-3: ≥2 familias Infer sobre recipe Capa 0; "
        "deltas vs ner son descriptivos (no gate de superioridad)."
    )
    return {
        "hypothesis": "oleada-3_infer_families",
        "status": status,
        "capa0_run_id": capa0_run_id,
        "n_families": len(present),
        "families": rows,
        "deltas_vs_baseline": deltas,
        "pass": status == "COMPARED",
        "note": note,
    }
