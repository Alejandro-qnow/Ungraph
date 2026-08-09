"""Catalog persistence interface (BibliographicArticle in Neo4j)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class BibliographicArticleRecord:
    """Snapshot fields stored on :BibliographicArticle."""

    document_uid: str
    doi_norm: Optional[str] = None
    external_id: Optional[str] = None
    title: Optional[str] = None
    abstract_text: Optional[str] = None
    abstract_embedding: Optional[List[float]] = None
    embedding_model: Optional[str] = None
    canonical_filename: Optional[str] = None
    source_sha256: Optional[str] = None
    source_size_bytes: Optional[int] = None
    embedded_file_metadata_snapshot: Optional[str] = None
    ingested_at: Optional[int] = None


class CatalogRepository(ABC):
    """Read/write bibliography catalog for dedup and bookkeeping."""

    @abstractmethod
    def exists_with_sha256(self, source_sha256: str) -> bool:
        ...

    @abstractmethod
    def exists_with_doi_norm(self, doi_norm: str) -> bool:
        ...

    @abstractmethod
    def exists_with_external_id(self, external_id: str) -> bool:
        ...

    @abstractmethod
    def list_abstract_embedding_rows(self, limit: int = 256) -> List[Tuple[str, List[float]]]:
        """Pairs (document_uid, abstract_embedding) for semantic similarity scans."""

        ...

    @abstractmethod
    def merge_article(self, row: BibliographicArticleRecord) -> None:
        """UPSERT bibliographic catalog node keyed by ``document_uid``."""

        ...

    @abstractmethod
    def try_claim_ingest(self, claim_key: str, holder_id: str) -> bool:
        """
        Lightweight logical lock on ``claim_key`` (often doi_norm).
        Returns True if this holder owns the lock (fresh or reclaim same holder).
        """

        ...
