// =============================================================================
// Contrato de prueba: HTML → grafo (documentación / CIR enriquecido)
// =============================================================================
// Objetivo: consultas Cypher reproducibles para validar que la ingesta respeta
// secciones, texto, enlaces e imágenes como subnodos (no solo texto plano).
// Estado: ESPECIFICACIÓN — el pipeline actual (FILE_PAGE_CHUNK) aún no crea
// todos estos nodos; usar como checklist al extender CIR + patrones Neo4j.
// =============================================================================

// --- 1) Forma de grafo objetivo (ejemplo mínimo) ---
// WebPage (o File) —[:HAS_SECTION]-> Section —[:CONTAINS]-> ContentAtom
// ContentAtom: kind IN ['text','link','image','code',...]
// (:ImageAsset)-[:REFERENCED_BY]->(:ContentAtom {kind:'image'})
// Chunk sigue pudiendo colgarse de Page/File para GraphRAG; los átomos dan
// granularidad para pruebas y para el constructor de imágenes (WIP 11/12).

/*
CREATE (wp:WebPage {
  source_id: 'https://example.com/doc',
  title: 'Demo',
  canonical_url: 'https://example.com/doc'
})
CREATE (sec:Section {
  section_id: 'sec-1',
  order_index: 0,
  heading_path: ['Intro', 'Detalle']
})
CREATE (t:ContentAtom {
  atom_id: 'a1',
  kind: 'text',
  order_index: 0,
  text: 'Párrafo visible.'
})
CREATE (l:ContentAtom {
  atom_id: 'a2',
  kind: 'link',
  order_index: 1,
  text: 'leer más',
  href: 'https://example.com/more'
})
CREATE (i:ContentAtom {
  atom_id: 'a3',
  kind: 'image',
  order_index: 2,
  alt: 'Diagrama',
  src: 'https://example.com/d.png'
})
CREATE (img:ImageAsset {
  asset_id: 'img-hash-or-uri',
  src: 'https://example.com/d.png',
  mime: 'image/png'
})
CREATE (wp)-[:HAS_SECTION {order_index:0}]->(sec)
CREATE (sec)-[:CONTAINS]->(t)
CREATE (sec)-[:CONTAINS]->(l)
CREATE (sec)-[:CONTAINS]->(i)
CREATE (img)-[:REFERENCED_BY]->(i);
*/

// --- 2) Consultas de sanidad (ejecutar tras CREATE de prueba o ingesta real) ---

// Todas las imágenes con su sección y página de origen
// MATCH (wp:WebPage)-[:HAS_SECTION*0..1]->(sec:Section)-[:CONTAINS]->(atom:ContentAtom {kind:'image'})
// RETURN wp.source_id, sec.heading_path, atom.src, atom.alt;

// Enlaces salientes por página (deduplicar por href si hace falta)
// MATCH (wp:WebPage)-[:HAS_SECTION]->(:Section)-[:CONTAINS]->(l:ContentAtom {kind:'link'})
// RETURN wp.source_id, l.href, l.text
// ORDER BY l.href;

// Orden dentro de una sección (subnodos)
// MATCH (sec:Section {section_id:'sec-1'})-[:CONTAINS]->(a:ContentAtom)
// RETURN a.order_index, a.kind, coalesce(a.text, a.alt, a.href) AS preview
// ORDER BY a.order_index;

// Puente futuro: átomo imagen → asset para pipeline ETI de imágenes
// MATCH (atom:ContentAtom {kind:'image'})-[:LINKS_TO_ASSET]->(asset:ImageAsset)
// RETURN atom, asset;
