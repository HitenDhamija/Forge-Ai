"""Shared activity logger for standalone APIs.

Activities are persisted to disk so they survive server restarts.
"""

from uuid import uuid4
from datetime import datetime, UTC
from typing import Optional
import json
import os


# Shared activity store - imported by experience.py and standalone APIs
_activities: list[dict] = []

_ACTIVITIES_FILE = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "forgeai", "activities.json")


def _persist_activities():
    """Save activities to disk."""
    try:
        os.makedirs(os.path.dirname(_ACTIVITIES_FILE), exist_ok=True)
        with open(_ACTIVITIES_FILE, "w", encoding="utf-8") as f:
            json.dump(_activities[-500:], f, indent=2, ensure_ascii=False)  # keep last 500
    except Exception:
        pass


def _load_activities():
    """Load activities from disk on startup."""
    try:
        if os.path.exists(_ACTIVITIES_FILE):
            with open(_ACTIVITIES_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            _activities.extend(saved)
    except Exception:
        pass


_load_activities()


def _backfill_from_existing_data():
    """Generate activities from existing repos/projects/workflows if store is empty."""
    if _activities:
        return
    try:
        # Backfill from repositories_standalone
        from app.api.v1.repositories_standalone import _repositories
        for repo_id, repo in _repositories.items():
            name = getattr(repo, "name", repo_id)
            created = getattr(repo, "created_at", "") or ""
            file_count = getattr(repo, "file_count", 0)
            _activities.append({
                "id": str(uuid4()),
                "type": "repository",
                "action": "imported",
                "title": f"Imported repository: {name}",
                "description": f"Analyzed {file_count} files",
                "entity_type": "repository",
                "entity_id": repo_id,
                "timestamp": created or datetime.now(UTC).isoformat(),
                "icon": "GitBranch",
            })
    except Exception:
        pass

    try:
        # Backfill from projects_standalone
        from app.api.v1.projects_standalone import _PROJECTS
        for proj in _PROJECTS:
            proj_id = proj.get("id", "")
            name = proj.get("name", "")
            created = proj.get("created_at", "")
            _activities.append({
                "id": str(uuid4()),
                "type": "project",
                "action": "created",
                "title": f"Created project: {name}",
                "description": "",
                "entity_type": "project",
                "entity_id": proj_id,
                "timestamp": created or datetime.now(UTC).isoformat(),
                "icon": "FolderKanban",
            })
    except Exception:
        pass

    try:
        # Backfill from workflows_standalone
        from app.api.v1.workflows_standalone import _WORKFLOWS
        for wf in _WORKFLOWS:
            wf_id = wf.get("id", "")
            name = wf.get("title", wf.get("name", ""))
            created = wf.get("created_at", "")
            tasks = wf.get("tasks", [])
            _activities.append({
                "id": str(uuid4()),
                "type": "workflow",
                "action": "created",
                "title": f"Created workflow: {name}",
                "description": f"{len(tasks)} tasks",
                "entity_type": "workflow",
                "entity_id": wf_id,
                "timestamp": created or datetime.now(UTC).isoformat(),
                "icon": "GitMerge",
            })
    except Exception:
        pass

    try:
        # Backfill from agents_standalone
        from app.api.v1.agents_standalone import _AGENTS
        for agent in _AGENTS:
            agent_id = agent.get("id", agent.get("name", ""))
            name = agent.get("name", "")
            _activities.append({
                "id": str(uuid4()),
                "type": "agent",
                "action": "created",
                "title": f"Agent ready: {name}",
                "description": agent.get("description", ""),
                "entity_type": "agent",
                "entity_id": str(agent_id),
                "timestamp": datetime.now(UTC).isoformat(),
                "icon": "Bot",
            })
    except Exception:
        pass

    if _activities:
        _persist_activities()


_backfill_from_existing_data()


def log_activity(
    activity_type: str,
    action: str,
    title: str,
    description: str = "",
    entity_type: str = "",
    entity_id: str = "",
) -> dict:
    """Log an activity event. Returns the created activity dict."""
    icon = _get_activity_icon(activity_type, action)
    activity = {
        "id": str(uuid4()),
        "type": activity_type,
        "action": action,
        "title": title,
        "description": description,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "icon": icon,
    }
    _activities.append(activity)
    _persist_activities()
    return activity


def get_activities(limit: int = 50) -> list[dict]:
    """Get recent activities, sorted by timestamp descending."""
    sorted_activities = sorted(
        _activities, key=lambda x: x.get("timestamp", ""), reverse=True
    )
    return sorted_activities[:limit]


def _get_activity_icon(activity_type: str, action: str) -> str:
    icons = {
        ("project", "created"): "FolderKanban",
        ("project", "deleted"): "Trash2",
        ("repository", "imported"): "GitBranch",
        ("workflow", "created"): "GitMerge",
        ("workflow", "started"): "Play",
        ("workflow", "completed"): "CheckCircle",
        ("workflow", "failed"): "XCircle",
        ("agent", "task_assigned"): "Bot",
        ("agent", "task_completed"): "CheckCircle",
        ("agent", "task_failed"): "XCircle",
    }
    return icons.get((activity_type, action), "Activity")
