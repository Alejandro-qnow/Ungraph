"""Cliente SPARQL: parseo de respuesta JSON."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ungraph.infrastructure.services.sparql_client import (
    binding_text,
    sparql_select_bindings,
)

pytestmark = pytest.mark.unit


def test_binding_text_reads_literal() -> None:
    b = {"label": {"type": "literal", "value": "Person"}}
    assert binding_text(b, "label") == "Person"


@patch("urllib.request.urlopen")
def test_sparql_select_bindings_parses_json(mock_urlopen: MagicMock) -> None:
    payload = {
        "head": {"vars": ["label", "uri"]},
        "results": {
            "bindings": [
                {
                    "label": {"type": "literal", "value": "A"},
                    "uri": {"type": "uri", "value": "http://ex/A"},
                }
            ]
        },
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(payload).encode()
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_resp
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    rows = sparql_select_bindings(
        "http://sparql.example/query", "SELECT ...", timeout_seconds=5.0
    )
    assert len(rows) == 1
    assert binding_text(rows[0], "label") == "A"
