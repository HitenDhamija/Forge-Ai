"""Monitoring API endpoints for enterprise observability.

Provides endpoints for system overview, workflow monitoring,
agent status, tool health, memory metrics, and analytics.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.monitoring.metrics_collector import MetricsCollector
from app.monitoring.agent_monitor import AgentMonitor
from app.monitoring.workflow_monitor import WorkflowMonitor
from app.monitoring.tool_monitor import ToolMonitor
from app.monitoring.memory_monitor import MemoryMonitor
from app.monitoring.prompt_monitor import PromptMonitor
from app.monitoring.execution_monitor import ExecutionMonitor
from app.monitoring.analytics_engine import AnalyticsEngine
from app.monitoring.health_service import HealthService
from app.monitoring.timeline_service import TimelineService
from app.monitoring.event_stream import EventStream
from app.schemas.common import BaseResponse, ResponseStatus

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

# Singleton instances
_metrics_collector: MetricsCollector | None = None
_agent_monitor: AgentMonitor | None = None
_workflow_monitor: WorkflowMonitor | None = None
_tool_monitor: ToolMonitor | None = None
_memory_monitor: MemoryMonitor | None = None
_prompt_monitor: PromptMonitor | None = None
_execution_monitor: ExecutionMonitor | None = None
_analytics_engine: AnalyticsEngine | None = None
_health_service: HealthService | None = None
_timeline_service: TimelineService | None = None
_event_stream: EventStream | None = None


def _get_monitors() -> dict[str, Any]:
    global _metrics_collector, _agent_monitor, _workflow_monitor
    global _tool_monitor, _memory_monitor, _prompt_monitor
    global _execution_monitor, _analytics_engine, _health_service
    global _timeline_service, _event_stream

    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    if _agent_monitor is None:
        _agent_monitor = AgentMonitor()
    if _workflow_monitor is None:
        _workflow_monitor = WorkflowMonitor()
    if _tool_monitor is None:
        _tool_monitor = ToolMonitor()
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    if _prompt_monitor is None:
        _prompt_monitor = PromptMonitor()
    if _execution_monitor is None:
        _execution_monitor = ExecutionMonitor()
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    if _health_service is None:
        _health_service = HealthService()
    if _timeline_service is None:
        _timeline_service = TimelineService()
    if _event_stream is None:
        _event_stream = EventStream()

    return {
        "metrics": _metrics_collector,
        "agent": _agent_monitor,
        "workflow": _workflow_monitor,
        "tool": _tool_monitor,
        "memory": _memory_monitor,
        "prompt": _prompt_monitor,
        "execution": _execution_monitor,
        "analytics": _analytics_engine,
        "health": _health_service,
        "timeline": _timeline_service,
        "event_stream": _event_stream,
    }


# ── Request / Response Models ──────────────────────────────────────────


class OverviewResponse(BaseModel):
    """System overview response."""

    agents: dict[str, Any]
    workflows: dict[str, Any]
    tools: dict[str, Any]
    memory: dict[str, Any]
    execution: dict[str, Any]
    learning: dict[str, Any]
    health: dict[str, Any]


class TimelineQuery(BaseModel):
    """Query parameters for timeline."""

    hours: int = Field(default=24, ge=1, le=168)
    event_type: str | None = None
    source: str | None = None
    limit: int = Field(default=100, ge=1, le=500)


class AnalyticsQuery(BaseModel):
    """Query parameters for analytics."""

    time_range: str = Field(default="day", description="hour, day, week, month")
    limit: int = Field(default=20, ge=1, le=100)


# ── Endpoints ──────────────────────────────────────────────────────────


@router.get("/overview", response_model=BaseResponse[OverviewResponse])
async def get_overview():
    """Get comprehensive system overview.

    Returns metrics and status from all monitoring modules.
    """
    monitors = _get_monitors()

    try:
        agents = await monitors["agent"].get_overview()
        workflows = await monitors["workflow"].get_overview()
        tools = await monitors["tool"].get_overview()
        memory = await monitors["memory"].get_overview()
        execution = await monitors["execution"].get_overview()
        try:
            health = await asyncio.wait_for(monitors["health"].get_health_summary(None), timeout=3.0)
        except (asyncio.TimeoutError, Exception):
            health = {
                "overall_status": "unknown",
                "components": [],
                "summary": {"total": 0, "healthy": 0, "degraded": 0, "unhealthy": 0, "unknown": 0},
            }

        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="System overview",
            data=OverviewResponse(
                agents=agents,
                workflows=workflows,
                tools=tools,
                memory=memory,
                execution=execution,
                learning={},
                health=health,
            ),
        )
    except Exception as e:
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Overview (partial)",
            data={
                "agents": {},
                "workflows": {},
                "tools": {},
                "memory": {},
                "execution": {},
                "health": {"overall_status": "unknown", "components": [], "summary": {"total": 0, "healthy": 0, "degraded": 0, "unhealthy": 0, "unknown": 0}},
            },
        )


@router.get("/workflows", response_model=BaseResponse[list[dict[str, Any]]])
async def get_workflows():
    """Get workflow monitoring snapshots."""
    monitors = _get_monitors()
    try:
        snapshots = await monitors["workflow"].snapshot()
        data = [
            {
                "workflow_id": s.workflow_id,
                "title": s.title,
                "status": s.status.value if hasattr(s.status, "value") else s.status,
                "progress": s.progress,
                "tasks_total": s.tasks_total,
                "tasks_completed": s.tasks_completed,
                "tasks_failed": s.tasks_failed,
                "elapsed_time": s.elapsed_time,
                "risk_level": s.risk_level,
            }
            for s in snapshots
        ]
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(data)} workflows",
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=BaseResponse[list[dict[str, Any]]])
async def get_agents():
    """Get agent monitoring snapshots."""
    monitors = _get_monitors()
    try:
        snapshots = await monitors["agent"].snapshot(None)
        data = [
            {
                "agent_id": s.agent_id,
                "name": s.name,
                "agent_type": s.agent_type,
                "status": s.status,
                "current_task_id": s.current_task_id,
                "tasks_completed": s.tasks_completed,
                "tasks_failed": s.tasks_failed,
                "avg_execution_time": s.avg_execution_time,
                "last_active": s.last_active.isoformat() if s.last_active else None,
            }
            for s in snapshots
        ]
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(data)} agents",
            data=data,
        )
    except Exception:
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="No agent data yet",
            data=[],
        )


@router.get("/tools", response_model=BaseResponse[list[dict[str, Any]]])
async def get_tools():
    """Get tool monitoring snapshots."""
    monitors = _get_monitors()
    try:
        snapshots = await monitors["tool"].snapshot(None)
        data = [
            {
                "tool_id": s.tool_id,
                "name": s.name,
                "provider": s.provider,
                "status": s.status,
                "total_calls": s.total_calls,
                "success_count": s.success_count,
                "error_count": s.error_count,
                "avg_latency": s.avg_latency,
                "health_status": s.health_status.value if hasattr(s.health_status, "value") else s.health_status,
            }
            for s in snapshots
        ]
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(data)} tools",
            data=data,
        )
    except Exception:
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="No tools tracked yet",
            data=[],
        )


@router.get("/memory", response_model=BaseResponse[dict[str, Any]])
async def get_memory():
    """Get memory monitoring status."""
    monitors = _get_monitors()
    try:
        snapshot = await monitors["memory"].snapshot(None)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Memory status",
            data={
                "total_chunks": snapshot.total_chunks,
                "total_repositories": snapshot.total_repositories,
                "collections": snapshot.collections,
                "embedding_model": snapshot.embedding_model,
                "avg_search_time": snapshot.avg_search_time,
                "total_searches": snapshot.total_searches,
                "cache_hit_rate": snapshot.cache_hit_rate,
            },
        )
    except Exception:
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="No memory data yet",
            data={
                "total_chunks": 0,
                "total_repositories": 0,
                "collections": 0,
                "embedding_model": "none",
                "avg_search_time": 0,
                "total_searches": 0,
                "cache_hit_rate": 0,
            },
        )


@router.get("/prompts", response_model=BaseResponse[dict[str, Any]])
async def get_prompts():
    """Get prompt monitoring status."""
    monitors = _get_monitors()
    try:
        snapshot = await monitors["prompt"].get_snapshot()
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Prompt status",
            data={
                "total_prompts": snapshot.total_prompts,
                "avg_latency": snapshot.avg_latency,
                "avg_tokens": snapshot.avg_tokens,
                "avg_confidence": snapshot.avg_confidence,
                "success_rate": snapshot.success_rate,
                "models_used": snapshot.models_used,
                "top_templates": snapshot.top_templates,
            },
        )
    except Exception:
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="No prompt data yet",
            data={
                "total_prompts": 0,
                "avg_latency": 0,
                "avg_tokens": 0,
                "avg_confidence": 0,
                "success_rate": 0,
                "models_used": [],
                "top_templates": [],
            },
        )


@router.get("/analytics", response_model=BaseResponse[dict[str, Any]])
async def get_analytics(time_range: str = "day"):
    """Get analytics and trends."""
    monitors = _get_monitors()
    try:
        daily = await monitors["analytics"].get_daily_activity(7)
        execution_trend = await monitors["analytics"].get_execution_time_trend(time_range)
        success_trend = await monitors["analytics"].get_success_rate_trend(time_range)
        most_active = await monitors["analytics"].get_most_active_agent()
        most_used = await monitors["analytics"].get_most_used_tool()

        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Analytics",
            data={
                "daily_activity": [
                    {
                        "period": d.period,
                        "workflows_started": d.workflows_started,
                        "workflows_completed": d.workflows_completed,
                        "tasks_completed": d.tasks_completed,
                        "tools_used": d.tools_used,
                    }
                    for d in daily
                ],
                "execution_trend": {
                    "metric": execution_trend.metric_name,
                    "current": execution_trend.current_value,
                    "previous": execution_trend.previous_value,
                    "change_percent": execution_trend.change_percent,
                    "direction": execution_trend.direction,
                },
                "success_trend": {
                    "metric": success_trend.metric_name,
                    "current": success_trend.current_value,
                    "previous": success_trend.previous_value,
                    "change_percent": success_trend.change_percent,
                    "direction": success_trend.direction,
                },
                "most_active_agent": most_active,
                "most_used_tool": most_used,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=BaseResponse[dict[str, Any]])
async def get_health():
    """Get system health status."""
    monitors = _get_monitors()
    try:
        health = await monitors["health"].get_health_summary(None)
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="Health status",
            data=health,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline", response_model=BaseResponse[list[dict[str, Any]]])
async def get_timeline(
    hours: int = 24,
    event_type: str | None = None,
    source: str | None = None,
    limit: int = 100,
):
    """Get chronological event timeline."""
    monitors = _get_monitors()
    try:
        events = await monitors["timeline"].get_timeline(
            hours=hours, event_type=event_type, source=source, limit=limit
        )
        data = [
            {
                "id": e.id,
                "event_type": e.event_type.value if hasattr(e.event_type, "value") else e.event_type,
                "source": e.source,
                "title": e.title,
                "description": e.description,
                "severity": e.severity.value if hasattr(e.severity, "value") else e.severity,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ]
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(data)} events",
            data=data,
        )
    except Exception:
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message="No timeline data",
            data=[],
        )


@router.get("/executions", response_model=BaseResponse[list[dict[str, Any]]])
async def get_executions():
    """Get execution monitoring snapshots."""
    monitors = _get_monitors()
    try:
        snapshots = await monitors["execution"].snapshot(None)
        data = [
            {
                "execution_id": s.execution_id,
                "workflow_id": s.workflow_id,
                "status": s.status.value if hasattr(s.status, "value") else s.status,
                "progress": s.progress,
                "steps_total": s.steps_total,
                "steps_completed": s.steps_completed,
                "steps_failed": s.steps_failed,
                "elapsed_time": s.elapsed_time,
                "current_step": s.current_step,
                "current_agent": s.current_agent,
            }
            for s in snapshots
        ]
        return BaseResponse(
            status=ResponseStatus.SUCCESS,
            message=f"Found {len(data)} executions",
            data=data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
