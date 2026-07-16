"""Release Notes Generator for Documentation Agent.

Generates release notes and changelogs.
"""

from typing import Any
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ReleaseNotes:
    """Release notes."""

    version: str
    title: str
    summary: str
    features: list[str]
    bug_fixes: list[str]
    improvements: list[str]
    breaking_changes: list[str]
    migration_notes: list[str]
    contributors: list[str]


class ReleaseNotesGenerator:
    """Generates release notes."""

    def __init__(self):
        """Initialize release notes generator."""

    async def generate(
        self,
        version: str,
        changes: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> ReleaseNotes:
        """Generate release notes.

        Args:
            version: Version number.
            changes: List of changes.
            context: Optional context.

        Returns:
            Release notes.
        """
        logger.info("Generating release notes for version %s", version)

        features = []
        bug_fixes = []
        improvements = []
        breaking_changes = []

        for change in changes:
            change_type = change.get("type", "improvement")
            description = change.get("description", "")

            if change_type == "feature":
                features.append(description)
            elif change_type == "bug_fix":
                bug_fixes.append(description)
            elif change_type == "breaking":
                breaking_changes.append(description)
            else:
                improvements.append(description)

        title = f"Release {version}"
        summary = self._generate_summary(features, bug_fixes, improvements, breaking_changes)

        notes = ReleaseNotes(
            version=version,
            title=title,
            summary=summary,
            features=features,
            bug_fixes=bug_fixes,
            improvements=improvements,
            breaking_changes=breaking_changes,
            migration_notes=self._generate_migration_notes(breaking_changes),
            contributors=[],
        )

        logger.info(
            "Release notes generated: %d features, %d fixes, %d improvements",
            len(features),
            len(bug_fixes),
            len(improvements),
        )

        return notes

    def _generate_summary(
        self,
        features: list[str],
        bug_fixes: list[str],
        improvements: list[str],
        breaking_changes: list[str],
    ) -> str:
        """Generate release summary."""
        parts = []

        if features:
            parts.append(f"Added {len(features)} new features")
        if bug_fixes:
            parts.append(f"fixed {len(bug_fixes)} bugs")
        if improvements:
            parts.append(f"made {len(improvements)} improvements")
        if breaking_changes:
            parts.append(f"introduced {len(breaking_changes)} breaking changes")

        if not parts:
            return "General improvements and bug fixes."

        return "This release " + ", ".join(parts) + "."

    def _generate_migration_notes(
        self,
        breaking_changes: list[str],
    ) -> list[str]:
        """Generate migration notes for breaking changes."""
        notes = []

        for change in breaking_changes:
            notes.append(f"Migration required: {change}")

        return notes

    def format_markdown(self, notes: ReleaseNotes) -> str:
        """Format release notes as markdown."""
        lines = []
        lines.append(f"# {notes.title}")
        lines.append("")
        lines.append(notes.summary)
        lines.append("")

        if notes.features:
            lines.append("## Features")
            for feature in notes.features:
                lines.append(f"- {feature}")
            lines.append("")

        if notes.bug_fixes:
            lines.append("## Bug Fixes")
            for fix in notes.bug_fixes:
                lines.append(f"- {fix}")
            lines.append("")

        if notes.improvements:
            lines.append("## Improvements")
            for improvement in notes.improvements:
                lines.append(f"- {improvement}")
            lines.append("")

        if notes.breaking_changes:
            lines.append("## Breaking Changes")
            for change in notes.breaking_changes:
                lines.append(f"- {change}")
            lines.append("")

        if notes.migration_notes:
            lines.append("## Migration Guide")
            for note in notes.migration_notes:
                lines.append(f"- {note}")
            lines.append("")

        return "\n".join(lines)
