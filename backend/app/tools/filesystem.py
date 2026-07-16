"""Filesystem MCP tool for file operations."""

import os
from pathlib import Path
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


class FilesystemTool(BaseTool):
    """Filesystem tool for file operations.

    Capabilities:
    - Read File
    - Write File
    - List Directory
    - Search Files
    - Move File
    - Delete File
    """

    def __init__(self, base_path: str = "."):
        """Initialize filesystem tool.

        Args:
            base_path: Base path for file operations.
        """
        super().__init__(
            tool_id="filesystem",
            name="Filesystem",
            description="File system operations including read, write, list, search, move, and delete",
            provider=ToolProvider.MCP,
            version="1.0.0",
            capabilities=[
                ToolCapability(
                    name="read_file",
                    description="Read file contents",
                    operations=["read"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="write_file",
                    description="Write content to file",
                    operations=["write"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="list_directory",
                    description="List directory contents",
                    operations=["read"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="search_files",
                    description="Search for files by pattern",
                    operations=["read"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="move_file",
                    description="Move or rename a file",
                    operations=["write"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="delete_file",
                    description="Delete a file",
                    operations=["write"],
                    required_permissions=[],
                ),
            ],
            supported_operations=[
                "read",
                "write",
                "list",
                "search",
                "move",
                "delete",
            ],
        )
        self.base_path = Path(base_path).resolve()

    async def initialize(self) -> None:
        """Initialize the filesystem tool."""
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)
        await super().initialize()

    async def health_check(self) -> ToolHealth:
        """Check filesystem tool health."""
        try:
            test_path = self.base_path / ".health_check"
            test_path.write_text("ok")
            test_path.unlink()
            return ToolHealth(
                status=ToolStatus.HEALTHY,
                latency_ms=0.0,
                version=self.version,
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
        """Validate filesystem request."""
        base_valid, base_error = await super().validate(operation, parameters)
        if not base_valid:
            return base_valid, base_error

        if operation == "read" and "path" not in parameters:
            return False, "Missing required parameter: path"

        if operation == "write" and ("path" not in parameters or "content" not in parameters):
            return False, "Missing required parameters: path, content"

        if operation == "list" and "path" not in parameters:
            return False, "Missing required parameter: path"

        if operation == "search" and "pattern" not in parameters:
            return False, "Missing required parameter: pattern"

        if operation == "move" and ("source" not in parameters or "destination" not in parameters):
            return False, "Missing required parameters: source, destination"

        if operation == "delete" and "path" not in parameters:
            return False, "Missing required parameter: path"

        return True, None

    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Execute filesystem operation."""
        self._active_requests[request_id] = True

        try:
            if operation == "read":
                return await self._read_file(parameters)
            elif operation == "write":
                return await self._write_file(parameters)
            elif operation == "list":
                return await self._list_directory(parameters)
            elif operation == "search":
                return await self._search_files(parameters)
            elif operation == "move":
                return await self._move_file(parameters)
            elif operation == "delete":
                return await self._delete_file(parameters)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        finally:
            self._active_requests.pop(request_id, None)

    async def _read_file(self, params: dict[str, Any]) -> dict[str, Any]:
        """Read file contents."""
        path = self._resolve_path(params["path"])
        try:
            content = path.read_text(encoding="utf-8")
            return {
                "success": True,
                "content": content,
                "size": len(content),
                "path": str(path),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _write_file(self, params: dict[str, Any]) -> dict[str, Any]:
        """Write content to file."""
        path = self._resolve_path(params["path"])
        content = params["content"]
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {
                "success": True,
                "path": str(path),
                "size": len(content),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _list_directory(self, params: dict[str, Any]) -> dict[str, Any]:
        """List directory contents."""
        path = self._resolve_path(params["path"])
        try:
            items = []
            for item in sorted(path.iterdir()):
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                })
            return {
                "success": True,
                "items": items,
                "path": str(path),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _search_files(self, params: dict[str, Any]) -> dict[str, Any]:
        """Search for files by pattern."""
        pattern = params["pattern"]
        directory = self._resolve_path(params.get("directory", "."))
        try:
            matches = list(directory.glob(pattern))
            return {
                "success": True,
                "matches": [str(m) for m in matches],
                "count": len(matches),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _move_file(self, params: dict[str, Any]) -> dict[str, Any]:
        """Move or rename a file."""
        source = self._resolve_path(params["source"])
        destination = self._resolve_path(params["destination"])
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
            return {
                "success": True,
                "source": str(source),
                "destination": str(destination),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _delete_file(self, params: dict[str, Any]) -> dict[str, Any]:
        """Delete a file."""
        path = self._resolve_path(params["path"])
        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
            return {
                "success": True,
                "path": str(path),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to base path."""
        return (self.base_path / path).resolve()
