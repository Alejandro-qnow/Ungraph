"""Fusión de nodos :Entity en Neo4j (post-inferencia)."""

from __future__ import annotations

import logging

from ungraph.domain.services.entity_graph_maintenance import EntityGraphMaintenanceService
from ungraph.utils.graph_operations import graph_session
from ungraph.utils.neo4j_infer_reltype import is_safe_interpolated_reltype

logger = logging.getLogger(__name__)

_GROUPS_CASE_INSENSITIVE = """
MATCH (e:Entity)
WITH toLower(trim(toString(e.name))) AS k, collect(elementId(e)) AS ids
WHERE size(ids) > 1
RETURN ids
"""

_GROUPS_STRIP_PUNCT = """
MATCH (e:Entity)
WITH toLower(trim(replace(replace(toString(e.name), '.', ''), ',', ''))) AS k,
     collect(elementId(e)) AS ids
WHERE size(ids) > 1
RETURN ids
"""

_LIST_RELS_ON_DUP = """
MATCH (dup) WHERE elementId(dup) = $dup_id
MATCH (dup)-[r]-()
RETURN DISTINCT elementId(r) AS rel_eid, type(r) AS rt
"""


def _reroute_relationship(tx, rel_eid: str, rt: str, keep_id: str, dup_id: str) -> None:
    """Mueve una arista que toca ``dup`` para que use ``keep``; borra la arista antigua."""
    if not is_safe_interpolated_reltype(rt):
        logger.warning("Skipping reroute: unsafe relationship type %r", rt)
        return
    row = tx.run(
        """
        MATCH ()-[r]->()
        WHERE elementId(r) = $rel_eid
        RETURN elementId(startNode(r)) AS sid, elementId(endNode(r)) AS eid,
               properties(r) AS props
        """,
        rel_eid=rel_eid,
    ).single()
    if row is None:
        return
    sid: str = row["sid"]
    eid: str = row["eid"]
    props = dict(row["props"])

    if sid == dup_id and eid == dup_id:
        q = f"""
        MATCH (keep) WHERE elementId(keep) = $keep_id
        MATCH ()-[r]->()
        WHERE elementId(r) = $rel_eid
        MERGE (keep)-[r2:`{rt}`]->(keep)
        SET r2 = $props
        DELETE r
        """
        tx.run(q, keep_id=keep_id, rel_eid=rel_eid, props=props)
        return

    if sid == dup_id:
        q = f"""
        MATCH (keep) WHERE elementId(keep) = $keep_id
        MATCH (other) WHERE elementId(other) = $other_id
        MATCH ()-[r]->()
        WHERE elementId(r) = $rel_eid
        MERGE (keep)-[r2:`{rt}`]->(other)
        SET r2 = $props
        DELETE r
        """
        tx.run(
            q,
            keep_id=keep_id,
            other_id=eid,
            rel_eid=rel_eid,
            props=props,
        )
        return

    if eid == dup_id:
        q = f"""
        MATCH (keep) WHERE elementId(keep) = $keep_id
        MATCH (other) WHERE elementId(other) = $other_id
        MATCH ()-[r]->()
        WHERE elementId(r) = $rel_eid
        MERGE (other)-[r2:`{rt}`]->(keep)
        SET r2 = $props
        DELETE r
        """
        tx.run(
            q,
            keep_id=keep_id,
            other_id=sid,
            rel_eid=rel_eid,
            props=props,
        )
        return


class Neo4jEntityGraphMaintenanceService(EntityGraphMaintenanceService):
    def __init__(self, database: str = "neo4j") -> None:
        self._database = database

    @staticmethod
    def _merge_pair_tx(tx, keep_id: str, dup_id: str) -> None:
        rel_rows = list(tx.run(_LIST_RELS_ON_DUP, dup_id=dup_id))
        seen: set[str] = set()
        for row in rel_rows:
            rel_eid = row["rel_eid"]
            if rel_eid in seen:
                continue
            seen.add(rel_eid)
            _reroute_relationship(tx, rel_eid, row["rt"], keep_id, dup_id)
        tx.run(
            "MATCH (dup:Entity) WHERE elementId(dup) = $dup_id DETACH DELETE dup",
            dup_id=dup_id,
        )

    def _merge_round(self, group_cypher: str) -> int:
        removed = 0
        driver = graph_session()
        try:
            with driver.session(database=self._database) as session:
                while True:
                    rows = list(session.run(group_cypher))
                    if not rows:
                        break
                    for row in rows:
                        ids = sorted(row["ids"])
                        keep_id = ids[0]
                        for dup_id in ids[1:]:
                            session.execute_write(
                                Neo4jEntityGraphMaintenanceService._merge_pair_tx,
                                keep_id,
                                dup_id,
                            )
                            removed += 1
        finally:
            try:
                driver.close()
            except Exception as e:
                logger.debug("driver close: %s", e)
        return removed

    def consolidate_entities_case_insensitive(self) -> int:
        return self._merge_round(_GROUPS_CASE_INSENSITIVE)

    def resolve_entities_strip_punctuation(self) -> int:
        return self._merge_round(_GROUPS_STRIP_PUNCT)
