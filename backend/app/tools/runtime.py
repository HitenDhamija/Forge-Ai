"""Tool Runtime for orchestrating tool execution."""

import uuid
from datetime import datetime
from typing import Any

from app.tools.schemas import (
    ToolResult,
    ToolStatus,
    ToolType,
)
from app.tools.registry import ToolRegistry
from app.tools.permissions import PermissionEngine
from app.tools.events import ToolEventEmitter, ToolEventType
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolRuntime:
    """Orchestrates tool execution with permissions and events."""

    def __init__(
        self,
        registry: ToolRegistry,
        permission_engine: PermissionEngine,
        event_emitter: ToolEventEmitter,
    ):
        """Initialize tool runtime."""
        self.registry = registry
        self.permission_engine = permission_engine
        self.event_emitter = event_emitter
        self._executions: dict[str, ToolResult] = {}

    async def execute(
        self,
        agent_id: str,
        tool_id: str,
        operation: str,
        parameters: dict[str, Any],
        request_id: str | None = None,
    ) -> ToolResult:
        """Execute a tool operation."""
        execution_id = request_id or str(uuid.uuid4())
        start_time = datetime.utcnow()

        # Get tool
        tool = self.registry.get_tool(tool_id)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_id}",
                tool_id=tool_id,
                execution_id=execution_id,
                duration_ms=0,
            )

        # Check permissions
        permitted, reason = await self.permission_engine.check_tool_permission(
            agent_id, tool_id, operation, parameters
        )
        if not permitted:
            self.event_emitter.emit(
                ToolEventType.PERMISSION_DENIED,
                tool_id=tool_id,
                execution_id=execution_id,
                data={"reason": reason},
            )
            return ToolResult(
                success=False,
                error=f"Permission denied: {reason}",
                tool_id=tool_id,
                execution_id=execution_id,
                duration_ms=0,
            )

        # Validate
        valid, error = await tool.validate(operation, parameters)
        if not valid:
            self.event_emitter.emit(
                ToolEventType.ERROR,
                tool_id=tool_id,
                execution_id=execution_id,
                data={"error": error},
            )
            return ToolResult(
                success=False,
                error=error,
                tool_id=tool_id,
                execution_id=execution_id,
                duration_ms=0,
            )

        # Execute
        try:
            result = await tool.execute(operation, parameters, execution_id)
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            tool_result = ToolResult(
                success=result.get("success", False),
                data=result,
                error=result.get("error"),
                tool_id=tool_id,
                execution_id=execution_id,
                duration_ms=duration_ms,
            )

            # Emit events
            event_type = (
                ToolEventType.EXECUTE_SUCCESS
                if tool_result.success
                else ToolEventType.EXECUTE_ERROR
            )
            self.event_emitter.emit(
                event_type,
                tool_id=tool_id,
                execution_id=execution_id,
                data=result,
            )

            self._executions[execution_id] = tool_result
            return tool_result

        except Exception as e:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.event_emitter.emit(
                ToolEventType.ERROR,
                tool_id=tool_id,
                execution_id=execution_id,
                data={"error": str(e)},
            )
            return ToolResult(
                success=False,
                error=str(e),
                tool_id=tool_id,
                execution_id=execution_id,
                duration_ms=duration_ms,
            )

    async def cancel(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        result = self._executions.get(execution_id)
        if not result:
            return False

        tool = self.registry.get_tool(result.tool_id)
        if tool:
            await tool.cancel(execution_id)
            self.event_emitter.emit(
                ToolEventType.CANCEL,
                tool_id=result.tool_id,
                execution_id=execution_id,
            )
            return True
        return False

    def get_execution(self, execution_id: str) -> ToolResult | None:
        """Get execution result."""
        return self._executions.get(execution_id)

    def list_executions(self) -> list[ToolResult]:
        """List all executions."""
        return list(self._executions.values())

    async def cleanup(self) -> None:
        """Clean up runtime."""
        self._executions.clear()
        await self.registry.cleanup()
