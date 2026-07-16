"""Dependency analysis for the Planning Engine."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from app.core.logging import get_logger
from app.planner.schemas.planner import (
    DependencyInfo,
    Task,
    TaskStatus,
)

logger = get_logger(__name__)


class DependencyAnalyzer:
    """Analyzes and validates task dependency graphs.

    Detects circular dependencies, validates dependency chains,
    and identifies critical path tasks.
    """

    def __init__(self) -> None:
        pass

    def analyze(self, tasks: list[Task]) -> list[DependencyInfo]:
        """Analyze dependencies and produce DependencyInfo list.

        Args:
            tasks: List of tasks with dependency information.

        Returns:
            List of DependencyInfo describing all dependency relationships.
        """
        task_map = {t.id: t for t in tasks}
        dependencies: list[DependencyInfo] = []

        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    dep_info = DependencyInfo(
                        task_id=dep_id,
                        dependent_task_id=task.id,
                        dependency_type="blocks",
                        description=f"{task_map[dep_id].title} blocks {task.title}",
                    )
                    dependencies.append(dep_info)

        logger.info("Analyzed %d dependency relationships", len(dependencies))
        return dependencies

    def detect_cycles(self, tasks: list[Task]) -> list[list[str]]:
        """Detect circular dependencies in the task graph.

        Uses DFS-based cycle detection.

        Args:
            tasks: List of tasks.

        Returns:
            List of cycles found. Each cycle is a list of task IDs.
        """
        graph: dict[str, list[str]] = defaultdict(list)
        for task in tasks:
            for dep_id in task.dependencies:
                graph[dep_id].append(task.id)

        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()
        path: list[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.discard(node)

        for task in tasks:
            if task.id not in visited:
                dfs(task.id)

        if cycles:
            logger.warning("Found %d circular dependency cycles", len(cycles))

        return cycles

    def validate(self, tasks: list[Task]) -> dict[str, Any]:
        """Validate the dependency graph.

        Args:
            tasks: List of tasks.

        Returns:
            Dictionary with validation results.
        """
        task_ids = {t.id for t in tasks}
        issues: list[dict[str, str]] = []

        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    issues.append({
                        "type": "missing_dependency",
                        "task_id": task.id,
                        "missing_dep": dep_id,
                        "message": f"Task '{task.id}' depends on non-existent task '{dep_id}'",
                    })

        cycles = self.detect_cycles(tasks)
        for cycle in cycles:
            issues.append({
                "type": "circular_dependency",
                "cycle": " -> ".join(cycle),
                "message": f"Circular dependency detected: {' -> '.join(cycle)}",
            })

        orphans = self._find_orphan_tasks(tasks)
        for orphan_id in orphans:
            issues.append({
                "type": "orphan_task",
                "task_id": orphan_id,
                "message": f"Task '{orphan_id}' is not depended upon by any other task",
            })

        return {
            "valid": len(issues) == 0,
            "issue_count": len(issues),
            "issues": issues,
            "task_count": len(tasks),
            "dependency_count": sum(len(t.dependencies) for t in tasks),
        }

    def get_execution_order(self, tasks: list[Task]) -> list[list[str]]:
        """Compute topological execution order (topological sort).

        Returns a list of "levels" where tasks in the same level
        can be executed in parallel.

        Args:
            tasks: List of tasks.

        Returns:
            List of levels, each level is a list of task IDs.

        Raises:
            ValueError: If circular dependencies are detected.
        """
        cycles = self.detect_cycles(tasks)
        if cycles:
            raise ValueError(
                f"Circular dependency detected: {' -> '.join(cycles[0])}"
            )

        task_map = {t.id: t for t in tasks}
        in_degree: dict[str, int] = {t.id: 0 for t in tasks}
        graph: dict[str, list[str]] = defaultdict(list)

        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id in task_map:
                    graph[dep_id].append(task.id)
                    in_degree[task.id] += 1

        queue: deque[str] = deque()
        for task_id, degree in in_degree.items():
            if degree == 0:
                queue.append(task_id)

        levels: list[list[str]] = []
        while queue:
            level = list(queue)
            levels.append(level)
            queue.clear()
            for task_id in level:
                for neighbor in graph.get(task_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return levels

    def get_critical_path(self, tasks: list[Task]) -> list[str]:
        """Find the critical path (longest path) through the task graph.

        Args:
            tasks: List of tasks.

        Returns:
            List of task IDs on the critical path.
        """
        task_map = {t.id: t for t in tasks}
        memo: dict[str, tuple[float, list[str]]] = {}

        def longest_path(task_id: str, visited: set[str]) -> tuple[float, list[str]]:
            if task_id in memo:
                return memo[task_id]
            if task_id not in task_map:
                return (0.0, [])
            if task_id in visited:
                return (0.0, [])

            visited.add(task_id)
            task = task_map[task_id]

            best_hours = 0.0
            best_path: list[str] = []

            for dep_id in task.dependencies:
                hours, path = longest_path(dep_id, visited.copy())
                if hours > best_hours:
                    best_hours = hours
                    best_path = path

            result_hours = best_hours + task.estimated_hours
            result_path = best_path + [task_id]
            memo[task_id] = (result_hours, result_path)
            return result_hours, result_path

        max_hours = 0.0
        critical: list[str] = []
        for task in tasks:
            hours, path = longest_path(task.id, set())
            if hours > max_hours:
                max_hours = hours
                critical = path

        return critical

    def _find_orphan_tasks(self, tasks: list[Task]) -> list[str]:
        """Find tasks that no other task depends on."""
        depended_upon: set[str] = set()
        for task in tasks:
            for dep_id in task.dependencies:
                depended_upon.add(dep_id)

        return [t.id for t in tasks if t.id not in depended_upon and not t.dependencies]
