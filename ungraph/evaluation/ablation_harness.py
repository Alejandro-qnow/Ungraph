"""
Harness de ablación parametrizado — base para el Diseño de Experimentos (fase 3).

Expone la evaluación del razonamiento como una **función objetivo**:
``run_trial(params) -> respuestas``. Cada ``PipelineParams`` es un punto en el espacio
de factores (pesos de señales, umbrales, ventana de evidencia, gates…) y cada corrida
devuelve las respuestas (F1, hallucination_rate, recall, …) en una fila plana.

Ese formato (lista de dicts factores+respuestas) es exactamente lo que consume
``doekit`` (vía pandas) para: screening de factores relevantes (``plackett_burman`` /
``definitive_screening`` + ``anova_table``/``main_effects``), superficie de respuesta
(``central_composite``) y augmentación secuencial (``propose_next_runs``).

Puro: sin LLM/Neo4j en import-time. El crítico LLM se inyecta (opcional).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from ungraph.domain.value_objects.ontology_profile import OntologyProfile
from ungraph.evaluation.cognitive_eval import (
    CandidateFact,
    EvidenceIndex,
    evaluate_verifier,
    load_gold,
    make_candidates,
)
from ungraph.reasoning.agentic import (
    FactCritic,
    SignalWeights,
    make_structural_verifier,
)

# Respuestas (variables de salida) que el DoE modela/optimiza.
RESPONSE_KEYS = (
    "f1",
    "hallucination_rate",
    "real_recall",
    "acceptance_precision",
    "distractor_rejection_rate",
)


@dataclass
class PipelineParams:
    """Un punto en el espacio de factores del pipeline de verify (DoE)."""

    accept_threshold: float = 0.6
    w_cooccurrence: float = 0.5
    w_both_mentioned: float = 0.2
    w_predicate_ontology: float = 0.3
    w_llm_faithfulness: float = 0.5
    use_ontology: bool = True
    ontology_gate: bool = False
    use_llm: bool = False
    llm_gate: bool = False
    llm_min_confidence: float = 0.6
    window_sentences: int = 2

    def to_flat(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def factor_names(cls) -> List[str]:
        return [f.name for f in fields(cls)]

    @classmethod
    def from_record(cls, rec: Dict[str, Any]) -> "PipelineParams":
        """Construye desde una fila (p. ej. de un diseño ``doekit``); ignora columnas
        extra y castea tipos según el default del campo."""
        kwargs: Dict[str, Any] = {}
        for f in fields(cls):
            if f.name in rec and rec[f.name] is not None:
                val = rec[f.name]
                if isinstance(f.default, bool):
                    kwargs[f.name] = bool(val) if not isinstance(val, str) else val.strip().lower() in ("1", "true", "yes", "on")
                elif isinstance(f.default, int) and not isinstance(f.default, bool):
                    kwargs[f.name] = int(round(float(val)))
                else:
                    kwargs[f.name] = float(val)
        return cls(**kwargs)

    def weights(self) -> SignalWeights:
        return SignalWeights(
            cooccurrence=self.w_cooccurrence,
            both_mentioned=self.w_both_mentioned,
            predicate_ontology=self.w_predicate_ontology,
            llm_faithfulness=self.w_llm_faithfulness,
        )


@dataclass
class EvalTask:
    """Corpus + candidatos (reales + distractores) + ontología, cargados una vez."""

    corpus_text: str
    candidates: List[CandidateFact]
    ontology: Optional[OntologyProfile] = None

    @classmethod
    def from_files(
        cls,
        corpus_path: Path,
        gold_path: Path,
        *,
        ontology: Optional[OntologyProfile] = None,
        max_distractors: Optional[int] = None,
    ) -> "EvalTask":
        gold = load_gold(gold_path)
        text = Path(corpus_path).read_text(encoding="utf-8")
        candidates = make_candidates(gold, max_distractors=max_distractors)
        return cls(corpus_text=text, candidates=candidates, ontology=ontology)


def run_trial(
    params: PipelineParams,
    task: EvalTask,
    *,
    llm_critic: Optional[FactCritic] = None,
) -> Dict[str, Any]:
    """Evalúa un punto de factores y devuelve una fila plana factores+respuestas.

    ``llm_critic`` solo se usa si ``params.use_llm``; sin él, el trial es determinista.
    """
    evidence = EvidenceIndex.from_text(
        task.corpus_text, window_sentences=params.window_sentences
    )
    ontology = task.ontology if params.use_ontology else None
    critic = llm_critic if params.use_llm else None
    verifier = make_structural_verifier(
        ontology=ontology,
        accept_threshold=params.accept_threshold,
        ontology_gate=params.ontology_gate,
        llm_critic=critic,
        llm_gate=params.llm_gate,
        weights=params.weights(),
    )
    metrics = evaluate_verifier(task.candidates, verifier, evidence)

    row: Dict[str, Any] = dict(params.to_flat())
    for k in RESPONSE_KEYS:
        row[k] = metrics.get(k)
    row["n_candidates"] = metrics.get("n_candidates")
    return row


def run_grid(
    params_list: Sequence[PipelineParams],
    task: EvalTask,
    *,
    llm_critic: Optional[FactCritic] = None,
) -> List[Dict[str, Any]]:
    """Corre múltiples puntos (p. ej. un diseño ``doekit``) y devuelve las filas."""
    return [run_trial(p, task, llm_critic=llm_critic) for p in params_list]


def run_design(
    design_records: Sequence[Dict[str, Any]],
    task: EvalTask,
    *,
    llm_critic: Optional[FactCritic] = None,
) -> List[Dict[str, Any]]:
    """Evalúa un diseño expresado como filas (columnas = factores). Cada fila se
    convierte a ``PipelineParams`` (``from_record``) y se corre. La salida (factores +
    respuestas) alimenta ``doekit.fit_linear_model`` / ``anova_table``."""
    params = [PipelineParams.from_record(r) for r in design_records]
    return run_grid(params, task, llm_critic=llm_critic)
