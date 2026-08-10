"""
Entidad de Dominio: Entity

Representa una entidad nombrada extraída de un chunk (persona, organización, lugar, etc.).

En Clean Architecture, las entidades:
- Contienen SOLO datos (atributos)
- Pueden tener lógica de negocio básica (validaciones)
- NO conocen frameworks externos
- NO saben cómo persistirse

Ejemplo de uso:
    entity = Entity(
        id="entity_123",
        name="Apple Inc.",
        type="ORGANIZATION",
        mentions=["chunk_1", "chunk_5"]
    )
"""

from dataclasses import dataclass, field
from typing import List, Optional

from ungraph.domain.value_objects.curation_state import normalize_curation_state


@dataclass
class Entity:
    """
    Entidad que representa una entidad nombrada extraída de texto.
    
    Una entidad puede ser una persona, organización, lugar, concepto, etc.
    Se extrae mediante técnicas de NER (Named Entity Recognition) o LLMs.
    
    Attributes:
        id: Identificador único de la entidad
        name: Nombre/texto de la entidad
        type: Tipo de entidad (PERSON, ORGANIZATION, LOCATION, etc.)
        mentions: Lista de IDs de chunks donde aparece la entidad
        ontology_class_uri: URI de clase OWL/RDFS si se alinea a ontología externa
        extraction_method: Origen de la extracción (p. ej. "llm", "spacy")
        quality_score: Puntuación opcional de calidad o confianza normalizada
        decision_log_id: Identificador de trazabilidad de la corrida de inferencia
        curation_state: Ciclo de vida de validación: Extracted | Curated | Invalid
    """
    id: str
    name: str
    type: str
    mentions: List[str]
    ontology_class_uri: Optional[str] = None
    extraction_method: Optional[str] = None
    quality_score: Optional[float] = None
    decision_log_id: Optional[str] = field(default=None, repr=False)
    curation_state: str = "Extracted"
    
    def __post_init__(self):
        """
        Validaciones básicas de negocio después de crear la instancia.
        """
        if not self.id:
            raise ValueError("Entity id cannot be empty")
        if not self.name:
            raise ValueError("Entity name cannot be empty")
        if not self.type:
            raise ValueError("Entity type cannot be empty")
        if not isinstance(self.mentions, list):
            raise ValueError("Entity mentions must be a list")
        if self.quality_score is not None and not (0.0 <= self.quality_score <= 1.0):
            raise ValueError(
                f"quality_score must be between 0.0 and 1.0, got {self.quality_score}"
            )
        object.__setattr__(self, "curation_state", normalize_curation_state(self.curation_state))
    
    def add_mention(self, chunk_id: str) -> None:
        """
        Método de dominio: añade una mención de la entidad.
        
        Args:
            chunk_id: ID del chunk donde aparece la entidad
        """
        if chunk_id not in self.mentions:
            self.mentions.append(chunk_id)
    
    def get_mention_count(self) -> int:
        """
        Método de dominio: retorna el número de menciones.
        
        Returns:
            Número de chunks donde aparece la entidad
        """
        return len(self.mentions)
    
    def is_person(self) -> bool:
        """
        Método de dominio: verifica si la entidad es una persona.
        
        Returns:
            True si type es PERSON
        """
        return self.type.upper() == "PERSON"
    
    def is_organization(self) -> bool:
        """
        Método de dominio: verifica si la entidad es una organización.
        
        Returns:
            True si type es ORGANIZATION u ORG
        """
        return self.type.upper() in ("ORGANIZATION", "ORG")




