"""Prompt versioning and management service."""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger
import uuid

logger = get_logger(__name__)


@dataclass
class PromptVersion:
    """A single version of a prompt."""

    version: int
    content: str
    created_by: str
    created_at: datetime
    comment: str = ""


@dataclass
class PromptTemplate:
    """A versioned prompt template."""

    id: str
    name: str
    description: str
    content: str
    variables: list[str] = field(default_factory=list)
    versions: list[PromptVersion] = field(default_factory=list)
    current_version: int = 1
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptTestResult:
    """Result of testing a prompt against a model."""

    prompt_id: str
    model: str
    input: dict[str, Any]
    output: str
    tokens_used: int
    latency_ms: float
    confidence: float


class PromptManagerService:
    """Service for managing prompt templates with version history.

    Stores prompts in-memory and provides versioning, comparison,
    and testing capabilities.
    """

    def __init__(self) -> None:
        self._prompts: dict[str, PromptTemplate] = {}

    async def list_prompts(self) -> list[PromptTemplate]:
        """List all stored prompts.

        Returns:
            List of all PromptTemplate instances.
        """
        return list(self._prompts.values())

    async def get_prompt(self, prompt_id: str) -> PromptTemplate:
        """Get a prompt by ID.

        Args:
            prompt_id: The prompt identifier.

        Returns:
            The PromptTemplate instance.

        Raises:
            ValueError: If prompt is not found.
        """
        prompt = self._prompts.get(prompt_id)
        if prompt is None:
            raise ValueError(f"Prompt not found: {prompt_id}")
        return prompt

    async def create_prompt(
        self,
        name: str,
        description: str,
        content: str,
        variables: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> str:
        """Create a new prompt template.

        Args:
            name: Prompt name.
            description: Prompt description.
            content: Prompt content.
            variables: Template variable names.
            tags: Classification tags.

        Returns:
            The new prompt ID.
        """
        prompt_id = str(uuid.uuid4())
        now = datetime.now(UTC)

        version = PromptVersion(
            version=1,
            content=content,
            created_by="system",
            created_at=now,
            comment="Initial version",
        )

        prompt = PromptTemplate(
            id=prompt_id,
            name=name,
            description=description,
            content=content,
            variables=variables or [],
            versions=[version],
            current_version=1,
            tags=tags or [],
        )

        self._prompts[prompt_id] = prompt
        logger.info("Created prompt '%s' (id=%s)", name, prompt_id[:8])
        return prompt_id

    async def update_prompt(
        self, prompt_id: str, content: str, comment: str
    ) -> str:
        """Update prompt content, creating a new version.

        Args:
            prompt_id: The prompt identifier.
            content: New prompt content.
            comment: Version comment.

        Returns:
            The new version number.

        Raises:
            ValueError: If prompt is not found.
        """
        prompt = await self.get_prompt(prompt_id)

        new_version = prompt.current_version + 1
        version_entry = PromptVersion(
            version=new_version,
            content=content,
            created_by="system",
            created_at=datetime.now(UTC),
            comment=comment,
        )

        prompt.versions.append(version_entry)
        prompt.content = content
        prompt.current_version = new_version

        logger.info(
            "Updated prompt id=%s to version %d", prompt_id[:8], new_version
        )
        return new_version

    async def rollback_prompt(self, prompt_id: str, version: int) -> None:
        """Rollback a prompt to a previous version.

        Args:
            prompt_id: The prompt identifier.
            version: Target version number.

        Raises:
            ValueError: If prompt or version is not found.
        """
        prompt = await self.get_prompt(prompt_id)

        target = None
        for v in prompt.versions:
            if v.version == version:
                target = v
                break

        if target is None:
            raise ValueError(
                f"Version {version} not found for prompt {prompt_id}"
            )

        prompt.content = target.content
        prompt.current_version = version

        logger.info(
            "Rolled back prompt id=%s to version %d", prompt_id[:8], version
        )

    async def compare_versions(
        self, prompt_id: str, v1: int, v2: int
    ) -> dict[str, Any]:
        """Compare two versions of a prompt.

        Args:
            prompt_id: The prompt identifier.
            v1: First version number.
            v2: Second version number.

        Returns:
            Diff data between the two versions.

        Raises:
            ValueError: If prompt or either version is not found.
        """
        prompt = await self.get_prompt(prompt_id)

        content_v1 = None
        content_v2 = None

        for v in prompt.versions:
            if v.version == v1:
                content_v1 = v.content
            if v.version == v2:
                content_v2 = v.content

        if content_v1 is None:
            raise ValueError(f"Version {v1} not found")
        if content_v2 is None:
            raise ValueError(f"Version {v2} not found")

        diff = list(difflib.unified_diff(
            content_v1.splitlines(keepends=True),
            content_v2.splitlines(keepends=True),
            fromfile=f"v{v1}",
            tofile=f"v{v2}",
        ))

        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

        return {
            "prompt_id": prompt_id,
            "version_1": v1,
            "version_2": v2,
            "diff": "".join(diff),
            "lines_added": added,
            "lines_removed": removed,
            "identical": content_v1 == content_v2,
        }

    async def test_prompt(
        self,
        prompt_id: str,
        model: str,
        input_vars: dict[str, Any],
    ) -> PromptTestResult:
        """Test a prompt with given variables.

        Args:
            prompt_id: The prompt identifier.
            model: Model to test against.
            input_vars: Variable values for template.

        Returns:
            PromptTestResult with the output.

        Raises:
            ValueError: If prompt is not found.
        """
        prompt = await self.get_prompt(prompt_id)

        content = prompt.content
        for key, value in input_vars.items():
            content = content.replace(f"{{{key}}}", str(value))

        output = f"[Test output for model={model}] Simulated response for: {content[:100]}..."
        tokens_used = len(content.split()) + len(output.split())

        result = PromptTestResult(
            prompt_id=prompt_id,
            model=model,
            input=input_vars,
            output=output,
            tokens_used=tokens_used,
            latency_ms=150.0,
            confidence=0.85,
        )

        logger.info(
            "Tested prompt id=%s model=%s tokens=%d",
            prompt_id[:8],
            model,
            tokens_used,
        )

        return result

    async def search_prompts(
        self, query: str, tags: list[str] | None = None
    ) -> list[PromptTemplate]:
        """Search prompts by query and tags.

        Args:
            query: Search string to match against name, description, content.
            tags: Optional tags to filter by.

        Returns:
            Matching prompt templates.
        """
        results: list[PromptTemplate] = []
        query_lower = query.lower()

        for prompt in self._prompts.values():
            name_match = query_lower in prompt.name.lower()
            desc_match = query_lower in prompt.description.lower()
            content_match = query_lower in prompt.content.lower()

            if not (name_match or desc_match or content_match):
                continue

            if tags:
                if not any(t in prompt.tags for t in tags):
                    continue

            results.append(prompt)

        return results

    async def get_prompt_history(self, prompt_id: str) -> list[PromptVersion]:
        """Get version history for a prompt.

        Args:
            prompt_id: The prompt identifier.

        Returns:
            List of PromptVersion instances.

        Raises:
            ValueError: If prompt is not found.
        """
        prompt = await self.get_prompt(prompt_id)
        return list(prompt.versions)
