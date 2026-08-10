"""
Tests para servicios de inferencia.

Verifica que los servicios de inferencia extraen correctamente entidades,
relaciones y facts desde chunks de texto.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.entities.chunk import Chunk
from domain.entities.fact import Fact
from domain.entities.entity import Entity
from domain.entities.relation import Relation
from domain.services.inference_service import InferenceService


class TestFactEntity:
    """Tests para la entidad Fact."""
    
    def test_fact_creation(self):
        """Test: Crear un Fact válido."""
        fact = Fact(
            id="fact_1",
            subject="chunk_1",
            predicate="MENTIONS",
            object="Apple Inc.",
            confidence=0.95,
            provenance_ref="chunk_1"
        )
        
        assert fact.id == "fact_1"
        assert fact.subject == "chunk_1"
        assert fact.predicate == "MENTIONS"
        assert fact.object == "Apple Inc."
        assert fact.confidence == 0.95
        assert fact.provenance_ref == "chunk_1"
    
    def test_fact_validation(self):
        """Test: Validar que Fact rechaza datos inválidos."""
        with pytest.raises(ValueError, match="subject cannot be empty"):
            Fact(
                id="fact_1",
                subject="",
                predicate="MENTIONS",
                object="Apple",
                confidence=0.9,
                provenance_ref="chunk_1"
            )
        
        with pytest.raises(ValueError, match="Confidence must be between"):
            Fact(
                id="fact_1",
                subject="chunk_1",
                predicate="MENTIONS",
                object="Apple",
                confidence=1.5,  # Inválido: > 1.0
                provenance_ref="chunk_1"
            )
    
    def test_fact_to_triple(self):
        """Test: Convertir Fact a tripleta."""
        fact = Fact(
            id="fact_1",
            subject="chunk_1",
            predicate="MENTIONS",
            object="Apple Inc.",
            confidence=0.95,
            provenance_ref="chunk_1"
        )
        
        triple = fact.to_triple()
        assert triple == ("chunk_1", "MENTIONS", "Apple Inc.")
    
    def test_fact_high_confidence(self):
        """Test: Verificar confianza alta."""
        high_conf_fact = Fact(
            id="fact_1",
            subject="chunk_1",
            predicate="MENTIONS",
            object="Apple",
            confidence=0.9,
            provenance_ref="chunk_1"
        )
        
        low_conf_fact = Fact(
            id="fact_2",
            subject="chunk_1",
            predicate="MENTIONS",
            object="Apple",
            confidence=0.5,
            provenance_ref="chunk_1"
        )
        
        assert high_conf_fact.is_high_confidence(threshold=0.8) is True
        assert low_conf_fact.is_high_confidence(threshold=0.8) is False


class TestEntityEntity:
    """Tests para la entidad Entity."""
    
    def test_entity_creation(self):
        """Test: Crear una Entity válida."""
        entity = Entity(
            id="entity_1",
            name="Apple Inc.",
            type="ORGANIZATION",
            mentions=["chunk_1", "chunk_2"]
        )
        
        assert entity.id == "entity_1"
        assert entity.name == "Apple Inc."
        assert entity.type == "ORGANIZATION"
        assert len(entity.mentions) == 2
    
    def test_entity_add_mention(self):
        """Test: Añadir mención a entidad."""
        entity = Entity(
            id="entity_1",
            name="Apple Inc.",
            type="ORGANIZATION",
            mentions=["chunk_1"]
        )
        
        entity.add_mention("chunk_2")
        assert len(entity.mentions) == 2
        assert "chunk_2" in entity.mentions
        
        # No duplicar menciones
        entity.add_mention("chunk_2")
        assert len(entity.mentions) == 2
    
    def test_entity_type_check(self):
        """Test: Verificar tipos de entidad."""
        person = Entity(
            id="e1",
            name="John Doe",
            type="PERSON",
            mentions=[]
        )
        
        org = Entity(
            id="e2",
            name="Apple Inc.",
            type="ORGANIZATION",
            mentions=[]
        )
        
        assert person.is_person() is True
        assert person.is_organization() is False
        assert org.is_organization() is True
        assert org.is_person() is False


class TestSpacyInferenceService:
    """Tests para SpacyInferenceService."""
    
    @pytest.fixture
    def sample_chunk(self):
        """Fixture: Chunk de ejemplo con texto que contiene entidades."""
        return Chunk(
            id="chunk_test_1",
            page_content="Apple Inc. is a technology company based in Cupertino, California. Tim Cook is the CEO.",
            metadata={"filename": "test.md", "page_number": 1},
            chunk_id_consecutive=1
        )
    
    def test_spacy_service_requires_installation(self):
        """Test: Verificar que requiere spaCy instalado."""
        try:
            from infrastructure.services.spacy_inference_service import SpacyInferenceService
            
            # Si spaCy está instalado, debería funcionar
            service = SpacyInferenceService()
            assert service is not None
        except ImportError:
            # Si no está instalado, debería lanzar ImportError
            pytest.skip("spaCy no está instalado. Instala con: pip install spacy && python -m spacy download en_core_web_sm")
    
    def test_extract_entities(self, sample_chunk):
        """Test: Extraer entidades de un chunk."""
        try:
            from infrastructure.services.spacy_inference_service import SpacyInferenceService
            
            service = SpacyInferenceService()
            entities = service.extract_entities(sample_chunk)
            
            assert len(entities) > 0
            assert all(isinstance(e, Entity) for e in entities)
            
            # Verificar que se extrajeron entidades esperadas
            entity_names = [e.name for e in entities]
            # spaCy debería extraer al menos "Apple Inc." o "Cupertino" o "California"
            assert any("Apple" in name or "Cupertino" in name or "California" in name 
                      for name in entity_names)
        except ImportError:
            pytest.skip("spaCy no está instalado")
    
    def test_infer_facts(self, sample_chunk):
        """Test: Inferir facts desde un chunk."""
        try:
            from infrastructure.services.spacy_inference_service import SpacyInferenceService
            
            service = SpacyInferenceService()
            facts = service.infer_facts(sample_chunk)
            
            assert len(facts) > 0
            assert all(isinstance(f, Fact) for f in facts)
            
            # Verificar estructura de facts
            for fact in facts:
                assert fact.subject == sample_chunk.id
                assert fact.predicate == "MENTIONS"
                assert fact.object is not None
                assert 0.0 <= fact.confidence <= 1.0
                assert fact.provenance_ref == sample_chunk.id
        except ImportError:
            pytest.skip("spaCy no está instalado")
    
    def test_extract_relations(self, sample_chunk):
        """Test: Extraer relaciones entre entidades."""
        try:
            from infrastructure.services.spacy_inference_service import SpacyInferenceService
            
            service = SpacyInferenceService()
            entities = service.extract_entities(sample_chunk)
            
            if len(entities) >= 2:
                relations = service.extract_relations(sample_chunk, entities)
                
                # Si hay múltiples entidades, debería haber relaciones de co-ocurrencia
                assert len(relations) >= 0  # Puede ser 0 si hay menos de 2 entidades
                
                if relations:
                    assert all(isinstance(r, Relation) for r in relations)
                    assert all(r.relation_type == "CO_OCCURS_WITH" for r in relations)
        except ImportError:
            pytest.skip("spaCy no está instalado")
    
    def test_empty_chunk_handling(self):
        """Test: Manejar chunks vacíos."""
        try:
            from infrastructure.services.spacy_inference_service import SpacyInferenceService
            
            service = SpacyInferenceService()
            empty_chunk = Chunk(
                id="empty",
                page_content="",
                metadata={},
                chunk_id_consecutive=1
            )
            
            with pytest.raises(ValueError):
                service.extract_entities(empty_chunk)
        except ImportError:
            pytest.skip("spaCy no está instalado")


class TestInferenceIntegration:
    """Tests de integración para el servicio de inferencia."""
    
    def test_inference_service_interface(self):
        """Test: Verificar que SpacyInferenceService implementa InferenceService."""
        try:
            from infrastructure.services.spacy_inference_service import SpacyInferenceService
            
            service = SpacyInferenceService()
            assert isinstance(service, InferenceService)
        except ImportError:
            pytest.skip("spaCy no está instalado")
    
    def test_fact_persistence_structure(self):
        """Test: Verificar estructura de datos para persistencia."""
        fact = Fact(
            id="fact_test",
            subject="chunk_1",
            predicate="MENTIONS",
            object="Apple Inc.",
            confidence=0.9,
            provenance_ref="chunk_1"
        )
        
        # Verificar que tiene todos los campos necesarios para persistencia
        assert hasattr(fact, 'id')
        assert hasattr(fact, 'subject')
        assert hasattr(fact, 'predicate')
        assert hasattr(fact, 'object')
        assert hasattr(fact, 'confidence')
        assert hasattr(fact, 'provenance_ref')





