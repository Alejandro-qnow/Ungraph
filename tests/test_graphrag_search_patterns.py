import re
from src.infrastructure.services.graphrag_search_patterns import GraphRAGSearchPatterns


def test_parent_child_query_structure():
    """Verifica que la query de parent_child usa WITH para agregar children antes del RETURN."""
    query, params = GraphRAGSearchPatterns.parent_child_retriever(
        "test",
        parent_label="Page",
        child_label="Chunk",
        relationship_type="HAS_CHUNK",
        limit=3
    )

    # Debe contener WITH que agrega children
    assert "WITH parent_node, parent_score, collect" in query

    # El RETURN no debe contener collect(DISTINCT ...) directamente
    assert "collect(DISTINCT" not in query.split("RETURN")[1]

    # Parámetros deben incluir query_text y limit
    assert params["query_text"] == "test"
    assert params["limit"] == 3
