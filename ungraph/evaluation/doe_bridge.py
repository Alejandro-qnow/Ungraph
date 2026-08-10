"""
Bridge Ungraph ↔ doekit para el diseño experimental del pipeline ETI.

El núcleo ``domain/`` no importa doekit. Este módulo (extra ``experiments``)
traduce factores de arquitectura + verify a factores doekit, genera diseños de
screening, convierte filas a configs del runner y analiza resultados
(main_effects / fit → ``retained_factors``).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

# Respuestas Y típicas del scorecard / reasoning (columnas planas).
DEFAULT_RESPONSE_KEYS: Tuple[str, ...] = (
    "composite_score",
    "entity_recall",
    "relation_pair_recall",
    "evidence_coverage",
    "f1",
    "hallucination_rate",
    "distractor_rejection_rate",
    "answer_correctness",
    "mrr",
    "latency_s",
)


@dataclass
class ArchitectureParams:
    """Punto en el espacio de factores ETI (Extract / Infer / RAG)."""

    chunking: str = "recursive"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    inference: str = "ner"  # none | ner | llm
    rag: str = "text"  # text | vector | hybrid
    top_k: int = 5

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def factor_names(cls) -> List[str]:
        return [f.name for f in fields(cls)]

    @classmethod
    def from_record(cls, rec: Mapping[str, Any]) -> "ArchitectureParams":
        kwargs: Dict[str, Any] = {}
        for f in fields(cls):
            if f.name not in rec or rec[f.name] is None:
                continue
            val = rec[f.name]
            if f.name in ("chunking", "inference", "rag"):
                kwargs[f.name] = str(val)
            elif f.name in ("chunk_size", "chunk_overlap", "top_k"):
                kwargs[f.name] = int(round(float(val)))
            else:
                kwargs[f.name] = val
        return cls(**kwargs)


@dataclass
class DoeAnalysisResult:
    """Salida de ``analyze_results``."""

    response: str
    main_effects: Dict[str, float] = field(default_factory=dict)
    pvalues: Dict[str, float] = field(default_factory=dict)
    retained_factors: List[str] = field(default_factory=list)
    r_squared: Optional[float] = None
    n_runs: int = 0
    notes: str = ""

    def to_json_obj(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "main_effects": dict(self.main_effects),
            "pvalues": dict(self.pvalues),
            "retained_factors": list(self.retained_factors),
            "r_squared": self.r_squared,
            "n_runs": self.n_runs,
            "notes": self.notes,
        }


def _require_doekit():
    try:
        import doekit as ed  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "doekit is required for DoE bridge. Install with: "
            "pip install 'ungraph[experiments]' or pip install doekit"
        ) from exc
    return ed


def load_doe_descriptor(path: Union[str, Path]) -> Dict[str, Any]:
    """Carga ``doe.yaml`` (YAML) o JSON con factores/respuestas."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("PyYAML required to load doe.yaml") from exc
        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"DoE descriptor must be a mapping: {p}")
    return data


def architecture_factors_from_manifest(
    manifest: Optional[Mapping[str, Any]] = None,
    *,
    doe: Optional[Mapping[str, Any]] = None,
    mode: str = "offline",
) -> List[Any]:
    """
    Construye factores doekit desde ``manifest.yaml`` / ``doe.yaml``.

    Oleada-1 offline por defecto: chunking, chunk_size, inference (none/ner), rag.
    """
    ed = _require_doekit()
    manifest = dict(manifest or {})
    doe = dict(doe or {})
    arch = dict(manifest.get("architectures") or {})
    defaults = dict(manifest.get("defaults") or {})
    factor_spec = list(doe.get("factors") or [])

    if factor_spec:
        factors: List[Any] = []
        for spec in factor_spec:
            name = str(spec["name"])
            kind = str(spec.get("kind") or "categorical").lower()
            if kind == "continuous":
                lo = float(spec.get("low", spec.get("min", 0)))
                hi = float(spec.get("high", spec.get("max", 1)))
                factors.append(ed.ContinuousFactor(name, lo, hi))
            else:
                levels = list(spec.get("levels") or [])
                if mode == "offline" and name == "inference":
                    levels = [lv for lv in levels if str(lv) != "llm"] or levels
                if mode == "offline" and name == "rag":
                    levels = [lv for lv in levels if str(lv) != "hybrid"] or levels
                factors.append(ed.CategoricalFactor(name, levels))
        return factors

    # Defaults alineados al plan (oleada-1)
    chunking_levels = list(arch.get("chunking") or ["recursive", "markdown_header"])
    if mode == "offline":
        chunking_levels = [c for c in chunking_levels if c != "semantic"] or chunking_levels
    inference_levels = list(arch.get("inference") or ["none", "ner"])
    if mode == "offline":
        inference_levels = [i for i in inference_levels if i != "llm"]
        if "none" not in inference_levels:
            inference_levels = ["none"] + inference_levels
    rag_levels = list(arch.get("rag") or ["text", "vector"])
    if mode == "offline":
        rag_levels = [r for r in rag_levels if r != "hybrid"] or ["text", "vector"]

    sizes = doe.get("chunk_size_levels") or [512, 1024]
    return [
        ed.CategoricalFactor("chunking", chunking_levels),
        ed.ContinuousFactor("chunk_size", float(min(sizes)), float(max(sizes))),
        ed.CategoricalFactor("inference", inference_levels),
        ed.CategoricalFactor("rag", rag_levels),
    ]


def recommend_screening_design(
    factors: Sequence[Any],
    *,
    budget: int = 8,
    seed: int = 0,
    goal: str = "screening",
) -> Any:
    """Invoca ``doekit.recommend_design`` y devuelve el objeto ``Recommendation``."""
    ed = _require_doekit()
    return ed.recommend_design(goal, list(factors), budget=budget, seed=seed)


def build_screening_design(
    factors: Sequence[Any],
    *,
    budget: int = 8,
    seed: int = 0,
    goal: str = "screening",
) -> Tuple[Any, List[Dict[str, Any]], Dict[str, Any]]:
    """
    Genera diseño de screening.

    Returns:
        (design, rows_as_dicts, meta) donde meta incluye method/rationale/design_id.
    """
    rec = recommend_screening_design(factors, budget=budget, seed=seed, goal=goal)
    design = rec.design
    rows = design_to_records(design)
    summary_attr = getattr(rec, "summary", None)
    if callable(summary_attr):
        try:
            summary_val = summary_attr()
        except TypeError:
            summary_val = str(rec)
    else:
        summary_val = summary_attr or str(rec)
    meta = {
        "design_id": f"{rec.method}-b{budget}-s{seed}",
        "method": rec.method,
        "rationale": str(getattr(rec, "rationale", "") or ""),
        "summary": str(summary_val),
        "budget": budget,
        "seed": seed,
        "n_runs": len(rows),
        "factor_names": list(getattr(design, "factor_names", []) or []),
    }
    return design, rows, meta


def design_to_records(design: Any) -> List[Dict[str, Any]]:
    """Design.matrix (DataFrame) → lista de dicts."""
    matrix = getattr(design, "matrix", None)
    if matrix is None:
        return []
    # pandas DataFrame
    records = matrix.to_dict(orient="records")
    out: List[Dict[str, Any]] = []
    for i, rec in enumerate(records):
        row = dict(rec)
        # normalize chunk_size to int when present
        if "chunk_size" in row and row["chunk_size"] is not None:
            try:
                row["chunk_size"] = int(round(float(row["chunk_size"])))
            except (TypeError, ValueError):
                pass
        row["_design_row_id"] = str(i)
        out.append(row)
    return out


def rows_to_pipeline_configs(
    rows: Sequence[Mapping[str, Any]],
    *,
    defaults: Optional[Mapping[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Filas doekit → configs que entiende el runner / ``ArchitectureParams``."""
    defaults = dict(defaults or {})
    configs: List[Dict[str, Any]] = []
    for rec in rows:
        merged = {**defaults, **dict(rec)}
        arch = ArchitectureParams.from_record(merged)
        cfg = arch.to_flat()
        cfg["design_row_id"] = str(merged.get("_design_row_id", merged.get("design_row_id", "")))
        # pass-through verify params if present
        for k, v in merged.items():
            if k.startswith("w_") or k in (
                "accept_threshold",
                "use_ontology",
                "ontology_gate",
                "use_llm",
                "llm_gate",
                "window_sentences",
            ):
                cfg[k] = v
        configs.append(cfg)
    return configs


def _base_factor_name(term: str, known: Sequence[str]) -> str:
    """Mapea término dummy (chunking_recursive) → factor base (chunking)."""
    if term in known:
        return term
    for name in sorted(known, key=len, reverse=True):
        if term == name or term.startswith(name + "_"):
            return name
    return term.split("_")[0] if "_" in term else term


def analyze_results(
    design: Any,
    results: Union[Sequence[Mapping[str, Any]], Any],
    *,
    response: str = "composite_score",
    alpha: float = 0.1,
    effect_abs_min: float = 0.05,
) -> DoeAnalysisResult:
    """
    Ajusta modelo lineal doekit sobre ``response`` y retiene factores relevantes.

    Criterio de retención: p-value < alpha **o** |main_effect| >= effect_abs_min
    (si no hay p-values). Si ningún factor pasa, ``retained_factors`` vacío y nota
    explícita (recortar filosofía / ampliar N).
    """
    ed = _require_doekit()
    import pandas as pd

    if hasattr(results, "to_dict"):
        # DataFrame
        df = results if isinstance(results, pd.DataFrame) else pd.DataFrame(results)
    else:
        df = pd.DataFrame(list(results))

    if response not in df.columns:
        raise KeyError(f"Response column {response!r} missing from results: {list(df.columns)}")

    y = df[response].astype(float)
    factor_names = list(getattr(design, "factor_names", []) or [])

    me_series = ed.main_effects(design, y)
    main_effects = {str(k): float(v) for k, v in me_series.items()}

    pvalues: Dict[str, float] = {}
    r2: Optional[float] = None
    try:
        fit = ed.fit_linear_model(design, y)
        r2 = float(getattr(fit, "r_squared", None) or 0.0)
        pvs = getattr(fit, "pvalues", None)
        names = list(getattr(fit, "names", None) or [])
        if pvs is not None and names:
            for name, pv in zip(names, list(pvs)):
                if str(name) == "(Intercept)":
                    continue
                try:
                    pvalues[str(name)] = float(pv)
                except (TypeError, ValueError):
                    continue
        elif pvs is not None and hasattr(pvs, "items"):
            for k, v in pvs.items():
                if str(k) == "(Intercept)":
                    continue
                try:
                    pvalues[str(k)] = float(v)
                except (TypeError, ValueError):
                    continue
    except Exception as exc:  # pragma: no cover - defensive
        return DoeAnalysisResult(
            response=response,
            main_effects=main_effects,
            pvalues={},
            retained_factors=[],
            r_squared=None,
            n_runs=len(df),
            notes=f"fit_linear_model failed: {exc}",
        )

    retained: List[str] = []
    for term, coef in main_effects.items():
        base = _base_factor_name(term, factor_names)
        pv = pvalues.get(term)
        keep = False
        if pv is not None and pv < alpha:
            keep = True
        elif pv is None and abs(coef) >= effect_abs_min:
            keep = True
        elif pv is not None and abs(coef) >= effect_abs_min and pv < max(alpha, 0.25):
            # efecto grande con p marginal
            keep = True
        if keep and base not in retained:
            retained.append(base)

    notes = ""
    if not retained:
        notes = (
            "ningún efecto → recortar filosofía / ampliar presupuesto o revisar Y; "
            "no inflar el espacio de factores"
        )

    return DoeAnalysisResult(
        response=response,
        main_effects=main_effects,
        pvalues=pvalues,
        retained_factors=retained,
        r_squared=r2,
        n_runs=len(df),
        notes=notes,
    )


def propose_next(
    design: Any,
    results: Union[Sequence[Mapping[str, Any]], Any],
    *,
    response: str = "composite_score",
    n_add: int = 4,
    seed: int = 0,
) -> Dict[str, Any]:
    """Wrapper de ``doekit.propose_next_runs`` → JSON-friendly."""
    ed = _require_doekit()
    import pandas as pd

    df = results if isinstance(results, pd.DataFrame) else pd.DataFrame(list(results))
    y = df[response].astype(float)
    proposal = ed.propose_next_runs(design, response=y, n_add=n_add, seed=seed)
    out: Dict[str, Any] = {"n_add": n_add, "response": response}
    for attr in ("rationale", "summary", "method"):
        if hasattr(proposal, attr):
            out[attr] = getattr(proposal, attr)
    next_design = getattr(proposal, "design", None) or getattr(proposal, "next_design", None)
    if next_design is not None:
        out["next_rows"] = design_to_records(next_design)
    elif hasattr(proposal, "to_dict"):
        out["raw"] = proposal.to_dict()
    else:
        out["raw"] = str(proposal)
    return out


def _json_safe(obj: Any) -> Any:
    """Convierte estructuras doekit/pandas a JSON-serializable."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if callable(obj) and not isinstance(obj, type):
        return str(obj)
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, Mapping):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    # pandas / numpy scalars
    if hasattr(obj, "item") and callable(obj.item):
        try:
            return _json_safe(obj.item())
        except Exception:
            pass
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        try:
            return _json_safe(obj.to_dict())
        except Exception:
            return str(obj)
    return str(obj)


def save_design_artifacts(
    out_dir: Union[str, Path],
    *,
    design: Any,
    rows: Sequence[Mapping[str, Any]],
    meta: Mapping[str, Any],
    filename: str = "design.json",
) -> Path:
    """Persiste design JSON bajo ``out_dir`` (default ``design.json``)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    design_path = out / filename
    design_blob = None
    if hasattr(design, "to_dict"):
        try:
            design_blob = _json_safe(design.to_dict())
        except Exception:
            design_blob = None
    payload = {
        "meta": _json_safe(dict(meta)),
        "design": design_blob,
        "rows": _json_safe(list(rows)),
    }
    design_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return design_path


def load_design_artifacts(path: Union[str, Path]) -> Tuple[Optional[Any], List[Dict[str, Any]], Dict[str, Any]]:
    """Carga design.json → (design|None, rows, meta)."""
    ed = _require_doekit()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    meta = dict(data.get("meta") or {})
    rows = list(data.get("rows") or [])
    design = None
    raw = data.get("design")
    if raw:
        try:
            design = ed.Design.from_dict(raw)
        except Exception:
            design = None
    return design, rows, meta
