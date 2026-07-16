"""Agent API endpoints."""

from fastapi import APIRouter, Request

from app.agents.schemas import (
    AgentType,
    TaskRequest,
    TaskStatus,
)
from app.schemas.common import BaseResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=BaseResponse[list[dict]])
async def list_agents(
    request: Request,
) -> BaseResponse[list[dict]]:
    """List all available agents.

    Returns:
        List of agent information dictionaries.
    """
    orchestrator = request.app.state.agent_orchestrator
    return BaseResponse(data=orchestrator.list_agents())


@router.get("/{agent_id}", response_model=BaseResponse[dict])
async def get_agent(
    agent_id: str,
    request: Request,
) -> BaseResponse[dict]:
    """Get agent details by ID.

    Args:
        agent_id: ID of the agent.

    Returns:
        Agent information.

    Raises:
        404: If agent not found.
    """
    orchestrator = request.app.state.agent_orchestrator
    agent = orchestrator.get_agent(agent_id)
    return BaseResponse(data=agent.get_info().model_dump())


@router.post("/tasks", response_model=BaseResponse[dict])
async def create_task(
    task_request: TaskRequest,
    request: Request,
) -> BaseResponse[dict]:
    """Submit a new task for execution.

    Args:
        task_request: Task request details.

    Returns:
        Created task information.
    """
    orchestrator = request.app.state.agent_orchestrator
    task = await orchestrator.submit_task(task_request)
    return BaseResponse(data=task.model_dump())


@router.get("/tasks/{task_id}", response_model=BaseResponse[dict])
async def get_task(
    task_id: str,
    request: Request,
) -> BaseResponse[dict]:
    """Get task status and details.

    Args:
        task_id: ID of the task.

    Returns:
        Task information.

    Raises:
        404: If task not found.
    """
    orchestrator = request.app.state.agent_orchestrator
    task = orchestrator.get_task(task_id)
    return BaseResponse(data=task.model_dump())


@router.post("/tasks/{task_id}/cancel", response_model=BaseResponse[dict])
async def cancel_task(
    task_id: str,
    request: Request,
) -> BaseResponse[dict]:
    """Cancel a running task.

    Args:
        task_id: ID of the task to cancel.

    Returns:
        Updated task information.

    Raises:
        404: If task not found.
        409: If task cannot be cancelled.
    """
    orchestrator = request.app.state.agent_orchestrator
    task = await orchestrator.cancel_task(task_id)
    return BaseResponse(data=task.model_dump())


@router.get("/tasks/list", response_model=BaseResponse[list[dict]])
async def list_tasks(
    request: Request,
    status: TaskStatus | None = None,
    agent_type: AgentType | None = None,
) -> BaseResponse[list[dict]]:
    """List tasks with optional filters.

    Args:
        status: Filter by task status.
        agent_type: Filter by agent type.

    Returns:
        List of matching tasks.
    """
    orchestrator = request.app.state.agent_orchestrator
    tasks = orchestrator.list_tasks(status=status, agent_type=agent_type)
    return BaseResponse(data=[task.model_dump() for task in tasks])


@router.get("/metrics/overview", response_model=BaseResponse[dict])
async def get_metrics(
    request: Request,
) -> BaseResponse[dict]:
    """Get orchestrator metrics.

    Returns:
        System metrics including agent and task counts.
    """
    orchestrator = request.app.state.agent_orchestrator
    return BaseResponse(data=orchestrator.get_metrics())
