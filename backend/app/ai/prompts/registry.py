"""Prompt template registry."""

from app.ai.prompts.base import BasePrompt
from app.ai.prompts.general_chat import (
    CodeExplanationPrompt,
    DocumentationPrompt,
    GeneralChatPrompt,
    PlanningPrompt,
    SummarizationPrompt,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptRegistry:
    """Registry for managing and retrieving prompt templates."""

    def __init__(self) -> None:
        self._prompts: dict[str, BasePrompt] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register all built-in prompt templates."""
        defaults: list[BasePrompt] = [
            GeneralChatPrompt(),
            CodeExplanationPrompt(),
            PlanningPrompt(),
            SummarizationPrompt(),
            DocumentationPrompt(),
        ]
        for prompt in defaults:
            self.register(prompt)

    def register(self, prompt: BasePrompt) -> None:
        """Register a prompt template.

        Args:
            prompt: The prompt instance to register.
        """
        self._prompts[prompt.name] = prompt
        logger.debug("Registered prompt: %s", prompt.name)

    def get(self, name: str) -> BasePrompt:
        """Retrieve a prompt by name.

        Args:
            name: The prompt identifier.

        Returns:
            The matching ``BasePrompt``.

        Raises:
            KeyError: If no prompt with that name is registered.
        """
        if name not in self._prompts:
            available = ", ".join(sorted(self._prompts.keys()))
            raise KeyError(
                f"Prompt '{name}' not found. Available: {available}"
            )
        return self._prompts[name]

    def list_prompts(self) -> list[dict[str, str]]:
        """List all registered prompts.

        Returns:
            List of dicts with ``name`` and ``description`` keys.
        """
        return [
            {"name": p.name, "description": p.description}
            for p in self._prompts.values()
        ]

    def get_default(self) -> BasePrompt:
        """Return the default prompt (``general_chat``).

        Returns:
            The default ``BasePrompt`` instance.
        """
        return self._prompts["general_chat"]
