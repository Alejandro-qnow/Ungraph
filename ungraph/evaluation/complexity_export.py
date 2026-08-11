"""Export mínimos de proyecciones ETI para Complexometrum Fase A (F5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union


def export_chunk_embeddings(
    chunks: Sequence[Any],
    dest_dir: Union[Path, str],
    *,
    dataset_id: Optional[str] = None,
    graph_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Escribe ``embeddings.npy`` + ``chunks_meta.json`` para ``from_embeddings``.

    Cada chunk debe exponer ``embeddings`` (lista/array) y opcionalmente
    ``page_content``, ``metadata``, ``chunk_id_consecutive``.
    """
    import numpy as np

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    vectors: List[List[float]] = []
    meta_rows: List[Dict[str, Any]] = []
    for i, ch in enumerate(chunks):
        emb = getattr(ch, "embeddings", None)
        if emb is None and isinstance(getattr(ch, "metadata", None), dict):
            emb = ch.metadata.get("embeddings")
        if emb is None:
            continue
        vec = [float(x) for x in list(emb)]
        if not vec:
            continue
        vectors.append(vec)
        md = dict(getattr(ch, "metadata", None) or {})
        meta_rows.append(
            {
                "i": i,
                "chunk_id": getattr(ch, "id", None) or md.get("chunk_id"),
                "chunk_id_consecutive": getattr(ch, "chunk_id_consecutive", None),
                "n_chars": len(str(getattr(ch, "page_content", "") or "")),
                "dataset_id": md.get("dataset_id") or dataset_id,
                "graph_id": md.get("graph_id") or graph_id,
                "source_document_uid": md.get("source_document_uid")
                or getattr(ch, "source_document_uid", None),
            }
        )
    if not vectors:
        raise ValueError("no chunk embeddings to export")
    X = np.asarray(vectors, dtype=float)
    npy_path = dest / "embeddings.npy"
    meta_path = dest / "chunks_meta.json"
    np.save(npy_path, X)
    payload = {
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "dataset_id": dataset_id,
        "graph_id": graph_id,
        "chunks": meta_rows,
        "note": "Projection for Complexometrum.from_embeddings — not raw PDF complexity.",
        "complexometrum_hint": (
            "from complexometrum.adapters import from_embeddings; "
            "import numpy as np; X=np.load('embeddings.npy'); from_embeddings(X)"
        ),
    }
    meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "embeddings_path": str(npy_path),
        "meta_path": str(meta_path),
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
    }
