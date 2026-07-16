from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class TemplateType(str, Enum):
    planning = "planning"
    engineering = "engineering"
    deployment = "deployment"
    review = "review"
    qa = "qa"
    documentation = "documentation"


@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str
    template_type: TemplateType
    template_data: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    usage_count: int = 0
    is_default: bool = False


class WorkflowTemplates:
    """Workflow template management for organization standards."""

    def __init__(self, db=None):
        self.db = db

    async def create_template(
        self,
        org_id: str,
        name: str,
        description: str,
        template_type: TemplateType,
        template_data: dict[str, Any],
        tags: Optional[list[str]] = None,
    ) -> str:
        template_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        if self.db is not None:
            await self.db.execute(
                """
                INSERT INTO workflow_templates
                    (id, organization_id, name, description, template_type, template_data, tags, usage_count, is_default, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, 0, false, $8, $8)
                """,
                template_id,
                org_id,
                name,
                description,
                template_type.value,
                template_data,
                tags or [],
                now,
            )
        return template_id

    async def get_template(self, template_id: str) -> dict:
        if self.db is None:
            return {"id": template_id, "name": "", "description": ""}
        row = await self.db.fetchrow(
            """
            SELECT id, organization_id, name, description, template_type,
                   template_data, tags, usage_count, is_default, created_at, updated_at
            FROM workflow_templates
            WHERE id = $1
            """,
            template_id,
        )
        if row is None:
            return {}
        return dict(row)

    async def list_templates(
        self, org_id: str, template_type: Optional[TemplateType] = None
    ) -> list[dict]:
        if self.db is None:
            return []
        if template_type:
            rows = await self.db.fetch(
                """
                SELECT id, name, description, template_type, tags, usage_count, is_default, created_at
                FROM workflow_templates
                WHERE organization_id = $1 AND template_type = $2
                ORDER BY created_at DESC
                """,
                org_id,
                template_type.value,
            )
        else:
            rows = await self.db.fetch(
                """
                SELECT id, name, description, template_type, tags, usage_count, is_default, created_at
                FROM workflow_templates
                WHERE organization_id = $1
                ORDER BY created_at DESC
                """,
                org_id,
            )
        return [dict(r) for r in rows]

    async def update_template(self, template_id: str, updates: dict[str, Any]) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        if self.db is not None and updates:
            set_parts = []
            values = []
            idx = 1
            for key, val in updates.items():
                set_parts.append(f"{key} = ${idx}")
                values.append(val)
                idx += 1
            set_parts.append(f"updated_at = ${idx}")
            values.append(now)
            values.append(template_id)
            query = f"UPDATE workflow_templates SET {', '.join(set_parts)} WHERE id = ${idx + 1} RETURNING *"
            row = await self.db.fetchrow(query, *values)
            return dict(row) if row else {}
        return {}

    async def delete_template(self, template_id: str) -> None:
        if self.db is not None:
            await self.db.execute(
                "DELETE FROM workflow_templates WHERE id = $1", template_id
            )

    async def use_template(self, template_id: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        if self.db is not None:
            row = await self.db.fetchrow(
                """
                UPDATE workflow_templates
                SET usage_count = usage_count + 1, updated_at = $2
                WHERE id = $1
                RETURNING id, name, description, template_type, template_data, tags, usage_count, is_default
                """,
                template_id,
                now,
            )
            return dict(row) if row else {}
        return {}

    async def get_default_templates(self, org_id: str) -> list[dict]:
        if self.db is None:
            return []
        rows = await self.db.fetch(
            """
            SELECT id, name, description, template_type, template_data, tags, usage_count
            FROM workflow_templates
            WHERE organization_id = $1 AND is_default = true
            ORDER BY created_at DESC
            """,
            org_id,
        )
        return [dict(r) for r in rows]

    async def get_popular_templates(self, org_id: str, limit: int = 10) -> list[dict]:
        if self.db is None:
            return []
        rows = await self.db.fetch(
            """
            SELECT id, name, description, template_type, tags, usage_count
            FROM workflow_templates
            WHERE organization_id = $1
            ORDER BY usage_count DESC
            LIMIT $2
            """,
            org_id,
            limit,
        )
        return [dict(r) for r in rows]

    async def clone_template(self, template_id: str, new_name: str) -> str:
        if self.db is None:
            return str(uuid.uuid4())
        row = await self.db.fetchrow(
            """
            SELECT name, description, template_type, template_data, tags, organization_id
            FROM workflow_templates
            WHERE id = $1
            """,
            template_id,
        )
        if row is None:
            raise ValueError(f"Template {template_id} not found")
        new_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            """
            INSERT INTO workflow_templates
                (id, organization_id, name, description, template_type, template_data, tags, usage_count, is_default, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 0, false, $8, $8)
            """,
            new_id,
            row["organization_id"],
            new_name,
            row["description"],
            row["template_type"],
            row["template_data"],
            row["tags"],
            now,
        )
        return new_id
