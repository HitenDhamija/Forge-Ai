from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
import re


class SearchableType(Enum):
    REPOSITORY = "repository"
    ORGANIZATION = "organization"
    WORKFLOW = "workflow"
    AGENT = "agent"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    PROMPT = "prompt"
    TEMPLATE = "template"
    EXECUTION = "execution"
    DOCUMENTATION = "documentation"


@dataclass
class SearchResult:
    id: str
    type: SearchableType
    title: str
    description: str
    subtitle: str
    url: str
    icon: str
    score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchContext:
    query: str
    filters: list[SearchableType] = field(default_factory=list)
    user_id: str = ""
    limit: int = 20
    offset: int = 0


class GlobalSearch:
    def __init__(self) -> None:
        self._index: dict[tuple[str, str], dict[str, Any]] = {}
        self._recent_searches: dict[str, list[dict[str, Any]]] = {}
        self._popular_searches: dict[str, int] = {}
        self._populate_defaults()

    def _populate_defaults(self) -> None:
        default_entities: list[dict[str, Any]] = [
            {
                "type": "repository",
                "id": "repo-001",
                "title": "forge-ai-backend",
                "description": "Core backend service for the ForgeAI platform",
                "subtitle": "Python · FastAPI · 24k lines",
                "url": "/repos/forge-ai-backend",
                "icon": "git-branch",
                "metadata": {"language": "Python", "stars": 142},
            },
            {
                "type": "repository",
                "id": "repo-002",
                "title": "forge-ai-frontend",
                "description": "React frontend application for ForgeAI",
                "subtitle": "TypeScript · React · 18k lines",
                "url": "/repos/forge-ai-frontend",
                "icon": "git-branch",
                "metadata": {"language": "TypeScript", "stars": 98},
            },
            {
                "type": "repository",
                "id": "repo-003",
                "title": "forge-docs",
                "description": "Official documentation for ForgeAI",
                "subtitle": "Markdown · Docusaurus · 4k lines",
                "url": "/repos/forge-docs",
                "icon": "git-branch",
                "metadata": {"language": "Markdown", "stars": 31},
            },
            {
                "type": "workflow",
                "id": "wf-001",
                "title": "code-review",
                "description": "Automated code review workflow with AI analysis",
                "subtitle": "5 steps · Last run 2h ago",
                "url": "/workflows/code-review",
                "icon": "workflow",
                "metadata": {"runs": 312, "success_rate": 0.97},
            },
            {
                "type": "workflow",
                "id": "wf-002",
                "title": "deployment",
                "description": "CI/CD deployment pipeline with staging and production",
                "subtitle": "8 steps · Last run 4h ago",
                "url": "/workflows/deployment",
                "icon": "workflow",
                "metadata": {"runs": 189, "success_rate": 0.94},
            },
            {
                "type": "workflow",
                "id": "wf-003",
                "title": "testing",
                "description": "Comprehensive test suite execution and reporting",
                "subtitle": "4 steps · Last run 1h ago",
                "url": "/workflows/testing",
                "icon": "workflow",
                "metadata": {"runs": 521, "success_rate": 0.99},
            },
            {
                "type": "agent",
                "id": "agent-001",
                "title": "software-engineer",
                "description": "AI agent specialized in full-stack software engineering",
                "subtitle": "gpt-4o · 12k executions",
                "url": "/agents/software-engineer",
                "icon": "bot",
                "metadata": {"model": "gpt-4o", "avg_latency_ms": 820},
            },
            {
                "type": "agent",
                "id": "agent-002",
                "title": "code-reviewer",
                "description": "AI agent for thorough code review and suggestions",
                "subtitle": "claude-3-opus · 8k executions",
                "url": "/agents/code-reviewer",
                "icon": "bot",
                "metadata": {"model": "claude-3-opus", "avg_latency_ms": 1200},
            },
            {
                "type": "agent",
                "id": "agent-003",
                "title": "devops",
                "description": "AI agent for infrastructure and deployment automation",
                "subtitle": "gpt-4o · 5k executions",
                "url": "/agents/devops",
                "icon": "bot",
                "metadata": {"model": "gpt-4o", "avg_latency_ms": 650},
            },
            {
                "type": "memory",
                "id": "mem-001",
                "title": "Project Architecture Decisions",
                "description": "Stored architectural decisions and rationale for the platform",
                "subtitle": "12 entries · Updated 3h ago",
                "url": "/memory/project-architecture",
                "icon": "database",
                "metadata": {"entries": 12},
            },
            {
                "type": "knowledge",
                "id": "kb-001",
                "title": "API Reference",
                "description": "Complete API reference documentation",
                "subtitle": "45 endpoints · Auto-synced",
                "url": "/knowledge/api-reference",
                "icon": "book-open",
                "metadata": {"endpoints": 45},
            },
            {
                "type": "prompt",
                "id": "prompt-001",
                "title": "Code Review Prompt",
                "description": "System prompt for code review agent",
                "subtitle": "v3 · Last modified 1d ago",
                "url": "/prompts/code-review",
                "icon": "message-square",
                "metadata": {"version": 3},
            },
            {
                "type": "template",
                "id": "tmpl-001",
                "title": "FastAPI Boilerplate",
                "description": "Starter template for FastAPI projects",
                "subtitle": "Python · 12 files",
                "url": "/templates/fastapi-boilerplate",
                "icon": "layout-template",
                "metadata": {"files": 12},
            },
            {
                "type": "documentation",
                "id": "doc-001",
                "title": "Getting Started Guide",
                "description": "Step-by-step guide to get started with ForgeAI",
                "subtitle": "5 min read · Last updated 2d ago",
                "url": "/docs/getting-started",
                "icon": "file-text",
                "metadata": {"read_time_min": 5},
            },
        ]

        for entity in default_entities:
            key = (entity["type"], entity["id"])
            self._index[key] = entity

    def _score(self, query: str, text: str) -> float:
        query_lower = query.lower()
        text_lower = text.lower()
        if query_lower == text_lower:
            return 1.0
        if query_lower in text_lower:
            idx = text_lower.index(query_lower)
            return 0.8 - (idx / max(len(text_lower), 1)) * 0.3
        query_tokens = set(query_lower.split())
        text_tokens = set(text_lower.split())
        overlap = query_tokens & text_tokens
        if overlap:
            return len(overlap) / max(len(query_tokens), 1) * 0.6
        return 0.0

    def _search_type(
        self, query: str, search_type: str, limit: int
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        for (_type, _id), entity in self._index.items():
            if _type != search_type:
                continue
            searchable = f"{entity['title']} {entity['description']} {entity.get('subtitle', '')}"
            score = self._score(query, searchable)
            if score > 0:
                results.append(
                    SearchResult(
                        id=entity["id"],
                        type=SearchableType(entity["type"]),
                        title=entity["title"],
                        description=entity["description"],
                        subtitle=entity.get("subtitle", ""),
                        url=entity["url"],
                        icon=entity["icon"],
                        score=score,
                        metadata=entity.get("metadata", {}),
                    )
                )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def search(
        self,
        query: str,
        types: list[SearchableType] | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        allowed_types = (
            [t.value for t in types] if types else [t.value for t in SearchableType]
        )
        results: list[SearchResult] = []
        for entity_type in allowed_types:
            results.extend(self._search_type(query, entity_type, limit))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def search_repositories(self, query: str) -> list[SearchResult]:
        return self._search_type(query, SearchableType.REPOSITORY.value, 20)

    def search_workflows(self, query: str) -> list[SearchResult]:
        return self._search_type(query, SearchableType.WORKFLOW.value, 20)

    def search_agents(self, query: str) -> list[SearchResult]:
        return self._search_type(query, SearchableType.AGENT.value, 20)

    def search_memory(self, query: str) -> list[SearchResult]:
        return self._search_type(query, SearchableType.MEMORY.value, 20)

    def search_knowledge(self, query: str) -> list[SearchResult]:
        return self._search_type(query, SearchableType.KNOWLEDGE.value, 20)

    def search_prompts(self, query: str) -> list[SearchResult]:
        return self._search_type(query, SearchableType.PROMPT.value, 20)

    def search_templates(self, query: str) -> list[SearchResult]:
        return self._search_type(query, SearchableType.TEMPLATE.value, 20)

    def search_documentation(self, query: str) -> list[SearchResult]:
        return self._search_type(query, SearchableType.DOCUMENTATION.value, 20)

    def get_recent_searches(self, user_id: str, limit: int = 10) -> list[str]:
        entries = self._recent_searches.get(user_id, [])
        return [e["query"] for e in entries[:limit]]

    def save_search(self, user_id: str, query: str) -> None:
        if user_id not in self._recent_searches:
            self._recent_searches[user_id] = []
        self._recent_searches[user_id].insert(
            0, {"query": query, "timestamp": datetime.utcnow().isoformat()}
        )
        self._recent_searches[user_id] = self._recent_searches[user_id][:50]
        self._popular_searches[query.lower()] = (
            self._popular_searches.get(query.lower(), 0) + 1
        )

    def get_popular_searches(self, limit: int = 10) -> list[dict]:
        sorted_queries = sorted(
            self._popular_searches.items(), key=lambda x: x[1], reverse=True
        )
        return [{"query": q, "count": c} for q, c in sorted_queries[:limit]]

    def index_entity(
        self, entity_type: str, entity_id: str, data: dict
    ) -> None:
        key = (entity_type, entity_id)
        data["type"] = entity_type
        data["id"] = entity_id
        self._index[key] = data

    def remove_entity(self, entity_type: str, entity_id: str) -> None:
        key = (entity_type, entity_id)
        self._index.pop(key, None)


global_search = GlobalSearch()
