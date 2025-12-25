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

# API pública de alto nivel
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import os

# Importar configuración global
try:
    from .core.configuration import get_settings, configure, reset_configuration
except ImportError:
    from src.core.configuration import get_settings, configure, reset_configuration

# Importar componentes internos para uso avanzado
# Usar imports relativos desde src/ para que funcionen cuando se instale el paquete
try:
    # Cuando se instala como paquete, los imports deben ser relativos a src/
    from .application.dependencies import create_ingest_document_use_case
    from .application.use_cases.ingest_document import IngestDocumentUseCase
    from .domain.entities.chunk import Chunk
    from .domain.services.search_service import SearchResult
    from .domain.value_objects.graph_pattern import GraphPattern
    from .infrastructure.services.neo4j_search_service import Neo4jSearchService
    from .infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
except ImportError:
    # Fallback para desarrollo local
    from application.dependencies import create_ingest_document_use_case
    from application.use_cases.ingest_document import IngestDocumentUseCase
    from domain.entities.chunk import Chunk
    from domain.services.search_service import SearchResult
    from domain.value_objects.graph_pattern import GraphPattern
    from infrastructure.services.neo4j_search_service import Neo4jSearchService
    from infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService

# Importar ChunkingMaster para sugerencias
try:
    from .utils.chunking_master import ChunkingMaster, ChunkingResult, ChunkingStrategy
    from langchain_core.documents import Document as LangChainDocument
except ImportError:
    from src.utils.chunking_master import ChunkingMaster, ChunkingResult, ChunkingStrategy
    from langchain_core.documents import Document as LangChainDocument

__version__ = "0.1.0"
__all__ = [
    # Funciones de configuración
    "configure",
    "reset_configuration",
    
    # Funciones de alto nivel
    "ingest_document",
    "search",
    "hybrid_search",
    "search_with_pattern",
    "suggest_chunking_strategy",
    
    # Clases para uso avanzado
    "IngestDocumentUseCase",
    "Chunk",
    "SearchResult",
    "ChunkingRecommendation",
    "GraphPattern",
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
    pattern: Optional["GraphPattern"] = None
) -> List[Chunk]:
    """
    Ingiere un documento al grafo de conocimiento.
    
    Esta es la función principal de alto nivel para usar la librería.
    Carga el documento, lo divide en chunks, genera embeddings y lo persiste en Neo4j.
    
    Usa configuración global si no se especifican parámetros. La configuración puede
    establecerse mediante variables de entorno o programáticamente con configure().
    
    Args:
        file_path: Ruta al archivo a ingerir (Markdown, TXT, Word)
        chunk_size: Tamaño de cada chunk en caracteres (default: 1000)
        chunk_overlap: Overlap entre chunks en caracteres (default: 200)
        clean_text: Si True, limpia el texto antes de procesar (default: True)
        database: Nombre de la base de datos Neo4j (default: desde configuración global)
        embedding_model: Modelo de embeddings a usar (default: desde configuración global)
        pattern: Patrón de grafo opcional. Si es None, usa FILE_PAGE_CHUNK (default: None)
    
    Returns:
        Lista de Chunks creados
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el archivo no puede ser procesado
        RuntimeError: Si hay un error al conectarse a Neo4j
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Configurar (opcional, también puede usar variables de entorno)
        >>> ungraph.configure(
        ...     neo4j_uri="bolt://localhost:7687",
        ...     neo4j_password="password"
        ... )
        >>> 
        >>> # Ingerir un documento (usa FILE_PAGE_CHUNK por defecto)
        >>> chunks = ungraph.ingest_document("mi_documento.md")
        >>> print(f"✅ {len(chunks)} chunks creados")
        >>>
        >>> # Con parámetros personalizados
        >>> chunks = ungraph.ingest_document(
        ...     "documento.txt",
        ...     chunk_size=500,
        ...     chunk_overlap=100
        ... )
        >>>
        >>> # Con patrón personalizado
        >>> from ungraph.domain.value_objects.graph_pattern import GraphPattern, NodeDefinition
        >>> simple_pattern = GraphPattern(
        ...     name="SIMPLE_CHUNK",
        ...     description="Solo chunks",
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
        raise FileNotFoundError(f"El archivo no existe: {file_path}")
    
    # Obtener configuración global
    settings = get_settings()
    
    # Usar parámetros proporcionados o configuración global
    db_name = database or settings.neo4j_database
    emb_model = embedding_model or settings.embedding_model
    
    # Crear caso de uso usando el Composition Root
    use_case = create_ingest_document_use_case(
        database=db_name,
        embedding_model=emb_model
    )
    
    try:
        # Ejecutar el caso de uso
        chunks = use_case.execute(
            file_path=file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            clean_text=clean_text,
            pattern=pattern
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
    Busca en el grafo de conocimiento usando búsqueda por texto.
    
    Args:
        query_text: Texto a buscar
        limit: Número máximo de resultados (default: 5)
        database: Nombre de la base de datos Neo4j (default: desde configuración global)
    
    Returns:
        Lista de SearchResult ordenados por score descendente
    
    Raises:
        ValueError: Si el query_text está vacío
        RuntimeError: Si hay un error al conectarse a Neo4j
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Buscar en el grafo
        >>> results = ungraph.search("computación cuántica")
        >>> for result in results:
        ...     print(f"Score: {result.score:.3f}")
        ...     print(f"Contenido: {result.content[:200]}...")
        ...     print("---")
    """
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


def hybrid_search(
    query_text: str,
    limit: int = 5,
    weights: Tuple[float, float] = (0.3, 0.7),
    database: Optional[str] = None,
    embedding_model: Optional[str] = None
) -> List[SearchResult]:
    """
    Búsqueda híbrida combinando texto y similitud vectorial.
    
    Esta función combina búsqueda por texto (full-text) y búsqueda vectorial
    para obtener mejores resultados.
    
    Args:
        query_text: Texto a buscar
        limit: Número máximo de resultados (default: 5)
        weights: Pesos para combinar scores (text_weight, vector_weight) (default: (0.3, 0.7))
        database: Nombre de la base de datos Neo4j (default: desde configuración global)
        embedding_model: Modelo de embeddings a usar (default: desde configuración global)
    
    Returns:
        Lista de SearchResult ordenados por score combinado descendente
    
    Raises:
        ValueError: Si el query_text está vacío
        RuntimeError: Si hay un error al conectarse a Neo4j
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Búsqueda híbrida
        >>> results = ungraph.hybrid_search(
        ...     "inteligencia artificial",
        ...     limit=10,
        ...     weights=(0.4, 0.6)  # Más peso a búsqueda vectorial
        ... )
        >>> for result in results:
        ...     print(f"Score: {result.score:.3f}")
        ...     print(f"Contenido: {result.content[:200]}...")
    """
    if not query_text:
        raise ValueError("Query text cannot be empty")
    
    # Obtener configuración global
    settings = get_settings()
    db_name = database or settings.neo4j_database
    emb_model = embedding_model or settings.embedding_model
    
    # Generar embedding para la consulta
    embedding_service = HuggingFaceEmbeddingService(model_name=emb_model)
    query_embedding = embedding_service.generate_embedding(query_text)
    
    # Realizar búsqueda híbrida
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
    Búsqueda usando un patrón GraphRAG específico.
    
    Soporta patrones básicos y avanzados de búsqueda basados en GraphRAG:
    
    **Patrones básicos** (siempre disponibles):
    - `basic` o `basic_retriever`: Búsqueda full-text simple
    - `metadata_filtering`: Búsqueda con filtros por metadatos
    - `parent_child` o `parent_child_retriever`: Busca en nodos padre y expande a hijos
    
    **Patrones avanzados** (requieren módulos opcionales):
    - `local` o `local_retriever`: Búsqueda en comunidades pequeñas (requiere ungraph[gds])
    - `graph_enhanced` o `graph_enhanced_vector`: Búsqueda vectorial mejorada con traversal (requiere ungraph[gds])
    - `community_summary` o `community_summary_gds`: Resúmenes de comunidades (requiere ungraph[gds])
    
    Args:
        query_text: Texto a buscar
        pattern_type: Tipo de patrón
        limit: Número máximo de resultados (default: 5)
        database: Nombre de la base de datos Neo4j (default: desde configuración global)
        embedding_model: Modelo de embeddings para patrones que lo requieren (default: desde configuración)
        **kwargs: Parámetros específicos del patrón
    
    Returns:
        Lista de SearchResult ordenados por score descendente
    
    Raises:
        ValueError: Si el query_text está vacío o pattern_type es inválido
        RuntimeError: Si hay un error al conectarse a Neo4j
        ImportError: Si se requiere un módulo opcional no instalado
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Búsqueda básica
        >>> results = ungraph.search_with_pattern(
        ...     "machine learning",
        ...     pattern_type="basic",
        ...     limit=5
        ... )
        >>> 
        >>> # Búsqueda con filtros de metadatos
        >>> results = ungraph.search_with_pattern(
        ...     "machine learning",
        ...     pattern_type="metadata_filtering",
        ...     metadata_filters={"filename": "ai_paper.md", "page_number": 1},
        ...     limit=10
        ... )
        >>> 
        >>> # Búsqueda parent-child
        >>> results = ungraph.search_with_pattern(
        ...     "inteligencia artificial",
        ...     pattern_type="parent_child_retriever",
        ...     parent_label="Page",
        ...     child_label="Chunk",
        ...     limit=5
        ... )
        >>> 
        >>> # Búsqueda avanzada: Graph-Enhanced (requiere ungraph[gds])
        >>> results = ungraph.search_with_pattern(
        ...     "machine learning",
        ...     pattern_type="graph_enhanced",
        ...     limit=5,
        ...     max_traversal_depth=2
        ... )
        >>> 
        >>> # Búsqueda avanzada: Local Retriever (requiere ungraph[gds])
        >>> results = ungraph.search_with_pattern(
        ...     "neural networks",
        ...     pattern_type="local",
        ...     limit=5,
        ...     community_threshold=3,
        ...     max_depth=1
        ... )
    """
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
    evaluate_all: bool = False
) -> ChunkingRecommendation:
    """
    Sugiere la mejor estrategia de chunking para un documento con explicación.
    
    Analiza el documento y recomienda la estrategia de chunking más adecuada
    basándose en su estructura, tipo y características.
    
    Args:
        file_path: Ruta al archivo a analizar
        chunk_size: Tamaño de chunk deseado (opcional, se calcula automáticamente)
        chunk_overlap: Overlap deseado (opcional, se calcula automáticamente)
        evaluate_all: Si True, evalúa todas las estrategias candidatas (default: False)
    
    Returns:
        ChunkingRecommendation con estrategia recomendada, explicación y alternativas
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el archivo no puede ser procesado
    
    Example:
        >>> import ungraph
        >>> 
        >>> # Obtener recomendación
        >>> recommendation = ungraph.suggest_chunking_strategy("documento.md")
        >>> print(f"Estrategia recomendada: {recommendation.strategy}")
        >>> print(f"Explicación: {recommendation.explanation}")
        >>> print(f"Chunk size: {recommendation.chunk_size}")
        >>> print(f"Quality score: {recommendation.quality_score:.2f}")
        >>> 
        >>> # Ver alternativas evaluadas
        >>> for alt in recommendation.alternatives:
        ...     print(f"  - {alt['strategy']}: score {alt['score']:.2f}")
        >>> 
        >>> # Usar la recomendación
        >>> chunks = ungraph.ingest_document(
        ...     "documento.md",
        ...     chunk_size=recommendation.chunk_size,
        ...     chunk_overlap=recommendation.chunk_overlap
        ... )
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"El archivo no existe: {file_path}")
    
    # Cargar documento usando el loader
    try:
        from .infrastructure.services.langchain_document_loader_service import LangChainDocumentLoaderService
        from .infrastructure.services.simple_text_cleaning_service import SimpleTextCleaningService
    except ImportError:
        from infrastructure.services.langchain_document_loader_service import LangChainDocumentLoaderService
        from infrastructure.services.simple_text_cleaning_service import SimpleTextCleaningService
    
    text_cleaning_service = SimpleTextCleaningService()
    loader_service = LangChainDocumentLoaderService(text_cleaning_service=text_cleaning_service)
    
    # Cargar documento
    domain_documents = loader_service.load(file_path, clean=False)
    if not domain_documents:
        raise ValueError(f"No se pudo cargar el documento: {file_path}")
    
    # Convertir a LangChain Document
    lc_document = LangChainDocument(
        page_content=domain_documents[0].content,
        metadata=domain_documents[0].metadata
    )
    
    # Crear ChunkingMaster
    master = ChunkingMaster()
    
    # Encontrar mejor estrategia
    result: ChunkingResult = master.find_best_chunking_strategy(
        documents=[lc_document],
        file_path=file_path,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        evaluate_all=evaluate_all
    )
    
    # Generar explicación
    explanation = _generate_chunking_explanation(result, master)
    
    # Obtener alternativas (si se evaluaron múltiples)
    alternatives = []
    if evaluate_all:
        # Si evaluate_all=True, ChunkingMaster ya evaluó múltiples estrategias
        # Por ahora, solo incluimos la mejor. En una implementación completa,
        # podríamos almacenar todas las evaluaciones
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


def _generate_chunking_explanation(result: ChunkingResult, master: ChunkingMaster) -> str:
    """Genera una explicación legible de por qué se eligió esta estrategia."""
    strategy_name = result.strategy.value
    doc_type = result.config.get('doc_type', 'unknown')
    structure = result.config.get('structure', {})
    metrics = result.metrics
    
    explanation_parts = [
        f"Se recomienda la estrategia '{strategy_name}' porque:"
    ]
    
    # Explicación basada en tipo de documento
    if doc_type == 'markdown':
        explanation_parts.append("- El documento es Markdown con estructura de headers")
        if strategy_name == 'markdown_header':
            explanation_parts.append("- La estrategia preserva la jerarquía de headers")
    elif doc_type == 'python':
        explanation_parts.append("- El documento contiene código Python")
        if strategy_name == 'language_specific':
            explanation_parts.append("- La estrategia respeta la sintaxis del lenguaje")
    else:
        explanation_parts.append(f"- El documento es de tipo '{doc_type}'")
    
    # Explicación basada en métricas
    if metrics.avg_sentence_completeness > 0.9:
        explanation_parts.append("- Alta preservación de oraciones completas (>90%)")
    if metrics.avg_paragraph_preservation > 0.8:
        explanation_parts.append("- Buena preservación de párrafos (>80%)")
    
    # Explicación basada en estructura
    if structure.get('headers', 0) > 0:
        explanation_parts.append(f"- El documento tiene {structure['headers']} headers")
    if structure.get('paragraphs', 0) > 0:
        explanation_parts.append(f"- El documento tiene {structure['paragraphs']} párrafos")
    
    explanation_parts.append(f"- Generará aproximadamente {metrics.num_chunks} chunks")
    explanation_parts.append(f"- Tamaño promedio de chunk: {metrics.avg_chunk_size:.0f} caracteres")
    explanation_parts.append(f"- Score de calidad: {master.evaluator.score_strategy(metrics):.2f}/1.0")
    
    return "\n".join(explanation_parts)


# Exportar clases para uso avanzado
__all__.extend([
    "create_ingest_document_use_case",  # Para usuarios avanzados
])

