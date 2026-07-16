"""Enterprise Experience API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, UTC

from app.api.v1.activity_store import _activities, log_activity, get_activities


router = APIRouter()


class NotificationCreate(BaseModel):
    type: str
    title: str
    message: str
    priority: Optional[str] = "medium"
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


class ActivityCreate(BaseModel):
    type: str
    action: str
    title: str
    description: Optional[str] = ""
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None


class SearchQuery(BaseModel):
    query: str
    types: Optional[list[str]] = None
    limit: Optional[int] = 20


class SettingUpdate(BaseModel):
    key: str
    value: str


_notifications = []
_recent_searches = []
_popular_searches: dict[str, int] = {}
_search_index = {}  # Built dynamically from actual data
_settings = {}
_onboarding_steps = [
    {"id": "welcome", "title": "Welcome to ForgeAI", "description": "Learn about the platform", "order": 1, "completed": False, "skippable": False},
    {"id": "connect_repo", "title": "Connect Your First Repository", "description": "Add a repository to analyze", "order": 2, "completed": False, "skippable": True},
    {"id": "explore_memory", "title": "Explore the Memory System", "description": "See how AI remembers context", "order": 3, "completed": False, "skippable": True},
    {"id": "run_workflow", "title": "Run a Workflow", "description": "Execute your first workflow", "order": 4, "completed": False, "skippable": True},
    {"id": "inspect_results", "title": "Inspect AI Results", "description": "Review AI analysis output", "order": 5, "completed": False, "skippable": True},
    {"id": "invite_team", "title": "Invite Your Team", "description": "Collaborate with team members", "order": 6, "completed": False, "skippable": True},
]
_tutorials = [
    {"id": "getting-started", "title": "Getting Started with ForgeAI", "description": "Learn the basics of the platform", "difficulty": "beginner", "estimated_minutes": 10, "steps": 5},
    {"id": "repo-intelligence", "title": "Understanding Repository Intelligence", "description": "Deep dive into repo analysis", "difficulty": "intermediate", "estimated_minutes": 15, "steps": 7},
    {"id": "ai-agents", "title": "Working with AI Agents", "description": "Create and manage AI agents", "difficulty": "intermediate", "estimated_minutes": 20, "steps": 8},
    {"id": "workflows", "title": "Building Workflows", "description": "Design automated workflows", "difficulty": "advanced", "estimated_minutes": 25, "steps": 10},
]


@router.get("/experience/notifications")
async def list_notifications(user_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    results = _notifications.copy()
    if user_id:
        results = [n for n in results if n.get("user_id") == user_id]
    if status:
        results = [n for n in results if n.get("status") == status]
    return results[:limit]


@router.post("/experience/notifications")
async def create_notification(data: NotificationCreate):
    notification = {
        "id": str(uuid4()),
        "type": data.type,
        "title": data.title,
        "message": data.message,
        "priority": data.priority,
        "status": "unread",
        "entity_type": data.entity_type,
        "entity_id": data.entity_id,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _notifications.append(notification)
    return notification


@router.put("/experience/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    for n in _notifications:
        if n["id"] == notification_id:
            n["status"] = "read"
            n["read_at"] = datetime.now(UTC).isoformat()
            return {"status": "read"}
    raise HTTPException(status_code=404, detail="Notification not found")


@router.put("/experience/notifications/read-all")
async def mark_all_read(user_id: Optional[str] = None):
    count = 0
    for n in _notifications:
        if n.get("status") == "unread":
            if user_id is None or n.get("user_id") == user_id:
                n["status"] = "read"
                n["read_at"] = datetime.now(UTC).isoformat()
                count += 1
    return {"marked_read": count}


@router.get("/experience/notifications/unread-count")
async def get_unread_count(user_id: Optional[str] = None):
    count = sum(1 for n in _notifications if n.get("status") == "unread")
    return {"count": count}


@router.delete("/experience/notifications/{notification_id}")
async def delete_notification(notification_id: str):
    global _notifications
    _notifications = [n for n in _notifications if n["id"] != notification_id]
    return {"status": "deleted"}


@router.get("/experience/activity")
async def list_activity(limit: int = 50, activity_type: Optional[str] = None, user_id: Optional[str] = None):
    results = get_activities(limit=limit)
    if activity_type:
        results = [a for a in results if a.get("type") == activity_type]
    if user_id:
        results = [a for a in results if a.get("user_id") == user_id]
    return results


@router.post("/experience/activity")
async def log_activity_endpoint(data: ActivityCreate):
    activity = log_activity(
        activity_type=data.type,
        action=data.action,
        title=data.title,
        description=data.description or "",
        entity_type=data.entity_type or "",
        entity_id=data.entity_id or "",
    )
    return activity


@router.get("/experience/activity/entity/{entity_type}/{entity_id}")
async def get_entity_activity(entity_type: str, entity_id: str):
    return [a for a in _activities if a.get("entity_type") == entity_type and a.get("entity_id") == entity_id]


@router.get("/experience/search")
async def global_search(query: str, types: Optional[str] = None, limit: int = 20):
    _rebuild_search_index()
    results = []
    query_lower = query.lower()

    search_types = types.split(",") if types else None

    # Track the search
    _track_search(query)

    for category, items in _search_index.items():
        if search_types and category not in search_types:
            continue
        for item in items:
            if (query_lower in item.get("title", "").lower() or
                query_lower in item.get("description", "").lower()):
                results.append({
                    "id": item["id"],
                    "type": item["type"],
                    "title": item["title"],
                    "description": item.get("description", ""),
                    "score": 0.9 if query_lower in item.get("title", "").lower() else 0.7,
                })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit]


def _rebuild_search_index():
    """Rebuild search index from actual platform data."""
    global _search_index
    _search_index = {}

    # Index repositories
    try:
        from app.api.v1.repositories_standalone import _repositories
        _search_index["repositories"] = [
            {"id": repo_id, "title": repo.name, "description": getattr(repo, "description", "") or "", "type": "repository"}
            for repo_id, repo in _repositories.items()
        ]
    except Exception:
        _search_index["repositories"] = []

    # Index agents
    try:
        from app.api.v1.agents_standalone import _AGENTS
        _search_index["agents"] = [
            {"id": agent.get("name", str(i)), "title": agent.get("name", ""), "description": agent.get("description", ""), "type": "agent"}
            for i, agent in enumerate(_AGENTS)
        ]
    except Exception:
        _search_index["agents"] = []

    # Index workflows
    try:
        from app.api.v1.workflows_standalone import _WORKFLOWS
        _search_index["workflows"] = [
            {"id": wf.get("id", str(i)), "title": wf.get("title", wf.get("name", "")), "description": wf.get("description", ""), "type": "workflow"}
            for i, wf in enumerate(_WORKFLOWS)
        ]
    except Exception:
        _search_index["workflows"] = []

    # Index memory chunks
    try:
        from app.api.v1.memory_standalone import _indexed_repositories
        _search_index["memory"] = [
            {"id": r["id"], "title": r["name"], "description": f"{r.get('chunks', 0)} indexed chunks", "type": "memory"}
            for r in _indexed_repositories
        ]
    except Exception:
        _search_index["memory"] = []

    # Static knowledge/prompts (platform features)
    _search_index["knowledge"] = [
        {"id": "know-1", "title": "JWT Implementation", "description": "Reusable JWT authentication pattern", "type": "knowledge"},
        {"id": "know-2", "title": "Error Handling", "description": "Standardized error handling approach", "type": "knowledge"},
    ]
    _search_index["prompts"] = [
        {"id": "prompt-1", "title": "Code Review Prompt", "description": "Prompt for automated code review", "type": "prompt"},
        {"id": "prompt-2", "title": "Documentation Prompt", "description": "Generate documentation from code", "type": "prompt"},
    ]


def _track_search(query: str):
    """Track a search query for recent/popular."""
    from datetime import datetime, UTC
    q = query.strip().lower()
    if not q:
        return
    # Add to recent (deduplicate, keep latest)
    global _recent_searches
    _recent_searches = [s for s in _recent_searches if s["query"].lower() != q]
    _recent_searches.insert(0, {"query": query.strip(), "timestamp": datetime.now(UTC).isoformat()})
    _recent_searches = _recent_searches[:20]
    # Increment popular count
    _popular_searches[q] = _popular_searches.get(q, 0) + 1


@router.get("/experience/search/recent")
async def get_recent_searches(user_id: Optional[str] = None, limit: int = 10):
    return _recent_searches[:limit]


@router.get("/experience/search/popular")
async def get_popular_searches(limit: int = 10):
    sorted_searches = sorted(_popular_searches.items(), key=lambda x: x[1], reverse=True)
    return [{"query": q, "count": c} for q, c in sorted_searches[:limit]]


@router.get("/experience/settings")
async def get_settings(category: Optional[str] = None):
    settings = _get_default_settings()
    if category:
        return {k: v for k, v in settings.items() if v.get("category") == category}
    return settings


@router.get("/experience/settings/{key}")
async def get_setting(key: str):
    settings = _get_default_settings()
    if key in settings:
        return settings[key]
    raise HTTPException(status_code=404, detail="Setting not found")


@router.put("/experience/settings")
async def update_setting(data: SettingUpdate):
    _settings[data.key] = data.value
    return {"status": "updated", "key": data.key, "value": data.value}


@router.post("/experience/settings/reset")
async def reset_settings(category: Optional[str] = None):
    return {"status": "reset", "category": category}


@router.get("/experience/onboarding/steps")
async def get_onboarding_steps():
    return _onboarding_steps


@router.get("/experience/onboarding/state")
async def get_onboarding_state(user_id: str = "current-user"):
    completed = [s for s in _onboarding_steps if s.get("completed")]
    return {
        "user_id": user_id,
        "current_step": _onboarding_steps[0]["id"] if _onboarding_steps else None,
        "completed_steps": len(completed),
        "total_steps": len(_onboarding_steps),
        "is_complete": len(completed) == len(_onboarding_steps),
        "progress": len(completed) / len(_onboarding_steps) * 100 if _onboarding_steps else 0,
    }


@router.put("/experience/onboarding/step/{step_id}")
async def complete_onboarding_step(step_id: str, user_id: str = "current-user"):
    for step in _onboarding_steps:
        if step["id"] == step_id:
            step["completed"] = True
            return {"status": "completed", "step": step_id}
    raise HTTPException(status_code=404, detail="Step not found")


@router.post("/experience/onboarding/skip")
async def skip_onboarding(user_id: str = "current-user"):
    for step in _onboarding_steps:
        step["completed"] = True
    return {"status": "skipped"}


@router.get("/experience/tutorials")
async def list_tutorials():
    return _tutorials


@router.get("/experience/tutorials/{tutorial_id}")
async def get_tutorial(tutorial_id: str):
    for t in _tutorials:
        if t["id"] == tutorial_id:
            return t
    raise HTTPException(status_code=404, detail="Tutorial not found")


@router.get("/experience/command-palette")
async def get_command_palette_items():
    return [
        {"id": "open-repo", "label": "Open Repository", "category": "navigation", "icon": "GitBranch", "shortcut": ""},
        {"id": "search-workflows", "label": "Search Workflows", "category": "navigation", "icon": "GitMerge", "shortcut": ""},
        {"id": "search-agents", "label": "Search Agents", "category": "navigation", "icon": "Bot", "shortcut": ""},
        {"id": "run-workflow", "label": "Run Workflow", "category": "action", "icon": "Play", "shortcut": ""},
        {"id": "switch-model", "label": "Switch AI Model", "category": "action", "icon": "Brain", "shortcut": ""},
        {"id": "open-settings", "label": "Open Settings", "category": "navigation", "icon": "Settings", "shortcut": ""},
        {"id": "search-knowledge", "label": "Search Knowledge", "category": "navigation", "icon": "Database", "shortcut": ""},
        {"id": "go-dashboard", "label": "Go to Dashboard", "category": "navigation", "icon": "LayoutDashboard", "shortcut": ""},
        {"id": "go-workflows", "label": "Go to Workflows", "category": "navigation", "icon": "GitMerge", "shortcut": ""},
        {"id": "go-agents", "label": "Go to Agents", "category": "navigation", "icon": "Bot", "shortcut": ""},
        {"id": "go-monitoring", "label": "Go to Monitoring", "category": "navigation", "icon": "Activity", "shortcut": ""},
        {"id": "go-studio", "label": "Go to Studio", "category": "navigation", "icon": "Sparkles", "shortcut": ""},
    ]


@router.get("/experience/shortcuts")
async def get_keyboard_shortcuts():
    return {
        "general": [
            {"keys": ["Ctrl", "K"], "action": "Open Command Palette"},
            {"keys": ["Ctrl", "/"], "action": "Toggle Search"},
            {"keys": ["Ctrl", "B"], "action": "Toggle Sidebar"},
            {"keys": ["Escape"], "action": "Close Modal/Overlay"},
        ],
        "navigation": [
            {"keys": ["G", "D"], "action": "Go to Dashboard"},
            {"keys": ["G", "W"], "action": "Go to Workflows"},
            {"keys": ["G", "A"], "action": "Go to Agents"},
            {"keys": ["G", "M"], "action": "Go to Monitoring"},
            {"keys": ["G", "S"], "action": "Go to Studio"},
        ],
        "actions": [
            {"keys": ["R", "W"], "action": "Run Workflow"},
            {"keys": ["N", "N"], "action": "New Notification"},
            {"keys": ["?"], "action": "Show Keyboard Shortcuts"},
        ],
    }


def _get_activity_icon(activity_type: str, action: str) -> str:
    icons = {
        ("workflow", "started"): "Play",
        ("workflow", "completed"): "CheckCircle",
        ("workflow", "failed"): "XCircle",
        ("repository", "indexed"): "GitBranch",
        ("agent", "completed"): "Bot",
        ("execution", "started"): "Terminal",
        ("organization", "created"): "Building2",
    }
    return icons.get((activity_type, action), "Activity")


def _get_default_settings() -> dict:
    return {
        "app_name": {"key": "app_name", "label": "Application Name", "type": "string", "category": "general", "default": "ForgeAI", "value": _settings.get("app_name", "ForgeAI")},
        "app_url": {"key": "app_url", "label": "Application URL", "type": "string", "category": "general", "default": "http://localhost:3000", "value": _settings.get("app_url", "http://localhost:3000")},
        "timezone": {"key": "timezone", "label": "Timezone", "type": "select", "category": "general", "default": "UTC", "options": ["UTC", "US/Eastern", "US/Pacific", "Europe/London"], "value": _settings.get("timezone", "UTC")},
        "default_model": {"key": "default_model", "label": "Default AI Model", "type": "select", "category": "models", "default": "qwen2.5", "options": ["qwen2.5", "llama3", "mistral", "codellama"], "value": _settings.get("default_model", "qwen2.5")},
        "ollama_url": {"key": "ollama_url", "label": "Ollama URL", "type": "string", "category": "models", "default": "http://localhost:11434", "value": _settings.get("ollama_url", "http://localhost:11434")},
        "theme": {"key": "theme", "label": "Theme", "type": "select", "category": "appearance", "default": "dark", "options": ["dark", "light", "system"], "value": _settings.get("theme", "dark")},
        "accent_color": {"key": "accent_color", "label": "Accent Color", "type": "color", "category": "appearance", "default": "#3b82f6", "value": _settings.get("accent_color", "#3b82f6")},
        "compact_mode": {"key": "compact_mode", "label": "Compact Mode", "type": "boolean", "category": "appearance", "default": False, "value": _settings.get("compact_mode", False)},
        "email_notifications": {"key": "email_notifications", "label": "Email Notifications", "type": "boolean", "category": "notifications", "default": True, "value": _settings.get("email_notifications", True)},
        "workflow_notifications": {"key": "workflow_notifications", "label": "Workflow Notifications", "type": "boolean", "category": "notifications", "default": True, "value": _settings.get("workflow_notifications", True)},
        "debug_mode": {"key": "debug_mode", "label": "Debug Mode", "type": "boolean", "category": "developer", "default": False, "value": _settings.get("debug_mode", False)},
        "api_logging": {"key": "api_logging", "label": "API Logging", "type": "boolean", "category": "developer", "default": False, "value": _settings.get("api_logging", False)},
        "session_timeout": {"key": "session_timeout", "label": "Session Timeout (minutes)", "type": "number", "category": "security", "default": 60, "value": _settings.get("session_timeout", 60)},
        "mfa_enabled": {"key": "mfa_enabled", "label": "Multi-Factor Auth", "type": "boolean", "category": "security", "default": False, "value": _settings.get("mfa_enabled", False)},
    }
