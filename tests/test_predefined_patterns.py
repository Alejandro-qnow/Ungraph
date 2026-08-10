"""
Tests para patrones predefinidos.

Valida que los patrones predefinidos son correctos y reflejan
el código actual del sistema.
"""

import pytest
import sys
from pathlib import Path

# Agregar src al path sin importar src.__init__.py
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from domain.value_objects.predefined_patterns import FILE_PAGE_CHUNK_PATTERN
from domain.value_objects.graph_pattern import GraphPattern


class TestPredefinedPatterns:
    """Tests para patrones predefinidos."""
    
    def test_file_page_chunk_pattern_exists(self):
        """Test: FILE_PAGE_CHUNK_PATTERN existe y es válido."""
        assert FILE_PAGE_CHUNK_PATTERN is not None
        assert isinstance(FILE_PAGE_CHUNK_PATTERN, GraphPattern)
        assert FILE_PAGE_CHUNK_PATTERN.name == "FILE_PAGE_CHUNK"
    
    def test_file_page_chunk_pattern_has_three_nodes(self):
        """Test: FILE_PAGE_CHUNK_PATTERN tiene 3 tipos de nodos."""
        assert len(FILE_PAGE_CHUNK_PATTERN.node_definitions) == 3
        
        node_labels = {node.label for node in FILE_PAGE_CHUNK_PATTERN.node_definitions}
        assert "File" in node_labels
        assert "Page" in node_labels
        assert "Chunk" in node_labels
    
    def test_file_page_chunk_pattern_has_correct_properties(self):
        """Test: FILE_PAGE_CHUNK_PATTERN tiene las propiedades correctas."""
        # Encontrar nodo File
        file_node = next(
            node for node in FILE_PAGE_CHUNK_PATTERN.node_definitions 
            if node.label == "File"
        )
        assert "filename" in file_node.required_properties
        
        # Encontrar nodo Chunk
        chunk_node = next(
            node for node in FILE_PAGE_CHUNK_PATTERN.node_definitions 
            if node.label == "Chunk"
        )
        assert "chunk_id" in chunk_node.required_properties
        assert "page_content" in chunk_node.required_properties
        assert "embeddings" in chunk_node.required_properties
        assert "chunk_id_consecutive" in chunk_node.optional_properties
    
    def test_file_page_chunk_pattern_has_correct_relationships(self):
        """Test: FILE_PAGE_CHUNK_PATTERN tiene las relaciones correctas."""
        assert len(FILE_PAGE_CHUNK_PATTERN.relationship_definitions) == 3
        
        rel_types = {rel.relationship_type for rel in FILE_PAGE_CHUNK_PATTERN.relationship_definitions}
        assert "CONTAINS" in rel_types
        assert "HAS_CHUNK" in rel_types
        assert "NEXT_CHUNK" in rel_types
    
    def test_file_page_chunk_pattern_relationships_reference_valid_nodes(self):
        """Test: Todas las relaciones referencian nodos válidos."""
        node_labels = {node.label for node in FILE_PAGE_CHUNK_PATTERN.node_definitions}
        
        for rel in FILE_PAGE_CHUNK_PATTERN.relationship_definitions:
            assert rel.from_node in node_labels, f"Relationship {rel.relationship_type} references unknown from_node: {rel.from_node}"
            assert rel.to_node in node_labels, f"Relationship {rel.relationship_type} references unknown to_node: {rel.to_node}"








