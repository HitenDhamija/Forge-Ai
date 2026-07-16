"""Terminal MCP tool for shell command execution."""

import subprocess
import asyncio
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


class TerminalTool(BaseTool):
    """Terminal tool for shell command execution.

    Capabilities:
    - Run Command
    - Cancel Command
    - Stream Output
    """

    def __init__(self, working_directory: str = "."):
        """Initialize terminal tool.

        Args:
            working_directory: Default working directory.
        """
        super().__init__(
            tool_id="terminal",
            name="Terminal",
            description="Execute shell commands with streaming output",
            provider=ToolProvider.MCP,
            version="1.0.0",
            capabilities=[
                ToolCapability(
                    name="run_command",
                    description="Execute a shell command",
                    operations=["execute"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="cancel_command",
                    description="Cancel a running command",
                    operations=["cancel"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="stream_output",
                    description="Stream command output",
                    operations=["stream"],
                    required_permissions=[],
                ),
            ],
            supported_operations=["execute", "cancel", "stream"],
        )
        self.working_directory = working_directory
        self._processes: dict[str, subprocess.Popen] = {}

    async def health_check(self) -> ToolHealth:
        """Check terminal tool health."""
        try:
            result = subprocess.run(
                ["echo", "ok"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return ToolHealth(
                    status=ToolStatus.HEALTHY,
                    latency_ms=0.0,
                    version=self.version,
                )
            return ToolHealth(
                status=ToolStatus.ERROR,
                error_message="Terminal not available",
            )
        except Exception as e:
            return ToolHealth(
                status=ToolStatus.ERROR,
                error_message=str(e),
            )

    async def validate(
        self,
        operation: str,
        parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate terminal request."""
        base_valid, base_error = await super().validate(operation, parameters)
        if not base_valid:
            return base_valid, base_error

        if operation == "execute" and "command" not in parameters:
            return False, "Missing required parameter: command"

        if operation == "cancel" and "process_id" not in parameters:
            return False, "Missing required parameter: process_id"

        return True, None

    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Execute terminal operation."""
        self._active_requests[request_id] = True

        try:
            if operation == "execute":
                return await self._run_command(parameters, request_id)
            elif operation == "cancel":
                return await self._cancel_command(parameters)
            elif operation == "stream":
                return await self._stream_output(parameters)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        finally:
            self._active_requests.pop(request_id, None)

    async def _run_command(
        self,
        params: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Run a shell command."""
        command = params["command"]
        timeout = params.get("timeout", 30)
        working_dir = params.get("working_directory", self.working_directory)

        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self._processes[request_id] = process

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return {
                    "success": process.returncode == 0,
                    "output": stdout,
                    "error": stderr if process.returncode != 0 else None,
                    "exit_code": process.returncode,
                }
            except subprocess.TimeoutExpired:
                process.kill()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout}s",
                }
            finally:
                self._processes.pop(request_id, None)

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _cancel_command(self, params: dict[str, Any]) -> dict[str, Any]:
        """Cancel a running command."""
        process_id = params["process_id"]
        process = self._processes.get(process_id)

        if process:
            try:
                process.kill()
                return {"success": True, "message": "Process cancelled"}
            except Exception as e:
                return {"success": False, "error": str(e)}
        else:
            return {"success": False, "error": "Process not found"}

    async def _stream_output(self, params: dict[str, Any]) -> dict[str, Any]:
        """Stream command output."""
        return {
            "success": True,
            "message": "Streaming not yet implemented",
        }

    async def cleanup(self) -> None:
        """Clean up terminal tool."""
        for process_id, process in self._processes.items():
            try:
                process.kill()
            except Exception:
                pass
        self._processes.clear()
        await super().cleanup()
