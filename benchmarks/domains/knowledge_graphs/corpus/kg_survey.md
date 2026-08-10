# A Concise Survey of Knowledge Graphs

## Foundations

A Knowledge Graph is a structured representation of facts, where entities are nodes and
relationships are edges. Knowledge Graphs power semantic search, question answering, and
retrieval-augmented generation. Two dominant data models exist: the RDF model and the
property graph model.

RDF represents facts as subject–predicate–object triples. SPARQL is the standard query
language for RDF data. Ontologies define the schema of an RDF graph; RDFS and OWL are
ontology languages, and OWL extends RDFS with richer semantics such as class hierarchies
and property restrictions.

The property graph model stores properties on both nodes and edges. Neo4j is a popular
property graph database, and Cypher is the query language used by Neo4j. Property graphs
are favored for operational workloads because Cypher expresses traversals concisely.

## Learning over graphs

Knowledge Graph Embeddings map entities and relations into a vector space. TransE is a
translational embedding model that represents a relation as a translation from the
subject vector to the object vector. DistMult is a bilinear embedding model. These
embeddings enable link prediction, which infers missing relationships in an incomplete
Knowledge Graph.

Graph Neural Networks operate directly on graph structure. A Graph Neural Network
aggregates information from a node's neighbors to compute node representations, and it is
widely used for node classification over Knowledge Graphs.

## Construction

Knowledge Graph Construction extracts a graph from unstructured text. Named Entity
Recognition identifies entity mentions, and Relation Extraction identifies relationships
between entities. Entity Resolution merges duplicate entities that refer to the same
real-world object. Large Language Models are increasingly used for Relation Extraction
because they capture semantic context beyond surface patterns.

## Retrieval-augmented generation

GraphRAG is a retrieval-augmented generation method that retrieves context from a
Knowledge Graph instead of a flat vector index. GraphRAG improves multi-hop reasoning
because the graph makes relationships between facts explicit. A GraphRAG system typically
combines vector search over text chunks with graph traversal over entities.
