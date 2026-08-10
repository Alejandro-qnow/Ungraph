"""
Implementación concreta: Neo4jChunkRepository

Implementa ChunkRepository usando Neo4j.
Envuelve el código existente de graph_operations.py.
"""

from collections import defaultdict
from typing import List, Optional
from neo4j import GraphDatabase
from neo4j.exceptions import ClientError
import logging

from ungraph.domain.repositories.chunk_repository import ChunkRepository
from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.entities.fact import Fact
from ungraph.domain.entities.relation import Relation
from ungraph.domain.value_objects.graph_pattern import GraphPattern
from ungraph.utils.neo4j_infer_reltype import (
    EXTRACTED_REL_FALLBACK,
    is_safe_interpolated_reltype,
    native_neo4j_relationship_type,
)

logger = logging.getLogger(__name__)

# Importar funciones de graph_operations de manera lazy para evitar importaciones circulares
# Estas funciones se importan solo cuando se necesitan, no al nivel del módulo
try:
    from ungraph.utils.graph_operations import (
        graph_session,
        extract_document_structure,
        create_chunk_relationships as neo4j_create_chunk_relationships,
        merge_retrieval_context_view,
    )
except ImportError as e:
    logger.error("Cannot import graph_operations. Ensure the package is installed or PYTHONPATH includes project root. Original error: %s", e)
    raise


def _chunk_lineage_params(chunk: Chunk) -> dict:
    uid = chunk.get_source_document_uid()
    parents = chunk.get_source_parent_uids()
    doi = chunk.doi_norm if chunk.doi_norm is not None else chunk.metadata.get('doi_norm')
    primary = (
        chunk.primary_parent_uid
        if chunk.primary_parent_uid is not None
        else chunk.metadata.get('primary_parent_uid')
    )
    return {
        'source_document_uid': uid,
        'source_parent_uids': parents,
        'doi_norm': doi,
        'primary_parent_uid': primary,
    }


class Neo4jChunkRepository(ChunkRepository):
    """
    Implementación de ChunkRepository usando Neo4j.
    
    Esta implementación:
    - Crea File y Page automáticamente al guardar Chunks
    - Usa el código existente de graph_operations.py
    - Maneja la conexión a Neo4j internamente
    """
    
    def __init__(self, database: str = "neo4j"):
        """
        Inicializa el repositorio.
        
        Args:
            database: Nombre de la base de datos Neo4j (default: "neo4j")
        """
        self.database = database
        self._driver = None
    
    def _get_driver(self) -> GraphDatabase:
        """Obtiene o crea el driver de Neo4j."""
        if self._driver is None:
            self._driver = graph_session()
        return self._driver
    
    def save(self, chunk: Chunk) -> None:
        """
        Guarda un chunk individual en Neo4j.
        
        Crea automáticamente File y Page si no existen.
        """
        self.save_batch([chunk])
    
    def save_batch(self, chunks: List[Chunk]) -> None:
        """
        Guarda múltiples chunks en Neo4j de forma eficiente.
        
        Crea automáticamente File y Page si no existen.
        """
        if not chunks:
            return
        
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                for chunk in chunks:
                    # Extraer datos del chunk
                    filename = chunk.metadata.get('filename', 'unknown')
                    page_number = chunk.metadata.get('page_number', 1)
                    
                    # Convertir embeddings a lista si es necesario
                    embeddings = chunk.embeddings
                    if embeddings is None:
                        embeddings = []
                    
                    lin = _chunk_lineage_params(chunk)
                    session.execute_write(
                        extract_document_structure,
                        filename=filename,
                        page_number=page_number,
                        chunk_id=chunk.id,
                        page_content=chunk.page_content,
                        is_unitary=chunk.is_unitary,
                        embeddings=embeddings,
                        embeddings_dimensions=chunk.embeddings_dimensions or 384,
                        embedding_encoder_info=chunk.embedding_encoder_info or 'unknown',
                        chunk_id_consecutive=chunk.chunk_id_consecutive or 0,
                        **lin,
                    )
                    rot = getattr(chunk, "retrieval_optimized_text", None)
                    if rot and str(rot).strip():
                        te = getattr(chunk, "retrieval_token_estimate", None)
                        if te is None:
                            te = max(1, len(str(rot)) // 4)
                        session.execute_write(
                            merge_retrieval_context_view,
                            parent_chunk_id=chunk.id,
                            optimized_text=str(rot).strip(),
                            strategy=chunk.retrieval_optimization_strategy or "heuristic_v1",
                            token_estimate=int(te),
                        )
        except ClientError as e:
            logger.error(f"Error saving chunks to Neo4j: {e}", exc_info=True)
            raise
    
    def find_by_id(self, chunk_id: str) -> Optional[Chunk]:
        """
        Busca un chunk por su ID en Neo4j.
        
        Args:
            chunk_id: Identificador único del chunk
        
        Returns:
            La entidad Chunk si se encuentra, None si no existe
        """
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                result = session.execute_read(
                    self._find_chunk_by_id_query,
                    chunk_id=chunk_id
                )
                
                if not result:
                    return None
                
                # Convertir resultado de Neo4j a entidad Chunk
                record = result[0]
                return self._record_to_chunk(record)
        except Exception as e:
            logger.error(f"Error finding chunk by id {chunk_id}: {e}", exc_info=True)
            raise
    
    def _find_chunk_by_id_query(self, tx, chunk_id: str):
        """Query helper para buscar chunk por ID."""
        query = """
        MATCH (c:Chunk {chunk_id: $chunk_id})
        RETURN c.page_content as page_content,
               c.chunk_id as chunk_id,
               c.chunk_id_consecutive as chunk_id_consecutive,
               c.is_unitary as is_unitary,
               c.embeddings as embeddings,
               c.embeddings_dimensions as embeddings_dimensions,
               c.embedding_encoder_info as embedding_encoder_info,
               c.filename as filename,
               c.page_number as page_number,
               c.source_document_uid as source_document_uid,
               c.source_parent_uids as source_parent_uids,
               c["doi_norm"] AS doi_norm
        LIMIT 1
        """
        result = tx.run(query, chunk_id=chunk_id)
        return list(result)
    
    def find_by_filename(self, filename: str) -> List[Chunk]:
        """
        Busca todos los chunks de un archivo específico en Neo4j.
        
        Args:
            filename: Nombre del archivo
        
        Returns:
            Lista de entidades Chunk del archivo
        """
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                result = session.execute_read(
                    self._find_chunks_by_filename_query,
                    filename=filename
                )
                
                # Convertir resultados de Neo4j a entidades Chunk
                chunks = [self._record_to_chunk(record) for record in result]
                return chunks
        except Exception as e:
            logger.error(f"Error finding chunks by filename {filename}: {e}", exc_info=True)
            raise
    
    def _find_chunks_by_filename_query(self, tx, filename: str):
        """Query helper para buscar chunks por filename."""
        query = """
        MATCH (c:Chunk)
        WHERE c.filename = $filename
        RETURN c.page_content as page_content,
               c.chunk_id as chunk_id,
               c.chunk_id_consecutive as chunk_id_consecutive,
               c.is_unitary as is_unitary,
               c.embeddings as embeddings,
               c.embeddings_dimensions as embeddings_dimensions,
               c.embedding_encoder_info as embedding_encoder_info,
               c.filename as filename,
               c.page_number as page_number,
               c.source_document_uid as source_document_uid,
               c.source_parent_uids as source_parent_uids,
               c["doi_norm"] AS doi_norm
        ORDER BY c.chunk_id_consecutive ASC
        """
        result = tx.run(query, filename=filename)
        return list(result)

    def list_chunk_ids_without_derived_facts(self, *, min_content_chars: int = 1) -> List[str]:
        """
        Chunks sin facts derivados (re-inferencia / minado) y con texto suficiente.
        """
        driver = self._get_driver()
        q = """
        MATCH (c:Chunk)
        WHERE NOT EXISTS { MATCH (:Fact)-[:DERIVED_FROM]->(c) }
          AND size(trim(toString(coalesce(c.page_content, '')))) >= $min_chars
        RETURN c.chunk_id AS id
        ORDER BY c.chunk_id
        """
        try:
            with driver.session(database=self.database) as session:

                def work(tx):
                    return [r["id"] for r in tx.run(q, min_chars=min_content_chars)]

                return session.execute_read(work)
        except Exception as e:
            logger.error(
                "Error listing chunks without derived facts: %s",
                e,
                exc_info=True,
            )
            raise
    
    def _record_to_chunk(self, record) -> Chunk:
        """Convierte un record de Neo4j a entidad Chunk."""
        from ungraph.domain.entities.chunk import Chunk

        extra_lists = record.get('source_parent_uids') or []
        if extra_lists and not isinstance(extra_lists, list):
            extra_lists = [extra_lists]
        metadata = {
            'filename': record.get('filename', 'unknown'),
            'page_number': record.get('page_number', 1),
        }
        if record.get('source_document_uid'):
            metadata['source_document_uid'] = record['source_document_uid']
        if extra_lists:
            metadata['source_parent_uids'] = list(extra_lists)
        if record.get('doi_norm'):
            metadata['doi_norm'] = record['doi_norm']

        return Chunk(
            id=record.get('chunk_id', ''),
            page_content=record.get('page_content', ''),
            metadata=metadata,
            is_unitary=record.get('is_unitary', False),
            chunk_id_consecutive=record.get('chunk_id_consecutive', 0),
            embeddings=record.get('embeddings'),
            embeddings_dimensions=record.get('embeddings_dimensions'),
            embedding_encoder_info=record.get('embedding_encoder_info'),
            source_document_uid=record.get('source_document_uid'),
            source_parent_uids=list(extra_lists) if extra_lists else None,
            doi_norm=record.get('doi_norm'),
        )
    
    def save_with_pattern(self, chunks: List[Chunk], pattern: GraphPattern) -> None:
        """
        Guarda chunks usando un patrón específico de grafo.
        
        Si el patrón es FILE_PAGE_CHUNK, usa save_batch() existente (compatibilidad).
        Si es otro patrón, usa PatternService para aplicar el patrón.
        
        Args:
            chunks: Lista de chunks a guardar
            pattern: Patrón de grafo a usar
        
        Raises:
            ValueError: Si el patrón es inválido
            RuntimeError: Si hay un error al guardar
        """
        if not chunks:
            return
        
        # Importar PatternService aquí para evitar dependencia circular
        from ungraph.infrastructure.services.neo4j_pattern_service import Neo4jPatternService
        
        # Si es FILE_PAGE_CHUNK, usar método existente (backward compatibility)
        if pattern.name == "FILE_PAGE_CHUNK":
            logger.info("Using existing save_batch() for FILE_PAGE_CHUNK pattern")
            self.save_batch(chunks)
            return
        
        # Para otros patrones, usar PatternService
        # PatternService maneja su propia sesión, así que solo necesitamos llamarlo
        pattern_service = Neo4jPatternService(database=self.database)
        
        try:
            for chunk in chunks:
                # Convertir chunk a formato de datos para el patrón
                data = self._chunk_to_pattern_data(chunk, pattern)
                
                # Aplicar patrón usando PatternService
                # PatternService.apply_pattern maneja la ejecución internamente
                pattern_service.apply_pattern(pattern, data)
        except Exception as e:
            logger.error(f"Error saving chunks with pattern {pattern.name}: {e}", exc_info=True)
            raise
        finally:
            pattern_service.close()
    
    def _chunk_to_pattern_data(self, chunk: Chunk, pattern: GraphPattern) -> dict:
        """
        Convierte un Chunk a formato de datos compatible con el patrón.
        
        Extrae los datos necesarios del chunk según las propiedades requeridas del patrón.
        """
        data = {}
        
        # Extraer datos comunes del chunk
        filename = chunk.metadata.get('filename', 'unknown')
        page_number = chunk.metadata.get('page_number', 1)
        
        # Mapear datos según el patrón
        for node_def in pattern.node_definitions:
            if node_def.label == "Chunk":
                # Propiedades requeridas de Chunk
                data['chunk_id'] = chunk.id
                data['page_content'] = chunk.page_content
                data['embeddings'] = chunk.embeddings or []
                data['embeddings_dimensions'] = chunk.embeddings_dimensions or 384
                
                # Propiedades opcionales
                if 'is_unitary' in node_def.optional_properties:
                    data['is_unitary'] = chunk.is_unitary
                if 'chunk_id_consecutive' in node_def.optional_properties:
                    data['chunk_id_consecutive'] = chunk.chunk_id_consecutive or 0
                if 'embedding_encoder_info' in node_def.optional_properties:
                    data['embedding_encoder_info'] = chunk.embedding_encoder_info or 'unknown'
            
            elif node_def.label == "File":
                data['filename'] = filename
                # createdAt se maneja automáticamente en el query
            
            elif node_def.label == "Page":
                data['filename'] = filename
                data['page_number'] = page_number
        
        return data
    
    
    def create_chunk_relationships(
        self,
        *,
        source_document_uid: Optional[str] = None,
        filename: Optional[str] = None,
        chunk_ids: Optional[List[str]] = None,
        global_legacy: bool = False,
    ) -> None:
        gl = global_legacy
        if not source_document_uid and not filename and not chunk_ids and not gl:
            logger.warning(
                "create_chunk_relationships without scope — falling back to global_legacy (legacy batch path)"
            )
            gl = True
        driver = self._get_driver()

        try:
            with driver.session(database=self.database) as session:
                neo4j_create_chunk_relationships(
                    session,
                    source_document_uid=source_document_uid,
                    filename=filename,
                    chunk_ids=chunk_ids,
                    global_legacy=gl,
                )
        except Exception as e:
            logger.error(f"Error creating chunk relationships: {e}", exc_info=True)
            raise
    
    def save_facts(self, facts: List[Fact]) -> None:
        """
        Guarda facts en Neo4j creando nodos Fact y relaciones DERIVED_FROM.
        
        Para cada fact:
        - Crea un nodo Fact con propiedades: id, subject, predicate, object, confidence, curation_state
        - Crea relación DERIVED_FROM desde Fact hacia Chunk (provenance)
        - Si el object es una entidad mencionada, crea nodo Entity y relación MENTIONS
        
        Args:
            facts: Lista de facts a persistir
        
        Raises:
            ClientError: Si hay un error al guardar en Neo4j
        """
        if not facts:
            return
        
        driver = self._get_driver()
        
        try:
            with driver.session(database=self.database) as session:
                session.execute_write(
                    self._save_facts_query,
                    facts=facts
                )
            logger.info(f"Successfully saved {len(facts)} facts to Neo4j")
        except ClientError as e:
            logger.error(f"Error saving facts to Neo4j: {e}", exc_info=True)
            raise
    
    def _save_facts_query(self, tx, facts: List[Fact]):
        """
        Query helper para guardar facts en Neo4j.
        
        Crea nodos Fact y relaciones DERIVED_FROM hacia Chunks.
        También crea nodos Entity para objetos que son entidades nombradas.
        """
        query = """
        UNWIND $facts AS fact_data
        MATCH (chunk:Chunk {chunk_id: fact_data.provenance_ref})
        
        // Crear o actualizar nodo Fact
        MERGE (fact:Fact {fact_id: fact_data.id})
        SET fact.subject = fact_data.subject,
            fact.predicate = fact_data.predicate,
            fact.object = fact_data.object,
            fact.confidence = fact_data.confidence,
            fact.provenance_ref = fact_data.provenance_ref,
            fact.curation_state = CASE
                WHEN coalesce(fact.curation_state, '') IN ['Curated', 'Invalid']
                THEN fact.curation_state
                ELSE coalesce(fact_data.curation_state, 'Extracted')
            END
        
        // Crear relación DERIVED_FROM (provenance)
        MERGE (fact)-[:DERIVED_FROM]->(chunk)
        
        WITH fact, fact_data, chunk
        
        // Si el object NO es un chunk_id existente, crear nodo Entity
        // y relación MENTIONS desde chunk hacia entity
        WHERE NOT EXISTS {
            MATCH (c:Chunk {chunk_id: fact_data.object})
        }
        
        MERGE (entity:Entity {name: fact_data.object})
        ON CREATE SET entity.entity_id = fact_data.object + '_entity',
                      entity.type = coalesce(fact_data.object_entity_type, 'UNKNOWN'),
                      entity.curation_state = coalesce(fact_data.curation_state, 'Extracted')
        SET entity.type = coalesce(fact_data.object_entity_type, entity.type, 'UNKNOWN'),
            entity.ontology_class_uri = coalesce(
                fact_data.object_ontology_class_uri,
                entity.ontology_class_uri
            ),
            entity.curation_state = CASE
                WHEN coalesce(entity.curation_state, '') IN ['Curated', 'Invalid']
                THEN entity.curation_state
                ELSE coalesce(fact_data.curation_state, 'Extracted')
            END
        
        MERGE (chunk)-[:MENTIONS]->(entity)
        
        RETURN count(fact) as facts_created
        """
        
        # Preparar datos para la query
        facts_data = [
            {
                "id": fact.id,
                "subject": fact.subject,
                "predicate": fact.predicate,
                "object": fact.object,
                "confidence": fact.confidence,
                "provenance_ref": fact.provenance_ref,
                "object_entity_type": fact.object_entity_type,
                "object_ontology_class_uri": fact.object_ontology_class_uri,
                "curation_state": fact.curation_state,
            }
            for fact in facts
        ]
        
        result = tx.run(query, facts=facts_data)
        return list(result)
    
    def save_relations(self, relations: List[Relation]) -> None:
        """
        Crea relaciones inferidas entre :Entity emparejados por ``name``.

        Si ``relation_type`` es un identificador Neo4j seguro (p. ej. ``WORKS_FOR``),
        se usa como tipo nativo; si no, ``EXTRACTED_REL`` + propiedad ``relation_type``.

        Requiere que los nodos existan (p. ej. vía save_facts). Omite filas sin
        ``source_entity_name`` / ``target_entity_name`` o si no hay MATCH.
        """
        if not relations:
            return
        rel_data: List[dict] = []
        for r in relations:
            sn = (r.source_entity_name or "").strip()
            tn = (r.target_entity_name or "").strip()
            if not sn or not tn or sn == tn:
                continue
            cypher_type, is_native = native_neo4j_relationship_type(r.relation_type)
            if not is_native:
                cypher_type = EXTRACTED_REL_FALLBACK
            rel_data.append(
                {
                    "id": r.id,
                    "source_name": sn,
                    "target_name": tn,
                    "relation_type": r.relation_type,
                    "confidence": r.confidence,
                    "provenance_ref": r.provenance_ref,
                    "ontology_property_uri": r.ontology_property_uri,
                    "extraction_method": r.extraction_method,
                    "curation_state": r.curation_state,
                    "_cypher_rel_type": cypher_type,
                }
            )
        if not rel_data:
            return
        buckets: dict[str, List[dict]] = defaultdict(list)
        for row in rel_data:
            ct = row.pop("_cypher_rel_type", EXTRACTED_REL_FALLBACK)
            if not is_safe_interpolated_reltype(ct):
                ct = EXTRACTED_REL_FALLBACK
            buckets[ct].append(row)
        driver = self._get_driver()
        try:
            with driver.session(database=self.database) as session:
                for cypher_type, batch in buckets.items():
                    session.execute_write(
                        self._save_relations_typed_batch,
                        batch,
                        cypher_type,
                    )
            logger.info("Successfully saved %s inferred relations to Neo4j", len(rel_data))
        except ClientError as e:
            logger.error(f"Error saving relations to Neo4j: {e}", exc_info=True)
            raise

    def _save_relations_typed_batch(
        self,
        tx,
        relations: List[dict],
        cypher_rel_type: str,
    ) -> list:
        if not is_safe_interpolated_reltype(cypher_rel_type):
            cypher_rel_type = EXTRACTED_REL_FALLBACK
        query = f"""
        UNWIND $relations AS rel
        OPTIONAL MATCH (source:Entity {{name: rel.source_name}})
        OPTIONAL MATCH (target:Entity {{name: rel.target_name}})
        WITH rel, source, target
        WHERE source IS NOT NULL AND target IS NOT NULL AND id(source) <> id(target)
        MERGE (source)-[r:`{cypher_rel_type}` {{relation_id: rel.id}}]->(target)
        SET r.relation_type = rel.relation_type,
            r.confidence = rel.confidence,
            r.provenance_ref = rel.provenance_ref,
            r.ontology_property_uri = rel.ontology_property_uri,
            r.extraction_method = rel.extraction_method,
            r.curation_state = CASE
                WHEN coalesce(r.curation_state, '') IN ['Curated', 'Invalid']
                THEN r.curation_state
                ELSE coalesce(rel.curation_state, 'Extracted')
            END
        RETURN count(r) AS created
        """
        return list(tx.run(query, relations=relations))
    
    def close(self) -> None:
        """Cierra la conexión a Neo4j."""
        if self._driver:
            self._driver.close()
            self._driver = None

