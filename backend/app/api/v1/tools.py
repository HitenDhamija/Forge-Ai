"""Tool Management API Endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel
from typing import Any

from app.core.dependencies import get_current_user
from app.tools.runtime import ToolRuntime
from app.tools.registry import ToolRegistry
from app.tools.permissions import PermissionEngine
from app.tools.schemas import ToolStatus, ToolType

router = APIRouter()


class ToolExecuteRequest(BaseModel):
    tool_id: str
    operation: str
    parameters: dict[str, Any]


class ToolExecuteResponse(BaseModel):
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    tool_id: str
    execution_id: str
    duration_ms: float


class ToolListResponse(BaseModel):
    tools: list[dict[str, Any]]


class ToolHealthResponse(BaseModel):
    tool_id: str
    status: str
    latency_ms: float | None = None
    version: str | None = None
    error: str | None = None


def get_tool_runtime(request: Request) -> ToolRuntime:
    return request.app.state.tool_runtime


def get_tool_registry(request: Request) -> ToolRegistry:
    return request.app.state.tool_registry


def get_permission_engine(request: Request) -> PermissionEngine:
    return request.app.state.permission_engine


@router.get("/tools", response_model=ToolListResponse)
async def list_tools(
    request: Request,
    current_user: dict = Depends(get_current_user),
    tool_type: ToolType | None = Query(None, description="Filter by tool type"),
    status: ToolStatus | None = Query(None, description="Filter by status"),
):
    """List available tools."""
    registry = get_tool_registry(request)

    tools = registry.list_tools(tool_type=tool_type, status=status)

    return ToolListResponse(
        tools=[
            {
                "tool_id": tool.tool_id,
                "name": tool.name,
                "description": tool.description,
                "type": tool.tool_type.value,
                "provider": tool.provider.value,
                "status": tool.status.value,
                "version": tool.version,
                "supported_operations": tool.supported_operations,
            }
            for tool in tools
        ]
    )


@router.get("/tools/{tool_id}", response_model=ToolHealthResponse)
async def get_tool(
    request: Request,
    tool_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get tool details."""
    registry = get_tool_registry(request)

    tool = registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    health = await tool.health_check()

    return ToolHealthResponse(
        tool_id=tool.tool_id,
        status=health.status.value,
        latency_ms=health.latency_ms,
        version=health.version,
        error=health.error_message,
    )


@router.get("/tools/{tool_id}/health", response_model=ToolHealthResponse)
async def check_tool_health(
    request: Request,
    tool_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Check tool health."""
    registry = get_tool_registry(request)

    tool = registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    health = await tool.health_check()

    return ToolHealthResponse(
        tool_id=tool.tool_id,
        status=health.status.value,
        latency_ms=health.latency_ms,
        version=health.version,
        error=health.error_message,
    )


@router.post("/tools/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: Request,
    execute_request: ToolExecuteRequest,
    current_user: dict = Depends(get_current_user),
):
    """Execute a tool operation."""
    tool_runtime = get_tool_runtime(request)

    result = await tool_runtime.execute(
        agent_id=current_user.get("id", "unknown"),
        tool_id=execute_request.tool_id,
        operation=execute_request.operation,
        parameters=execute_request.parameters,
    )

    return ToolExecuteResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        tool_id=result.tool_id,
        execution_id=result.execution_id,
        duration_ms=result.duration_ms,
    )


@router.post("/tools/{tool_id}/cancel")
async def cancel_tool_execution(
    request: Request,
    tool_id: str,
    execution_id: str = Query(..., description="Execution ID to cancel"),
    current_user: dict = Depends(get_current_user),
):
    """Cancel a running tool execution."""
    tool_runtime = get_tool_runtime(request)

    cancelled = await tool_runtime.cancel(execution_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="Execution not found or already completed")

    return {"message": "Execution cancelled", "execution_id": execution_id}


@router.get("/tools/executions")
async def list_executions(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """List all tool executions."""
    tool_runtime = get_tool_runtime(request)

    executions = tool_runtime.list_executions()

    return {
        "executions": [
            {
                "execution_id": e.execution_id,
                "tool_id": e.tool_id,
                "success": e.success,
                "duration_ms": e.duration_ms,
                "error": e.error,
            }
            for e in executions
        ]
    }


@router.get("/tools/health")
async def check_all_tools_health(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Check health of all tools."""
    registry = get_tool_registry(request)

    tools = registry.list_tools()
    health_results = []

    for tool in tools:
        health = await tool.health_check()
        health_results.append({
            "tool_id": tool.tool_id,
            "status": health.status.value,
            "latency_ms": health.latency_ms,
            "error": health.error_message,
        })

    return {"health": health_results}
