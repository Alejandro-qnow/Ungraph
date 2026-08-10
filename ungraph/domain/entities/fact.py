"""
Entidad de Dominio: Fact

Representa un hecho extraído mediante inferencia desde un chunk.
Un fact es una tripleta (subject-predicate-object) con confianza y trazabilidad.

En Clean Architecture, las entidades:
- Contienen SOLO datos (atributos)
- Pueden tener lógica de negocio básica (validaciones)
- NO conocen frameworks externos
- NO saben cómo persistirse

Ejemplo de uso:
    fact = Fact(
        id="fact_123",
        subject="chunk_1",
        predicate="MENTIONS",
        object="Apple Inc.",
        confidence=0.95,
        provenance_ref="chunk_1"
    )
"""

from dataclasses import dataclass
from typing import Optional

from ungraph.domain.value_objects.curation_state import normalize_curation_state


@dataclass
class Fact:
    """
    Entidad que representa un hecho extraído mediante inferencia.
    
    Un fact es una tripleta estructurada que representa conocimiento
    derivado de un chunk de texto. Incluye información de confianza
    y trazabilidad para validación y auditoría.
    
    Attributes:
        id: Identificador único del fact
        subject: Sujeto de la tripleta (típicamente chunk_id o entidad)
        predicate: Predicado/relación (ej: "MENTIONS", "LOCATED_IN", etc.)
        object: Objeto de la tripleta (típicamente entidad o valor)
        confidence: Nivel de confianza (0.0-1.0)
        provenance_ref: Referencia al chunk origen (para trazabilidad PROV-O)
        object_entity_type: Si ``predicate`` es MENTIONS, tipo de la entidad objeto (opcional)
        object_ontology_class_uri: Si ``predicate`` es MENTIONS, IRI de clase OWL (opcional)
        curation_state: Ciclo de vida de validación: Extracted | Curated | Invalid
    """
    id: str
    subject: str
    predicate: str
    object: str
    confidence: float
    provenance_ref: str
    object_entity_type: Optional[str] = None
    object_ontology_class_uri: Optional[str] = None
    curation_state: str = "Extracted"
    
    def __post_init__(self):
        """
        Validaciones básicas de negocio después de crear la instancia.
        """
        if not self.id:
            raise ValueError("Fact id cannot be empty")
        if not self.subject:
            raise ValueError("Fact subject cannot be empty")
        if not self.predicate:
            raise ValueError("Fact predicate cannot be empty")
        if not self.object:
            raise ValueError("Fact object cannot be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if not self.provenance_ref:
            raise ValueError("Fact provenance_ref cannot be empty")
        object.__setattr__(self, "curation_state", normalize_curation_state(self.curation_state))
    
    def to_triple(self) -> tuple[str, str, str]:
        """
        Método de dominio: convierte el fact a una tripleta.
        
        Returns:
            Tupla (subject, predicate, object)
        """
        return (self.subject, self.predicate, self.object)
    
    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """
        Método de dominio: verifica si el fact tiene alta confianza.
        
        Args:
            threshold: Umbral de confianza (default: 0.8)
        
        Returns:
            True si confidence >= threshold
        """
        return self.confidence >= threshold




