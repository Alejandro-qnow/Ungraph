"""
Oleada H_chunk: variar tamaño/estrategia de chunk con Infer fijo (recipe Capa 0).

Y primarias: retrieval/tarea @ top-k (answer_correctness, hit_at_k).
Y apoyo H_T: proxies de transform (entity_recall, evidence_coverage) en las mismas celdas.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

from ungraph.evaluation.capa0_artifact import gate_metrics_from_scorecard
from ungraph.evaluation.experiment_run import ExperimentRun


def build_chunk_wave_verdict(
    runs: Sequence[ExperimentRun],
    *,
    capa0_run_id: str = "",
    fixed_inference: str = "ner",
) -> Dict[str, Any]:
    """
    Contraste descriptivo de chunk_size (y chunking) a Infer fijo.

    ``pass`` = ≥2 celdas comparadas (H_chunk ejecutable). No exige un tamaño ganador.
    """
    rows: List[Dict[str, Any]] = []
    for run in runs:
        arch = dict(run.architecture or {})
        gate = gate_metrics_from_scorecard(run.scorecard)
        extract = dict((run.scorecard or {}).get("extract") or {})
        eff = dict(run.efficiency or (run.scorecard or {}).get("efficiency") or {})
        rows.append(
            {
                "run_id": run.run_id,
                "chunking": arch.get("chunking"),
                "chunk_size": arch.get("chunk_size"),
                "chunk_overlap": arch.get("chunk_overlap"),
                "inference": arch.get("inference"),
                "n_chunks": extract.get("n_chunks"),
                "hit_at_k": extract.get("hit_at_k"),
                "gate": gate,
                "latency_s": eff.get("latency_s"),
                "composite_score": run.composite_score(),
            }
        )

    # Sort by chunk_size for readability
    rows.sort(key=lambda r: (int(r.get("chunk_size") or 0), str(r.get("chunking") or "")))

    # H_chunk: does AC or hit_at_k vary across sizes?
    ac_vals = [
        float(r["gate"]["answer_correctness"])
        for r in rows
        if r.get("gate", {}).get("answer_correctness") is not None
    ]
    hit_vals = [float(r["hit_at_k"]) for r in rows if r.get("hit_at_k") is not None]
    ac_spread = (max(ac_vals) - min(ac_vals)) if len(ac_vals) >= 2 else None
    hit_spread = (max(hit_vals) - min(hit_vals)) if len(hit_vals) >= 2 else None

    # H_T weak proxy: rank correlation not required; report pairs (entity_recall, AC)
    ht_pairs = [
        {
            "chunk_size": r.get("chunk_size"),
            "entity_recall": r["gate"].get("entity_recall"),
            "answer_correctness": r["gate"].get("answer_correctness"),
            "evidence_coverage": r["gate"].get("evidence_coverage"),
        }
        for r in rows
    ]

    status = "COMPARED" if len(rows) >= 2 else "INCOMPLETE"
    return {
        "hypothesis": ["H_chunk", "H_T"],
        "status": status,
        "capa0_run_id": capa0_run_id,
        "fixed_inference": fixed_inference,
        "n_cells": len(rows),
        "cells": rows,
        "h_chunk": {
            "answer_correctness_spread": ac_spread,
            "hit_at_k_spread": hit_spread,
            "note": (
                "Spread>0 ⇒ Y de tarea/retrieval discriminan por chunk_size; "
                "spread=0 ⇒ seed/probes demasiado fáciles (no falsar aún)."
            ),
        },
        "h_t": {
            "pairs": ht_pairs,
            "note": (
                "Pares proxy transform→QA en las mismas celdas; "
                "N pequeño — no inferir causalidad; habilita oleada DoE posterior."
            ),
        },
        "pass": status == "COMPARED",
        "note": "H_chunk/H_T ejecutables con Y reales (Neo4j + top-k); veredicto descriptivo.",
    }
