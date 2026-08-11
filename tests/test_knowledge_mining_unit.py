"""Pruebas unitarias: minado de conocimiento sin Neo4j."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ungraph.application.use_cases.knowledge_mining import KnowledgeMiningUseCase
from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.entities.fact import Fact

pytestmark = pytest.mark.unit


def _chunk(cid: str, text: str) -> Chunk:
    return Chunk(
        id=cid,
        page_content=text,
        metadata={"filename": "unit.md", "page_number": 1},
    )


def test_knowledge_mining_persists_facts_and_indexes() -> None:
    repo = MagicMock()
    repo.list_chunk_ids_without_derived_facts.return_value = ["c1"]
    repo.find_by_id.return_value = _chunk("c1", "alpha beta")

    fact = Fact(
        id="f1",
        subject="c1",
        predicate="MENTIONS",
        object="alpha",
        confidence=0.9,
        provenance_ref="c1",
    )
    inference = MagicMock()
    inference.extract_entities.return_value = []
    inference.extract_relations.return_value = []
    inference.infer_facts.return_value = [fact]

    index = MagicMock()
    uc = KnowledgeMiningUseCase(repo, inference, index_service=index)
    res = uc.execute(use_tqdm=False)

    assert res.chunks_pending == 1
    assert res.chunks_inferred == 1
    assert res.facts_persisted == 1
    assert res.relations_persisted == 0
    assert res.errors == 0
    repo.save_facts.assert_called_once_with([fact])
    repo.save_relations.assert_not_called()
    index.setup_all_indexes.assert_called_once()
    uc.close()
    repo.close.assert_called_once()
    index.close.assert_called_once()


def test_knowledge_mining_force_remines_all_and_clears_prior() -> None:
    """force=True: usa list_all_chunk_ids y limpia derivaciones previas por chunk."""
    repo = MagicMock()
    # Sin force procesaría 0; con force debe re-minar TODOS.
    repo.list_chunk_ids_without_derived_facts.return_value = []
    repo.list_all_chunk_ids.return_value = ["c1", "c2"]
    repo.find_by_id.side_effect = [
        _chunk("c1", "graphrag retrieves from a knowledge graph"),
        _chunk("c2", "llm builds a graph index"),
    ]
    fact = Fact(
        id="f1",
        subject="c1",
        predicate="MENTIONS",
        object="GraphRAG",
        confidence=0.9,
        provenance_ref="c1",
    )
    inference = MagicMock()
    inference.extract_entities.return_value = []
    inference.extract_relations.return_value = []
    inference.infer_facts.return_value = [fact]

    uc = KnowledgeMiningUseCase(repo, inference, index_service=None)
    res = uc.execute(use_tqdm=False, force=True)

    assert res.chunks_pending == 2
    assert res.chunks_inferred == 2
    repo.list_all_chunk_ids.assert_called_once()
    repo.list_chunk_ids_without_derived_facts.assert_not_called()
    # Limpia las derivaciones previas de cada chunk antes de re-guardar.
    assert repo.delete_derived_facts_for_chunk.call_count == 2


def test_knowledge_mining_skips_empty_text_chunks() -> None:
    repo = MagicMock()
    repo.list_chunk_ids_without_derived_facts.return_value = ["c1", "c2"]
    repo.find_by_id.side_effect = [
        _chunk("c1", "ok"),
        _chunk("c2", "   "),
    ]
    inference = MagicMock()
    inference.extract_entities.return_value = []
    inference.extract_relations.return_value = []
    inference.infer_facts.return_value = []

    uc = KnowledgeMiningUseCase(repo, inference, index_service=None)
    res = uc.execute(use_tqdm=False)

    assert res.chunks_inferred == 1
    inference.extract_entities.assert_called_once()
    inference.extract_relations.assert_called_once()
    inference.infer_facts.assert_called_once()


def test_create_knowledge_mining_raises_when_inference_unavailable(mocker) -> None:
    from ungraph.application.dependencies import create_knowledge_mining_use_case
    from ungraph.core.configuration import reset_configuration

    reset_configuration()
    mocker.patch(
        "ungraph.application.dependencies.create_inference_service",
        return_value=None,
    )
    with pytest.raises(RuntimeError, match="Inference service"):
        create_knowledge_mining_use_case()
