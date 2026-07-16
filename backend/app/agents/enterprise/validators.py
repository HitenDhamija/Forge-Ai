"""Agent validation system for capability and context checking."""

from typing import Any

from app.agents.enterprise.schemas import AgentInfo, AgentStatus, Capability
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentValidator:
    """Validates agents before accepting work.

    Before accepting work, an agent validates:
    - Capability: Does the agent have the required capabilities?
    - Required Context: Is the necessary context available?
    - Dependencies: Are dependencies satisfied?
    - Repository Availability: Is the repository accessible?
    """

    def __init__(self):
        """Initialize the validator."""
        pass

    def validate_capability(
        self,
        agent: AgentInfo,
        required_capabilities: list[str],
    ) -> tuple[bool, str | None]:
        """Validate agent has required capabilities.

        Args:
            agent: Agent information.
            required_capabilities: Required capability names.

        Returns:
            Tuple of (is_valid, error_message).
        """
        agent_capabilities = {cap.name for cap in agent.capabilities}

        for required in required_capabilities:
            if required not in agent_capabilities:
                return False, f"Missing required capability: {required}"

        return True, None

    def validate_context(
        self,
        agent: AgentInfo,
        required_context: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Validate agent has required context.

        Args:
            agent: Agent information.
            required_context: Required context keys.

        Returns:
            Tuple of (is_valid, error_message).
        """
        agent_context = agent.memory.execution_context

        for key in required_context:
            if key not in agent_context:
                return False, f"Missing required context: {key}"

        return True, None

    def validate_dependencies(
        self,
        agent: AgentInfo,
        completed_dependencies: list[str],
        required_dependencies: list[str],
    ) -> tuple[bool, str | None]:
        """Validate task dependencies are satisfied.

        Args:
            agent: Agent information.
            completed_dependencies: List of completed dependency IDs.
            required_dependencies: List of required dependency IDs.

        Returns:
            Tuple of (is_valid, error_message).
        """
        completed_set = set(completed_dependencies)

        for dep in required_dependencies:
            if dep not in completed_set:
                return False, f"Dependency not satisfied: {dep}"

        return True, None

    def validate_availability(
        self,
        agent: AgentInfo,
        max_concurrent: int = 1,
    ) -> tuple[bool, str | None]:
        """Validate agent is available for work.

        Args:
            agent: Agent information.
            max_concurrent: Maximum concurrent tasks.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if agent.status in (AgentStatus.OFFLINE, AgentStatus.UNAVAILABLE):
            return False, "Agent is not available"

        if agent.status in (AgentStatus.ASSIGNED, AgentStatus.EXECUTING):
            return False, "Agent is busy"

        return True, None

    def validate_task_acceptance(
        self,
        agent: AgentInfo,
        task_requirements: dict[str, Any],
        completed_dependencies: list[str] | None = None,
    ) -> tuple[bool, str | None]:
        """Comprehensive validation for task acceptance.

        Args:
            agent: Agent information.
            task_requirements: Task requirements.
            completed_dependencies: Completed dependencies.

        Returns:
            Tuple of (is_valid, error_message).
        """
        required_capabilities = task_requirements.get("required_capabilities", [])
        if required_capabilities:
            valid, error = self.validate_capability(agent, required_capabilities)
            if not valid:
                return valid, error

        required_context = task_requirements.get("required_context", {})
        if required_context:
            valid, error = self.validate_context(agent, required_context)
            if not valid:
                return valid, error

        required_deps = task_requirements.get("dependencies", [])
        if required_deps and completed_dependencies is not None:
            valid, error = self.validate_dependencies(
                agent, completed_dependencies, required_deps
            )
            if not valid:
                return valid, error

        valid, error = self.validate_availability(agent)
        if not valid:
            return valid, error

        return True, None

    def get_capability_match_score(
        self,
        agent: AgentInfo,
        required_capabilities: list[str],
    ) -> float:
        """Calculate capability match score.

        Args:
            agent: Agent information.
            required_capabilities: Required capabilities.

        Returns:
            Match score between 0 and 1.
        """
        if not required_capabilities:
            return 1.0

        agent_caps = {cap.name: cap for cap in agent.capabilities}
        total_score = 0

        for required in required_capabilities:
            if required in agent_caps:
                total_score += agent_caps[required].level / 10
            else:
                return 0.0

        return total_score / len(required_capabilities)
