#!/usr/bin/env python3
"""
Runner end-to-end de benchmark ETI por dominio (DoE con doekit).

Flujo:
  recommend|screening → genera diseño
  run                 → ejecuta filas (offline por defecto)
  analyze             → main_effects / retained_factors
  propose             → propose_next_runs sobre factores activos

Ejemplos:
  python scripts/run_domain_pipeline.py --domain knowledge_graphs --design screening
  python scripts/run_domain_pipeline.py --domain knowledge_graphs --design run --mode offline
  python scripts/run_domain_pipeline.py --domain knowledge_graphs --design run --mode online --hi-wave
  python scripts/run_domain_pipeline.py --domain knowledge_graphs --design freeze-capa0 --run-id <uuid>
  python scripts/run_domain_pipeline.py --domain knowledge_graphs --design reload-capa0
  python scripts/run_domain_pipeline.py --domain knowledge_graphs --design family-wave
  python scripts/run_domain_pipeline.py --domain knowledge_graphs --design chunk-wave
  python scripts/run_domain_pipeline.py --domain knowledge_graphs --design analyze
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _git_sha() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return ""


def _domain_dir(name: str) -> Path:
    return ROOT / "benchmarks" / "domains" / name


def _reports_dir(domain: str) -> Path:
    d = _domain_dir(domain) / "reports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _resolve_doe_path(args: argparse.Namespace, domain_dir: Path) -> Optional[Path]:
    if getattr(args, "doe_path", None):
        p = Path(args.doe_path)
        if not p.is_absolute():
            cand = domain_dir / p
            p = cand if cand.exists() else Path(args.doe_path)
        return p
    return None


def cmd_screening(args: argparse.Namespace) -> int:
    from ungraph.evaluation.doe_bridge import (
        architecture_factors_from_manifest,
        build_screening_design,
        save_design_artifacts,
    )
    from ungraph.evaluation.domain_pipeline import load_domain_bundle

    domain_dir = _domain_dir(args.domain)
    doe_file = _resolve_doe_path(args, domain_dir)
    manifest, doe, _, _ = load_domain_bundle(domain_dir, doe_path=doe_file)
    budget = int(args.budget or doe.get("budget") or 8)
    seed = int(args.seed if args.seed is not None else doe.get("seed") or 0)
    factors = architecture_factors_from_manifest(manifest, doe=doe, mode=args.mode)
    design, rows, meta = build_screening_design(
        factors, budget=budget, seed=seed, goal=str(doe.get("goal") or "screening")
    )
    meta = {
        **meta,
        "wave": doe.get("wave"),
        "doe_path": str(doe_file) if doe_file else str(domain_dir / "doe.yaml"),
        "fixed": dict(doe.get("fixed") or {}),
        "response_primary": doe.get("response_primary"),
    }
    out = _reports_dir(args.domain)
    design_name = "design_h_chunk.json" if str(doe.get("wave") or "") == "h_chunk" else "design.json"
    path = save_design_artifacts(
        out, design=design, rows=rows, meta=meta, filename=design_name
    )
    print(json.dumps({"ok": True, "design_path": str(path), "meta": meta}, indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from ungraph.evaluation.doe_bridge import (
        architecture_factors_from_manifest,
        build_screening_design,
        load_design_artifacts,
        rows_to_pipeline_configs,
        save_design_artifacts,
    )
    from ungraph.evaluation.domain_pipeline import (
        hi_wave_configs,
        load_domain_bundle,
        run_architecture_offline,
        run_architecture_online,
    )
    from ungraph.evaluation.experiment_run import rank_experiment_runs_by_composite_score
    from ungraph.core.configuration import get_settings

    domain_dir = _domain_dir(args.domain)
    reports = _reports_dir(args.domain)
    doe_file = _resolve_doe_path(args, domain_dir)
    manifest, doe, gold_path, corpus_paths = load_domain_bundle(
        domain_dir, doe_path=doe_file
    )
    if not gold_path.exists():
        print(f"ERROR: gold not found: {gold_path}", file=sys.stderr)
        return 2
    if not corpus_paths:
        print("ERROR: no corpus files found", file=sys.stderr)
        return 2

    # Seed corpus for reproducible DoE / H_I unless --full-corpus
    if not args.full_corpus:
        seed_doc = domain_dir / "corpus" / "kg_survey.md"
        if seed_doc.exists():
            corpus_paths = [seed_doc]

    defaults = dict(manifest.get("defaults") or {})
    # DoE ``fixed`` blocks Infer / overlap / mode (H_chunk coherent design)
    defaults = {**defaults, **dict(doe.get("fixed") or {})}
    git_sha = _git_sha()
    seed = int(args.seed if args.seed is not None else doe.get("seed") or 0)
    wave = str(doe.get("wave") or "")

    if args.hi_wave:
        configs = hi_wave_configs(
            chunk_size=int(defaults.get("chunk_size") or 1024),
            chunk_overlap=int(defaults.get("chunk_overlap") or 200),
            top_k=int(defaults.get("top_k") or 3),
            rag="text",
        )
        design_id = "hi-wave-2"
        meta = {
            "design_id": design_id,
            "method": "H_I_contrast",
            "n_runs": len(configs),
            "seed": seed,
            "factor_names": ["inference"],
            "rationale": "Oleada-2: Transform fijo; inference none vs ner (Neo4j+spaCy).",
        }
        (reports / "design_hi_wave.json").write_text(
            json.dumps({"meta": meta, "rows": configs}, indent=2), encoding="utf-8"
        )
    else:
        default_design = (
            reports / "design_h_chunk.json"
            if wave == "h_chunk"
            else reports / "design.json"
        )
        design_path = Path(args.design_path) if args.design_path else default_design
        if design_path.exists() and not args.redesign:
            design, rows, meta = load_design_artifacts(design_path)
            if design is None:
                data = json.loads(design_path.read_text(encoding="utf-8"))
                rows = list(data.get("rows") or [])
                meta = dict(data.get("meta") or {})
        else:
            budget = int(args.budget or doe.get("budget") or 8)
            factors = architecture_factors_from_manifest(manifest, doe=doe, mode=args.mode)
            design, rows, meta = build_screening_design(
                factors, budget=budget, seed=seed, goal=str(doe.get("goal") or "screening")
            )
            meta = {
                **meta,
                "wave": wave or None,
                "fixed": dict(doe.get("fixed") or {}),
                "response_primary": doe.get("response_primary"),
            }
            fname = "design_h_chunk.json" if wave == "h_chunk" else "design.json"
            save_design_artifacts(
                reports, design=design, rows=rows, meta=meta, filename=fname
            )
        configs = rows_to_pipeline_configs(rows, defaults=defaults)
        design_id = str(meta.get("design_id") or "design")

    runs_meta: List[Dict[str, Any]] = []
    result_rows: List[Dict[str, Any]] = []
    experiment_runs = []
    db = args.database or get_settings().neo4j_database or "neo4j"

    for cfg in configs:
        if args.mode == "online":
            try:
                run, doe_row = run_architecture_online(
                    domain=args.domain,
                    architecture=cfg,
                    corpus_paths=corpus_paths,
                    gold_path=gold_path,
                    database=db,
                    design_id=design_id,
                    design_row_id=str(cfg.get("design_row_id") or ""),
                    seed=seed,
                    git_sha=git_sha,
                    wipe=not args.no_wipe,
                )
            except Exception as exc:
                print(f"ERROR online run {cfg}: {exc}", file=sys.stderr)
                return 3
        else:
            run, doe_row = run_architecture_offline(
                domain=args.domain,
                architecture=cfg,
                corpus_paths=corpus_paths,
                gold_path=gold_path,
                design_id=design_id,
                design_row_id=str(cfg.get("design_row_id") or ""),
                seed=seed,
                git_sha=git_sha,
            )
        experiment_runs.append(run)
        result_rows.append(doe_row)
        run_path = reports / f"{run.run_id}.json"
        run_path.write_text(run.to_json(), encoding="utf-8")
        runs_meta.append(
            {
                "run_id": run.run_id,
                "path": str(run_path),
                "composite_score": run.composite_score(),
                "architecture": run.architecture,
                "transform": (run.scorecard or {}).get("transform"),
                "rag_qa": (run.scorecard or {}).get("rag_qa"),
            }
        )

    # results.csv (wave-specific name for H_chunk DoE)
    csv_path = (
        reports / "results_h_chunk.csv" if wave == "h_chunk" else reports / "results.csv"
    )
    if result_rows:
        keys: List[str] = []
        for r in result_rows:
            for k in r.keys():
                if k not in keys:
                    keys.append(k)
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in result_rows:
                w.writerow(r)

    ranked = rank_experiment_runs_by_composite_score(experiment_runs)
    hi_verdict: Optional[Dict[str, Any]] = None
    if args.hi_wave and len(experiment_runs) >= 2:
        by_inf = {str((r.architecture or {}).get("inference")): r for r in experiment_runs}
        none_r, ner_r = by_inf.get("none"), by_inf.get("ner")
        if none_r and ner_r:
            def _er(run):
                return float(((run.scorecard or {}).get("transform") or {}).get("entity_recall") or 0.0)

            def _ac(run):
                v = ((run.scorecard or {}).get("rag_qa") or {}).get("answer_correctness")
                return float(v) if v is not None else None

            er_n, er_i = _er(none_r), _er(ner_r)
            ac_n, ac_i = _ac(none_r), _ac(ner_r)
            graph_ok = er_i > er_n
            task_ok = True
            if ac_n is not None and ac_i is not None:
                task_ok = ac_i >= (ac_n - 1e-9)  # no colapso
            hi_verdict = {
                "hypothesis": "H_I",
                "entity_recall_none": er_n,
                "entity_recall_ner": er_i,
                "answer_correctness_none": ac_n,
                "answer_correctness_ner": ac_i,
                "graph_improves": graph_ok,
                "task_does_not_collapse": task_ok,
                "pass": bool(graph_ok and task_ok),
                "note": (
                    "PASS: ner > none en entity_recall y tarea no colapsa"
                    if (graph_ok and task_ok)
                    else "FAIL/partial: recortar claim o revisar Y/gold/indexes"
                ),
            }
            (reports / "hi_wave_verdict.json").write_text(
                json.dumps(hi_verdict, indent=2), encoding="utf-8"
            )

    summary = {
        "domain": args.domain,
        "mode": args.mode,
        "hi_wave": bool(args.hi_wave),
        "wave": wave or None,
        "doe_path": str(doe_file) if doe_file else None,
        "design_id": design_id,
        "design_meta": meta,
        "n_runs": len(experiment_runs),
        "results_csv": str(csv_path),
        "hi_wave_verdict": hi_verdict,
        "ranking": [
            {
                "composite_score": score,
                "run_id": run.run_id,
                "architecture": run.architecture,
            }
            for score, run in ranked
        ],
        "runs": runs_meta,
    }
    summary_name = "summary_h_chunk.json" if wave == "h_chunk" else "summary.json"
    summary_path = reports / summary_name
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if wave == "h_chunk":
        csv_h = reports / "results_h_chunk.csv"
        if csv_path.exists() and csv_path.resolve() != csv_h.resolve():
            csv_h.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    if ranked:
        best = ranked[0][1]
        (reports / "scorecard.json").write_text(
            json.dumps(best.scorecard, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    capa0_path = None
    if args.freeze_capa0 and experiment_runs:
        from ungraph.evaluation.capa0_artifact import (
            DEFAULT_ARTIFACT_NAME,
            select_ner_run,
        )

        try:
            ner_run = select_ner_run(experiment_runs)
        except ValueError as exc:
            print(f"ERROR freeze-capa0: {exc}", file=sys.stderr)
            return 4
        capa0_path = _freeze_run_to_capa0(
            ner_run,
            domain_dir=domain_dir,
            reports=reports,
            database=db,
            with_graph_stats=not args.no_graph_stats,
            out_name=DEFAULT_ARTIFACT_NAME,
        )

    print(
        json.dumps(
            {
                "ok": True,
                "summary": str(summary_path),
                "n_runs": len(experiment_runs),
                "hi_wave_verdict": hi_verdict,
                "capa0_artifact": str(capa0_path) if capa0_path else None,
            },
            indent=2,
        )
    )
    return 0


def _optional_graph_stats(database: str) -> Optional[Dict[str, Any]]:
    try:
        from ungraph.evaluation.graph_structural_stats import (
            collect_structural_graph_stats,
        )
        from ungraph.utils.graph_operations import graph_session

        driver = graph_session()
        return collect_structural_graph_stats(driver, database=database).to_json_obj()
    except Exception:
        return None


def _freeze_run_to_capa0(
    run,
    *,
    domain_dir: Path,
    reports: Path,
    database: str,
    with_graph_stats: bool,
    out_name: str,
) -> Path:
    from ungraph.evaluation.capa0_artifact import (
        build_capa0_from_experiment_run,
        save_capa0_artifact,
    )

    stats = _optional_graph_stats(database) if with_graph_stats else None
    art = build_capa0_from_experiment_run(
        run,
        domain_dir=domain_dir,
        experiment_run_path=f"{run.run_id}.json",
        graph_stats=stats,
    )
    out = reports / out_name
    save_capa0_artifact(out, art)
    return out


def cmd_freeze_capa0(args: argparse.Namespace) -> int:
    """Freeze Capa 0 from an existing ExperimentRun JSON (prefer H_I ner)."""
    from ungraph.core.configuration import get_settings
    from ungraph.evaluation.capa0_artifact import DEFAULT_ARTIFACT_NAME
    from ungraph.evaluation.experiment_run import ExperimentRun

    domain_dir = _domain_dir(args.domain)
    reports = _reports_dir(args.domain)
    db = args.database or get_settings().neo4j_database or "neo4j"

    run_path: Optional[Path] = None
    if args.run_id:
        cand = Path(args.run_id)
        if cand.is_file():
            run_path = cand
        else:
            run_path = reports / f"{args.run_id}.json"
            if not run_path.exists() and not str(args.run_id).endswith(".json"):
                run_path = reports / f"{args.run_id}.json"
    else:
        # Prefer NER from summary ranking / any *ner* online run
        summary_path = reports / "summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            for item in summary.get("runs") or []:
                arch = item.get("architecture") or {}
                if str(arch.get("inference")).lower() == "ner":
                    run_path = Path(item.get("path") or reports / f"{item['run_id']}.json")
                    break
        if run_path is None:
            for p in sorted(reports.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
                if p.name in (
                    "summary.json",
                    "design.json",
                    "design_hi_wave.json",
                    "analysis.json",
                    "scorecard.json",
                    "hi_wave_verdict.json",
                    DEFAULT_ARTIFACT_NAME,
                    "reload_verdict.json",
                ):
                    continue
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if str((data.get("architecture") or {}).get("inference")).lower() == "ner":
                    run_path = p
                    break

    if run_path is None or not run_path.exists():
        print(
            "ERROR: no ner ExperimentRun found. Pass --run-id <uuid> "
            "or run --hi-wave --freeze-capa0 first.",
            file=sys.stderr,
        )
        return 2

    run = ExperimentRun.from_json(run_path.read_text(encoding="utf-8"))
    out = _freeze_run_to_capa0(
        run,
        domain_dir=domain_dir,
        reports=reports,
        database=db,
        with_graph_stats=not args.no_graph_stats,
        out_name=Path(args.capa0_path).name if args.capa0_path else DEFAULT_ARTIFACT_NAME,
    )
    if args.capa0_path:
        target = Path(args.capa0_path)
        if target.resolve() != out.resolve():
            target.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
            out = target
    print(json.dumps({"ok": True, "capa0_artifact": str(out), "run_id": run.run_id}, indent=2))
    return 0


def cmd_reload_capa0(args: argparse.Namespace) -> int:
    """Wipe → re-ingest pinned Capa 0 recipe; compare gate Y to freeze."""
    from ungraph.core.configuration import get_settings
    from ungraph.evaluation.capa0_artifact import (
        DEFAULT_ARTIFACT_NAME,
        compare_gate,
        gate_metrics_from_scorecard,
        load_capa0_artifact,
        resolve_under_domain,
    )
    from ungraph.evaluation.domain_pipeline import run_architecture_online

    domain_dir = _domain_dir(args.domain)
    reports = _reports_dir(args.domain)
    art_path = Path(args.capa0_path) if args.capa0_path else reports / DEFAULT_ARTIFACT_NAME
    if not art_path.exists():
        print(f"ERROR: capa0 artifact not found: {art_path}", file=sys.stderr)
        return 2

    art = load_capa0_artifact(art_path)
    corpus_paths = [resolve_under_domain(p, domain_dir) for p in art.corpus_paths]
    gold_path = resolve_under_domain(art.gold_path, domain_dir)
    missing = [str(p) for p in corpus_paths if not p.exists()]
    if missing:
        print(f"ERROR: corpus missing: {missing}", file=sys.stderr)
        return 2
    if not gold_path.exists():
        print(f"ERROR: gold missing: {gold_path}", file=sys.stderr)
        return 2

    db = args.database or get_settings().neo4j_database or "neo4j"
    git_sha = _git_sha()
    try:
        run, _ = run_architecture_online(
            domain=art.domain or args.domain,
            architecture=art.architecture,
            corpus_paths=corpus_paths,
            gold_path=gold_path,
            database=db,
            design_id="capa0-reload",
            design_row_id=art.run_id,
            seed=art.seed,
            git_sha=git_sha,
            wipe=not args.no_wipe,
        )
    except Exception as exc:
        print(f"ERROR reload-capa0: {exc}", file=sys.stderr)
        return 3

    # Keep scientific pointer to frozen run_id
    run.notes = (
        f"reload of capa0 run_id={art.run_id}; protocol={art.reload_protocol}; "
        f"new_run_id={run.run_id}"
    )
    run_path = reports / f"{run.run_id}.json"
    run_path.write_text(run.to_json(), encoding="utf-8")

    observed = gate_metrics_from_scorecard(run.scorecard)
    verdict = compare_gate(art.gate, observed, atol=float(args.gate_atol or 1e-4))
    # Optional structural counts
    stats = _optional_graph_stats(db)
    stats_ok = None
    if art.graph_stats and stats:
        from ungraph.evaluation.graph_structural_stats import (
            GraphStructuralStats,
            diff_structural_stats,
        )

        try:
            d = diff_structural_stats(
                GraphStructuralStats.from_json_obj(art.graph_stats),
                GraphStructuralStats.from_json_obj(stats),
            )
            # treat as ok if no large count deltas — helper may return dict/list
            stats_ok = d
        except Exception as exc:
            stats_ok = {"error": str(exc)}

    payload = {
        "ok": bool(verdict.get("ok")),
        "frozen_run_id": art.run_id,
        "reload_run_id": run.run_id,
        "gate_compare": verdict,
        "graph_stats_diff": stats_ok,
        "reload_protocol": art.reload_protocol,
        "experiment_run_path": str(run_path),
        "note": (
            "PASS: gate Y matched freeze after wipe→re-ingest"
            if verdict.get("ok")
            else "FAIL: gate Y drifted; check spaCy/model/indexes/gold"
        ),
    }
    out = reports / "reload_verdict.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 5


def cmd_family_wave(args: argparse.Namespace) -> int:
    """Oleada-3: ≥2 familias Infer sobre recipe Capa 0; mismas Y capa B."""
    from ungraph.core.configuration import get_settings
    from ungraph.evaluation.capa0_artifact import (
        DEFAULT_ARTIFACT_NAME,
        load_capa0_artifact,
        resolve_under_domain,
    )
    from ungraph.evaluation.domain_pipeline import (
        family_wave_configs_from_capa0,
        run_architecture_online,
    )
    from ungraph.evaluation.family_wave import build_family_wave_verdict

    domain_dir = _domain_dir(args.domain)
    reports = _reports_dir(args.domain)
    art_path = Path(args.capa0_path) if args.capa0_path else reports / DEFAULT_ARTIFACT_NAME
    if not art_path.exists():
        print(f"ERROR: capa0 artifact not found: {art_path}", file=sys.stderr)
        return 2

    art = load_capa0_artifact(art_path)
    corpus_paths = [resolve_under_domain(p, domain_dir) for p in art.corpus_paths]
    gold_path = resolve_under_domain(art.gold_path, domain_dir)
    if any(not p.exists() for p in corpus_paths) or not gold_path.exists():
        print("ERROR: corpus/gold from capa0 missing on disk", file=sys.stderr)
        return 2

    families = [
        x.strip().lower()
        for x in str(args.families or "ner,pattern").split(",")
        if x.strip()
    ]
    try:
        configs = family_wave_configs_from_capa0(art.architecture, families=families)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    db = args.database or get_settings().neo4j_database or "neo4j"
    git_sha = _git_sha()
    experiment_runs = []
    runs_meta: List[Dict[str, Any]] = []

    (reports / "design_family_wave.json").write_text(
        json.dumps(
            {
                "meta": {
                    "design_id": "family-wave-3",
                    "capa0_run_id": art.run_id,
                    "families": families,
                    "method": "infer_family_contrast",
                },
                "rows": configs,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    for cfg in configs:
        try:
            run, _ = run_architecture_online(
                domain=art.domain or args.domain,
                architecture=cfg,
                corpus_paths=corpus_paths,
                gold_path=gold_path,
                database=db,
                design_id="family-wave-3",
                design_row_id=str(cfg.get("design_row_id") or ""),
                seed=art.seed,
                git_sha=git_sha,
                wipe=not args.no_wipe,
            )
        except Exception as exc:
            print(f"ERROR family-wave {cfg.get('inference')}: {exc}", file=sys.stderr)
            return 3
        run.notes = f"family-wave on capa0={art.run_id}; inference={cfg.get('inference')}"
        experiment_runs.append(run)
        run_path = reports / f"{run.run_id}.json"
        run_path.write_text(run.to_json(), encoding="utf-8")
        runs_meta.append(
            {
                "run_id": run.run_id,
                "path": str(run_path),
                "architecture": run.architecture,
                "transform": (run.scorecard or {}).get("transform"),
                "rag_qa": (run.scorecard or {}).get("rag_qa"),
            }
        )

    verdict = build_family_wave_verdict(
        experiment_runs, capa0_run_id=art.run_id, families=families
    )
    verdict_path = reports / "family_wave_verdict.json"
    verdict_path.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    summary = {
        "domain": args.domain,
        "design_id": "family-wave-3",
        "capa0_run_id": art.run_id,
        "n_runs": len(experiment_runs),
        "runs": runs_meta,
        "family_wave_verdict": verdict,
    }
    (reports / "summary_family_wave.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ok": bool(verdict.get("pass")),
                "verdict": str(verdict_path),
                "family_wave_verdict": verdict,
            },
            indent=2,
        )
    )
    return 0 if verdict.get("pass") else 5


def cmd_chunk_wave(args: argparse.Namespace) -> int:
    """H_chunk / H_T: variar chunk_size con Infer fijo desde capa0; Y top-k + transform."""
    from ungraph.core.configuration import get_settings
    from ungraph.evaluation.capa0_artifact import (
        DEFAULT_ARTIFACT_NAME,
        load_capa0_artifact,
        resolve_under_domain,
    )
    from ungraph.evaluation.chunk_wave import build_chunk_wave_verdict
    from ungraph.evaluation.domain_pipeline import (
        chunk_wave_configs_from_capa0,
        run_architecture_online,
    )

    domain_dir = _domain_dir(args.domain)
    reports = _reports_dir(args.domain)
    art_path = Path(args.capa0_path) if args.capa0_path else reports / DEFAULT_ARTIFACT_NAME
    if not art_path.exists():
        print(f"ERROR: capa0 artifact not found: {art_path}", file=sys.stderr)
        return 2

    art = load_capa0_artifact(art_path)
    corpus_paths = [resolve_under_domain(p, domain_dir) for p in art.corpus_paths]
    gold_path = resolve_under_domain(art.gold_path, domain_dir)
    if any(not p.exists() for p in corpus_paths) or not gold_path.exists():
        print("ERROR: corpus/gold from capa0 missing on disk", file=sys.stderr)
        return 2

    sizes = [
        int(x.strip())
        for x in str(args.chunk_sizes or "512,1000,1500").split(",")
        if x.strip()
    ]
    inf = str(args.fixed_inference or art.architecture.get("inference") or "ner").lower()
    try:
        configs = chunk_wave_configs_from_capa0(
            art.architecture, chunk_sizes=sizes, inference=inf
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    db = args.database or get_settings().neo4j_database or "neo4j"
    git_sha = _git_sha()
    experiment_runs = []
    runs_meta: List[Dict[str, Any]] = []

    (reports / "design_chunk_wave.json").write_text(
        json.dumps(
            {
                "meta": {
                    "design_id": "chunk-wave-h",
                    "capa0_run_id": art.run_id,
                    "fixed_inference": inf,
                    "chunk_sizes": sizes,
                    "method": "H_chunk_H_T",
                },
                "rows": configs,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    for cfg in configs:
        try:
            run, _ = run_architecture_online(
                domain=art.domain or args.domain,
                architecture=cfg,
                corpus_paths=corpus_paths,
                gold_path=gold_path,
                database=db,
                design_id="chunk-wave-h",
                design_row_id=str(cfg.get("design_row_id") or ""),
                seed=art.seed,
                git_sha=git_sha,
                wipe=not args.no_wipe,
            )
        except Exception as exc:
            print(f"ERROR chunk-wave size={cfg.get('chunk_size')}: {exc}", file=sys.stderr)
            return 3
        run.notes = (
            f"chunk-wave on capa0={art.run_id}; "
            f"chunk_size={cfg.get('chunk_size')}; inference={inf}"
        )
        experiment_runs.append(run)
        run_path = reports / f"{run.run_id}.json"
        run_path.write_text(run.to_json(), encoding="utf-8")
        runs_meta.append(
            {
                "run_id": run.run_id,
                "path": str(run_path),
                "architecture": run.architecture,
                "transform": (run.scorecard or {}).get("transform"),
                "rag_qa": (run.scorecard or {}).get("rag_qa"),
                "extract": (run.scorecard or {}).get("extract"),
            }
        )

    verdict = build_chunk_wave_verdict(
        experiment_runs, capa0_run_id=art.run_id, fixed_inference=inf
    )
    verdict_path = reports / "chunk_wave_verdict.json"
    verdict_path.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    (reports / "summary_chunk_wave.json").write_text(
        json.dumps(
            {
                "domain": args.domain,
                "design_id": "chunk-wave-h",
                "capa0_run_id": art.run_id,
                "n_runs": len(experiment_runs),
                "runs": runs_meta,
                "chunk_wave_verdict": verdict,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": bool(verdict.get("pass")),
                "verdict": str(verdict_path),
                "chunk_wave_verdict": verdict,
            },
            indent=2,
        )
    )
    return 0 if verdict.get("pass") else 5


def cmd_analyze(args: argparse.Namespace) -> int:
    from ungraph.evaluation.doe_bridge import analyze_results, load_design_artifacts
    from ungraph.evaluation.domain_pipeline import load_domain_bundle

    domain_dir = _domain_dir(args.domain)
    reports = _reports_dir(args.domain)
    doe_file = _resolve_doe_path(args, domain_dir)
    _, doe, _, _ = load_domain_bundle(domain_dir, doe_path=doe_file)
    wave = str(doe.get("wave") or "")
    default_design = (
        reports / "design_h_chunk.json" if wave == "h_chunk" else reports / "design.json"
    )
    default_results = (
        reports / "results_h_chunk.csv" if wave == "h_chunk" else reports / "results.csv"
    )
    design_path = Path(args.design_path) if args.design_path else default_design
    results_path = Path(args.results) if args.results else default_results
    if not design_path.exists():
        print(f"ERROR: design not found: {design_path}", file=sys.stderr)
        return 2
    if not results_path.exists():
        # fallback to results.csv written by runner
        alt = reports / "results.csv"
        if alt.exists():
            results_path = alt
        else:
            print(f"ERROR: results not found: {results_path}", file=sys.stderr)
            return 2

    import pandas as pd

    design, _, meta = load_design_artifacts(design_path)
    if design is None:
        print("ERROR: could not restore doekit Design from design.json", file=sys.stderr)
        return 2
    df = pd.read_csv(results_path)
    response = args.response or doe.get("response_primary") or "composite_score"
    retain = dict(doe.get("retain") or {})
    analysis = analyze_results(
        design,
        df,
        response=str(response),
        alpha=float(retain.get("alpha") or 0.1),
        effect_abs_min=float(retain.get("effect_abs_min") or 0.05),
    )
    payload = {
        "design_meta": meta,
        "analysis": analysis.to_json_obj(),
    }
    out_name = "analysis_h_chunk.json" if wave == "h_chunk" else "analysis.json"
    out_path = reports / out_name
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # retained_factors convenience
    retain_name = (
        "retained_factors_h_chunk.json" if wave == "h_chunk" else "retained_factors.json"
    )
    (reports / retain_name).write_text(
        json.dumps(
            {
                "retained_factors": analysis.retained_factors,
                "response": analysis.response,
                "notes": analysis.notes,
                "wave": wave or None,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    return 0


def cmd_propose(args: argparse.Namespace) -> int:
    from ungraph.evaluation.doe_bridge import load_design_artifacts, propose_next
    from ungraph.evaluation.domain_pipeline import load_domain_bundle

    reports = _reports_dir(args.domain)
    design_path = Path(args.design_path) if args.design_path else reports / "design.json"
    results_path = Path(args.results) if args.results else reports / "results.csv"
    design, _, _ = load_design_artifacts(design_path)
    if design is None:
        print("ERROR: could not restore Design", file=sys.stderr)
        return 2
    import pandas as pd

    df = pd.read_csv(results_path)
    _, doe, _, _ = load_domain_bundle(_domain_dir(args.domain))
    response = args.response or doe.get("response_primary") or "composite_score"
    prop = propose_next(
        design,
        df,
        response=str(response),
        n_add=int(args.n_add or 4),
        seed=int(args.seed or 0),
    )
    out = reports / "next_runs.json"
    out.write_text(json.dumps(prop, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(out)}, indent=2))
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    """Alias de screening que imprime también la recommendation completa."""
    return cmd_screening(args)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ungraph domain ETI pipeline + doekit DoE")
    p.add_argument("--domain", default="knowledge_graphs")
    p.add_argument(
        "--design",
        choices=[
            "recommend",
            "screening",
            "run",
            "analyze",
            "propose",
            "freeze-capa0",
            "reload-capa0",
            "family-wave",
            "chunk-wave",
        ],
        default="run",
        help="DoE stage to execute",
    )
    p.add_argument("--mode", choices=["offline", "online"], default="offline")
    p.add_argument("--budget", type=int, default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--design-path", default=None)
    p.add_argument("--results", default=None)
    p.add_argument("--response", default=None)
    p.add_argument("--n-add", type=int, default=4)
    p.add_argument("--redesign", action="store_true", help="Ignore existing design.json")
    p.add_argument(
        "--full-corpus",
        action="store_true",
        help="Use all manifest corpus files (defaults to kg_survey.md for smoke/H_I)",
    )
    p.add_argument(
        "--hi-wave",
        action="store_true",
        help="Oleada-2 H_I: solo configs none vs ner, Transform fijo (recursive/1024)",
    )
    p.add_argument("--database", "-d", default=None, help="Neo4j database name")
    p.add_argument(
        "--no-wipe",
        action="store_true",
        help="Online: do not DETACH DELETE before each cell (debug only)",
    )
    p.add_argument(
        "--freeze-capa0",
        action="store_true",
        help="After --design run: freeze NER ExperimentRun as capa0_artifact.json",
    )
    p.add_argument(
        "--run-id",
        default=None,
        help="freeze-capa0: ExperimentRun uuid or path under reports/",
    )
    p.add_argument(
        "--capa0-path",
        default=None,
        help="Path to capa0_artifact.json (freeze out / reload in)",
    )
    p.add_argument(
        "--no-graph-stats",
        action="store_true",
        help="Skip Neo4j structural stats when freezing Capa 0",
    )
    p.add_argument(
        "--gate-atol",
        type=float,
        default=1e-4,
        help="reload-capa0: absolute tolerance for gate Y compare",
    )
    p.add_argument(
        "--families",
        default="ner,pattern",
        help="family-wave: comma-separated inference families (default ner,pattern)",
    )
    p.add_argument(
        "--chunk-sizes",
        default="512,1000,1500",
        help="chunk-wave: comma-separated chunk_size levels",
    )
    p.add_argument(
        "--fixed-inference",
        default=None,
        help="chunk-wave: pin inference family (default: capa0 architecture.inference)",
    )
    p.add_argument(
        "--doe-path",
        default=None,
        help="Path to doe YAML (e.g. doe_h_chunk.yaml) relative to domain dir or absolute",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    dispatch = {
        "recommend": cmd_recommend,
        "screening": cmd_screening,
        "run": cmd_run,
        "analyze": cmd_analyze,
        "propose": cmd_propose,
        "freeze-capa0": cmd_freeze_capa0,
        "reload-capa0": cmd_reload_capa0,
        "family-wave": cmd_family_wave,
        "chunk-wave": cmd_chunk_wave,
    }
    return dispatch[args.design](args)


if __name__ == "__main__":
    raise SystemExit(main())
