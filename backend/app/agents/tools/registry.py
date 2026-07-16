"""Registry for managing available tools."""

from typing import Any

from app.agents.exceptions import ToolExecutionError, ToolNotFoundError
from app.agents.schemas import ToolDefinition, ToolType
from app.agents.tools.base import ToolBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Registry for managing and executing tools.

    Provides a central location for tool registration, discovery, and execution.
    Agents use this registry to find and use available tools.
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        """Register a tool in the registry.

        Args:
            tool: Tool instance to register.
        """
        self._tools[tool.name] = tool
        logger.info("Tool registered: %s (%s)", tool.name, tool.tool_type.value)

    def unregister(self, tool_name: str) -> None:
        """Remove a tool from the registry.

        Args:
            tool_name: Name of the tool to remove.
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info("Tool unregistered: %s", tool_name)

    def get_tool(self, tool_name: str) -> ToolBase:
        """Get a tool by name.

        Args:
            tool_name: Name of the tool to retrieve.

        Returns:
            The requested tool instance.

        Raises:
            ToolNotFoundError: If the tool is not registered.
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(tool_name)
        return self._tools[tool_name]

    def get_tools_by_type(self, tool_type: ToolType) -> list[ToolBase]:
        """Get all tools of a specific type.

        Args:
            tool_type: Type of tools to retrieve.

        Returns:
            List of tools matching the specified type.
        """
        return [
            tool for tool in self._tools.values()
            if tool.tool_type == tool_type
        ]

    def get_all_tools(self) -> list[ToolBase]:
        """Get all registered tools.

        Returns:
            List of all registered tools.
        """
        return list(self._tools.values())

    def get_tool_definitions(self) -> list[ToolDefinition]:
        """Get definitions for all registered tools.

        Returns:
            List of tool definitions.
        """
        return [tool.get_definition() for tool in self._tools.values()]

    def get_available_tool_names(self) -> list[str]:
        """Get names of all available tools.

        Returns:
            List of tool names.
        """
        return list(self._tools.keys())

    async def execute_tool(
        self,
        tool_name: str,
        agent_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute.
            agent_id: ID of the agent executing the tool (for logging).
            **kwargs: Parameters to pass to the tool.

        Returns:
            Dictionary containing the tool execution results.

        Raises:
            ToolNotFoundError: If the tool is not registered.
            ToolExecutionError: If the tool fails to execute.
        """
        tool = self.get_tool(tool_name)

        try:
            logger.info(
                "Executing tool: %s (agent: %s)",
                tool_name,
                agent_id or "system",
            )
            result = await tool.execute(**kwargs)
            logger.info("Tool execution completed: %s", tool_name)
            return result
        except Exception as e:
            logger.error("Tool execution failed: %s - %s", tool_name, str(e))
            raise ToolExecutionError(
                tool_name=tool_name,
                message=str(e),
                agent_id=agent_id,
            )

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools
