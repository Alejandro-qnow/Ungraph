"""
InferenceService simbólico/determinista: frases con patrón léxico + co-ocurrencia.

Familia Infer distinta de spaCy NER (transductiva) y de LLM (neural). Sin API keys.
Útil para oleada-3 (D5): comparar familias bajo las mismas Y de capa B.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import List, Optional, Set, Tuple

from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.entities.entity import Entity
from ungraph.domain.entities.fact import Fact
from ungraph.domain.entities.relation import Relation
from ungraph.domain.services.inference_service import InferenceService

logger = logging.getLogger(__name__)

EXTRACTION_METHOD = "lexical_pattern"

# Multi-word Title Case / Camel-ish phrases; single Cap words length ≥ 3
_MULTI = re.compile(
    r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+){1,4})\b"
)
_SINGLE = re.compile(r"\b([A-Z][a-zA-Z0-9]{2,})\b")

_STOP = frozenset(
    {
        "The",
        "This",
        "That",
        "These",
        "Those",
        "A",
        "An",
        "And",
        "Or",
        "But",
        "For",
        "With",
        "From",
        "Into",
        "In",
        "On",
        "At",
        "To",
        "Of",
        "By",
        "As",
        "Is",
        "Are",
        "Was",
        "Were",
        "Be",
        "Been",
        "Being",
        "It",
        "Its",
        "We",
        "Our",
        "You",
        "Your",
        "They",
        "Their",
        "He",
        "She",
        "His",
        "Her",
        "Figure",
        "Table",
        "Section",
        "Chapter",
        "Abstract",
        "Introduction",
        "Conclusion",
        "References",
        "Appendix",
    }
)


def _candidate_spans(text: str) -> List[str]:
    found: List[str] = []
    seen: Set[str] = set()
    for m in _MULTI.finditer(text):
        span = " ".join(m.group(1).split())
        if span in _STOP or span in seen:
            continue
        seen.add(span)
        found.append(span)
    covered = " ".join(found)
    for m in _SINGLE.finditer(text):
        span = m.group(1)
        if span in _STOP or span in seen:
            continue
        # skip if already part of a multi-word hit
        if span in covered:
            continue
        seen.add(span)
        found.append(span)
    return found


class LexicalPatternInferenceService(InferenceService):
    """
    Extracción simbólica: patrones tipográficos + CO_OCCURS_WITH + MENTIONS.

    ``extraction_method`` = ``lexical_pattern`` para distinguir de ``spacy`` / LLM.
    """

    def extract_entities(self, chunk: Chunk) -> List[Entity]:
        if not chunk or not chunk.page_content:
            raise ValueError("Chunk cannot be empty")
        entities: List[Entity] = []
        for name in _candidate_spans(chunk.page_content):
            entities.append(
                Entity(
                    id=f"entity_{uuid.uuid4().hex[:8]}",
                    name=name,
                    type="CONCEPT",
                    mentions=[chunk.id],
                    extraction_method=EXTRACTION_METHOD,
                )
            )
        logger.debug(
            "lexical_pattern: %s entities from chunk %s", len(entities), chunk.id
        )
        return entities

    def extract_relations(
        self, chunk: Chunk, entities: List[Entity]
    ) -> List[Relation]:
        if not entities:
            return []
        relations: List[Relation] = []
        seen: Set[Tuple[str, str]] = set()
        for i, src in enumerate(entities):
            for tgt in entities[i + 1 :]:
                a, b = sorted((src.name, tgt.name))
                key = (a, b)
                if key in seen:
                    continue
                seen.add(key)
                relations.append(
                    Relation(
                        id=f"rel_{uuid.uuid4().hex[:8]}",
                        source_entity_id=src.id,
                        target_entity_id=tgt.id,
                        relation_type="CO_OCCURS_WITH",
                        confidence=0.55,
                        provenance_ref=chunk.id,
                        extraction_method=EXTRACTION_METHOD,
                        source_entity_name=src.name,
                        target_entity_name=tgt.name,
                    )
                )
        return relations

    def infer_facts(
        self, chunk: Chunk, entities: Optional[List[Entity]] = None
    ) -> List[Fact]:
        if not chunk or not chunk.page_content:
            raise ValueError("Chunk cannot be empty")
        ent_list = entities if entities is not None else self.extract_entities(chunk)
        facts: List[Fact] = []
        for entity in ent_list:
            facts.append(
                Fact(
                    id=f"fact_{uuid.uuid4().hex[:8]}",
                    subject=chunk.id,
                    predicate="MENTIONS",
                    object=entity.name,
                    confidence=0.6,
                    provenance_ref=chunk.id,
                    object_entity_type=entity.type,
                )
            )
        logger.info(
            "lexical_pattern: %s facts from chunk %s", len(facts), chunk.id
        )
        return facts
