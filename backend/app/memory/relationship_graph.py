"""Relationship graph for memory chunks."""

from app.core.logging import get_logger
from app.memory.schemas.memory import SemanticChunk
from app.memory.vector_store import VectorStore
from app.repo_intelligence.schemas.graph import SemanticGraph

logger = get_logger(__name__)


class RelationshipGraph:
    """Manages chunk relationships for enhanced retrieval."""

    def __init__(self, vector_store: VectorStore):
        self._vector_store = vector_store
        self._relationships: dict[str, list[str]] = {}

    async def build_relationships(
        self,
        repository_id: str,
        chunks: list[SemanticChunk],
        semantic_graph: SemanticGraph | None = None,
    ) -> None:
        """Build relationships between chunks."""
        # Build from semantic graph if available
        if semantic_graph:
            self._build_from_graph(repository_id, chunks, semantic_graph)

        # Build implicit relationships
        self._build_implicit_relationships(chunks)

        logger.info(
            "Built relationships: repo=%s relationships=%d",
            repository_id,
            len(self._relationships),
        )

    def _build_from_graph(
        self,
        repository_id: str,
        chunks: list[SemanticChunk],
        graph: SemanticGraph,
    ) -> None:
        """Build relationships from semantic graph."""
        chunk_map = {c.id: c for c in chunks}

        for edge in graph.edges:
            source_chunks = [c for c in chunks if edge.source in c.id]
            target_chunks = [c for c in chunks if edge.target in c.id]

            for src in source_chunks:
                for tgt in target_chunks:
                    if src.id not in self._relationships:
                        self._relationships[src.id] = []
                    if tgt.id not in self._relationships[src.id]:
                        self._relationships[src.id].append(tgt.id)

    def _build_implicit_relationships(self, chunks: list[SemanticChunk]) -> None:
        """Build implicit relationships based on shared metadata."""
        # Group by repository, module, class
        by_repo: dict[str, list[str]] = {}
        by_module: dict[str, list[str]] = {}
        by_class: dict[str, list[str]] = {}

        for chunk in chunks:
            repo_id = chunk.metadata.get("repository_id", "")
            module = chunk.metadata.get("module_path", "")
            cls = chunk.metadata.get("class_name", "")

            by_repo.setdefault(repo_id, []).append(chunk.id)
            if module:
                by_module.setdefault(module, []).append(chunk.id)
            if cls:
                by_class.setdefault(cls, []).append(chunk.id)

        # Create relationships for chunks in same module/class
        for group in [by_module.values(), by_class.values()]:
            for chunk_ids in group:
                for i, cid in enumerate(chunk_ids):
                    if cid not in self._relationships:
                        self._relationships[cid] = []
                    for j, other_id in enumerate(chunk_ids):
                        if i != j and other_id not in self._relationships[cid]:
                            self._relationships[cid].append(other_id)

    def get_related(self, chunk_id: str) -> list[str]:
        """Get related chunk IDs."""
        return self._relationships.get(chunk_id, [])
