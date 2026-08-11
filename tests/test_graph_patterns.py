"""
Tests para Value Objects de patrones de grafo.

Valida que los Value Objects funcionan correctamente y tienen
las validaciones necesarias.
"""

"""
Tests para Value Objects de patrones de grafo.

Valida que los Value Objects funcionan correctamente y tienen
las validaciones necesarias.
"""

import pytest
import sys
from pathlib import Path

# Agregar src al path sin importar src.__init__.py
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Importar directamente desde el módulo
from domain.value_objects.graph_pattern import (
    NodeDefinition,
    RelationshipDefinition,
    GraphPattern
)


class TestNodeDefinition:
    """Tests para NodeDefinition."""
    
    def test_create_valid_node_definition(self):
        """Test: Crear un NodeDefinition válido."""
        node = NodeDefinition(
            label="File",
            required_properties={"filename": str},
            optional_properties={"createdAt": int},
            indexes=["filename"]
        )
        
        assert node.label == "File"
        assert "filename" in node.required_properties
        assert "createdAt" in node.optional_properties
        assert "filename" in node.indexes
    
    def test_node_definition_empty_label_raises_error(self):
        """Test: NodeDefinition con label vacío debe lanzar error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            NodeDefinition(label="")
    
    def test_node_definition_invalid_label_format(self):
        """Test: NodeDefinition con formato de label inválido."""
        with pytest.raises(ValueError, match="Invalid label format"):
            NodeDefinition(label="file")  # Debe empezar con mayúscula
        
        with pytest.raises(ValueError, match="Invalid label format"):
            NodeDefinition(label="file-name")  # No puede tener guiones
    
    def test_node_definition_invalid_property_name(self):
        """Test: NodeDefinition con nombre de propiedad inválido."""
        with pytest.raises(ValueError, match="Invalid property name"):
            NodeDefinition(
                label="File",
                required_properties={"file-name": str}  # Nombre inválido
            )
    
    def test_node_definition_index_not_in_properties(self):
        """Test: NodeDefinition con índice que no existe en propiedades."""
        with pytest.raises(ValueError, match="not found in node properties"):
            NodeDefinition(
                label="File",
                required_properties={"filename": str},
                indexes=["nonexistent"]  # Propiedad que no existe
            )


class TestRelationshipDefinition:
    """Tests para RelationshipDefinition."""
    
    def test_create_valid_relationship_definition(self):
        """Test: Crear un RelationshipDefinition válido."""
        rel = RelationshipDefinition(
            from_node="File",
            to_node="Page",
            relationship_type="CONTAINS",
            direction="OUTGOING"
        )
        
        assert rel.from_node == "File"
        assert rel.to_node == "Page"
        assert rel.relationship_type == "CONTAINS"
        assert rel.direction == "OUTGOING"
    
    def test_relationship_definition_empty_fields_raise_error(self):
        """Test: RelationshipDefinition con campos vacíos debe lanzar error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            RelationshipDefinition(from_node="", to_node="Page", relationship_type="CONTAINS")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            RelationshipDefinition(from_node="File", to_node="", relationship_type="CONTAINS")
        
        with pytest.raises(ValueError, match="cannot be empty"):
            RelationshipDefinition(from_node="File", to_node="Page", relationship_type="")
    
    def test_relationship_definition_invalid_type_format(self):
        """Test: RelationshipDefinition con formato de tipo inválido."""
        with pytest.raises(ValueError, match="Invalid relationship_type format"):
            RelationshipDefinition(
                from_node="File",
                to_node="Page",
                relationship_type="contains"  # Debe ser mayúsculas
            )
    
    def test_relationship_definition_invalid_direction(self):
        """Test: RelationshipDefinition con dirección inválida."""
        with pytest.raises(ValueError, match="Invalid direction"):
            RelationshipDefinition(
                from_node="File",
                to_node="Page",
                relationship_type="CONTAINS",
                direction="BIDIRECTIONAL"  # No válido
            )


class TestGraphPattern:
    """Tests para GraphPattern."""
    
    def test_create_valid_graph_pattern(self):
        """Test: Crear un GraphPattern válido."""
        file_node = NodeDefinition(
            label="File",
            required_properties={"filename": str},
            indexes=["filename"]
        )
        page_node = NodeDefinition(
            label="Page",
            required_properties={"filename": str, "page_number": int},
            indexes=["filename"]
        )
        
        contains_rel = RelationshipDefinition(
            from_node="File",
            to_node="Page",
            relationship_type="CONTAINS"
        )
        
        pattern = GraphPattern(
            name="FILE_PAGE",
            description="File contiene Page",
            node_definitions=[file_node, page_node],
            relationship_definitions=[contains_rel]
        )
        
        assert pattern.name == "FILE_PAGE"
        assert len(pattern.node_definitions) == 2
        assert len(pattern.relationship_definitions) == 1
    
    def test_graph_pattern_empty_name_raises_error(self):
        """Test: GraphPattern con nombre vacío debe lanzar error."""
        node = NodeDefinition(label="File", required_properties={})
        
        with pytest.raises(ValueError, match="cannot be empty"):
            GraphPattern(
                name="",
                description="Test",
                node_definitions=[node],
                relationship_definitions=[]
            )
    
    def test_graph_pattern_no_nodes_raises_error(self):
        """Test: GraphPattern sin nodos debe lanzar error."""
        with pytest.raises(ValueError, match="at least one node definition"):
            GraphPattern(
                name="EMPTY",
                description="Empty pattern",
                node_definitions=[],
                relationship_definitions=[]
            )
    
    def test_graph_pattern_invalid_relationship_reference(self):
        """Test: GraphPattern con relación que referencia nodo inexistente."""
        file_node = NodeDefinition(label="File", required_properties={})
        
        invalid_rel = RelationshipDefinition(
            from_node="File",
            to_node="Nonexistent",  # Nodo que no existe
            relationship_type="CONTAINS"
        )
        
        with pytest.raises(ValueError, match="references unknown node"):
            GraphPattern(
                name="INVALID",
                description="Invalid pattern",
                node_definitions=[file_node],
                relationship_definitions=[invalid_rel]
            )

