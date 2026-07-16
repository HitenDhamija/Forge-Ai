"""Standalone ForgeAI server - runs without legacy dependencies."""

import sys
import os
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger("forgeai.startup")

# Create app
app = FastAPI(
    title="ForgeAI",
    version="1.0.0-rc1",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def restore_persisted_data():
    """Restore repos, projects, and workflows from disk on startup."""
    try:
        from app.persistence import load_metadata
        meta = load_metadata()
        if not meta:
            logger.info("No persisted data found — starting fresh")
            return

        # Restore repositories
        repos = meta.get("repositories", [])
        if repos:
            try:
                from app.api.v1.repositories_standalone import _repositories, RepositoryInfo
                from datetime import datetime, UTC
                for r in repos:
                    local_path = r.get("local_path", "")
                    if local_path and os.path.isdir(local_path):
                        info = RepositoryInfo(
                            id=r["id"], name=r["name"],
                            description=r.get("description"),
                            status=r.get("status", "ready"),
                            import_method=r.get("import_method", "local-folder"),
                            source_url=r.get("source_url"),
                            local_path=local_path,
                            created_at=r.get("created_at", datetime.now(UTC).isoformat()),
                            analyzed_at=r.get("analyzed_at"),
                            error_message=r.get("error_message"),
                            file_count=r.get("file_count", 0),
                            total_lines=r.get("total_lines", 0),
                            languages=r.get("languages", []),
                            frameworks=r.get("frameworks", []),
                        )
                        _repositories[r["id"]] = info
                logger.info(f"Restored {len(_repositories)} repositories from disk")
            except Exception as e:
                logger.error(f"Failed to restore repos: {e}")

        # Restore projects
        projects = meta.get("projects", [])
        if projects:
            try:
                from app.api.v1.projects_standalone import _PROJECTS
                _PROJECTS.extend(projects)
                logger.info(f"Restored {len(projects)} projects from disk")
            except Exception as e:
                logger.error(f"Failed to restore projects: {e}")

        # Restore workflows
        workflows = meta.get("workflows", [])
        if workflows:
            try:
                from app.api.v1.workflows_standalone import _WORKFLOWS
                _WORKFLOWS.extend(workflows)
                logger.info(f"Restored {len(workflows)} workflows from disk")
            except Exception as e:
                logger.error(f"Failed to restore workflows: {e}")

    except Exception as e:
        logger.error(f"Startup restore failed: {e}")


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0-rc1", environment="development")


# --- Import and include our new API routers directly ---
# We import them one by one to avoid legacy module import chains
#
# IMPORTANT: Some routers already define an internal prefix (e.g. monitoring → /monitoring).
# We must NOT add another prefix when mounting them, otherwise routes get doubled.

# Auth API (mount at both /api/v1 and / for frontend compatibility)
from app.api.v1.auth.router import router as auth_router
app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
app.include_router(auth_router, prefix="", tags=["Auth"])

# Users API
from app.api.v1.users.router import router as users_router
app.include_router(users_router, prefix="/api/v1", tags=["Users"])
app.include_router(users_router, prefix="", tags=["Users"])

# Organizations API (no internal prefix)
# Studio API — internal prefix is /studio, mount at /api/v1 and /
from app.api.v1.studio import router as studio_router
app.include_router(studio_router, prefix="/api/v1", tags=["Studio"])
app.include_router(studio_router, prefix="", tags=["Studio"])

# DevOps API — internal prefix is /devops, mount at /api/v1 and /
from app.api.v1.devops import router as devops_router
app.include_router(devops_router, prefix="/api/v1", tags=["DevOps"])
app.include_router(devops_router, prefix="", tags=["DevOps"])

# Learning API — internal prefix is /learning, mount at /api/v1 and /
from app.api.v1.learning import router as learning_router
app.include_router(learning_router, prefix="/api/v1", tags=["Learning"])
app.include_router(learning_router, prefix="", tags=["Learning"])

# Monitoring API — internal prefix is /monitoring, mount at /api/v1 and / for frontend
from app.api.v1.monitoring import router as monitoring_router
app.include_router(monitoring_router, prefix="/api/v1", tags=["Monitoring"])
app.include_router(monitoring_router, prefix="", tags=["Monitoring"])

# Experience API
from app.api.v1.experience import router as experience_router
app.include_router(experience_router, prefix="/api/v1", tags=["Enterprise Experience"])
app.include_router(experience_router, prefix="", tags=["Enterprise Experience"])

# Validation API (no internal prefix)
from app.api.v1.validation import router as validation_router
app.include_router(validation_router, prefix="/api/v1/validation", tags=["Release Validation"])
app.include_router(validation_router, prefix="", tags=["Release Validation"])

# Observability API (no internal prefix)
from app.infrastructure.observability import observability_router
app.include_router(observability_router, prefix="/api/v1", tags=["Observability"])

# Repositories API (standalone - no internal prefix)
from app.api.v1.repositories_standalone import router as repositories_router
app.include_router(repositories_router, prefix="/api/v1", tags=["Repositories"])
app.include_router(repositories_router, prefix="", tags=["Repositories"])

# Software Engineer API (standalone - internal prefix is /software-engineer)
from app.api.v1.software_engineer_standalone import router as se_router
app.include_router(se_router, prefix="/api/v1", tags=["Software Engineer"])
app.include_router(se_router, prefix="", tags=["Software Engineer"])

# Notifications API (no internal prefix)
from app.api.v1.notifications import router as notifications_router
app.include_router(notifications_router, prefix="/api/v1", tags=["Notifications"])
app.include_router(notifications_router, prefix="", tags=["Notifications"])

# Agents API (standalone - no internal prefix)
from app.api.v1.agents_standalone import router as agents_standalone_router
app.include_router(agents_standalone_router, prefix="/api/v1", tags=["Agents"])
app.include_router(agents_standalone_router, prefix="", tags=["Agents"])

# Workflows API (standalone - no internal prefix)
from app.api.v1.workflows_standalone import router as workflows_standalone_router
app.include_router(workflows_standalone_router, prefix="/api/v1", tags=["Workflows"])
app.include_router(workflows_standalone_router, prefix="", tags=["Workflows"])

# Projects API (standalone - no internal prefix)
from app.api.v1.projects_standalone import router as projects_standalone_router
app.include_router(projects_standalone_router, prefix="/api/v1", tags=["Projects"])
app.include_router(projects_standalone_router, prefix="", tags=["Projects"])

# Memory API (standalone)
from app.api.v1.memory_standalone import router as memory_router
app.include_router(memory_router, prefix="/api/v1", tags=["Memory"])
app.include_router(memory_router, prefix="", tags=["Memory"])

# Planner API (standalone)
from app.api.v1.planner_standalone import router as planner_router
app.include_router(planner_router, prefix="/api/v1", tags=["Planner"])
app.include_router(planner_router, prefix="", tags=["Planner"])

# Tools API (standalone)
from app.api.v1.tools_standalone import router as tools_router
app.include_router(tools_router, prefix="/api/v1", tags=["Tools"])
app.include_router(tools_router, prefix="", tags=["Tools"])

# AI Chat API (standalone)
from app.api.v1.ai_standalone import router as ai_router
app.include_router(ai_router, prefix="/api/v1", tags=["AI"])
app.include_router(ai_router, prefix="", tags=["AI"])

# Approval API (standalone)
from app.api.v1.approval_standalone import router as approval_router
app.include_router(approval_router, prefix="/api/v1", tags=["Approval"])
app.include_router(approval_router, prefix="", tags=["Approval"])

# Workforce API (standalone)
from app.api.v1.workforce_standalone import router as workforce_router
app.include_router(workforce_router, prefix="/api/v1", tags=["Workforce"])
app.include_router(workforce_router, prefix="", tags=["Workforce"])

# Documentation API (standalone)
from app.api.v1.documentation_standalone import router as documentation_router
app.include_router(documentation_router, prefix="/api/v1", tags=["Documentation"])
app.include_router(documentation_router, prefix="", tags=["Documentation"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "ForgeAI",
        "version": "1.0.0-rc1",
        "status": "running",
        "docs": "/docs",
    }
