"""Semantic graph models."""

from enum import Enum
from typing import Any

from pydantic import BaseModel


class GraphNodeType(str, Enum):
    """Node types in the semantic graph."""

    REPOSITORY = "repository"
    FOLDER = "folder"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    ROUTE = "route"
    DATABASE = "database"
    DEPENDENCY = "dependency"
    CONFIG = "config"


class GraphNode(BaseModel):
    """A node in the semantic graph."""

    id: str
    type: GraphNodeType
    name: str
    metadata: dict[str, Any] = {}


class GraphEdge(BaseModel):
    """An edge in the semantic graph."""

    source: str
    target: str
    relationship: str


class SemanticGraph(BaseModel):
    """Complete semantic graph of a repository."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    root_id: str
