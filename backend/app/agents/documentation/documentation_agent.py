"""Documentation Agent for Documentation Pipeline.

Generates documentation, release notes, and change reports.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

from app.core.logging import get_logger
from app.agents.documentation.release_notes import ReleaseNotesGenerator, ReleaseNotes
from app.agents.documentation.change_report import ChangeReportGenerator, ChangeReport

logger = get_logger(__name__)


class DocumentationStatus(str, Enum):
    """Documentation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DocumentationContext:
    """Context for documentation generation."""

    task_id: str
    repository_id: str
    task_description: str
    files_changed: list[str]
    changes: dict[str, Any]
    status: DocumentationStatus = DocumentationStatus.PENDING
    release_notes: ReleaseNotes | None = None
    change_report: ChangeReport | None = None
    api_documentation: str = ""
    readme_updates: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class DocumentationAgent:
    """Documentation Agent."""

    def __init__(self):
        """Initialize documentation agent."""
        self.release_notes_generator = ReleaseNotesGenerator()
        self.change_report_generator = ChangeReportGenerator()
        self._processes: dict[str, DocumentationContext] = {}

    async def start_documentation(
        self,
        task_id: str,
        repository_id: str,
        task_description: str,
        files_changed: list[str],
        changes: dict[str, Any],
    ) -> DocumentationContext:
        """Start documentation generation.

        Args:
            task_id: Task identifier.
            repository_id: Repository identifier.
            task_description: Task description.
            files_changed: List of changed files.
            changes: Change details.

        Returns:
            Documentation context with results.
        """
        doc_id = str(uuid.uuid4())

        context = DocumentationContext(
            task_id=task_id,
            repository_id=repository_id,
            task_description=task_description,
            files_changed=files_changed,
            changes=changes,
        )

        self._processes[doc_id] = context

        logger.info(
            "Starting documentation: id=%s, task=%s",
            doc_id,
            task_id,
        )

        try:
            context.status = DocumentationStatus.IN_PROGRESS

            # Generate release notes
            logger.info("Generating release notes")
            change_dicts = [
                {"type": "feature", "description": task_description}
            ]
            context.release_notes = await self.release_notes_generator.generate(
                version="1.0.0",
                changes=change_dicts,
            )

            # Generate change report
            logger.info("Generating change report")
            context.change_report = await self.change_report_generator.generate(
                task_description=task_description,
                files_changed=files_changed,
                changes=changes,
            )

            # Generate API documentation
            context.api_documentation = await self._generate_api_docs(
                files_changed, changes
            )

            # Generate README updates
            context.readme_updates = await self._generate_readme_updates(
                task_description, files_changed
            )

            context.status = DocumentationStatus.COMPLETED
            context.completed_at = datetime.utcnow()

            logger.info(
                "Documentation completed: id=%s",
                doc_id,
            )

        except Exception as e:
            logger.error("Documentation failed: %s", str(e))
            context.status = DocumentationStatus.FAILED
            context.completed_at = datetime.utcnow()

        return context

    def get_process(self, doc_id: str) -> DocumentationContext | None:
        """Get documentation process."""
        return self._processes.get(doc_id)

    def list_processes(
        self,
        status: DocumentationStatus | None = None,
    ) -> list[DocumentationContext]:
        """List documentation processes."""
        processes = list(self._processes.values())
        if status:
            processes = [p for p in processes if p.status == status]
        return processes

    async def _generate_api_docs(
        self,
        files_changed: list[str],
        changes: dict[str, Any],
    ) -> str:
        """Generate API documentation."""
        api_files = [f for f in files_changed if "api" in f.lower() or "router" in f.lower()]

        if not api_files:
            return "No API changes detected."

        lines = ["## API Changes", ""]
        for file in api_files:
            lines.append(f"### {file}")
            lines.append("")
            lines.append("Updated endpoint documentation.")
            lines.append("")

        return "\n".join(lines)

    async def _generate_readme_updates(
        self,
        task_description: str,
        files_changed: list[str],
    ) -> str:
        """Generate README updates."""
        lines = ["## Updates", ""]
        lines.append(f"- {task_description}")
        lines.append("")
        lines.append("### Changed Files")
        for file in files_changed:
            lines.append(f"- `{file}`")

        return "\n".join(lines)
