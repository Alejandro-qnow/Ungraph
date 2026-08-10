"""
Caso de Uso: IngestDocumentUseCase

Orquesta el flujo completo de ingestión de documentos siguiendo el patrón ETI:
1. Extract: Cargar documento desde archivo
2. Transform: Dividir en chunks, generar embeddings
3. Inference: Extraer entidades, relaciones y facts (opcional)
4. Persistir en el grafo
5. Crear relaciones entre chunks
"""

import hashlib
import json
import logging
import uuid
from pathlib import Path
from typing import Any, List, Optional

from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.entities.fact import Fact
from ungraph.domain.entities.relation import Relation
from ungraph.domain.repositories.catalog_repository import (
    BibliographicArticleRecord,
    CatalogRepository,
)
from ungraph.domain.services.document_loader_service import DocumentLoaderService
from ungraph.domain.services.chunking_service import ChunkingService
from ungraph.domain.services.embedding_service import EmbeddingService
from ungraph.domain.services.index_service import IndexService
from ungraph.domain.services.inference_service import InferenceService
from ungraph.domain.repositories.chunk_repository import ChunkRepository
from ungraph.domain.services.context_optimization_service import ContextOptimizationService
from ungraph.domain.value_objects.deduplication import normalize_doi
from ungraph.domain.value_objects.graph_pattern import GraphPattern
from ungraph.domain.value_objects.document_type import DocumentType
from ungraph.utils.chunk_metadata import enrich_chunks_logical_page_numbers
from ungraph.utils.chunk_retrieval_context import apply_retrieval_optimization_to_chunks

logger = logging.getLogger(__name__)


class IngestDocumentUseCase:
    """
    Caso de uso para ingerir un documento completo al grafo de conocimiento.
    
    Este caso de uso:
    - Depende SOLO de interfaces del dominio (no de implementaciones concretas)
    - Orquesta el flujo completo de ingestión
    - Es fácil de testear (puedes mockear las dependencias)
    """
    
    def __init__(
        self,
        document_loader_service: DocumentLoaderService,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        index_service: IndexService,
        chunk_repository: ChunkRepository,
        inference_service: Optional[InferenceService] = None,
        context_optimization_service: Optional[ContextOptimizationService] = None,
        catalog_repository: Optional[CatalogRepository] = None,
    ):
        """
        Inicializa el caso de uso con sus dependencias.
        
        Args:
            document_loader_service: Servicio para cargar documentos
            chunking_service: Servicio para dividir documentos
            embedding_service: Servicio para generar embeddings
            index_service: Servicio para crear índices
            chunk_repository: Repositorio para persistir chunks
            inference_service: Servicio de inferencia (opcional). Si se proporciona,
                              se ejecuta la fase Inference del patrón ETI.
            context_optimization_service: Opcional; si se usa con ``retrieval_optimization``,
                              genera texto derivado para nodo RetrievalChunk.
        """
        self.document_loader_service = document_loader_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.index_service = index_service
        self.chunk_repository = chunk_repository
        self.inference_service = inference_service
        self.context_optimization_service = context_optimization_service
        self.catalog_repository = catalog_repository

    def execute(
        self,
        file_path: Path,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        clean_text: bool = True,
        pattern: Optional[GraphPattern] = None,
        source_url: Optional[str] = None,
        retrieval_optimization: bool = False,
        source_document_uid: Optional[str] = None,
        doi: Optional[str] = None,
        external_id: Optional[str] = None,
        abstract_text: Optional[str] = None,
        embedded_file_metadata_snapshot: Optional[Any] = None,
        persist_catalog_snapshot: Optional[bool] = None,
        report_output_dir: Optional[Path] = None,
        report_sample_limit: int = 400,
        **loader_kwargs: Any,
    ) -> List[Chunk]:
        """
        Ejecuta el caso de uso completo siguiendo el patrón ETI.
        
        Flujo ETI:
        1. Extract: Cargar documento desde archivo
        2. Transform: Dividir en chunks, generar embeddings
        3. Inference: Extraer entidades, relaciones y facts (si inference_service está disponible)
        4. Persistir chunks y facts en el grafo (usando patrón si se proporciona)
        5. Crear relaciones entre chunks consecutivos
        
        Args:
            file_path: Ruta al archivo a ingerir
            chunk_size: Tamaño de cada chunk (default: 1000)
            chunk_overlap: Overlap entre chunks (default: 200)
            clean_text: Si True, limpia el texto (default: True)
            pattern: Patrón de grafo opcional. Si es None, usa FILE_PAGE_CHUNK (comportamiento por defecto)
            retrieval_optimization: Si True y hay ``context_optimization_service``,
                rellena texto derivado para nodo ``RetrievalChunk`` (el contenido semántico
                completo sigue en ``Chunk.page_content``).
            report_output_dir: Si se indica, al finalizar se escribe el bundle HTML del reporte ETI.
            report_sample_limit: Límite de nodos ancla para la muestra NVL del reporte.
        
        Returns:
            Lista de Chunks creados
        
        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo no puede ser procesado
        
        Note:
            Si se proporciona un patrón personalizado, debe ser compatible con la estructura de Chunk.
            El patrón FILE_PAGE_CHUNK es el patrón por defecto y está completamente soportado.
            La fase Inference solo se ejecuta si inference_service está configurado.
        """
        logger.info(f"Starting document ingestion: {file_path}")
        if source_url:
            loader_kwargs = {**loader_kwargs, "source_url": source_url}

        # Si no se proporciona patrón, usar FILE_PAGE_CHUNK (comportamiento por defecto)
        if pattern is None:
            from ungraph.domain.value_objects.predefined_patterns import FILE_PAGE_CHUNK_PATTERN
            pattern = FILE_PAGE_CHUNK_PATTERN
        
        logger.info(f"Using pattern: {pattern.name}")
        
        # 1. Cargar documento
        logger.info("Step 1: Loading document")
        documents = self.document_loader_service.load(
            file_path, clean=clean_text, **loader_kwargs
        )
        
        if not documents:
            raise ValueError(f"No documents loaded from {file_path}")
        
        # Por ahora procesamos solo el primer documento
        # (en el futuro podríamos procesar múltiples documentos)
        document = documents[0]
        
        # 2. Dividir en chunks (HTML: markdown_header + secciones lógicas como Page)
        logger.info("Step 2: Chunking document")
        if document.file_type == DocumentType.HTML.value and hasattr(
            self.chunking_service, "smart_chunk"
        ):
            chunks, _ = self.chunking_service.smart_chunk(
                document,
                preferred_strategy="markdown_header",
                evaluate_all=False,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            enrich_chunks_logical_page_numbers(chunks)
            sid = document.metadata.get("source_id")
            if sid:
                for c in chunks:
                    c.metadata.setdefault("source_id", sid)
            url = document.metadata.get("canonical_url")
            if url:
                for c in chunks:
                    c.metadata.setdefault("canonical_url", url)
        else:
            chunks = self.chunking_service.chunk(
                document,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        
        if not chunks:
            raise ValueError("No chunks generated from document")

        source_uid = source_document_uid or document.metadata.get("source_document_uid")
        if not source_uid:
            source_uid = str(uuid.uuid4())
        document.metadata["source_document_uid"] = source_uid
        resolved = Path(file_path).resolve()
        parent_ids = {str(resolved)}
        for key in ("source_id", "canonical_url"):
            val = document.metadata.get(key)
            if val:
                parent_ids.add(str(val))
        parent_list = sorted(parent_ids)
        doi_n = normalize_doi(doi or document.metadata.get("doi"))

        for ch in chunks:
            ch.metadata.setdefault("source_document_uid", source_uid)
            ch.metadata["source_parent_uids"] = parent_list
            ch.source_document_uid = source_uid
            ch.source_parent_uids = parent_list
            if doi_n:
                ch.metadata["doi_norm"] = doi_n
                ch.doi_norm = doi_n

        if retrieval_optimization:
            if self.context_optimization_service:
                logger.info(
                    "Step 2b: Retrieval context optimization (RetrievalChunk / HAS_RETRIEVAL_VIEW)"
                )
                apply_retrieval_optimization_to_chunks(
                    chunks, self.context_optimization_service
                )
            else:
                logger.warning(
                    "retrieval_optimization=True but no context_optimization_service; "
                    "skipping retrieval-optimized text"
                )

        # 3. Generar embeddings
        logger.info("Step 3: Generating embeddings")
        embeddings = self.embedding_service.generate_embeddings_batch(chunks)
        
        # Asignar embeddings a chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embeddings = embedding.vector
            chunk.embeddings_dimensions = embedding.dimensions
            chunk.embedding_encoder_info = embedding.encoder_info
        
        # 4. Inference: Extraer entidades, relaciones y facts (si está disponible)
        all_facts: List[Fact] = []
        all_relations: List[Relation] = []
        if self.inference_service:
            logger.info("Step 4: Running inference phase (ETI)")
            for chunk in chunks:
                try:
                    entities = self.inference_service.extract_entities(chunk)
                    chunk_rels = self.inference_service.extract_relations(chunk, entities)
                    chunk_facts = self.inference_service.infer_facts(chunk, entities=entities)
                    all_relations.extend(chunk_rels)
                    all_facts.extend(chunk_facts)
                    logger.debug(
                        "Inferred %s facts, %s relations from chunk %s",
                        len(chunk_facts),
                        len(chunk_rels),
                        chunk.id,
                    )
                except Exception as e:
                    logger.warning(f"Error inferring facts from chunk {chunk.id}: {e}")
                    # Continuar con otros chunks aunque uno falle
            logger.info(
                "Inference phase completed. Generated %s facts, %s relations",
                len(all_facts),
                len(all_relations),
            )
        else:
            logger.info("Step 4: Skipping inference phase (no inference_service provided)")
        
        # 5. Configurar índices
        logger.info("Step 5: Setting up indexes")
        self.index_service.setup_all_indexes()
        
        # 6. Persistir chunks usando el patrón especificado
        logger.info(f"Step 6: Persisting chunks with pattern {pattern.name}")
        # Verificar si el repositorio soporta save_with_pattern
        if hasattr(self.chunk_repository, 'save_with_pattern'):
            self.chunk_repository.save_with_pattern(chunks, pattern)
        else:
            # Fallback: usar save_batch si el repositorio no soporta patrones
            logger.warning("Repository does not support patterns, using save_batch()")
            self.chunk_repository.save_batch(chunks)
        
        # 7. Persistir facts si se generaron
        if all_facts and hasattr(self.chunk_repository, 'save_facts'):
            logger.info(f"Step 7: Persisting {len(all_facts)} facts")
            try:
                self.chunk_repository.save_facts(all_facts)
                logger.info(f"Successfully persisted {len(all_facts)} facts")
            except Exception as e:
                logger.error(f"Error persisting facts: {e}")
                # No fallar el proceso completo si falla la persistencia de facts
        elif all_facts:
            logger.warning("Facts generated but repository does not support save_facts()")

        if all_relations and hasattr(self.chunk_repository, "save_relations"):
            logger.info("Step 7b: Persisting %s inferred relations", len(all_relations))
            try:
                self.chunk_repository.save_relations(all_relations)
                logger.info("Successfully persisted %s relations", len(all_relations))
            except Exception as e:
                logger.error("Error persisting relations: %s", e)
        elif all_relations:
            logger.warning(
                "Relations generated but repository does not support save_relations()"
            )
        
        # 8. Crear relaciones entre chunks consecutivos
        # Solo para FILE_PAGE_CHUNK por ahora
        if pattern.name == "FILE_PAGE_CHUNK":
            logger.info("Step 8: Creating scoped chunk relationships")
            self.chunk_repository.create_chunk_relationships(
                source_document_uid=source_uid,
                filename=document.filename,
            )
        else:
            logger.info(f"Skipping chunk relationships for pattern {pattern.name}")

        persist_cat = persist_catalog_snapshot
        if persist_cat is None:
            persist_cat = self.catalog_repository is not None

        if persist_cat and self.catalog_repository:
            try:
                file_bytes = Path(file_path).read_bytes()
                sha_hex = hashlib.sha256(file_bytes).hexdigest()
                stat = Path(file_path).stat()
                snap = (
                    json.dumps(
                        embedded_file_metadata_snapshot,
                        sort_keys=True,
                        ensure_ascii=False,
                        default=str,
                    )
                    if embedded_file_metadata_snapshot
                    else None
                )
                abs_emb = None
                emb_model = None
                if abstract_text and len(abstract_text.strip()) >= 40:
                    try:
                        vo = self.embedding_service.generate_embedding(abstract_text)
                        abs_emb = vo.vector
                        emb_model = vo.encoder_info
                    except Exception as ex_emb:
                        logger.debug("Skipping abstract_embedding for catalog: %s", ex_emb)
                self.catalog_repository.merge_article(
                    BibliographicArticleRecord(
                        document_uid=source_uid,
                        doi_norm=doi_n,
                        external_id=str(external_id) if external_id is not None else None,
                        abstract_text=abstract_text,
                        abstract_embedding=abs_emb,
                        embedding_model=emb_model,
                        canonical_filename=document.filename,
                        source_sha256=sha_hex,
                        source_size_bytes=stat.st_size,
                        embedded_file_metadata_snapshot=snap,
                        ingested_at=None,
                    )
                )
            except Exception as ex_cat:
                logger.warning("Catalog merge after ingest skipped: %s", ex_cat)

        if report_output_dir is not None:
            try:
                from ungraph.core.configuration import get_settings
                from ungraph.utils.eti_report_bundler import emit_eti_report_after_ingest

                st = get_settings()
                emit_eti_report_after_ingest(
                    settings=st,
                    output_dir=Path(report_output_dir),
                    file_path=resolved,
                    source_document_uid=source_uid,
                    pattern_name=pattern.name,
                    chunks=chunks,
                    facts_count=len(all_facts),
                    relations_count=len(all_relations),
                    inference_mode=st.inference_mode,
                    sample_node_limit=report_sample_limit,
                )
            except Exception as ex_rep:
                logger.warning("ETI HTML report skipped: %s", ex_rep)

        logger.info(
            f"Document ingestion completed. Created {len(chunks)} chunks"
            + (f" and {len(all_facts)} facts" if all_facts else "")
        )
        return chunks

