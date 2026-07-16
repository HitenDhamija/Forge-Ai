"""Workspace management for organizing Studio data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class WorkspaceItem:
    """An item in the workspace."""

    id: str
    type: str
    name: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = ""


class WorkspaceManagerService:
    """Service for managing workspace organization.

    Provides search, bookmarks, and overview capabilities
    across all Studio data.
    """

    def __init__(self) -> None:
        self._items: dict[str, WorkspaceItem] = {}
        self._bookmarks: set[str] = set()

    async def get_workspace_overview(self) -> dict[str, Any]:
        """Get overview of all workspace items.

        Returns:
            Workspace summary with counts by type.
        """
        type_counts: dict[str, int] = {}
        for item in self._items.values():
            type_counts[item.type] = type_counts.get(item.type, 0) + 1

        recent = await self.get_recent_items(limit=5)
        bookmarked = await self.get_bookmarks()

        return {
            "total_items": len(self._items),
            "type_counts": type_counts,
            "recent_count": len(recent),
            "bookmarked_count": len(bookmarked),
            "types": list(type_counts.keys()),
            "recent_items": [
                {
                    "id": i.id,
                    "type": i.type,
                    "name": i.name,
                    "updated_at": i.updated_at,
                }
                for i in recent
            ],
        }

    async def search(
        self, query: str, types: list[str] | None = None
    ) -> list[WorkspaceItem]:
        """Search workspace items by query and type.

        Args:
            query: Search string.
            types: Optional type filter.

        Returns:
            Matching WorkspaceItem instances.
        """
        results: list[WorkspaceItem] = []
        query_lower = query.lower()

        for item in self._items.values():
            name_match = query_lower in item.name.lower()
            desc_match = query_lower in item.description.lower()

            if not (name_match or desc_match):
                continue

            if types and item.type not in types:
                continue

            results.append(item)

        return results

    async def get_recent_items(
        self, limit: int = 10
    ) -> list[WorkspaceItem]:
        """Get recently updated items.

        Args:
            limit: Maximum items to return.

        Returns:
            Most recently updated WorkspaceItem instances.
        """
        sorted_items = sorted(
            self._items.values(),
            key=lambda i: i.updated_at,
            reverse=True,
        )
        return sorted_items[:limit]

    async def get_bookmarks(self) -> list[WorkspaceItem]:
        """Get all bookmarked items.

        Returns:
            List of bookmarked WorkspaceItem instances.
        """
        return [
            self._items[item_id]
            for item_id in self._bookmarks
            if item_id in self._items
        ]

    async def add_bookmark(self, item_id: str, item_type: str) -> None:
        """Add a bookmark for an item.

        Args:
            item_id: The item identifier.
            item_type: The item type (for metadata).
        """
        self._bookmarks.add(item_id)

        item = self._items.get(item_id)
        if item:
            item.metadata["bookmarked"] = True
            item.metadata["bookmark_type"] = item_type

        logger.info(
            "Added bookmark: item=%s type=%s", item_id[:8], item_type
        )

    async def remove_bookmark(self, item_id: str) -> None:
        """Remove a bookmark from an item.

        Args:
            item_id: The item identifier.
        """
        self._bookmarks.discard(item_id)

        item = self._items.get(item_id)
        if item:
            item.metadata.pop("bookmarked", None)
            item.metadata.pop("bookmark_type", None)

        logger.info("Removed bookmark: item=%s", item_id[:8])

    def register_item(self, item: WorkspaceItem) -> None:
        """Register an item in the workspace.

        Args:
            item: The WorkspaceItem to register.
        """
        self._items[item.id] = item
        logger.debug(
            "Registered workspace item: id=%s type=%s name=%s",
            item.id[:8],
            item.type,
            item.name,
        )

    def remove_item(self, item_id: str) -> None:
        """Remove an item from the workspace.

        Args:
            item_id: The item identifier.
        """
        self._items.pop(item_id, None)
        self._bookmarks.discard(item_id)
        logger.debug("Removed workspace item: id=%s", item_id[:8])
