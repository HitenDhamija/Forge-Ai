"""Search tools for agents."""

import os
import re
from pathlib import Path
from typing import Any

from app.agents.config import get_agent_settings
from app.agents.schemas import ToolType
from app.agents.tools.base import ToolBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class GrepSearchTool(ToolBase):
    """Tool for searching file contents using regex patterns."""

    def __init__(self) -> None:
        super().__init__(
            name="grep_search",
            description="Search for patterns in file contents using regex",
            tool_type=ToolType.SEARCH,
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for",
                },
                "directory": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)",
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern for files to search (e.g., '*.py')",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 50)",
                    "default": 50,
                },
            },
        )
        self.settings = get_agent_settings()

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate grep search parameters."""
        if "pattern" not in kwargs:
            return False
        return isinstance(kwargs["pattern"], str) and len(kwargs["pattern"]) > 0

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Search file contents for pattern."""
        pattern = kwargs["pattern"]
        directory = kwargs.get("directory", ".")
        file_pattern = kwargs.get("file_pattern")
        max_results = kwargs.get("max_results", 50)

        search_path = Path(directory)

        for blocked in self.settings.BLOCKED_DIRECTORIES:
            if blocked in search_path.parts:
                return {
                    "success": False,
                    "error": f"Access denied: {blocked} directory is blocked",
                }

        if not search_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}",
            }

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return {
                "success": False,
                "error": f"Invalid regex pattern: {str(e)}",
            }

        results = []
        files_searched = 0

        try:
            for root, dirs, files in os.walk(search_path):
                dirs[:] = [
                    d for d in dirs
                    if d not in self.settings.BLOCKED_DIRECTORIES
                ]

                for file in files:
                    if file_pattern and not Path(file).match(file_pattern):
                        continue

                    if Path(file).suffix not in self.settings.ALLOWED_FILE_EXTENSIONS:
                        continue

                    file_path = Path(root) / file
                    files_searched += 1

                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        lines = content.split("\n")

                        for i, line in enumerate(lines, 1):
                            if regex.search(line):
                                results.append({
                                    "file": str(file_path.relative_to(search_path)),
                                    "line_number": i,
                                    "line": line.strip(),
                                    "match": regex.search(line).group() if regex.search(line) else "",
                                })

                                if len(results) >= max_results:
                                    return {
                                        "success": True,
                                        "results": results,
                                        "total_matches": len(results),
                                        "files_searched": files_searched,
                                        "truncated": True,
                                    }
                    except Exception:
                        continue

            return {
                "success": True,
                "results": results,
                "total_matches": len(results),
                "files_searched": files_searched,
                "truncated": False,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
            }


class FindFilesTool(ToolBase):
    """Tool for finding files by name pattern."""

    def __init__(self) -> None:
        super().__init__(
            name="find_files",
            description="Find files matching a name pattern",
            tool_type=ToolType.SEARCH,
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '*.py', 'src/**/*.ts')",
                },
                "directory": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 100)",
                    "default": 100,
                },
            },
        )
        self.settings = get_agent_settings()

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate find files parameters."""
        if "pattern" not in kwargs:
            return False
        return isinstance(kwargs["pattern"], str) and len(kwargs["pattern"]) > 0

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Find files matching pattern."""
        pattern = kwargs["pattern"]
        directory = kwargs.get("directory", ".")
        max_results = kwargs.get("max_results", 100)

        search_path = Path(directory)

        for blocked in self.settings.BLOCKED_DIRECTORIES:
            if blocked in search_path.parts:
                return {
                    "success": False,
                    "error": f"Access denied: {blocked} directory is blocked",
                }

        if not search_path.exists():
            return {
                "success": False,
                "error": f"Directory not found: {directory}",
            }

        try:
            matches = list(search_path.glob(pattern))
            filtered = []

            for match in matches:
                if len(filtered) >= max_results:
                    break

                parts = match.relative_to(search_path).parts
                if any(p in self.settings.BLOCKED_DIRECTORIES for p in parts):
                    continue

                filtered.append({
                    "path": str(match.relative_to(search_path)),
                    "type": "directory" if match.is_dir() else "file",
                    "size": match.stat().st_size if match.is_file() else None,
                })

            return {
                "success": True,
                "results": filtered,
                "total": len(filtered),
                "truncated": len(matches) > max_results,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Find failed: {str(e)}",
            }
