"""Git MCP tool for version control operations."""

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


class GitTool(BaseTool):
    """Git tool for version control operations.

    Capabilities:
    - Status
    - Branch
    - Commit
    - Diff
    - History
    - Checkout
    """

    def __init__(self, repo_path: str = "."):
        """Initialize git tool.

        Args:
            repo_path: Path to git repository.
        """
        super().__init__(
            tool_id="git",
            name="Git",
            description="Git version control operations",
            provider=ToolProvider.MCP,
            version="1.0.0",
            capabilities=[
                ToolCapability(
                    name="status",
                    description="Get repository status",
                    operations=["status"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="branch",
                    description="List or create branches",
                    operations=["branch"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="commit",
                    description="Commit changes",
                    operations=["commit"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="diff",
                    description="Show differences",
                    operations=["diff"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="history",
                    description="Show commit history",
                    operations=["log"],
                    required_permissions=[],
                ),
                ToolCapability(
                    name="checkout",
                    description="Checkout branch or commit",
                    operations=["checkout"],
                    required_permissions=[],
                ),
            ],
            supported_operations=[
                "status",
                "branch",
                "commit",
                "diff",
                "log",
                "checkout",
            ],
        )
        self.repo_path = repo_path

    async def health_check(self) -> ToolHealth:
        """Check git tool health."""
        try:
            result = self._run_git(["--version"])
            if result["success"]:
                return ToolHealth(
                    status=ToolStatus.HEALTHY,
                    latency_ms=0.0,
                    version=self.version,
                )
            return ToolHealth(
                status=ToolStatus.ERROR,
                error_message="Git not available",
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
        """Validate git request."""
        base_valid, base_error = await super().validate(operation, parameters)
        if not base_valid:
            return base_valid, base_error

        if operation == "commit" and "message" not in parameters:
            return False, "Missing required parameter: message"

        if operation == "checkout" and "target" not in parameters:
            return False, "Missing required parameter: target"

        return True, None

    async def execute(
        self,
        operation: str,
        parameters: dict[str, Any],
        request_id: str,
    ) -> dict[str, Any]:
        """Execute git operation."""
        self._active_requests[request_id] = True

        try:
            if operation == "status":
                return await self._get_status()
            elif operation == "branch":
                return await self._branch(parameters)
            elif operation == "commit":
                return await self._commit(parameters)
            elif operation == "diff":
                return await self._diff(parameters)
            elif operation == "log":
                return await self._log(parameters)
            elif operation == "checkout":
                return await self._checkout(parameters)
            else:
                return {"success": False, "error": f"Unknown operation: {operation}"}
        finally:
            self._active_requests.pop(request_id, None)

    async def _get_status(self) -> dict[str, Any]:
        """Get repository status."""
        result = self._run_git(["status", "--porcelain"])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _branch(self, params: dict[str, Any]) -> dict[str, Any]:
        """List or create branches."""
        branch_name = params.get("name")
        if branch_name:
            result = self._run_git(["branch", branch_name])
        else:
            result = self._run_git(["branch"])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _commit(self, params: dict[str, Any]) -> dict[str, Any]:
        """Commit changes."""
        message = params["message"]
        self._run_git(["add", "."])
        result = self._run_git(["commit", "-m", message])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _diff(self, params: dict[str, Any]) -> dict[str, Any]:
        """Show differences."""
        target = params.get("target")
        if target:
            result = self._run_git(["diff", target])
        else:
            result = self._run_git(["diff"])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _log(self, params: dict[str, Any]) -> dict[str, Any]:
        """Show commit history."""
        count = params.get("count", 10)
        result = self._run_git(["log", f"--oneline", f"-{count}"])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    async def _checkout(self, params: dict[str, Any]) -> dict[str, Any]:
        """Checkout branch or commit."""
        target = params["target"]
        result = self._run_git(["checkout", target])
        return {
            "success": result["success"],
            "output": result.get("output", ""),
            "error": result.get("error"),
        }

    def _run_git(self, args: list[str]) -> dict[str, Any]:
        """Run a git command."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
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
            return {"success": False, "error": "Git command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
