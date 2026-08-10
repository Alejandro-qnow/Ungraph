"""
Métricas gold vs grafo Neo4j (B3/B4) — Y discriminativas para H_I.

La lógica de recall es pura (testeable sin Neo4j). Los fetchers usan el driver.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


def normalize_entity_name(name: str) -> str:
    """Normalización estable para matching gold ↔ Entity.name (case/espacios)."""
    s = (name or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def entity_recall_from_names(
    gold_entities: Sequence[str],
    graph_entity_names: Sequence[str],
) -> Dict[str, Any]:
    """Recall de entidades: fracción de gold cuyo nombre normalizado está en el grafo."""
    gold = [str(e) for e in gold_entities if str(e).strip()]
    gset = {normalize_entity_name(n) for n in graph_entity_names if str(n).strip()}
    if not gold:
        return {"entity_recall": None, "n_gold_entities": 0, "n_hit_entities": 0, "n_graph_entities": len(gset)}
    hits = sum(1 for e in gold if normalize_entity_name(e) in gset)
    return {
        "entity_recall": round(hits / len(gold), 4),
        "n_gold_entities": len(gold),
        "n_hit_entities": hits,
        "n_graph_entities": len(gset),
    }


def relation_pair_recall_from_names(
    gold_pairs: Sequence[Mapping[str, Any]],
    graph_entity_names: Sequence[str],
) -> Dict[str, Any]:
    """
    Recall de pares gold: ambos extremos existen como ``:Entity`` en el grafo.

    Adecuado para NER/MENTIONS (no exige arista tipada entre entidades).
    """
    gset = {normalize_entity_name(n) for n in graph_entity_names if str(n).strip()}
    pairs = [p for p in gold_pairs if isinstance(p, Mapping)]
    if not pairs:
        return {
            "relation_pair_recall": None,
            "n_gold_pairs": 0,
            "n_hit_pairs": 0,
        }
    hit = 0
    for p in pairs:
        s = normalize_entity_name(str(p.get("subject") or ""))
        o = normalize_entity_name(str(p.get("object") or ""))
        if s and o and s in gset and o in gset:
            hit += 1
    return {
        "relation_pair_recall": round(hit / len(pairs), 4),
        "n_gold_pairs": len(pairs),
        "n_hit_pairs": hit,
    }


def transform_metrics_from_graph_names(
    gold: Mapping[str, Any],
    graph_entity_names: Sequence[str],
) -> Dict[str, Any]:
    """Bloque transform (entity + pair recall) desde nombres de Entity en grafo."""
    out: Dict[str, Any] = {}
    out.update(entity_recall_from_names(list(gold.get("entities") or []), graph_entity_names))
    out.update(
        relation_pair_recall_from_names(list(gold.get("relation_pairs") or []), graph_entity_names)
    )
    return out


def fetch_entity_names(driver: Any, *, database: str = "neo4j") -> List[str]:
    """``MATCH (e:Entity) RETURN e.name``."""
    q = "MATCH (e:Entity) WHERE e.name IS NOT NULL RETURN collect(DISTINCT e.name) AS names"
    with driver.session(database=database) as session:
        rec = session.run(q).single()
    names = list((rec and rec.get("names")) or [])
    return [str(n) for n in names if n is not None]


def fetch_fact_provenance_counts(driver: Any, *, database: str = "neo4j") -> Tuple[int, int]:
    """``(n_facts, n_with_DERIVED_FROM)``."""
    q = """
    MATCH (f:Fact)
    OPTIONAL MATCH (f)-[d:DERIVED_FROM]->(:Chunk)
    WITH f, count(d) AS dc
    RETURN count(f) AS n_facts,
           sum(CASE WHEN dc > 0 THEN 1 ELSE 0 END) AS n_prov
    """
    with driver.session(database=database) as session:
        rec = session.run(q).single()
    if rec is None:
        return 0, 0
    n_facts = int(rec.get("n_facts") or 0)
    n_prov = int(rec.get("n_prov") or 0)
    return n_facts, n_prov


def fetch_chunk_count(driver: Any, *, database: str = "neo4j") -> int:
    with driver.session(database=database) as session:
        rec = session.run("MATCH (c:Chunk) RETURN count(c) AS n").single()
    return int((rec and rec.get("n")) or 0)


def evaluate_gold_against_neo4j(
    driver: Any,
    gold: Mapping[str, Any],
    *,
    database: str = "neo4j",
) -> Dict[str, Any]:
    """Transform block + evidence_coverage from live Neo4j."""
    from ungraph.evaluation.scorecard import evidence_coverage_from_counts

    names = fetch_entity_names(driver, database=database)
    transform = transform_metrics_from_graph_names(gold, names)
    n_facts, n_prov = fetch_fact_provenance_counts(driver, database=database)
    transform.update(evidence_coverage_from_counts(n_facts=n_facts, n_with_provenance=n_prov))
    transform["n_chunks"] = fetch_chunk_count(driver, database=database)
    return transform
