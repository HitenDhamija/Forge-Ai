"""Docker MCP tool for container operations."""

import subprocess
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


class DockerTool(BaseTool):
    """Docker tool for container operations.

    Capabilities:
    - List Containers
    - List Images
    - Run Container
    - Stop Container
    - Exec in Container
    - Logs
    """

    def __init__(self):
        """Initialize Docker tool."""
        super().__init__(
            tool_id="docker",
            name="Docker",
            description="Docker container and image management",
            provider=ToolProvider.MCP,
            version="1.0.0",
            capabilities=[
                ToolCapability(
                    name="list_containers",
                    description="List running containers",
                    operations=["list"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="list_images",
                    description="List Docker images",
                    operations=["list"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="run_container",
                    description="Run a new container",
                    operations=["run"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="stop_container",
                    description="Stop a running container",
                    operations=["stop"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="exec_in_container",
                    description="Execute command in container",
                    operations=["exec"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="logs",
                    description="Get container logs",
                    operations=["logs"],
                    required_permissions=[],
                ),
            ],
            supported_operations=[
                "list",
                "run",
                "stop",
                "exec",
                "logs",
            ],
        )

    async def health_check(self) -> ToolHealth:
        """Check Docker tool health."""
        try:
            result = self._run_docker(["--version"])
            if result["success"]:
                return ToolHealth(
                    status=ToolStatus.HEALTHY,
                    latency_ms=0.0,
                    version=self.version,
                )
            return ToolHealth(
                status=ToolStatus.ERROR,
                error_message="Docker not available",
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
        """Validate Docker request."""
        base_valid, base_error = await super().validate(operation, parameters)
        if not base_valid:
            return base_valid, base_error

        if operation == "run" and "image" not in parameters:
            return False, "Missing required parameter: image"

        if operation == "stop" and "container_id" not in parameters:
            return False, "Missing required parameter: container_id"

        if operation == "exec" and ("container_id" not in parameters or "command" not in parameters):
            return False, "Missing required parameters: container_id, command"

        return True, None

    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Execute Docker operation."""
        self._active_requests[request_id] = True

        try:
            if operation == "list":
                return await self._list(parameters)
            elif operation == "run":
                return await self._run(parameters)
            elif operation == "stop":
                return await self._stop(parameters)
            elif operation == "exec":
                return await self._exec(parameters)
            elif operation == "logs":
                return await self._logs(parameters)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        finally:
            self._active_requests.pop(request_id, None)

    async def _list(self, params: dict[str, Any]) -> dict[str, Any]:
        """List containers or images."""
        target = params.get("target", "containers")
        if target == "images":
            result = self._run_docker(["images", "--format", "{{.Repository}}:{{.Tag}}"])
        else:
            result = self._run_docker(["ps", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}"])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _run(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run a container."""
        image = params["image"]
        name = params.get("name")
        detach = params.get("detach", True)

        cmd = ["run"]
        if detach:
            cmd.append("-d")
        if name:
            cmd.extend(["--name", name])

        cmd.append(image)
        result = self._run_docker(cmd)
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _stop(self, params: dict[str, Any]) -> dict[str, Any]:
        """Stop a container."""
        container_id = params["container_id"]
        result = self._run_docker(["stop", container_id])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _exec(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute command in container."""
        container_id = params["container_id"]
        command = params["command"]
        result = self._run_docker(["exec", container_id, "sh", "-c", command])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _logs(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get container logs."""
        container_id = params["container_id"]
        tail = params.get("tail", 100)
        result = self._run_docker(["logs", "--tail", str(tail), container_id])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    def _run_docker(self, args: list[str]) -> dict[str, Any]:
        """Run a docker command."""
        try:
            result = subprocess.run(
                ["docker"] + args,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Docker command timed out"}
        except FileNotFoundError:
            return {"success": False, "error": "Docker not installed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
