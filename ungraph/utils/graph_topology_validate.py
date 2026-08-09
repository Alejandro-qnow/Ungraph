"""
Post-ingest topology checks for FILE_PAGE_CHUNK and related lexical graphs.

Validates invariants so patterns do not "step on" each other: scoped NEXT_CHUNK,
lexical layer (File/Page/Chunk) vs inferred layer (Entity/Fact) stays a convention
documented in docs/PLAN_MAESTRO.md — this module only asserts structural rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from neo4j import Driver


@dataclass
class TopologyReport:
    """Result of running topology validators."""

    ok: bool
    issues: List[str] = field(default_factory=list)

    def add(self, condition: bool, message: str) -> None:
        if not condition:
            self.ok = False
            self.issues.append(message)


def count_cross_uid_next_chunk(driver: Driver, database: str) -> int:
    """NEXT_CHUNK edges where both ends have source_document_uid and they differ."""
    q = """
    MATCH (c1:Chunk)-[:NEXT_CHUNK]->(c2:Chunk)
    WHERE c1.source_document_uid IS NOT NULL AND c2.source_document_uid IS NOT NULL
      AND c1.source_document_uid <> c2.source_document_uid
    RETURN count(*) AS n
    """
    with driver.session(database=database) as session:
        rows = session.execute_read(lambda tx: list(tx.run(q)))
    return int(rows[0]["n"]) if rows else 0


def validate_next_chunk_same_document_scope(
    driver: Driver,
    database: str,
) -> TopologyReport:
    """Fails if any NEXT_CHUNK connects chunks from different source_document_uid."""
    n = count_cross_uid_next_chunk(driver, database)
    r = TopologyReport(ok=True)
    r.add(n == 0, f"cross-document NEXT_CHUNK edges: {n}")
    return r


def validate_file_page_chunk_document(
    driver: Driver,
    database: str,
    *,
    source_document_uid: str,
    min_chunks: int = 1,
) -> TopologyReport:
    """
    Checks chunks for one logical document share the same uid and form a NEXT_CHUNK chain
    matching chunk_id_consecutive 1..N when all chunks have consecutive ids set.
    """
    r = TopologyReport(ok=True)
    q_count = """
    MATCH (c:Chunk {source_document_uid: $uid})
    RETURN count(c) AS n
    """
    q_chain = """
    MATCH (c:Chunk {source_document_uid: $uid})
    RETURN c.chunk_id_consecutive AS ord ORDER BY ord
    """
    with driver.session(database=database) as session:
        n = session.execute_read(
            lambda tx: tx.run(q_count, uid=source_document_uid).single()["n"]
        )
    r.add(int(n) >= min_chunks, f"expected at least {min_chunks} chunks with uid {source_document_uid!r}, got {n}")
    with driver.session(database=database) as session:
        ords = session.execute_read(
            lambda tx: [rec["ord"] for rec in tx.run(q_chain, uid=source_document_uid)]
        )
    ords = [x for x in ords if x is not None]
    if len(ords) >= 2:
        ords_sorted = sorted(int(x) for x in ords)
        expected = list(range(ords_sorted[0], ords_sorted[0] + len(ords_sorted)))
        seq_ok = ords_sorted == expected
        r.add(seq_ok, f"chunk_id_consecutive not contiguous {ords_sorted} for uid {source_document_uid!r}")
    return r


def run_file_page_chunk_checks(
    driver: Driver,
    database: str,
    *,
    source_document_uid: Optional[str] = None,
    min_chunks: int = 1,
) -> TopologyReport:
    """Run cross-uid guard plus optional per-document checks."""
    combined = TopologyReport(ok=True)
    r1 = validate_next_chunk_same_document_scope(driver, database)
    combined.issues.extend(r1.issues)
    combined.ok = combined.ok and r1.ok
    if source_document_uid:
        r2 = validate_file_page_chunk_document(
            driver, database, source_document_uid=source_document_uid, min_chunks=min_chunks
        )
        combined.issues.extend(r2.issues)
        combined.ok = combined.ok and r2.ok
    return combined
