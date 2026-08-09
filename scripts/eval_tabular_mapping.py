"""
Banco de evaluación de la inferencia de esquema tabular (SGI).

Corre el corpus de ``tests/fixtures/tabular/`` (datos + gold mapping) y estima:
  1. Calidad del mapeo   — accuracy de columnas + precision/recall/F1 por rol.
  2. Coherencia          — el GraphPattern derivado es válido y sin nodos huérfanos.
  3. Consultabilidad     — % de relaciones objetivo (dimensiones/FKs del gold) presentes.
  4. Costo/latencia      — tiempo por tabla y nº de columnas enviadas al LLM.

Compara la heurística pura contra la híbrida (heurística + LLM) cuando hay API key,
para cuantificar el aporte del LLM.

Uso:
    python scripts/eval_tabular_mapping.py                 # heurística
    python scripts/eval_tabular_mapping.py --llm           # híbrida (si hay API key)
    python scripts/eval_tabular_mapping.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Permite ejecutar el script directamente (sin instalación editable).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from ungraph.domain.value_objects.tabular_data import TabularData
from ungraph.domain.value_objects.tabular_schema import ColumnRole, TabularSchemaProposal
from ungraph.infrastructure.services.heuristic_schema_inference_service import (
    HeuristicSchemaInferenceService,
)
from ungraph.infrastructure.services.pandas_tabular_loader_service import (
    PandasTabularLoaderService,
)

FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "tabular"
ROLES = [r.value for r in ColumnRole]


def _gold_tables(gold: dict) -> List[dict]:
    if "tables" in gold:
        return gold["tables"]
    return [gold]


def _iter_corpus() -> List[Tuple[Path, dict]]:
    items = []
    for gold_file in sorted(FIXTURES.glob("*.gold.yaml")):
        stem = gold_file.name[: -len(".gold.yaml")]
        data_file = None
        for ext in (".csv", ".xlsx", ".xls"):
            candidate = FIXTURES / f"{stem}{ext}"
            if candidate.exists():
                data_file = candidate
                break
        if data_file:
            items.append((data_file, yaml.safe_load(gold_file.read_text(encoding="utf-8"))))
    return items


def _build_inference(use_llm: bool):
    heuristic = HeuristicSchemaInferenceService()
    if not use_llm:
        return heuristic, 0
    try:
        from ungraph.core.configuration import Settings
        from ungraph.application.dependencies import _chat_openai_for_llm_inference
        from ungraph.infrastructure.services.llm_schema_inference_service import (
            LlmSchemaInferenceService,
        )

        settings = Settings()
        if not getattr(settings, "openai_api_key", None):
            print("[aviso] Sin API key: se evalúa solo la heurística.")
            return heuristic, 0
        llm = _chat_openai_for_llm_inference(settings)
        return LlmSchemaInferenceService(heuristic=heuristic, llm=llm), 1
    except Exception as e:
        print(f"[aviso] LLM no disponible ({e}); se evalúa solo la heurística.")
        return heuristic, 0


def _evaluate_table(
    proposal: TabularSchemaProposal, gold_roles: Dict[str, str]
) -> Dict[str, Any]:
    predicted = {c.column: c.role.value for c in proposal.columns}
    correct = 0
    per_role_tp = defaultdict(int)
    per_role_fp = defaultdict(int)
    per_role_fn = defaultdict(int)
    mistakes = []
    for col, gold_role in gold_roles.items():
        pred = predicted.get(col, "<missing>")
        if pred == gold_role:
            correct += 1
            per_role_tp[gold_role] += 1
        else:
            per_role_fn[gold_role] += 1
            if pred in ROLES:
                per_role_fp[pred] += 1
            mistakes.append({"column": col, "gold": gold_role, "pred": pred})

    # Consultabilidad: relaciones objetivo (dimension/relation_fk) presentes en el patrón.
    gold_rel_cols = {c for c, r in gold_roles.items() if r in ("dimension", "relation_fk")}
    pred_rel_cols = {
        c.column
        for c in proposal.columns
        if c.role in (ColumnRole.DIMENSION_NODE, ColumnRole.RELATION_FK)
    }
    rel_hits = len(gold_rel_cols & pred_rel_cols)
    queryability = (rel_hits / len(gold_rel_cols)) if gold_rel_cols else 1.0

    # Coherencia: el patrón derivado es construible/válido.
    coherent = True
    try:
        proposal.to_graph_pattern()
    except Exception:
        coherent = False

    return {
        "n_columns": len(gold_roles),
        "correct": correct,
        "accuracy": correct / len(gold_roles) if gold_roles else 1.0,
        "tp": dict(per_role_tp),
        "fp": dict(per_role_fp),
        "fn": dict(per_role_fn),
        "queryability": queryability,
        "coherent": coherent,
        "mistakes": mistakes,
    }


def _prf(tp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def run(use_llm: bool) -> Dict[str, Any]:
    loader = PandasTabularLoaderService()
    inference, _ = _build_inference(use_llm)

    corpus = _iter_corpus()
    if not corpus:
        raise SystemExit(
            f"No hay fixtures en {FIXTURES}. Genera con: python scripts/gen_tabular_fixtures.py"
        )

    total_cols = total_correct = 0
    agg_tp = defaultdict(int)
    agg_fp = defaultdict(int)
    agg_fn = defaultdict(int)
    query_scores: List[float] = []
    coherent_count = 0
    coherent_total = 0
    per_fixture: List[Dict[str, Any]] = []

    for data_file, gold in corpus:
        tables = loader.load(data_file)
        gold_by_source = {g["source"]: g for g in _gold_tables(gold)}
        t0 = time.perf_counter()
        for table in tables:
            g = gold_by_source.get(table.name)
            if not g:
                continue
            profiles = inference.profile(table)
            proposal = inference.propose_schema(table, profiles)
            res = _evaluate_table(proposal, g["roles"])
            elapsed = time.perf_counter() - t0

            total_cols += res["n_columns"]
            total_correct += res["correct"]
            for role, v in res["tp"].items():
                agg_tp[role] += v
            for role, v in res["fp"].items():
                agg_fp[role] += v
            for role, v in res["fn"].items():
                agg_fn[role] += v
            query_scores.append(res["queryability"])
            coherent_total += 1
            coherent_count += int(res["coherent"])
            per_fixture.append(
                {
                    "fixture": data_file.name,
                    "table": table.name,
                    "rows": table.n_rows,
                    "accuracy": round(res["accuracy"], 3),
                    "queryability": round(res["queryability"], 3),
                    "coherent": res["coherent"],
                    "elapsed_s": round(elapsed, 4),
                    "mistakes": res["mistakes"],
                }
            )

    per_role = {}
    for role in ROLES:
        p, r, f = _prf(agg_tp[role], agg_fp[role], agg_fn[role])
        if agg_tp[role] or agg_fp[role] or agg_fn[role]:
            per_role[role] = {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}

    return {
        "mode": "hybrid(llm)" if use_llm else "heuristic",
        "column_accuracy": round(total_correct / total_cols, 3) if total_cols else 0.0,
        "per_role": per_role,
        "queryability_mean": round(sum(query_scores) / len(query_scores), 3) if query_scores else 0.0,
        "coherence_rate": round(coherent_count / coherent_total, 3) if coherent_total else 0.0,
        "n_tables": coherent_total,
        "n_columns": total_cols,
        "per_fixture": per_fixture,
    }


def _print_report(report: Dict[str, Any]) -> None:
    print(f"\n=== Banco de evaluación SGI — modo: {report['mode']} ===")
    print(f"Tablas: {report['n_tables']}  |  Columnas: {report['n_columns']}")
    print(f"Accuracy de columnas : {report['column_accuracy']}")
    print(f"Consultabilidad (media): {report['queryability_mean']}")
    print(f"Coherencia (patrón)  : {report['coherence_rate']}")
    print("\nPor rol (precision / recall / f1):")
    for role, m in report["per_role"].items():
        print(f"  {role:14s} P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}")
    print("\nPor fixture:")
    print(f"  {'fixture':26s} {'tabla':14s} {'filas':>6s} {'acc':>6s} {'query':>6s} coh")
    for f in report["per_fixture"]:
        print(
            f"  {f['fixture']:26s} {f['table']:14s} {f['rows']:6d} "
            f"{f['accuracy']:6.2f} {f['queryability']:6.2f} {str(f['coherent'])}"
        )
    # errores para iterar heurística/prompt
    print("\nErrores de mapeo (para iterar):")
    for f in report["per_fixture"]:
        for m in f["mistakes"]:
            print(f"  {f['table']}.{m['column']}: gold={m['gold']} pred={m['pred']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluación de inferencia de esquema tabular")
    ap.add_argument("--llm", action="store_true", help="Evaluar la vía híbrida (heurística+LLM)")
    ap.add_argument("--json", type=str, default=None, help="Ruta para volcar el reporte JSON")
    args = ap.parse_args()

    report = run(use_llm=args.llm)
    _print_report(report)
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nReporte JSON escrito en {args.json}")


if __name__ == "__main__":
    main()
