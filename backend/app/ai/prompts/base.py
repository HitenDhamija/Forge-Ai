"""Base prompt template class."""

from abc import ABC, abstractmethod
from typing import Any


class BasePrompt(ABC):
    """Base class for all prompt templates.

    Subclasses must set ``name``, ``description``, and ``system_prompt``,
    and implement ``build_messages``.
    """

    name: str
    description: str
    system_prompt: str

    @abstractmethod
    def build_messages(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        """Build the message list for the LLM.

        Args:
            user_input: The latest user message.
            context: Optional context dict (e.g., conversation history).

        Returns:
            List of ``{"role": ..., "content": ...}`` dicts.
        """
        ...

    def get_system_prompt(self) -> str:
        """Return the system prompt string."""
        return self.system_prompt
