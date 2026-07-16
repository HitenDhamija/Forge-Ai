"""Task scheduler for workflow execution."""

from datetime import datetime, timezone
from typing import Any

from app.workflows.state_machine import InvalidTransitionError, TaskStateMachine, WorkflowStateMachine
from app.workflows.task_queue import TaskQueue
from app.workflows.schemas import TaskPriority, TaskStatus, WorkflowStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskScheduler:
    """Scheduler for workflow task execution.

    Responsible for:
    - Finding executable tasks
    - Detecting blocked tasks
    - Detecting circular dependencies
    - Estimating execution order
    """

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self._queues: dict[str, TaskQueue] = {}

    def create_queue(self, workflow_id: str) -> TaskQueue:
        """Create a task queue for a workflow.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Created task queue.
        """
        queue = TaskQueue()
        self._queues[workflow_id] = queue
        return queue

    def get_queue(self, workflow_id: str) -> TaskQueue | None:
        """Get task queue for a workflow.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Task queue or None.
        """
        return self._queues.get(workflow_id)

    def remove_queue(self, workflow_id: str) -> None:
        """Remove task queue for a workflow.

        Args:
            workflow_id: Workflow ID.
        """
        if workflow_id in self._queues:
            del self._queues[workflow_id]

    def detect_circular_dependencies(
        self, tasks: list[dict[str, Any]]
    ) -> list[list[str]]:
        """Detect circular dependencies in tasks.

        Args:
            tasks: List of task dictionaries with id and dependencies.

        Returns:
            List of circular dependency chains.
        """
        graph: dict[str, list[str]] = {}
        for task in tasks:
            graph[task["id"]] = task.get("dependencies", [])

        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            path.pop()
            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def estimate_execution_order(
        self, tasks: list[dict[str, Any]]
    ) -> list[list[str]]:
        """Estimate execution order using topological sort.

        Args:
            tasks: List of task dictionaries.

        Returns:
            List of execution layers (tasks in same layer can run in parallel).
        """
        graph: dict[str, set[str]] = {}
        in_degree: dict[str, int] = {}

        for task in tasks:
            task_id = task["id"]
            deps = set(task.get("dependencies", []))
            graph[task_id] = deps
            in_degree[task_id] = len(deps)

        layers = []
        remaining = set(graph.keys())

        while remaining:
            layer = [
                task_id
                for task_id in remaining
                if in_degree[task_id] == 0
            ]

            if not layer:
                break

            layers.append(sorted(layer))

            for task_id in layer:
                remaining.remove(task_id)
                for other_id in remaining:
                    if task_id in graph.get(other_id, set()):
                        in_degree[other_id] -= 1

        return layers

    def get_ready_tasks(
        self,
        tasks: list[dict[str, Any]],
        completed_tasks: set[str],
    ) -> list[str]:
        """Get tasks that are ready to execute.

        Args:
            tasks: List of task dictionaries.
            completed_tasks: Set of completed task IDs.

        Returns:
            List of ready task IDs.
        """
        ready = []

        for task in tasks:
            task_id = task["id"]
            deps = set(task.get("dependencies", []))

            if task_id not in completed_tasks and deps.issubset(completed_tasks):
                ready.append(task_id)

        return ready

    def get_blocked_tasks(
        self,
        tasks: list[dict[str, Any]],
        completed_tasks: set[str],
    ) -> list[dict[str, Any]]:
        """Get tasks that are blocked by dependencies.

        Args:
            tasks: List of task dictionaries.
            completed_tasks: Set of completed task IDs.

        Returns:
            List of blocked task dictionaries with their blocking dependencies.
        """
        blocked = []

        for task in tasks:
            task_id = task["id"]
            deps = set(task.get("dependencies", []))
            pending_deps = deps - completed_tasks

            if task_id not in completed_tasks and pending_deps:
                blocked.append({
                    "task_id": task_id,
                    "blocked_by": list(pending_deps),
                })

        return blocked

    def estimate_duration(
        self,
        tasks: list[dict[str, Any]],
        execution_layers: list[list[str]],
    ) -> int:
        """Estimate total execution duration.

        Args:
            tasks: List of task dictionaries.
            execution_layers: Execution layers from topological sort.

        Returns:
            Estimated duration in seconds.
        """
        task_map = {task["id"]: task for task in tasks}
        total_duration = 0

        for layer in execution_layers:
            layer_duration = 0
            for task_id in layer:
                task = task_map.get(task_id, {})
                duration = task.get("estimated_duration", 60)
                layer_duration = max(layer_duration, duration)
            total_duration += layer_duration

        return total_duration
