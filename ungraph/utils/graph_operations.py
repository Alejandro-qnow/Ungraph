import os
import ast
from typing import Optional, Sequence

from neo4j import GraphDatabase
from neo4j.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


# DB Connection
def graph_session() -> GraphDatabase:
    """
    Creates and returns a connection session to the Neo4j database.

    This function uses configuration from src.core.configuration (centralized).

    Returns:
        GraphDatabase: A Neo4j database driver that allows performing operations
        on the database.

    Raises:
        ValueError: If NEO4J_URI or NEO4J_PASSWORD are not set.
        RuntimeError: If an error occurs while trying to create the database session.
    """
    from ..core.configuration import get_settings
    
    settings = get_settings()
    URI = settings.neo4j_uri
    USER = settings.neo4j_user
    PASSWORD = settings.neo4j_password

    if not URI or not PASSWORD:
        raise ValueError(
            "Faltan credenciales Neo4j. Define UNGRAPH_NEO4J_URI y UNGRAPH_NEO4J_PASSWORD "
            "(o NEO4J_URI y NEO4J_PASSWORD), o usa ungraph.configure(...). "
            "Si usas un .env en la carpeta del paquete, puede ir en ungraph/.env junto a este proyecto."
        )
    
    AUTH = (USER, PASSWORD)

    try:
        logger.info(f"Connecting to Neo4j at {URI} with user {USER}")
        driver = GraphDatabase.driver(URI, auth=AUTH)
        driver.verify_connectivity()
        logger.info("Successfully connected to Neo4j")
        return driver
    except Exception as e:
        error_msg = (
            f"Failed to create a graph session: {e}\n"
            f"URI: {URI}\n"
            f"User: {USER}\n"
            "Please check:\n"
            "1. Neo4j is running\n"
            "2. Credentials are correct\n"
            "3. URI is accessible"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e




## PROCESAMIENTO DE DOCUMENT DATA OBJECT A GRAFO.
# Función para extraer estructura de documento
def extract_document_structure(
    tx,
    filename,
    page_number,
    chunk_id,
    page_content,
    is_unitary,
    embeddings,
    embeddings_dimensions,
    embedding_encoder_info,
    chunk_id_consecutive,
    source_document_uid: Optional[str] = None,
    source_parent_uids: Optional[Sequence[str]] = None,
    doi_norm: Optional[str] = None,
    primary_parent_uid: Optional[str] = None,
):
    """
    Extrae y persiste la estructura FILE-PAGE-CHUNK en Neo4j.
    
    Esta función implementa el patrón básico de estructura del grafo:
    File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
    
    TODO: CREAR EL FUNCIONAMIENTO DE DOD PARA QUE SIRVA CON LO QUE SE LEE EN EL DCUMENTO DE DOCLING.
    
    NOTA: Patrón actual hardcodeado. Para implementar patrones configurables:
    
    ```python
    # Pseudo-implementación de sistema de patrones:
    
    # 1. Definir Value Object para patrones
    @dataclass(frozen=True)
    class GraphPattern:
        name: str
        node_types: List[str]  # ["File", "Page", "Chunk"]
        relationships: Dict[str, List[str]]  # {"File": ["CONTAINS"], "Page": ["HAS_CHUNK"]}
        node_properties: Dict[str, Dict[str, Any]]  # Propiedades por tipo de nodo
    
    # 2. Patrón básico actual
    BASIC_PATTERN = GraphPattern(
        name="FILE_PAGE_CHUNK",
        node_types=["File", "Page", "Chunk"],
        relationships={
            "File": ["CONTAINS"],
            "Page": ["HAS_CHUNK"],
            "Chunk": ["NEXT_CHUNK"]
        },
        node_properties={
            "File": {"filename": str, "createdAt": int},
            "Page": {"filename": str, "page_number": int},
            "Chunk": {"chunk_id": str, "page_content": str, ...}
        }
    )
    
    # 3. Función genérica que usa el patrón
    def extract_document_structure_with_pattern(
        tx, pattern: GraphPattern, **data
    ):
        # Generar query Cypher dinámicamente basado en el patrón
        query = generate_cypher_from_pattern(pattern, data)
        return tx.run(query, **data)
    
    # 4. Permitir pasar patrón como parámetro
    def ingest_document(file_path, pattern: GraphPattern = BASIC_PATTERN):
        # Usar patrón para estructurar el grafo
        ...
    ```
    """
    try:
        parent_list = list(source_parent_uids or [])
        query = """
                MERGE (f:File {filename: $filename})
                ON CREATE SET f.createdAt = timestamp()

                MERGE (p:Page {filename: $filename, page_number: toInteger($page_number)})

                MERGE (c:Chunk {chunk_id: $chunk_id})
                ON CREATE SET c.page_content = $page_content,
                              c.is_unitary = $is_unitary,
                              c.embeddings = $embeddings,
                              c.embeddings_dimensions = toInteger($embeddings_dimensions),
                              c.embedding_encoder_info = $embedding_encoder_info,
                              c.chunk_id_consecutive = toInteger($chunk_id_consecutive),
                              c.filename = $filename,
                              c.page_number = toInteger($page_number),
                              c.source_document_uid = $source_document_uid,
                              c.source_parent_uids = $source_parent_uids,
                              c.doi_norm = $doi_norm,
                              c.primary_parent_uid = $primary_parent_uid
                ON MATCH SET c.page_content = $page_content,
                             c.is_unitary = $is_unitary,
                             c.embeddings = $embeddings,
                             c.embeddings_dimensions = toInteger($embeddings_dimensions),
                             c.embedding_encoder_info = $embedding_encoder_info,
                             c.chunk_id_consecutive = toInteger($chunk_id_consecutive),
                             c.filename = $filename,
                             c.page_number = toInteger($page_number),
                             c.source_document_uid = CASE WHEN $source_document_uid IS NULL THEN c.source_document_uid ELSE $source_document_uid END,
                             c.source_parent_uids = CASE WHEN size($source_parent_uids) = 0 AND c.source_parent_uids IS NOT NULL THEN c.source_parent_uids ELSE $source_parent_uids END,
                             c.doi_norm = CASE WHEN $doi_norm IS NULL THEN c.doi_norm ELSE $doi_norm END,
                             c.primary_parent_uid = CASE WHEN $primary_parent_uid IS NULL THEN c.primary_parent_uid ELSE $primary_parent_uid END

                MERGE (f)-[:CONTAINS]->(p)
                MERGE (p)-[:HAS_CHUNK]->(c)

            """
        result = tx.run(
            query,
            filename=filename,
            page_number=page_number,
            chunk_id=chunk_id,
            page_content=page_content,
            is_unitary=is_unitary,
            embeddings=embeddings,
            embeddings_dimensions=embeddings_dimensions,
            embedding_encoder_info=embedding_encoder_info,
            chunk_id_consecutive=chunk_id_consecutive,
            source_document_uid=source_document_uid,
            source_parent_uids=parent_list,
            doi_norm=doi_norm,
            primary_parent_uid=primary_parent_uid,
        )
        return result
    except ClientError as e:
        logger.error("Database error", exc_info=True)
        tx.rollback()
        raise


def merge_retrieval_context_view(
    tx,
    parent_chunk_id: str,
    optimized_text: str,
    strategy: str,
    token_estimate: int,
):
    """
    Crea/actualiza un nodo RetrievalChunk y la relación HAS_RETRIEVAL_VIEW desde Chunk.

    El texto completo permanece en ``Chunk.page_content``; ``optimized_text`` es la
    vista reducida para ventanas de LLM y búsquedas con menos ruido.
    """
    try:
        query = """
            MATCH (c:Chunk {chunk_id: $parent_chunk_id})
            MERGE (v:RetrievalChunk {parent_chunk_id: $parent_chunk_id})
            SET v.text = $optimized_text,
                v.strategy = $strategy,
                v.token_estimate = toInteger($token_estimate),
                v.updatedAt = timestamp()
            MERGE (c)-[:HAS_RETRIEVAL_VIEW]->(v)
            """
        return tx.run(
            query,
            parent_chunk_id=parent_chunk_id,
            optimized_text=optimized_text,
            strategy=strategy,
            token_estimate=int(token_estimate),
        )
    except ClientError as e:
        logger.error("merge_retrieval_context_view error", exc_info=True)
        tx.rollback()
        raise


def create_chunk_relationships_tx(
    tx,
    *,
    source_document_uid: Optional[str] = None,
    filename: Optional[str] = None,
    chunk_ids: Optional[Sequence[str]] = None,
    global_legacy: bool = False,
) -> None:
    """
    NEXT_CHUNK dentro del mismo ámbito de documento.

    Preferir ``source_document_uid``; si falta usar ``filename`` via patrón File→Page→Chunk;
    si ``chunk_ids`` se proporciona enlaza en orden tras ordenar por ``chunk_id_consecutive``
    dentro de ese conjunto (compat reparación); ``global_legacy`` conserva comportamiento anterior.
    """
    if global_legacy:
        q = """
        MATCH (c1:Chunk), (c2:Chunk)
        WHERE c1.chunk_id_consecutive + 1 = c2.chunk_id_consecutive
        MERGE (c1)-[:NEXT_CHUNK]->(c2)
        """
        tx.run(q)
        return

    if source_document_uid:
        q = """
        MATCH (c1:Chunk), (c2:Chunk)
        WHERE c1.source_document_uid = $uid
          AND c2.source_document_uid = $uid
          AND c1.chunk_id_consecutive + 1 = c2.chunk_id_consecutive
        MERGE (c1)-[:NEXT_CHUNK]->(c2)
        """
        tx.run(q, uid=source_document_uid)
        return

    if filename:
        q = """
        MATCH (f:File {filename: $fn})-[:CONTAINS]->(:Page)-[:HAS_CHUNK]->(c1:Chunk)
        MATCH (f)-[:CONTAINS]->(:Page)-[:HAS_CHUNK]->(c2:Chunk)
        WHERE c1.chunk_id_consecutive + 1 = c2.chunk_id_consecutive
        MERGE (c1)-[:NEXT_CHUNK]->(c2)
        """
        tx.run(q, fn=filename)
        return

    if chunk_ids:
        q = """
        MATCH (c:Chunk)
        WHERE c.chunk_id IN $ids
        WITH c ORDER BY c.chunk_id_consecutive ASC
        WITH collect(c) AS nodes
        UNWIND range(0, size(nodes) - 2) AS i
        WITH nodes[i] AS c1, nodes[i + 1] AS c2
        MERGE (c1)-[:NEXT_CHUNK]->(c2)
        """
        tx.run(q, ids=list(chunk_ids))
        return

    raise ValueError(
        "create_chunk_relationships_tx requires source_document_uid, filename, chunk_ids, or global_legacy=True"
    )


def create_chunk_relationships(
    session,
    *,
    source_document_uid: Optional[str] = None,
    filename: Optional[str] = None,
    chunk_ids: Optional[Sequence[str]] = None,
    global_legacy: bool = False,
) -> None:
    """Crear relaciones NEXT_CHUNK; envoltorio de sesión Neo4j."""

    def work(tx):
        create_chunk_relationships_tx(
            tx,
            source_document_uid=source_document_uid,
            filename=filename,
            chunk_ids=chunk_ids,
            global_legacy=global_legacy,
        )

    try:
        session.execute_write(work)
        logger.info(
            "Chunk relationships created successfully (scoped=%s)",
            source_document_uid or filename or chunk_ids or "global_legacy",
        )
    except Exception as e:
        logger.exception("Error creating chunk relationships: %s", e)
        raise


def create_chunk_relationships_global(session) -> None:
    """Solo saneamiento/admin: cadena NEXT_CHUNK entre todos los chunks consecutivos compartidos (legacy)."""
    create_chunk_relationships(session, global_legacy=True)


def delete_next_chunk_edges_for_chunks_tx(tx, chunk_ids: Sequence[str]) -> None:
    """Elimina aristas NEXT_CHUNK incidentes sobre los chunks dados (incoming y outgoing)."""
    ids = list(chunk_ids)
    if not ids:
        return
    q_out = """
    UNWIND $ids AS cid
    MATCH (c:Chunk {chunk_id: cid})-[r:NEXT_CHUNK]->()
    DELETE r
    """
    q_in = """
    UNWIND $ids AS cid
    MATCH (c:Chunk {chunk_id: cid})<-[r:NEXT_CHUNK]-()
    DELETE r
    """
    tx.run(q_out, ids=ids)
    tx.run(q_in, ids=ids)


def repair_next_chunk_chain_tx(tx, chunk_ids: Sequence[str]) -> None:
    """
    Parche qsar-lab: borrar NEXT_CHUNK que toquen estos ids y recrear cadena por chunk_id_consecutive.
    Requiere que los chunks ya existan y compartan ámbito lógico.
    """
    delete_next_chunk_edges_for_chunks_tx(tx, chunk_ids)
    create_chunk_relationships_tx(tx, chunk_ids=chunk_ids)


def sanitize_illegitimate_next_chunk_tx(tx) -> None:
    """
    Borra NEXT_CHUNK donde ambos extremos tienen source_document_uid distinto (ambos definidos).
    """
    q = """
    MATCH (c1:Chunk)-[r:NEXT_CHUNK]->(c2:Chunk)
    WHERE c1.source_document_uid IS NOT NULL AND c2.source_document_uid IS NOT NULL
      AND c1.source_document_uid <> c2.source_document_uid
    DELETE r
    """
    tx.run(q)


def sanitize_illegitimate_next_chunk(session) -> None:
    session.execute_write(sanitize_illegitimate_next_chunk_tx)



#  Valido que el DataFrame tenga la estructura correcta.
def validate_dataframe(df, expected_dim=384):
    """Validar que el DataFrame tenga la estructura correcta"""
    required_columns = [
        'filename', 'page_number', 'chunk_id', 'page_content',
        'is_unitary', 'embeddings', 'embeddings_dimensions',
        'embedding_encoder_info', 'chunk_id_consecutive'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Validar dimensiones de embeddings
    # Aqui podemos poner las demas dimensiones de los modelo, y ligarlos a la columna de encoder_info.
    if not all(len(emb) == expected_dim for emb in df['embeddings']):
        raise ValueError(f"All embeddings must have {expected_dim} dimensions")
    
    # Validar que chunk_id_consecutive sea secuencial
    # 
    expected_range = range(1, len(df) + 1)
    if not all(df['chunk_id_consecutive'] == expected_range):
        raise ValueError("chunk_id_consecutive must be sequential starting from 1")
    
    return True



# Configuración de índices avanzados, para la búsqueda por contenido y por vector.
def setup_advanced_indexes(session):
    """Configuración de índices avanzados"""
    try:
        # Índice vectorial mejorado
        vector_index_query = """
        CALL db.index.vector.createNodeIndex(
            'chunk_embeddings',           // nombre del índice
            'Chunk',                      // label del nodo
            'embeddings',                 // propiedad que contiene el vector
            384,                          // dimensiones del vector
            'cosine'                      // similitud por coseno
        )
        """
        
        # Índice de texto completo mejorado
        fulltext_index_query = """
        CREATE FULLTEXT INDEX chunk_content IF NOT EXISTS
        FOR (c:Chunk)
        ON EACH [c.page_content]
        OPTIONS {
            indexConfig: {
                `fulltext.analyzer`: 'spanish',
                `fulltext.eventually_consistent`: false
            }
        }
        """
        # Índice regular para búsquedas por chunk_id_consecutive
        regular_index_query = """
        CREATE INDEX chunk_consecutive_idx IF NOT EXISTS
        FOR (c:Chunk)
        ON (c.chunk_id_consecutive)
        """
        

        try:
            session.execute_write(lambda tx: tx.run(regular_index_query))
            logger.info("Regular index created successfully")
        except Exception as e:
            logger.exception("Regular index creation message: %s", e)
            
        try:
            session.execute_write(lambda tx: tx.run(vector_index_query))
            logger.info("Vector index created successfully")
        except Exception as e:
            if "An equivalent index already exists" not in str(e):
                logger.exception("Error creating vector index: %s", e)
                raise e
            logger.info("Vector index already exists")

        try:
            session.execute_write(lambda tx: tx.run(fulltext_index_query))
            logger.info("Full-text index created successfully")
        except Exception as e:
            logger.exception("Full-text index creation message: %s", e)

    except Exception as e:
        print(f"Error in index setup: {e}")



# Tratamiento de columnas para añadir secuencialidad y tipo de dato
def colummn_pretreatment(df):
    # Se les da el formato necesario, esto lo peudo llevar al momento en que se escribe la data en el modulo de ingestión
    df["embeddings"] = df["embeddings"].apply(ast.literal_eval)
    df['chunk_id_consecutive'] = range(1, len(df) + 1)
    return df


# Función para centralizar  el proceso de ingestión de datos al grafo.
def process_with_neo4j(df, batch_size=100, target_database="neo4j"):
    ''' 
    Función que busca:
    1. Configurar los índices en la base de datos.
    2. Validar la idoneidad del dataframe
    3. Procesar en lotes los chunks del texto.
    3.1 Cada lote procesarlo con el query que facilita extraer la extructura del texto.
    4. Una vez creado, populamos con relaciones consecutivas.
    
    '''
    with graph_session() as driver:
        with driver.session(database = target_database) as session:
            # Configurar índices
            setup_advanced_indexes(session)
            
            # Validar datos
            if validate_dataframe(df):
            
                # Procesar chunks en lotes
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i + batch_size]
                    total_batches = (len(df) + batch_size - 1) // batch_size
                    logger.info("Processing batch %d of %d", i // batch_size + 1, total_batches)

                    # Expected default embedding dimension (can be parameterized in the future)
                    embeddings_expected_dim = 384

                    batch.apply(
                        lambda row: session.execute_write(
                            extract_document_structure,
                            filename=row['filename'],
                            page_number=int(row['page_number']),
                            chunk_id=row['chunk_id'],
                            page_content=row['page_content'],
                            is_unitary=bool(row.get('is_unitary', False)),
                            embeddings=row['embeddings'],
                            embeddings_dimensions=int(row.get('embeddings_dimensions', embeddings_expected_dim)),
                            embedding_encoder_info=row.get('embedding_encoder_info', 'unknown'),
                            chunk_id_consecutive=int(row['chunk_id_consecutive'])
                        ),
                        axis=1
                    )

                # Crear relaciones entre chunks consecutivos (legacy global; DataFrame batch path)
                create_chunk_relationships(session, global_legacy=True)
            else:
                logger.error("Data validation failed for DataFrame")
                raise ValueError("Data validation failed for provided DataFrame")



