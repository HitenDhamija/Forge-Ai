"""Execution Monitor for tracking runtime, step progress, and completion rates."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionStatus(str, Enum):
    """Status of an execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"


@dataclass
class ExecutionSnapshot:
    """Snapshot of an execution's current state."""

    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    progress: float
    steps_total: int
    steps_completed: int
    steps_failed: int
    started_at: datetime
    elapsed_time: float
    current_step: str | None
    current_agent: str | None


@dataclass
class ExecutionRecord:
    """Internal record of an execution lifecycle event."""

    execution_id: str
    workflow_id: str
    status: ExecutionStatus
    timestamp: datetime
    event_type: str
    step_number: int | None = None
    data: dict[str, Any] = field(default_factory=dict)


class ExecutionMonitor:
    """Monitors execution runtime, step progress, and completion rates.

    Stores execution records in-memory.
    """

    def __init__(self) -> None:
        """Initialize execution monitor."""
        self._records: dict[str, list[ExecutionRecord]] = {}
        self._active: dict[str, dict[str, Any]] = {}

    async def snapshot(
        self,
        execution_runtime: Any,
    ) -> list[ExecutionSnapshot]:
        """Get current execution snapshots from a runtime instance.

        Args:
            execution_runtime: ExecutionRuntime instance with _executions dict.

        Returns:
            List of ExecutionSnapshot for active executions.
        """
        snapshots: list[ExecutionSnapshot] = []

        executions = getattr(execution_runtime, "_executions", {})
        progress_tracker = getattr(execution_runtime, "progress_tracker", None)

        for exec_id, execution in executions.items():
            progress = None
            if progress_tracker:
                progress = progress_tracker.get_progress(exec_id)

            steps_total = len(getattr(execution, "steps", []))
            steps_completed = 0
            steps_failed = 0
            current_step = getattr(execution, "current_step", None)
            current_agent = None

            if progress:
                tasks = getattr(progress, "tasks", [])
                steps_completed = sum(
                    1 for t in tasks if getattr(t, "status", "") == "completed"
                )
                steps_failed = sum(
                    1 for t in tasks if getattr(t, "status", "") == "failed"
                )
                current_agent = getattr(progress, "current_agent", None)

            started_at = getattr(execution, "started_at", datetime.utcnow())
            elapsed = (datetime.utcnow() - started_at).total_seconds()

            progress_pct = (steps_completed / steps_total * 100) if steps_total > 0 else 0.0

            status_str = getattr(execution, "status", "pending")
            try:
                status = ExecutionStatus(status_str.value if hasattr(status_str, "value") else str(status_str))
            except ValueError:
                status = ExecutionStatus.PENDING

            snapshots.append(
                ExecutionSnapshot(
                    execution_id=exec_id,
                    workflow_id=getattr(execution, "workflow_id", "unknown"),
                    status=status,
                    progress=progress_pct,
                    steps_total=steps_total,
                    steps_completed=steps_completed,
                    steps_failed=steps_failed,
                    started_at=started_at,
                    elapsed_time=elapsed,
                    current_step=current_step,
                    current_agent=current_agent,
                )
            )

        return snapshots

    async def record_execution_start(
        self,
        execution_id: str,
        workflow_id: str,
    ) -> None:
        """Record execution start.

        Args:
            execution_id: Execution identifier.
            workflow_id: Workflow identifier.
        """
        self._active[execution_id] = {
            "workflow_id": workflow_id,
            "status": ExecutionStatus.RUNNING,
            "started_at": datetime.utcnow(),
            "steps_total": 0,
            "steps_completed": 0,
            "steps_failed": 0,
            "current_step": None,
        }

        record = ExecutionRecord(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING,
            timestamp=datetime.utcnow(),
            event_type="start",
        )

        if execution_id not in self._records:
            self._records[execution_id] = []
        self._records[execution_id].append(record)

        logger.info(
            "Execution started: id=%s, workflow=%s",
            execution_id[:8],
            workflow_id[:8],
        )

    async def record_execution_complete(
        self,
        execution_id: str,
        success: bool,
        duration: float,
    ) -> None:
        """Record execution completion.

        Args:
            execution_id: Execution identifier.
            success: Whether execution succeeded.
            duration: Total duration in seconds.
        """
        status = ExecutionStatus.COMPLETED if success else ExecutionStatus.FAILED

        active = self._active.get(execution_id)
        if active:
            active["status"] = status

        record = ExecutionRecord(
            execution_id=execution_id,
            workflow_id=active["workflow_id"] if active else "unknown",
            status=status,
            timestamp=datetime.utcnow(),
            event_type="complete",
            data={"duration_seconds": duration, "success": success},
        )

        if execution_id not in self._records:
            self._records[execution_id] = []
        self._records[execution_id].append(record)

        logger.info(
            "Execution completed: id=%s, success=%s, duration=%.1fs",
            execution_id[:8],
            success,
            duration,
        )

    async def record_step_event(
        self,
        execution_id: str,
        step_number: int,
        event_type: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Record a step-level event.

        Args:
            execution_id: Execution identifier.
            step_number: Step number.
            event_type: Type of event (started, completed, failed, skipped).
            data: Optional event data.
        """
        active = self._active.get(execution_id)

        if event_type == "completed" and active:
            active["steps_completed"] = active.get("steps_completed", 0) + 1
            active["current_step"] = f"step-{step_number}"
        elif event_type == "failed" and active:
            active["steps_failed"] = active.get("steps_failed", 0) + 1
        elif event_type == "started" and active:
            active["steps_total"] = max(
                active.get("steps_total", 0), step_number
            )
            active["current_step"] = f"step-{step_number}"

        record = ExecutionRecord(
            execution_id=execution_id,
            workflow_id=active["workflow_id"] if active else "unknown",
            status=active["status"] if active else ExecutionStatus.RUNNING,
            timestamp=datetime.utcnow(),
            event_type=f"step_{event_type}",
            step_number=step_number,
            data=data or {},
        )

        if execution_id not in self._records:
            self._records[execution_id] = []
        self._records[execution_id].append(record)

    async def get_execution_history(
        self,
        execution_id: str,
    ) -> list[dict[str, Any]]:
        """Get event history for an execution.

        Args:
            execution_id: Execution identifier.

        Returns:
            List of event dictionaries.
        """
        records = self._records.get(execution_id, [])

        return [
            {
                "execution_id": r.execution_id,
                "workflow_id": r.workflow_id,
                "status": r.status.value,
                "event_type": r.event_type,
                "step_number": r.step_number,
                "data": r.data,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in records
        ]

    async def get_execution_performance(self) -> dict[str, Any]:
        """Get aggregate execution performance statistics.

        Returns:
            Dictionary with performance metrics.
        """
        all_records = [
            r for records in self._records.values() for r in records
        ]

        if not all_records:
            return {
                "total_executions": 0,
                "completed": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_duration_seconds": 0.0,
                "total_steps_completed": 0,
                "total_steps_failed": 0,
            }

        completed_records = [
            r for r in all_records if r.event_type == "complete"
        ]

        completed_count = sum(
            1 for r in completed_records if r.status == ExecutionStatus.COMPLETED
        )
        failed_count = sum(
            1 for r in completed_records if r.status == ExecutionStatus.FAILED
        )
        total_executions = len(completed_records)

        durations = [
            r.data.get("duration_seconds", 0.0) for r in completed_records
        ]

        step_completed_records = [
            r for r in all_records if r.event_type == "step_completed"
        ]
        step_failed_records = [
            r for r in all_records if r.event_type == "step_failed"
        ]

        return {
            "total_executions": total_executions,
            "completed": completed_count,
            "failed": failed_count,
            "success_rate": (
                completed_count / total_executions if total_executions > 0 else 0.0
            ),
            "avg_duration_seconds": (
                sum(durations) / len(durations) if durations else 0.0
            ),
            "total_steps_completed": len(step_completed_records),
            "total_steps_failed": len(step_failed_records),
        }

    async def get_overview(self) -> dict[str, Any]:
        """Get execution monitoring overview.

        Returns:
            Dictionary with overview metrics and active executions.
        """
        perf = await self.get_execution_performance()

        active_executions = [
            {
                "execution_id": exec_id,
                "workflow_id": info["workflow_id"],
                "status": info["status"].value,
                "started_at": info["started_at"].isoformat(),
                "elapsed_seconds": (
                    datetime.utcnow() - info["started_at"]
                ).total_seconds(),
                "steps_completed": info.get("steps_completed", 0),
                "steps_failed": info.get("steps_failed", 0),
                "current_step": info.get("current_step"),
            }
            for exec_id, info in self._active.items()
            if info["status"] in (ExecutionStatus.RUNNING, ExecutionStatus.PENDING)
        ]

        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_events = 0
        for records in self._records.values():
            recent_events += sum(
                1 for r in records if r.timestamp >= recent_cutoff
            )

        return {
            "performance": perf,
            "active_executions": active_executions,
            "active_count": len(active_executions),
            "recent_events_last_hour": recent_events,
        }
