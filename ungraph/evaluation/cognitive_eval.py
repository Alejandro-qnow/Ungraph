"""
Evaluación *cognitiva* del razonamiento sobre el grafo (horizonte nivel C, fase C5).

No mide solo la extracción (¿cuántas entidades/relaciones?) sino el **valor que
agrega el razonamiento**: la capacidad del sistema de **aceptar lo verdadero y
rechazar lo falso** (faithfulness a nivel de statement). Es la "vara de medir" que
debe existir *antes* de construir la capa agentic propose→critique→verify: si no
podemos medirlo, no sabremos si el sistema "piensa mejor".

Método (inspirado en GraphRAG-Bench / faithfulness statement-level):

1. **Distractor injection.** A partir del gold se generan hechos FALSOS pero
   plausibles (pares de entidades reales que NO están relacionados en el gold).
2. Un **verificador anclado** (``Verifier``) decide, para cada hecho candidato,
   ``Curated`` (aceptar) o ``Invalid`` (rechazar), usando SOLO evidencia
   determinista (co-ocurrencia en el texto fuente). No hay LLM aquí.
3. Se miden precisión/recall del verificador tratando "aceptar un hecho verdadero"
   como acierto y "aceptar un distractor" como alucinación.
4. **Ablation:** el harness corre varios verificadores (p. ej. ``accept_all`` como
   piso vs. anclado) y compara. Cuando exista el crítico LLM, se enchufa a la misma
   interfaz ``Verifier`` y se compara con estas líneas base.

Sin dependencias de LLM/Neo4j: puro y ejecutable en CI.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ungraph.domain.value_objects.curation_state import (
    CURATION_STATE_CURATED,
    CURATION_STATE_INVALID,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------- helpers
def _normalize(name: str) -> str:
    s = (name or "").strip().lower()
    return re.sub(r"\s+", " ", s)


def _names_align(a: str, b: str, *, min_sub: int = 4) -> bool:
    """Igualdad o contención laxa (desajuste de span humano / NER)."""
    na, nb = _normalize(a), _normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    return len(na) >= min_sub and (na in nb or nb in na)


# --------------------------------------------------------------------- modelos
@dataclass(frozen=True)
class CandidateFact:
    """Un hecho (par sujeto→objeto) sometido a verificación.

    ``is_distractor`` es la verdad de referencia para la evaluación (no la ve el
    verificador): True si el hecho fue inyectado como falso.
    """

    subject: str
    object: str
    predicate_hint: str = ""
    is_distractor: bool = False


@dataclass
class VerificationOutcome:
    candidate: CandidateFact
    decision: str  # CURATION_STATE_CURATED | CURATION_STATE_INVALID
    score: float
    rationale: str

    @property
    def accepted(self) -> bool:
        return self.decision == CURATION_STATE_CURATED


class EvidenceIndex:
    """Índice de evidencia textual: ventanas deslizantes de oraciones del corpus.

    Ancla la verificación en el texto fuente: dos entidades "co-ocurren" si
    aparecen (match laxo) dentro de una misma ventana. Aproxima el soporte de
    evidencia sin extraer ni tocar el grafo.
    """

    def __init__(self, passages: Sequence[str]):
        self._passages: List[str] = [p.strip() for p in passages if p and p.strip()]

    @classmethod
    def from_text(cls, text: str, *, window_sentences: int = 2) -> "EvidenceIndex":
        raw = re.split(r"(?<=[.!?])\s+|\n+", text or "")
        sents = [s.strip() for s in raw if s and s.strip()]
        if not sents:
            return cls([])
        w = max(1, window_sentences)
        windows = [" ".join(sents[i : i + w]) for i in range(len(sents))]
        # incluir también oraciones sueltas para ventanas de 1
        return cls(windows + sents)

    def mentions(self, name: str) -> bool:
        return any(_names_align(name, p) for p in self._passages)

    def cooccur(self, a: str, b: str) -> bool:
        return any(_names_align(a, p) and _names_align(b, p) for p in self._passages)


# ------------------------------------------------------- verificadores (líneas base)
Verifier = Callable[[CandidateFact, EvidenceIndex], VerificationOutcome]


def accept_all_verifier(c: CandidateFact, ev: EvidenceIndex) -> VerificationOutcome:
    """Piso (propose-only): acepta todo. Sirve para cuantificar el ruido de base."""
    return VerificationOutcome(c, CURATION_STATE_CURATED, 1.0, "accept-all (baseline)")


def grounded_cooccurrence_verifier(
    c: CandidateFact, ev: EvidenceIndex
) -> VerificationOutcome:
    """Anclado: acepta solo si sujeto y objeto co-ocurren en alguna ventana de
    evidencia; rechaza si no hay soporte textual (faithfulness determinista)."""
    if ev.cooccur(c.subject, c.object):
        return VerificationOutcome(
            c, CURATION_STATE_CURATED, 1.0, "co-ocurrencia en evidencia"
        )
    if not (ev.mentions(c.subject) and ev.mentions(c.object)):
        return VerificationOutcome(
            c, CURATION_STATE_INVALID, 0.0, "entidad(es) sin mención en el corpus"
        )
    return VerificationOutcome(
        c, CURATION_STATE_INVALID, 0.0, "sin co-ocurrencia (soporte insuficiente)"
    )


# --------------------------------------------------------------- gold / candidatos
def load_gold(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _pair_in_gold(a: str, b: str, gold_pairs: Sequence[Dict[str, str]]) -> bool:
    for row in gold_pairs:
        gs, go = row.get("subject", ""), row.get("object", "")
        if (_names_align(a, gs) and _names_align(b, go)) or (
            _names_align(a, go) and _names_align(b, gs)
        ):
            return True
    return False


def build_distractors(
    entities: Sequence[str],
    gold_pairs: Sequence[Dict[str, str]],
    *,
    max_distractors: Optional[int] = None,
) -> List[CandidateFact]:
    """Genera hechos falsos plausibles: pares de entidades del gold que NO están
    relacionadas (ni en un sentido ni en el inverso)."""
    ents = [e for e in entities if e and e.strip()]
    out: List[CandidateFact] = []
    for i in range(len(ents)):
        for j in range(len(ents)):
            if i == j:
                continue
            a, b = ents[i], ents[j]
            if _pair_in_gold(a, b, gold_pairs):
                continue
            out.append(
                CandidateFact(a, b, predicate_hint="INJECTED", is_distractor=True)
            )
    # dedupe no-dirigido para no contar (a,b) y (b,a)
    seen: set = set()
    uniq: List[CandidateFact] = []
    for c in out:
        key = tuple(sorted((_normalize(c.subject), _normalize(c.object))))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    if max_distractors is not None:
        uniq = uniq[:max_distractors]
    return uniq


def make_candidates(gold: Dict[str, Any], **kw: Any) -> List[CandidateFact]:
    """Reales (del gold) + distractores inyectados, mezclados."""
    reales = [
        CandidateFact(
            r.get("subject", ""),
            r.get("object", ""),
            predicate_hint=r.get("predicate_hint", ""),
            is_distractor=False,
        )
        for r in gold.get("relation_pairs", [])
        if r.get("subject") and r.get("object")
    ]
    distractores = build_distractors(
        gold.get("entities", []), gold.get("relation_pairs", []), **kw
    )
    return reales + distractores


# ----------------------------------------------------------------- evaluación
def evaluate_verifier(
    candidates: Sequence[CandidateFact],
    verifier: Verifier,
    evidence: EvidenceIndex,
) -> Dict[str, Any]:
    """Corre el verificador y calcula la matriz de confianza del crítico.

    Clase positiva = "hecho verdadero aceptado". Un distractor aceptado es una
    alucinación (falso positivo); un real rechazado es un falso negativo.
    """
    outcomes = [verifier(c, evidence) for c in candidates]
    tp = fp = fn = tn = 0
    for o in outcomes:
        real = not o.candidate.is_distractor
        if o.accepted and real:
            tp += 1
        elif o.accepted and not real:
            fp += 1  # distractor colado (alucinación aceptada)
        elif (not o.accepted) and real:
            fn += 1  # verdadero rechazado
        else:
            tn += 1  # distractor correctamente rechazado

    n_real = tp + fn
    n_distractor = fp + tn
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / n_real if n_real else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {
        "n_candidates": len(candidates),
        "n_real": n_real,
        "n_distractor": n_distractor,
        "true_accept": tp,
        "false_accept": fp,
        "false_reject": fn,
        "true_reject": tn,
        "acceptance_precision": round(precision, 4),
        "real_recall": round(recall, 4),
        "f1": round(f1, 4),
        "distractor_rejection_rate": round(tn / n_distractor, 4) if n_distractor else 1.0,
        "hallucination_rate": round(fp / n_distractor, 4) if n_distractor else 0.0,
    }


DEFAULT_VERIFIERS: Dict[str, Verifier] = {
    "accept_all": accept_all_verifier,
    "grounded_cooccurrence": grounded_cooccurrence_verifier,
}


def run_cognitive_eval(
    corpus_path: Path,
    gold_path: Path,
    *,
    verifiers: Optional[Dict[str, Verifier]] = None,
    window_sentences: int = 2,
    max_distractors: Optional[int] = None,
) -> Dict[str, Any]:
    """Harness de evaluación cognitiva con *ablation* de verificadores.

    Args:
        corpus_path: Texto fuente (evidencia).
        gold_path: Gold con ``entities`` y ``relation_pairs``.
        verifiers: Mapa nombre→``Verifier`` a comparar. Por defecto, piso
            (``accept_all``) vs. anclado (``grounded_cooccurrence``).

    Returns:
        Reporte JSON-serializable con métricas por verificador y el ``delta`` del
        anclado respecto al piso (evidencia del valor del razonamiento).
    """
    gold = load_gold(gold_path)
    evidence = EvidenceIndex.from_text(
        Path(corpus_path).read_text(encoding="utf-8"),
        window_sentences=window_sentences,
    )
    candidates = make_candidates(gold, max_distractors=max_distractors)
    vs = verifiers or DEFAULT_VERIFIERS

    per_verifier = {
        name: evaluate_verifier(candidates, v, evidence) for name, v in vs.items()
    }
    report: Dict[str, Any] = {
        "corpus": str(corpus_path),
        "gold": str(gold_path),
        "candidates": {
            "total": len(candidates),
            "real": sum(1 for c in candidates if not c.is_distractor),
            "distractor": sum(1 for c in candidates if c.is_distractor),
        },
        "verifiers": per_verifier,
    }
    # ablation: mejora del anclado sobre el piso (si ambos están)
    if "accept_all" in per_verifier and "grounded_cooccurrence" in per_verifier:
        base = per_verifier["accept_all"]
        grounded = per_verifier["grounded_cooccurrence"]
        report["ablation_delta"] = {
            "acceptance_precision": round(
                grounded["acceptance_precision"] - base["acceptance_precision"], 4
            ),
            "hallucination_rate": round(
                grounded["hallucination_rate"] - base["hallucination_rate"], 4
            ),
            "f1": round(grounded["f1"] - base["f1"], 4),
        }
    return report
