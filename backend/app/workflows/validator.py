"""Workflow validator for ensuring workflow integrity."""

from typing import Any

from app.workflows.schemas import ValidationResult, RiskLevel
from app.workflows.scheduler import TaskScheduler
from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowValidator:
    """Validator for workflow definitions.

    Ensures workflows are valid before execution.
    """

    def __init__(self) -> None:
        """Initialize the validator."""
        self.scheduler = TaskScheduler()

    def validate(
        self,
        tasks: list[dict[str, Any]],
        requires_approval: bool = True,
        risk_level: str = "medium",
    ) -> ValidationResult:
        """Validate a workflow definition.

        Args:
            tasks: List of task definitions.
            requires_approval: Whether approval is required.
            risk_level: Risk level.

        Returns:
            Validation result.
        """
        errors = []
        warnings = []

        if not tasks:
            errors.append("Workflow must have at least one task")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                dependency_cycles=[],
                ready_tasks=[],
            )

        task_ids = {task["id"] for task in tasks}

        for task in tasks:
            deps = task.get("dependencies", [])
            for dep in deps:
                if dep not in task_ids:
                    errors.append(
                        f"Task '{task['id']}' depends on non-existent task '{dep}'"
                    )

        cycles = self.scheduler.detect_circular_dependencies(tasks)
        if cycles:
            for cycle in cycles:
                errors.append(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                )

        duplicate_ids = [tid for tid in task_ids if sum(1 for t in tasks if t["id"] == tid) > 1]
        if duplicate_ids:
            errors.append(f"Duplicate task IDs: {', '.join(set(duplicate_ids))}")

        for task in tasks:
            if not task.get("title"):
                errors.append(f"Task '{task['id']}' is missing a title")
            if not task.get("description"):
                warnings.append(f"Task '{task['id']}' is missing a description")

        completed_tasks = set()
        ready_tasks = self.scheduler.get_ready_tasks(tasks, completed_tasks)

        execution_layers = self.scheduler.estimate_execution_order(tasks)
        estimated_duration = self.scheduler.estimate_duration(tasks, execution_layers)

        if estimated_duration > 3600:
            warnings.append(
                f"Estimated execution time ({estimated_duration}s) exceeds 1 hour"
            )

        if risk_level in ("high", "critical") and not requires_approval:
            warnings.append(
                f"High risk workflow (level: {risk_level}) should require approval"
            )

        if len(tasks) > 50:
            warnings.append(
                f"Workflow has {len(tasks)} tasks, which may impact performance"
            )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            dependency_cycles=cycles,
            ready_tasks=ready_tasks,
        )

    def validate_task_transition(
        self,
        current_status: str,
        target_status: str,
    ) -> tuple[bool, str | None]:
        """Validate a task status transition.

        Args:
            current_status: Current task status.
            target_status: Target task status.

        Returns:
            Tuple of (is_valid, error_message).
        """
        from app.workflows.schemas import TaskStatus

        try:
            current = TaskStatus(current_status)
            target = TaskStatus(target_status)
            TaskStateMachine.validate_transition(current, target)
            return True, None
        except (ValueError, Exception) as e:
            return False, str(e)

    def validate_workflow_transition(
        self,
        current_status: str,
        target_status: str,
    ) -> tuple[bool, str | None]:
        """Validate a workflow status transition.

        Args:
            current_status: Current workflow status.
            target_status: Target workflow status.

        Returns:
            Tuple of (is_valid, error_message).
        """
        from app.workflows.schemas import WorkflowStatus

        try:
            current = WorkflowStatus(current_status)
            target = WorkflowStatus(target_status)
            WorkflowStateMachine.validate_transition(current, target)
            return True, None
        except (ValueError, Exception) as e:
            return False, str(e)
