"""
Verificación del pipeline documentación HTML → CIR → loader → chunks → Neo4j (opcional).

Usado por ``scripts/verify_documentation_ingest_pipeline.py`` y por el notebook 10.1.
"""

from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocSeed:
    """Nombre legible, URL semilla y prefijo de path para el crawler (mismo host)."""

    name: str
    url: str
    path_prefix: str


DOCUMENTATION_SEEDS: tuple[DocSeed, ...] = (
    DocSeed(
        "IBM Quantum (guides)",
        "https://quantum.cloud.ibm.com/docs/en/guides",
        "/docs/en",
    ),
    DocSeed(
        "LangChain Reference (home)",
        "https://reference.langchain.com/",
        "/",
    ),
    DocSeed(
        "Neo4j Documentation (hub)",
        "https://neo4j.com/docs/",
        "/docs",
    ),
    DocSeed(
        "LangChain Reference (Python)",
        "https://reference.langchain.com/python",
        "/",
    ),
)


def step_httpx_and_cir(url: str, source_id: str | None = None) -> tuple[int, str]:
    """GET HTML + extracción CIR. Devuelve (n_bloques, preview_markdown)."""
    try:
        import httpx
    except ImportError as e:
        raise RuntimeError("Instala: pip install 'ungraph[crawl]'") from e

    from ungraph.infrastructure.services.html_cir_extractor import extract_web_document

    sid = source_id or url
    r = httpx.get(
        url,
        timeout=45.0,
        headers={"User-Agent": "UngraphVerify/1.0"},
        follow_redirects=True,
    )
    r.raise_for_status()
    ct = r.headers.get("content-type", "")
    if "text/html" not in ct and "application/xhtml" not in ct:
        raise ValueError(f"No HTML: {ct}")

    web = extract_web_document(r.content, source_id=sid)
    preview = web.to_markdown_outline()[:400]
    return len(web.blocks), preview


def step_loader_and_chunking(html_bytes: bytes, filename: str, source_url: str) -> int:
    """Escribe HTML temporal, carga con LangChainDocumentLoaderService, smart_chunk."""
    from ungraph.infrastructure.services.langchain_document_loader_service import (
        LangChainDocumentLoaderService,
    )
    from ungraph.infrastructure.services.langchain_chunking_service import (
        LangChainChunkingService,
    )

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / filename
        p.write_bytes(html_bytes)
        loader = LangChainDocumentLoaderService()
        docs = loader.load(p, clean=False, source_url=source_url)
        if not docs:
            raise ValueError("Loader devolvió 0 documentos")
        chunker = LangChainChunkingService()
        chunks, meta = chunker.smart_chunk(
            docs[0],
            preferred_strategy="markdown_header",
            chunk_size=600,
            chunk_overlap=80,
        )
        assert meta.get("strategy") == "markdown_header"
        return len(chunks)


def step_neo4j_ingest_html_file(
    html_path: Path,
    *,
    source_url: str,
    database: str = "neo4j",
) -> int:
    """Ingesta un archivo HTML con ungraph.ingest_document (requiere Neo4j configurado)."""
    import ungraph
    from ungraph.core.configuration import get_settings

    s = get_settings()
    if not s.neo4j_uri or not s.neo4j_password:
        raise RuntimeError(
            "Neo4j no configurado: UNGRAPH_NEO4J_URI y UNGRAPH_NEO4J_PASSWORD "
            "o ungraph.configure(...)"
        )

    chunks = ungraph.ingest_document(
        html_path,
        chunk_size=800,
        chunk_overlap=120,
        database=database,
        source_url=source_url,
    )
    return len(chunks)


def run_verification(
    *,
    ingest_one: bool = False,
    database: str = "neo4j",
) -> dict[str, Any]:
    """
    Ejecuta verificación por cada semilla: CIR + loader/chunking.
    Si ``ingest_one`` y Neo4j está configurado, ingiere la primera semilla solamente.
    """
    try:
        import httpx
    except ImportError:
        logger.error("Falta httpx: uv sync --extra crawl")
        raise

    results: dict[str, Any] = {"seeds": [], "ingest": None}

    for seed in DOCUMENTATION_SEEDS:
        logger.info("=== %s ===", seed.name)
        n_blocks, preview = step_httpx_and_cir(seed.url)
        logger.info("  CIR bloques: %s", n_blocks)

        r = httpx.get(
            seed.url,
            timeout=45.0,
            headers={"User-Agent": "UngraphVerify/1.0"},
            follow_redirects=True,
        )
        r.raise_for_status()
        n_chunks = step_loader_and_chunking(
            r.content,
            filename="page.html",
            source_url=str(r.url),
        )
        logger.info("  Chunks (markdown_header): %s", n_chunks)

        results["seeds"].append(
            {
                "name": seed.name,
                "url": seed.url,
                "cir_blocks": n_blocks,
                "chunks": n_chunks,
                "markdown_preview": preview[:200] + ("..." if len(preview) > 200 else ""),
            }
        )

        if n_blocks < 1:
            raise AssertionError(f"Sin bloques CIR para {seed.url}")

    if ingest_one:
        first = DOCUMENTATION_SEEDS[0]
        logger.info("Ingesta Neo4j (una página): %s", first.url)
        import httpx

        r = httpx.get(
            first.url,
            timeout=45.0,
            headers={"User-Agent": "UngraphVerify/1.0"},
            follow_redirects=True,
        )
        r.raise_for_status()
        with tempfile.TemporaryDirectory() as td:
            hp = Path(td) / "ibm_guides.html"
            hp.write_bytes(r.content)
            n = step_neo4j_ingest_html_file(
                hp,
                source_url=str(r.url),
                database=database,
            )
            logger.info("Chunks persistidos en grafo: %s", n)
            results["ingest"] = {"url": str(r.url), "chunks": n}

    return results
