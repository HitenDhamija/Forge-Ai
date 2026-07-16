"""Standalone projects API — works without legacy imports."""

import uuid
from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.api.v1.activity_store import log_activity

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    languages: list[str] = []
    frameworks: list[str] = []


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


_PROJECTS: list[dict[str, Any]] = []


def _load_projects():
    """Load projects from disk on startup."""
    try:
        from app.persistence import load_projects
        saved = load_projects()
        _PROJECTS.extend(saved)
        if saved:
            import logging
            logging.getLogger(__name__).info(f"Loaded {len(saved)} projects from disk")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"_load_projects failed: {e}")


def _persist_projects():
    """Save projects to disk so they survive restart."""
    try:
        from app.persistence import save_projects
        save_projects(_PROJECTS)
    except Exception:
        pass


@router.get("")
@router.get("/")
async def list_projects():
    seen = set()
    unique = []
    for p in _PROJECTS:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)
    if len(unique) != len(_PROJECTS):
        _PROJECTS.clear()
        _PROJECTS.extend(unique)
        _persist_projects()
    return {"status": "success", "data": _PROJECTS}


@router.post("")
@router.post("/")
async def create_project(request: ProjectCreate):
    project_id = str(uuid.uuid4())
    project = {
        "id": project_id,
        "name": request.name,
        "description": request.description,
        "languages": request.languages,
        "frameworks": request.frameworks,
        "status": "active",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _PROJECTS.insert(0, project)
    _persist_projects()

    # Log activity
    log_activity(
        "project", "created",
        f"Created project: {request.name}",
        request.description or f"Project with {len(request.languages)} languages",
        "project", project_id,
    )

    return {"status": "success", "data": project}


@router.get("/{project_id}")
async def get_project(project_id: str):
    project = next((p for p in _PROJECTS if p["id"] == project_id), None)
    if not project:
        return {"status": "error", "message": "Project not found"}
    return {"status": "success", "data": project}


@router.put("/{project_id}")
async def update_project(project_id: str, request: ProjectUpdate):
    project = next((p for p in _PROJECTS if p["id"] == project_id), None)
    if not project:
        return {"status": "error", "message": "Project not found"}
    if request.name is not None:
        project["name"] = request.name
    if request.description is not None:
        project["description"] = request.description
    project["updated_at"] = datetime.now(UTC).isoformat()
    return {"status": "success", "data": project}


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    global _PROJECTS
    before = len(_PROJECTS)
    _PROJECTS = [p for p in _PROJECTS if p["id"] != project_id]
    if len(_PROJECTS) == before:
        return {"status": "error", "message": "Project not found"}
    _persist_projects()

    log_activity(
        "project", "deleted",
        "Deleted a project",
        "",
        "project", project_id,
    )

    return {"status": "success", "message": "Project deleted"}
