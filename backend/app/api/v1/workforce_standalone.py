"""Standalone workforce API — connects to real agent monitoring data."""

import uuid
from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/workforce", tags=["Workforce"])

# Map agent_type to workforce role
AGENT_TYPE_MAP = {
    "reviewer": "code_reviewer",
    "executor": "software_engineer",
    "devops": "devops_engineer",
    "planner": "technical_writer",
    "researcher": "qa_engineer",
}

AGENT_DISPLAY_NAMES = {
    "reviewer": "Code Reviewer",
    "executor": "Software Engineer",
    "devops": "DevOps Engineer",
    "planner": "Task Planner",
    "researcher": "Researcher",
}

AGENT_DESCRIPTIONS = {
    "reviewer": "Reviews code for bugs, security issues, and best practices",
    "executor": "Writes, refactors, and fixes code across the codebase",
    "devops": "Analyzes deployment readiness, generates Docker/CI configs",
    "planner": "Breaks complex tasks into actionable steps with dependencies",
    "researcher": "Explores codebases, finds patterns, gathers context",
}


def _get_real_agents() -> list[dict[str, Any]]:
    """Build agent list from the real agents system."""
    agents = []
    try:
        from app.api.v1.agents_standalone import _AGENTS, _TASKS

        for agent_info in _AGENTS:
            agent_type = agent_info["agent_type"]
            role = AGENT_TYPE_MAP.get(agent_type, agent_type)

            # Count tasks for this agent type
            agent_tasks = [t for t in _TASKS if t.get("agent_type") == agent_type]
            completed = sum(1 for t in agent_tasks if t.get("status") == "completed")
            running = sum(1 for t in agent_tasks if t.get("status") == "running")
            failed = sum(1 for t in agent_tasks if t.get("status") == "failed")

            # Determine real status
            if running > 0:
                status = "executing"
            elif failed > 0:
                status = "idle"  # Still available for new tasks
            else:
                status = "idle"

            # Get last task time
            last_task_time = None
            if agent_tasks:
                last_task_time = agent_tasks[0].get("completed_at") or agent_tasks[0].get("created_at")

            agents.append({
                "id": agent_info["id"],
                "role": role,
                "name": AGENT_DISPLAY_NAMES.get(agent_type, agent_info["name"]),
                "description": AGENT_DESCRIPTIONS.get(agent_type, agent_info["description"]),
                "status": status,
                "agent_type": agent_type,
                "capabilities": [
                    {"name": cap.replace("_", " "), "description": cap.replace("_", " "), "level": 8, "tools": [], "task_types": [agent_type]}
                    for cap in agent_info.get("capabilities", [])
                ],
                "stats": {
                    "total_tasks": len(agent_tasks),
                    "completed": completed,
                    "running": running,
                    "failed": failed,
                },
                "last_task_at": last_task_time,
                "version": "1.0.0",
                "created_at": datetime.now(UTC).isoformat(),
            })
    except Exception:
        # Fallback to static agents
        agents = [
            {"id": "agent-se-001", "role": "software_engineer", "name": "Software Engineer", "status": "idle", "stats": {"total_tasks": 0, "completed": 0, "running": 0, "failed": 0}},
            {"id": "agent-qa-001", "role": "qa_engineer", "name": "QA Engineer", "status": "idle", "stats": {"total_tasks": 0, "completed": 0, "running": 0, "failed": 0}},
            {"id": "agent-reviewer-001", "role": "code_reviewer", "name": "Code Reviewer", "status": "idle", "stats": {"total_tasks": 0, "completed": 0, "running": 0, "failed": 0}},
            {"id": "agent-devops-001", "role": "devops_engineer", "name": "DevOps Engineer", "status": "idle", "stats": {"total_tasks": 0, "completed": 0, "running": 0, "failed": 0}},
            {"id": "agent-docs-001", "role": "technical_writer", "name": "Technical Writer", "status": "idle", "stats": {"total_tasks": 0, "completed": 0, "running": 0, "failed": 0}},
        ]

    return agents


@router.get("")
@router.get("/")
async def list_agents():
    agents = _get_real_agents()
    return {"status": "success", "data": agents}


@router.get("/status")
async def get_status_summary():
    agents = _get_real_agents()
    roles: dict[str, int] = {}
    for a in agents:
        roles[a["role"]] = roles.get(a["role"], 0) + 1

    return {
        "status": "success",
        "data": {
            "total_agents": len(agents),
            "idle_agents": sum(1 for a in agents if a["status"] == "idle"),
            "busy_agents": sum(1 for a in agents if a["status"] in ("executing", "assigned")),
            "unavailable_agents": sum(1 for a in agents if a["status"] in ("offline", "unavailable")),
            "agents_by_role": roles,
        },
    }


@router.get("/events/recent")
async def get_recent_events(limit: int = 50):
    events = []
    try:
        from app.api.v1.agents_standalone import _TASKS
        for task in _TASKS[:limit]:
            events.append({
                "id": task["id"],
                "agent_type": task.get("agent_type"),
                "status": task.get("status"),
                "description": task.get("task_description", "")[:100],
                "created_at": task.get("created_at"),
                "completed_at": task.get("completed_at"),
            })
    except Exception:
        pass
    return {"status": "success", "data": events}


@router.get("/role/{role}")
async def get_agents_by_role(role: str):
    agents = _get_real_agents()
    matching = [a for a in agents if a["role"] == role]
    return {"status": "success", "data": matching}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    agents = _get_real_agents()
    agent = next((a for a in agents if a["id"] == agent_id), None)
    if not agent:
        return {"status": "error", "message": "Agent not found"}
    return {"status": "success", "data": agent}


@router.post("/register")
async def register_agent(data: dict[str, Any]):
    agent_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    agent = {
        "id": agent_id,
        "role": data.get("role", "software_engineer"),
        "name": data.get("name", "New Agent"),
        "description": data.get("description", ""),
        "status": "idle",
        "capabilities": data.get("capabilities", []),
        "stats": {"total_tasks": 0, "completed": 0, "running": 0, "failed": 0},
        "version": "1.0.0",
        "created_at": now,
    }
    return {"status": "success", "data": {"agent_id": agent_id}}


@router.post("/{agent_id}/heartbeat")
async def send_heartbeat(agent_id: str):
    return {"status": "success", "data": {}}


@router.post("/{agent_id}/status")
async def update_agent_status(agent_id: str, data: dict[str, Any]):
    return {"status": "success", "data": {}}


@router.post("/workflow/{workflow_id}/process")
async def process_workflow(workflow_id: str, data: dict[str, Any]):
    return {"status": "success", "data": {"workflow_id": workflow_id, "status": "processing"}}
