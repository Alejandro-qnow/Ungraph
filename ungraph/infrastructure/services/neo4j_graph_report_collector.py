"""
Recolector de introspección Neo4j para reportes ETI.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from neo4j.graph import Node as Neo4jNode
from neo4j.graph import Relationship as Neo4jRelationship

from ungraph.domain.services.graph_report_collector import GraphReportCollector
from ungraph.utils.graph_operations import graph_session

logger = logging.getLogger(__name__)

REFERENCE_MODEL_ASCII = """
(:Document {id, source, doc_type, metadata})
  -[:HAS_CHUNK]->
(:Chunk {id, text, embedding, chunk_index, document_id, token_count})
  -[:MENTIONS]->
(:Entity {name, type, source, embedding?})

(:Entity)-[:RELATED_TO {relation_type, confidence}]->(:Entity)
(:Chunk)-[:HAS_FACT]->(:Fact {subject, predicate, object, confidence})

Patrón operativo frecuente en Ungraph (File/Page/Chunk):

(:File)-[:CONTAINS]->(:Page)-[:HAS_CHUNK]->(:Chunk)-[:NEXT_CHUNK]->(:Chunk)
""".strip()


def _json_safe(v: Any) -> Any:
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, float) and (v != v):  # NaN
        return None
    if isinstance(v, (list, tuple)):
        return [_json_safe(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _json_safe(val) for k, val in v.items()}
    if isinstance(v, Neo4jNode):
        return dict(v)
    if isinstance(v, Neo4jRelationship):
        return {"type": v.type, **dict(v)}
    return str(v)


def _caption_for_node(n: Neo4jNode) -> str:
    props = dict(n)
    for key in ("name", "chunk_id", "filename", "title", "id"):
        if key in props and props[key] is not None:
            s = str(props[key])
            return s[:120] if len(s) > 120 else s
    labs = list(n.labels)
    return labs[0] if labs else n.element_id


def _node_to_nvl(n: Neo4jNode) -> dict[str, Any]:
    return {
        "id": str(n.element_id),
        "caption": _caption_for_node(n),
        "labels": list(n.labels),
        "properties": {k: _json_safe(v) for k, v in dict(n).items()},
        "size": 12.0,
    }


def _rel_to_nvl(r: Neo4jRelationship) -> dict[str, Any]:
    start = getattr(r, "start_node", None)
    end = getattr(r, "end_node", None)
    if start is None or end is None:
        nodes = getattr(r, "nodes", None)
        if nodes and len(nodes) >= 2:
            start, end = nodes[0], nodes[1]
        else:
            raise ValueError("Relationship without start/end nodes")
    return {
        "id": str(r.element_id),
        "from": str(start.element_id),
        "to": str(end.element_id),
        "caption": r.type,
    }


def _graph_to_nvl(nodes: list[Any], rels: list[Any]) -> dict[str, Any]:
    out_nodes: list[dict[str, Any]] = []
    out_rels: list[dict[str, Any]] = []
    seen_n: set[str] = set()
    seen_r: set[str] = set()
    for n in nodes:
        if not isinstance(n, Neo4jNode):
            continue
        sid = str(n.element_id)
        if sid not in seen_n:
            seen_n.add(sid)
            out_nodes.append(_node_to_nvl(n))
    for r in rels:
        if not isinstance(r, Neo4jRelationship):
            continue
        sid = str(r.element_id)
        if sid not in seen_r:
            seen_r.add(sid)
            out_rels.append(_rel_to_nvl(r))
    return {"nodes": out_nodes, "rels": out_rels}


class Neo4jGraphReportCollector(GraphReportCollector):
    def __init__(self, database: str = "neo4j", driver: Any = None):
        self.database = database
        self._driver = driver
        self._owns_driver = driver is None

    def _get_driver(self):
        if self._driver is None:
            self._driver = graph_session()
        return self._driver

    def close(self) -> None:
        if self._owns_driver and self._driver is not None:
            self._driver.close()
            self._driver = None

    def collect_db_snapshot(
        self,
        *,
        document_uid: str | None,
        sample_node_limit: int,
    ) -> dict:
        driver = self._get_driver()
        lim = max(10, min(int(sample_node_limit), 5000))
        out: dict[str, Any] = {
            "label_counts": {},
            "rel_type_counts": {},
            "entity_type_counts": {},
            "related_to_relation_type_counts": {},
            "node_schema_rows": [],
            "rel_schema_rows": [],
            "indexes": [],
            "constraints": [],
            "schema_visualization": {"nodes": [], "relationships": []},
            "instance_sample": {"nodes": [], "relationships": []},
            "reference_model_ascii": REFERENCE_MODEL_ASCII,
        }
        try:
            with driver.session(database=self.database) as session:
                rows = session.run(
                    """
                    MATCH (n)
                    UNWIND labels(n) AS lab
                    RETURN lab AS label, count(*) AS c
                    ORDER BY label
                    """
                )
                for r in rows:
                    out["label_counts"][r["label"]] = int(r["c"])

                rows = session.run(
                    """
                    MATCH ()-[r]->()
                    RETURN type(r) AS t, count(r) AS c
                    ORDER BY c DESC
                    """
                )
                for r in rows:
                    out["rel_type_counts"][r["t"]] = int(r["c"])

                rows = session.run(
                    """
                    MATCH (e:Entity)
                    RETURN coalesce(toString(e.type), 'unknown') AS t, count(*) AS c
                    ORDER BY c DESC
                    """
                )
                for r in rows:
                    out["entity_type_counts"][r["t"]] = int(r["c"])

                rows = session.run(
                    """
                    MATCH ()-[r:RELATED_TO]->()
                    RETURN coalesce(toString(r.relation_type), 'unknown') AS t, count(r) AS c
                    ORDER BY c DESC
                    """
                )
                for r in rows:
                    out["related_to_relation_type_counts"][r["t"]] = int(r["c"])

                try:
                    rows = session.run(
                        """
                        CALL db.schema.nodeTypeProperties()
                        YIELD nodeType, nodeLabels, propertyName, propertyTypes, mandatory
                        RETURN nodeType, nodeLabels, propertyName, propertyTypes, mandatory
                        """
                    )
                    out["node_schema_rows"] = [
                        {k: _json_safe(v) for k, v in rec.data().items()} for rec in rows
                    ]
                except Exception as ex:
                    logger.debug("nodeTypeProperties unavailable: %s", ex)

                try:
                    rows = session.run(
                        """
                        CALL db.schema.relTypeProperties()
                        YIELD relationshipType, propertyName, propertyTypes, mandatory
                        RETURN relationshipType, propertyName, propertyTypes, mandatory
                        """
                    )
                    out["rel_schema_rows"] = [
                        {k: _json_safe(v) for k, v in rec.data().items()} for rec in rows
                    ]
                except Exception as ex:
                    logger.debug("relTypeProperties unavailable: %s", ex)

                try:
                    rows = session.run("SHOW INDEXES YIELD * RETURN *")
                    out["indexes"] = [
                        {k: _json_safe(v) for k, v in rec.data().items()} for rec in rows
                    ]
                except Exception as ex:
                    logger.debug("SHOW INDEXES: %s", ex)

                try:
                    rows = session.run("SHOW CONSTRAINTS YIELD * RETURN *")
                    out["constraints"] = [
                        {k: _json_safe(v) for k, v in rec.data().items()} for rec in rows
                    ]
                except Exception as ex:
                    logger.debug("SHOW CONSTRAINTS: %s", ex)

                try:
                    rec = session.run(
                        "CALL db.schema.visualization() YIELD nodes, relationships RETURN nodes, relationships"
                    ).single()
                    if rec:
                        n_list = list(rec["nodes"] or [])
                        r_list = list(rec["relationships"] or [])
                        out["schema_visualization"] = _graph_to_nvl(n_list, r_list)
                except Exception as ex:
                    logger.debug("db.schema.visualization: %s", ex)

                nodes_out: list[Neo4jNode] = []
                rels_out: list[Neo4jRelationship] = []
                if document_uid:
                    q = """
                    MATCH (c:Chunk {source_document_uid: $uid})
                    WITH c ORDER BY coalesce(c.chunk_id_consecutive, 0) ASC LIMIT $lim
                    WITH collect(c) AS cs
                    UNWIND cs AS c
                    OPTIONAL MATCH (c)-[r]-(m)
                    WITH collect(DISTINCT c) AS dc, collect(m) AS dm, collect(r) AS dr
                    RETURN dc + [x IN dm WHERE x IS NOT NULL] AS nodes,
                           [y IN dr WHERE y IS NOT NULL] AS rels
                    """
                    rec = session.run(q, uid=document_uid, lim=lim).single()
                    if rec:
                        raw_nodes = [x for x in (rec["nodes"] or []) if x is not None]
                        raw_rels = [x for x in (rec["rels"] or []) if x is not None]
                        nodes_out = [n for n in raw_nodes if isinstance(n, Neo4jNode)]
                        rels_out = [x for x in raw_rels if isinstance(x, Neo4jRelationship)]
                if not nodes_out:
                    q = """
                    MATCH (n)
                    WITH n LIMIT $lim
                    WITH collect(n) AS ns
                    UNWIND ns AS n
                    OPTIONAL MATCH (n)-[r]-(m)
                    WITH collect(DISTINCT n) AS dn, collect(m) AS dm, collect(r) AS dr
                    RETURN dn + [x IN dm WHERE x IS NOT NULL] AS nodes,
                           [y IN dr WHERE y IS NOT NULL] AS rels
                    """
                    rec = session.run(q, lim=lim).single()
                    if rec:
                        raw_nodes = list(rec["nodes"] or [])
                        raw_rels = list(rec["rels"] or [])
                        nodes_out = [n for n in raw_nodes if isinstance(n, Neo4jNode)]
                        rels_out = [x for x in raw_rels if isinstance(x, Neo4jRelationship)]

                out["instance_sample"] = _graph_to_nvl(nodes_out, rels_out)
        except Exception:
            logger.exception("Neo4jGraphReportCollector failed")
            raise
        return out


def neo4j_uri_host(uri: str) -> str:
    try:
        p = urlparse(uri)
        if p.netloc:
            return p.netloc
        return uri
    except Exception:
        return ""
