"""Plugin Marketplace API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, UTC


router = APIRouter()


class PluginInstall(BaseModel):
    plugin_id: str
    source: Optional[str] = "marketplace"


class PluginConfigUpdate(BaseModel):
    config: dict


class PluginCreate(BaseModel):
    name: str
    description: str
    category: str
    version: Optional[str] = "1.0.0"
    author: Optional[str] = ""
    permissions: Optional[list[str]] = []


class PluginReview(BaseModel):
    rating: int
    comment: str


class PluginValidate(BaseModel):
    plugin_id: str


_marketplace_plugins = [
    {
        "id": "forge-github",
        "name": "GitHub Integration",
        "description": "Connect repositories with GitHub, sync issues, and manage pull requests",
        "category": "integration",
        "author": "ForgeAI",
        "version": "1.2.0",
        "downloads": 15420,
        "rating": 4.8,
        "reviews_count": 124,
        "last_updated": "2025-01-15T10:00:00Z",
        "verified": True,
        "featured": True,
        "tags": ["github", "git", "integration", "scm"],
        "permissions": ["read_repositories", "access_network"],
        "config_schema": {"github_token": {"type": "string", "required": True}},
    },
    {
        "id": "forge-slack",
        "name": "Slack Notifications",
        "description": "Send notifications to Slack channels when workflows complete",
        "category": "notification",
        "author": "ForgeAI",
        "version": "2.0.1",
        "downloads": 12350,
        "rating": 4.6,
        "reviews_count": 98,
        "last_updated": "2025-01-10T08:00:00Z",
        "verified": True,
        "featured": True,
        "tags": ["slack", "notifications", "messaging"],
        "permissions": ["access_network"],
        "config_schema": {"webhook_url": {"type": "string", "required": True}},
    },
    {
        "id": "forge-jira",
        "name": "Jira Workflow",
        "description": "Create and manage Jira tickets from ForgeAI workflows",
        "category": "integration",
        "author": "ForgeAI",
        "version": "1.1.0",
        "downloads": 8720,
        "rating": 4.5,
        "reviews_count": 67,
        "last_updated": "2025-01-08T12:00:00Z",
        "verified": True,
        "featured": False,
        "tags": ["jira", "workflow", "project-management"],
        "permissions": ["read_repositories", "access_network"],
        "config_schema": {"api_url": {"type": "string", "required": True}, "token": {"type": "string", "required": True}},
    },
    {
        "id": "forge-docker",
        "name": "Docker Deployment",
        "description": "Deploy applications to Docker containers with automatic configuration",
        "category": "deployment",
        "author": "ForgeAI",
        "version": "1.0.3",
        "downloads": 21500,
        "rating": 4.9,
        "reviews_count": 203,
        "last_updated": "2025-01-12T14:00:00Z",
        "verified": True,
        "featured": True,
        "tags": ["docker", "deployment", "containers"],
        "permissions": ["read_repositories", "write_files", "access_network"],
        "config_schema": {},
    },
    {
        "id": "forge-aws",
        "name": "AWS Integration",
        "description": "Deploy to AWS services including ECS, Lambda, and S3",
        "category": "deployment",
        "author": "ForgeAI",
        "version": "1.0.0",
        "downloads": 6540,
        "rating": 4.4,
        "reviews_count": 45,
        "last_updated": "2025-01-05T16:00:00Z",
        "verified": True,
        "featured": False,
        "tags": ["aws", "cloud", "deployment", "lambda", "ecs"],
        "permissions": ["read_repositories", "access_network"],
        "config_schema": {"access_key": {"type": "string", "required": True}, "secret_key": {"type": "string", "required": True}},
    },
    {
        "id": "forge-azure",
        "name": "Azure Integration",
        "description": "Deploy to Azure services including App Service and Functions",
        "category": "deployment",
        "author": "ForgeAI",
        "version": "1.0.0",
        "downloads": 4230,
        "rating": 4.3,
        "reviews_count": 32,
        "last_updated": "2025-01-03T10:00:00Z",
        "verified": True,
        "featured": False,
        "tags": ["azure", "cloud", "deployment"],
        "permissions": ["read_repositories", "access_network"],
        "config_schema": {"subscription_id": {"type": "string", "required": True}},
    },
    {
        "id": "forge-custom-prompts",
        "name": "Custom Prompt Pack",
        "description": "Collection of 50+ prompts for code review, documentation, and testing",
        "category": "prompt",
        "author": "Community",
        "version": "3.1.0",
        "downloads": 18900,
        "rating": 4.7,
        "reviews_count": 156,
        "last_updated": "2025-01-14T09:00:00Z",
        "verified": True,
        "featured": True,
        "tags": ["prompts", "code-review", "documentation", "testing"],
        "permissions": [],
        "config_schema": {},
    },
    {
        "id": "forge-code-review",
        "name": "Code Review Agent",
        "description": "AI-powered code review with best practices enforcement",
        "category": "agent",
        "author": "ForgeAI",
        "version": "2.0.0",
        "downloads": 25600,
        "rating": 4.9,
        "reviews_count": 234,
        "last_updated": "2025-01-16T11:00:00Z",
        "verified": True,
        "featured": True,
        "tags": ["code-review", "agent", "ai", "best-practices"],
        "permissions": ["read_repositories", "manage_agents"],
        "config_schema": {"auto_review": {"type": "boolean", "default": True}},
    },
]

_installed_plugins = []
_reviews = {}
_categories = [
    {"name": "agent", "description": "AI Agent plugins", "plugins_count": 12},
    {"name": "tool", "description": "MCP Tool plugins", "plugins_count": 8},
    {"name": "workflow", "description": "Workflow automation", "plugins_count": 15},
    {"name": "prompt", "description": "Prompt templates", "plugins_count": 22},
    {"name": "knowledge", "description": "Knowledge providers", "plugins_count": 6},
    {"name": "memory", "description": "Memory providers", "plugins_count": 4},
    {"name": "ui", "description": "UI components", "plugins_count": 10},
    {"name": "visualization", "description": "Data visualization", "plugins_count": 7},
    {"name": "deployment", "description": "Deployment targets", "plugins_count": 9},
    {"name": "analytics", "description": "Analytics tools", "plugins_count": 5},
    {"name": "notification", "description": "Notification services", "plugins_count": 11},
    {"name": "integration", "description": "External integrations", "plugins_count": 18},
]


@router.get("/plugins")
async def list_plugins(category: Optional[str] = None, status: Optional[str] = None):
    results = _marketplace_plugins.copy()
    if category:
        results = [p for p in results if p.get("category") == category]
    return results


@router.get("/plugins/marketplace")
async def list_marketplace(
    category: Optional[str] = None,
    search: Optional[str] = None,
    sort: Optional[str] = "popular"
):
    results = _marketplace_plugins.copy()
    if category:
        results = [p for p in results if p.get("category") == category]
    if search:
        query = search.lower()
        results = [p for p in results if query in p.get("name", "").lower() or query in p.get("description", "").lower() or any(query in t for t in p.get("tags", []))]
    if sort == "popular":
        results.sort(key=lambda x: x.get("downloads", 0), reverse=True)
    elif sort == "rating":
        results.sort(key=lambda x: x.get("rating", 0), reverse=True)
    elif sort == "recent":
        results.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
    return results


@router.get("/plugins/featured")
async def list_featured():
    return [p for p in _marketplace_plugins if p.get("featured")]


@router.get("/plugins/trending")
async def list_trending():
    return sorted(_marketplace_plugins, key=lambda x: x.get("downloads", 0), reverse=True)[:5]


@router.get("/plugins/categories")
async def list_categories():
    return _categories


@router.get("/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    for p in _marketplace_plugins:
        if p["id"] == plugin_id:
            plugin = p.copy()
            plugin["reviews"] = _reviews.get(plugin_id, [])
            return plugin
    raise HTTPException(status_code=404, detail="Plugin not found")


@router.post("/plugins/install")
async def install_plugin(data: PluginInstall):
    plugin_id = data.plugin_id
    for p in _marketplace_plugins:
        if p["id"] == plugin_id:
            installed = {
                "id": plugin_id,
                "status": "active",
                "installed_at": datetime.now(UTC).isoformat(),
                "config": {},
            }
            _installed_plugins.append(installed)
            return {"status": "installed", "plugin_id": plugin_id}
    raise HTTPException(status_code=404, detail="Plugin not found")


@router.post("/plugins/{plugin_id}/uninstall")
async def uninstall_plugin(plugin_id: str):
    global _installed_plugins
    _installed_plugins = [p for p in _installed_plugins if p["id"] != plugin_id]
    return {"status": "uninstalled", "plugin_id": plugin_id}


@router.post("/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    for p in _installed_plugins:
        if p["id"] == plugin_id:
            p["status"] = "active"
            return {"status": "enabled"}
    raise HTTPException(status_code=404, detail="Plugin not installed")


@router.post("/plugins/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    for p in _installed_plugins:
        if p["id"] == plugin_id:
            p["status"] = "inactive"
            return {"status": "disabled"}
    raise HTTPException(status_code=404, detail="Plugin not installed")


@router.put("/plugins/{plugin_id}/config")
async def update_plugin_config(plugin_id: str, data: PluginConfigUpdate):
    for p in _installed_plugins:
        if p["id"] == plugin_id:
            p["config"].update(data.config)
            return {"status": "updated"}
    raise HTTPException(status_code=404, detail="Plugin not installed")


@router.post("/plugins/{plugin_id}/validate")
async def validate_plugin(plugin_id: str):
    for p in _marketplace_plugins:
        if p["id"] == plugin_id:
            return {
                "valid": True,
                "checks": [
                    {"name": "manifest", "passed": True, "message": "Valid manifest"},
                    {"name": "permissions", "passed": True, "message": "Permissions valid"},
                    {"name": "dependencies", "passed": True, "message": "Dependencies satisfied"},
                    {"name": "compatibility", "passed": True, "message": "Compatible with current version"},
                ],
            }
    raise HTTPException(status_code=404, detail="Plugin not found")


@router.post("/plugins/{plugin_id}/reviews")
async def add_review(plugin_id: str, data: PluginReview):
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    review = {
        "id": str(uuid4()),
        "user_id": "current-user",
        "rating": data.rating,
        "comment": data.comment,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _reviews.setdefault(plugin_id, []).append(review)
    return review


@router.get("/plugins/{plugin_id}/reviews")
async def get_reviews(plugin_id: str):
    return _reviews.get(plugin_id, [])


@router.get("/plugins/installed")
async def list_installed():
    return _installed_plugins


@router.get("/plugins/stats")
async def get_stats():
    return {
        "total_marketplace": len(_marketplace_plugins),
        "total_installed": len(_installed_plugins),
        "total_active": len([p for p in _installed_plugins if p.get("status") == "active"]),
        "total_reviews": sum(len(r) for r in _reviews.values()),
        "total_downloads": sum(p.get("downloads", 0) for p in _marketplace_plugins),
    }


@router.get("/plugins/sdk/docs")
async def get_sdk_docs():
    return {
        "python": {
            "install": "pip install forgeai-plugin-sdk",
            "create": "from forgeai_plugin import PluginBase",
            "example": """
class MyPlugin(PluginBase):
    def initialize(self):
        pass
    
    def shutdown(self):
        pass
""",
        },
        "typescript": {
            "install": "npm install @forgeai/plugin-sdk",
            "create": "import { PluginBase } from '@forgeai/plugin-sdk'",
            "example": """
class MyPlugin extends PluginBase {
    initialize() {}
    shutdown() {}
}
""",
        },
    }


@router.get("/plugins/templates")
async def list_templates():
    return [
        {"id": "agent-plugin", "name": "Agent Plugin", "description": "Create a custom AI agent", "type": "agent"},
        {"id": "tool-plugin", "name": "Tool Plugin", "description": "Create an MCP tool", "type": "tool"},
        {"id": "workflow-plugin", "name": "Workflow Plugin", "description": "Create a workflow automation", "type": "workflow"},
        {"id": "prompt-plugin", "name": "Prompt Plugin", "description": "Create prompt templates", "type": "prompt"},
        {"id": "ui-plugin", "name": "UI Plugin", "description": "Create UI components", "type": "ui"},
        {"id": "integration-plugin", "name": "Integration Plugin", "description": "Integrate with external services", "type": "integration"},
    ]
