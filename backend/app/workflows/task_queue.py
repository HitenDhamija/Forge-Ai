"""Task queue for workflow execution."""

import asyncio
from collections import defaultdict
from typing import Any

from app.workflows.schemas import TaskPriority, TaskStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskQueue:
    """Priority-based task queue for workflow execution.

    Manages task queuing, prioritization, and retrieval.
    """

    def __init__(self) -> None:
        """Initialize the task queue."""
        self._queues: dict[TaskPriority, asyncio.Queue[str]] = {
            priority: asyncio.Queue()
            for priority in TaskPriority
        }
        self._tasks: dict[str, dict[str, Any]] = {}
        self._blocked: dict[str, set[str]] = defaultdict(set)

    def add_task(
        self,
        task_id: str,
        priority: TaskPriority,
        dependencies: list[str] | None = None,
    ) -> None:
        """Add a task to the queue.

        Args:
            task_id: Task ID.
            priority: Task priority.
            dependencies: Task dependencies.
        """
        self._tasks[task_id] = {
            "priority": priority,
            "dependencies": set(dependencies or []),
            "status": TaskStatus.PENDING,
        }

        if dependencies:
            for dep in dependencies:
                self._blocked[dep].add(task_id)
        else:
            self._queues[priority].put_nowait(task_id)

        logger.info("Task added to queue: %s (priority: %s)", task_id, priority.value)

    def get_ready_tasks(self) -> list[str]:
        """Get all tasks that are ready for execution.

        Returns:
            List of task IDs ready for execution.
        """
        ready = []

        for priority in [
            TaskPriority.CRITICAL,
            TaskPriority.HIGH,
            TaskPriority.MEDIUM,
            TaskPriority.LOW,
        ]:
            queue = self._queues[priority]
            while not queue.empty():
                try:
                    task_id = queue.get_nowait()
                    if self._tasks.get(task_id, {}).get("status") == TaskStatus.PENDING:
                        ready.append(task_id)
                except asyncio.QueueEmpty:
                    break

        return ready

    def mark_running(self, task_id: str) -> None:
        """Mark a task as running.

        Args:
            task_id: Task ID.
        """
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = TaskStatus.RUNNING

    def mark_completed(self, task_id: str) -> list[str]:
        """Mark a task as completed and return newly unblocked tasks.

        Args:
            task_id: Task ID.

        Returns:
            List of task IDs that are now ready.
        """
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = TaskStatus.COMPLETED

        newly_ready = []

        if task_id in self._blocked:
            for blocked_id in self._blocked[task_id]:
                if blocked_id in self._tasks:
                    self._tasks[blocked_id]["dependencies"].discard(task_id)
                    if not self._tasks[blocked_id]["dependencies"]:
                        priority = self._tasks[blocked_id]["priority"]
                        self._queues[priority].put_nowait(blocked_id)
                        newly_ready.append(blocked_id)

            del self._blocked[task_id]

        return newly_ready

    def mark_failed(self, task_id: str) -> None:
        """Mark a task as failed.

        Args:
            task_id: Task ID.
        """
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = TaskStatus.FAILED

    def mark_retrying(self, task_id: str, priority: TaskPriority) -> None:
        """Mark a task as retrying and re-queue it.

        Args:
            task_id: Task ID.
            priority: Task priority.
        """
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = TaskStatus.RETRYING
            self._queues[priority].put_nowait(task_id)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from the queue.

        Args:
            task_id: Task ID.
        """
        if task_id in self._tasks:
            del self._tasks[task_id]

        for blocked_tasks in self._blocked.values():
            blocked_tasks.discard(task_id)

    def is_empty(self) -> bool:
        """Check if the queue is empty.

        Returns:
            True if no tasks are queued.
        """
        return all(q.empty() for q in self._queues.values())

    def get_task_count(self) -> int:
        """Get total number of tasks in queue.

        Returns:
            Total task count.
        """
        return sum(q.qsize() for q in self._queues.values())

    def get_task_status(self, task_id: str) -> TaskStatus | None:
        """Get task status.

        Args:
            task_id: Task ID.

        Returns:
            Task status or None.
        """
        if task_id in self._tasks:
            return self._tasks[task_id]["status"]
        return None

    def clear(self) -> None:
        """Clear all tasks from the queue."""
        for queue in self._queues.values():
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        self._tasks.clear()
        self._blocked.clear()
