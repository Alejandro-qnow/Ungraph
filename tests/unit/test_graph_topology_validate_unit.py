"""Unit tests for topology report helpers (no Neo4j)."""

from __future__ import annotations

import pytest

from ungraph.utils.graph_topology_validate import TopologyReport


@pytest.mark.unit
def test_topology_report_add():
    r = TopologyReport(ok=True)
    r.add(True, "should not appear")
    assert r.ok
    assert r.issues == []
    r.add(False, "bad")
    assert not r.ok
    assert "bad" in r.issues
