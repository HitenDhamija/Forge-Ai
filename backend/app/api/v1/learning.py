"""Learning API endpoints for experience management and recommendations.

Provides endpoints for processing workflows, retrieving patterns,
getting recommendations, and managing feedback.
"""

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.learning.learning_service import LearningService, LearningStatus
from app.schemas.common import BaseResponse, ResponseStatus

router = APIRouter(prefix="/learning", tags=["Learning"])

# Singleton learning service
_learning_service: LearningService | None = None


async def _get_service() -> LearningService:
    global _learning_service
    if _learning_service is None:
        try:
            from sqlalchemy.ext.asyncio import (
                AsyncSession,
                async_sessionmaker,
                create_async_engine,
            )
            from app.learning.experience_memory import ExperienceMemory

            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "forgeai.db")
            db_url = f"sqlite+aiosqlite:///{os.path.abspath(db_path)}"
            engine = create_async_engine(db_url, echo=False)
            session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

            async with session_factory() as session:
                memory = ExperienceMemory(session)
                _learning_service = LearningService(memory=memory, session_factory=session_factory)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to init DB persistence: %s", e)
            _learning_service = LearningService()
    return _learning_service


# ── Request / Response Models ──────────────────────────────────────────


class ProcessWorkflowRequest(BaseModel):
    """Request to process a completed workflow for learning."""

    workflow_id: str = Field(..., description="Workflow identifier")
    repository_id: str | None = Field(default=None, description="Repository identifier")
    title: str = Field(default="", description="Workflow title")
    description: str = Field(default="", description="Workflow description")
    outcome: str = Field(
        default="success", description="Workflow outcome: success, failure, partial"
    )
    files_changed: list[str] = Field(default_factory=list, description="Files changed")
    technologies: list[str] = Field(default_factory=list, description="Technologies used")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")
    execution_data: dict[str, Any] | None = Field(
        default=None, description="Execution step data"
    )
    reflection_data: dict[str, Any] | None = Field(
        default=None, description="Reflection results"
    )
    qa_data: dict[str, Any] | None = Field(default=None, description="QA test results")
    review_data: dict[str, Any] | None = Field(
        default=None, description="Code review data"
    )


class RecommendationRequest(BaseModel):
    """Request to get recommendations for a new task."""

    task_type: str = Field(..., description="Type of task")
    context_keywords: list[str] = Field(
        default_factory=list, description="Context keywords"
    )
    technologies: list[str] = Field(
        default_factory=list, description="Technologies involved"
    )
    description: str = Field(default="", description="Task description")


class FeedbackRequest(BaseModel):
    """Request to provide feedback on an experience or recommendation."""

    experience_id: str = Field(..., description="Experience identifier")
    feedback_type: str = Field(
        ..., description="Feedback type: helpful, incorrect, needs_improvement, excellent"
    )
    rating: int | None = Field(default=None, ge=1, le=5, description="Rating 1-5")
    comment: str | None = Field(default=None, description="Optional comment")


class PatternSearchRequest(BaseModel):
    """Request to search for patterns."""

    pattern_type: str | None = Field(default=None, description="Filter by pattern type")
    technologies: list[str] = Field(default_factory=list, description="Filter by technologies")
    tags: list[str] = Field(default_factory=list, description="Filter by tags")
    query: str = Field(default="", description="Search query")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")


class ProcessResponse(BaseModel):
    """Response for workflow processing."""

    task_id: str
    status: str
    experiences_count: int
    patterns_count: int
    lessons_count: int
    recommendations_count: int
    experiences: list[dict[str, Any]]
    patterns: list[dict[str, Any]]
    lessons: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]


class StatsResponse(BaseModel):
    """Response for learning statistics."""

    total_tasks: int
    total_experiences: int
    total_patterns: int
    total_lessons: int
    total_recommendations: int
    successful_experiences: int
    failed_experiences: int
    success_rate: float


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/process", response_model=BaseResponse[ProcessResponse])
async def process_workflow(request: ProcessWorkflowRequest):
    """Process a completed workflow to extract learning.

    Analyzes the workflow execution, extracts experiences,
    identifies patterns, analyzes failures, and generates
    recommendations for future similar tasks.
    """
    service = await _get_service()

    workflow_data = {
        "workflow_id": request.workflow_id,
        "repository_id": request.repository_id,
        "title": request.title,
        "description": request.description,
        "outcome": request.outcome,
        "files_changed": request.files_changed,
        "technologies": request.technologies,
        **request.context,
    }

    task = await service.process_workflow(
        workflow_data=workflow_data,
        execution_data=request.execution_data,
        reflection_data=request.reflection_data,
        qa_data=request.qa_data,
        review_data=request.review_data,
    )

    if task.status == LearningStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {'; '.join(task.errors)}",
        )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Workflow processed for learning",
        data=ProcessResponse(
            task_id=task.task_id,
            status=task.status.value,
            experiences_count=len(task.experiences),
            patterns_count=len(task.patterns),
            lessons_count=len(task.lessons),
            recommendations_count=len(task.recommendations),
            experiences=task.experiences,
            patterns=task.patterns,
            lessons=task.lessons,
            recommendations=task.recommendations,
        ),
    )


@router.get("/patterns", response_model=BaseResponse[list[dict[str, Any]]])
async def get_patterns(
    pattern_type: str | None = None,
    technologies: str | None = None,
    limit: int = 20,
):
    """Get extracted engineering patterns."""
    service = await _get_service()

    all_patterns = []

    # Collect from in-memory tasks
    for task in service.list_tasks():
        if task.status == LearningStatus.COMPLETED:
            all_patterns.extend(task.patterns)

    # Collect from database
    if service._session_factory:
        try:
            from app.learning.experience_memory import ExperienceMemory
            async with service._session_factory() as session:
                memory = ExperienceMemory(session)
                query: dict[str, Any] = {"limit": 100}
                if pattern_type:
                    query["pattern_type"] = pattern_type
                if technologies:
                    query["technologies"] = [t.strip() for t in technologies.split(",")]
                db_patterns = await memory.search_patterns(query)
                all_patterns.extend(db_patterns)
        except Exception:
            pass

    # Filter (for in-memory patterns)
    if pattern_type:
        all_patterns = [p for p in all_patterns if p.get("pattern_type") == pattern_type]

    if technologies:
        tech_list = [t.strip() for t in technologies.split(",")]
        all_patterns = [
            p for p in all_patterns
            if any(t in p.get("technologies", []) for t in tech_list)
        ]

    # Deduplicate by name
    seen = set()
    unique_patterns = []
    for p in all_patterns:
        key = p.get("name", p.get("id", ""))
        if key and key not in seen:
            seen.add(key)
            unique_patterns.append(p)
    all_patterns = unique_patterns

    # Limit
    all_patterns = all_patterns[:limit]

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Found {len(all_patterns)} patterns",
        data=all_patterns,
    )


@router.get("/experiences", response_model=BaseResponse[list[dict[str, Any]]])
async def get_experiences(
    experience_type: str | None = None,
    outcome: str | None = None,
    limit: int = 20,
):
    """Get collected experiences."""
    service = await _get_service()

    all_experiences = []

    # Collect from in-memory tasks
    for task in service.list_tasks():
        if task.status == LearningStatus.COMPLETED:
            all_experiences.extend(task.experiences)

    # Collect from database
    if service._session_factory:
        try:
            from app.learning.experience_memory import ExperienceMemory
            async with service._session_factory() as session:
                memory = ExperienceMemory(session)
                query: dict[str, Any] = {"limit": 100}
                if experience_type:
                    query["experience_type"] = experience_type
                if outcome:
                    query["outcome"] = outcome
                db_experiences = await memory.search_experiences(query)
                all_experiences.extend(db_experiences)
        except Exception:
            pass

    # Deduplicate by id
    seen = set()
    unique_experiences = []
    for e in all_experiences:
        key = e.get("id", "")
        if key and key not in seen:
            seen.add(key)
            unique_experiences.append(e)
    all_experiences = unique_experiences

    # Filter (for in-memory experiences)
    if experience_type:
        all_experiences = [
            e for e in all_experiences if e.get("experience_type") == experience_type
        ]

    if outcome:
        all_experiences = [e for e in all_experiences if e.get("outcome") == outcome]

    # Limit
    all_experiences = all_experiences[:limit]

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Found {len(all_experiences)} experiences",
        data=all_experiences,
    )


@router.get(
    "/recommendations", response_model=BaseResponse[list[dict[str, Any]]]
)
async def get_recommendations(
    task_type: str | None = None,
    technologies: str | None = None,
):
    """Get recommendations for future tasks."""
    service = await _get_service()

    task_context = {}
    if task_type:
        task_context["task_type"] = task_type
    if technologies:
        task_context["technologies"] = [t.strip() for t in technologies.split(",")]

    recommendations = []

    # Collect from in-memory tasks
    for task in service.list_tasks():
        if task.status == LearningStatus.COMPLETED:
            recommendations.extend(task.recommendations)

    # Collect from database
    if service._session_factory:
        try:
            from app.learning.experience_memory import ExperienceMemory
            async with service._session_factory() as session:
                memory = ExperienceMemory(session)
                db_recs = await memory.get_recommendations(task_context)
                recommendations.extend(db_recs)
        except Exception:
            pass

    # If no context provided and no results yet, get all from DB
    if not task_context and not recommendations and service._session_factory:
        try:
            from app.learning.experience_memory import ExperienceMemory
            from sqlalchemy import select as sa_select
            from app.learning.models import RecommendationModel
            async with service._session_factory() as session:
                result = await session.execute(sa_select(RecommendationModel).limit(50))
                models = result.scalars().all()
                recommendations = [ExperienceMemory._recommendation_to_dict(m) for m in models]
        except Exception:
            pass

    # Deduplicate and filter old-format recs
    seen = set()
    unique = []
    for r in recommendations:
        # Skip old-format generic recs (no recommendation_type, no source_name, no description)
        rec_type = r.get("recommendation_type", "")
        source = r.get("source_name", "")
        desc = r.get("description", "")
        task_type = r.get("task_type", "").lower()

        # Old format: task_type is approach/architecture/security/testing/general with no real content
        is_old_format = (
            not rec_type
            and not source
            and not desc
            and task_type in ("approach", "architecture", "security", "testing", "general")
        )
        # Old format: has "Proven Pattern:" or "Recommended" in recommendation field
        is_old_template = (
            not rec_type
            and not source
            and any(kw in (r.get("recommendation") or "") for kw in ["Proven Pattern:", "Recommended Approach", "Architecture Recommendation", "Security Guidance", "Testing Strategy"])
        )
        # Empty rec with no useful content
        is_empty = not desc and not source and not r.get("title")

        if is_old_format or is_old_template or is_empty:
            continue

        key = r.get("id", r.get("recommendation", ""))
        if key and key not in seen:
            seen.add(key)
            unique.append(r)
    recommendations = unique

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Found {len(recommendations)} recommendations",
        data=recommendations,
    )


@router.post("/recommendations", response_model=BaseResponse[list[dict[str, Any]]])
async def generate_recommendations(request: RecommendationRequest):
    """Generate recommendations for a specific task."""
    service = await _get_service()

    task_context = {
        "task_type": request.task_type,
        "context_keywords": request.context_keywords,
        "technologies": request.technologies,
        "description": request.description,
    }

    recommendations = await service.get_recommendations(task_context)

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Generated {len(recommendations)} recommendations",
        data=recommendations,
    )


@router.post("/feedback", response_model=BaseResponse[dict[str, str]])
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on an experience or recommendation."""
    service = await _get_service()

    feedback_data = {
        "experience_id": request.experience_id,
        "feedback_type": request.feedback_type,
        "rating": request.rating,
        "comment": request.comment,
    }

    # Store feedback (in-memory for now)
    logger.info(
        "Feedback received: experience=%s, type=%s, rating=%s",
        request.experience_id,
        request.feedback_type,
        request.rating,
    )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Feedback submitted",
        data={"experience_id": request.experience_id, "status": "recorded"},
    )


@router.get("/stats", response_model=BaseResponse[StatsResponse])
async def get_stats():
    """Get learning statistics."""
    service = await _get_service()
    stats = await service.get_stats()

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Learning statistics",
        data=StatsResponse(**stats),
    )


@router.get("/growth", response_model=BaseResponse[dict[str, Any]])
async def get_growth():
    """Get growth analytics."""
    service = await _get_service()
    analytics = await service.get_growth_analytics()

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Growth analytics",
        data=analytics,
    )


@router.get("/tasks", response_model=BaseResponse[list[dict[str, Any]]])
async def list_tasks():
    """List all learning processing tasks."""
    service = await _get_service()

    # Combine in-memory tasks with database tasks
    task_list = []
    for task in service.list_tasks():
        task_list.append(
            {
                "task_id": task.task_id,
                "workflow_id": task.workflow_id,
                "repository_id": task.repository_id,
                "status": task.status.value,
                "experiences_count": len(task.experiences),
                "patterns_count": len(task.patterns),
                "lessons_count": len(task.lessons),
                "started_at": task.started_at.isoformat(),
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
            }
        )

    # Also get tasks from database
    db_tasks = await service.list_tasks_from_db()
    task_list.extend(db_tasks)

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Found {len(task_list)} tasks",
        data=task_list,
    )


# Need to import logger for the feedback endpoint
from app.core.logging import get_logger

logger = get_logger(__name__)


@router.delete("/cleanup-old", response_model=BaseResponse[dict[str, int]])
async def cleanup_old_recommendations():
    """Remove old-format recommendations from the database.

    Old recs had task_type='approach'/'architecture'/'security'/'testing'
    with generic descriptions. New recs have recommendation_type and source_name.
    """
    service = await _get_service()
    deleted = 0

    if service._session_factory:
        try:
            from sqlalchemy import delete as sa_delete
            from app.learning.models import RecommendationModel
            async with service._session_factory() as session:
                # Delete old-format recs (no recommendation_type or with generic task_types)
                old_types = ("approach", "architecture", "security", "testing")
                stmt = sa_delete(RecommendationModel).where(
                    RecommendationModel.task_type.in_(old_types)
                )
                result = await session.execute(stmt)
                deleted = result.rowcount
                await session.commit()
        except Exception as e:
            logger.warning("Failed to cleanup old recs: %s", str(e))

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Deleted {deleted} old-format recommendations",
        data={"deleted": deleted},
    )


# ── Code Analysis Endpoint ────────────────────────────────────────────

class CodeAnalysisRequest(BaseModel):
    project_path: str = Field(..., description="Path to project root directory")
    max_files: int = Field(50, description="Max files to analyze")


def _detect_architecture_from_structure(file_paths: list[str]) -> dict[str, Any]:
    """Detect architecture patterns from file directory structure."""
    dirs = set()
    for fp in file_paths:
        parts = fp.replace("\\", "/").split("/")
        if len(parts) > 1:
            dirs.add(parts[0].lower())

    patterns_found = []

    # Layered architecture detection
    layer_keywords = {"controllers", "services", "repositories", "models", "views", "routes", "handlers", "middleware"}
    matching_layers = [d for d in dirs if any(k in d for k in layer_keywords)]
    if len(matching_layers) >= 2:
        patterns_found.append({
            "name": "Layered Architecture",
            "type": "architecture",
            "confidence": min(0.5 + len(matching_layers) * 0.1, 0.9),
            "evidence": f"Found layered directory structure: {', '.join(matching_layers[:5])}",
            "directories": matching_layers[:5],
        })

    # MVC pattern
    mvc_dirs = {"models", "views", "controllers"}
    if mvc_dirs.issubset(dirs):
        patterns_found.append({
            "name": "MVC Pattern",
            "type": "architecture",
            "confidence": 0.85,
            "evidence": "Found models/, views/, controllers/ directories",
        })

    # API structure
    api_dirs = {"routes", "endpoints", "api", "controllers"}
    if any(d in dirs for d in api_dirs):
        patterns_found.append({
            "name": "API-based Architecture",
            "type": "architecture",
            "confidence": 0.7,
            "evidence": f"Found API directory: {[d for d in dirs if d in api_dirs][0]}",
        })

    return {"patterns": patterns_found, "directories": list(dirs)[:20]}


def _extract_dependencies_from_config(file_paths: list[str], project_path: str) -> dict[str, Any]:
    """Extract dependencies from config files in the project."""
    deps = {"python": [], "node": [], "system": []}
    config_files = {}

    for fp in file_paths:
        fname = os.path.basename(fp).lower()
        if fname in ("requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"):
            config_files["python"] = fp
        elif fname in ("package.json", "yarn.lock", "pnpm-lock.yaml"):
            config_files["node"] = fp
        elif fname in ("dockerfile", "docker-compose.yml", "docker-compose.yaml"):
            config_files["docker"] = fp
        elif fname in (".env", ".env.example", ".env.local"):
            config_files["env"] = fp

    # Try to read requirements.txt
    req_path = os.path.join(project_path, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, "r", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        if pkg:
                            deps["python"].append(pkg)
        except Exception:
            pass

    # Try to read package.json
    pkg_path = os.path.join(project_path, "package.json")
    if os.path.exists(pkg_path):
        try:
            import json
            with open(pkg_path, "r", errors="ignore") as f:
                data = json.load(f)
                deps["node"] = list(data.get("dependencies", {}).keys())[:30]
        except Exception:
            pass

    # Try to read pyproject.toml
    pyproject_path = os.path.join(project_path, "pyproject.toml")
    if os.path.exists(pyproject_path):
        try:
            with open(pyproject_path, "r", errors="ignore") as f:
                content = f.read()
                in_deps = False
                for line in content.split("\n"):
                    if "dependencies" in line and "[" in line:
                        in_deps = True
                    elif "[" in line and "]" in line:
                        in_deps = False
                    elif in_deps and '"' in line:
                        pkg = line.strip().strip('"').strip("'").split("==")[0].split(">=")[0].split("<")[0].strip()
                        if pkg and pkg != "python":
                            deps["python"].append(pkg)
        except Exception:
            pass

    return deps


def _analyze_code_structure(file_paths: list[str], project_path: str) -> dict[str, Any]:
    """Analyze code structure - classes, functions, imports."""
    stats = {
        "total_files": len(file_paths),
        "by_extension": {},
        "languages": set(),
        "entry_points": [],
        "config_files": [],
    }

    ext_count: dict[str, int] = {}
    for fp in file_paths:
        ext = os.path.splitext(fp)[1].lower()
        ext_count[ext] = ext_count.get(ext, 0) + 1

        # Detect entry points
        fname = os.path.basename(fp).lower()
        if fname in ("main.py", "app.py", "server.py", "manage.py", "index.js", "index.ts", "main.ts"):
            stats["entry_points"].append(fp)
        elif fname in ("config.py", "settings.py", "config.ts", "config.js"):
            stats["config_files"].append(fp)

    # Map extensions to languages
    ext_lang_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TSX", ".jsx": "JSX", ".java": "Java", ".go": "Go",
        ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
        ".cpp": "C++", ".c": "C", ".h": "C Header",
        ".sql": "SQL", ".yaml": "YAML", ".yml": "YAML",
        ".json": "JSON", ".toml": "TOML", ".md": "Markdown",
        ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
        ".tf": "Terraform", ".sh": "Shell", ".bash": "Shell",
    }

    for ext, count in ext_count.items():
        lang = ext_lang_map.get(ext, ext)
        stats["by_extension"][ext] = count
        if lang in ext_lang_map.values():
            stats["languages"].add(lang)

    stats["languages"] = list(stats["languages"])
    return stats


@router.post("/analyze-code", response_model=BaseResponse[dict[str, Any]])
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze project code structure and detect patterns."""
    project_path = request.project_path

    if not os.path.exists(project_path):
        raise HTTPException(status_code=400, detail=f"Path not found: {project_path}")

    # Collect file paths
    file_paths = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".next", "dist", "build", ".venv", "venv", "env"}
    skip_exts = {".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe", ".bin"}

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        rel_root = os.path.relpath(root, project_path)
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in skip_exts:
                file_paths.append(os.path.join(rel_root, f))
        if len(file_paths) >= request.max_files * 2:
            break

    file_paths = file_paths[:request.max_files]

    # Run analysis
    architecture = _detect_architecture_from_structure(file_paths)
    dependencies = _extract_dependencies_from_config(file_paths, project_path)
    structure = _analyze_code_structure(file_paths, project_path)

    # Combine findings
    result = {
        "project_path": project_path,
        "architecture": architecture,
        "dependencies": dependencies,
        "structure": structure,
        "file_count": len(file_paths),
        "files_sample": file_paths[:20],
    }

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Analyzed {len(file_paths)} files",
        data=result,
    )
