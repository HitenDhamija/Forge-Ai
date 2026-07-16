"""Agent monitoring and health tracking."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentHealthStatus(str, Enum):
    """Agent health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class AgentStatusSnapshot:
    """Snapshot of agent status at a point in time."""

    agent_id: str
    name: str
    agent_type: str
    status: str
    current_task_id: str | None
    tasks_completed: int
    tasks_failed: int
    avg_execution_time: float
    last_active: datetime
    uptime: float
    memory_usage: float
    cpu_usage: float


@dataclass
class _AgentRecord:
    """Internal agent tracking record."""

    agent_id: str
    name: str
    agent_type: str
    status: str = "idle"
    current_task_id: str | None = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    last_active: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    task_history: list[dict] = field(default_factory=list)
    status_history: list[dict] = field(default_factory=list)


class AgentMonitor:
    """Monitors agent health, status, and performance.

    Tracks agent lifecycle events, task assignments, and execution metrics
    using in-memory storage with timestamps.
    """

    def __init__(self) -> None:
        """Initialize the agent monitor."""
        self._agents: dict[str, _AgentRecord] = {}
        self._events: list[dict] = []

    async def register_agent(
        self,
        agent_id: str,
        name: str,
        agent_type: str,
    ) -> None:
        """Register an agent for monitoring.

        Args:
            agent_id: Unique agent identifier.
            name: Human-readable agent name.
            agent_type: Type of agent (e.g., 'coder', 'reviewer', 'planner').
        """
        record = _AgentRecord(
            agent_id=agent_id,
            name=name,
            agent_type=agent_type,
        )
        self._agents[agent_id] = record
        self._record_event(agent_id, "registered", {"name": name, "agent_type": agent_type})
        logger.info("Agent registered: %s (%s)", name, agent_type)

    async def snapshot(self, orchestrator: Any = None) -> list[AgentStatusSnapshot]:
        """Get current state of all registered agents.

        Args:
            orchestrator: Optional orchestrator instance for live data.

        Returns:
            List of agent status snapshots.
        """
        snapshots = []
        now = datetime.now(timezone.utc)

        for agent_id, record in self._agents.items():
            uptime = (now - record.started_at).total_seconds()
            avg_time = (
                record.total_execution_time / record.tasks_completed
                if record.tasks_completed > 0
                else 0.0
            )

            snapshot = AgentStatusSnapshot(
                agent_id=agent_id,
                name=record.name,
                agent_type=record.agent_type,
                status=record.status,
                current_task_id=record.current_task_id,
                tasks_completed=record.tasks_completed,
                tasks_failed=record.tasks_failed,
                avg_execution_time=avg_time,
                last_active=record.last_active,
                uptime=uptime,
                memory_usage=record.memory_usage,
                cpu_usage=record.cpu_usage,
            )
            snapshots.append(snapshot)

        return snapshots

    async def get_agent_history(
        self, agent_id: str, hours: int = 24
    ) -> list[dict]:
        """Get agent status history within a time window.

        Args:
            agent_id: Agent identifier.
            hours: Number of hours of history to retrieve.

        Returns:
            List of status history entries.
        """
        record = self._agents.get(agent_id)
        if not record:
            logger.warning("Agent not found: %s", agent_id)
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            entry
            for entry in record.status_history
            if entry["timestamp"] >= cutoff
        ]

    async def record_task_start(self, agent_id: str, task_id: str) -> None:
        """Record that an agent has started a task.

        Args:
            agent_id: Agent identifier.
            task_id: Task identifier.
        """
        record = self._agents.get(agent_id)
        if not record:
            logger.warning("Agent not found for task start: %s", agent_id)
            return

        record.current_task_id = task_id
        record.status = "working"
        record.last_active = datetime.now(timezone.utc)

        self._record_event(agent_id, "task_started", {"task_id": task_id})
        logger.info("Agent %s started task %s", agent_id, task_id)

    async def record_task_complete(
        self, agent_id: str, task_id: str, duration: float, success: bool
    ) -> None:
        """Record task completion for an agent.

        Args:
            agent_id: Agent identifier.
            task_id: Task identifier.
            duration: Task execution duration in seconds.
            success: Whether the task completed successfully.
        """
        record = self._agents.get(agent_id)
        if not record:
            logger.warning("Agent not found for task complete: %s", agent_id)
            return

        record.current_task_id = None
        record.status = "idle"
        record.last_active = datetime.now(timezone.utc)
        record.total_execution_time += duration

        if success:
            record.tasks_completed += 1
        else:
            record.tasks_failed += 1

        event_data = {
            "task_id": task_id,
            "duration": duration,
            "success": success,
        }
        self._record_event(agent_id, "task_completed", event_data)
        record.task_history.append(
            {
                "task_id": task_id,
                "duration": duration,
                "success": success,
                "timestamp": datetime.now(timezone.utc),
            }
        )

        status_label = "completed" if success else "failed"
        logger.info(
            "Agent %s %s task %s (%.1fs)",
            agent_id,
            status_label,
            task_id,
            duration,
        )

    async def get_agent_performance(self, agent_id: str) -> dict:
        """Get performance metrics for an agent.

        Args:
            agent_id: Agent identifier.

        Returns:
            Dictionary of performance metrics.
        """
        record = self._agents.get(agent_id)
        if not record:
            logger.warning("Agent not found for performance: %s", agent_id)
            return {}

        now = datetime.now(timezone.utc)
        uptime = (now - record.started_at).total_seconds()
        total_tasks = record.tasks_completed + record.tasks_failed
        avg_time = (
            record.total_execution_time / record.tasks_completed
            if record.tasks_completed > 0
            else 0.0
        )
        success_rate = (
            record.tasks_completed / total_tasks if total_tasks > 0 else 0.0
        )

        return {
            "agent_id": agent_id,
            "name": record.name,
            "agent_type": record.agent_type,
            "tasks_completed": record.tasks_completed,
            "tasks_failed": record.tasks_failed,
            "total_tasks": total_tasks,
            "success_rate": round(success_rate, 4),
            "avg_execution_time": round(avg_time, 2),
            "total_execution_time": round(record.total_execution_time, 2),
            "uptime": round(uptime, 2),
            "last_active": record.last_active.isoformat(),
        }

    async def get_agent_health(self, agent_id: str) -> AgentHealthStatus:
        """Get health status for an agent.

        Health is determined by recent activity, failure rate, and uptime.

        Args:
            agent_id: Agent identifier.

        Returns:
            Current health status.
        """
        record = self._agents.get(agent_id)
        if not record:
            return AgentHealthStatus.OFFLINE

        now = datetime.now(timezone.utc)
        inactive_minutes = (now - record.last_active).total_seconds() / 60

        if inactive_minutes > 30:
            return AgentHealthStatus.OFFLINE

        total_tasks = record.tasks_completed + record.tasks_failed
        if total_tasks == 0:
            return AgentHealthStatus.HEALTHY

        failure_rate = record.tasks_failed / total_tasks
        if failure_rate > 0.5:
            return AgentHealthStatus.UNHEALTHY
        if failure_rate > 0.2 or inactive_minutes > 10:
            return AgentHealthStatus.DEGRADED

        return AgentHealthStatus.HEALTHY

    async def get_overview(self) -> dict:
        """Get overview statistics across all monitored agents.

        Returns:
            Dictionary with aggregate agent statistics.
        """
        total = len(self._agents)
        status_counts: dict[str, int] = {}
        health_counts: dict[str, int] = {}
        total_completed = 0
        total_failed = 0

        for agent_id, record in self._agents.items():
            status_counts[record.status] = status_counts.get(record.status, 0) + 1

            health = await self.get_agent_health(agent_id)
            health_counts[health.value] = health_counts.get(health.value, 0) + 1

            total_completed += record.tasks_completed
            total_failed += record.tasks_failed

        total_tasks = total_completed + total_failed

        return {
            "total_agents": total,
            "status_breakdown": status_counts,
            "health_breakdown": health_counts,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "overall_success_rate": (
                round(total_completed / total_tasks, 4) if total_tasks > 0 else 0.0
            ),
        }

    def _record_event(self, agent_id: str, event_type: str, data: dict) -> None:
        """Record an agent event.

        Args:
            agent_id: Agent identifier.
            event_type: Type of event.
            data: Event data.
        """
        event = {
            "agent_id": agent_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc),
        }
        self._events.append(event)

        record = self._agents.get(agent_id)
        if record:
            record.status_history.append(event)
