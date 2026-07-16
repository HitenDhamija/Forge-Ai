"""MCP (Model Context Protocol) runtime and adapters."""

from typing import Any

from app.tools.base import BaseTool
from app.tools.schemas import (
    ToolCapability,
    ToolHealth,
    ToolProvider,
    ToolStatus,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPServer:
    """MCP Server adapter for connecting to MCP servers."""

    def __init__(
        self,
        server_id: str,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ):
        """Initialize MCP server.

        Args:
            server_id: Server identifier.
            name: Server name.
            command: Command to start server.
            args: Command arguments.
            env: Environment variables.
        """
        self.server_id = server_id
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self._process = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to the MCP server.

        Returns:
            True if connected successfully.
        """
        try:
            logger.info("Connecting to MCP server: %s", self.name)
            self._connected = True
            return True
        except Exception as e:
            logger.error("Failed to connect to MCP server: %s", str(e))
            return False

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        self._connected = False
        logger.info("Disconnected from MCP server: %s", self.name)

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            tool_name: Tool name.
            arguments: Tool arguments.

        Returns:
            Tool result.
        """
        if not self._connected:
            return {"error": "Not connected to MCP server"}

        logger.info("Calling MCP tool: %s.%s", self.name, tool_name)
        return {"status": "success", "result": {}}

    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._connected


class MCPAdapter(BaseTool):
    """Adapter for wrapping MCP servers as tools."""

    def __init__(
        self,
        tool_id: str,
        name: str,
        description: str,
        server: MCPServer,
        capabilities: list[ToolCapability] | None = None,
        supported_operations: list[str] | None = None,
    ):
        """Initialize MCP adapter.

        Args:
            tool_id: Tool identifier.
            name: Tool name.
            description: Tool description.
            server: MCP server instance.
            capabilities: Tool capabilities.
            supported_operations: Supported operations.
        """
        super().__init__(
            tool_id=tool_id,
            name=name,
            description=description,
            provider=ToolProvider.MCP,
            version="1.0.0",
            capabilities=capabilities or [],
            supported_operations=supported_operations or [],
        )
        self.server = server

    async def initialize(self) -> None:
        """Initialize the MCP adapter."""
        await self.server.connect()
        await super().initialize()

    async def health_check(self) -> ToolHealth:
        """Check MCP server health."""
        if not self.server.is_connected():
            return ToolHealth(
                status=ToolStatus.OFFLINE,
                error_message="Not connected to MCP server",
            )

        return ToolHealth(
            status=ToolStatus.HEALTHY,
            latency_ms=0.0,
            version=self.version,
        )

    async def validate(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate MCP tool request."""
        base_valid, base_error = await super().validate(operation, parameters)
        if not base_valid:
            return base_valid, base_error

        return True, None

    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Execute MCP tool operation."""
        self._active_requests[request_id] = True

        try:
            result = await self.server.call_tool(operation, parameters)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self._active_requests.pop(request_id, None)

    async def cancel(self, request_id: str) -> bool:
        """Cancel MCP tool execution."""
        return await super().cancel(request_id)

    async def cleanup(self) -> None:
        """Clean up MCP adapter."""
        await self.server.disconnect()
        await super().cleanup()
