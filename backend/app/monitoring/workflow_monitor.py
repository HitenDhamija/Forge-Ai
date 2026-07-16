"""Workflow monitoring and performance tracking."""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status for monitoring."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class WorkflowSnapshot:
    """Snapshot of workflow status at a point in time."""

    workflow_id: str
    title: str
    status: str
    progress: float
    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    started_at: datetime | None
    elapsed_time: float
    estimated_remaining: float | None
    risk_level: str


@dataclass
class _WorkflowRecord:
    """Internal workflow tracking record."""

    workflow_id: str
    title: str
    status: WorkflowStatus = WorkflowStatus.CREATED
    risk_level: str = "medium"
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration: float = 0.0
    events: list[dict] = field(default_factory=list)
    task_durations: list[float] = field(default_factory=list)


class WorkflowMonitor:
    """Monitors workflow execution, lifecycle events, and performance.

    Tracks workflow state transitions, task progress, and execution metrics
    using in-memory storage with timestamps.
    """

    def __init__(self) -> None:
        """Initialize the workflow monitor."""
        self._workflows: dict[str, _WorkflowRecord] = {}
        self._global_events: list[dict] = []

    async def record_workflow_start(
        self, workflow_id: str, title: str
    ) -> None:
        """Record the start of a workflow.

        Args:
            workflow_id: Workflow identifier.
            title: Workflow title.
        """
        record = _WorkflowRecord(
            workflow_id=workflow_id,
            title=title,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self._workflows[workflow_id] = record

        self._record_event(workflow_id, None, "workflow_started", {"title": title})
        logger.info("Workflow started: %s (%s)", title, workflow_id)

    async def record_workflow_complete(
        self, workflow_id: str, success: bool, duration: float
    ) -> None:
        """Record workflow completion.

        Args:
            workflow_id: Workflow identifier.
            success: Whether the workflow completed successfully.
            duration: Total workflow duration in seconds.
        """
        record = self._workflows.get(workflow_id)
        if not record:
            logger.warning("Workflow not found for completion: %s", workflow_id)
            return

        now = datetime.now(timezone.utc)
        record.completed_at = now
        record.duration = duration
        record.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED

        event_type = "workflow_completed" if success else "workflow_failed"
        self._record_event(
            workflow_id,
            None,
            event_type,
            {"duration": duration, "success": success},
        )
        logger.info(
            "Workflow %s: %s (%.1fs)",
            event_type,
            workflow_id,
            duration,
        )

    async def record_task_event(
        self,
        workflow_id: str,
        task_id: str,
        event_type: str,
        data: dict | None = None,
    ) -> None:
        """Record a task event within a workflow.

        Args:
            workflow_id: Workflow identifier.
            task_id: Task identifier.
            event_type: Type of task event (e.g., 'task_started', 'task_completed').
            data: Optional event data.
        """
        record = self._workflows.get(workflow_id)
        if not record:
            logger.warning("Workflow not found for task event: %s", workflow_id)
            return

        event_data = data or {}

        if event_type == "task_started":
            record.tasks_total += 1
        elif event_type == "task_completed":
            record.tasks_completed += 1
            if "duration" in event_data:
                record.task_durations.append(event_data["duration"])
        elif event_type == "task_failed":
            record.tasks_failed += 1

        self._record_event(workflow_id, task_id, event_type, event_data)
        logger.debug(
            "Task event %s for workflow %s, task %s",
            event_type,
            workflow_id,
            task_id,
        )

    async def snapshot(self) -> list[WorkflowSnapshot]:
        """Get current state of all tracked workflows.

        Returns:
            List of workflow status snapshots.
        """
        snapshots = []
        now = datetime.now(timezone.utc)

        for wf_id, record in self._workflows.items():
            elapsed = 0.0
            if record.started_at:
                end_time = record.completed_at or now
                elapsed = (end_time - record.started_at).total_seconds()

            progress = 0.0
            if record.tasks_total > 0:
                progress = record.tasks_completed / record.tasks_total

            estimated_remaining = None
            if record.tasks_total > 0 and record.task_durations:
                avg_duration = sum(record.task_durations) / len(record.task_durations)
                remaining_tasks = record.tasks_total - record.tasks_completed
                estimated_remaining = avg_duration * remaining_tasks

            snapshot = WorkflowSnapshot(
                workflow_id=wf_id,
                title=record.title,
                status=record.status.value,
                progress=round(progress, 4),
                tasks_total=record.tasks_total,
                tasks_completed=record.tasks_completed,
                tasks_failed=record.tasks_failed,
                started_at=record.started_at,
                elapsed_time=round(elapsed, 2),
                estimated_remaining=(
                    round(estimated_remaining, 2) if estimated_remaining else None
                ),
                risk_level=record.risk_level,
            )
            snapshots.append(snapshot)

        return snapshots

    async def get_workflow_history(self, workflow_id: str) -> list[dict]:
        """Get event history for a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            List of workflow events.
        """
        record = self._workflows.get(workflow_id)
        if not record:
            logger.warning("Workflow not found for history: %s", workflow_id)
            return []

        return list(record.events)

    async def get_workflow_performance(self) -> dict:
        """Get aggregate performance statistics across all workflows.

        Returns:
            Dictionary of performance metrics.
        """
        total = len(self._workflows)
        completed = 0
        failed = 0
        total_duration = 0.0
        durations: list[float] = []

        for record in self._workflows.values():
            if record.status == WorkflowStatus.COMPLETED:
                completed += 1
            elif record.status == WorkflowStatus.FAILED:
                failed += 1

            if record.duration > 0:
                total_duration += record.duration
                durations.append(record.duration)

        avg_duration = sum(durations) / len(durations) if durations else 0.0
        success_rate = completed / total if total > 0 else 0.0

        return {
            "total_workflows": total,
            "completed": completed,
            "failed": failed,
            "success_rate": round(success_rate, 4),
            "avg_duration": round(avg_duration, 2),
            "total_duration": round(total_duration, 2),
        }

    async def get_overview(self) -> dict:
        """Get overview statistics for all workflows.

        Returns:
            Dictionary with aggregate workflow statistics.
        """
        status_counts: dict[str, int] = {}
        risk_counts: dict[str, int] = {}
        total_tasks = 0
        total_completed = 0
        total_failed = 0

        for record in self._workflows.values():
            status_counts[record.status.value] = (
                status_counts.get(record.status.value, 0) + 1
            )
            risk_counts[record.risk_level] = (
                risk_counts.get(record.risk_level, 0) + 1
            )
            total_tasks += record.tasks_total
            total_completed += record.tasks_completed
            total_failed += record.tasks_failed

        performance = await self.get_workflow_performance()

        return {
            "total_workflows": len(self._workflows),
            "status_breakdown": status_counts,
            "risk_breakdown": risk_counts,
            "total_tasks": total_tasks,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "performance": performance,
        }

    def _record_event(
        self,
        workflow_id: str,
        task_id: str | None,
        event_type: str,
        data: dict,
    ) -> None:
        """Record a workflow event.

        Args:
            workflow_id: Workflow identifier.
            task_id: Optional task identifier.
            event_type: Type of event.
            data: Event data.
        """
        event = {
            "workflow_id": workflow_id,
            "task_id": task_id,
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc),
        }
        self._global_events.append(event)

        record = self._workflows.get(workflow_id)
        if record:
            record.events.append(event)
