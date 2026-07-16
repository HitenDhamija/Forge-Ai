from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any


class SharedLearning:
    def __init__(self) -> None:
        self._knowledge: dict[str, dict[str, Any]] = {}

    async def add_knowledge(
        self,
        org_id: str,
        knowledge_type: str,
        title: str,
        description: str,
        content: str,
        source_repo: str,
        tags: list[str] | None = None,
    ) -> str:
        kid = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        self._knowledge[kid] = {
            "id": kid,
            "org_id": org_id,
            "knowledge_type": knowledge_type,
            "title": title,
            "description": description,
            "content": content,
            "source_repo": source_repo,
            "tags": tags or [],
            "usage_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        return kid

    async def get_knowledge(self, knowledge_id: str) -> dict[str, Any]:
        return self._knowledge.get(knowledge_id, {})

    async def list_knowledge(
        self,
        org_id: str,
        knowledge_type: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        results = [k for k in self._knowledge.values() if k["org_id"] == org_id]
        if knowledge_type:
            results = [k for k in results if k["knowledge_type"] == knowledge_type]
        if tags:
            tag_set = set(tags)
            results = [k for k in results if tag_set & set(k["tags"])]
        return results

    async def search_knowledge(self, org_id: str, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            k for k in self._knowledge.values()
            if k["org_id"] == org_id
            and (
                q in k["title"].lower()
                or q in k["description"].lower()
                or q in k["content"].lower()
                or any(q in t.lower() for t in k["tags"])
            )
        ]

    async def get_recommendations(
        self, org_id: str, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        repo_id = context.get("repository_id")
        knowledge_type = context.get("knowledge_type")
        candidates = await self.list_knowledge(org_id, knowledge_type=knowledge_type)
        if repo_id:
            repo_items = [k for k in candidates if k["source_repo"] == repo_id]
            other_items = [k for k in candidates if k["source_repo"] != repo_id]
            return repo_items + other_items
        return sorted(candidates, key=lambda k: k["usage_count"], reverse=True)

    async def get_popular_knowledge(
        self, org_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        org_items = [k for k in self._knowledge.values() if k["org_id"] == org_id]
        return sorted(org_items, key=lambda k: k["usage_count"], reverse=True)[:limit]

    async def get_knowledge_by_repository(
        self, org_id: str, repo_id: str
    ) -> list[dict[str, Any]]:
        return [
            k for k in self._knowledge.values()
            if k["org_id"] == org_id and k["source_repo"] == repo_id
        ]

    async def update_knowledge(
        self, knowledge_id: str, updates: dict[str, Any]
    ) -> dict[str, Any]:
        item = self._knowledge.get(knowledge_id)
        if not item:
            return {}
        item.update(updates)
        item["updated_at"] = datetime.utcnow().isoformat()
        return item

    async def delete_knowledge(self, knowledge_id: str) -> None:
        self._knowledge.pop(knowledge_id, None)
