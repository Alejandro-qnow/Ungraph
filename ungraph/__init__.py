"""
Ungraph - Python package for Knowledge Graph construction.

API pública de la librería para convertir datos no estructurados en grafos de conocimiento.

Ejemplo de uso básico:
    >>> import ungraph
    >>> 
    >>> # Ingerir un documento al grafo
    >>> chunks = ungraph.ingest_document("documento.md")
    >>> print(f"Documento dividido en {len(chunks)} chunks")
    >>>
    >>> # Buscar en el grafo
    >>> results = ungraph.search("consulta de ejemplo")
    >>> for result in results:
    >>>     print(f"Score: {result.score}, Contenido: {result.content[:100]}...")

Para uso avanzado, puedes acceder a los componentes internos:
    >>> from ungraph import IngestDocumentUseCase
    >>> from ungraph.application.dependencies import create_ingest_document_use_case
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from ungraph.application.use_cases.ingest_document import IngestDocumentUseCase
    from ungraph.domain.entities.chunk import Chunk
    from ungraph.domain.services.search_service import SearchResult
    from ungraph.domain.value_objects.graph_pattern import GraphPattern
    from ungraph.domain.value_objects.web_document import ExtractionRecipe, WebDocument

try:
    from .core.configuration import get_settings, configure, reset_configuration
except ImportError:
    from ungraph.core.configuration import get_settings, configure, reset_configuration

__version__ = "0.1.5"
__all__ = [
    # Configuration functions
    "configure",
    "reset_configuration",
    
    # Funciones de alto nivel
    "ingest_document",
    "search",
    "vector_search",
    "hybrid_search",
    "search_with_pattern",
    "suggest_chunking_strategy",
    "ingest_tabular",
    "mine_knowledge",
    "infer_over_document",
    "graph_stats",
    "validate_topology",

    # Clases para uso avanzado
    "IngestDocumentUseCase",
    "Chunk",
    "SearchResult",
    "ChunkingRecommendation",
    "GraphPattern",
    "ExtractionRecipe",
    "WebDocument",
]


@dataclass
class ChunkingRecommendation:
    """Recomendación de estrategia de chunking con explicación."""
    strategy: str
    chunk_size: int
    chunk_overlap: int
    explanation: str
    quality_score: float
    alternatives: List[Dict[str, Any]]
    metrics: Dict[str, Any]


def ingest_document(
    file_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    clean_text: bool = True,
    database: Optional[str] = None,
    embedding_model: Optional[str] = None,
    pattern: Optional["GraphPattern"] = None,
    extraction_recipe: Optional[Any] = None,
    source_url: Optional[str] = None,
    retrieval_optimization: bool = False,
) -> List[Chunk]:
    """
    Ingest a document into the knowledge graph.
    
    This is the main high-level function for using the library.
    Loads the document, splits it into chunks, generates embeddings and persists it in Neo4j.
    
    Uses global configuration if parameters are not specified. Configuration can be
    set using environment variables or programmatically with configure().
    
    Args:
        file_path: Path to the file to ingest (Markdown, TXT, Word, PDF)
        chunk_size: Size of each chunk in characters (default: 1000)
        chunk_overlap: Overlap between chunks in characters (default: 200)
        clean_text: If True, cleans the text before processing (default: True)
        database: Neo4j database name (default: from global configuration)
        embedding_model: Embedding model to use (default: from global configuration)
        pattern: Optional graph pattern. If None, uses FILE_PAGE_CHUNK (default: None)
        extraction_recipe: For ``.html`` / ``.htm``, optional
            :class:`~ungraph.domain.value_objects.web_document.ExtractionRecipe` (XPath/CSS, excludes).
        source_url: When ingesting HTML saved from a crawl, the public URL of the page
            (provenance for chunks; ``source_id`` in metadata).
        retrieval_optimization: If True, fills derived retrieval text on each chunk and,
            when using the default Neo4j repository, persists ``(:RetrievalChunk)``
            linked with ``HAS_RETRIEVAL_VIEW`` from ``(:Chunk)``. Full text remains on
            ``Chunk.page_content``.
    
    Returns:
        List of created Chunks
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file can't be processed
        RuntimeError: If there's an error connecting to Neo4j
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Configure (optional, can also use environment variables)
        >>> ungraph.configure(
        ...     neo4j_uri="bolt://localhost:7687",
        ...     neo4j_password="password"
        ... )
        >>> 
        >>> # Ingest a document (uses FILE_PAGE_CHUNK by default)
        >>> chunks = ungraph.ingest_document("my_document.md")
        >>> print(f"✅ {len(chunks)} chunks created")
        >>>
        >>> # With custom parameters
        >>> chunks = ungraph.ingest_document(
        ...     "document.txt",
        ...     chunk_size=500,
        ...     chunk_overlap=100
        ... )
        >>>
        >>> # With custom pattern
        >>> from ungraph.domain.value_objects.graph_pattern import GraphPattern, NodeDefinition
        >>> simple_pattern = GraphPattern(
        ...     name="SIMPLE_CHUNK",
        ...     description="Chunks only",
        ...     node_definitions=[
        ...         NodeDefinition(
        ...             label="Chunk",
        ...             required_properties={"chunk_id": str, "content": str}
        ...         )
        ...     ],
        ...     relationship_definitions=[]
        ... )
        >>> chunks = ungraph.ingest_document("doc.md", pattern=simple_pattern)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    # Get global configuration
    settings = get_settings()
    
    # Use provided parameters or global configuration
    db_name = database or settings.neo4j_database
    emb_model = embedding_model or settings.embedding_model
    
    # Crear caso de uso usando el Composition Root
    # Import here to avoid circular import with application.dependencies
    from ungraph.application.dependencies import create_ingest_document_use_case
    
    use_case = create_ingest_document_use_case(
        settings=settings,
        database=db_name,
        embedding_model=emb_model,
    )
    
    loader_kw: Dict[str, Any] = {}
    if extraction_recipe is not None:
        loader_kw["extraction_recipe"] = extraction_recipe
    try:
        # Ejecutar el caso de uso
        chunks = use_case.execute(
            file_path=file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            clean_text=clean_text,
            pattern=pattern,
            source_url=source_url,
            retrieval_optimization=retrieval_optimization,
            **loader_kw,
        )
        return chunks
    finally:
        # Limpiar recursos
        if hasattr(use_case.chunk_repository, 'close'):
            use_case.chunk_repository.close()
        if hasattr(use_case.index_service, 'close'):
            use_case.index_service.close()


def search(
    query_text: str,
    limit: int = 5,
    database: Optional[str] = None
) -> List[SearchResult]:
    """
    Search the knowledge graph using text search.
    
    Args:
        query_text: Text to search for
        limit: Maximum number of results (default: 5)
        database: Neo4j database name (default: from global configuration)
    
    Returns:
        List of SearchResults sorted by score in descending order
    
    Raises:
        ValueError: If query_text is empty
        RuntimeError: If there's an error connecting to Neo4j
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Search the graph
        >>> results = ungraph.search("quantum computing")
        >>> for result in results:
        ...     print(f"Score: {result.score:.3f}")
        ...     print(f"Content: {result.content[:200]}...")
        ...     print("---")
    """
    from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

    if not query_text:
        raise ValueError("Query text cannot be empty")
    
    # Obtener configuración global
    settings = get_settings()
    db_name = database or settings.neo4j_database
    
    search_service = Neo4jSearchService(database=db_name)
    
    try:
        results = search_service.text_search(query_text, limit=limit)
        return results
    finally:
        search_service.close()


def vector_search(
    query_text: str,
    limit: int = 5,
    database: Optional[str] = None,
    embedding_model: Optional[str] = None
) -> List[SearchResult]:
    """
    Vector search using semantic similarity.
    
    This function performs semantic search using vector embeddings.
    It generates an embedding for the query text and searches for
    similar chunks in the knowledge graph.
    
    Args:
        query_text: Text to search for
        limit: Maximum number of results (default: 5)
        database: Neo4j database name (default: from global configuration)
        embedding_model: Embedding model to use (default: from global configuration)
    
    Returns:
        List of SearchResults sorted by similarity score in descending order
    
    Raises:
        ValueError: If query_text is empty
        RuntimeError: If there's an error connecting to Neo4j
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Vector search
        >>> results = ungraph.vector_search("machine learning", limit=5)
        >>> for result in results:
        ...     print(f"Score: {result.score:.3f}")
        ...     print(f"Content: {result.content[:200]}...")
    """
    from ungraph.infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
    from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

    if not query_text:
        raise ValueError("Query text cannot be empty")
    
    # Obtener configuración global
    settings = get_settings()
    db_name = database or settings.neo4j_database
    emb_model = embedding_model or settings.embedding_model
    
    # Generar embedding para la consulta
    embedding_service = HuggingFaceEmbeddingService(model_name=emb_model)
    query_embedding = embedding_service.generate_embedding(query_text)
    
    # Perform vector search
    search_service = Neo4jSearchService(database=db_name)
    
    try:
        results = search_service.vector_search(query_embedding, limit=limit)
        return results
    finally:
        search_service.close()


def hybrid_search(
    query_text: str,
    limit: int = 5,
    weights: Tuple[float, float] = (0.3, 0.7),
    database: Optional[str] = None,
    embedding_model: Optional[str] = None
) -> List[SearchResult]:
    """
    Hybrid search combining text and vector similarity.
    
    This function combines full-text search and vector search
    to get better results.
    
    Args:
        query_text: Text to search for
        limit: Maximum number of results (default: 5)
        weights: Weights to combine scores (text_weight, vector_weight) (default: (0.3, 0.7))
        database: Neo4j database name (default: from global configuration)
        embedding_model: Embedding model to use (default: from global configuration)
    
    Returns:
        List of SearchResults sorted by combined score in descending order
    
    Raises:
        ValueError: If query_text is empty
        RuntimeError: If there's an error connecting to Neo4j
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Hybrid search
        >>> results = ungraph.hybrid_search(
        ...     "artificial intelligence",
        ...     limit=10,
        ...     weights=(0.4, 0.6)  # More weight to vector search
        ... )
        >>> for result in results:
        ...     print(f"Score: {result.score:.3f}")
        ...     print(f"Content: {result.content[:200]}...")
    """
    from ungraph.infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
    from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

    if not query_text:
        raise ValueError("Query text cannot be empty")
    
    # Obtener configuración global
    settings = get_settings()
    db_name = database or settings.neo4j_database
    emb_model = embedding_model or settings.embedding_model
    
    # Generar embedding para la consulta
    embedding_service = HuggingFaceEmbeddingService(model_name=emb_model)
    query_embedding = embedding_service.generate_embedding(query_text)
    
    # Perform hybrid search
    search_service = Neo4jSearchService(database=db_name)
    
    try:
        results = search_service.hybrid_search(
            query_text=query_text,
            query_embedding=query_embedding,
            weights=weights,
            limit=limit
        )
        return results
    finally:
        search_service.close()


def search_with_pattern(
    query_text: str,
    pattern_type: str,
    limit: int = 5,
    database: Optional[str] = None,
    embedding_model: Optional[str] = None,
    **kwargs
) -> List[SearchResult]:
    """
    Search using a specific GraphRAG pattern.
    
    Supports basic and advanced GraphRAG-based search patterns:
    
    **Basic patterns** (always available):
    - `basic` or `basic_retriever`: Simple full-text search
    - `metadata_filtering`: Search with metadata filters
    - `parent_child` or `parent_child_retriever`: Search in parent nodes and expand to children
    
    **Advanced patterns** (require optional modules):
    - `local` or `local_retriever`: Search in small communities (requires ungraph[gds])
    - `graph_enhanced` or `graph_enhanced_vector`: Vector search enhanced with traversal (requires ungraph[gds])
    - `community_summary` or `community_summary_gds`: Community summaries (requires ungraph[gds])
    
    Args:
        query_text: Text to search for
        pattern_type: Pattern type
        limit: Maximum number of results (default: 5)
        database: Neo4j database name (default: from global configuration)
        embedding_model: Embedding model for patterns that require it (default: from configuration)
        **kwargs: Pattern-specific parameters
    
    Returns:
        List of SearchResults sorted by score in descending order
    
    Raises:
        ValueError: If query_text is empty or pattern_type is invalid
        RuntimeError: If there's an error connecting to Neo4j
        ImportError: If a required optional module is not installed
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Basic search
        >>> results = ungraph.search_with_pattern(
        ...     "machine learning",
        ...     pattern_type="basic",
        ...     limit=5
        ... )
        >>> 
        >>> # Search with metadata filters
        >>> results = ungraph.search_with_pattern(
        ...     "machine learning",
        ...     pattern_type="metadata_filtering",
        ...     metadata_filters={"filename": "ai_paper.md", "page_number": 1},
        ...     limit=10
        ... )
        >>> 
        >>> # Parent-child search
        >>> results = ungraph.search_with_pattern(
        ...     "artificial intelligence",
        ...     pattern_type="parent_child_retriever",
        ...     parent_label="Page",
        ...     child_label="Chunk",
        ...     limit=5
        ... )
        >>> 
        >>> # Advanced search: Graph-Enhanced (requires ungraph[gds])
        >>> results = ungraph.search_with_pattern(
        ...     "machine learning",
        ...     pattern_type="graph_enhanced",
        ...     limit=5,
        ...     max_traversal_depth=2
        ... )
        >>> 
        >>> # Advanced search: Local Retriever (requires ungraph[gds])
        >>> results = ungraph.search_with_pattern(
        ...     "neural networks",
        ...     pattern_type="local",
        ...     limit=5,
        ...     community_threshold=3,
        ...     max_depth=1
        ... )
    """
    from ungraph.infrastructure.services.neo4j_search_service import Neo4jSearchService

    if not query_text:
        raise ValueError("Query text cannot be empty")
    
    # Obtener configuración global
    settings = get_settings()
    db_name = database or settings.neo4j_database
    
    search_service = Neo4jSearchService(database=db_name)
    
    try:
        results = search_service.search_with_pattern(
            query_text=query_text,
            pattern_type=pattern_type,
            limit=limit,
            **kwargs
        )
        return results
    finally:
        search_service.close()


def suggest_chunking_strategy(
    file_path: str | Path,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    evaluate_all: bool = False,
    embedding_model: Any = None,
) -> ChunkingRecommendation:
    """
    Suggest the best chunking strategy for a document with explanation.
    
    Analyzes the document and recommends the most appropriate chunking strategy
    based on its structure, type, and characteristics.
    
    Args:
        file_path: Path to the file to analyze
        chunk_size: Desired chunk size (optional, calculated automatically)
        chunk_overlap: Desired overlap (optional, calculated automatically)
        evaluate_all: If True, evaluates all candidate strategies (default: False)
    
    Returns:
        ChunkingRecommendation with recommended strategy, explanation and alternatives
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file can't be processed
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Get recommendation
        >>> recommendation = ungraph.suggest_chunking_strategy("document.md")
        >>> print(f"Recommended strategy: {recommendation.strategy}")
        >>> print(f"Explanation: {recommendation.explanation}")
        >>> print(f"Chunk size: {recommendation.chunk_size}")
        >>> print(f"Quality score: {recommendation.quality_score:.2f}")
        >>> 
        >>> # View evaluated alternatives
        >>> for alt in recommendation.alternatives:
        ...     print(f"  - {alt['strategy']}: score {alt['score']:.2f}")
        >>> 
        >>> # Use the recommendation
        >>> chunks = ungraph.ingest_document(
        ...     "document.md",
        ...     chunk_size=recommendation.chunk_size,
        ...     chunk_overlap=recommendation.chunk_overlap
        ... )
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")
    
    from langchain_core.documents import Document as LangChainDocument
    from ungraph.infrastructure.services.langchain_document_loader_service import (
        LangChainDocumentLoaderService,
    )
    from ungraph.infrastructure.services.simple_text_cleaning_service import (
        SimpleTextCleaningService,
    )
    from ungraph.utils.chunking_master import ChunkingMaster
    
    text_cleaning_service = SimpleTextCleaningService()
    loader_service = LangChainDocumentLoaderService(text_cleaning_service=text_cleaning_service)
    
    # Load document
    domain_documents = loader_service.load(file_path, clean=False)
    if not domain_documents:
        raise ValueError(f"Could not load document: {file_path}")
    
    # Convert to LangChain Document
    lc_document = LangChainDocument(
        page_content=domain_documents[0].content,
        metadata=domain_documents[0].metadata
    )
    
    # Create ChunkingMaster. Con embedding_model, SEMANTIC entra como candidata
    # (antes el suggester era ciego al chunking semántico).
    master = ChunkingMaster(embedding_model=embedding_model)
    
    # Find best strategy
    result = master.find_best_chunking_strategy(
        documents=[lc_document],
        file_path=file_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        evaluate_all=evaluate_all
    )
    
    # Generate explanation
    explanation = _generate_chunking_explanation(result, master)
    
    # Get alternatives (if multiple were evaluated). ChunkingMaster ahora expone
    # TODAS las estrategias evaluadas en result.evaluated_alternatives (ordenadas
    # por score). Fallback a la mejor si no hubo evaluación múltiple.
    alternatives = []
    if evaluate_all:
        alternatives = list(getattr(result, "evaluated_alternatives", []) or [])
        if not alternatives:
            alternatives.append({
                "strategy": result.strategy.value,
                "score": master.evaluator.score_strategy(result.metrics),
                "num_chunks": result.metrics.num_chunks,
                "avg_chunk_size": result.metrics.avg_chunk_size
            })
    
    return ChunkingRecommendation(
        strategy=result.strategy.value,
        chunk_size=result.config.get('chunk_size', 1000),
        chunk_overlap=result.config.get('chunk_overlap', 200),
        explanation=explanation,
        quality_score=master.evaluator.score_strategy(result.metrics),
        alternatives=alternatives,
        metrics={
            "num_chunks": result.metrics.num_chunks,
            "avg_chunk_size": result.metrics.avg_chunk_size,
            "min_chunk_size": result.metrics.min_chunk_size,
            "max_chunk_size": result.metrics.max_chunk_size,
            "sentence_completeness": result.metrics.avg_sentence_completeness,
            "paragraph_preservation": result.metrics.avg_paragraph_preservation
        }
    )


def _generate_chunking_explanation(result: Any, master: Any) -> str:
    """Generate a readable explanation of why this strategy was chosen."""
    strategy_name = result.strategy.value
    doc_type = result.config.get('doc_type', 'unknown')
    structure = result.config.get('structure', {})
    metrics = result.metrics
    
    explanation_parts = [
        f"The strategy '{strategy_name}' is recommended because:"
    ]
    
    # Explanation based on document type
    if doc_type == 'markdown':
        explanation_parts.append("- The document is Markdown with header structure")
        if strategy_name == 'markdown_header':
            explanation_parts.append("- The strategy preserves header hierarchy")
    elif doc_type == 'python':
        explanation_parts.append("- The document contains Python code")
        if strategy_name == 'language_specific':
            explanation_parts.append("- The strategy respects language syntax")
    else:
        explanation_parts.append(f"- The document is of type '{doc_type}'")
    
    # Explanation based on metrics
    if metrics.avg_sentence_completeness > 0.9:
        explanation_parts.append("- High preservation of complete sentences (>90%)")
    if metrics.avg_paragraph_preservation > 0.8:
        explanation_parts.append("- Good paragraph preservation (>80%)")
    
    # Explanation based on structure
    if structure.get('headers', 0) > 0:
        explanation_parts.append(f"- The document has {structure['headers']} headers")
    if structure.get('paragraphs', 0) > 0:
        explanation_parts.append(f"- The document has {structure['paragraphs']} paragraphs")
    
    explanation_parts.append(f"- Will generate approximately {metrics.num_chunks} chunks")
    explanation_parts.append(f"- Average chunk size: {metrics.avg_chunk_size:.0f} characters")
    explanation_parts.append(f"- Quality score: {master.evaluator.score_strategy(metrics):.2f}/1.0")
    
    return "\n".join(explanation_parts)


def ingest_tabular(
    file_path: str | Path,
    database: Optional[str] = None,
    *,
    apply: bool = False,
    mapping: Optional[List[Dict[str, Any]]] = None,
    use_llm: bool = True,
    batch_size: int = 1000,
) -> Dict[str, Any]:
    """Ingest a tabular source (CSV/XLSX) via Schema-Guided Ingestion (SGI).

    Runs alongside the text ETI pipeline: a table's structure is already explicit, so
    instead of chunking + NLP extraction, the column→role mapping is inferred and rows
    are materialized as nodes/relationships. Two-step flow:

    - ``apply=False`` (default, dry-run): infer and return the schema proposal WITHOUT
      writing to the graph. Review/edit it and call again.
    - ``apply=True``: persist to the graph. If ``mapping`` (confirmed/edited proposals as
      a list of ``TabularSchemaProposal``-shaped dicts) is given, it is used instead of
      re-inferring.

    LLM disambiguation (``use_llm``) is only used when ``OPENAI_API_KEY`` is available;
    otherwise inference is pure heuristic (deterministic).

    Returns:
        ``{'file_path', 'persisted': bool, 'proposals': [dict...], 'stats': [dict...]}``.
    """
    from ungraph.reasoning import ingest_tabular as _ingest_tabular

    return _ingest_tabular(
        str(file_path),
        database=database,
        apply=apply,
        mapping=mapping,
        use_llm=use_llm,
        batch_size=batch_size,
    )


def mine_knowledge(
    database: Optional[str] = None,
    *,
    inference_language: str = "en",
    use_tqdm: bool = False,
) -> Dict[str, Any]:
    """Re-inferencia sobre chunks sin facts (fase I post-ingest). Ver ``ungraph.reasoning``."""
    from ungraph.reasoning import mine_knowledge as _mine_knowledge

    return _mine_knowledge(
        database=database,
        inference_language=inference_language,
        use_tqdm=use_tqdm,
    )


def infer_over_document(
    document_path: str | Path,
    database: Optional[str] = None,
    *,
    inference_language: str = "en",
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> Dict[str, Any]:
    """Ingesta + inferencia sobre un documento; fachada serializable. Ver ``ungraph.reasoning``."""
    from ungraph.reasoning import infer_over_document as _infer_over_document

    return _infer_over_document(
        str(document_path),
        database=database,
        inference_language=inference_language,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def graph_stats(database: Optional[str] = None) -> Dict[str, Any]:
    """Estadísticas estructurales del grafo (R/O). Ver ``ungraph.reasoning``."""
    from ungraph.reasoning import graph_stats as _graph_stats

    return _graph_stats(database=database)


def validate_topology(
    database: Optional[str] = None,
    *,
    source_document_uid: Optional[str] = None,
    min_chunks: int = 1,
) -> Dict[str, Any]:
    """Valida topología File–Page–Chunk. Ver ``ungraph.reasoning``."""
    from ungraph.reasoning import validate_topology as _validate_topology

    return _validate_topology(
        database=database,
        source_document_uid=source_document_uid,
        min_chunks=min_chunks,
    )


_EXPORT_LAZY = {
    "IngestDocumentUseCase": (
        "ungraph.application.use_cases.ingest_document",
        "IngestDocumentUseCase",
    ),
    "Chunk": ("ungraph.domain.entities.chunk", "Chunk"),
    "SearchResult": ("ungraph.domain.services.search_service", "SearchResult"),
    "GraphPattern": ("ungraph.domain.value_objects.graph_pattern", "GraphPattern"),
    "ExtractionRecipe": (
        "ungraph.domain.value_objects.web_document",
        "ExtractionRecipe",
    ),
    "WebDocument": ("ungraph.domain.value_objects.web_document", "WebDocument"),
}


def __getattr__(name: str) -> Any:
    """Load public types on first access (keeps `import ungraph` light)."""
    if name in _EXPORT_LAZY:
        mod_name, attr_name = _EXPORT_LAZY[name]
        module = importlib.import_module(mod_name)
        obj = getattr(module, attr_name)
        globals()[name] = obj
        return obj
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(set(__all__) | {"__version__", "get_settings"})
