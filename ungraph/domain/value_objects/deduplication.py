"""Helpers for duplicate detection prior to ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass


def normalize_doi(raw: str | None) -> str | None:
    """Return lowercase stripped DOI without https://doi.org/ prefix."""
    if not raw:
        return None
    s = str(raw).strip().lower()
    if not s:
        return None
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if s.startswith(prefix):
            s = s[len(prefix) :].strip()
    # strip trailing punctuation often copied from citations
    s = re.sub(r"[\s.]+$", "", s)
    return s or None


@dataclass(frozen=True)
class DuplicateCheckResult:
    """Outcome of DuplicateGuard.evaluate."""

    should_skip_ingest: bool
    reason: str
    source_sha256: str | None = None
