# Translation & Naming Checklist (Ungraph)

This checklist organizes documentation and code to standardize everything in English and apply language prefixes. It is intended for incremental execution; check items as they are completed.

## Conventions
- Prefix for Spanish docs: `sp-<original>.md`
- Prefix for English docs: `en-<original>.md`
- Keep parallel files when both languages exist (e.g., `sp-quickstart.md` and `en-quickstart.md`).
- Code docstrings and comments: English only. Docstrings should follow Google-style or NumPy-style consistently.

## Proposed Renames (Spanish → add `sp-` prefix)
Note: Do NOT apply renames until link updates are planned. This list is a mapping proposal.

- [ ] docs/_RELEASE_v0.1.0_COMPLETADO.md → docs/sp-_RELEASE_v0.1.0_COMPLETADO.md
- [ ] docs/INSTALLATION_INFERENCE.md → docs/sp-INSTALLATION_INFERENCE.md
- [ ] docs/guides/ingestion.md → docs/guides/sp-ingestion.md
- [ ] docs/guides/custom-patterns.md → docs/guides/sp-custom-patterns.md
- [ ] docs/guides/quickstart.md → docs/guides/sp-quickstart.md
- [ ] docs/guides/search.md → docs/guides/sp-search.md
- [ ] docs/examples/basic-examples.md → docs/examples/sp-basic-examples.md
- [ ] docs/examples/advanced-examples.md → docs/examples/sp-advanced-examples.md
- [ ] docs/examples/notebooks.md → docs/examples/sp-notebooks.md
- [ ] docs/concepts/introduction.md → docs/concepts/sp-introduction.md
- [ ] docs/concepts/architecture.md → docs/concepts/sp-architecture.md
- [ ] docs/concepts/graph-patterns.md → docs/concepts/sp-graph-patterns.md
- [ ] docs/concepts/lexical-graphs.md → docs/concepts/sp-lexical-graphs.md
- [ ] docs/api/public-api.md → docs/api/sp-public-api.md
- [ ] docs/api/advanced-search-patterns.md → docs/api/sp-advanced-search-patterns.md
- [ ] docs/api/search-patterns.md → docs/api/sp-search-patterns.md
- [ ] docs/validation/README.md → docs/validation/sp-README.md
- [ ] docs/validation/validation_summary.md → docs/validation/sp-validation_summary.md
- [ ] VALIDACION_RELEASE.md → sp-VALIDACION_RELEASE.md (repository root)
- [ ] article/PLAN_PUBLICACION.md → article/sp-PLAN_PUBLICACION.md
- [ ] article/ungraph.md → article/sp-ungraph.md
- [ ] src/notebooks/_NOTEBOOKS_FALTANTES.md → src/notebooks/sp-_NOTEBOOKS_FALTANTES.md
- [ ] src/notebooks/_ANALISIS_REORDENAMIENTO.md → src/notebooks/sp-_ANALISIS_REORDENAMIENTO.md

## Proposed Renames (English → add `en-` prefix)
- [ ] article/experiments/README.md → article/experiments/en-README.md
- [ ] article/experiments/templates/README.md → article/experiments/templates/en-README.md
- [ ] article/E1_chunking_finance/dataset/README.md → article/E1_chunking_finance/dataset/en-README.md

If other English docs exist (e.g., theory or API sections), include them after language verification.

## Translation Targets — Documentation (create English versions)
Create corresponding `en-` files with full translation and keep Spanish files as `sp-`.

- [ ] docs/guides/sp-quickstart.md → docs/guides/en-quickstart.md
- [ ] docs/guides/sp-ingestion.md → docs/guides/en-ingestion.md
- [ ] docs/guides/sp-custom-patterns.md → docs/guides/en-custom-patterns.md
- [ ] docs/guides/sp-search.md → docs/guides/en-search.md
- [ ] docs/api/sp-public-api.md → docs/api/en-public-api.md
- [ ] docs/api/sp-search-patterns.md → docs/api/en-search-patterns.md
- [ ] docs/api/sp-advanced-search-patterns.md → docs/api/en-advanced-search-patterns.md
- [ ] docs/concepts/sp-introduction.md → docs/concepts/en-introduction.md
- [ ] docs/concepts/sp-architecture.md → docs/concepts/en-architecture.md
- [ ] docs/concepts/sp-graph-patterns.md → docs/concepts/en-graph-patterns.md
- [ ] docs/concepts/sp-lexical-graphs.md → docs/concepts/en-lexical-graphs.md
- [ ] docs/validation/sp-README.md → docs/validation/en-README.md
- [ ] docs/validation/sp-validation_summary.md → docs/validation/en-validation_summary.md
- [ ] docs/sp-INSTALLATION_INFERENCE.md → docs/en-INSTALLATION_INFERENCE.md
- [ ] docs/sp-_RELEASE_v0.1.0_COMPLETADO.md → docs/en-RELEASE_v0.1.0_SUMMARY.md (adapt title)
- [ ] sp-VALIDACION_RELEASE.md → en-RELEASE_VALIDATION.md
- [ ] article/sp-PLAN_PUBLICACION.md → article/en-PUBLICATION_PLAN.md
- [ ] article/sp-ungraph.md → article/en-ungraph.md
- [ ] src/notebooks/sp-_NOTEBOOKS_FALTANTES.md → src/notebooks/en-NOTEBOOKS_GAP_ANALYSIS.md
- [ ] src/notebooks/sp-_ANALISIS_REORDENAMIENTO.md → src/notebooks/en-NOTEBOOKS_REORDERING_ANALYSIS.md

## Translation Targets — Code (docstrings and comments → English)
Prioritize public API and developer-facing modules. Keep identifiers in English.

- [ ] src/__init__.py — translate module header, examples, and docstrings:
  - [ ] `ChunkingRecommendation` docstring
  - [ ] `ingest_document()` docstring
  - [ ] `search()` docstring
  - [ ] `hybrid_search()` docstring
  - [ ] `search_with_pattern()` docstring
  - [ ] `suggest_chunking_strategy()` docstring
- [ ] src/core/configuration.py — ensure all docstrings in English
- [ ] src/application/use_cases/ingest_document.py — docstrings/comments in English
- [ ] src/domain/entities/* — class docstrings in English
- [ ] src/domain/services/* — service docstrings in English
- [ ] src/infrastructure/services/* — docstrings in English
- [ ] src/utils/chunking_master.py — docstrings in English
- [ ] scripts/*.py — user-facing script help/messages in English

## Link Updates (after renames)
- [ ] Update internal links in the documentation to new `sp-*/en-*` filenames
- [ ] Update indexes/TOCs: docs/README.md and repository README
- [ ] Ensure tests or docs references to paths are updated

## Process & QA
- [ ] Establish style guide for English docstrings (Google-style preferred)
- [ ] Add a pre-commit check to flag non-English docstrings/comments in `src/`
- [ ] Spot-check translations for technical accuracy
- [ ] Build docs locally (if applicable) to validate links

## Notes
- This file is the working checklist; feel free to add/remove entries as we discover more files.
- Large renames will be done in batches, with automated link updates to avoid breakages.
