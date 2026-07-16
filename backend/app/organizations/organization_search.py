from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class SearchableType(str, Enum):
    repository = "repository"
    knowledge = "knowledge"
    pattern = "pattern"
    template = "template"
    workflow = "workflow"
    execution = "execution"
    documentation = "documentation"


@dataclass
class SearchResult:
    id: str
    type: SearchableType
    title: str
    description: str
    repository_id: Optional[str] = None
    score: float = 0.0
    metadata: dict = field(default_factory=dict)


class OrganizationSearch:
    """Global search across organization repositories, knowledge, and patterns."""

    def __init__(self, db=None):
        self.db = db
        self._recent_searches: dict[str, list[dict]] = {}

    async def search(
        self,
        org_id: str,
        query: str,
        types: Optional[list[SearchableType]] = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        search_types = types or list(SearchableType)
        results: list[SearchResult] = []

        for stype in search_types:
            method_map = {
                SearchableType.repository: self.search_repositories,
                SearchableType.knowledge: self.search_knowledge,
                SearchableType.pattern: self.search_patterns,
                SearchableType.template: self.search_templates,
            }
            method = method_map.get(stype)
            if method:
                results.extend(await method(org_id, query))

        ranked = self._rank_results(results)[:limit]
        await self._record_search(org_id, query)
        return ranked

    async def search_repositories(self, org_id: str, query: str) -> list[SearchResult]:
        results: list[SearchResult] = []
        if self.db is None:
            return results
        rows = await self.db.fetch(
            """
            SELECT id, name, description, language
            FROM repositories
            WHERE organization_id = $1 AND (name ILIKE $2 OR description ILIKE $2)
            """,
            org_id,
            f"%{query}%",
        )
        for row in rows:
            score = self._calculate_relevance(query, row)
            results.append(
                SearchResult(
                    id=str(row["id"]),
                    type=SearchableType.repository,
                    title=row["name"],
                    description=row.get("description", ""),
                    score=score,
                    metadata={"language": row.get("language", "")},
                )
            )
        return results

    async def search_knowledge(self, org_id: str, query: str) -> list[SearchResult]:
        results: list[SearchResult] = []
        if self.db is None:
            return results
        rows = await self.db.fetch(
            """
            SELECT id, title, content, repository_id
            FROM knowledge_base
            WHERE organization_id = $1 AND (title ILIKE $2 OR content ILIKE $2)
            """,
            org_id,
            f"%{query}%",
        )
        for row in rows:
            score = self._calculate_relevance(query, row)
            results.append(
                SearchResult(
                    id=str(row["id"]),
                    type=SearchableType.knowledge,
                    title=row["title"],
                    description=row.get("content", "")[:200],
                    repository_id=str(row.get("repository_id")) if row.get("repository_id") else None,
                    score=score,
                )
            )
        return results

    async def search_patterns(self, org_id: str, query: str) -> list[SearchResult]:
        results: list[SearchResult] = []
        if self.db is None:
            return results
        rows = await self.db.fetch(
            """
            SELECT id, name, description, pattern_type
            FROM code_patterns
            WHERE organization_id = $1 AND (name ILIKE $2 OR description ILIKE $2)
            """,
            org_id,
            f"%{query}%",
        )
        for row in rows:
            score = self._calculate_relevance(query, row)
            results.append(
                SearchResult(
                    id=str(row["id"]),
                    type=SearchableType.pattern,
                    title=row["name"],
                    description=row.get("description", ""),
                    score=score,
                    metadata={"pattern_type": row.get("pattern_type", "")},
                )
            )
        return results

    async def search_templates(self, org_id: str, query: str) -> list[SearchResult]:
        results: list[SearchResult] = []
        if self.db is None:
            return results
        rows = await self.db.fetch(
            """
            SELECT id, name, description, template_type
            FROM workflow_templates
            WHERE organization_id = $1 AND (name ILIKE $2 OR description ILIKE $2)
            """,
            org_id,
            f"%{query}%",
        )
        for row in rows:
            score = self._calculate_relevance(query, row)
            results.append(
                SearchResult(
                    id=str(row["id"]),
                    type=SearchableType.template,
                    title=row["name"],
                    description=row.get("description", ""),
                    score=score,
                    metadata={"template_type": row.get("template_type", "")},
                )
            )
        return results

    async def get_recent_searches(self, org_id: str, limit: int = 10) -> list[dict]:
        searches = self._recent_searches.get(org_id, [])
        return searches[-limit:]

    def _calculate_relevance(self, query: str, item: dict) -> float:
        query_lower = query.lower()
        score = 0.0
        name = (item.get("name") or item.get("title") or "").lower()
        description = (item.get("description") or item.get("content") or "").lower()

        if query_lower == name:
            score += 10.0
        elif query_lower in name:
            score += 7.0
        elif any(tok in name for tok in query_lower.split()):
            score += 4.0

        if query_lower in description:
            score += 3.0
        elif any(tok in description for tok in query_lower.split()):
            score += 1.5

        return score

    def _rank_results(self, results: list[SearchResult]) -> list[SearchResult]:
        return sorted(results, key=lambda r: r.score, reverse=True)

    async def _record_search(self, org_id: str, query: str) -> None:
        if org_id not in self._recent_searches:
            self._recent_searches[org_id] = []
        self._recent_searches[org_id].append(
            {
                "query": query,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        if len(self._recent_searches[org_id]) > 50:
            self._recent_searches[org_id] = self._recent_searches[org_id][-50:]
