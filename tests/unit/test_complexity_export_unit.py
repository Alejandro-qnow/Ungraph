"""Unit: export embeddings → Complexometrum Fase A."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ungraph.domain.entities.chunk import Chunk
from ungraph.evaluation.complexity_export import export_chunk_embeddings


def test_export_chunk_embeddings(tmp_path: Path) -> None:
    chunks = [
        Chunk(
            id=f"c{i}",
            page_content=f"text {i}",
            metadata={"dataset_id": "ds-kg-survey", "graph_id": "kg-survey-seed"},
            embeddings=[float(i), float(i + 1), 0.5],
            chunk_id_consecutive=i,
        )
        for i in range(5)
    ]
    out = export_chunk_embeddings(chunks, tmp_path, dataset_id="ds-kg-survey")
    X = np.load(out["embeddings_path"])
    assert X.shape == (5, 3)
    assert Path(out["meta_path"]).is_file()
