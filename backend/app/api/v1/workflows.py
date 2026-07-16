"""Workflow API endpoints."""

from fastapi import APIRouter, Request

from app.workflows.schemas import (
    TaskStatus,
    WorkflowRequest,
    WorkflowStatus,
)
from app.schemas.common import BaseResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/", response_model=BaseResponse[dict])
async def create_workflow(
    request: WorkflowRequest,
    req: Request,
) -> BaseResponse[dict]:
    """Create a new workflow.

    Args:
        request: Workflow creation request.

    Returns:
        Created workflow information.
    """
    service = req.app.state.workflow_service
    workflow = await service.create_workflow(request)
    return BaseResponse(data=workflow.model_dump())


@router.get("/", response_model=BaseResponse[list[dict]])
async def list_workflows(
    req: Request,
    status: WorkflowStatus | None = None,
    project_id: str | None = None,
) -> BaseResponse[list[dict]]:
    """List workflows with optional filters.

    Args:
        status: Filter by status.
        project_id: Filter by project ID.

    Returns:
        List of workflow information.
    """
    service = req.app.state.workflow_service
    workflows = await service.list_workflows(
        status=status,
        project_id=project_id,
    )
    return BaseResponse(data=[w.model_dump() for w in workflows])


@router.get("/{workflow_id}", response_model=BaseResponse[dict])
async def get_workflow(
    workflow_id: str,
    req: Request,
) -> BaseResponse[dict]:
    """Get workflow by ID.

    Args:
        workflow_id: Workflow ID.

    Returns:
        Workflow information.

    Raises:
        404: If workflow not found.
    """
    service = req.app.state.workflow_service
    workflow = await service.get_workflow(workflow_id)
    if not workflow:
        return BaseResponse(data={"error": "Workflow not found"})
    return BaseResponse(data=workflow.model_dump())


@router.post("/{workflow_id}/approve", response_model=BaseResponse[dict])
async def approve_workflow(
    workflow_id: str,
    req: Request,
) -> BaseResponse[dict]:
    """Approve a workflow for execution.

    Args:
        workflow_id: Workflow ID.

    Returns:
        Updated workflow information.
    """
    service = req.app.state.workflow_service
    workflow = await service.approve_workflow(workflow_id)
    return BaseResponse(data=workflow.model_dump())


@router.post("/{workflow_id}/start", response_model=BaseResponse[dict])
async def start_workflow(
    workflow_id: str,
    req: Request,
) -> BaseResponse[dict]:
    """Start workflow execution.

    Args:
        workflow_id: Workflow ID.

    Returns:
        Updated workflow information.
    """
    service = req.app.state.workflow_service
    workflow = await service.start_workflow(workflow_id)
    return BaseResponse(data=workflow.model_dump())


@router.post("/{workflow_id}/pause", response_model=BaseResponse[dict])
async def pause_workflow(
    workflow_id: str,
    req: Request,
) -> BaseResponse[dict]:
    """Pause workflow execution.

    Args:
        workflow_id: Workflow ID.

    Returns:
        Updated workflow information.
    """
    service = req.app.state.workflow_service
    workflow = await service.pause_workflow(workflow_id)
    return BaseResponse(data=workflow.model_dump())


@router.post("/{workflow_id}/resume", response_model=BaseResponse[dict])
async def resume_workflow(
    workflow_id: str,
    req: Request,
) -> BaseResponse[dict]:
    """Resume workflow execution.

    Args:
        workflow_id: Workflow ID.

    Returns:
        Updated workflow information.
    """
    service = req.app.state.workflow_service
    workflow = await service.resume_workflow(workflow_id)
    return BaseResponse(data=workflow.model_dump())


@router.post("/{workflow_id}/cancel", response_model=BaseResponse[dict])
async def cancel_workflow(
    workflow_id: str,
    req: Request,
) -> BaseResponse[dict]:
    """Cancel workflow execution.

    Args:
        workflow_id: Workflow ID.

    Returns:
        Updated workflow information.
    """
    service = req.app.state.workflow_service
    workflow = await service.cancel_workflow(workflow_id)
    return BaseResponse(data=workflow.model_dump())


@router.get("/{workflow_id}/summary", response_model=BaseResponse[dict])
async def get_execution_summary(
    workflow_id: str,
    req: Request,
) -> BaseResponse[dict]:
    """Get execution summary for a workflow.

    Args:
        workflow_id: Workflow ID.

    Returns:
        Execution summary.
    """
    service = req.app.state.workflow_service
    summary = await service.get_execution_summary(workflow_id)
    return BaseResponse(data=summary)
