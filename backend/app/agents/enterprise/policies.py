"""Policy engine for agent task and tool permissions."""

from typing import Any

from app.agents.enterprise.schemas import Policy
from app.core.logging import get_logger

logger = get_logger(__name__)


class PolicyEngine:
    """Policy engine for enforcing agent constraints.

    Policies define:
    - Allowed Tasks: Tasks the agent can perform
    - Forbidden Tasks: Tasks the agent cannot perform
    - Tool Permissions: Tools the agent can use
    - Repository Access: Repositories the agent can access
    - Execution Limits: Maximum concurrent tasks, retries, timeout
    """

    def __init__(self):
        """Initialize the policy engine."""
        self._policies: dict[str, Policy] = {}

    def register_policy(self, agent_id: str, policy: Policy) -> None:
        """Register a policy for an agent.

        Args:
            agent_id: Agent ID.
            policy: Agent policy.
        """
        self._policies[agent_id] = policy
        logger.info("Policy registered for agent: %s", agent_id)

    def get_policy(self, agent_id: str) -> Policy | None:
        """Get policy for an agent.

        Args:
            agent_id: Agent ID.

        Returns:
            Agent policy or None.
        """
        return self._policies.get(agent_id)

    def can_perform_task(self, agent_id: str, task_type: str) -> bool:
        """Check if agent can perform a task.

        Args:
            agent_id: Agent ID.
            task_type: Task type to check.

        Returns:
            True if allowed.
        """
        policy = self.get_policy(agent_id)
        if not policy:
            return False

        if task_type in policy.forbidden_tasks:
            return False

        if policy.allowed_tasks and task_type not in policy.allowed_tasks:
            return False

        return True

    def can_use_tool(self, agent_id: str, tool_name: str) -> bool:
        """Check if agent can use a tool.

        Args:
            agent_id: Agent ID.
            tool_name: Tool name to check.

        Returns:
            True if allowed.
        """
        policy = self.get_policy(agent_id)
        if not policy:
            return False

        if tool_name in policy.forbidden_tools:
            return False

        if policy.allowed_tools and tool_name not in policy.allowed_tools:
            return False

        return True

    def can_access_repository(self, agent_id: str, repository_path: str) -> bool:
        """Check if agent can access a repository.

        Args:
            agent_id: Agent ID.
            repository_path: Repository path to check.

        Returns:
            True if allowed.
        """
        policy = self.get_policy(agent_id)
        if not policy:
            return False

        if not policy.repository_access:
            return True

        for allowed in policy.repository_access:
            if repository_path.startswith(allowed):
                return True

        return False

    def get_max_concurrent_tasks(self, agent_id: str) -> int:
        """Get maximum concurrent tasks for an agent.

        Args:
            agent_id: Agent ID.

        Returns:
            Maximum concurrent tasks.
        """
        policy = self.get_policy(agent_id)
        return policy.max_concurrent_tasks if policy else 1

    def get_max_retries(self, agent_id: str) -> int:
        """Get maximum retries for an agent.

        Args:
            agent_id: Agent ID.

        Returns:
            Maximum retries.
        """
        policy = self.get_policy(agent_id)
        return policy.max_retries if policy else 3

    def get_timeout(self, agent_id: str) -> int:
        """Get timeout for an agent.

        Args:
            agent_id: Agent ID.

        Returns:
            Timeout in seconds.
        """
        policy = self.get_policy(agent_id)
        return policy.timeout_seconds if policy else 300

    def validate_task_assignment(
        self, agent_id: str, task_type: str, required_tools: list[str] | None = None
    ) -> tuple[bool, str | None]:
        """Validate if agent can accept a task assignment.

        Args:
            agent_id: Agent ID.
            task_type: Task type.
            required_tools: Required tools for the task.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not self.can_perform_task(agent_id, task_type):
            return False, f"Agent not allowed to perform task type: {task_type}"

        if required_tools:
            for tool in required_tools:
                if not self.can_use_tool(agent_id, tool):
                    return False, f"Agent not allowed to use tool: {tool}"

        return True, None
