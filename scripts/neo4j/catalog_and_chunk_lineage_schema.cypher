// Idempotent schema for BibliographicArticle catalog + Chunk lineage indexing.
// Run with: cypher-shell -f scripts/neo4j/catalog_and_chunk_lineage_schema.cypher
// Neo4j 5.x syntax (RANGE / RANGE INDEX where applicable).

// --- BibliographicArticle (catalog) ---
CREATE CONSTRAINT bibliographic_article_document_uid_unique IF NOT EXISTS
FOR (a:BibliographicArticle)
REQUIRE a.document_uid IS UNIQUE;

CREATE INDEX biblio_doi_norm_idx IF NOT EXISTS
FOR (a:BibliographicArticle)
ON (a.doi_norm);

CREATE INDEX biblio_external_id_idx IF NOT EXISTS
FOR (a:BibliographicArticle)
ON (a.external_id);

CREATE INDEX biblio_source_sha256_idx IF NOT EXISTS
FOR (a:BibliographicArticle)
ON (a.source_sha256);

CREATE INDEX biblio_canonical_filename_idx IF NOT EXISTS
FOR (a:BibliographicArticle)
ON (a.canonical_filename);

CREATE INDEX biblio_source_size_bytes_idx IF NOT EXISTS
FOR (a:BibliographicArticle)
ON (a.source_size_bytes);

// --- Chunk lineage (NEXT_CHUNK scoping) ---
CREATE INDEX chunk_source_document_uid_idx IF NOT EXISTS
FOR (c:Chunk)
ON (c.source_document_uid);
