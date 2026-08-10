"""
Probe-QA offline: answer containment sobre ``gold.json`` (sin LLM).

Mide si las respuestas esperadas de ``graphrag_probe_queries`` aparecen en el
contexto recuperado (lista de strings) o, en modo dry-run, en el corpus/chunks.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Union


def load_probe_queries(gold: Union[Path, str, Mapping[str, Any]]) -> List[Dict[str, str]]:
    """Carga probes ``{query, answer}`` desde gold path o dict ya parseado."""
    if isinstance(gold, Mapping):
        data = gold
    else:
        data = json.loads(Path(gold).read_text(encoding="utf-8"))
    probes = list(data.get("graphrag_probe_queries") or [])
    out: List[Dict[str, str]] = []
    for p in probes:
        if not isinstance(p, Mapping):
            continue
        q = str(p.get("query") or "").strip()
        a = str(p.get("answer") or "").strip()
        if q and a:
            out.append({"query": q, "answer": a})
    return out


def _normalize(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def answer_contained(answer: str, contexts: Sequence[str]) -> bool:
    """
    True si la respuesta aparece en algún contexto.

    Frases con ≥4 tokens alfanuméricos requieren **substring exacto**
    (normalizado); el fallback token-AND solo aplica a respuestas cortas
    (1–3 tokens) para no saturar Y con matches espurios.
    """
    ans = _normalize(answer)
    if not ans:
        return False
    joined = _normalize("\n".join(contexts or []))
    if ans in joined:
        return True
    tokens = [t for t in re.findall(r"[a-z0-9_]{3,}", ans)]
    if not tokens:
        return False
    if len(tokens) >= 4:
        return False
    return all(t in joined for t in tokens)


def evaluate_answer_containment(
    probes: Sequence[Mapping[str, str]],
    contexts_by_query: Mapping[str, Sequence[str]],
) -> Dict[str, Any]:
    """
    ``answer_correctness`` = fracción de probes cuya respuesta está contenida
    en los contextos asociados a su query.
    """
    if not probes:
        return {
            "answer_correctness": None,
            "n_probes": 0,
            "n_correct": 0,
            "per_probe": [],
        }
    per: List[Dict[str, Any]] = []
    n_ok = 0
    for p in probes:
        q = str(p.get("query") or "")
        a = str(p.get("answer") or "")
        ctxs = list(contexts_by_query.get(q) or [])
        ok = answer_contained(a, ctxs)
        if ok:
            n_ok += 1
        per.append({"query": q, "answer": a, "correct": ok, "n_contexts": len(ctxs)})
    return {
        "answer_correctness": round(n_ok / len(probes), 4),
        "n_probes": len(probes),
        "n_correct": n_ok,
        "per_probe": per,
    }


def evaluate_answer_containment_corpus(
    probes: Sequence[Mapping[str, str]],
    corpus_texts: Sequence[str],
) -> Dict[str, Any]:
    """Dry-run / baseline: usa el corpus completo como único contexto por probe."""
    contexts_by_query = {str(p.get("query") or ""): list(corpus_texts) for p in probes}
    return evaluate_answer_containment(probes, contexts_by_query)


def evaluate_answer_containment_topk(
    probes: Sequence[Mapping[str, str]],
    retrieve_fn,
) -> Dict[str, Any]:
    """
    B2: containment sobre contextos **recuperados** por probe.

    ``retrieve_fn(query: str) -> Sequence[str]`` debe devolver solo top-k
    (p. ej. via ``SearchService``), nunca el corpus completo.
    """
    contexts_by_query: Dict[str, List[str]] = {}
    for p in probes:
        q = str(p.get("query") or "")
        if not q:
            continue
        contexts_by_query[q] = list(retrieve_fn(q) or [])
    out = evaluate_answer_containment(probes, contexts_by_query)
    out["eval_mode"] = "topk_retrieved"
    return out


def probes_to_retrieval_probes(probes: Sequence[Mapping[str, str]]):
    """Convierte probes gold → ``RetrievalProbe`` (keywords = tokens de la answer)."""
    from ungraph.evaluation.chunking_downstream_eval import RetrievalProbe

    out = []
    for p in probes:
        ans = str(p.get("answer") or "")
        kws = re.findall(r"[A-Za-z0-9_]{3,}", ans) or [ans]
        out.append(RetrievalProbe.make(str(p.get("query") or ""), kws))
    return out
