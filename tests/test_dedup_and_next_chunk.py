"""Unit tests for dedup VO and NEXT_CHUNK scoping helpers."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from ungraph.domain.value_objects.deduplication import normalize_doi
from ungraph.utils import graph_operations as go


class TestNormalizeDoi(unittest.TestCase):
    def test_strip_prefix_and_lower(self):
        self.assertEqual(
            normalize_doi("https://doi.org/10.1000/Xyz"),
            "10.1000/xyz",
        )
        self.assertEqual(normalize_doi("doi:10.1234/paper"), "10.1234/paper")


class TestScopedNextChunk(unittest.TestCase):
    def test_tx_requires_scope(self):
        tx = MagicMock()
        with self.assertRaises(ValueError):
            go.create_chunk_relationships_tx(tx)

    def test_tx_uses_uid_in_query(self):
        tx = MagicMock()
        go.create_chunk_relationships_tx(tx, source_document_uid="doc-a")
        self.assertTrue(tx.run.called)
        arg0 = tx.run.call_args[0][0]
        self.assertIn("source_document_uid", arg0)


if __name__ == "__main__":
    unittest.main()
