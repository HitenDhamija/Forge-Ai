from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class CollaborationType(str, Enum):
    comment = "comment"
    approval = "approval"
    review = "review"
    note = "note"
    mention = "mention"


@dataclass
class CollaborationItem:
    id: str
    type: CollaborationType
    entity_type: str
    entity_id: str
    user_id: str
    content: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict = field(default_factory=dict)


class CollaborationService:
    """Collaboration features for organization members."""

    def __init__(self, db=None):
        self.db = db

    async def add_comment(
        self,
        org_id: str,
        entity_type: str,
        entity_id: str,
        user_id: str,
        content: str,
    ) -> str:
        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if self.db is not None:
            await self.db.execute(
                """
                INSERT INTO collaboration_items
                    (id, organization_id, type, entity_type, entity_id, user_id, content, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                item_id,
                org_id,
                CollaborationType.comment.value,
                entity_type,
                entity_id,
                user_id,
                content,
                now,
                {},
            )
        return item_id

    async def get_comments(self, entity_type: str, entity_id: str) -> list[dict]:
        if self.db is None:
            return []
        rows = await self.db.fetch(
            """
            SELECT id, type, entity_type, entity_id, user_id, content, created_at, metadata
            FROM collaboration_items
            WHERE entity_type = $1 AND entity_id = $2 AND type = $3
            ORDER BY created_at ASC
            """,
            entity_type,
            entity_id,
            CollaborationType.comment.value,
        )
        return [dict(r) for r in rows]

    async def add_review(
        self,
        org_id: str,
        entity_type: str,
        entity_id: str,
        user_id: str,
        content: str,
        status: str,
    ) -> str:
        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        metadata = {"status": status}
        if self.db is not None:
            await self.db.execute(
                """
                INSERT INTO collaboration_items
                    (id, organization_id, type, entity_type, entity_id, user_id, content, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                item_id,
                org_id,
                CollaborationType.review.value,
                entity_type,
                entity_id,
                user_id,
                content,
                now,
                metadata,
            )
        return item_id

    async def get_reviews(self, entity_type: str, entity_id: str) -> list[dict]:
        if self.db is None:
            return []
        rows = await self.db.fetch(
            """
            SELECT id, type, entity_type, entity_id, user_id, content, created_at, metadata
            FROM collaboration_items
            WHERE entity_type = $1 AND entity_id = $2 AND type = $3
            ORDER BY created_at DESC
            """,
            entity_type,
            entity_id,
            CollaborationType.review.value,
        )
        return [dict(r) for r in rows]

    async def approve(
        self, entity_type: str, entity_id: str, user_id: str, comment: str = ""
    ) -> dict:
        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        metadata = {"status": "approved"}
        if self.db is not None:
            await self.db.execute(
                """
                INSERT INTO collaboration_items
                    (id, type, entity_type, entity_id, user_id, content, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                item_id,
                CollaborationType.approval.value,
                entity_type,
                entity_id,
                user_id,
                comment,
                now,
                metadata,
            )
        return {"id": item_id, "status": "approved", "user_id": user_id, "created_at": now}

    async def reject(
        self, entity_type: str, entity_id: str, user_id: str, comment: str = ""
    ) -> dict:
        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        metadata = {"status": "rejected"}
        if self.db is not None:
            await self.db.execute(
                """
                INSERT INTO collaboration_items
                    (id, type, entity_type, entity_id, user_id, content, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                item_id,
                CollaborationType.approval.value,
                entity_type,
                entity_id,
                user_id,
                comment,
                now,
                metadata,
            )
        return {"id": item_id, "status": "rejected", "user_id": user_id, "created_at": now}

    async def get_activity(self, org_id: str, limit: int = 20) -> list[dict]:
        if self.db is None:
            return []
        rows = await self.db.fetch(
            """
            SELECT id, type, entity_type, entity_id, user_id, content, created_at, metadata
            FROM collaboration_items
            WHERE organization_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            org_id,
            limit,
        )
        return [dict(r) for r in rows]

    async def get_entity_activity(self, entity_type: str, entity_id: str) -> list[dict]:
        if self.db is None:
            return []
        rows = await self.db.fetch(
            """
            SELECT id, type, entity_type, entity_id, user_id, content, created_at, metadata
            FROM collaboration_items
            WHERE entity_type = $1 AND entity_id = $2
            ORDER BY created_at DESC
            """,
            entity_type,
            entity_id,
        )
        return [dict(r) for r in rows]
