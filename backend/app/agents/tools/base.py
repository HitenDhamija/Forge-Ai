"""Base class for all tools available to agents."""

from abc import ABC, abstractmethod
from typing import Any

from app.agents.schemas import ToolDefinition, ToolType


class ToolBase(ABC):
    """Abstract base class for all tools.

    All tools must inherit from this class and implement the execute method.
    Tools provide capabilities to agents for interacting with the system.
    """

    def __init__(
        self,
        name: str,
        description: str,
        tool_type: ToolType,
        parameters: dict[str, dict] | None = None,
        required_permissions: list[str] | None = None,
    ):
        """Initialize the tool.

        Args:
            name: Unique name for this tool.
            description: Human-readable description of what this tool does.
            tool_type: Category of tool.
            parameters: JSON Schema for tool parameters.
            required_permissions: Permissions needed to use this tool.
        """
        self.name = name
        self.description = description
        self.tool_type = tool_type
        self.parameters = parameters or {}
        self.required_permissions = required_permissions or []

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool with the given parameters.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            Dictionary containing the tool execution results.

        Raises:
            ToolExecutionError: If the tool fails to execute.
        """
        pass

    @abstractmethod
    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate that the provided parameters are correct.

        Args:
            **kwargs: Parameters to validate.

        Returns:
            True if parameters are valid, False otherwise.
        """
        pass

    def get_definition(self) -> ToolDefinition:
        """Get the tool definition for registration.

        Returns:
            ToolDefinition containing all tool metadata.
        """
        return ToolDefinition(
            name=self.name,
            description=self.description,
            tool_type=self.tool_type,
            parameters=self.parameters,
            required_permissions=self.required_permissions,
        )

    def __repr__(self) -> str:
        return f"<Tool {self.name} ({self.tool_type.value})>"
