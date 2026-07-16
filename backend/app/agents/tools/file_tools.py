"""File system tools for agents."""

import os
from pathlib import Path
from typing import Any

from app.agents.config import get_agent_settings
from app.agents.schemas import ToolType
from app.agents.tools.base import ToolBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReadFileTool(ToolBase):
    """Tool for reading file contents."""

    def __init__(self) -> None:
        super().__init__(
            name="read_file",
            description="Read the contents of a file at the specified path",
            tool_type=ToolType.FILE,
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
            },
        )
        self.settings = get_agent_settings()

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate read file parameters."""
        if "file_path" not in kwargs:
            return False

        file_path = kwargs["file_path"]
        if not isinstance(file_path, str) or not file_path:
            return False

        path = Path(file_path)
        if path.suffix not in self.settings.ALLOWED_FILE_EXTENSIONS:
            return False

        return True

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Read file contents."""
        file_path = kwargs["file_path"]
        encoding = kwargs.get("encoding", "utf-8")

        path = Path(file_path)

        for blocked in self.settings.BLOCKED_DIRECTORIES:
            if blocked in path.parts:
                return {
                    "success": False,
                    "error": f"Access denied: {blocked} directory is blocked",
                }

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        if not path.is_file():
            return {
                "success": False,
                "error": f"Not a file: {file_path}",
            }

        try:
            content = path.read_text(encoding=encoding)
            return {
                "success": True,
                "content": content,
                "file_path": str(path.absolute()),
                "size": len(content),
                "lines": content.count("\n") + 1,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read file: {str(e)}",
            }


class WriteFileTool(ToolBase):
    """Tool for writing file contents."""

    def __init__(self) -> None:
        super().__init__(
            name="write_file",
            description="Write content to a file at the specified path",
            tool_type=ToolType.FILE,
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
            },
        )
        self.settings = get_agent_settings()

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate write file parameters."""
        if "file_path" not in kwargs or "content" not in kwargs:
            return False

        file_path = kwargs["file_path"]
        content = kwargs["content"]

        if not isinstance(file_path, str) or not file_path:
            return False

        if not isinstance(content, str):
            return False

        path = Path(file_path)
        if path.suffix not in self.settings.ALLOWED_FILE_EXTENSIONS:
            return False

        return True

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Write content to a file."""
        if not self.settings.ENABLE_FILE_MODIFICATION:
            return {
                "success": False,
                "error": "File modification is disabled in agent settings",
            }

        file_path = kwargs["file_path"]
        content = kwargs["content"]
        encoding = kwargs.get("encoding", "utf-8")

        path = Path(file_path)

        for blocked in self.settings.BLOCKED_DIRECTORIES:
            if blocked in path.parts:
                return {
                    "success": False,
                    "error": f"Access denied: {blocked} directory is blocked",
                }

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)
            return {
                "success": True,
                "file_path": str(path.absolute()),
                "size": len(content),
                "lines": content.count("\n") + 1,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write file: {str(e)}",
            }


class EditFileTool(ToolBase):
    """Tool for editing specific parts of a file."""

    def __init__(self) -> None:
        super().__init__(
            name="edit_file",
            description="Edit a specific part of a file by replacing content",
            tool_type=ToolType.FILE,
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit",
                },
                "old_content": {
                    "type": "string",
                    "description": "Content to find and replace",
                },
                "new_content": {
                    "type": "string",
                    "description": "Content to replace with",
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8",
                },
            },
        )
        self.settings = get_agent_settings()

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate edit file parameters."""
        required = ["file_path", "old_content", "new_content"]
        if not all(k in kwargs for k in required):
            return False

        file_path = kwargs["file_path"]
        if not isinstance(file_path, str) or not file_path:
            return False

        path = Path(file_path)
        if path.suffix not in self.settings.ALLOWED_FILE_EXTENSIONS:
            return False

        return True

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Edit file by replacing content."""
        if not self.settings.ENABLE_FILE_MODIFICATION:
            return {
                "success": False,
                "error": "File modification is disabled in agent settings",
            }

        file_path = kwargs["file_path"]
        old_content = kwargs["old_content"]
        new_content = kwargs["new_content"]
        encoding = kwargs.get("encoding", "utf-8")

        path = Path(file_path)

        for blocked in self.settings.BLOCKED_DIRECTORIES:
            if blocked in path.parts:
                return {
                    "success": False,
                    "error": f"Access denied: {blocked} directory is blocked",
                }

        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}",
            }

        try:
            content = path.read_text(encoding=encoding)

            if old_content not in content:
                return {
                    "success": False,
                    "error": "Old content not found in file",
                }

            occurrences = content.count(old_content)
            if occurrences > 1:
                return {
                    "success": False,
                    "error": f"Multiple occurrences ({occurrences}) of old content found. Provide more context to make it unique.",
                }

            new_file_content = content.replace(old_content, new_content)
            path.write_text(new_file_content, encoding=encoding)

            return {
                "success": True,
                "file_path": str(path.absolute()),
                "replacements": 1,
                "size": len(new_file_content),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to edit file: {str(e)}",
            }


class ListDirectoryTool(ToolBase):
    """Tool for listing directory contents."""

    def __init__(self) -> None:
        super().__init__(
            name="list_directory",
            description="List the contents of a directory",
            tool_type=ToolType.FILE,
            parameters={
                "directory_path": {
                    "type": "string",
                    "description": "Path to the directory to list",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively (default: false)",
                    "default": False,
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth for recursive listing (default: 2)",
                    "default": 2,
                },
            },
        )
        self.settings = get_agent_settings()

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate list directory parameters."""
        if "directory_path" not in kwargs:
            return False

        directory_path = kwargs["directory_path"]
        if not isinstance(directory_path, str) or not directory_path:
            return False

        return True

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """List directory contents."""
        directory_path = kwargs["directory_path"]
        recursive = kwargs.get("recursive", False)
        max_depth = kwargs.get("max_depth", 2)

        path = Path(directory_path)

        for blocked in self.settings.BLOCKED_DIRECTORIES:
            if blocked in path.parts:
                return {
                    "success": False,
                    "error": f"Access denied: {blocked} directory is blocked",
                }

        if not path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory_path}",
            }

        if not path.is_dir():
            return {
                "success": False,
                "error": f"Not a directory: {directory_path}",
            }

        try:
            items = []

            if recursive:
                for root, dirs, files in os.walk(path):
                    current_depth = len(Path(root).relative_to(path).parts)
                    if current_depth >= max_depth:
                        dirs.clear()
                        continue

                    rel_root = Path(root).relative_to(path)
                    for d in dirs:
                        if d not in self.settings.BLOCKED_DIRECTORIES:
                            items.append({
                                "path": str(rel_root / d),
                                "type": "directory",
                            })
                    for f in files:
                        items.append({
                            "path": str(rel_root / f),
                            "type": "file",
                        })
            else:
                for item in sorted(path.iterdir()):
                    if item.name in self.settings.BLOCKED_DIRECTORIES:
                        continue
                    items.append({
                        "path": item.name,
                        "type": "directory" if item.is_dir() else "file",
                    })

            return {
                "success": True,
                "items": items,
                "total": len(items),
                "directory": str(path.absolute()),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list directory: {str(e)}",
            }
