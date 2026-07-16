"""DevOps API endpoints for deployment automation.

Provides endpoints for analyzing projects, generating deployment artifacts,
and retrieving deployment reports and configurations.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.devops.devops_agent import ArtifactType, DevOpsAgent, DevOpsStatus
from app.schemas.common import BaseResponse, ResponseStatus

router = APIRouter(prefix="/devops", tags=["DevOps"])

# Singleton DevOps agent
_devops_agent: DevOpsAgent | None = None


def _get_agent() -> DevOpsAgent:
    global _devops_agent
    if _devops_agent is None:
        _devops_agent = DevOpsAgent()
    return _devops_agent


# ── Request / Response Models ──────────────────────────────────────────


class AnalyzeRequest(BaseModel):
    """Request to run deployment analysis."""

    repository_id: str = Field(..., description="Repository identifier")
    project_path: str = Field(
        default=".", description="Path to the project root"
    )
    description: str = Field(default="", description="Optional task description")
    artifact_types: list[str] | None = Field(
        default=None,
        description="Specific artifacts to generate (dockerfile, compose, github_actions, kubernetes, all)",
    )


class GenerateRequest(BaseModel):
    """Request to generate specific deployment artifacts."""

    repository_id: str = Field(..., description="Repository identifier")
    project_path: str = Field(default=".", description="Path to the project root")
    artifact_type: str = Field(
        ..., description="Artifact type: dockerfile, compose, compose_dev, github_actions, kubernetes"
    )
    config: dict[str, Any] | None = Field(
        default=None, description="Optional generation configuration"
    )


class ArtifactResponse(BaseModel):
    """Response for generated artifacts."""

    task_id: str
    status: str
    artifacts: dict[str, Any]
    analysis: dict[str, Any] | None = None
    security: dict[str, Any] | None = None
    score: dict[str, Any] | None = None


class ReportResponse(BaseModel):
    """Response for deployment report."""

    task_id: str
    report: dict[str, Any]
    score: dict[str, Any] | None = None


class DockerResponse(BaseModel):
    """Response for Docker configurations."""

    dockerfile: dict[str, Any] | None = None
    compose: dict[str, Any] | None = None
    compose_dev: dict[str, Any] | None = None


class GitHubActionsResponse(BaseModel):
    """Response for GitHub Actions workflows."""

    workflows: list[dict[str, Any]]
    total_workflows: int


class KubernetesResponse(BaseModel):
    """Response for Kubernetes manifests."""

    resources: list[dict[str, Any]]
    namespace: str
    total_resources: int


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/analyze", response_model=BaseResponse[ArtifactResponse])
async def analyze_deployment(request: AnalyzeRequest):
    """Analyze project deployment readiness and generate artifacts.

    Runs a comprehensive analysis of the project including:
    - Infrastructure detection
    - Security validation
    - Production readiness scoring
    - Deployment artifact generation
    """
    agent = _get_agent()

    artifact_types = None
    if request.artifact_types:
        artifact_types = [ArtifactType(t) for t in request.artifact_types]

    task = await agent.analyze(
        repository_id=request.repository_id,
        project_path=request.project_path,
        description=request.description,
        artifact_types=artifact_types,
    )

    if task.status == DevOpsStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {'; '.join(task.errors)}",
        )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Deployment analysis completed",
        data=ArtifactResponse(
            task_id=task.task_id,
            status=task.status.value,
            artifacts=task.artifacts,
            analysis=task.analysis,
            security=task.security,
            score=task.score,
        ),
    )


@router.post("/generate", response_model=BaseResponse[ArtifactResponse])
async def generate_artifact(request: GenerateRequest):
    """Generate a specific deployment artifact."""
    agent = _get_agent()

    try:
        artifact_type = ArtifactType(request.artifact_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid artifact type: {request.artifact_type}",
        )

    task = await agent.analyze(
        repository_id=request.repository_id,
        project_path=request.project_path,
        artifact_types=[artifact_type],
    )

    if task.status == DevOpsStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {'; '.join(task.errors)}",
        )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Generated {request.artifact_type}",
        data=ArtifactResponse(
            task_id=task.task_id,
            status=task.status.value,
            artifacts=task.artifacts,
            analysis=task.analysis,
            security=task.security,
            score=task.score,
        ),
    )


@router.get("/report/{task_id}", response_model=BaseResponse[ReportResponse])
async def get_report(task_id: str):
    """Get deployment report for a completed analysis."""
    agent = _get_agent()
    task = await agent.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != DevOpsStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed. Status: {task.status.value}",
        )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Deployment report retrieved",
        data=ReportResponse(
            task_id=task.task_id,
            report=task.report or {},
            score=task.score,
        ),
    )


@router.get("/docker/{task_id}", response_model=BaseResponse[DockerResponse])
async def get_docker(task_id: str):
    """Get Docker configurations for a completed analysis."""
    agent = _get_agent()
    task = await agent.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != DevOpsStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed. Status: {task.status.value}",
        )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Docker configurations retrieved",
        data=DockerResponse(
            dockerfile=task.artifacts.get("dockerfile"),
            compose=task.artifacts.get("compose"),
            compose_dev=task.artifacts.get("compose_dev"),
        ),
    )


@router.get(
    "/github-actions/{task_id}",
    response_model=BaseResponse[GitHubActionsResponse],
)
async def get_github_actions(task_id: str):
    """Get GitHub Actions workflows for a completed analysis."""
    agent = _get_agent()
    task = await agent.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != DevOpsStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed. Status: {task.status.value}",
        )

    ga_data = task.artifacts.get("github_actions", {})
    workflows = ga_data.get("workflows", [])

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="GitHub Actions workflows retrieved",
        data=GitHubActionsResponse(
            workflows=workflows,
            total_workflows=len(workflows),
        ),
    )


@router.get(
    "/kubernetes/{task_id}",
    response_model=BaseResponse[KubernetesResponse],
)
async def get_kubernetes(task_id: str):
    """Get Kubernetes manifests for a completed analysis."""
    agent = _get_agent()
    task = await agent.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != DevOpsStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed. Status: {task.status.value}",
        )

    k8s_data = task.artifacts.get("kubernetes", {})
    resources = k8s_data.get("resources", [])

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Kubernetes manifests retrieved",
        data=KubernetesResponse(
            resources=resources,
            namespace=k8s_data.get("namespace", "default"),
            total_resources=len(resources),
        ),
    )


@router.get("/tasks", response_model=BaseResponse[list[dict[str, Any]]])
async def list_tasks(status: str | None = None):
    """List all DevOps analysis tasks."""
    agent = _get_agent()

    filter_status = None
    if status:
        try:
            filter_status = DevOpsStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}",
            )

    tasks = agent.list_tasks(filter_status)

    task_list = []
    for task in tasks:
        task_list.append(
            {
                "task_id": task.task_id,
                "repository_id": task.repository_id,
                "status": task.status.value,
                "description": task.description,
                "has_score": task.score is not None,
                "overall_score": (
                    task.score.get("overall_score", 0) if task.score else None
                ),
                "started_at": task.started_at.isoformat(),
                "completed_at": (
                    task.completed_at.isoformat() if task.completed_at else None
                ),
            }
        )

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Found {len(task_list)} tasks",
        data=task_list,
    )


@router.get("/tasks/{task_id}", response_model=BaseResponse[ArtifactResponse])
async def get_task(task_id: str):
    """Get a specific DevOps task by ID."""
    agent = _get_agent()
    task = await agent.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return BaseResponse(
        status=ResponseStatus.SUCCESS,
        message="Task retrieved",
        data=ArtifactResponse(
            task_id=task.task_id,
            status=task.status.value,
            artifacts=task.artifacts,
            analysis=task.analysis,
            security=task.security,
            score=task.score,
        ),
    )
