from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from .registry import PluginCategory


@dataclass
class MarketplacePlugin:
    manifest: dict
    downloads: int = 0
    rating: float = 0.0
    reviews_count: int = 0
    last_updated: float = field(default_factory=time.time)
    verified: bool = False
    featured: bool = False


@dataclass
class MarketplaceCategory:
    name: str
    description: str
    plugins_count: int = 0


@dataclass
class Review:
    user_id: str
    rating: int
    comment: str
    created_at: float = field(default_factory=time.time)


class PluginMarketplace:
    def __init__(self) -> None:
        self._plugins: dict[str, MarketplacePlugin] = {}
        self._reviews: dict[str, list[Review]] = {}
        self._categories: dict[str, MarketplaceCategory] = {}
        self._installed: set[str] = set()
        self._load_default_plugins()

    def _load_default_plugins(self) -> None:
        defaults = [
            MarketplacePlugin(
                manifest={
                    "id": "forge-github",
                    "name": "GitHub Integration",
                    "version": "1.2.0",
                    "author": "ForgeAI Team",
                    "description": "Seamless GitHub integration for repository management, PR reviews, and issue tracking.",
                    "category": "integration",
                    "permissions": ["repo:read", "repo:write", "issues:read"],
                    "tags": ["github", "git", "repository", "scm"],
                },
                downloads=12500,
                rating=4.8,
                reviews_count=234,
                verified=True,
                featured=True,
            ),
            MarketplacePlugin(
                manifest={
                    "id": "forge-slack",
                    "name": "Slack Notifications",
                    "version": "2.0.1",
                    "author": "ForgeAI Team",
                    "description": "Send real-time notifications and alerts to Slack channels and users.",
                    "category": "notification",
                    "permissions": ["chat:write", "channels:read"],
                    "tags": ["slack", "notifications", "messaging"],
                },
                downloads=9800,
                rating=4.6,
                reviews_count=189,
                verified=True,
                featured=True,
            ),
            MarketplacePlugin(
                manifest={
                    "id": "forge-jira",
                    "name": "Jira Workflow",
                    "version": "1.5.0",
                    "author": "ForgeAI Team",
                    "description": "Integrate with Jira for project management, issue tracking, and workflow automation.",
                    "category": "workflow",
                    "permissions": ["project:read", "issue:read", "issue:write"],
                    "tags": ["jira", "project-management", "workflow"],
                },
                downloads=7200,
                rating=4.5,
                reviews_count=156,
                verified=True,
                featured=False,
            ),
            MarketplacePlugin(
                manifest={
                    "id": "forge-docker",
                    "name": "Docker Deployment",
                    "version": "1.3.2",
                    "author": "ForgeAI Team",
                    "description": "Deploy and manage containerized applications with Docker integration.",
                    "category": "deployment",
                    "permissions": ["docker:read", "docker:write"],
                    "tags": ["docker", "containers", "deployment"],
                },
                downloads=8900,
                rating=4.7,
                reviews_count=201,
                verified=True,
                featured=True,
            ),
            MarketplacePlugin(
                manifest={
                    "id": "forge-aws",
                    "name": "AWS Integration",
                    "version": "2.1.0",
                    "author": "ForgeAI Team",
                    "description": "Full AWS integration for S3, EC2, Lambda, and other AWS services.",
                    "category": "integration",
                    "permissions": ["aws:read", "aws:write"],
                    "tags": ["aws", "cloud", "infrastructure"],
                },
                downloads=11200,
                rating=4.7,
                reviews_count=278,
                verified=True,
                featured=True,
            ),
            MarketplacePlugin(
                manifest={
                    "id": "forge-azure",
                    "name": "Azure Integration",
                    "version": "1.8.0",
                    "author": "ForgeAI Team",
                    "description": "Microsoft Azure integration for cloud resources, DevOps, and AI services.",
                    "category": "integration",
                    "permissions": ["azure:read", "azure:write"],
                    "tags": ["azure", "microsoft", "cloud"],
                },
                downloads=6500,
                rating=4.4,
                reviews_count=134,
                verified=True,
                featured=False,
            ),
            MarketplacePlugin(
                manifest={
                    "id": "forge-custom-prompts",
                    "name": "Custom Prompt Pack",
                    "version": "3.0.0",
                    "author": "ForgeAI Community",
                    "description": "A collection of 200+ curated prompts for various use cases and domains.",
                    "category": "prompt",
                    "permissions": [],
                    "tags": ["prompts", "templates", "productivity"],
                },
                downloads=15600,
                rating=4.9,
                reviews_count=412,
                verified=True,
                featured=True,
            ),
            MarketplacePlugin(
                manifest={
                    "id": "forge-code-review",
                    "name": "Code Review Agent",
                    "version": "1.1.0",
                    "author": "ForgeAI Team",
                    "description": "AI-powered code review agent that checks for bugs, style issues, and security vulnerabilities.",
                    "category": "agent",
                    "permissions": ["repo:read", "pull_requests:read"],
                    "tags": ["code-review", "security", "quality"],
                },
                downloads=8200,
                rating=4.6,
                reviews_count=178,
                verified=True,
                featured=False,
            ),
        ]

        for plugin in defaults:
            plugin_id = plugin.manifest["id"]
            self._plugins[plugin_id] = plugin
            self._reviews[plugin_id] = []

        self._build_categories()

    def _build_categories(self) -> None:
        cat_counts: dict[str, int] = {}
        for plugin in self._plugins.values():
            cat = plugin.manifest.get("category", "other")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        cat_descriptions = {
            "agent": "Autonomous AI agents for task execution",
            "tool": "Developer tools and utilities",
            "workflow": "Automation workflows and pipelines",
            "prompt": "Prompt templates and packs",
            "knowledge": "Knowledge base and RAG plugins",
            "memory": "Memory and context management",
            "ui": "User interface components",
            "visualization": "Data visualization tools",
            "deployment": "Deployment and hosting solutions",
            "analytics": "Analytics and monitoring",
            "notification": "Alerts and notification systems",
            "integration": "Third-party service integrations",
            "other": "Uncategorized plugins",
        }

        for cat, count in cat_counts.items():
            self._categories[cat] = MarketplaceCategory(
                name=cat,
                description=cat_descriptions.get(cat, cat),
                plugins_count=count,
            )

    def search_plugins(
        self, query: str, category: PluginCategory | None = None
    ) -> list[MarketplacePlugin]:
        query_lower = query.lower()
        results: list[MarketplacePlugin] = []
        for plugin in self._plugins.values():
            name = plugin.manifest.get("name", "").lower()
            desc = plugin.manifest.get("description", "").lower()
            tags = plugin.manifest.get("tags", [])
            tag_match = any(query_lower in t.lower() for t in tags)

            if query_lower not in name and query_lower not in desc and not tag_match:
                continue

            if category is not None:
                plugin_cat = plugin.manifest.get("category", "")
                if plugin_cat != category.value:
                    continue

            results.append(plugin)
        return results

    def get_plugin(self, plugin_id: str) -> MarketplacePlugin | None:
        return self._plugins.get(plugin_id)

    def list_featured(self) -> list[MarketplacePlugin]:
        return [p for p in self._plugins.values() if p.featured]

    def list_popular(self, limit: int = 20) -> list[MarketplacePlugin]:
        sorted_plugins = sorted(
            self._plugins.values(), key=lambda p: p.downloads, reverse=True
        )
        return sorted_plugins[:limit]

    def list_recent(self, limit: int = 20) -> list[MarketplacePlugin]:
        sorted_plugins = sorted(
            self._plugins.values(), key=lambda p: p.last_updated, reverse=True
        )
        return sorted_plugins[:limit]

    def list_categories(self) -> list[MarketplaceCategory]:
        return list(self._categories.values())

    def get_plugins_by_category(
        self, category: PluginCategory
    ) -> list[MarketplacePlugin]:
        return [
            p
            for p in self._plugins.values()
            if p.manifest.get("category") == category.value
        ]

    def install_plugin(self, plugin_id: str) -> dict:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found in marketplace"}

        if plugin_id in self._installed:
            return {"success": False, "error": f"Plugin '{plugin_id}' is already installed"}

        self._installed.add(plugin_id)
        plugin.downloads += 1

        return {
            "success": True,
            "plugin_id": plugin_id,
            "version": plugin.manifest.get("version", "0.0.0"),
            "message": f"Successfully installed {plugin.manifest.get('name', plugin_id)}",
        }

    def uninstall_plugin(self, plugin_id: str) -> dict:
        if plugin_id not in self._installed:
            return {"success": False, "error": f"Plugin '{plugin_id}' is not installed"}

        self._installed.discard(plugin_id)
        plugin = self._plugins.get(plugin_id)
        name = plugin.manifest.get("name", plugin_id) if plugin else plugin_id

        return {
            "success": True,
            "plugin_id": plugin_id,
            "message": f"Successfully uninstalled {name}",
        }

    def update_plugin(self, plugin_id: str) -> dict:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found"}

        if plugin_id not in self._installed:
            return {"success": False, "error": f"Plugin '{plugin_id}' is not installed"}

        plugin.last_updated = time.time()

        return {
            "success": True,
            "plugin_id": plugin_id,
            "version": plugin.manifest.get("version", "0.0.0"),
            "message": f"Successfully updated {plugin.manifest.get('name', plugin_id)}",
        }

    def get_plugin_reviews(self, plugin_id: str) -> list[Review]:
        return self._reviews.get(plugin_id, [])

    def add_review(self, plugin_id: str, rating: int, comment: str) -> Review:
        if plugin_id not in self._plugins:
            raise ValueError(f"Plugin '{plugin_id}' not found")

        rating = max(1, min(5, rating))
        review = Review(
            user_id=str(uuid.uuid4()),
            rating=rating,
            comment=comment,
        )

        if plugin_id not in self._reviews:
            self._reviews[plugin_id] = []
        self._reviews[plugin_id].append(review)

        plugin = self._plugins[plugin_id]
        total_rating = plugin.rating * plugin.reviews_count + rating
        plugin.reviews_count += 1
        plugin.rating = round(total_rating / plugin.reviews_count, 2)

        return review

    def get_trending(self) -> list[MarketplacePlugin]:
        now = time.time()
        one_week = 7 * 24 * 60 * 60

        trending: list[tuple[MarketplacePlugin, float]] = []
        for plugin in self._plugins.values():
            recency = max(0, 1 - (now - plugin.last_updated) / one_week)
            popularity = plugin.downloads / 1000
            score = recency * 0.4 + popularity * 0.3 + plugin.rating * 0.3
            trending.append((plugin, score))

        trending.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in trending[:20]]

    def get_recommended(self, plugin_id: str) -> list[MarketplacePlugin]:
        source = self._plugins.get(plugin_id)
        if source is None:
            return []

        source_cat = source.manifest.get("category", "")
        source_tags = set(source.manifest.get("tags", []))

        scored: list[tuple[MarketplacePlugin, float]] = []
        for pid, plugin in self._plugins.items():
            if pid == plugin_id:
                continue

            score = 0.0
            if plugin.manifest.get("category") == source_cat:
                score += 2.0

            plugin_tags = set(plugin.manifest.get("tags", []))
            overlap = len(source_tags & plugin_tags)
            score += overlap * 0.5

            score += plugin.rating * 0.2
            scored.append((plugin, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored[:10]]


plugin_marketplace = PluginMarketplace()
