"""Complexity analysis for the Planning Engine."""

from __future__ import annotations

from app.core.logging import get_logger
from app.planner.config import get_planner_settings
from app.planner.schemas.planner import (
    ComplexityAnalysis,
    ComplexityLevel,
    Task,
)

logger = get_logger(__name__)


class ComplexityAnalyzer:
    """Analyzes the complexity of a set of tasks.

    Evaluates task count, individual complexities, dependencies,
    and other factors to produce an overall complexity assessment.
    """

    def __init__(self) -> None:
        self._settings = get_planner_settings()

    def analyze(self, tasks: list[Task]) -> ComplexityAnalysis:
        """Analyze complexity of a task list.

        Args:
            tasks: List of tasks to analyze.

        Returns:
            ComplexityAnalysis with level, score, and factors.
        """
        if not tasks:
            return ComplexityAnalysis(
                level=ComplexityLevel.SIMPLE,
                score=0.0,
                factors=["No tasks to analyze"],
                estimated_total_hours=0.0,
                task_count=0,
                avg_task_complexity=0.0,
            )

        factors: list[str] = []
        score = 0.0

        task_count_score = self._analyze_task_count(tasks, factors)
        score += task_count_score

        type_distribution_score = self._analyze_type_distribution(tasks, factors)
        score += type_distribution_score

        dependency_score = self._analyze_dependencies(tasks, factors)
        score += dependency_score

        priority_score = self._analyze_priorities(tasks, factors)
        score += priority_score

        hours_score = self._analyze_hours(tasks, factors)
        score += hours_score

        level = self._score_to_level(score)
        avg_complexity = self._calculate_avg_complexity(tasks)
        total_hours = sum(t.estimated_hours for t in tasks)

        analysis = ComplexityAnalysis(
            level=level,
            score=round(score, 2),
            factors=factors,
            estimated_total_hours=round(total_hours, 1),
            task_count=len(tasks),
            avg_task_complexity=round(avg_complexity, 2),
        )

        logger.info(
            "Complexity analysis: level=%s score=%.2f tasks=%d",
            level.value,
            score,
            len(tasks),
        )
        return analysis

    def _analyze_task_count(self, tasks: list[Task], factors: list[str]) -> float:
        """Analyze impact of task count on complexity."""
        count = len(tasks)
        thresholds = self._settings.COMPLEXITY_THRESHOLDS

        if count <= thresholds.get("simple", 3):
            factors.append(f"Low task count ({count})")
            return 0.0
        elif count <= thresholds.get("medium", 7):
            factors.append(f"Moderate task count ({count})")
            return 1.0
        elif count <= thresholds.get("complex", 12):
            factors.append(f"High task count ({count})")
            return 2.0
        else:
            factors.append(f"Very high task count ({count})")
            return 3.0

    def _analyze_type_distribution(
        self, tasks: list[Task], factors: list[str]
    ) -> float:
        """Analyze complexity from task type diversity."""
        type_counts: dict[str, int] = {}
        for task in tasks:
            type_key = task.task_type.value
            type_counts[type_key] = type_counts.get(type_key, 0) + 1

        unique_types = len(type_counts)
        score = 0.0

        if unique_types >= 5:
            factors.append(f"High task type diversity ({unique_types} types)")
            score += 1.5
        elif unique_types >= 3:
            factors.append(f"Moderate task type diversity ({unique_types} types)")
            score += 0.5
        else:
            factors.append(f"Low task type diversity ({unique_types} types)")

        if type_counts.get("implementation", 0) > 3:
            factors.append("Multiple implementation tasks")
            score += 1.0

        if type_counts.get("testing", 0) == 0 and type_counts.get("implementation", 0) > 0:
            factors.append("No testing tasks for implementation work")
            score += 0.5

        return score

    def _analyze_dependencies(self, tasks: list[Task], factors: list[str]) -> float:
        """Analyze complexity from task dependencies."""
        total_deps = sum(len(t.dependencies) for t in tasks)
        max_chain = self._find_longest_dependency_chain(tasks)
        score = 0.0

        if total_deps > len(tasks) * 1.5:
            factors.append(f"Dense dependency graph ({total_deps} dependencies)")
            score += 1.5
        elif total_deps > len(tasks):
            factors.append(f"Moderate dependency graph ({total_deps} dependencies)")
            score += 0.7
        elif total_deps > 0:
            factors.append(f"Light dependency graph ({total_deps} dependencies)")
            score += 0.2

        if max_chain > 3:
            factors.append(f"Long dependency chain ({max_chain} levels)")
            score += 1.0
        elif max_chain > 2:
            factors.append(f"Moderate dependency chain ({max_chain} levels)")
            score += 0.5

        return score

    def _analyze_priorities(self, tasks: list[Task], factors: list[str]) -> float:
        """Analyze complexity from task priorities."""
        critical_count = sum(1 for t in tasks if t.priority.value == "critical")
        high_count = sum(1 for t in tasks if t.priority.value == "high")
        score = 0.0

        if critical_count > 2:
            factors.append(f"Multiple critical tasks ({critical_count})")
            score += 1.0
        elif critical_count > 0:
            factors.append(f"Contains critical tasks ({critical_count})")
            score += 0.3

        if high_count > len(tasks) * 0.6:
            factors.append(f"Majority of tasks are high priority ({high_count}/{len(tasks)})")
            score += 0.5

        return score

    def _analyze_hours(self, tasks: list[Task], factors: list[str]) -> float:
        """Analyze complexity from estimated hours."""
        total_hours = sum(t.estimated_hours for t in tasks)

        if total_hours > 40:
            factors.append(f"High estimated effort ({total_hours:.1f} hours)")
            return 2.0
        elif total_hours > 20:
            factors.append(f"Moderate estimated effort ({total_hours:.1f} hours)")
            return 1.0
        elif total_hours > 8:
            factors.append(f"Light estimated effort ({total_hours:.1f} hours)")
            return 0.5

        return 0.0

    def _find_longest_dependency_chain(self, tasks: list[Task]) -> int:
        """Find the longest dependency chain in the task graph."""
        task_map = {t.id: t for t in tasks}
        memo: dict[str, int] = {}

        def chain_length(task_id: str, visited: set[str]) -> int:
            if task_id in memo:
                return memo[task_id]
            if task_id not in task_map:
                return 0
            if task_id in visited:
                return 0

            visited.add(task_id)
            task = task_map[task_id]
            max_child = 0
            for dep_id in task.dependencies:
                child_len = chain_length(dep_id, visited.copy())
                max_child = max(max_child, child_len)
            result = max_child + 1
            memo[task_id] = result
            return result

        max_chain = 0
        for task in tasks:
            chain = chain_length(task.id, set())
            max_chain = max(max_chain, chain)

        return max_chain

    def _score_to_level(self, score: float) -> ComplexityLevel:
        """Convert numeric score to complexity level."""
        if score <= 2.0:
            return ComplexityLevel.SIMPLE
        elif score <= 5.0:
            return ComplexityLevel.MEDIUM
        elif score <= 8.0:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX

    def _calculate_avg_complexity(self, tasks: list[Task]) -> float:
        """Calculate average complexity as a numeric value."""
        complexity_values = {
            ComplexityLevel.SIMPLE: 1.0,
            ComplexityLevel.MEDIUM: 2.0,
            ComplexityLevel.COMPLEX: 3.0,
            ComplexityLevel.VERY_COMPLEX: 4.0,
        }
        if not tasks:
            return 0.0
        total = sum(complexity_values.get(t.complexity, 1.0) for t in tasks)
        return total / len(tasks)
