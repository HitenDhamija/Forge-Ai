"""Tool interface and base classes for the Tool Virtualization Layer."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.tools.schemas import (
    ToolCapability,
    ToolHealth,
    ToolProvider,
    ToolStatus,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolInterface(ABC):
    """Abstract interface that all tools must implement.

    Every tool must implement:
    - initialize(): Set up the tool
    - health_check(): Check tool health
    - validate(): Validate request parameters
    - execute(): Execute the tool operation
    - cancel(): Cancel ongoing execution
    - cleanup(): Clean up resources
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the tool.

        Called once when the tool is registered.
        """
        pass

    @abstractmethod
    async def health_check(self) -> ToolHealth:
        """Check tool health.

        Returns:
            Current health status.
        """
        pass

    @abstractmethod
    async def validate(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate request parameters.

        Args:
            operation: Operation to perform.
            parameters: Operation parameters.

        Returns:
            Tuple of (is_valid, error_message).
        """
        pass

    @abstractmethod
    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Execute a tool operation.

        Args:
            operation: Operation to perform.
            parameters: Operation parameters.
            request_id: Request ID for tracking.

        Returns:
            Execution result.
        """
        pass

    @abstractmethod
    async def cancel(self, request_id: str) -> bool:
        """Cancel an ongoing execution.

        Args:
            request_id: Request ID to cancel.

        Returns:
            True if cancelled successfully.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up tool resources.

        Called when the tool is unregistered.
        """
        pass


class BaseTool(ToolInterface):
    """Base implementation for tools with common functionality."""

    def __init__(
        self,
        tool_id: str,
        name: str,
        description: str,
        provider: ToolProvider,
        version: str,
        capabilities: list[ToolCapability],
        supported_operations: list[str],
    ):
        """Initialize the base tool.

        Args:
            tool_id: Unique tool identifier.
            name: Human-readable tool name.
            description: Tool description.
            provider: Tool provider.
            version: Tool version.
            capabilities: Tool capabilities.
            supported_operations: Supported operations.
        """
        self.tool_id = tool_id
        self.name = name
        self.description = description
        self.provider = provider
        self.version = version
        self.capabilities = capabilities
        self.supported_operations = supported_operations

        self._initialized = False
        self._active_requests: dict[str, bool] = {}
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = self._created_at

    async def initialize(self) -> None:
        """Initialize the tool."""
        self._initialized = True
        self._updated_at = datetime.now(timezone.utc)
        logger.info("Tool initialized: %s", self.name)

    async def health_check(self) -> ToolHealth:
        """Check tool health.

        Returns:
            Health status.
        """
        if not self._initialized:
            return ToolHealth(
                status=ToolStatus.OFFLINE,
                error_message="Tool not initialized",
            )

        return ToolHealth(
            status=ToolStatus.HEALTHY,
            latency_ms=0.0,
            last_check=datetime.now(timezone.utc),
            version=self.version,
        )

    async def validate(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate request parameters.

        Args:
            operation: Operation to perform.
            parameters: Operation parameters.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if operation not in self.supported_operations:
            return False, f"Unsupported operation: {operation}"

        return True, None

    async def cancel(self, request_id: str) -> bool:
        """Cancel an ongoing execution.

        Args:
            request_id: Request ID to cancel.

        Returns:
            True if cancelled successfully.
        """
        if request_id in self._active_requests:
            self._active_requests[request_id] = False
            logger.info("Request cancelled: %s", request_id)
            return True
        return False

    async def cleanup(self) -> None:
        """Clean up tool resources."""
        self._initialized = False
        self._active_requests.clear()
        self._updated_at = datetime.now(timezone.utc)
        logger.info("Tool cleaned up: %s", self.name)

    def is_initialized(self) -> bool:
        """Check if tool is initialized."""
        return self._initialized

    def get_definition(self) -> dict[str, Any]:
        """Get tool definition."""
        return {
            "id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "provider": self.provider.value,
            "version": self.version,
            "capabilities": [cap.model_dump() for cap in self.capabilities],
            "supported_operations": self.supported_operations,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
        }
