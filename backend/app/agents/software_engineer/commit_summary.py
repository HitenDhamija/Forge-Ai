"""Commit Summary for Software Engineer Agent.

Generates commit messages and summaries.
"""

from typing import Any
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CommitSummary:
    """Commit summary."""

    message: str
    description: str
    files_changed: list[str]
    additions: int
    deletions: int
    breaking_changes: list[str]
    references: list[str]


class CommitSummaryGenerator:
    """Generates commit messages and summaries."""

    def __init__(self):
        """Initialize commit summary generator."""
        self._convention = "conventional"

    async def generate(
        self,
        task_description: str,
        files_changed: list[str],
        changes: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> CommitSummary:
        """Generate commit summary.

        Args:
            task_description: Description of task.
            files_changed: List of changed files.
            changes: Change details.
            context: Optional context.

        Returns:
            Commit summary.
        """
        logger.info("Generating commit summary for %d files", len(files_changed))

        # Determine commit type
        commit_type = self._determine_commit_type(task_description, files_changed)

        # Generate scope
        scope = self._determine_scope(files_changed)

        # Generate subject
        subject = self._generate_subject(commit_type, scope, task_description)

        # Generate description
        description = self._generate_description(
            task_description, files_changed, changes
        )

        # Calculate stats
        stats = self._calculate_stats(changes)

        # Identify breaking changes
        breaking_changes = self._identify_breaking_changes(changes)

        # Generate references
        references = self._generate_references(task_description)

        summary = CommitSummary(
            message=subject,
            description=description,
            files_changed=files_changed,
            additions=stats["additions"],
            deletions=stats["deletions"],
            breaking_changes=breaking_changes,
            references=references,
        )

        logger.info(
            "Commit summary generated: type=%s, files=%d",
            commit_type,
            len(files_changed),
        )

        return summary

    def _determine_commit_type(
        self,
        task_description: str,
        files_changed: list[str],
    ) -> str:
        """Determine commit type."""
        task_lower = task_description.lower()

        if any(w in task_lower for w in ["fix", "bug", "issue"]):
            return "fix"
        if any(w in task_lower for w in ["add", "create", "implement", "feature"]):
            return "feat"
        if any(w in task_lower for w in ["refactor", "restructure", "reorganize"]):
            return "refactor"
        if any(w in task_lower for w in ["doc", "documentation", "readme"]):
            return "docs"
        if any(w in task_lower for w in ["test", "testing"]):
            return "test"
        if any(w in task_lower for w in ["style", "format", "lint"]):
            return "style"
        if any(w in task_lower for w in ["perf", "performance", "optimize"]):
            return "perf"
        if any(w in task_lower for w in ["ci", "cd", "deploy", "build"]):
            return "build"
        return "feat"

    def _determine_scope(self, files_changed: list[str]) -> str:
        """Determine commit scope."""
        if not files_changed:
            return ""

        # Get common directory
        parts = files_changed[0].split("/")
        if len(parts) > 2:
            return parts[-2]
        return ""

    def _generate_subject(
        self,
        commit_type: str,
        scope: str,
        task_description: str,
    ) -> str:
        """Generate commit subject."""
        # Clean task description
        subject = task_description.lower().strip()
        subject = subject.rstrip(".")

        # Truncate if too long
        if len(subject) > 50:
            subject = subject[:47] + "..."

        # Add scope
        if scope:
            return f"{commit_type}({scope}): {subject}"
        return f"{commit_type}: {subject}"

    def _generate_description(
        self,
        task_description: str,
        files_changed: list[str],
        changes: dict[str, Any],
    ) -> str:
        """Generate commit description."""
        lines = []
        lines.append(task_description)
        lines.append("")
        lines.append("Changes:")
        for file in files_changed:
            lines.append(f"- {file}")

        return "\n".join(lines)

    def _calculate_stats(self, changes: dict[str, Any]) -> dict[str, int]:
        """Calculate addition/deletion stats."""
        additions = 0
        deletions = 0

        for file_path, change in changes.items():
            if isinstance(change, dict):
                additions += change.get("additions", 0)
                deletions += change.get("deletions", 0)

        return {"additions": additions, "deletions": deletions}

    def _identify_breaking_changes(self, changes: dict[str, Any]) -> list[str]:
        """Identify breaking changes."""
        breaking = []

        for file_path, change in changes.items():
            if isinstance(change, dict):
                if change.get("breaking"):
                    breaking.append(f"Modified {file_path}")

        return breaking

    def _generate_references(self, task_description: str) -> list[str]:
        """Generate references."""
        references = []

        # Check for issue references
        import re
        issue_pattern = re.compile(r"#(\d+)")
        for match in issue_pattern.finditer(task_description):
            references.append(f"#{match.group(1)}")

        return references

    def format_commit_message(self, summary: CommitSummary) -> str:
        """Format commit message."""
        lines = []
        lines.append(summary.message)
        lines.append("")
        lines.append(summary.description)

        if summary.breaking_changes:
            lines.append("")
            lines.append("BREAKING CHANGE:")
            for change in summary.breaking_changes:
                lines.append(f"- {change}")

        if summary.references:
            lines.append("")
            lines.append("References:")
            for ref in summary.references:
                lines.append(f"- {ref}")

        return "\n".join(lines)
