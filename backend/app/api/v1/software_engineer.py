"""Software Engineer Agent API Endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Any

from app.core.dependencies import get_current_user
from app.agents.software_engineer.software_engineer import (
    SoftwareEngineerAgent,
    AgentState,
    TaskType,
    TaskContext,
)

router = APIRouter()


class ExecuteTaskRequest(BaseModel):
    """Request to execute a task."""

    repository_id: str = Field(..., description="Repository identifier")
    task_description: str = Field(..., description="Task description")
    task_type: TaskType = Field(..., description="Task type")
    target_files: list[str] = Field(default_factory=list, description="Target files")


class AnalyzeRequest(BaseModel):
    """Request to analyze a task."""

    repository_id: str = Field(..., description="Repository identifier")
    task_description: str = Field(..., description="Task description")


class ApproveRequest(BaseModel):
    """Request to approve a task."""

    task_id: str = Field(..., description="Task identifier")


class RejectRequest(BaseModel):
    """Request to reject a task."""

    task_id: str = Field(..., description="Task identifier")
    reason: str = Field(..., description="Rejection reason")


class TaskResponse(BaseModel):
    """Task response."""

    task_id: str
    repository_id: str
    task_description: str
    task_type: str
    state: str
    target_files: list[str]
    generated_code: list[dict[str, Any]] | None = None
    diffs: list[dict[str, Any]] | None = None
    review_result: dict[str, Any] | None = None
    validation_result: dict[str, Any] | None = None
    commit_summary: dict[str, Any] | None = None
    guidance_response: dict[str, Any] | None = None
    error: str | None = None
    execution_log: list[dict[str, Any]]
    started_at: str
    completed_at: str | None = None


class TaskListResponse(BaseModel):
    """Task list response."""

    tasks: list[TaskResponse]
    total: int


class AnalysisResponse(BaseModel):
    """Analysis response."""

    repository_id: str
    context: dict[str, Any]
    style_profile: dict[str, Any] | None = None
    task_type_suggestion: str | None = None


def get_software_engineer(request: Request) -> SoftwareEngineerAgent:
    return request.app.state.software_engineer


@router.post("/software-engineer/execute", response_model=TaskResponse)
async def execute_task(
    request: Request,
    execute_request: ExecuteTaskRequest,
    current_user: dict = Depends(get_current_user),
):
    """Execute a software engineering task."""
    agent = get_software_engineer(request)

    task = await agent.execute_task(
        repository_id=execute_request.repository_id,
        task_description=execute_request.task_description,
        task_type=execute_request.task_type,
        target_files=execute_request.target_files,
    )

    return TaskResponse(
        task_id=task.task_id,
        repository_id=task.repository_id,
        task_description=task.task_description,
        task_type=task.task_type.value,
        state=task.state.value,
        target_files=task.target_files,
        generated_code=[
            {
                "file_path": g.file_path,
                "content": g.content,
                "explanation": g.explanation,
            }
            for g in (task.generated_code or [])
        ],
        diffs=[
            {
                "file_path": d.file_path,
                "stats": d.stats,
                "is_new_file": d.is_new_file,
            }
            for d in (task.diffs or [])
        ],
        review_result={
            "passed": task.review_result.passed,
            "score": task.review_result.score,
            "summary": task.review_result.summary,
        } if task.review_result else None,
        validation_result={
            "valid": task.validation_result.valid,
            "errors": task.validation_result.errors,
            "warnings": task.validation_result.warnings,
        } if task.validation_result else None,
        commit_summary={
            "message": task.commit_summary.message,
            "description": task.commit_summary.description,
            "files_changed": task.commit_summary.files_changed,
        } if task.commit_summary else None,
        guidance_response=task.guidance_response,
        error=task.error,
        execution_log=task.execution_log,
        started_at=task.started_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.post("/software-engineer/analyze", response_model=AnalysisResponse)
async def analyze_task(
    request: Request,
    analyze_request: AnalyzeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Analyze a task and repository."""
    agent = get_software_engineer(request)

    # Load context
    context = await agent.context_loader.load_context(
        analyze_request.repository_id,
        analyze_request.task_description,
    )

    # Analyze style
    style_files = await agent._get_style_files(
        TaskContext(
            task_id="analysis",
            repository_id=analyze_request.repository_id,
            task_description=analyze_request.task_description,
            task_type=TaskType.FEATURE,
            target_files=[],
        )
    )
    style_profile = await agent.style_analyzer.analyze(
        analyze_request.repository_id,
        style_files,
    )

    return AnalysisResponse(
        repository_id=analyze_request.repository_id,
        context={
            "summary": context.summary,
            "architecture": context.architecture,
            "dependencies": context.dependencies,
            "framework": context.framework,
            "language": context.language,
        },
        style_profile=style_profile.__dict__,
        task_type_suggestion="feature",
    )


@router.get("/software-engineer/status")
async def get_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get software engineer status."""
    agent = get_software_engineer(request)

    tasks = agent.list_tasks()
    active_tasks = [t for t in tasks if t.state in [
        AgentState.ANALYZING,
        AgentState.PLANNING,
        AgentState.GENERATING,
        AgentState.REVIEWING,
        AgentState.VALIDATING,
    ]]

    return {
        "status": "active" if active_tasks else "idle",
        "total_tasks": len(tasks),
        "active_tasks": len(active_tasks),
        "completed_tasks": len([t for t in tasks if t.state == AgentState.COMPLETED]),
        "failed_tasks": len([t for t in tasks if t.state == AgentState.FAILED]),
    }


@router.get("/software-engineer/history", response_model=TaskListResponse)
async def get_history(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get task execution history."""
    agent = get_software_engineer(request)

    tasks = agent.list_tasks()

    return TaskListResponse(
        tasks=[
            TaskResponse(
                task_id=t.task_id,
                repository_id=t.repository_id,
                task_description=t.task_description,
                task_type=t.task_type.value,
                state=t.state.value,
                target_files=t.target_files,
                error=t.error,
                execution_log=t.execution_log,
                started_at=t.started_at.isoformat(),
                completed_at=t.completed_at.isoformat() if t.completed_at else None,
            )
            for t in tasks
        ],
        total=len(tasks),
    )


@router.post("/software-engineer/approve", response_model=TaskResponse)
async def approve_task(
    request: Request,
    approve_request: ApproveRequest,
    current_user: dict = Depends(get_current_user),
):
    """Approve a completed task."""
    agent = get_software_engineer(request)

    task = await agent.approve_task(approve_request.task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found or not awaiting approval",
        )

    return TaskResponse(
        task_id=task.task_id,
        repository_id=task.repository_id,
        task_description=task.task_description,
        task_type=task.task_type.value,
        state=task.state.value,
        target_files=task.target_files,
        error=task.error,
        execution_log=task.execution_log,
        started_at=task.started_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.post("/software-engineer/reject", response_model=TaskResponse)
async def reject_task(
    request: Request,
    reject_request: RejectRequest,
    current_user: dict = Depends(get_current_user),
):
    """Reject a task."""
    agent = get_software_engineer(request)

    task = await agent.reject_task(reject_request.task_id, reject_request.reason)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        task_id=task.task_id,
        repository_id=task.repository_id,
        task_description=task.task_description,
        task_type=task.task_type.value,
        state=task.state.value,
        target_files=task.target_files,
        error=task.error,
        execution_log=task.execution_log,
        started_at=task.started_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )


@router.get("/software-engineer/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    request: Request,
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get task details."""
    agent = get_software_engineer(request)

    task = agent.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskResponse(
        task_id=task.task_id,
        repository_id=task.repository_id,
        task_description=task.task_description,
        task_type=task.task_type.value,
        state=task.state.value,
        target_files=task.target_files,
        generated_code=[
            {
                "file_path": g.file_path,
                "content": g.content,
                "explanation": g.explanation,
            }
            for g in (task.generated_code or [])
        ],
        diffs=[
            {
                "file_path": d.file_path,
                "stats": d.stats,
                "is_new_file": d.is_new_file,
            }
            for d in (task.diffs or [])
        ],
        review_result={
            "passed": task.review_result.passed,
            "score": task.review_result.score,
            "summary": task.review_result.summary,
        } if task.review_result else None,
        validation_result={
            "valid": task.validation_result.valid,
            "errors": task.validation_result.errors,
            "warnings": task.validation_result.warnings,
        } if task.validation_result else None,
        commit_summary={
            "message": task.commit_summary.message,
            "description": task.commit_summary.description,
            "files_changed": task.commit_summary.files_changed,
        } if task.commit_summary else None,
        guidance_response=task.guidance_response,
        error=task.error,
        execution_log=task.execution_log,
        started_at=task.started_at.isoformat(),
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
    )
