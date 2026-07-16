"""Progress Tracker for Execution Engine.

Tracks execution progress and status.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(str, Enum):
    """Task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


@dataclass
class TaskProgress:
    """Single task progress."""

    task_id: str
    agent_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0
    current_file: str | None = None
    current_tool: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None


@dataclass
class ExecutionProgress:
    """Complete execution progress."""

    execution_id: str
    status: str
    overall_progress: float
    tasks: list[TaskProgress]
    current_task: str | None = None
    current_agent: str | None = None
    elapsed_time: float = 0.0
    estimated_remaining: float | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class ProgressTracker:
    """Tracks execution progress."""

    def __init__(self):
        """Initialize progress tracker."""
        self._progress: dict[str, ExecutionProgress] = {}

    def create_progress(
        self,
        execution_id: str,
        total_tasks: int,
    ) -> ExecutionProgress:
        """Create new progress tracker."""
        progress = ExecutionProgress(
            execution_id=execution_id,
            status="initializing",
            overall_progress=0.0,
            tasks=[],
        )
        self._progress[execution_id] = progress
        return progress

    def add_task(
        self,
        execution_id: str,
        task_id: str,
        agent_id: str,
        description: str,
    ) -> TaskProgress:
        """Add task to progress."""
        progress = self._progress.get(execution_id)
        if not progress:
            progress = self.create_progress(execution_id, 0)

        task = TaskProgress(
            task_id=task_id,
            agent_id=agent_id,
            description=description,
        )
        progress.tasks.append(task)
        return task

    def update_task(
        self,
        execution_id: str,
        task_id: str,
        status: TaskStatus | None = None,
        progress: float | None = None,
        current_file: str | None = None,
        current_tool: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update task progress."""
        exec_progress = self._progress.get(execution_id)
        if not exec_progress:
            return

        for task in exec_progress.tasks:
            if task.task_id == task_id:
                if status:
                    task.status = status
                    if status == TaskStatus.RUNNING and not task.started_at:
                        task.started_at = datetime.utcnow()
                    elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        task.completed_at = datetime.utcnow()
                if progress is not None:
                    task.progress = progress
                if current_file:
                    task.current_file = current_file
                if current_tool:
                    task.current_tool = current_tool
                if error:
                    task.error = error

                # Update overall progress
                self._update_overall_progress(exec_progress)
                exec_progress.updated_at = datetime.utcnow()

                break

    def update_execution_status(
        self,
        execution_id: str,
        status: str,
    ) -> None:
        """Update execution status."""
        progress = self._progress.get(execution_id)
        if progress:
            progress.status = status
            progress.updated_at = datetime.utcnow()

    def _update_overall_progress(self, progress: ExecutionProgress) -> None:
        """Update overall progress."""
        if not progress.tasks:
            progress.overall_progress = 0.0
            return

        completed = sum(1 for t in progress.tasks if t.status == TaskStatus.COMPLETED)
        running = sum(1 for t in progress.tasks if t.status == TaskStatus.RUNNING)

        progress.overall_progress = ((completed + running * 0.5) / len(progress.tasks)) * 100

        # Update current task
        for task in progress.tasks:
            if task.status == TaskStatus.RUNNING:
                progress.current_task = task.task_id
                progress.current_agent = task.agent_id
                break

    def get_progress(self, execution_id: str) -> ExecutionProgress | None:
        """Get execution progress."""
        return self._progress.get(execution_id)

    def get_task_progress(
        self,
        execution_id: str,
        task_id: str,
    ) -> TaskProgress | None:
        """Get task progress."""
        progress = self._progress.get(execution_id)
        if not progress:
            return None

        for task in progress.tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_summary(self, execution_id: str) -> dict[str, Any]:
        """Get progress summary."""
        progress = self._progress.get(execution_id)
        if not progress:
            return {}

        return {
            "execution_id": execution_id,
            "status": progress.status,
            "overall_progress": progress.overall_progress,
            "total_tasks": len(progress.tasks),
            "completed_tasks": sum(1 for t in progress.tasks if t.status == TaskStatus.COMPLETED),
            "running_tasks": sum(1 for t in progress.tasks if t.status == TaskStatus.RUNNING),
            "failed_tasks": sum(1 for t in progress.tasks if t.status == TaskStatus.FAILED),
            "current_task": progress.current_task,
            "current_agent": progress.current_agent,
            "elapsed_time": progress.elapsed_time,
            "started_at": progress.started_at.isoformat(),
            "updated_at": progress.updated_at.isoformat(),
        }
