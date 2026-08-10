"""
Integration tests for LLMInferenceService.

These tests use real LLM calls (Ollama) and should be run separately
from unit tests to avoid latency and API dependencies.

Run with: pytest tests/test_llm_inference_integration.py -m integration
"""

import pytest
from src.core.configuration import Settings
from src.application.dependencies import create_inference_service
from src.domain.entities.chunk import Chunk


@pytest.mark.integration
@pytest.mark.skipif(
    not Settings().ollama_model,
    reason="Ollama not configured (UNGRAPH_OLLAMA_MODEL not set)",
)
class TestLLMInferenceIntegration:
    """Integration tests requiring live Ollama instance."""
    
    def test_create_llm_inference_service(self):
        """Test factory creates LLMInferenceService for LLM mode."""
        # Arrange
        settings = Settings(inference_mode="llm")
        
        # Act
        service = create_inference_service(settings)
        
        # Assert
        assert service is not None
        assert service.__class__.__name__ == "LLMInferenceService"
    
    def test_extract_entities_real_llm(self):
        """Test entity extraction with real LLM."""
        # Arrange
        settings = Settings(inference_mode="llm")
        service = create_inference_service(settings)
        
        # Skip if service could not be created
        if service is None:
            pytest.skip("LLMInferenceService could not be created (missing dependencies or config)")
        
        chunk = Chunk(
            id="test_chunk",
            page_content="Elon Musk founded SpaceX in California.",
            metadata={},
        )
        
        # Act
        entities = service.extract_entities(chunk)
        
        # Assert
        assert len(entities) > 0
        entity_names = [e.name for e in entities]
        # LLM should extract at least Elon Musk and SpaceX
        assert any("Elon Musk" in name or "Musk" in name for name in entity_names)
        assert any("SpaceX" in name for name in entity_names)
    
    def test_extract_relations_real_llm(self):
        """Test relation extraction with real LLM."""
        # Arrange
        settings = Settings(inference_mode="llm")
        service = create_inference_service(settings)
        
        # Skip if service could not be created
        if service is None:
            pytest.skip("LLMInferenceService could not be created (missing dependencies or config)")
        
        chunk = Chunk(
            id="test_chunk",
            page_content="Alice works at Google in Mountain View.",
            metadata={},
        )
        
        # Act
        entities = service.extract_entities(chunk)
        relations = service.extract_relations(chunk, entities)
        
        # Assert
        assert len(relations) > 0
        relation_types = [r.relation_type for r in relations]
        # LLM should extract WORKS_FOR or similar relation
        assert any(
            rel_type in ["WORKS_FOR", "EMPLOYED_BY", "WORKS_AT"]
            for rel_type in relation_types
        )
    
    def test_infer_facts_real_llm(self):
        """Test fact inference with real LLM."""
        # Arrange
        settings = Settings(inference_mode="llm")
        service = create_inference_service(settings)
        
        # Skip if service could not be created
        if service is None:
            pytest.skip("LLMInferenceService could not be created (missing dependencies or config)")
        
        chunk = Chunk(
            id="test_chunk",
            page_content="Microsoft released Windows 11.",
            metadata={},
        )
        
        # Act
        facts = service.infer_facts(chunk)
        
        # Assert
        assert len(facts) > 0
        assert all(f.predicate == "MENTIONS" for f in facts)
        assert all(f.subject == "test_chunk" for f in facts)
        fact_objects = [f.object for f in facts]
        # Should have MENTIONS facts for Microsoft and Windows
        assert any("Microsoft" in obj for obj in fact_objects)


@pytest.mark.integration
class TestLLMInferenceConfigValidation:
    """Test configuration validation for LLM inference."""
    
    def test_create_llm_service_missing_model(self):
        """Test that service creation fails gracefully without model config."""
        # Arrange
        settings = Settings(inference_mode="llm", ollama_model=None)
        
        # Act
        service = create_inference_service(settings)
        
        # Assert: Should return None with warning
        assert service is None
    
    def test_create_ner_service_fallback(self):
        """Test that NER mode still works (no LLM required)."""
        # Arrange
        settings = Settings(inference_mode="ner")
        
        # Act
        service = create_inference_service(settings, language="en")
        
        # Assert: Should create SpacyInferenceService or None (if spaCy not available)
        # Both outcomes are acceptable for this test
        if service is not None:
            assert service.__class__.__name__ == "SpacyInferenceService"
    
    def test_hybrid_mode_not_implemented(self):
        """Test that hybrid mode raises NotImplementedError."""
        # Arrange
        settings = Settings(inference_mode="hybrid")
        
        # Act & Assert
        with pytest.raises(NotImplementedError, match="Hybrid inference mode"):
            create_inference_service(settings)
    
    def test_invalid_mode(self):
        """Test that invalid mode raises ValueError."""
        # Arrange
        settings = Settings(inference_mode="invalid_mode")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid inference_mode"):
            create_inference_service(settings)
