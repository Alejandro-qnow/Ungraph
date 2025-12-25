"""
Composition Root: Dependencies

Factory para crear y configurar todas las dependencias.
Este es el único lugar donde se crean implementaciones concretas.
"""

from pathlib import Path
from typing import Optional

from application.use_cases.ingest_document import IngestDocumentUseCase

# Infrastructure - Implementaciones concretas
from infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository
from infrastructure.services.langchain_document_loader_service import LangChainDocumentLoaderService
from infrastructure.services.simple_text_cleaning_service import SimpleTextCleaningService
from infrastructure.services.langchain_chunking_service import LangChainChunkingService
from infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
from infrastructure.services.neo4j_index_service import Neo4jIndexService


def create_ingest_document_use_case(
    database: str = "neo4j",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> IngestDocumentUseCase:
    """
    Factory: crea y configura el caso de uso IngestDocumentUseCase.
    
    Este método:
    - Crea todas las implementaciones concretas
    - Configura las dependencias
    - Retorna el caso de uso listo para usar
    
    Args:
        database: Nombre de la base de datos Neo4j (default: "neo4j")
        embedding_model: Modelo de embeddings a usar (default: all-MiniLM-L6-v2)
    
    Returns:
        IngestDocumentUseCase configurado y listo para usar
    """
    # Crear servicios de infraestructura
    text_cleaning_service = SimpleTextCleaningService()
    
    document_loader_service = LangChainDocumentLoaderService(
        text_cleaning_service=text_cleaning_service
    )
    
    chunking_service = LangChainChunkingService()
    
    embedding_service = HuggingFaceEmbeddingService(
        model_name=embedding_model
    )
    
    index_service = Neo4jIndexService(database=database)
    
    # Crear repositorio
    chunk_repository = Neo4jChunkRepository(database=database)
    
    # Crear caso de uso con dependencias inyectadas
    return IngestDocumentUseCase(
        document_loader_service=document_loader_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        index_service=index_service,
        chunk_repository=chunk_repository
    )

