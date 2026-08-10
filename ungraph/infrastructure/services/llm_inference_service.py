"""
LLM-based Inference Service

Implements InferenceService interface using LangChain's LLMGraphTransformer
for entity and relationship extraction from text chunks.

This implementation uses a Language Model (LLM) to extract structured knowledge
from unstructured text, producing entities, relationships, and facts suitable
for knowledge graph construction.

Architecture:
    - LLMInferenceService: Main service implementing InferenceService interface
    - LangGraph StateGraph (``build_llm_extraction_graph``): spacy_hints → context → extract
    - LangChainAdapter: conversión tipos LangChain ↔ dominio

Dependencies:
    - langgraph: orquestación (StateGraph)
    - langchain_experimental.graph_transformers.LLMGraphTransformer (vía el grafo)
    - langchain_core.documents.Document
    - langchain_community.graphs.graph_document.GraphDocument

Usage:
    from langchain_openai import ChatOpenAI
    from src.infrastructure.services.llm_inference_service import LLMInferenceService
    
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    service = LLMInferenceService(
        llm=llm,
        allowed_nodes=["Person", "Organization", "Location"],
        allowed_relationships=["WORKS_FOR", "LOCATED_IN"]
    )
    
    entities = service.extract_entities(chunk)
    relations = service.extract_relations(chunk, entities)
    facts = service.infer_facts(chunk)

Status: Experimental (v0.1.0)

Note: This implementation provides basic LLM-based extraction. Advanced features
like dynamic example selection, confidence scoring, and Opik evaluation are
planned for v0.2.0.
"""

from typing import Dict, List, Optional, Any
from uuid import uuid4

from langchain_core.documents import Document as LangChainDocument
from langchain_core.language_models import BaseLanguageModel
from langchain_community.graphs.graph_document import (
    GraphDocument,
    Node as LangChainNode,
    Relationship as LangChainRelationship,
)

from ungraph.domain.entities.chunk import Chunk
from ungraph.domain.entities.entity import Entity
from ungraph.domain.entities.fact import Fact
from ungraph.domain.entities.relation import Relation
from ungraph.domain.services.document_context_service import DocumentContextService
from ungraph.domain.services.domain_question_service import DomainQuestionService
from ungraph.domain.services.inference_service import InferenceService
from ungraph.domain.value_objects.ontology_profile import OntologyProfile


class LangChainAdapter:
    """
    Adapter for converting between LangChain and Ungraph domain entities.
    
    This adapter handles bidirectional conversion:
    - Ungraph Chunk → LangChain Document
    - LangChain GraphDocument → Ungraph Entity/Relation/Fact
    
    The adapter ensures type safety and data integrity during conversion,
    handling edge cases like missing properties or invalid references.
    
    Design Pattern: Adapter Pattern (structural)
    Responsibility: Type conversion only, no business logic
    """
    
    @staticmethod
    def chunk_to_langchain_document(chunk: Chunk) -> LangChainDocument:
        """
        Convert Ungraph Chunk to LangChain Document.
        
        Args:
            chunk: Source chunk entity from domain layer
            
        Returns:
            LangChain Document with content and metadata
            
        Example:
            >>> chunk = Chunk(
            ...     id="chunk_1",
            ...     page_content="Apple Inc. is located in Cupertino.",
            ...     metadata={"filename": "doc.txt"}
            ... )
            >>> doc = LangChainAdapter.chunk_to_langchain_document(chunk)
            >>> doc.page_content
            'Apple Inc. is located in Cupertino.'
        """
        return LangChainDocument(
            page_content=chunk.page_content,
            metadata={
                **chunk.metadata,
                "chunk_id": chunk.id,
                "chunk_id_consecutive": chunk.chunk_id_consecutive,
            },
        )
    
    @staticmethod
    def langchain_nodes_to_entities(
        nodes: List[LangChainNode],
        chunk_id: str,
    ) -> List[Entity]:
        """
        Convert LangChain Nodes to Ungraph Entities.
        
        Args:
            nodes: List of LangChain Node objects
            chunk_id: Source chunk ID for provenance tracking
            
        Returns:
            List of Ungraph Entity objects
            
        Note:
            Each Node becomes an Entity with:
            - name: From node.id (human-readable identifier)
            - type: From node.type (entity category), or "UNKNOWN" if empty/None
            - mentions: Single-element list with source chunk_id
        """
        entities = []
        for node in nodes:
            # Handle empty or None type
            entity_type = node.type if node.type and node.type.strip() else "UNKNOWN"
            entity = Entity(
                id=f"entity_{uuid4().hex[:8]}",
                name=node.id,
                type=entity_type,
                mentions=[chunk_id],
                extraction_method="llm",
            )
            entities.append(entity)
        return entities
    
    @staticmethod
    def langchain_relationships_to_relations(
        relationships: List[LangChainRelationship],
        entities: List[Entity],
        chunk_id: str,
    ) -> List[Relation]:
        """
        Convert LangChain Relationships to Ungraph Relations.
        
        Args:
            relationships: List of LangChain Relationship objects
            entities: Corresponding entities for ID resolution
            chunk_id: Source chunk ID for provenance tracking
            
        Returns:
            List of Ungraph Relation objects
            
        Note:
            Entity resolution: Maps node.id (name) to Entity.id via lookup.
            If source or target entity not found, relation is skipped.
            Default confidence: 0.8 (reasonable baseline for LLM extraction)
        """
        # Create lookup: entity_name → entity_id
        entity_lookup = {entity.name: entity.id for entity in entities}
        
        relations = []
        for rel in relationships:
            source_id = entity_lookup.get(rel.source.id)
            target_id = entity_lookup.get(rel.target.id)
            
            # Skip if entities not found (data integrity)
            if not source_id or not target_id:
                continue
            
            relation = Relation(
                id=f"relation_{uuid4().hex[:8]}",
                source_entity_id=source_id,
                target_entity_id=target_id,
                relation_type=rel.type,
                confidence=0.8,  # Default confidence for LLM extraction
                provenance_ref=chunk_id,
                extraction_method="llm",
                source_entity_name=rel.source.id,
                target_entity_name=rel.target.id,
            )
            relations.append(relation)
        return relations
    
    @staticmethod
    def entities_to_facts(entities: List[Entity], chunk_id: str) -> List[Fact]:
        """
        Convert entities to MENTIONS facts for knowledge graph.
        
        Args:
            entities: List of extracted entities
            chunk_id: Source chunk ID
            
        Returns:
            List of Fact objects representing chunk-entity relationships
            
        Note:
            Each entity generates one MENTIONS fact:
            - subject: chunk_id
            - predicate: "MENTIONS"
            - object: entity.name
            - confidence: 1.0 (entity extraction confirmed)
        """
        facts = []
        for entity in entities:
            fact = Fact(
                id=f"fact_{uuid4().hex[:8]}",
                subject=chunk_id,
                predicate="MENTIONS",
                object=entity.name,
                confidence=1.0,
                provenance_ref=chunk_id,
                object_entity_type=entity.type,
                object_ontology_class_uri=entity.ontology_class_uri,
            )
            facts.append(fact)
        return facts


class LLMInferenceService(InferenceService):
    """
    LLM-based implementation of InferenceService.
    
    Uses LangChain's LLMGraphTransformer to extract entities, relationships,
    and facts from text chunks using a Language Model (LLM).
    
    This implementation runs a LangGraph pipeline (optional spaCy hints, context, extract)
    backed by LLMGraphTransformer, integrating with Ungraph via LangChainAdapter.
    
    Attributes:
        _extraction_graph: Grafo LangGraph compilado (spacy_hints → context → extract)
        adapter: LangChainAdapter for type conversion
        
    Configuration:
        - allowed_nodes: List of permitted entity types (e.g., ["Person", "Company"])
        - allowed_relationships: List of permitted relation types (e.g., ["WORKS_FOR"])
        - prompt: Optional custom ChatPromptTemplate (defaults to LLMGraphTransformer's)
        - strict_mode: Enable filtering to allowed_nodes/allowed_relationships (default: True)
        
    Performance Characteristics:
        - Latency: ~2-5s per chunk (LLM-dependent)
        - Accuracy: Higher than NER for complex domains (domain-dependent)
        - Cost: LLM API calls required
        
    Example:
        >>> from langchain_openai import ChatOpenAI
        >>> llm = ChatOpenAI(model="gpt-4", temperature=0)
        >>> service = LLMInferenceService(
        ...     llm=llm,
        ...     allowed_nodes=["Person", "Organization"],
        ...     allowed_relationships=["WORKS_FOR"]
        ... )
        >>> chunk = Chunk(id="1", page_content="Alice works at Google.", metadata={})
        >>> entities = service.extract_entities(chunk)
        >>> len(entities)
        2
    """
    
    def __init__(
        self,
        llm: BaseLanguageModel,
        allowed_nodes: Optional[List[str]] = None,
        allowed_relationships: Optional[List[str]] = None,
        prompt: Optional[Any] = None,
        strict_mode: bool = True,
        document_context_service: Optional[DocumentContextService] = None,
        domain_question_service: Optional[DomainQuestionService] = None,
        context_addon_max_chars: int = 6000,
        ontology_profile: Optional[OntologyProfile] = None,
        spacy_lexical_service: Any = None,
    ) -> None:
        """
        Initialize LLMInferenceService with LLM and schema configuration.
        
        Args:
            llm: LangChain-compatible chat model (expected: ChatOpenAI for the default factory).
            allowed_nodes: Permitted entity types. If None, all types allowed.
            allowed_relationships: Permitted relation types. If None, all types allowed.
            prompt: Custom ChatPromptTemplate for extraction. If None, uses default.
            strict_mode: If True, filter results to allowed_nodes/allowed_relationships.
                        If False, permit all extracted types (useful for exploration).
            document_context_service: Si viene junto con domain_question_service, el grafo
                enriquece el texto antes de ``LLMGraphTransformer``.
            domain_question_service: Par del anterior; ambos o ninguno tienen efecto.
            context_addon_max_chars: Tope para el snippet inyectado vía
                ``build_graph_transformer_context_addon``.
            ontology_profile: Perfil usado para ``ontology_class_uri`` / ``ontology_property_uri``
                cuando el mapa SPARQL o preset los define.
            spacy_lexical_service: Opcional; si expone ``extract_entities(chunk)``, el grafo antepone
                candidatos NER (p. ej. ``SpacyInferenceService``) al prompt del extractor.
                        
        Raises:
            ValueError: If llm is None or not a BaseLanguageModel
            
        Note:
            Default allowed_nodes and allowed_relationships are empty lists,
            which means LLMGraphTransformer will extract all types found.
            Set strict_mode=True to enforce filtering.
        """
        if llm is None:
            raise ValueError("llm parameter is required and cannot be None")
        
        # Use empty lists as defaults (allow all types)
        self.allowed_nodes = allowed_nodes or []
        self.allowed_relationships = allowed_relationships or []

        self._ontology_profile = ontology_profile

        from ungraph.infrastructure.agents.inference_state_graph import (
            build_llm_extraction_graph,
        )

        self._extraction_graph = build_llm_extraction_graph(
            llm,
            allowed_nodes=self.allowed_nodes,
            allowed_relationships=self.allowed_relationships,
            prompt=prompt,
            strict_mode=strict_mode,
            document_context_service=document_context_service,
            domain_question_service=domain_question_service,
            context_addon_max_chars=context_addon_max_chars,
            spacy_lexical_service=spacy_lexical_service,
        )

        # Initialize adapter
        self.adapter = LangChainAdapter()

        # Una sola llamada a LLMGraphTransformer por chunk_id (reutiliza GraphDocument)
        self._graph_cache: Dict[str, GraphDocument] = {}
        self._max_graph_cache_entries: int = 128

    def _cache_put_graph(self, chunk_id: str, graph_document: GraphDocument) -> None:
        if (
            len(self._graph_cache) >= self._max_graph_cache_entries
            and chunk_id not in self._graph_cache
        ):
            self._graph_cache.pop(next(iter(self._graph_cache)))
        self._graph_cache[chunk_id] = graph_document

    def _get_graph_document(self, chunk: Chunk) -> GraphDocument:
        """Una invocación a process_response por chunk (salvo caché)."""
        cached = self._graph_cache.get(chunk.id)
        if cached is not None:
            return cached
        out = self._extraction_graph.invoke({"chunk": chunk})
        graph_document = out.get("graph_document")
        if graph_document is None:
            raise RuntimeError("LangGraph extraction did not return graph_document")
        self._cache_put_graph(chunk.id, graph_document)
        return graph_document

    def _enrich_entities_ontology(self, entities: List[Entity]) -> None:
        prof = self._ontology_profile
        if not prof:
            return
        for e in entities:
            uri = prof.resolve_class_uri(e.type)
            if uri:
                e.ontology_class_uri = uri

    def _enrich_relations_ontology(self, relations: List[Relation]) -> None:
        prof = self._ontology_profile
        if not prof:
            return
        for r in relations:
            uri = prof.resolve_property_uri(r.relation_type)
            if uri:
                r.ontology_property_uri = uri

    def extract_entities(self, chunk: Chunk) -> List[Entity]:
        """
        Extract entities from chunk using LLM.
        
        Args:
            chunk: Input chunk containing text to analyze
            
        Returns:
            List of Entity objects extracted from chunk
            
        Process:
            1. Ejecutar grafo LangGraph (extract con LLMGraphTransformer)
            2. Extraer nodos del GraphDocument y convertir a Entity
            
        Example:
            >>> chunk = Chunk(
            ...     id="chunk_1",
            ...     page_content="Apple Inc. released iPhone 15.",
            ...     metadata={}
            ... )
            >>> entities = service.extract_entities(chunk)
            >>> [e.name for e in entities]
            ['Apple Inc.', 'iPhone 15']
        """
        graph_document = self._get_graph_document(chunk)

        entities = self.adapter.langchain_nodes_to_entities(
            nodes=graph_document.nodes,
            chunk_id=chunk.id,
        )
        self._enrich_entities_ontology(entities)
        return entities
    
    def extract_relations(
        self,
        chunk: Chunk,
        entities: List[Entity],
    ) -> List[Relation]:
        """
        Extract relations between entities from chunk using LLM.
        
        Args:
            chunk: Input chunk containing text to analyze
            entities: Previously extracted entities from same chunk
            
        Returns:
            List of Relation objects connecting entities
            
        Note:
            Reutiliza el mismo GraphDocument que ``extract_entities`` para este
            ``chunk.id`` (una sola llamada LLM por chunk cuando se llama a ambos).
            
        Process:
            1. Obtener GraphDocument (caché o grafo LangGraph)
            2. Convertir relationships a Relation con resolución de IDs
            
        Example:
            >>> relations = service.extract_relations(chunk, entities)
            >>> rel = relations[0]
            >>> rel.relation_type
            'PRODUCED_BY'
        """
        graph_document = self._get_graph_document(chunk)

        relations = self.adapter.langchain_relationships_to_relations(
            relationships=graph_document.relationships,
            entities=entities,
            chunk_id=chunk.id,
        )
        self._enrich_relations_ontology(relations)
        return relations
    
    def infer_facts(self, chunk: Chunk, entities: Optional[List[Entity]] = None) -> List[Fact]:
        """
        Infer facts from chunk (entity mentions).
        
        Args:
            chunk: Input chunk containing text to analyze
            
        Returns:
            List of Fact objects representing chunk-entity relationships
            
        Note:
            This implementation generates MENTIONS facts from extracted entities.
            Each fact represents: chunk MENTIONS entity_name
            
        Process:
            1. Reutilizar GraphDocument en caché si existe (misma ejecución del grafo que extract_entities)
            2. Generar MENTIONS fact por entidad
            
        Example:
            >>> facts = service.infer_facts(chunk)
            >>> fact = facts[0]
            >>> fact.predicate
            'MENTIONS'
        """
        if entities is not None:
            self._enrich_entities_ontology(entities)
            return self.adapter.entities_to_facts(
                entities=entities,
                chunk_id=chunk.id,
            )
        graph_document = self._get_graph_document(chunk)
        built = self.adapter.langchain_nodes_to_entities(
            nodes=graph_document.nodes,
            chunk_id=chunk.id,
        )
        self._enrich_entities_ontology(built)

        return self.adapter.entities_to_facts(
            entities=built,
            chunk_id=chunk.id,
        )
