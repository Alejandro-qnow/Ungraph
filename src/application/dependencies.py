"""
Composition Root: Dependencies

Factory para crear y configurar todas las dependencias.
Este es el único lugar donde se crean implementaciones concretas.
"""

from pathlib import Path
from typing import Optional

from application.use_cases.ingest_document import IngestDocumentUseCase

# Domain - Interfaces
from domain.services.inference_service import InferenceService

# Infrastructure - Implementaciones concretas
from infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository
from infrastructure.services.langchain_document_loader_service import LangChainDocumentLoaderService
from infrastructure.services.simple_text_cleaning_service import SimpleTextCleaningService
from infrastructure.services.langchain_chunking_service import LangChainChunkingService
from infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
from infrastructure.services.neo4j_index_service import Neo4jIndexService
from infrastructure.services.spacy_inference_service import SpacyInferenceService


def create_inference_service(
    model_name: str = "en_core_web_sm",
    enable_inference: bool = True,
    language: str = "en"
) -> Optional[InferenceService]:
    """
    Factory: crea y configura el servicio de inferencia.
    
    Para el release v0.1.0, solo se implementa SpacyInferenceService.
    Implementaciones LLM pueden añadirse en futuras versiones.
    
    Args:
        model_name: Nombre del modelo de spaCy (default: en_core_web_sm)
        enable_inference: Si False, retorna None (deshabilita fase Inference)
        language: Idioma para inferencia ('en' para inglés, 'es' para español)
                 Si se proporciona, sobrescribe model_name con el modelo apropiado
    
    Returns:
        InferenceService configurado o None si está deshabilitado
    
    Raises:
        ImportError: Si spaCy no está instalado y enable_inference=True
        OSError: Si el modelo de spaCy no está disponible
    
    Note:
        Modelos de spaCy recomendados:
        - Inglés: en_core_web_sm (instalar con: python -m spacy download en_core_web_sm)
        - Español: es_core_news_sm (instalar con: python -m spacy download es_core_news_sm)
    """
    if not enable_inference:
        return None
    
    # Seleccionar modelo según idioma si se especifica
    if language == "es":
        model_name = "es_core_news_sm"
    elif language == "en":
        model_name = "en_core_web_sm"
    # Si language no es 'en' ni 'es', usar model_name proporcionado
    
    try:
        return SpacyInferenceService(model_name=model_name)
    except ImportError as e:
        # Si spaCy no está instalado, retornar None en lugar de fallar
        # Esto permite usar el pipeline ET sin Inference
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"spaCy no está disponible. Fase Inference deshabilitada. "
            f"Instala con: pip install ungraph[infer] && python -m spacy download {model_name}"
        )
        return None
    except OSError as e:
        # Si el modelo no está disponible, sugerir instalación
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Modelo spaCy '{model_name}' no encontrado. "
            f"Instala con: python -m spacy download {model_name}"
        )
        return None


def create_ingest_document_use_case(
    database: str = "neo4j",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    enable_inference: bool = True,
    inference_model: str = "en_core_web_sm",
    inference_language: str = "en"
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
        enable_inference: Si True, habilita fase Inference del patrón ETI (default: True)
        inference_model: Modelo de spaCy para inferencia (default: en_core_web_sm)
        inference_language: Idioma para inferencia ('en' para inglés, 'es' para español) (default: "en")
    
    Note:
        Para usar inferencia en español:
        - Instalar: pip install ungraph[infer-es]
        - Descargar modelo: python -m spacy download es_core_news_sm
        - Usar: create_ingest_document_use_case(inference_language="es")
    
    Returns:
        IngestDocumentUseCase configurado y listo para usar
    
    Note:
        Si enable_inference=True pero spaCy no está instalado, el pipeline
        funcionará sin fase Inference (solo ET).
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
    
    # Crear servicio de inferencia (opcional)
    inference_service = create_inference_service(
        model_name=inference_model,
        enable_inference=enable_inference,
        language=inference_language
    )
    
    # Crear caso de uso con dependencias inyectadas
    return IngestDocumentUseCase(
        document_loader_service=document_loader_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        index_service=index_service,
        chunk_repository=chunk_repository,
        inference_service=inference_service
    )

