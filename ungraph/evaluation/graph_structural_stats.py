"""
Read-only structural statistics over a Neo4j database (nivel C — medición de grafo).

Used for build–evaluate–refine loops; does not mutate the graph.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, MutableMapping, Optional

from neo4j import Driver


@dataclass(frozen=True)
class GraphStructuralStats:
    """
    Lightweight snapshot: counts by primary node label and relationship type.

    Nodes with multiple labels are counted once under ``head(labels(n))`` to
    keep the query cheap; refine in phase C2 if multi-label accounting matters.
    """

    node_counts_by_label: Mapping[str, int]
    relationship_counts_by_type: Mapping[str, int]
    collected_at_utc: str
    database: str = "neo4j"

    def to_json_obj(self) -> Dict[str, Any]:
        d = asdict(self)
        d["node_counts_by_label"] = dict(self.node_counts_by_label)
        d["relationship_counts_by_type"] = dict(self.relationship_counts_by_type)
        return d

    @staticmethod
    def from_json_obj(data: Mapping[str, Any]) -> "GraphStructuralStats":
        return GraphStructuralStats(
            node_counts_by_label=dict(data["node_counts_by_label"]),
            relationship_counts_by_type=dict(data["relationship_counts_by_type"]),
            collected_at_utc=str(data["collected_at_utc"]),
            database=str(data.get("database", "neo4j")),
        )


def collect_structural_graph_stats(
    driver: Driver,
    *,
    database: str = "neo4j",
) -> GraphStructuralStats:
    """Run two aggregation queries; caller supplies a live Neo4j ``Driver``."""
    nodes_q = """
    MATCH (n)
    RETURN head(labels(n)) AS label, count(*) AS c
    """
    rels_q = """
    MATCH ()-[r]->()
    RETURN type(r) AS rel_type, count(*) AS c
    """
    node_counts: Dict[str, int] = {}
    rel_counts: Dict[str, int] = {}
    with driver.session(database=database) as session:
        for rec in session.run(nodes_q):
            lb = rec["label"]
            key = str(lb) if lb is not None else "UNKNOWN"
            node_counts[key] = int(rec["c"])
        for rec in session.run(rels_q):
            rt = rec["rel_type"]
            key = str(rt) if rt is not None else "UNKNOWN"
            rel_counts[key] = int(rec["c"])
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return GraphStructuralStats(
        node_counts_by_label=node_counts,
        relationship_counts_by_type=rel_counts,
        collected_at_utc=ts,
        database=database,
    )


def diff_structural_stats(
    baseline: GraphStructuralStats,
    current: GraphStructuralStats,
) -> Dict[str, Any]:
    """Symmetric diff of label/type counts (for notebooks and CI summaries)."""

    def _diff_maps(
        a: Mapping[str, int],
        b: Mapping[str, int],
    ) -> MutableMapping[str, Dict[str, int]]:
        keys = set(a) | set(b)
        out: Dict[str, Dict[str, int]] = {}
        for k in sorted(keys):
            ca, cb = a.get(k, 0), b.get(k, 0)
            if ca != cb:
                out[k] = {"baseline": ca, "current": cb, "delta": cb - ca}
        return out

    return {
        "nodes": _diff_maps(baseline.node_counts_by_label, current.node_counts_by_label),
        "relationships": _diff_maps(
            baseline.relationship_counts_by_type,
            current.relationship_counts_by_type,
        ),
    }


def collect_structural_graph_stats_from_settings() -> Optional[GraphStructuralStats]:
    """
    Convenience: driver from ``ungraph.utils.graph_operations.graph_session``.
    Returns ``None`` if Neo4j is not configured (no URI / password).
    """
    try:
        from ungraph.core.configuration import get_settings
        from ungraph.utils.graph_operations import graph_session
    except ImportError:
        return None

    s = get_settings()
    if not s.neo4j_uri or not s.neo4j_password:
        return None
    driver = graph_session()
    try:
        return collect_structural_graph_stats(
            driver,
            database=s.neo4j_database or "neo4j",
        )
    finally:
        try:
            driver.close()
        except Exception:
            pass
