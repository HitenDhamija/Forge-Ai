"""Context Loader for Software Engineer Agent.

Retrieves repository context, architecture, dependencies, and coding patterns.
"""

from typing import Any
from dataclasses import dataclass, field

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RepositoryContext:
    """Complete repository context for implementation."""

    repository_id: str
    summary: dict[str, Any] = field(default_factory=dict)
    architecture: dict[str, Any] = field(default_factory=dict)
    dependencies: dict[str, Any] = field(default_factory=dict)
    coding_standards: dict[str, Any] = field(default_factory=dict)
    existing_patterns: list[dict[str, Any]] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    related_files: list[str] = field(default_factory=list)
    database_models: list[dict[str, Any]] = field(default_factory=list)
    api_endpoints: list[dict[str, Any]] = field(default_factory=list)
    authentication: dict[str, Any] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)
    framework: str = "unknown"
    language: str = "unknown"


class ContextLoader:
    """Loads comprehensive repository context for implementation."""

    def __init__(self):
        """Initialize context loader."""
        self._context_cache: dict[str, RepositoryContext] = {}

    async def load_context(
        self,
        repository_id: str,
        task_description: str,
        target_files: list[str] | None = None,
    ) -> RepositoryContext:
        """Load complete context for implementation task.

        Args:
            repository_id: Repository identifier.
            task_description: Description of the task.
            target_files: Optional list of target files.

        Returns:
            Complete repository context.
        """
        logger.info("Loading context for repository %s", repository_id)

        context = RepositoryContext(
            repository_id=repository_id,
            affected_files=target_files or [],
        )

        # Load repository summary
        context.summary = await self._load_summary(repository_id)

        # Load architecture
        context.architecture = await self._load_architecture(repository_id)

        # Load dependencies
        context.dependencies = await self._load_dependencies(repository_id)

        # Detect framework and language
        context.framework = self._detect_framework(context.summary)
        context.language = self._detect_language(context.summary)

        # Load coding standards
        context.coding_standards = await self._load_coding_standards(
            repository_id, context.framework, context.language
        )

        # Load existing patterns
        context.existing_patterns = await self._load_existing_patterns(
            repository_id, task_description
        )

        # Load database models
        context.database_models = await self._load_database_models(repository_id)

        # Load API endpoints
        context.api_endpoints = await self._load_api_endpoints(repository_id)

        # Load authentication
        context.authentication = await self._load_authentication(repository_id)

        # Load configuration
        context.configuration = await self._load_configuration(repository_id)

        # Find related files
        context.related_files = await self._find_related_files(
            repository_id, task_description, context.affected_files
        )

        # Cache context
        self._context_cache[repository_id] = context

        logger.info(
            "Context loaded: framework=%s, language=%s, affected_files=%d",
            context.framework,
            context.language,
            len(context.affected_files),
        )

        return context

    async def _load_summary(self, repository_id: str) -> dict[str, Any]:
        """Load repository summary."""
        # Integration point with Repository Intelligence
        return {
            "name": "project",
            "description": "Application repository",
            "structure": {},
            "readme": "",
        }

    async def _load_architecture(self, repository_id: str) -> dict[str, Any]:
        """Load architecture information."""
        return {
            "pattern": "clean-architecture",
            "layers": ["presentation", "application", "domain", "infrastructure"],
            "modules": [],
            "services": [],
        }

    async def _load_dependencies(self, repository_id: str) -> dict[str, Any]:
        """Load project dependencies."""
        return {
            "production": {},
            "development": {},
            "manifest_files": [],
        }

    async def _load_coding_standards(
        self,
        repository_id: str,
        framework: str,
        language: str,
    ) -> dict[str, Any]:
        """Load coding standards based on framework and language."""
        standards = {
            "python": {
                "formatter": "black",
                "linter": "ruff",
                "type_hints": True,
                "docstrings": True,
                "max_line_length": 88,
            },
            "typescript": {
                "formatter": "prettier",
                "linter": "eslint",
                "type_hints": True,
                "strict": True,
            },
        }
        return standards.get(language, standards["python"])

    async def _load_existing_patterns(
        self,
        repository_id: str,
        task_description: str,
    ) -> list[dict[str, Any]]:
        """Load existing code patterns relevant to task."""
        return [
            {
                "type": "service",
                "pattern": "dependency-injection",
                "example": "class Service: def __init__(self, dep: Dep): ...",
            },
            {
                "type": "repository",
                "pattern": "repository-pattern",
                "example": "class Repo: async def get(self, id): ...",
            },
        ]

    async def _load_database_models(self, repository_id: str) -> list[dict[str, Any]]:
        """Load database models."""
        return []

    async def _load_api_endpoints(self, repository_id: str) -> list[dict[str, Any]]:
        """Load API endpoints."""
        return []

    async def _load_authentication(self, repository_id: str) -> dict[str, Any]:
        """Load authentication configuration."""
        return {
            "type": "jwt",
            "enabled": True,
            "header": "Authorization",
        }

    async def _load_configuration(self, repository_id: str) -> dict[str, Any]:
        """Load project configuration."""
        return {
            "env_files": [".env", ".env.example"],
            "config_files": ["config.py", "settings.py"],
        }

    async def _find_related_files(
        self,
        repository_id: str,
        task_description: str,
        affected_files: list[str],
    ) -> list[str]:
        """Find files related to the task."""
        return []

    def _detect_framework(self, summary: dict[str, Any]) -> str:
        """Detect framework from summary."""
        structure = summary.get("structure", {})
        if "fastapi" in str(structure).lower():
            return "fastapi"
        if "django" in str(structure).lower():
            return "django"
        if "flask" in str(structure).lower():
            return "flask"
        return "unknown"

    def _detect_language(self, summary: dict[str, Any]) -> str:
        """Detect primary language."""
        structure = summary.get("structure", {})
        if any(f.endswith(".py") for f in structure.get("files", [])):
            return "python"
        if any(f.endswith(".ts") or f.endswith(".tsx") for f in structure.get("files", [])):
            return "typescript"
        return "unknown"
