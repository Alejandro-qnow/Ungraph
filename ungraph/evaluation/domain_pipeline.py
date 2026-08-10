"""
Orquestación offline / online de una fila de arquitectura → DomainScorecard + ExperimentRun.

- Offline: sin Neo4j (laboratorio / CI).
- Online: wipe → ingest → Infer none|ner → Y desde Neo4j + probes top-k (H_I).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ungraph.evaluation.ablation_harness import EvalTask, PipelineParams, run_trial
from ungraph.evaluation.experiment_run import ExperimentRun
from ungraph.evaluation.probe_qa_eval import (
    evaluate_answer_containment_corpus,
    evaluate_answer_containment_topk,
    load_probe_queries,
)
from ungraph.evaluation.scorecard import (
    build_scorecard,
    evidence_coverage_from_counts,
    rag_qa_from_probe_eval,
    reasoning_from_cognitive,
)


def hi_wave_configs(
    *,
    chunk_size: int = 1024,
    chunk_overlap: int = 200,
    top_k: int = 5,
    rag: str = "text",
) -> List[Dict[str, Any]]:
    """Diseño mínimo oleada-2 H_I: Transform fijo, ``inference ∈ {none, ner}``."""
    base = {
        "chunking": "recursive",
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "rag": rag,
        "top_k": top_k,
    }
    return [
        {**base, "inference": "none", "design_row_id": "hi-0-none"},
        {**base, "inference": "ner", "design_row_id": "hi-1-ner"},
    ]


def family_wave_configs_from_capa0(
    capa0_architecture: Mapping[str, Any],
    *,
    families: Sequence[str] = ("ner", "pattern"),
) -> List[Dict[str, Any]]:
    """Oleada-3: recipe Capa 0 fija; solo cambia ``inference`` (familias Infer)."""
    base = {
        "chunking": str(capa0_architecture.get("chunking") or "recursive"),
        "chunk_size": int(capa0_architecture.get("chunk_size") or 1024),
        "chunk_overlap": int(capa0_architecture.get("chunk_overlap") or 200),
        "rag": str(capa0_architecture.get("rag") or "text"),
        "top_k": int(capa0_architecture.get("top_k") or 5),
        "mode": "online",
    }
    out: List[Dict[str, Any]] = []
    for fam in families:
        name = str(fam).lower().strip()
        if not name:
            continue
        out.append({**base, "inference": name, "design_row_id": f"fam-{name}"})
    if len(out) < 2:
        raise ValueError("family-wave requiere ≥2 familias Infer")
    return out


def chunk_wave_configs_from_capa0(
    capa0_architecture: Mapping[str, Any],
    *,
    chunk_sizes: Sequence[int] = (512, 1000, 1500),
    inference: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    H_chunk: Infer + rag + overlap fijos desde Capa 0; varía ``chunk_size``.
    """
    inf = str(inference or capa0_architecture.get("inference") or "ner").lower()
    base = {
        "chunking": str(capa0_architecture.get("chunking") or "recursive"),
        "chunk_overlap": int(capa0_architecture.get("chunk_overlap") or 200),
        "inference": inf,
        "rag": str(capa0_architecture.get("rag") or "text"),
        "top_k": int(capa0_architecture.get("top_k") or 5),
        "mode": "online",
    }
    sizes = sorted({int(s) for s in chunk_sizes if int(s) > 0})
    if len(sizes) < 2:
        raise ValueError("chunk-wave requiere ≥2 chunk_size distintos")
    return [
        {**base, "chunk_size": sz, "design_row_id": f"chunk-{sz}"} for sz in sizes
    ]


def _simple_chunk(text: str, *, strategy: str, chunk_size: int, overlap: int) -> List[str]:
    """Chunking offline mínimo (sin embeddings / LangChain)."""
    text = text or ""
    if strategy == "markdown_header":
        parts = re.split(r"(?m)(?=^#{1,3}\s)", text)
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            # further split oversized sections
            out: List[str] = []
            for p in parts:
                if len(p) <= chunk_size:
                    out.append(p)
                else:
                    out.extend(_window_chunks(p, chunk_size, overlap))
            return out
    return _window_chunks(text, chunk_size, overlap)


def _window_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    if chunk_size <= 0:
        return [text] if text else []
    step = max(1, chunk_size - max(0, overlap))
    chunks: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        chunks.append(text[i : i + chunk_size])
        i += step
    return chunks or ([text] if text else [])


def _entity_metrics(gold: Mapping[str, Any], text: str, inference: str) -> Dict[str, Any]:
    entities = [str(e) for e in (gold.get("entities") or [])]
    pairs = list(gold.get("relation_pairs") or [])
    if inference in ("none", "", "null"):
        return {
            "entity_recall": 0.0,
            "relation_pair_recall": 0.0,
            "n_entities": 0,
            "n_relations": 0,
        }
    lower = text.lower()
    hit_e = sum(1 for e in entities if e.lower() in lower)
    ent_recall = (hit_e / len(entities)) if entities else 0.0
    hit_p = 0
    for p in pairs:
        if not isinstance(p, Mapping):
            continue
        s = str(p.get("subject") or "").lower()
        o = str(p.get("object") or "").lower()
        if s and o and s in lower and o in lower:
            hit_p += 1
    rel_recall = (hit_p / len(pairs)) if pairs else 0.0
    return {
        "entity_recall": round(ent_recall, 4),
        "relation_pair_recall": round(rel_recall, 4),
        "n_entities": hit_e,
        "n_relations": hit_p,
    }


def _chunking_quality(chunks: Sequence[str], chunk_size: int) -> float:
    """Proxy intrínseco barato: fracción de chunks dentro de [0.25, 1.25]·chunk_size."""
    if not chunks or chunk_size <= 0:
        return 0.0
    lo, hi = 0.25 * chunk_size, 1.25 * chunk_size
    ok = sum(1 for c in chunks if lo <= len(c) <= hi)
    return round(ok / len(chunks), 4)


def _mrr_lexical(chunks: Sequence[str], probes: Sequence[Mapping[str, str]]) -> float:
    """MRR léxico: rank del primer chunk que contiene la answer."""
    if not probes or not chunks:
        return 0.0
    rr = 0.0
    n = 0
    for p in probes:
        ans = str(p.get("answer") or "").lower()
        if not ans:
            continue
        n += 1
        rank = None
        for i, c in enumerate(chunks, start=1):
            if ans in (c or "").lower():
                rank = i
                break
        if rank is not None:
            rr += 1.0 / rank
    return round(rr / n, 4) if n else 0.0


def run_architecture_offline(
    *,
    domain: str,
    architecture: Mapping[str, Any],
    corpus_paths: Sequence[Path],
    gold_path: Path,
    design_id: str = "",
    design_row_id: str = "",
    seed: Optional[int] = None,
    git_sha: str = "",
) -> Tuple[ExperimentRun, Dict[str, Any]]:
    """
    Ejecuta una arquitectura en modo offline y devuelve (ExperimentRun, doe_row).
    """
    t0 = time.perf_counter()
    gold = json.loads(Path(gold_path).read_text(encoding="utf-8"))
    texts = [Path(p).read_text(encoding="utf-8") for p in corpus_paths]
    corpus = "\n\n".join(texts)
    probes = load_probe_queries(gold)

    chunking = str(architecture.get("chunking") or "recursive")
    chunk_size = int(architecture.get("chunk_size") or 1000)
    overlap = int(architecture.get("chunk_overlap") or 200)
    inference = str(architecture.get("inference") or "ner")
    rag = str(architecture.get("rag") or "text")

    t_extract = time.perf_counter()
    chunks = _simple_chunk(corpus, strategy=chunking, chunk_size=chunk_size, overlap=overlap)
    extract = {
        "chunking_quality_score": _chunking_quality(chunks, chunk_size),
        "n_chunks": len(chunks),
        "mrr": _mrr_lexical(chunks, probes),
    }
    extract_s = time.perf_counter() - t_extract

    t_tr = time.perf_counter()
    transform = _entity_metrics(gold, corpus, inference)
    # provenance offline: facts anclados = entidades+pares hallados si hay inferencia
    n_facts = int(transform.get("n_entities") or 0) + int(transform.get("n_relations") or 0)
    if inference in ("none", "", "null"):
        transform.update(evidence_coverage_from_counts(n_facts=0, n_with_provenance=0))
    else:
        transform.update(
            evidence_coverage_from_counts(n_facts=n_facts, n_with_provenance=n_facts)
        )
    transform_s = time.perf_counter() - t_tr

    t_r = time.perf_counter()
    # reasoning via cognitive / structural verifier (determinista)
    try:
        task = EvalTask.from_files(corpus_paths[0], gold_path)
        trial = run_trial(PipelineParams(), task)
        reasoning = reasoning_from_cognitive(trial)
    except Exception as exc:
        reasoning = {"f1": 0.0, "hallucination_rate": 1.0, "error": str(exc)}
    # sin inferencia: no hay hechos nuevos que verificar → un piso ET
    if inference in ("none", "", "null"):
        reasoning = {
            "f1": 0.0,
            "hallucination_rate": 0.0,
            "distractor_rejection_rate": reasoning.get("distractor_rejection_rate", 0.0),
            "real_recall": 0.0,
        }
    reasoning_s = time.perf_counter() - t_r

    t_qa = time.perf_counter()
    # rag text → corpus; vector offline ≈ chunks unidos (misma containment, distinto mrr ya en extract)
    ctx_texts = texts if rag == "text" else chunks
    probe_metrics = evaluate_answer_containment_corpus(probes, ctx_texts)
    rag_qa = rag_qa_from_probe_eval(probe_metrics)
    if extract.get("mrr") is not None:
        rag_qa["mrr"] = extract["mrr"]
    rag_s = time.perf_counter() - t_qa

    total_s = time.perf_counter() - t0
    efficiency = {
        "latency_s": round(total_s, 4),
        "latency_extract_s": round(extract_s, 4),
        "latency_transform_s": round(transform_s, 4),
        "latency_reasoning_s": round(reasoning_s, 4),
        "latency_rag_s": round(rag_s, 4),
    }

    arch = {
        "chunking": chunking,
        "chunk_size": chunk_size,
        "chunk_overlap": overlap,
        "inference": inference,
        "rag": rag,
        "top_k": int(architecture.get("top_k") or 5),
    }
    card = build_scorecard(
        domain,
        arch,
        extract=extract,
        transform=transform,
        reasoning=reasoning,
        rag_qa=rag_qa,
        efficiency=efficiency,
    )
    run = ExperimentRun.from_scorecard(
        card,
        git_sha=git_sha,
        seed=seed,
        gold_path=str(gold_path),
        corpus_paths=[str(p) for p in corpus_paths],
        design_id=design_id,
        design_row_id=str(design_row_id),
        notes="offline domain pipeline",
    )
    return run, run.to_doe_row()


def load_domain_bundle(
    domain_dir: Path,
    *,
    doe_path: Optional[Path] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], Path, List[Path]]:
    """Carga manifest + doe + gold + corpus paths (relativos al domain_dir)."""
    import yaml

    manifest_path = domain_dir / "manifest.yaml"
    doe_file = Path(doe_path) if doe_path else domain_dir / "doe.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    doe = yaml.safe_load(doe_file.read_text(encoding="utf-8")) if doe_file.exists() else {}
    gold_name = (manifest or {}).get("gold") or "gold.json"
    gold_path = domain_dir / gold_name
    corpus_rel = list((manifest or {}).get("corpus") or [])
    # Prefer seed gold-aligned doc first for offline smoke
    corpus_paths = [domain_dir / c for c in corpus_rel if (domain_dir / c).exists()]
    if not corpus_paths:
        seed = domain_dir / "corpus" / "kg_survey.md"
        if seed.exists():
            corpus_paths = [seed]
    return dict(manifest or {}), dict(doe or {}), gold_path, corpus_paths


def run_architecture_online(
    *,
    domain: str,
    architecture: Mapping[str, Any],
    corpus_paths: Sequence[Path],
    gold_path: Path,
    database: str = "neo4j",
    design_id: str = "hi-wave-2",
    design_row_id: str = "",
    seed: Optional[int] = None,
    git_sha: str = "",
    wipe: bool = True,
    setup_indexes: bool = True,
) -> Tuple[ExperimentRun, Dict[str, Any]]:
    """
    Online cell: wipe → ingest (Transform fijo) → Infer none|ner|pattern|llm → Y Neo4j + top-k.

    Requiere Neo4j. ``ner`` → spaCy; ``pattern`` → léxico simbólico (sin API);
    ``llm`` → OpenAI key.
    """
    from ungraph.application.dependencies import create_ingest_document_use_case
    from ungraph.core.configuration import Settings, get_settings
    from ungraph.evaluation.neo4j_gold_metrics import evaluate_gold_against_neo4j
    from ungraph.evaluation.retrieval_context_eval import (
        retrieve_text_contexts,
        retrieve_vector_contexts,
    )
    from ungraph.infrastructure.services.neo4j_index_service import Neo4jIndexService
    from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService
    from ungraph.utils.graph_operations import graph_session

    t0 = time.perf_counter()
    gold = json.loads(Path(gold_path).read_text(encoding="utf-8"))
    probes = load_probe_queries(gold)
    paths = [Path(p) for p in corpus_paths]
    if not paths:
        raise FileNotFoundError("corpus_paths vacío")

    chunk_size = int(architecture.get("chunk_size") or 1024)
    overlap = int(architecture.get("chunk_overlap") or 200)
    inference = str(architecture.get("inference") or "ner").lower()
    rag = str(architecture.get("rag") or "text").lower()
    top_k = int(architecture.get("top_k") or 5)

    settings = get_settings()
    db = database or settings.neo4j_database or "neo4j"

    # --- wipe + indexes ---
    t_w = time.perf_counter()
    idx = Neo4jIndexService(database=db)
    try:
        if wipe:
            idx.clean_graph()
        if setup_indexes:
            try:
                idx.setup_all_indexes()
            except Exception:
                # índices pueden existir / API vector distinta; ingest suele tolerarlo
                pass
    finally:
        idx.close()
    wipe_s = time.perf_counter() - t_w

    # --- ingest ---
    t_ing = time.perf_counter()
    allowed_inf = {"none", "", "null", "ner", "pattern", "llm"}
    if inference not in allowed_inf:
        raise ValueError(
            f"online solo soporta inference=none|ner|pattern|llm (recibido {inference!r})"
        )
    mode_for_factory = "ner" if inference in ("none", "", "null") else inference
    # Preserve OpenAI key / env for llm; force mode for factory
    ingest_settings = settings.model_copy(update={"inference_mode": mode_for_factory})
    use_case = create_ingest_document_use_case(
        settings=ingest_settings,
        database=db,
        inference_language="en",
    )
    if inference in ("none", "", "null"):
        use_case.inference_service = None
    elif use_case.inference_service is None:
        if inference == "ner":
            raise RuntimeError(
                "inference=ner requiere spaCy + en_core_web_sm. "
                "Instala: uv sync --extra experiments --extra infer-en && "
                'uv pip install "https://github.com/explosion/spacy-models/releases/'
                'download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"'
            )
        if inference == "llm":
            raise RuntimeError(
                "inference=llm requiere UNGRAPH_OPENAI_API_KEY o OPENAI_API_KEY "
                "y dependencias LLM (ungraph[infer] / langchain-openai)."
            )
        raise RuntimeError(f"inference={inference!r}: no se pudo crear InferenceService")

    all_chunks: List[Any] = []
    for path in paths:
        chunks = use_case.execute(
            path,
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            clean_text=True,
        )
        all_chunks.extend(chunks or [])
    ingest_s = time.perf_counter() - t_ing

    # --- transform Y from Neo4j ---
    t_tr = time.perf_counter()
    driver = graph_session()
    try:
        transform = evaluate_gold_against_neo4j(driver, gold, database=db)
    finally:
        pass  # shared driver lifecycle via graph_session
    transform_s = time.perf_counter() - t_tr

    extract = {
        "n_chunks": int(transform.pop("n_chunks", None) or len(all_chunks)),
        "chunking_quality_score": _chunking_quality(
            [getattr(c, "page_content", "") or "" for c in all_chunks],
            chunk_size,
        ),
    }

    # --- reasoning (determinista, mismo verify offline; piso si none) ---
    t_r = time.perf_counter()
    try:
        task = EvalTask.from_files(paths[0], gold_path)
        trial = run_trial(PipelineParams(), task)
        reasoning = reasoning_from_cognitive(trial)
    except Exception as exc:
        reasoning = {"f1": 0.0, "hallucination_rate": 1.0, "error": str(exc)}
    if inference in ("none", "", "null"):
        reasoning = {
            "f1": 0.0,
            "hallucination_rate": 0.0,
            "distractor_rejection_rate": reasoning.get("distractor_rejection_rate", 0.0),
            "real_recall": 0.0,
        }
    reasoning_s = time.perf_counter() - t_r

    # --- B2 probes on top-k only ---
    t_qa = time.perf_counter()
    search = Neo4jSearchService(database=db)
    emb_svc = use_case.embedding_service

    def _retrieve(q: str) -> List[str]:
        if rag == "vector":
            return retrieve_vector_contexts(search, emb_svc, q, limit=top_k)
        if rag == "hybrid":
            from ungraph.evaluation.retrieval_context_eval import retrieve_hybrid_contexts

            return retrieve_hybrid_contexts(search, emb_svc, q, limit=top_k)
        return retrieve_text_contexts(search, q, limit=top_k)

    probe_metrics = evaluate_answer_containment_topk(probes, _retrieve)
    # hit@k proxy: same as answer_correctness for containment@k
    if probe_metrics.get("answer_correctness") is not None:
        extract["hit_at_k"] = probe_metrics["answer_correctness"]
        extract["mrr"] = None  # no rank from containment-only; avoid lexical corpus MRR
    rag_qa = rag_qa_from_probe_eval(probe_metrics)
    rag_s = time.perf_counter() - t_qa

    total_s = time.perf_counter() - t0
    efficiency = {
        "latency_s": round(total_s, 4),
        "latency_wipe_s": round(wipe_s, 4),
        "latency_ingest_s": round(ingest_s, 4),
        "latency_transform_s": round(transform_s, 4),
        "latency_reasoning_s": round(reasoning_s, 4),
        "latency_rag_s": round(rag_s, 4),
    }

    arch = {
        "chunking": str(architecture.get("chunking") or "recursive"),
        "chunk_size": chunk_size,
        "chunk_overlap": overlap,
        "inference": inference,
        "rag": rag,
        "top_k": top_k,
        "mode": "online",
    }
    card = build_scorecard(
        domain,
        arch,
        extract=extract,
        transform=transform,
        reasoning=reasoning,
        rag_qa=rag_qa,
        efficiency=efficiency,
    )
    run = ExperimentRun.from_scorecard(
        card,
        git_sha=git_sha,
        seed=seed,
        gold_path=str(gold_path),
        corpus_paths=[str(p) for p in paths],
        design_id=design_id,
        design_row_id=str(design_row_id or architecture.get("design_row_id") or ""),
        notes="online H_I domain pipeline (Neo4j + spaCy|none)",
    )
    return run, run.to_doe_row()
