"""
ungraph.reasoning.agentic — capa de razonamiento propose → critique → verify.

Este módulo implementa el **verify anclado (grounded)**: la decisión de aceptar o
rechazar un hecho candidato NO la toma un LLM opinando, sino la suma de **señales
deterministas** —evidencia textual, consistencia ontológica y (a futuro) invariantes
del grafo—. Es la contraparte reproducible y auditable de un crítico LLM.

Diseño:
- ``propose`` lo hacen las fachadas de inferencia (``mine_knowledge`` / ``infer_*``)
  o el gold en evaluación; aquí trabajamos sobre ``CandidateFact``.
- ``critique_fact`` calcula un ``CritiqueReport`` con señales ponderadas y trazables.
- ``make_structural_verifier`` umbraliza el reporte y produce un ``Verifier``
  compatible con ``ungraph.evaluation.cognitive_eval`` — de modo que el crítico se
  **mide** con la misma vara (distractor injection / ablation) que las líneas base.

El resultado se expresa en ``curation_state`` (``Curated`` / ``Invalid``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from ungraph.domain.value_objects.curation_state import (
    CURATION_STATE_CURATED,
    CURATION_STATE_INVALID,
)
from ungraph.domain.value_objects.ontology_profile import OntologyProfile
from ungraph.evaluation.cognitive_eval import (
    CandidateFact,
    EvidenceIndex,
    VerificationOutcome,
    Verifier,
    _normalize,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------- crítico LLM (señal)
@dataclass(frozen=True)
class FactJudgment:
    """Juicio de un crítico sobre si la evidencia respalda un hecho candidato."""

    supported: bool
    confidence: float = 0.5
    rationale: str = ""


# Un crítico recibe el candidato y los pasajes de evidencia; devuelve un juicio.
FactCritic = Callable[[CandidateFact, List[str]], FactJudgment]


# --------------------------------------------------------------------- señales
@dataclass(frozen=True)
class Signal:
    """Una señal determinista de verificación (aporta ``weight`` si ``passed``)."""

    name: str
    passed: bool
    weight: float
    detail: str = ""


@dataclass
class CritiqueReport:
    """Resultado del ``critique``: señales + score normalizado en [0, 1]."""

    candidate: CandidateFact
    signals: List[Signal] = field(default_factory=list)
    hard_reject: bool = False

    @property
    def applicable_weight(self) -> float:
        return sum(s.weight for s in self.signals)

    @property
    def passed_weight(self) -> float:
        return sum(s.weight for s in self.signals if s.passed)

    @property
    def score(self) -> float:
        if self.hard_reject:
            return 0.0
        w = self.applicable_weight
        return (self.passed_weight / w) if w else 0.0

    @property
    def rationale(self) -> str:
        parts = [
            f"{s.name}={'ok' if s.passed else 'x'}({s.weight:g})" for s in self.signals
        ]
        return "; ".join(parts) if parts else "sin señales"


# --------------------------------------------------------------------- critique
# Pesos por defecto de cada señal (grounding textual domina).
W_COOCCURRENCE = 0.5
W_BOTH_MENTIONED = 0.2
W_PREDICATE_ONTOLOGY = 0.3
W_LLM_FAITHFULNESS = 0.5


def critique_fact(
    candidate: CandidateFact,
    evidence: EvidenceIndex,
    *,
    ontology: Optional[OntologyProfile] = None,
    ontology_gate: bool = False,
    llm_critic: Optional[FactCritic] = None,
    llm_gate: bool = False,
    llm_min_confidence: float = 0.6,
) -> CritiqueReport:
    """Evalúa un hecho candidato con señales deterministas (+ crítico LLM opcional).

    Señales:
    - ``evidence_cooccurrence``: sujeto y objeto co-ocurren en una ventana de
      evidencia (grounding textual fuerte).
    - ``both_entities_mentioned``: ambas entidades existen en el corpus.
    - ``predicate_in_ontology`` (solo si ``ontology``): el predicado propuesto está
      en ``allowed_relationships`` (consistencia de esquema).
    - ``llm_faithfulness`` (solo si ``llm_critic``): un crítico juzga si la evidencia
      respalda el hecho. Ataca los distractores que co-ocurren pero no están
      relacionados (donde las señales léxicas no discriminan).

    Args:
        ontology_gate: si True y hay ontología, un predicado fuera del esquema fuerza
            el rechazo (score 0) sin importar el resto de señales.
        llm_gate: si True y el crítico veta con confianza ≥ ``llm_min_confidence``,
            fuerza el rechazo (verify anclado en el juicio de faithfulness).
    """
    signals: List[Signal] = []

    cooccur = evidence.cooccur(candidate.subject, candidate.object)
    signals.append(
        Signal("evidence_cooccurrence", cooccur, W_COOCCURRENCE, "misma ventana")
    )

    both = evidence.mentions(candidate.subject) and evidence.mentions(candidate.object)
    signals.append(
        Signal("both_entities_mentioned", both, W_BOTH_MENTIONED, "existencia")
    )

    predicate_ok = True
    if ontology is not None:
        allowed = {_normalize(r) for r in ontology.allowed_relationships_set()}
        predicate_ok = _normalize(candidate.predicate_hint) in allowed
        signals.append(
            Signal(
                "predicate_in_ontology",
                predicate_ok,
                W_PREDICATE_ONTOLOGY,
                candidate.predicate_hint,
            )
        )
        if ontology_gate and not predicate_ok:
            # gate: predicado fuera del esquema -> rechazo duro (score 0)
            return CritiqueReport(
                candidate,
                signals
                + [Signal("ontology_gate", False, 0.0, "predicado no permitido")],
                hard_reject=True,
            )

    if llm_critic is not None:
        passages = evidence.context_for(candidate.subject, candidate.object)
        try:
            judgment = llm_critic(candidate, passages)
        except Exception as exc:  # noqa: BLE001 — degradación grácil a determinista
            logger.warning("llm_critic falló; se ignora la señal LLM: %s", exc)
            judgment = None
        if judgment is not None:
            signals.append(
                Signal(
                    "llm_faithfulness",
                    judgment.supported,
                    W_LLM_FAITHFULNESS,
                    judgment.rationale,
                )
            )
            if (
                llm_gate
                and not judgment.supported
                and judgment.confidence >= llm_min_confidence
            ):
                return CritiqueReport(
                    candidate,
                    signals + [Signal("llm_gate", False, 0.0, "veto de faithfulness")],
                    hard_reject=True,
                )

    return CritiqueReport(candidate, signals)


# --------------------------------------------------------------------- verify
def make_structural_verifier(
    *,
    ontology: Optional[OntologyProfile] = None,
    accept_threshold: float = 0.6,
    ontology_gate: bool = False,
    llm_critic: Optional[FactCritic] = None,
    llm_gate: bool = False,
) -> Verifier:
    """Construye un ``Verifier`` (plug-in de ``cognitive_eval``) que acepta un hecho
    si su ``CritiqueReport.score`` alcanza ``accept_threshold``.

    Reproducible y auditable: la decisión y su ``rationale`` derivan de señales
    trazables. El crítico LLM (``llm_critic``) es opcional y se suma como una señal
    más; sin él, el verify es 100% determinista.
    """

    def _verify(candidate: CandidateFact, evidence: EvidenceIndex) -> VerificationOutcome:
        report = critique_fact(
            candidate,
            evidence,
            ontology=ontology,
            ontology_gate=ontology_gate,
            llm_critic=llm_critic,
            llm_gate=llm_gate,
        )
        accepted = report.score >= accept_threshold
        return VerificationOutcome(
            candidate=candidate,
            decision=CURATION_STATE_CURATED if accepted else CURATION_STATE_INVALID,
            score=report.score,
            rationale=report.rationale,
        )

    return _verify


# --------------------------------------------------- crítico LLM (implementación)
_FAITHFULNESS_PROMPT = (
    "You are a strict fact-checker for a knowledge graph. Given EVIDENCE passages "
    "and a candidate FACT (subject, predicate, object), decide if the evidence "
    "DIRECTLY supports that the subject and object hold that specific relationship. "
    "Co-occurrence in the same sentence is NOT enough; the relation must be stated "
    "or clearly entailed.\n\n"
    "EVIDENCE:\n{evidence}\n\n"
    'FACT: ("{subject}") -[{predicate}]-> ("{object}")\n\n'
    'Answer ONLY a JSON object: {{"supported": true|false, "confidence": 0.0-1.0, '
    '"rationale": "<short>"}}'
)


def make_llm_fact_critic(
    llm: Any,
    *,
    prompt_template: str = _FAITHFULNESS_PROMPT,
) -> FactCritic:
    """Crítico de faithfulness respaldado por un chat model LangChain.

    ``llm`` es cualquier objeto con ``.invoke(str) -> mensaje con .content`` (p. ej.
    ``ChatOpenAI``). No hay import de ``langchain_*`` aquí: el modelo se inyecta desde
    el composition root, manteniendo el dominio limpio y el módulo importable sin LLM.
    """
    from ungraph.utils.llm_json import parse_llm_json_object

    def _critic(candidate: CandidateFact, passages: List[str]) -> FactJudgment:
        evidence_text = "\n".join(f"- {p}" for p in passages) or "(no evidence)"
        prompt = prompt_template.format(
            evidence=evidence_text,
            subject=candidate.subject,
            predicate=candidate.predicate_hint or "RELATED_TO",
            object=candidate.object,
        )
        resp = llm.invoke(prompt)
        content = getattr(resp, "content", resp)
        data = parse_llm_json_object(str(content))
        return FactJudgment(
            supported=bool(data.get("supported", False)),
            confidence=float(data.get("confidence", 0.5)),
            rationale=str(data.get("rationale", "")),
        )

    return _critic
