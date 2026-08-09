"""Neo4j-backed catalog (:BibliographicArticle)."""

from __future__ import annotations

import logging
from typing import List, Tuple

from neo4j.exceptions import ClientError

from ungraph.domain.repositories.catalog_repository import (
    BibliographicArticleRecord,
    CatalogRepository,
)
from ungraph.utils.graph_operations import graph_session

logger = logging.getLogger(__name__)


class Neo4jCatalogRepository(CatalogRepository):
    """Persist catalog rows for duplicate detection and bookkeeping."""

    def __init__(self, database: str = "neo4j") -> None:
        self.database = database
        self._driver = None

    def _get_driver(self):
        if self._driver is None:
            self._driver = graph_session()
        return self._driver

    def exists_with_sha256(self, source_sha256: str) -> bool:
        q = """
        MATCH (a:BibliographicArticle {source_sha256: $sha})
        RETURN a LIMIT 1
        """
        return self._scalar(q, sha=source_sha256)

    def exists_with_doi_norm(self, doi_norm: str) -> bool:
        q = """
        MATCH (a:BibliographicArticle {doi_norm: $doi})
        RETURN a LIMIT 1
        """
        return self._scalar(q, doi=doi_norm)

    def exists_with_external_id(self, external_id: str) -> bool:
        q = """
        MATCH (a:BibliographicArticle {external_id: $eid})
        RETURN a LIMIT 1
        """
        return self._scalar(q, eid=external_id)

    def list_abstract_embedding_rows(self, limit: int = 256) -> List[Tuple[str, List[float]]]:
        q = """
        MATCH (a:BibliographicArticle)
        WHERE a.abstract_embedding IS NOT NULL
        RETURN a.document_uid AS uid, a.abstract_embedding AS emb
        ORDER BY a.ingested_at DESC
        LIMIT $lim
        """
        driver = self._get_driver()
        with driver.session(database=self.database) as session:
            rows = session.execute_read(lambda tx: list(tx.run(q, lim=limit)))
        out: List[Tuple[str, List[float]]] = []
        for r in rows:
            uid = r.get("uid")
            emb = r.get("emb") or []
            if uid and emb:
                out.append((str(uid), list(emb)))
        return out

    def merge_article(self, row: BibliographicArticleRecord) -> None:
        q = """
        MERGE (a:BibliographicArticle {document_uid: $document_uid})
        SET a.doi_norm = $doi_norm,
            a.external_id = $external_id,
            a.title = $title,
            a.abstract_text = $abstract_text,
            a.abstract_embedding = $abstract_embedding,
            a.embedding_model = $embedding_model,
            a.canonical_filename = $canonical_filename,
            a.source_sha256 = $source_sha256,
            a.source_size_bytes = $source_size_bytes,
            a.embedded_file_metadata_snapshot = $embedded_snapshot,
            a.ingested_at = coalesce($ingested_at, timestamp())
        """
        driver = self._get_driver()
        try:
            with driver.session(database=self.database) as session:
                session.execute_write(
                    lambda tx: tx.run(
                        q,
                        document_uid=row.document_uid,
                        doi_norm=row.doi_norm,
                        external_id=row.external_id,
                        title=row.title,
                        abstract_text=row.abstract_text,
                        abstract_embedding=row.abstract_embedding or None,
                        embedding_model=row.embedding_model,
                        canonical_filename=row.canonical_filename,
                        source_sha256=row.source_sha256,
                        source_size_bytes=row.source_size_bytes,
                        embedded_snapshot=row.embedded_file_metadata_snapshot,
                        ingested_at=row.ingested_at,
                    )
                )
        except ClientError as e:
            logger.error("merge_article failed: %s", e, exc_info=True)
            raise

    def try_claim_ingest(self, claim_key: str, holder_id: str) -> bool:
        """Acquire ingest claim; returns False if another holder owns ``claim_key``."""

        def work(tx):
            row = tx.run(
                """
                OPTIONAL MATCH (l:IngestClaim {claim_key: $ck})
                RETURN l AS node, l.holder AS holder
                LIMIT 1
                """,
                ck=claim_key,
            ).single()
            if row is None or row["node"] is None:
                tx.run(
                    """
                    CREATE (l:IngestClaim {claim_key: $ck, holder: $holder, updatedAt: timestamp()})
                    """,
                    ck=claim_key,
                    holder=holder_id,
                )
                return True
            holder = row.get("holder")
            if holder is None or holder == holder_id:
                tx.run(
                    """
                    MATCH (l:IngestClaim {claim_key: $ck})
                    SET l.holder = coalesce(l.holder, $holder),
                        l.updatedAt = timestamp()
                    """,
                    ck=claim_key,
                    holder=holder_id,
                )
                r2 = tx.run(
                    """
                    MATCH (l:IngestClaim {claim_key: $ck})
                    RETURN l.holder = $holder AS ok
                    """,
                    ck=claim_key,
                    holder=holder_id,
                ).single()
                return bool(r2 and r2.get("ok"))
            return False

        driver = self._get_driver()
        with driver.session(database=self.database) as session:
            return bool(session.execute_write(lambda tx: work(tx)))

    def _scalar(self, q: str, **params) -> bool:
        driver = self._get_driver()
        try:
            with driver.session(database=self.database) as session:
                recs = session.execute_read(lambda tx: list(tx.run(q, **params)))
            return bool(recs)
        except ClientError as e:
            logger.warning("Catalog query warning (label may be missing): %s", e)
            return False

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._driver = None
