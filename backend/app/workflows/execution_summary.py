"""Execution summary generator for workflows."""

from typing import Any

from app.workflows.events import WorkflowEventEmitter
from app.workflows.schemas import ExecutionSummary, EventType, WorkflowEvent
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionSummaryGenerator:
    """Generator for workflow execution summaries."""

    def generate(
        self,
        workflow_id: str,
        tasks: list[dict[str, Any]],
        events: list[WorkflowEvent],
        total_duration: int,
    ) -> ExecutionSummary:
        """Generate an execution summary.

        Args:
            workflow_id: Workflow ID.
            tasks: List of task dictionaries.
            events: List of workflow events.
            total_duration: Total execution duration in seconds.

        Returns:
            Execution summary.
        """
        total_tasks = len(tasks)
        completed_tasks = sum(
            1 for t in tasks if t.get("status") == "completed"
        )
        failed_tasks = sum(
            1 for t in tasks if t.get("status") == "failed"
        )
        skipped_tasks = sum(
            1 for t in tasks if t.get("status") == "skipped"
        )

        success_rate = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        task_durations = [
            t.get("duration", 0)
            for t in tasks
            if t.get("duration") is not None
        ]
        average_task_duration = (
            sum(task_durations) / len(task_durations)
            if task_durations
            else 0
        )

        return ExecutionSummary(
            workflow_id=workflow_id,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            skipped_tasks=skipped_tasks,
            total_duration=total_duration,
            events=events,
            success_rate=round(success_rate, 2),
            average_task_duration=round(average_task_duration, 2),
        )

    def generate_report(self, summary: ExecutionSummary) -> str:
        """Generate a human-readable report.

        Args:
            summary: Execution summary.

        Returns:
            Formatted report string.
        """
        lines = [
            f"Execution Summary for Workflow {summary.workflow_id}",
            "=" * 50,
            "",
            f"Total Tasks: {summary.total_tasks}",
            f"Completed: {summary.completed_tasks}",
            f"Failed: {summary.failed_tasks}",
            f"Skipped: {summary.skipped_tasks}",
            f"Success Rate: {summary.success_rate}%",
            "",
            f"Total Duration: {summary.total_duration}s",
            f"Average Task Duration: {summary.average_task_duration}s",
            "",
            "Events:",
        ]

        for event in summary.events:
            lines.append(
                f"  [{event.timestamp}] {event.event_type.value}"
                + (f" (task: {event.task_id})" if event.task_id else "")
            )

        return "\n".join(lines)
