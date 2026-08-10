"""
Entidad de Dominio: Chunk

Una entidad representa un objeto de negocio con identidad propia.
En Clean Architecture, las entidades:
- Contienen SOLO datos (atributos)
- Pueden tener lógica de negocio básica (validaciones, cálculos)
- NO conocen frameworks externos (Neo4j, LangChain, etc.)
- NO saben cómo guardarse o persistirse (eso es responsabilidad del repositorio)

Ejemplo de uso:
    chunk = Chunk(
        id="chunk_123",
        page_content="Este es el contenido del chunk",
        metadata={"filename": "doc.md", "page": 1}
    )
    print(chunk.page_content)  # Acceder a datos
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class Chunk:
    """
    Entidad que representa un chunk de texto en el dominio.
    
    Attributes:
        id: Identificador único del chunk
        page_content: Contenido textual del chunk (nombre consistente con código existente)
        metadata: Metadatos adicionales (filename, page_number, etc.)
        chunk_id_consecutive: Número consecutivo del chunk en el documento
        embeddings: Vector de embeddings (opcional)
        embeddings_dimensions: Dimensión del vector de embeddings
        embedding_encoder_info: Información del encoder usado
        is_unitary: Indica si el chunk es unitario (no dividido)
        source_document_uid: Ámbito estable del documento lógico para NEXT_CHUNK / catálogo (también puede ir en metadata).
        source_parent_uids: Lista de ids de fuentes padres (multipadre / trazabilidad).
        doi_norm: DOI normalizado si aplica al documento origen.
        primary_parent_uid: Ancla única UX opcional dentro de source_parent_uids.
        retrieval_optimized_text: Texto derivado para recuperación/LLM (menos ruido que page_content).
        retrieval_token_estimate: Estimación de tokens del texto de recuperación (p. ej. para Neo4j).
    """
    id: str
    page_content: str
    metadata: Dict[str, Any]
    chunk_id_consecutive: Optional[int] = None
    embeddings: Optional[List[float]] = None
    embeddings_dimensions: Optional[int] = None
    embedding_encoder_info: Optional[str] = None
    is_unitary: bool = False
    source_document_uid: Optional[str] = None
    source_parent_uids: Optional[List[str]] = field(default=None)
    doi_norm: Optional[str] = None
    primary_parent_uid: Optional[str] = None
    retrieval_optimized_text: Optional[str] = None
    retrieval_optimization_strategy: Optional[str] = field(default=None, repr=False)
    retrieval_token_estimate: Optional[int] = field(default=None, repr=False)
    
    def __post_init__(self):
        """
        Validaciones básicas de negocio después de crear la instancia.
        Esto es lógica de dominio permitida en entidades.
        """
        if not self.id:
            raise ValueError("Chunk id cannot be empty")
        if not self.page_content:
            raise ValueError("Chunk content cannot be empty")
        if self.embeddings and self.embeddings_dimensions:
            if len(self.embeddings) != self.embeddings_dimensions:
                raise ValueError(
                    f"Embeddings dimension mismatch: "
                    f"expected {self.embeddings_dimensions}, got {len(self.embeddings)}"
                )
    
    def get_filename(self) -> Optional[str]:
        """
        Método de dominio: extrae el filename de los metadatos.
        Esto es lógica de negocio, no persistencia.
        """
        return self.metadata.get('filename')

    def get_source_document_uid(self) -> Optional[str]:
        """UID del documento lógico (campo dedicado o metadata)."""
        return self.source_document_uid or self.metadata.get('source_document_uid')

    def get_source_parent_uids(self) -> List[str]:
        raw = self.source_parent_uids or self.metadata.get('source_parent_uids') or []
        if isinstance(raw, list):
            return [str(x) for x in raw]
        return [str(raw)] if raw is not None else []
    
    def get_page_number(self) -> Optional[int]:
        """
        Método de dominio: extrae el número de página de los metadatos.
        """
        return self.metadata.get('page_number')
