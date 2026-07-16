"""Change Report Generator for Documentation Agent.

Generates detailed change reports.
"""

from typing import Any
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChangeReport:
    """Change report."""

    summary: str
    files_changed: list[dict[str, Any]]
    lines_added: int
    lines_removed: int
    breaking_changes: list[str]
    warnings: list[str]
    security_notes: list[str]
    testing_status: str


class ChangeReportGenerator:
    """Generates change reports."""

    def __init__(self):
        """Initialize change report generator."""

    async def generate(
        self,
        task_description: str,
        files_changed: list[str],
        changes: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> ChangeReport:
        """Generate change report.

        Args:
            task_description: Task description.
            files_changed: List of changed files.
            changes: Change details.
            context: Optional context.

        Returns:
            Change report.
        """
        logger.info("Generating change report for %d files", len(files_changed))

        # Calculate stats
        lines_added = sum(
            changes.get(f, {}).get("additions", 0) for f in files_changed
        )
        lines_removed = sum(
            changes.get(f, {}).get("deletions", 0) for f in files_changed
        )

        # Build file details
        file_details = []
        for file_path in files_changed:
            file_changes = changes.get(file_path, {})
            file_details.append({
                "path": file_path,
                "action": "created" if file_changes.get("is_new") else "modified",
                "additions": file_changes.get("additions", 0),
                "deletions": file_changes.get("deletions", 0),
            })

        # Generate summary
        summary = self._generate_summary(
            task_description, files_changed, lines_added, lines_removed
        )

        # Identify breaking changes
        breaking_changes = self._identify_breaking_changes(changes)

        # Generate warnings
        warnings = self._generate_warnings(changes)

        # Generate security notes
        security_notes = self._generate_security_notes(changes)

        report = ChangeReport(
            summary=summary,
            files_changed=file_details,
            lines_added=lines_added,
            lines_removed=lines_removed,
            breaking_changes=breaking_changes,
            warnings=warnings,
            security_notes=security_notes,
            testing_status="tests generated",
        )

        logger.info(
            "Change report generated: +%d/-%d lines, %d files",
            lines_added,
            lines_removed,
            len(files_changed),
        )

        return report

    def _generate_summary(
        self,
        task_description: str,
        files_changed: list[str],
        lines_added: int,
        lines_removed: int,
    ) -> str:
        """Generate change summary."""
        return (
            f"{task_description}. "
            f"Modified {len(files_changed)} files "
            f"({lines_added} additions, {lines_removed} deletions)."
        )

    def _identify_breaking_changes(
        self,
        changes: dict[str, Any],
    ) -> list[str]:
        """Identify breaking changes."""
        breaking = []

        for file_path, change in changes.items():
            if isinstance(change, dict):
                if change.get("breaking"):
                    breaking.append(f"Modified {file_path}")
                if change.get("api_change"):
                    breaking.append(f"API changed in {file_path}")

        return breaking

    def _generate_warnings(self, changes: dict[str, Any]) -> list[str]:
        """Generate warnings."""
        warnings = []

        for file_path, change in changes.items():
            if isinstance(change, dict):
                if change.get("large_change", False):
                    warnings.append(f"Large change in {file_path}")
                if change.get("complex_change", False):
                    warnings.append(f"Complex change in {file_path}")

        return warnings

    def _generate_security_notes(self, changes: dict[str, Any]) -> list[str]:
        """Generate security notes."""
        notes = []

        for file_path, change in changes.items():
            if isinstance(change, dict):
                if change.get("security_related"):
                    notes.append(f"Security-related change in {file_path}")
                if change.get("auth_change"):
                    notes.append(f"Authentication modified in {file_path}")

        return notes

    def format_markdown(self, report: ChangeReport) -> str:
        """Format change report as markdown."""
        lines = []
        lines.append("# Change Report")
        lines.append("")
        lines.append(report.summary)
        lines.append("")
        lines.append("## Statistics")
        lines.append(f"- Files changed: {len(report.files_changed)}")
        lines.append(f"- Lines added: {report.lines_added}")
        lines.append(f"- Lines removed: {report.lines_removed}")
        lines.append("")

        if report.files_changed:
            lines.append("## Files Changed")
            for file in report.files_changed:
                lines.append(
                    f"- {file['action'].title()}: {file['path']} "
                    f"(+{file['additions']}/-{file['deletions']})"
                )
            lines.append("")

        if report.breaking_changes:
            lines.append("## Breaking Changes")
            for change in report.breaking_changes:
                lines.append(f"- {change}")
            lines.append("")

        if report.warnings:
            lines.append("## Warnings")
            for warning in report.warnings:
                lines.append(f"- {warning}")
            lines.append("")

        if report.security_notes:
            lines.append("## Security Notes")
            for note in report.security_notes:
                lines.append(f"- {note}")
            lines.append("")

        lines.append(f"## Testing Status")
        lines.append(report.testing_status)

        return "\n".join(lines)
