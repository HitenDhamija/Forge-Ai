from __future__ import annotations

import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GraphNode:
    id: str
    node_type: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relationship: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class OrganizationGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._org_nodes: dict[str, set[str]] = {}

    async def get_graph(self, org_id: str) -> dict[str, Any]:
        node_ids = self._org_nodes.get(org_id, set())
        nodes = [vars(self._nodes[nid]) for nid in node_ids if nid in self._nodes]
        edges = [
            vars(e) for e in self._edges.values()
            if e.source in node_ids or e.target in node_ids
        ]
        return {"nodes": nodes, "edges": edges}

    async def add_node(
        self,
        org_id: str,
        node_type: str,
        label: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        nid = str(uuid.uuid4())
        node = GraphNode(id=nid, node_type=node_type, label=label, metadata=metadata or {})
        self._nodes[nid] = node
        self._org_nodes.setdefault(org_id, set()).add(nid)
        return nid

    async def add_edge(
        self,
        org_id: str,
        source: str,
        target: str,
        relationship: str,
        weight: float = 1.0,
    ) -> str:
        eid = str(uuid.uuid4())
        edge = GraphEdge(source=source, target=target, relationship=relationship, weight=weight)
        self._edges[eid] = edge
        return eid

    async def remove_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        for org_nodes in self._org_nodes.values():
            org_nodes.discard(node_id)
        to_remove = [
            eid for eid, e in self._edges.items()
            if e.source == node_id or e.target == node_id
        ]
        for eid in to_remove:
            self._edges.pop(eid, None)

    async def remove_edge(self, edge_id: str) -> None:
        self._edges.pop(edge_id, None)

    async def get_node_connections(self, node_id: str) -> list[dict[str, Any]]:
        connections: list[dict[str, Any]] = []
        for edge in self._edges.values():
            if edge.source == node_id:
                target_node = self._nodes.get(edge.target)
                connections.append({
                    "direction": "outgoing",
                    "relationship": edge.relationship,
                    "node": vars(target_node) if target_node else None,
                })
            elif edge.target == node_id:
                source_node = self._nodes.get(edge.source)
                connections.append({
                    "direction": "incoming",
                    "relationship": edge.relationship,
                    "node": vars(source_node) if source_node else None,
                })
        return connections

    async def get_repository_graph(self, repo_id: str) -> dict[str, Any]:
        node_ids = {
            nid for nid, node in self._nodes.items()
            if node.metadata.get("repository_id") == repo_id
        }
        nodes = [vars(self._nodes[nid]) for nid in node_ids]
        edges = [
            vars(e) for e in self._edges.values()
            if e.source in node_ids or e.target in node_ids
        ]
        return {"nodes": nodes, "edges": edges}

    async def get_organization_structure(self, org_id: str) -> dict[str, Any]:
        node_ids = self._org_nodes.get(org_id, set())
        by_type: dict[str, list[dict[str, Any]]] = {}
        for nid in node_ids:
            node = self._nodes.get(nid)
            if node:
                by_type.setdefault(node.node_type, []).append(vars(node))
        edges = [
            vars(e) for e in self._edges.values()
            if e.source in node_ids or e.target in node_ids
        ]
        return {"nodes_by_type": by_type, "edges": edges}

    async def find_paths(self, source: str, target: str) -> list[list[str]]:
        if source not in self._nodes or target not in self._nodes:
            return []
        adj: dict[str, list[str]] = {}
        for edge in self._edges.values():
            adj.setdefault(edge.source, []).append(edge.target)
            adj.setdefault(edge.target, []).append(edge.source)
        queue: deque[list[str]] = deque([[source]])
        visited: set[str] = {source}
        paths: list[list[str]] = []
        while queue:
            path = queue.popleft()
            current = path[-1]
            if current == target:
                paths.append(path)
                continue
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return paths
