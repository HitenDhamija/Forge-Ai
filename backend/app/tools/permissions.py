"""Permission engine for tool execution validation."""

from typing import Any

from app.tools.schemas import (
    PermissionLevel,
    PermissionRequest,
    PermissionResult,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class PermissionEngine:
    """Permission engine for validating tool execution requests.

    Before execution, validates:
    - Agent: Is the agent authorized?
    - Tool: Is the tool allowed?
    - Operation: Is the operation permitted?
    - Project: Is the project accessible?
    - Repository: Is the repository accessible?
    - Approval Level: Is the required approval level met?
    """

    def __init__(self):
        """Initialize the permission engine."""
        self._agent_permissions: dict[str, dict[str, PermissionLevel]] = {}
        self._tool_permissions: dict[str, PermissionLevel] = {}
        self._project_access: dict[str, list[str]] = {}
        self._repository_access: dict[str, list[str]] = {}

    def set_agent_permission(
        self,
        agent_id: str,
        tool_id: str,
        level: PermissionLevel,
    ) -> None:
        """Set agent permission for a tool.

        Args:
            agent_id: Agent ID.
            tool_id: Tool ID.
            permission level.
        """
        if agent_id not in self._agent_permissions:
            self._agent_permissions[agent_id] = {}
        self._agent_permissions[agent_id][tool_id] = level
        logger.info(
            "Permission set: agent=%s tool=%s level=%s",
            agent_id,
            tool_id,
            level.value,
        )

    def set_tool_permission(self, tool_id: str, level: PermissionLevel) -> None:
        """Set default permission level for a tool.

        Args:
            tool_id: Tool ID.
            level: Permission level.
        """
        self._tool_permissions[tool_id] = level

    def set_project_access(self, project_id: str, agent_ids: list[str]) -> None:
        """Set project access for agents.

        Args:
            project_id: Project ID.
            agent_ids: List of authorized agent IDs.
        """
        self._project_access[project_id] = agent_ids

    def set_repository_access(self, repository_path: str, agent_ids: list[str]) -> None:
        """Set repository access for agents.

        Args:
            repository_path: Repository path.
            agent_ids: List of authorized agent IDs.
        """
        self._repository_access[repository_path] = agent_ids

    def validate(self, request: PermissionRequest) -> PermissionResult:
        """Validate a permission request.

        Args:
            request: Permission request.

        Returns:
            Permission result.
        """
        agent_id = request.agent_id
        tool_id = request.tool_id
        operation = request.operation

        agent_perms = self._agent_permissions.get(agent_id, {})
        agent_level = agent_perms.get(tool_id)

        if agent_level is None:
            tool_default = self._tool_permissions.get(tool_id, PermissionLevel.READ)
            agent_level = tool_default

        if not self._has_required_level(agent_level, request.required_level):
            return PermissionResult(
                allowed=False,
                reason=f"Insufficient permissions: has {agent_level.value}, requires {request.required_level.value}",
                granted_level=agent_level,
            )

        if request.project_id:
            if not self._can_access_project(agent_id, request.project_id):
                return PermissionResult(
                    allowed=False,
                    reason=f"Agent not authorized for project: {request.project_id}",
                    granted_level=agent_level,
                )

        if request.repository_path:
            if not self._can_access_repository(agent_id, request.repository_path):
                return PermissionResult(
                    allowed=False,
                    reason=f"Agent not authorized for repository: {request.repository_path}",
                    granted_level=agent_level,
                )

        logger.info(
            "Permission granted: agent=%s tool=%s operation=%s",
            agent_id,
            tool_id,
            operation,
        )

        return PermissionResult(
            allowed=True,
            granted_level=agent_level,
        )

    def _has_required_level(
        self,
        current: PermissionLevel,
        required: PermissionLevel,
    ) -> bool:
        """Check if current level meets required level.

        Args:
            current: Current permission level.
            required: Required permission level.

        Returns:
            True if current meets required.
        """
        level_hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4,
        }

        return level_hierarchy.get(current, 0) >= level_hierarchy.get(required, 0)

    def _can_access_project(self, agent_id: str, project_id: str) -> bool:
        """Check if agent can access a project.

        Args:
            agent_id: Agent ID.
            project_id: Project ID.

        Returns:
            True if access is allowed.
        """
        authorized_agents = self._project_access.get(project_id)
        if authorized_agents is None:
            return True
        return agent_id in authorized_agents

    def _can_access_repository(self, agent_id: str, repository_path: str) -> bool:
        """Check if agent can access a repository.

        Args:
            agent_id: Agent ID.
            repository_path: Repository path.

        Returns:
            True if access is allowed.
        """
        for path, authorized_agents in self._repository_access.items():
            if repository_path.startswith(path):
                if agent_id not in authorized_agents:
                    return False
        return True

    def get_agent_permissions(self, agent_id: str) -> dict[str, PermissionLevel]:
        """Get all permissions for an agent.

        Args:
            agent_id: Agent ID.

        Returns:
            Dictionary of tool IDs to permission levels.
        """
        return self._agent_permissions.get(agent_id, {}).copy()
