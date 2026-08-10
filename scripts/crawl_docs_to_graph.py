#!/usr/bin/env python3
"""
Crawl de sitios de documentación y ingesta en Neo4j vía Ungraph (HTML → CIR → chunks).

Requisitos:
  pip install 'ungraph[crawl]'
  Variables Neo4j configuradas (o ``ungraph.configure(...)`` en código).

Ejemplos (modo crawl + dry-run sin Neo4j):

  uv run python scripts/crawl_docs_to_graph.py --preset ibm-quantum --max-pages 20 --out ./_crawl_out --dry-run
  uv run python scripts/crawl_docs_to_graph.py --preset langchain-ref --max-pages 30 --out ./_crawl_out --dry-run
  uv run python scripts/crawl_docs_to_graph.py --preset neo4j-docs --max-pages 25 --out ./_crawl_out --dry-run

Ingesta real (requiere Neo4j):

  uv run python scripts/crawl_docs_to_graph.py --preset ibm-quantum --max-pages 15 --out ./_crawl_out

Notas:
  - El crawl no ejecuta JavaScript; si el HTML inicial está vacío, el sitio puede ser SPA.
  - Respeta ``delay`` entre peticiones; revisa robots.txt y términos del sitio antes de crawlear a escala.
  - Neo4j ``robots.txt`` tiene reglas complejas; el prefijo ``/docs`` puede excluir parte del árbol.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("crawl_docs")

PRESETS: dict[str, dict[str, str]] = {
    "ibm-quantum": {
        "seed": "https://quantum.cloud.ibm.com/docs/en/guides",
        "path_prefix": "/docs/en",
        "sitemap": "https://quantum.cloud.ibm.com/sitemap.xml",
    },
    "langchain-ref": {
        "seed": "https://reference.langchain.com/",
        "path_prefix": "/",
        "sitemap": "https://reference.langchain.com/sitemap.xml",
    },
    "neo4j-docs": {
        "seed": "https://neo4j.com/docs/",
        "path_prefix": "/docs",
        "sitemap": "https://neo4j.com/docs/sitemap_index.xml",
    },
}


def main() -> int:
    p = argparse.ArgumentParser(description="Crawl documentación → Ungraph / Neo4j")
    p.add_argument("--preset", choices=list(PRESETS.keys()), help="Semilla y prefijo conocidos")
    p.add_argument("--seed", help="URL semilla (si no usas --preset)")
    p.add_argument("--path-prefix", help="Solo enlaces bajo este path (p. ej. /docs/en)")
    p.add_argument("--max-pages", type=int, default=30)
    p.add_argument("--out", type=Path, default=Path("_crawl_html"))
    p.add_argument("--delay", type=float, default=0.6, help="Segundos entre GET")
    p.add_argument("--use-sitemap", action="store_true", help="Sembrar cola desde sitemap")
    p.add_argument("--sitemap-url", help="URL del sitemap (override)")
    p.add_argument("--dry-run", action="store_true", help="Solo crawl y extracción; no Neo4j")
    p.add_argument("--chunk-size", type=int, default=1000)
    p.add_argument("--chunk-overlap", type=int, default=200)
    args = p.parse_args()

    if args.preset:
        pr = PRESETS[args.preset]
        seed = pr["seed"]
        path_prefix = args.path_prefix or pr["path_prefix"]
        sitemap_url = args.sitemap_url or pr.get("sitemap")
    else:
        if not args.seed:
            logger.error("Indica --preset o --seed")
            return 2
        seed = args.seed
        path_prefix = args.path_prefix
        sitemap_url = args.sitemap_url

    from ungraph.infrastructure.services.doc_site_crawler import (
        DocumentationCrawlConfig,
        crawl_documentation_site,
    )

    cfg = DocumentationCrawlConfig(
        seed_urls=[seed],
        max_pages=args.max_pages,
        path_prefix=path_prefix,
        delay_seconds=args.delay,
        use_sitemap=args.use_sitemap,
        sitemap_url=sitemap_url,
    )

    logger.info("Crawling seed=%s prefix=%s max=%s", seed, path_prefix, args.max_pages)
    pages = crawl_documentation_site(cfg, args.out)
    logger.info("Descargadas %s páginas en %s", len(pages), args.out)

    if args.dry_run:
        from ungraph.infrastructure.services.html_cir_extractor import extract_web_document

        total_blocks = 0
        for pg in pages:
            raw = pg.local_path.read_bytes()
            wd = extract_web_document(raw, source_id=pg.url)
            total_blocks += len(wd.blocks)
            logger.info("  %s → %s bloques CIR", pg.url[:80], len(wd.blocks))
        logger.info("Dry-run OK: %s páginas, %s bloques CIR totales", len(pages), total_blocks)
        return 0

    import ungraph

    n_ok = 0
    for pg in pages:
        try:
            ungraph.ingest_document(
                pg.local_path,
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                source_url=pg.url,
            )
            n_ok += 1
            logger.info("Ingerido: %s", pg.url)
        except Exception as e:
            logger.exception("Fallo ingest %s: %s", pg.url, e)
    logger.info("Ingesta completada: %s / %s URLs", n_ok, len(pages))
    return 0 if n_ok == len(pages) else 1


if __name__ == "__main__":
    sys.exit(main())
