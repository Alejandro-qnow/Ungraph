"""
Composition Root: Dependencies

Factory para crear y configurar todas las dependencias.
Este es el único lugar donde se crean implementaciones concretas.
"""

from typing import Any, Optional

from ungraph.application.use_cases.bulk_ingest_documents import BulkIngestDocumentsUseCase
from ungraph.application.use_cases.ingest_document import IngestDocumentUseCase
from ungraph.application.use_cases.ingest_tabular import IngestTabularUseCase
from ungraph.application.use_cases.knowledge_mining import KnowledgeMiningUseCase
from ungraph.core.configuration import (
    Settings,
    resolve_openai_model_for_inference_domain_questions,
    resolve_openai_model_for_inference_extraction,
    resolve_openai_model_for_inference_context,
)

# Domain - Interfaces
from ungraph.domain.services.inference_service import InferenceService
from ungraph.domain.services.ontology_resolver import OntologyResolver
from ungraph.domain.value_objects.ontology_profile import OntologyProfile
from ungraph.domain.services.duplicate_guard_service import DuplicateGuardService
from ungraph.domain.services.entity_graph_maintenance import EntityGraphMaintenanceService

# Infrastructure - Implementaciones concretas
from ungraph.infrastructure.repositories.neo4j_catalog_repository import Neo4jCatalogRepository
from ungraph.infrastructure.repositories.neo4j_chunk_repository import Neo4jChunkRepository
from ungraph.infrastructure.services.langchain_document_loader_service import LangChainDocumentLoaderService
from ungraph.infrastructure.services.simple_text_cleaning_service import SimpleTextCleaningService
from ungraph.infrastructure.services.langchain_chunking_service import LangChainChunkingService
from ungraph.infrastructure.services.huggingface_embedding_service import HuggingFaceEmbeddingService
from ungraph.infrastructure.services.neo4j_entity_maintenance_service import (
    Neo4jEntityGraphMaintenanceService,
)
from ungraph.infrastructure.services.neo4j_index_service import Neo4jIndexService
from ungraph.infrastructure.services.heuristic_context_optimization_service import (
    HeuristicContextOptimizationService,
)


def _default_llm_inference_context_bundle():
    """
    Implementaciones ligeras (sin API LLM) para enriquecer el prompt del extractor.
    """
    from ungraph.infrastructure.services.heuristic_document_context_service import (
        HeuristicDocumentContextService,
    )
    from ungraph.infrastructure.services.template_domain_question_generator import (
        TemplateDomainQuestionGenerator,
    )

    return HeuristicDocumentContextService(), TemplateDomainQuestionGenerator()


def _llm_inference_context_bundle(settings: Settings):
    """
    Bundle DocumentContextService + DomainQuestionService para el grafo de inferencia.

    Por defecto: heurística + plantillas (sin llamadas LLM extra). Con
    ``inference_enrich_context_with_llm`` y API key, se usan ``LlmDocumentContextService``
    y ``LlmDomainQuestionGenerator``. Si el modelo resuelto para contexto y para
    preguntas coincide, comparten un ``ChatOpenAI``; si no, hay dos instancias.
    """
    if not settings.inference_enrich_context_with_llm:
        return _default_llm_inference_context_bundle()
    try:
        from langchain_openai import ChatOpenAI
        from ungraph.infrastructure.services.heuristic_document_context_service import (
            HeuristicDocumentContextService,
        )
        from ungraph.infrastructure.services.llm_document_context_service import (
            LlmDocumentContextService,
        )
        from ungraph.infrastructure.services.llm_domain_question_generator import (
            LlmDomainQuestionGenerator,
        )
        from ungraph.infrastructure.services.template_domain_question_generator import (
            TemplateDomainQuestionGenerator,
        )
    except ImportError:
        return _default_llm_inference_context_bundle()

    ctx_model = resolve_openai_model_for_inference_context(settings)
    q_model = resolve_openai_model_for_inference_domain_questions(settings)
    kw = dict(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url or None,
        temperature=0,
    )
    heur = HeuristicDocumentContextService()
    tmpl = TemplateDomainQuestionGenerator()
    if ctx_model == q_model:
        llm = ChatOpenAI(model=ctx_model, **kw)
        return (
            LlmDocumentContextService(llm, fallback=heur),
            LlmDomainQuestionGenerator(llm, fallback=tmpl),
        )
    llm_ctx = ChatOpenAI(model=ctx_model, **kw)
    llm_q = ChatOpenAI(model=q_model, **kw)
    return (
        LlmDocumentContextService(llm_ctx, fallback=heur),
        LlmDomainQuestionGenerator(llm_q, fallback=tmpl),
    )


def _optional_spacy_lexical_for_llm(
    settings: Settings,
    *,
    language: str = "en",
) -> Any:
    """
    Carga ``SpacyInferenceService`` solo para NER léxico en modo LLM (hints al prompt).

    Si ``inference_inject_spacy_hints`` es false o spaCy/modelo no está disponible, retorna None.
    """
    if not settings.inference_inject_spacy_hints:
        return None
    model_name = "en_core_web_sm" if (language or "en").lower().startswith("en") else "es_core_news_sm"
    try:
        from ungraph.infrastructure.services.spacy_inference_service import (
            SpacyInferenceService,
        )

        return SpacyInferenceService(model_name=model_name)
    except (ImportError, OSError) as e:
        import logging

        logging.getLogger(__name__).warning(
            "Modo LLM sin hints spaCy (instala ungraph[infer] y el modelo %s): %s",
            model_name,
            e,
        )
        return None


def _chat_openai_for_llm_inference(settings: Settings):
    """``ChatOpenAI`` para extracción LLM (modelo según presupuesto / override)."""
    from langchain_openai import ChatOpenAI

    model = resolve_openai_model_for_inference_extraction(settings)
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model=model,
        base_url=settings.openai_base_url or None,
        temperature=0,
    )


def _ontology_sparql_query_from_settings(settings: Settings, *, nodes: bool) -> Optional[str]:
    from pathlib import Path

    if nodes:
        file_p = settings.ontology_sparql_query_nodes_file
        inline = settings.ontology_sparql_query_nodes
    else:
        file_p = settings.ontology_sparql_query_relations_file
        inline = settings.ontology_sparql_query_relations
    if file_p and str(file_p).strip():
        path = Path(str(file_p).strip())
        if path.is_file():
            return path.read_text(encoding="utf-8")
    if inline and str(inline).strip():
        return str(inline).strip()
    return None


def create_ontology_resolver(
    settings: Optional[Settings] = None,
) -> OntologyResolver:
    """
    ``PresetOntologyResolver`` por defecto; si hay endpoint + dos consultas SPARQL,
    se enruta ``ontology_sparql_profile_id`` a ``SparqlOntologyResolver``.
    """
    from ungraph.infrastructure.services.preset_ontology_resolver import (
        PresetOntologyResolver,
    )
    from ungraph.infrastructure.services.routing_ontology_resolver import (
        RoutingOntologyResolver,
    )
    from ungraph.infrastructure.services.sparql_ontology_resolver import (
        SparqlOntologyResolver,
    )

    if settings is None:
        settings = Settings()
    preset = PresetOntologyResolver()
    ep = (settings.ontology_sparql_endpoint or "").strip()
    nq = _ontology_sparql_query_from_settings(settings, nodes=True)
    rq = _ontology_sparql_query_from_settings(settings, nodes=False)
    if not ep or not nq or not rq:
        return preset
    pid = (settings.ontology_sparql_profile_id or "sparql").strip()
    sparql = SparqlOntologyResolver(
        ep,
        nodes_query=nq,
        relations_query=rq,
        profile_id=pid,
        timeout_seconds=settings.ontology_sparql_timeout_seconds,
        post_format=settings.ontology_sparql_post_format,
    )
    return RoutingOntologyResolver({pid: sparql}, default=preset)


def resolve_inference_ontology_profile(settings: Settings) -> OntologyProfile:
    """
    Perfil ontológico activo para inferencia LLM (presets o SPARQL según settings).
    """
    import logging

    from ungraph.infrastructure.services.preset_ontology_resolver import (
        PresetOntologyResolver,
    )

    logger = logging.getLogger(__name__)
    resolver = create_ontology_resolver(settings)
    pid = (settings.inference_ontology_profile_id or "general").strip()
    candidates = [pid, "general", "default"]
    seen: set[str] = set()
    for cand in candidates:
        key = cand.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            return resolver.resolve(cand)
        except ValueError:
            continue
        except RuntimeError as e:
            logger.warning(
                "Ontology profile %r failed to load (SPARQL/network?): %s",
                cand,
                e,
            )
            continue
    return PresetOntologyResolver().resolve("general")


def _inference_llm_allowed_schema(settings: Settings) -> tuple[list[str], list[str]]:
    """Tipos permitidos para LLMGraphTransformer según OntologyResolver + settings."""
    p = resolve_inference_ontology_profile(settings)
    return list(p.allowed_nodes), list(p.allowed_relationships)


def create_inference_service(
    settings: Optional[Settings] = None,
    language: str = "en",
) -> Optional[InferenceService]:
    """
    Factory: crea y configura el servicio de inferencia.
    
    Creates appropriate inference service based on configuration:
    - inference_mode="ner": SpacyInferenceService (NER-based, default)
    - inference_mode="llm": LLMInferenceService (LLM-based, experimental)
    - inference_mode="hybrid": NotImplementedError (planned for v0.2.0)
    
    Args:
        settings: Configuration settings. If None, loads from environment.
        language: Language code for spaCy models in ``ner`` mode and for optional LLM lexical hints
            (``en`` → ``en_core_web_sm``, otherwise ``es_core_news_sm``) when ``inference_inject_spacy_hints`` is true.
        
    Returns:
        InferenceService implementation or None if inference disabled
        
    Raises:
        ImportError: If required dependencies not installed
        NotImplementedError: If inference_mode="hybrid"
        ValueError: If inference_mode invalid
        
    Example:
        >>> settings = Settings(inference_mode="llm", openai_api_key="sk-...")
        >>> service = create_inference_service(settings)
        >>> type(service).__name__
        'LLMInferenceService'
    """
    if settings is None:
        settings = Settings()
    
    inference_mode = settings.inference_mode.lower()
    
    # NER mode (default, existing implementation)
    if inference_mode == "ner":
        from ungraph.infrastructure.services.spacy_inference_service import (
            SpacyInferenceService,
        )
        # Seleccionar modelo según idioma
        model_name = "en_core_web_sm" if language == "en" else "es_core_news_sm"
        
        try:
            return SpacyInferenceService(model_name=model_name)
        except ImportError as e:
            # Si spaCy no está instalado, retornar None
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
    
    # LLM mode (new, experimental)
    elif inference_mode == "llm":
        try:
            from ungraph.infrastructure.services.llm_inference_service import LLMInferenceService
        except ImportError as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Cannot load LLMInferenceService: {e}. "
                "Ensure langchain-experimental, langchain-community, and langchain-openai are installed."
            )
            return None

        if not getattr(settings, "openai_api_key", None):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "LLM inference requires an OpenAI API key. "
                "Set UNGRAPH_OPENAI_API_KEY or OPENAI_API_KEY (e.g. export OPENAI_API_KEY=sk-...)."
            )
            return None

        llm = _chat_openai_for_llm_inference(settings)

        allowed_nodes, allowed_relationships = _inference_llm_allowed_schema(settings)
        onto = resolve_inference_ontology_profile(settings)

        doc_ctx_svc, domain_q_svc = _llm_inference_context_bundle(settings)
        spacy_lex = _optional_spacy_lexical_for_llm(settings, language=language)
        return LLMInferenceService(
            llm=llm,
            allowed_nodes=allowed_nodes,
            allowed_relationships=allowed_relationships,
            strict_mode=True,
            document_context_service=doc_ctx_svc,
            domain_question_service=domain_q_svc,
            ontology_profile=onto,
            spacy_lexical_service=spacy_lex,
        )
    
    # Hybrid mode (planned for v0.2.0)
    elif inference_mode == "hybrid":
        raise NotImplementedError(
            "Hybrid inference mode (NER + LLM) is planned for v0.2.0. "
            "Use 'ner' or 'llm' mode for now."
        )
    
    # Invalid mode
    else:
        raise ValueError(
            f"Invalid inference_mode: '{inference_mode}'. "
            "Valid options: 'ner', 'llm', 'hybrid'"
        )


def create_llm_inference_openai(
    settings: Optional[Settings] = None,
    *,
    language: str = "en",
) -> Optional[InferenceService]:
    """
    Explicit factory: ``LLMInferenceService`` with ``ChatOpenAI``.

    Returns ``None`` if no API key is available (after UNGRAPH_* + OPENAI_* merge).
    Does not store secrets; reads them from ``Settings`` / environment.

    ``language`` selects the spaCy model for ``UNGRAPH_INFERENCE_INJECT_SPACY_HINTS`` (default true)
    when spaCy is installed; otherwise hints are skipped.
    """
    if settings is None:
        settings = Settings()
    if not settings.openai_api_key:
        return None
    try:
        from ungraph.infrastructure.services.llm_inference_service import LLMInferenceService
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning("create_llm_inference_openai: %s", e)
        return None
    llm = _chat_openai_for_llm_inference(settings)
    allowed_nodes, allowed_relationships = _inference_llm_allowed_schema(settings)
    onto = resolve_inference_ontology_profile(settings)
    doc_ctx_svc, domain_q_svc = _llm_inference_context_bundle(settings)
    spacy_lex = _optional_spacy_lexical_for_llm(settings, language=language)
    return LLMInferenceService(
        llm=llm,
        allowed_nodes=allowed_nodes,
        allowed_relationships=allowed_relationships,
        strict_mode=True,
        document_context_service=doc_ctx_svc,
        domain_question_service=domain_q_svc,
        ontology_profile=onto,
        spacy_lexical_service=spacy_lex,
    )


def create_ingest_document_use_case(
    settings: Optional[Settings] = None,
    database: str = "neo4j",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    inference_language: str = "en"
) -> IngestDocumentUseCase:
    """
    Factory: crea y configura el caso de uso IngestDocumentUseCase.
    
    Este método:
    - Crea todas las implementaciones concretas
    - Configura las dependencias
    - Retorna el caso de uso listo para usar
    
    Args:
        settings: Configuration settings. If None, loads from environment.
        database: Nombre de la base de datos Neo4j (default: "neo4j")
        embedding_model: Modelo de embeddings a usar (default: all-MiniLM-L6-v2)
        inference_language: Idioma para inferencia ('en' para inglés, 'es' para español) (default: "en")
    
    Note:
        Inference mode is determined by settings.inference_mode:
        - "ner": SpaCy NER-based (default)
        - "llm": LLM-based (experimental; OpenAI via UNGRAPH_OPENAI_* / OPENAI_*)
        - "hybrid": Planned for v0.2.0
    
    Returns:
        IngestDocumentUseCase configurado y listo para usar
    
    Note:
        Si inference service no puede crearse (dependencias faltantes),
        el pipeline funcionará sin fase Inference (solo ET).
    """
    if settings is None:
        settings = Settings()
    
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
    
    # Crear servicio de inferencia basado en settings
    inference_service = create_inference_service(
        settings=settings,
        language=inference_language
    )

    context_optimization_service = HeuristicContextOptimizationService()

    catalog_repository = Neo4jCatalogRepository(database=database)

    # Crear caso de uso con dependencias inyectadas
    return IngestDocumentUseCase(
        document_loader_service=document_loader_service,
        chunking_service=chunking_service,
        embedding_service=embedding_service,
        index_service=index_service,
        chunk_repository=chunk_repository,
        inference_service=inference_service,
        context_optimization_service=context_optimization_service,
        catalog_repository=catalog_repository,
    )


def create_bulk_ingest_documents_use_case(
    settings: Optional[Settings] = None,
    database: str = "neo4j",
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    inference_language: str = "en",
) -> BulkIngestDocumentsUseCase:
    """Factory: ingest masivo con DuplicateGuard + catálogo Neo4j."""
    if settings is None:
        settings = Settings()
    ingest = create_ingest_document_use_case(
        settings=settings,
        database=database,
        embedding_model=embedding_model,
        inference_language=inference_language,
    )
    catalog = ingest.catalog_repository
    if catalog is None:
        catalog = Neo4jCatalogRepository(database=database)
    guard = DuplicateGuardService(
        catalog,
        semantic_similarity_threshold=settings.duplicate_semantic_similarity_threshold,
        abstract_min_chars=settings.duplicate_abstract_min_chars,
        embedding_service=ingest.embedding_service,
    )
    return BulkIngestDocumentsUseCase(
        ingest_document_use_case=ingest,
        duplicate_guard=guard,
        catalog_repository=catalog,
        settings=settings,
    )


def create_ingest_tabular_use_case(
    settings: Optional[Settings] = None,
    database: str = "neo4j",
    *,
    use_llm_disambiguation: bool = True,
) -> IngestTabularUseCase:
    """Factory: caso de uso de ingesta tabular (Schema-Guided Ingestion).

    Composition root del modo estructurado. La desambiguación LLM se activa solo si
    ``use_llm_disambiguation`` y hay API key; de lo contrario, inferencia heurística pura.

    Args:
        settings: Configuración; si None, se carga del entorno.
        database: Base de datos Neo4j.
        use_llm_disambiguation: Si True e ``openai_api_key`` disponible, usa el híbrido.

    Returns:
        IngestTabularUseCase configurado.
    """
    if settings is None:
        settings = Settings()

    from ungraph.infrastructure.repositories.neo4j_tabular_repository import (
        Neo4jTabularRepository,
    )
    from ungraph.infrastructure.services.heuristic_schema_inference_service import (
        HeuristicSchemaInferenceService,
    )
    from ungraph.infrastructure.services.pandas_tabular_loader_service import (
        PandasTabularLoaderService,
    )

    loader = PandasTabularLoaderService()
    heuristic = HeuristicSchemaInferenceService()

    schema_inference: Any = heuristic
    if use_llm_disambiguation and getattr(settings, "openai_api_key", None):
        try:
            from ungraph.infrastructure.services.llm_schema_inference_service import (
                LlmSchemaInferenceService,
            )

            llm = _chat_openai_for_llm_inference(settings)
            schema_inference = LlmSchemaInferenceService(heuristic=heuristic, llm=llm)
        except ImportError as e:
            import logging

            logging.getLogger(__name__).warning(
                "LLM de desambiguación no disponible (%s); se usa heurística pura.", e
            )

    tabular_repository = Neo4jTabularRepository(database=database)

    return IngestTabularUseCase(
        tabular_loader_service=loader,
        schema_inference_service=schema_inference,
        tabular_repository=tabular_repository,
    )


def create_knowledge_mining_use_case(
    settings: Optional[Settings] = None,
    database: str = "neo4j",
    inference_language: str = "en",
) -> KnowledgeMiningUseCase:
    """
    Re-inferencia sobre :Chunk sin :Fact derivados (CLI ``infer --kmining``).

    Raises:
        RuntimeError: si no hay ``InferenceService`` disponible (dependencias / modo).
    """
    if settings is None:
        settings = Settings()
    inference = create_inference_service(settings, language=inference_language)
    if inference is None:
        raise RuntimeError(
            "Inference service is not available. Check UNGRAPH_INFERENCE_MODE and "
            "optional dependencies (e.g. pip install 'ungraph[infer]', spaCy model, or "
            "OPENAI_API_KEY / UNGRAPH_OPENAI_API_KEY for LLM mode)."
        )
    chunk_repository = Neo4jChunkRepository(database=database)
    index_service = Neo4jIndexService(database=database)
    return KnowledgeMiningUseCase(
        chunk_repository=chunk_repository,
        inference_service=inference,
        index_service=index_service,
    )


def create_entity_graph_maintenance_service(
    database: str = "neo4j",
) -> EntityGraphMaintenanceService:
    """Fusión de nodos :Entity duplicados (``infer --consolidate`` / ``--resolve``)."""
    return Neo4jEntityGraphMaintenanceService(database=database)

