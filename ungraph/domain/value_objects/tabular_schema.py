"""
Value Objects: Esquema tabular inferido (CSV / XLSX → grafo de conocimiento).

Estos objetos representan el resultado de la fase de *inferencia de esquema* del modo
Schema-Guided Ingestion (SGI): por cada columna se decide si es un nodo, un atributo o
una relación. El resultado es un ``TabularSchemaProposal`` que el usuario puede confirmar
o editar, y del cual se deriva declarativamente un ``GraphPattern`` (reutilizando la
abstracción existente en ``graph_pattern.py``).

Principios (ver skill kg-schema):
- **Nodo**: entidad con identidad propia (la fila; o una dimensión categórica; o una FK).
- **Relación**: vínculo entre el nodo-fila y un nodo dimensión/FK.
- **Propiedad**: atributo escalar del nodo-fila sin vida propia.

El dominio no conoce pandas ni Neo4j: solo describe la estructura objetivo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ungraph.domain.value_objects.graph_pattern import (
    GraphPattern,
    NodeDefinition,
    RelationshipDefinition,
)


class ColumnRole(str, Enum):
    """Rol inferido de una columna dentro del grafo de conocimiento."""

    NODE_KEY = "node_key"          # identidad natural del nodo-fila
    ATTRIBUTE = "attribute"        # propiedad escalar del nodo-fila
    DIMENSION_NODE = "dimension"   # categórica de baja cardinalidad → nodo + relación
    RELATION_FK = "relation_fk"    # clave foránea → nodo referenciado + relación
    IGNORE = "ignore"              # columna descartada del modelado


def sanitize_label(name: str) -> str:
    """Convierte un nombre arbitrario a un label Neo4j válido (PascalCase).

    Labels válidos: ``^[A-Z][a-zA-Z0-9_]*$`` (ver ``NodeDefinition``).
    """
    tokens = re.split(r"[^0-9a-zA-Z]+", str(name).strip())
    parts = [t for t in tokens if t]
    if not parts:
        return "Node"
    label = "".join(p[:1].upper() + p[1:] for p in parts)
    if not re.match(r"^[A-Z]", label):
        label = "N" + label
    return label


def sanitize_property(name: str) -> str:
    """Convierte un nombre de columna a un nombre de propiedad Neo4j válido.

    Propiedades válidas: ``^[a-zA-Z_][a-zA-Z0-9_]*$`` (ver ``NodeDefinition``).
    """
    prop = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower()).strip("_")
    if not prop:
        return "value"
    if not re.match(r"^[a-zA-Z_]", prop):
        prop = "_" + prop
    return prop


def sanitize_relationship_type(name: str) -> str:
    """Convierte un nombre a un tipo de relación válido (MAYUSCULAS_SNAKE)."""
    rel = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip()).strip("_").upper()
    if not rel:
        return "RELATED_TO"
    if not re.match(r"^[A-Z]", rel):
        rel = "R_" + rel
    return rel


@dataclass(frozen=True)
class ColumnProfile:
    """Perfil determinista de una columna (fase Profile, sin LLM).

    Attributes:
        name: Nombre original de la columna.
        dtype_inferred: Tipo inferido ("int", "float", "str", "bool", "date", "mixed").
        cardinality: Nº de valores distintos no nulos.
        unique_ratio: distintos / total no nulos (1.0 ⇒ candidata a clave).
        null_ratio: nulos / total.
        n_rows: Nº total de filas perfiladas.
        sample_values: Muestra de valores (para el prompt LLM y auditoría).
        name_signals: Señales del nombre (is_id_like, is_date_like, is_fk_like, ...).
    """

    name: str
    dtype_inferred: str
    cardinality: int
    unique_ratio: float
    null_ratio: float
    n_rows: int
    sample_values: List[Any] = field(default_factory=list)
    name_signals: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dtype_inferred": self.dtype_inferred,
            "cardinality": self.cardinality,
            "unique_ratio": round(self.unique_ratio, 4),
            "null_ratio": round(self.null_ratio, 4),
            "n_rows": self.n_rows,
            "sample_values": list(self.sample_values),
            "name_signals": dict(self.name_signals),
        }


@dataclass(frozen=True)
class ColumnMapping:
    """Decisión de mapeo para una columna.

    Attributes:
        column: Nombre original de la columna.
        role: Rol asignado (ColumnRole).
        confidence: Confianza [0, 1] de la decisión.
        decided_by: "heuristic" | "llm".
        rationale: Justificación breve (auditable).
        property_name: Nombre de propiedad (roles NODE_KEY/ATTRIBUTE). Si None, se deriva.
        target_label: Label del nodo destino (roles DIMENSION_NODE/RELATION_FK).
        relationship_type: Tipo de relación (roles DIMENSION_NODE/RELATION_FK).
        target_key_property: Propiedad clave del nodo destino. Si None, se deriva.
    """

    column: str
    role: ColumnRole
    confidence: float = 1.0
    decided_by: str = "heuristic"
    rationale: str = ""
    property_name: Optional[str] = None
    target_label: Optional[str] = None
    relationship_type: Optional[str] = None
    target_key_property: Optional[str] = None

    # --- derivaciones convenientes -----------------------------------------
    def resolved_property_name(self) -> str:
        return self.property_name or sanitize_property(self.column)

    def resolved_target_label(self) -> str:
        return sanitize_label(self.target_label or self.column)

    def resolved_relationship_type(self) -> str:
        if self.relationship_type:
            return sanitize_relationship_type(self.relationship_type)
        return sanitize_relationship_type(f"HAS_{self.column}")

    def resolved_target_key_property(self) -> str:
        return self.target_key_property or sanitize_property(self.column)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "column": self.column,
            "role": self.role.value,
            "confidence": round(self.confidence, 4),
            "decided_by": self.decided_by,
            "rationale": self.rationale,
            "property_name": self.property_name,
            "target_label": self.target_label,
            "relationship_type": self.relationship_type,
            "target_key_property": self.target_key_property,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ColumnMapping":
        return cls(
            column=data["column"],
            role=ColumnRole(data["role"]),
            confidence=float(data.get("confidence", 1.0)),
            decided_by=data.get("decided_by", "heuristic"),
            rationale=data.get("rationale", ""),
            property_name=data.get("property_name"),
            target_label=data.get("target_label"),
            relationship_type=data.get("relationship_type"),
            target_key_property=data.get("target_key_property"),
        )


@dataclass(frozen=True)
class TabularSchemaProposal:
    """Propuesta completa de mapeo de una tabla a grafo (editable por el usuario).

    Attributes:
        source: Identificador de la fuente (archivo/hoja/tabla).
        row_node_label: Label del nodo-fila (entidad principal de la tabla).
        row_key_columns: Columnas que forman la clave natural del nodo-fila.
            Si está vacío, la persistencia usa una clave sintética (hash de fila).
        columns: Mapeo por columna.
    """

    source: str
    row_node_label: str
    row_key_columns: List[str] = field(default_factory=list)
    columns: List[ColumnMapping] = field(default_factory=list)

    # --- accesores por rol -------------------------------------------------
    def mappings_by_role(self, role: ColumnRole) -> List[ColumnMapping]:
        return [c for c in self.columns if c.role == role]

    @property
    def resolved_row_label(self) -> str:
        return sanitize_label(self.row_node_label)

    def row_key_property_names(self) -> List[str]:
        """Propiedades clave del nodo-fila (naturales o sintética)."""
        if self.row_key_columns:
            return [sanitize_property(c) for c in self.row_key_columns]
        return ["row_uid"]

    def attribute_property_names(self) -> List[str]:
        props: List[str] = []
        for c in self.columns:
            if c.role in (ColumnRole.ATTRIBUTE, ColumnRole.NODE_KEY):
                props.append(c.resolved_property_name())
        return props

    # --- derivación al patrón declarativo existente ------------------------
    def to_graph_pattern(self) -> GraphPattern:
        """Deriva un ``GraphPattern`` (NodeDefinition/RelationshipDefinition).

        El patrón declara la *estructura objetivo*: sirve para validación,
        constraints/índices y documentación. La materialización fila→grafo se
        realiza en la persistencia (``save_tabular``) usando este proposal.
        """
        row_label = self.resolved_row_label
        key_props = self.row_key_property_names()

        # Propiedades del nodo-fila: claves (requeridas) + atributos (opcionales).
        required_props: Dict[str, type] = {k: str for k in key_props}
        optional_props: Dict[str, type] = {}
        for c in self.columns:
            if c.role == ColumnRole.ATTRIBUTE:
                optional_props[c.resolved_property_name()] = str
            elif c.role == ColumnRole.NODE_KEY:
                # NODE_KEY que no está en row_key_columns se guarda como propiedad.
                pname = c.resolved_property_name()
                if pname not in required_props:
                    optional_props[pname] = str

        node_defs: List[NodeDefinition] = [
            NodeDefinition(
                label=row_label,
                required_properties=required_props,
                optional_properties=optional_props,
                indexes=list(key_props),
            )
        ]
        rel_defs: List[RelationshipDefinition] = []

        # Nodos dimensión / FK + relaciones (evitando labels duplicados).
        seen_labels = {row_label}
        for c in self.columns:
            if c.role not in (ColumnRole.DIMENSION_NODE, ColumnRole.RELATION_FK):
                continue
            target_label = c.resolved_target_label()
            key_prop = c.resolved_target_key_property()
            if target_label not in seen_labels:
                node_defs.append(
                    NodeDefinition(
                        label=target_label,
                        required_properties={key_prop: str},
                        indexes=[key_prop],
                    )
                )
                seen_labels.add(target_label)
            rel_defs.append(
                RelationshipDefinition(
                    from_node=row_label,
                    to_node=target_label,
                    relationship_type=c.resolved_relationship_type(),
                    direction="OUTGOING",
                )
            )

        return GraphPattern(
            name=f"TABULAR_{sanitize_relationship_type(self.source)}",
            description=f"Patrón tabular inferido desde '{self.source}'",
            node_definitions=node_defs,
            relationship_definitions=rel_defs,
            search_patterns=["basic"],
        )

    # --- serialización (confirmar/editar vía YAML/JSON) --------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "row_node_label": self.row_node_label,
            "row_key_columns": list(self.row_key_columns),
            "columns": [c.to_dict() for c in self.columns],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TabularSchemaProposal":
        return cls(
            source=data["source"],
            row_node_label=data["row_node_label"],
            row_key_columns=list(data.get("row_key_columns", [])),
            columns=[ColumnMapping.from_dict(c) for c in data.get("columns", [])],
        )
