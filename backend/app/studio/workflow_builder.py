"""Visual workflow builder service for providing node/edge data to the frontend."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.core.logging import get_logger
import uuid

logger = get_logger(__name__)


class NodeType(str, Enum):
    """Workflow node types."""

    START = "start"
    PLANNER = "planner"
    SUPERVISOR = "supervisor"
    AGENT = "agent"
    DECISION = "decision"
    APPROVAL = "approval"
    REFLECTION = "reflection"
    TOOL = "tool"
    MEMORY = "memory"
    EXECUTION = "execution"
    END = "end"


@dataclass
class NodePosition:
    """X/Y coordinates for a node on the canvas."""

    x: float
    y: float


@dataclass
class WorkflowNode:
    """A single node in a workflow graph."""

    id: str
    type: NodeType
    label: str
    position: NodePosition
    data: dict[str, Any] = field(default_factory=dict)
    status: str = "idle"


@dataclass
class WorkflowEdge:
    """A directed edge connecting two nodes."""

    id: str
    source: str
    target: str
    label: str = ""
    condition: str | None = None


@dataclass
class WorkflowGraph:
    """Complete visual graph for a workflow."""

    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    viewport: dict[str, Any] = field(default_factory=lambda: {"x": 0, "y": 0, "zoom": 1})


class WorkflowBuilderService:
    """Service for managing visual workflow graphs.

    Stores graphs in-memory and provides CRUD operations for
    nodes and edges used by the frontend workflow builder.
    """

    def __init__(self) -> None:
        self._graphs: dict[str, WorkflowGraph] = {}

    async def get_workflow_graph(self, workflow_id: str) -> WorkflowGraph:
        """Get visual graph from workflow data.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            The WorkflowGraph for the given workflow.
        """
        graph = self._graphs.get(workflow_id)
        if graph is not None:
            return graph

        graph = self._generate_default_graph(workflow_id)
        self._graphs[workflow_id] = graph
        return graph

    async def create_workflow_from_graph(self, graph: WorkflowGraph) -> dict[str, Any]:
        """Convert a visual graph to workflow definition data.

        Args:
            graph: The WorkflowGraph to convert.

        Returns:
            Workflow definition dictionary.
        """
        workflow_id = str(uuid.uuid4())
        self._graphs[workflow_id] = graph

        tasks = []
        for node in graph.nodes:
            if node.type in (
                NodeType.AGENT,
                NodeType.TOOL,
                NodeType.EXECUTION,
                NodeType.PLANNER,
                NodeType.SUPERVISOR,
            ):
                tasks.append({
                    "id": node.id,
                    "title": node.label,
                    "type": node.type.value,
                    "dependencies": [
                        e.source for e in graph.edges if e.target == node.id
                    ],
                    "data": node.data,
                })

        workflow = {
            "id": workflow_id,
            "tasks": tasks,
            "metadata": {
                "created_at": datetime.now(UTC).isoformat(),
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
            },
        }

        logger.info(
            "Created workflow from graph: id=%s nodes=%d edges=%d",
            workflow_id[:8],
            len(graph.nodes),
            len(graph.edges),
        )

        return workflow

    async def validate_graph(self, graph: WorkflowGraph) -> dict[str, Any]:
        """Validate graph connections and structure.

        Args:
            graph: The WorkflowGraph to validate.

        Returns:
            Validation result with errors list.
        """
        errors: list[str] = []

        node_ids = {n.id for n in graph.nodes}
        node_types = {n.id: n.type for n in graph.nodes}

        start_count = sum(1 for n in graph.nodes if n.type == NodeType.START)
        end_count = sum(1 for n in graph.nodes if n.type == NodeType.END)

        if start_count == 0:
            errors.append("Graph must have exactly one Start node")
        elif start_count > 1:
            errors.append("Graph must have exactly one Start node")

        if end_count == 0:
            errors.append("Graph must have at least one End node")

        for edge in graph.edges:
            if edge.source not in node_ids:
                errors.append(f"Edge references unknown source node: {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"Edge references unknown target node: {edge.target}")

        for node in graph.nodes:
            incoming = [e for e in graph.edges if e.target == node.id]
            outgoing = [e for e in graph.edges if e.source == node.id]

            if node.type == NodeType.START and incoming:
                errors.append(f"Start node '{node.label}' must not have incoming edges")
            if node.type == NodeType.END and outgoing:
                errors.append(f"End node '{node.label}' must not have outgoing edges")

        if graph.nodes:
            visited: set[str] = set()
            start_nodes = [n.id for n in graph.nodes if n.type == NodeType.START]
            for start_id in start_nodes:
                self._traverse(graph, start_id, visited)
            unreachable = node_ids - visited
            for uid in unreachable:
                n = next(x for x in graph.nodes if x.id == uid)
                errors.append(f"Node '{n.label}' is unreachable")

        is_valid = len(errors) == 0
        return {"valid": is_valid, "errors": errors}

    def _traverse(self, graph: WorkflowGraph, node_id: str, visited: set[str]) -> None:
        """BFS traversal from a node."""
        if node_id in visited:
            return
        visited.add(node_id)
        for edge in graph.edges:
            if edge.source == node_id:
                self._traverse(graph, edge.target, visited)

    async def get_node_templates(self) -> list[dict[str, Any]]:
        """Get available node types with their metadata.

        Returns:
            List of node template definitions.
        """
        return [
            {
                "type": NodeType.START.value,
                "label": "Start",
                "color": "#4caf50",
                "icon": "play",
                "description": "Entry point of the workflow",
                "category": "control",
            },
            {
                "type": NodeType.END.value,
                "label": "End",
                "color": "#f44336",
                "icon": "stop",
                "description": "Terminal point of the workflow",
                "category": "control",
            },
            {
                "type": NodeType.PLANNER.value,
                "label": "Planner",
                "color": "#2196f3",
                "icon": "route",
                "description": "Plans and decomposes tasks",
                "category": "agent",
            },
            {
                "type": NodeType.SUPERVISOR.value,
                "label": "Supervisor",
                "color": "#9c27b0",
                "icon": "eye",
                "description": "Monitors and directs other agents",
                "category": "agent",
            },
            {
                "type": NodeType.AGENT.value,
                "label": "Agent",
                "color": "#ff9800",
                "icon": "person",
                "description": "Executes a specific role or task",
                "category": "agent",
            },
            {
                "type": NodeType.DECISION.value,
                "label": "Decision",
                "color": "#607d8b",
                "icon": "split",
                "description": "Branches based on conditions",
                "category": "control",
            },
            {
                "type": NodeType.APPROVAL.value,
                "label": "Approval",
                "color": "#e91e63",
                "icon": "check-circle",
                "description": "Requires human approval before proceeding",
                "category": "control",
            },
            {
                "type": NodeType.REFLECTION.value,
                "label": "Reflection",
                "color": "#00bcd4",
                "icon": "refresh",
                "description": "Evaluates and reflects on previous steps",
                "category": "agent",
            },
            {
                "type": NodeType.TOOL.value,
                "label": "Tool",
                "color": "#795548",
                "icon": "wrench",
                "description": "Invokes an external tool or API",
                "category": "action",
            },
            {
                "type": NodeType.MEMORY.value,
                "label": "Memory",
                "color": "#3f51b5",
                "icon": "database",
                "description": "Retrieves or stores context in memory",
                "category": "action",
            },
            {
                "type": NodeType.EXECUTION.value,
                "label": "Execution",
                "color": "#ff5722",
                "icon": "zap",
                "description": "Runs code or executes commands",
                "category": "action",
            },
        ]

    async def update_node_position(self, node_id: str, position: NodePosition) -> None:
        """Update the position of a node across all graphs.

        Args:
            node_id: The node identifier.
            position: New position coordinates.
        """
        for graph in self._graphs.values():
            for node in graph.nodes:
                if node.id == node_id:
                    node.position = position
                    logger.debug("Updated node position: node=%s", node_id[:8])
                    return

        logger.warning("Node not found for position update: node=%s", node_id[:8])

    async def add_node(self, node: WorkflowNode) -> str:
        """Add a node to the first available graph or a new graph.

        Args:
            node: The node to add.

        Returns:
            The graph ID the node was added to.
        """
        if self._graphs:
            graph_id = next(iter(self._graphs))
            self._graphs[graph_id].nodes.append(node)
            logger.info("Added node: id=%s graph=%s", node.id[:8], graph_id[:8])
            return graph_id

        graph_id = str(uuid.uuid4())
        self._graphs[graph_id] = WorkflowGraph(nodes=[node])
        logger.info("Created new graph with node: id=%s graph=%s", node.id[:8], graph_id[:8])
        return graph_id

    async def remove_node(self, node_id: str) -> None:
        """Remove a node and its connected edges from all graphs.

        Args:
            node_id: The node identifier to remove.
        """
        for graph in self._graphs.values():
            graph.nodes = [n for n in graph.nodes if n.id != node_id]
            graph.edges = [
                e for e in graph.edges if e.source != node_id and e.target != node_id
            ]

        logger.info("Removed node: node=%s", node_id[:8])

    async def add_edge(self, edge: WorkflowEdge) -> str:
        """Add an edge to the first available graph.

        Args:
            edge: The edge to add.

        Returns:
            The graph ID the edge was added to.
        """
        if self._graphs:
            graph_id = next(iter(self._graphs))
            self._graphs[graph_id].edges.append(edge)
            logger.info(
                "Added edge: id=%s source=%s target=%s",
                edge.id[:8],
                edge.source[:8],
                edge.target[:8],
            )
            return graph_id

        graph_id = str(uuid.uuid4())
        self._graphs[graph_id] = WorkflowGraph(edges=[edge])
        return graph_id

    async def remove_edge(self, edge_id: str) -> None:
        """Remove an edge from all graphs.

        Args:
            edge_id: The edge identifier to remove.
        """
        for graph in self._graphs.values():
            graph.edges = [e for e in graph.edges if e.id != edge_id]

        logger.info("Removed edge: edge=%s", edge_id[:8])

    def _generate_default_graph(self, workflow_id: str) -> WorkflowGraph:
        """Generate a default graph layout from a workflow ID.

        Args:
            workflow_id: The workflow identifier.

        Returns:
            A default WorkflowGraph.
        """
        start_id = str(uuid.uuid4())
        end_id = str(uuid.uuid4())

        start_node = WorkflowNode(
            id=start_id,
            type=NodeType.START,
            label="Start",
            position=NodePosition(x=100, y=300),
        )

        end_node = WorkflowNode(
            id=end_id,
            type=NodeType.END,
            label="End",
            position=NodePosition(x=900, y=300),
        )

        edge = WorkflowEdge(
            id=str(uuid.uuid4()),
            source=start_id,
            target=end_id,
            label="",
        )

        return WorkflowGraph(
            nodes=[start_node, end_node],
            edges=[edge],
        )
