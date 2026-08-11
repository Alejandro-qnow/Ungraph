"""
Crawl de sitios de documentación: BFS por enlaces y/o semillas desde sitemap.

Requiere el extra ``ungraph[crawl]`` (httpx). Pensado para alimentar la ingesta HTML
con ``source_url`` para trazabilidad en RAG.

No ejecuta JavaScript: sitios 100% SPA pueden devolver HTML vacío; en ese caso
usar prerender o Playwright fuera del núcleo.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Set
from urllib.parse import urljoin, urlparse, urlunparse

from lxml import html as lxml_html

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (compatible; UngraphDocCrawler/0.1; +https://github.com/) "
    "AppleWebKit/537.36 (KHTML, like Gecko)"
)


def _norm_url(url: str) -> str:
    p = urlparse(url.strip())
    if not p.scheme or not p.netloc:
        return url.strip()
    # Quitar fragmento; opcionalmente normalizar path
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((p.scheme, p.netloc.lower(), path, "", p.query, ""))


def _same_site(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


_STATIC_SUFFIXES = (
    ".css",
    ".js",
    ".mjs",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
    ".xml",
    ".json",
    ".webmanifest",
)


def _looks_like_document_page(url: str) -> bool:
    """Excluye URLs que suelen ser assets, no páginas HTML de documentación."""
    path = urlparse(url).path.lower()
    if path.endswith("/"):
        path = path[:-1]
    for suf in _STATIC_SUFFIXES:
        if path.endswith(suf):
            return False
    return True


def _path_starts(url: str, prefix_path: str) -> bool:
    path = urlparse(url).path or "/"
    pref = prefix_path if prefix_path.startswith("/") else f"/{prefix_path}"
    pref = pref.rstrip("/") or "/"
    return path == pref or path.startswith(pref + "/") or path.startswith(pref)


@dataclass
class DocumentationCrawlConfig:
    """Configuración de un crawl orientado a documentación."""

    seed_urls: list[str]
    max_pages: int = 50
    path_prefix: str | None = None
    """Si se omite, se usa el path del primer seed (p. ej. /docs/en/guides)."""
    delay_seconds: float = 0.5
    request_timeout: float = 30.0
    user_agent: str = DEFAULT_UA
    use_sitemap: bool = False
    """Si True, añade URLs del sitemap del host que encajen con path_prefix."""
    sitemap_url: str | None = None
    """Por defecto: {scheme}://{host}/sitemap.xml"""
    link_allow: Callable[[str], bool] | None = None
    """Filtro opcional adicional sobre URLs absolutas."""


@dataclass
class CrawledPage:
    url: str
    local_path: Path
    bytes_written: int


def _default_sitemap_url(seed: str) -> str:
    p = urlparse(seed)
    return f"{p.scheme}://{p.netloc}/sitemap.xml"


def _loc_tags(xml_bytes: bytes) -> list[str]:
    text = xml_bytes.decode("utf-8", errors="ignore")
    return [m.strip() for m in re.findall(r"<loc>\s*([^<]+)\s*</loc>", text, re.I)]


def fetch_sitemap_urls(
    sitemap_url: str,
    *,
    timeout: float = 30.0,
    user_agent: str = DEFAULT_UA,
) -> list[str]:
    """Descarga sitemap (y sitemaps hijos de índice) y devuelve URLs de páginas."""
    try:
        import httpx
    except ImportError as e:
        raise ImportError("Instala httpx: pip install 'ungraph[crawl]'") from e

    out: list[str] = []
    seen_sm: Set[str] = set()

    def fetch_one(url: str) -> None:
        if url in seen_sm:
            return
        seen_sm.add(url)
        r = httpx.get(
            url,
            timeout=timeout,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )
        r.raise_for_status()
        for u in _loc_tags(r.content):
            if u.strip().lower().endswith(".xml"):
                fetch_one(u)
            else:
                out.append(_norm_url(u))

    fetch_one(sitemap_url)
    return out


def extract_same_site_links(html_bytes: bytes, base_url: str) -> set[str]:
    """Extrae href absolutos del mismo sitio (http/https)."""
    doc = lxml_html.document_fromstring(html_bytes)
    base = _norm_url(base_url)
    netloc = urlparse(base).netloc.lower()
    found: set[str] = set()
    for el, attr, link, _ in doc.iterlinks():
        if attr != "href":
            continue
        if not link or link.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_u = _norm_url(urljoin(base, link))
        p = urlparse(abs_u)
        if p.scheme not in ("http", "https"):
            continue
        if p.netloc.lower() != netloc:
            continue
        found.add(abs_u)
    return found


def _safe_filename(url: str) -> str:
    p = urlparse(url)
    slug = (p.path.strip("/") or "index").replace("/", "_")
    slug = re.sub(r"[^\w\-_.]", "_", slug)[:100]
    h = hashlib.sha256(url.encode()).hexdigest()[:12]
    return f"{slug}_{h}.html"


def crawl_documentation_site(
    config: DocumentationCrawlConfig,
    output_dir: Path,
) -> list[CrawledPage]:
    """
    Descarga páginas (BFS desde seeds + opcionalmente sitemap) y guarda HTML en disco.

    Returns:
        Lista de :class:`CrawledPage` con ``url``, ``local_path`` para pasar a
        ``ingest_document(..., source_url=url)``.
    """
    try:
        import httpx
    except ImportError as e:
        raise ImportError("Instala httpx: pip install 'ungraph[crawl]'") from e

    output_dir.mkdir(parents=True, exist_ok=True)
    seed = _norm_url(config.seed_urls[0])
    prefix = config.path_prefix
    if prefix is None:
        prefix = urlparse(seed).path.rstrip("/") or "/"
    if not prefix.startswith("/"):
        prefix = "/" + prefix

    queue: list[str] = []
    seen: Set[str] = set()

    if config.use_sitemap:
        sm_url = config.sitemap_url or _default_sitemap_url(seed)
        try:
            for u in fetch_sitemap_urls(sm_url, timeout=config.request_timeout, user_agent=config.user_agent):
                if (
                    _same_site(u, seed)
                    and _path_starts(u, prefix)
                    and _looks_like_document_page(u)
                ):
                    if config.link_allow is None or config.link_allow(u):
                        queue.append(u)
        except Exception as e:
            logger.warning("Sitemap no usable (%s): %s", sm_url, e)

    for s in config.seed_urls:
        su = _norm_url(s)
        if su not in seen:
            queue.append(su)

    results: list[CrawledPage] = []

    with httpx.Client(
        headers={"User-Agent": config.user_agent},
        timeout=config.request_timeout,
        follow_redirects=True,
    ) as client:
        while queue and len(results) < config.max_pages:
            url = queue.pop(0)
            if url in seen:
                continue
            seen.add(url)

            if not _same_site(url, seed):
                continue
            if not _path_starts(url, prefix):
                continue
            if not _looks_like_document_page(url):
                continue
            if config.link_allow and not config.link_allow(url):
                continue

            try:
                resp = client.get(url)
                resp.raise_for_status()
                ct = resp.headers.get("content-type", "")
                if "text/html" not in ct and "application/xhtml" not in ct:
                    logger.debug("Omitido (no HTML): %s (%s)", url, ct)
                    continue
                body = resp.content
            except Exception as e:
                logger.warning("Fallo GET %s: %s", url, e)
                continue

            fname = _safe_filename(url)
            local_path = output_dir / fname
            local_path.write_bytes(body)

            results.append(
                CrawledPage(url=url, local_path=local_path, bytes_written=len(body))
            )

            if config.delay_seconds > 0:
                time.sleep(config.delay_seconds)

            if len(results) >= config.max_pages:
                break

            for link in extract_same_site_links(body, url):
                if link in seen:
                    continue
                if not _path_starts(link, prefix):
                    continue
                if not _looks_like_document_page(link):
                    continue
                if config.link_allow and not config.link_allow(link):
                    continue
                if link not in queue:
                    queue.append(link)

    return results
