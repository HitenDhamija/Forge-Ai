"""Registry for managing available agent types."""

from typing import Any

from app.agents.agent_base import AgentBase
from app.agents.exceptions import AgentNotFoundError
from app.agents.schemas import AgentType
from app.agents.tools.registry import ToolRegistry
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentRegistry:
    """Registry for managing agent types and creating agent instances.

    Provides centralized agent management and factory methods for
    creating new agent instances.
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        """Initialize the agent registry.

        Args:
            tool_registry: Registry of available tools.
        """
        self.tool_registry = tool_registry
        self._agent_types: dict[AgentType, type[AgentBase]] = {}
        self._agents: dict[str, AgentBase] = {}

    def register_agent_type(
        self,
        agent_type: AgentType,
        agent_class: type[AgentBase],
    ) -> None:
        """Register an agent type.

        Args:
            agent_type: Type identifier for this agent.
            agent_class: Class to instantiate for this agent type.
        """
        self._agent_types[agent_type] = agent_class
        logger.info(
            "Agent type registered: %s -> %s",
            agent_type.value,
            agent_class.__name__,
        )

    def create_agent(
        self,
        agent_type: AgentType,
        **kwargs: Any,
    ) -> AgentBase:
        """Create a new agent instance.

        Args:
            agent_type: Type of agent to create.
            **kwargs: Additional arguments to pass to the agent constructor.

        Returns:
            New agent instance.

        Raises:
            AgentNotFoundError: If the agent type is not registered.
        """
        if agent_type not in self._agent_types:
            raise AgentNotFoundError(agent_type.value)

        agent_class = self._agent_types[agent_type]
        agent = agent_class(tool_registry=self.tool_registry, **kwargs)

        self._agents[agent.id] = agent

        logger.info(
            "Agent created: %s (%s)",
            agent.name,
            agent.id,
        )

        return agent

    def get_agent(self, agent_id: str) -> AgentBase:
        """Get an agent by ID.

        Args:
            agent_id: ID of the agent to retrieve.

        Returns:
            The requested agent.

        Raises:
            AgentNotFoundError: If the agent is not found.
        """
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id)
        return self._agents[agent_id]

    def list_agents(self) -> list[AgentBase]:
        """List all created agent instances.

        Returns:
            List of agent instances.
        """
        return list(self._agents.values())

    def get_available_types(self) -> list[AgentType]:
        """Get list of available agent types.

        Returns:
            List of registered agent types.
        """
        return list(self._agent_types.keys())

    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the registry.

        Args:
            agent_id: ID of the agent to remove.
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info("Agent removed: %s", agent_id)
