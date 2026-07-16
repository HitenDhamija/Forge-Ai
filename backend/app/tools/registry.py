"""Dynamic tool registry for discovering and managing tools."""

from datetime import datetime, timezone
from typing import Any

from app.tools.base import ToolInterface
from app.tools.schemas import (
    ToolDefinition,
    ToolHealth,
    ToolProvider,
    ToolStatus,
    ToolStatusResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Dynamic registry for tool discovery and management.

    Every tool registers:
    - Tool ID, Name, Description
    - Capabilities, Permissions
    - Version, Provider
    - Health, Status
    - Supported Operations

    Supervisor discovers tools automatically.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: dict[str, ToolInterface] = {}
        self._definitions: dict[str, ToolDefinition] = {}

    async def register(self, tool: ToolInterface) -> None:
        """Register a tool.

        Args:
            tool: Tool instance.
        """
        await tool.initialize()

        health = await tool.health_check()

        definition = ToolDefinition(
            id=tool.tool_id,
            name=tool.name,
            description=tool.description,
            provider=tool.provider,
            version=tool.version,
            capabilities=tool.capabilities,
            health=health,
            supported_operations=tool.supported_operations,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self._tools[tool.tool_id] = tool
        self._definitions[tool.tool_id] = definition

        logger.info(
            "Tool registered: %s (%s) - %s",
            tool.name,
            tool.tool_id,
            tool.provider.value,
        )

    async def unregister(self, tool_id: str) -> None:
        """Unregister a tool.

        Args:
            tool_id: Tool ID.
        """
        if tool_id in self._tools:
            tool = self._tools[tool_id]
            await tool.cleanup()

            del self._tools[tool_id]
            del self._definitions[tool_id]

            logger.info("Tool unregistered: %s", tool_id)

    def get_tool(self, tool_id: str) -> ToolInterface | None:
        """Get tool by ID.

        Args:
            tool_id: Tool ID.

        Returns:
            Tool instance or None.
        """
        return self._tools.get(tool_id)

    def get_definition(self, tool_id: str) -> ToolDefinition | None:
        """Get tool definition by ID.

        Args:
            tool_id: Tool ID.

        Returns:
            Tool definition or None.
        """
        return self._definitions.get(tool_id)

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools.

        Returns:
            List of tool definitions.
        """
        return list(self._definitions.values())

    def get_tools_by_provider(self, provider: ToolProvider) -> list[ToolDefinition]:
        """Get tools by provider.

        Args:
            provider: Tool provider.

        Returns:
            List of tool definitions.
        """
        return [
            defn for defn in self._definitions.values()
            if defn.provider == provider
        ]

    def get_healthy_tools(self) -> list[ToolDefinition]:
        """Get all healthy tools.

        Returns:
            List of healthy tool definitions.
        """
        return [
            defn for defn in self._definitions.values()
            if defn.health.status == ToolStatus.HEALTHY
        ]

    async def check_health(self, tool_id: str) -> ToolHealth | None:
        """Check health of a specific tool.

        Args:
            tool_id: Tool ID.

        Returns:
            Health status or None.
        """
        tool = self.get_tool(tool_id)
        if tool:
            health = await tool.health_check()
            self._definitions[tool_id].health = health
            self._definitions[tool_id].updated_at = datetime.now(timezone.utc)
            return health
        return None

    async def check_all_health(self) -> dict[str, ToolHealth]:
        """Check health of all tools.

        Returns:
            Dictionary of tool IDs to health statuses.
        """
        results = {}
        for tool_id in self._tools:
            health = await self.check_health(tool_id)
            if health:
                results[tool_id] = health
        return results

    def get_status_summary(self) -> ToolStatusResponse:
        """Get summary of all tool statuses.

        Returns:
            Status summary.
        """
        definitions = list(self._definitions.values())
        total = len(definitions)
        healthy = sum(1 for d in definitions if d.health.status == ToolStatus.HEALTHY)
        offline = sum(1 for d in definitions if d.health.status == ToolStatus.OFFLINE)
        busy = sum(1 for d in definitions if d.health.status == ToolStatus.BUSY)
        error = sum(1 for d in definitions if d.health.status == ToolStatus.ERROR)

        by_provider = {}
        for d in definitions:
            provider = d.provider.value
            by_provider[provider] = by_provider.get(provider, 0) + 1

        return ToolStatusResponse(
            total_tools=total,
            healthy_tools=healthy,
            offline_tools=offline,
            busy_tools=busy,
            error_tools=error,
            tools_by_provider=by_provider,
        )

    def find_tools_for_operation(
        self,
        operation: str,
        required_permissions: list[str] | None = None,
    ) -> list[ToolDefinition]:
        """Find tools capable of performing an operation.

        Args:
            operation: Required operation.
            required_permissions: Required permissions.

        Returns:
            List of matching tool definitions.
        """
        matches = []

        for defn in self._definitions.values():
            if operation in defn.supported_operations:
                if defn.health.status == ToolStatus.HEALTHY:
                    matches.append(defn)

        return matches

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, tool_id: str) -> bool:
        return tool_id in self._tools
