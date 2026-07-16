"""Execution Summary for Execution Engine.

Generates execution reports and summaries.
"""

from typing import Any
from dataclasses import dataclass, field
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionSummary:
    """Complete execution summary."""

    execution_id: str
    workflow_id: str
    status: str
    tasks_executed: int
    tasks_succeeded: int
    tasks_failed: int
    files_modified: list[str]
    files_created: list[str]
    files_deleted: list[str]
    commits_created: list[str]
    tests_executed: int
    warnings: list[str]
    errors: list[str]
    rollback_available: bool
    execution_duration: float
    started_at: datetime
    completed_at: datetime | None = None
    summary: str = ""


class ExecutionSummaryGenerator:
    """Generates execution reports."""

    def __init__(self):
        """Initialize summary generator."""

    async def generate(
        self,
        execution_id: str,
        workflow_id: str,
        status: str,
        tasks: list[dict[str, Any]],
        files_modified: list[str],
        files_created: list[str],
        files_deleted: list[str],
        commits: list[str],
        warnings: list[str],
        errors: list[str],
        started_at: datetime,
        completed_at: datetime | None = None,
    ) -> ExecutionSummary:
        """Generate execution summary.

        Args:
            execution_id: Execution identifier.
            workflow_id: Workflow identifier.
            status: Execution status.
            tasks: List of tasks.
            files_modified: Modified files.
            files_created: Created files.
            files_deleted: Deleted files.
            commits: Commits created.
            warnings: Warnings.
            errors: Errors.
            started_at: Start time.
            completed_at: End time.

        Returns:
            Execution summary.
        """
        logger.info("Generating execution summary for %s", execution_id[:8])

        # Calculate duration
        duration = 0.0
        if completed_at:
            duration = (completed_at - started_at).total_seconds()

        # Count tasks
        tasks_executed = len(tasks)
        tasks_succeeded = sum(1 for t in tasks if t.get("status") == "completed")
        tasks_failed = sum(1 for t in tasks if t.get("status") == "failed")

        # Generate summary text
        summary = self._generate_summary_text(
            status, tasks_executed, tasks_succeeded, tasks_failed,
            len(files_modified), len(files_created), len(files_deleted)
        )

        result = ExecutionSummary(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=status,
            tasks_executed=tasks_executed,
            tasks_succeeded=tasks_succeeded,
            tasks_failed=tasks_failed,
            files_modified=files_modified,
            files_created=files_created,
            files_deleted=files_deleted,
            commits_created=commits,
            tests_executed=0,
            warnings=warnings,
            errors=errors,
            rollback_available=status == "completed",
            execution_duration=duration,
            started_at=started_at,
            completed_at=completed_at,
            summary=summary,
        )

        logger.info(
            "Execution summary generated: %d tasks, %d files changed, duration=%.1fs",
            tasks_executed,
            len(files_modified) + len(files_created) + len(files_deleted),
            duration,
        )

        return result

    def _generate_summary_text(
        self,
        status: str,
        tasks_executed: int,
        tasks_succeeded: int,
        tasks_failed: int,
        files_modified: int,
        files_created: int,
        files_deleted: int,
    ) -> str:
        """Generate summary text."""
        parts = []

        if status == "completed":
            parts.append("Execution completed successfully.")
        elif status == "failed":
            parts.append("Execution failed.")
        else:
            parts.append(f"Execution {status}.")

        parts.append(
            f"Executed {tasks_executed} tasks "
            f"({tasks_succeeded} succeeded, {tasks_failed} failed)."
        )

        file_changes = files_modified + files_created + files_deleted
        if file_changes > 0:
            parts.append(
                f"Modified {files_modified} files, "
                f"created {files_created} files, "
                f"deleted {files_deleted} files."
            )

        return " ".join(parts)

    def format_markdown(self, summary: ExecutionSummary) -> str:
        """Format summary as markdown."""
        lines = []
        lines.append("# Execution Report")
        lines.append("")
        lines.append(f"**Execution ID:** {summary.execution_id}")
        lines.append(f"**Workflow ID:** {summary.workflow_id}")
        lines.append(f"**Status:** {summary.status}")
        lines.append(f"**Duration:** {summary.execution_duration:.1f}s")
        lines.append("")

        lines.append("## Tasks")
        lines.append(f"- Executed: {summary.tasks_executed}")
        lines.append(f"- Succeeded: {summary.tasks_succeeded}")
        lines.append(f"- Failed: {summary.tasks_failed}")
        lines.append("")

        lines.append("## File Changes")
        lines.append(f"- Modified: {len(summary.files_modified)}")
        lines.append(f"- Created: {len(summary.files_created)}")
        lines.append(f"- Deleted: {len(summary.files_deleted)}")
        lines.append("")

        if summary.commits_created:
            lines.append("## Commits")
            for commit in summary.commits_created:
                lines.append(f"- {commit}")
            lines.append("")

        if summary.warnings:
            lines.append("## Warnings")
            for warning in summary.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        if summary.errors:
            lines.append("## Errors")
            for error in summary.errors:
                lines.append(f"- {error}")
            lines.append("")

        lines.append("## Summary")
        lines.append(summary.summary)

        return "\n".join(lines)
