"""Enterprise AI Workforce API endpoints."""

from fastapi import APIRouter, Request

from app.agents.enterprise.schemas import AgentRole, AgentStatus
from app.schemas.common import BaseResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=BaseResponse[list[dict]])
async def list_agents(
    request: Request,
) -> BaseResponse[list[dict]]:
    """List all registered agents.

    Returns:
        List of agent information.
    """
    runtime = request.app.state.agent_runtime
    agents = runtime.list_agents()
    return BaseResponse(data=[a.model_dump() for a in agents])


@router.get("/status", response_model=BaseResponse[dict])
async def get_agents_status(
    request: Request,
) -> BaseResponse[dict]:
    """Get summary of all agent statuses.

    Returns:
        Status summary.
    """
    runtime = request.app.state.agent_runtime
    summary = runtime.get_status_summary()
    return BaseResponse(data=summary)


@router.get("/{agent_id}", response_model=BaseResponse[dict])
async def get_agent(
    agent_id: str,
    request: Request,
) -> BaseResponse[dict]:
    """Get agent details by ID.

    Args:
        agent_id: Agent ID.

    Returns:
        Agent information.

    Raises:
        404: If agent not found.
    """
    runtime = request.app.state.agent_runtime
    agent = runtime.get_agent(agent_id)
    if not agent:
        return BaseResponse(data={"error": "Agent not found"})
    return BaseResponse(data=agent.model_dump())


@router.get("/role/{role}", response_model=BaseResponse[list[dict]])
async def get_agents_by_role(
    role: AgentRole,
    request: Request,
) -> BaseResponse[list[dict]]:
    """Get agents by role.

    Args:
        role: Agent role.

    Returns:
        List of agents with the role.
    """
    runtime = request.app.state.agent_runtime
    agents = runtime.get_agents_by_role(role)
    return BaseResponse(data=[a.model_dump() for a in agents])


@router.post("/register", response_model=BaseResponse[dict])
async def register_agent(
    agent_data: dict,
    request: Request,
) -> BaseResponse[dict]:
    """Register a new agent.

    Args:
        agent_data: Agent registration data.

    Returns:
        Registration result.
    """
    from app.agents.enterprise.schemas import AgentInfo
    runtime = request.app.state.agent_runtime
    agent_info = AgentInfo(**agent_data)
    runtime.register_agent(agent_info)
    return BaseResponse(data={"status": "registered", "agent_id": agent_info.id})


@router.post("/{agent_id}/heartbeat", response_model=BaseResponse[dict])
async def agent_heartbeat(
    agent_id: str,
    request: Request,
) -> BaseResponse[dict]:
    """Update agent heartbeat.

    Args:
        agent_id: Agent ID.

    Returns:
        Heartbeat result.
    """
    runtime = request.app.state.agent_runtime
    runtime.agent_heartbeat(agent_id)
    return BaseResponse(data={"status": "ok"})


@router.post("/{agent_id}/status", response_model=BaseResponse[dict])
async def update_agent_status(
    agent_id: str,
    status: AgentStatus,
    request: Request,
) -> BaseResponse[dict]:
    """Update agent status.

    Args:
        agent_id: Agent ID.
        status: New status.

    Returns:
        Update result.
    """
    runtime = request.app.state.agent_runtime
    runtime.update_agent_status(agent_id, status)
    return BaseResponse(data={"status": "updated"})


@router.get("/events/recent", response_model=BaseResponse[list[dict]])
async def get_recent_events(
    request: Request,
    limit: int = 50,
) -> BaseResponse[list[dict]]:
    """Get recent events.

    Args:
        limit: Maximum events to return.

    Returns:
        List of recent events.
    """
    runtime = request.app.state.agent_runtime
    events = runtime.get_events(limit=limit)
    return BaseResponse(data=events)


@router.post("/workflow/{workflow_id}/process", response_model=BaseResponse[dict])
async def process_workflow(
    workflow_id: str,
    workflow_data: dict,
    request: Request,
) -> BaseResponse[dict]:
    """Process a workflow through the Supervisor.

    Args:
        workflow_id: Workflow ID.
        workflow_data: Workflow data.

    Returns:
        Processing result.
    """
    runtime = request.app.state.agent_runtime
    result = await runtime.process_workflow(workflow_id, workflow_data)
    return BaseResponse(data=result)
