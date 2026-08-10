"""
Configuration management using Pydantic Settings.

This module provides global configuration management for Ungraph.
Supports both environment variables and programmatic configuration.

Variables are automatically loaded from:
1. Environment variables (with UNGRAPH_ prefix)
2. .env file (via python-dotenv)
3. Programmatic configuration (via configure() function)

Example .env file:
    UNGRAPH_OPENAI_API_KEY=sk-...
    OPENAI_API_KEY=sk-...   # alternativa si no defines UNGRAPH_OPENAI_API_KEY
    UNGRAPH_OPENAI_MODEL=gpt-4o-mini
    UNGRAPH_OPENAI_BASE_URL=https://api.openai.com/v1
    OPENAI_MODEL=...
    OPENAI_BASE_URL=...
    UNGRAPH_INFERENCE_MODE=llm
    UNGRAPH_INFERENCE_MODEL_BUDGET=balanced   # economy | balanced | quality
    # UNGRAPH_INFERENCE_ENRICH_CONTEXT_WITH_LLM=true
    # UNGRAPH_INFERENCE_INJECT_SPACY_HINTS=true
    # Modelo auxiliar: contexto de documento vs preguntas (opcional; si no, mismas reglas)
    # UNGRAPH_OPENAI_MODEL_INFERENCE_CONTEXT=gpt-4o-mini
    # UNGRAPH_OPENAI_MODEL_INFERENCE_DOMAIN_QUESTIONS=gpt-4o
    # OPENAI_MODEL_INFERENCE_CONTEXT=gpt-4o-mini
    # OPENAI_MODEL_INFERENCE_DOMAIN_QUESTIONS=gpt-4o
    # Override del modelo solo para extracción (LLMGraphTransformer); opcional
    # UNGRAPH_OPENAI_MODEL_INFERENCE_EXTRACTION=gpt-4o
    # OPENAI_MODEL_INFERENCE_EXTRACTION=gpt-4o
    # UNGRAPH_INFERENCE_ONTOLOGY_PROFILE_ID=general
    # UNGRAPH_ONTOLOGY_SPARQL_ENDPOINT=https://dbpedia.org/sparql
    # UNGRAPH_ONTOLOGY_SPARQL_PROFILE_ID=sparql
    # UNGRAPH_ONTOLOGY_SPARQL_POST_FORMAT=content
    # UNGRAPH_ONTOLOGY_SPARQL_QUERY_NODES_FILE=queries/ontology_nodes.rq
    # UNGRAPH_ONTOLOGY_SPARQL_QUERY_RELATIONS_FILE=queries/ontology_rels.rq
    UNGRAPH_NEO4J_URI=bolt://localhost:7687
    UNGRAPH_NEO4J_USER=neo4j
    UNGRAPH_NEO4J_PASSWORD=password

    # Ollama (optional; reserved for future local-LLM wiring — not used by inference_mode=llm today)
    # UNGRAPH_OLLAMA_MODEL=llama3.2:3b
    # UNGRAPH_OLLAMA_BASE_URL=http://127.0.0.1:11434

Example programmatic configuration:
    from .configuration import configure
    
    configure(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        neo4j_database="neo4j"
    )
"""

from dotenv import load_dotenv, find_dotenv
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any, Literal
import os
from pathlib import Path


# Load environment variables from .env file(s)
load_dotenv(find_dotenv())
# .env junto al paquete ungraph/ (útil si el CWD es la raíz del repo y el archivo vive en ungraph/.env)
_pkg_dotenv = Path(__file__).resolve().parent.parent / ".env"
if _pkg_dotenv.is_file():
    load_dotenv(_pkg_dotenv, override=False)


def reload_dotenv_files(*, package_overrides: bool = False) -> None:
    """
    Vuelve a leer `.env` (directorio de trabajo y, si existe, `ungraph/.env`).
    Con ``package_overrides=False`` (por defecto), las claves ya definidas por el
    primer archivo no se sobreescriben por el segundo.
    """
    load_dotenv(find_dotenv(), override=True)
    if _pkg_dotenv.is_file():
        load_dotenv(_pkg_dotenv, override=package_overrides)
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Preferencia: variables con prefijo UNGRAPH_. Además se admiten alias sin prefijo
    para OpenAI (OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL) cuando no hay override UNGRAPH_*.
    
    Can be overridden programmatically using configure() function.
    """
    model_config = SettingsConfigDict(
        env_prefix='UNGRAPH_',
        case_sensitive=False,  # Allow case-insensitive env vars
        env_file='.env',
        env_file_encoding='utf-8',
    )
    
    # Ollama Configuration
    ollama_model: Optional[str] = Field(
        default=None,
        description="Reserved for future local LLM wiring; inference_mode=llm uses OpenAI only today.",
    )
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Base URL for Ollama API"
    )
    ollama_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for Ollama model (0.0-2.0)"
    )
    ollama_num_gpu: int = Field(
        default=1,
        ge=0,
        description="Number of GPUs to use"
    )
    ollama_num_thread: int = Field(
        default=8,
        ge=1,
        description="Number of threads to use"
    )
    
    # Neo4j Configuration
    neo4j_uri: Optional[str] = Field(
        default=None,
        description="Neo4j connection URI (e.g., 'bolt://localhost:7687')"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: Optional[str] = Field(
        default=None,
        description="Neo4j password"
    )
    neo4j_database: str = Field(
        default="neo4j",
        description="Neo4j database name"
    )

    ingest_max_workers: int = Field(
        default=4,
        ge=1,
        le=64,
        description="Max parallel workers for BulkIngestDocumentsUseCase"
    )
    duplicate_semantic_similarity_threshold: float = Field(
        default=0.995,
        ge=0.0,
        le=1.0,
        description="DuplicateGuard abstract cosine similarity skip threshold",
    )
    duplicate_abstract_min_chars: int = Field(
        default=80,
        ge=16,
        description="Minimum abstract length for DuplicateGuard semantic check",
    )
    
    # Storage Provider Configuration
    storage_provider: str = Field(
        default="neo4j",
        description="Storage provider (currently only 'neo4j' supported)"
    )
    
    # Embedding Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Default embedding model"
    )

    # Inference Configuration
    inference_mode: str = Field(
        default="ner",
        description=(
            "Inference mode: 'ner' (spaCy NER), 'pattern' (symbolic lexical), "
            "'llm' (OpenAI), or 'hybrid' (planned)"
        )
    )
    inference_model_budget: Literal["economy", "balanced", "quality"] = Field(
        default="balanced",
        description="Cost/quality policy for multi-step inference (document context, domain questions, extraction)",
    )
    inference_enrich_context_with_llm: bool = Field(
        default=False,
        description=(
            "When true and inference_mode=llm, document context + domain questions use "
            "ChatOpenAI helpers (`resolve_openai_model_for_inference_context` / "
            "`resolve_openai_model_for_inference_domain_questions`); "
            "otherwise heuristics + templates (no extra LLM calls)."
        ),
    )
    inference_inject_spacy_hints: bool = Field(
        default=True,
        description=(
            "When true and inference_mode=llm, run spaCy NER on each chunk (per ingest "
            "`inference_language`) and prepend lexical hints to the LLM extraction input. "
            "Requires spaCy and the matching model; if unavailable, extraction continues without hints."
        ),
    )
    inference_ontology_profile_id: str = Field(
        default="general",
        description=(
            "Ontology profile for LLM ``allowed_nodes`` / ``allowed_relationships``: "
            "preset ids (general, minimal, default) or ``ontology_sparql_profile_id`` when SPARQL is configured."
        ),
    )
    ontology_sparql_endpoint: Optional[str] = Field(
        default=None,
        description="SPARQL 1.1 HTTP endpoint; with nodes + relations queries enables remote profile loading.",
    )
    ontology_sparql_timeout_seconds: float = Field(
        default=60.0,
        ge=5.0,
        le=300.0,
        description="HTTP timeout for ontology SPARQL requests (seconds).",
    )
    ontology_sparql_profile_id: str = Field(
        default="sparql",
        description="profile_id for the resolver backed by SPARQL (match ``inference_ontology_profile_id`` to use it).",
    )
    ontology_sparql_post_format: Literal["content", "form"] = Field(
        default="content",
        description="POST encoding: application/sparql-query (content) vs urlencoded query= (form).",
    )
    ontology_sparql_query_nodes_file: Optional[str] = Field(
        default=None,
        description="Filesystem path to SPARQL file: SELECT with ?label and optional ?uri (classes).",
    )
    ontology_sparql_query_relations_file: Optional[str] = Field(
        default=None,
        description="Filesystem path to SPARQL: ?label and optional ?uri (properties / edge types).",
    )
    ontology_sparql_query_nodes: Optional[str] = Field(
        default=None,
        description="Inline nodes query if ``ontology_sparql_query_nodes_file`` is not set.",
    )
    ontology_sparql_query_relations: Optional[str] = Field(
        default=None,
        description="Inline relations query if ``ontology_sparql_query_relations_file`` is not set.",
    )
    ollama_model_document_context: Optional[str] = Field(
        default=None,
        description="Reserved for per-step local LLM (not wired in create_inference_service yet).",
    )
    ollama_model_domain_questions: Optional[str] = Field(
        default=None,
        description="Reserved for per-step local LLM (not wired yet).",
    )
    ollama_model_extraction: Optional[str] = Field(
        default=None,
        description="Reserved for per-step local LLM (not wired yet).",
    )

    # OpenAI / BYO LLM (optional; never persisted — read from env at runtime)
    openai_api_key: Optional[str] = Field(
        default=None,
        description="API key for ChatOpenAI when inference_mode=llm (UNGRAPH_OPENAI_API_KEY or OPENAI_API_KEY)",
    )
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="Model name for OpenAI-compatible chat completion",
    )
    openai_base_url: Optional[str] = Field(
        default=None,
        description="Optional base URL (OpenAI, Azure OpenAI, or compatible proxy)",
    )
    openai_model_inference_context: Optional[str] = Field(
        default=None,
        description=(
            "Optional ChatOpenAI model for LLM-backed document context (summary + hints); "
            "if unset, `resolve_openai_model_for_inference_context` applies."
        ),
    )
    openai_model_inference_domain_questions: Optional[str] = Field(
        default=None,
        description=(
            "Optional ChatOpenAI model for LLM domain question generation; "
            "if unset, uses the same resolved name as context (single shared client)."
        ),
    )
    openai_model_inference_extraction: Optional[str] = Field(
        default=None,
        description=(
            "Optional ChatOpenAI model name for LLM extraction only; "
            "if unset, `resolve_openai_model_for_inference_extraction` uses "
            "`inference_model_budget` and `openai_model`."
        ),
    )

    @model_validator(mode="after")
    def _merge_legacy_neo4j_env(self) -> "Settings":
        """
        Compatibilidad con variables sin prefijo UNGRAPH_ (NEO4J_URI, NEO4J_PASSWORD, …)
        tal como en CI, docker-compose y muchos .env existentes.
        """
        uri = self.neo4j_uri or os.environ.get("NEO4J_URI")
        pwd = self.neo4j_password or os.environ.get("NEO4J_PASSWORD")
        user = self.neo4j_user
        if not os.environ.get("UNGRAPH_NEO4J_USER") and os.environ.get("NEO4J_USER"):
            user = os.environ["NEO4J_USER"]
        db = self.neo4j_database
        if not os.environ.get("UNGRAPH_NEO4J_DATABASE"):
            db = (
                os.environ.get("NEO4J_DB")
                or os.environ.get("NEO4J_DATABASE")
                or db
            )
        object.__setattr__(self, "neo4j_uri", uri)
        object.__setattr__(self, "neo4j_password", pwd)
        object.__setattr__(self, "neo4j_user", user)
        object.__setattr__(self, "neo4j_database", db)
        return self

    @model_validator(mode="after")
    def _merge_openai_env_aliases(self) -> "Settings":
        """
        Compatibilidad con nombres estándar del ecosistema (OPENAI_API_KEY, etc.).
        Prefijo UNGRAPH_* cargado por Pydantic tiene prioridad; estos alias solo rellenan huecos.
        """
        raw_key = self.openai_api_key
        if raw_key is not None and not str(raw_key).strip():
            raw_key = None
        key = raw_key or os.environ.get("OPENAI_API_KEY")

        base = self.openai_base_url
        if base is not None and not str(base).strip():
            base = None
        if not base and not os.environ.get("UNGRAPH_OPENAI_BASE_URL"):
            env_b = os.environ.get("OPENAI_BASE_URL")
            if env_b and str(env_b).strip():
                base = str(env_b).strip()

        model = self.openai_model
        if not os.environ.get("UNGRAPH_OPENAI_MODEL"):
            env_m = os.environ.get("OPENAI_MODEL")
            if env_m and str(env_m).strip():
                model = str(env_m).strip()

        object.__setattr__(self, "openai_api_key", key if key else None)
        object.__setattr__(self, "openai_base_url", base)
        object.__setattr__(self, "openai_model", model)

        ext_raw = self.openai_model_inference_extraction
        if ext_raw is not None and not str(ext_raw).strip():
            ext_raw = None
        ext = ext_raw
        if not ext and not os.environ.get("UNGRAPH_OPENAI_MODEL_INFERENCE_EXTRACTION"):
            env_e = os.environ.get("OPENAI_MODEL_INFERENCE_EXTRACTION")
            if env_e and str(env_e).strip():
                ext = str(env_e).strip()
        object.__setattr__(self, "openai_model_inference_extraction", ext)

        ctx_raw = self.openai_model_inference_context
        if ctx_raw is not None and not str(ctx_raw).strip():
            ctx_raw = None
        ctx = ctx_raw
        if not ctx and not os.environ.get("UNGRAPH_OPENAI_MODEL_INFERENCE_CONTEXT"):
            env_c = os.environ.get("OPENAI_MODEL_INFERENCE_CONTEXT")
            if env_c and str(env_c).strip():
                ctx = str(env_c).strip()
        object.__setattr__(self, "openai_model_inference_context", ctx)

        dq_raw = self.openai_model_inference_domain_questions
        if dq_raw is not None and not str(dq_raw).strip():
            dq_raw = None
        dq = dq_raw
        if not dq and not os.environ.get("UNGRAPH_OPENAI_MODEL_INFERENCE_DOMAIN_QUESTIONS"):
            env_dq = os.environ.get("OPENAI_MODEL_INFERENCE_DOMAIN_QUESTIONS")
            if env_dq and str(env_dq).strip():
                dq = str(env_dq).strip()
        object.__setattr__(self, "openai_model_inference_domain_questions", dq)
        return self


def resolve_openai_model_for_inference_extraction(settings: Settings) -> str:
    """
    Model name for ``ChatOpenAI`` in LLM inference (GraphTransformer extraction).

    Precedence:
    1. ``openai_model_inference_extraction`` (explicit override).
    2. ``inference_model_budget``: *economy* → ``gpt-4o-mini``; *quality* upgrades
       ``*mini*`` models to ``gpt-4o``; *balanced* → ``openai_model``.
    """
    raw = settings.openai_model_inference_extraction
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    budget = settings.inference_model_budget
    base = (settings.openai_model or "").strip() or "gpt-4o-mini"
    if budget == "economy":
        return "gpt-4o-mini"
    if budget == "quality":
        if "mini" in base.lower():
            return "gpt-4o"
        return base
    return base


def resolve_openai_model_for_inference_context(settings: Settings) -> str:
    """
    Model for ``LlmDocumentContextService`` (resumen + hints del documento).

    Precedence:
    1. ``openai_model_inference_context`` (explicit override).
    2. *economy* / *balanced* → ``gpt-4o-mini``; *quality* upgrades ``*mini*`` to ``gpt-4o``.
    """
    raw = settings.openai_model_inference_context
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    budget = settings.inference_model_budget
    base = (settings.openai_model or "").strip() or "gpt-4o-mini"
    if budget in ("economy", "balanced"):
        return "gpt-4o-mini"
    if "mini" in base.lower():
        return "gpt-4o"
    return base


def resolve_openai_model_for_inference_domain_questions(settings: Settings) -> str:
    """
    Model for ``LlmDomainQuestionGenerator``.

    If ``openai_model_inference_domain_questions`` is set, returns it; otherwise
    matches the context step (one shared ``ChatOpenAI`` when names coincide).
    """
    raw = settings.openai_model_inference_domain_questions
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return resolve_openai_model_for_inference_context(settings)


_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings instance (singleton)
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def configure(**kwargs: Any) -> None:
    """
    Configure settings programmatically.
    
    This function allows setting configuration values programmatically,
    overriding environment variables. Values set here take precedence.
    
    Args:
        **kwargs: Configuration key-value pairs
        
    Example:
        >>> from src.core.configuration import configure
        >>> configure(
        ...     neo4j_uri="bolt://localhost:7687",
        ...     neo4j_password="mypassword",
        ...     neo4j_database="my_database"
        ... )
    """
    # Get current settings or create new
    current_settings = get_settings()
    
    # Update settings with provided values
    for key, value in kwargs.items():
        if hasattr(current_settings, key):
            setattr(current_settings, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")
    
    # Also update environment variables for compatibility
    for key, value in kwargs.items():
        env_key = f"UNGRAPH_{key.upper()}"
        os.environ[env_key] = str(value)


def reset_configuration() -> None:
    """
    Reset configuration to default (from environment variables).
    
    Useful for testing or resetting programmatic changes.
    """
    global _settings_instance
    _settings_instance = None


# Default settings instance
settings = get_settings()