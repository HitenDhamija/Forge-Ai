"""Dynamic agent registry for discovering and managing agents."""

from datetime import datetime, timezone
from typing import Any

from app.agents.enterprise.schemas import (
    AgentInfo,
    AgentRole,
    AgentStatus,
    AgentStatusResponse,
    Capability,
    Policy,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentRegistry:
    """Dynamic registry for agent discovery and management.

    Every agent registers:
    - ID, Role, Description
    - Capabilities, Tools
    - Supported Tasks
    - Priority, Status, Version

    Supervisor discovers agents dynamically.
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: dict[str, AgentInfo] = {}
        self._agents_by_role: dict[AgentRole, list[str]] = {}

    def register(self, agent: AgentInfo) -> None:
        """Register an agent.

        Args:
            agent: Agent information.
        """
        self._agents[agent.id] = agent

        if agent.role not in self._agents_by_role:
            self._agents_by_role[agent.role] = []
        self._agents_by_role[agent.role].append(agent.id)

        logger.info(
            "Agent registered: %s (%s) - %s",
            agent.name,
            agent.id,
            agent.role.value,
        )

    def unregister(self, agent_id: str) -> None:
        """Unregister an agent.

        Args:
            agent_id: Agent ID.
        """
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            self._agents_by_role.get(agent.role, []).remove(agent_id)
            del self._agents[agent_id]
            logger.info("Agent unregistered: %s", agent_id)

    def get_agent(self, agent_id: str) -> AgentInfo | None:
        """Get agent by ID.

        Args:
            agent_id: Agent ID.

        Returns:
            Agent information or None.
        """
        return self._agents.get(agent_id)

    def get_agents_by_role(self, role: AgentRole) -> list[AgentInfo]:
        """Get all agents with a specific role.

        Args:
            role: Agent role.

        Returns:
            List of agents with the role.
        """
        agent_ids = self._agents_by_role.get(role, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def get_available_agents(self) -> list[AgentInfo]:
        """Get all available agents.

        Returns:
            List of available agents.
        """
        return [
            agent for agent in self._agents.values()
            if agent.status in (AgentStatus.IDLE, AgentStatus.WAITING)
        ]

    def get_agents_by_status(self, status: AgentStatus) -> list[AgentInfo]:
        """Get all agents with a specific status.

        Args:
            status: Agent status.

        Returns:
            List of agents with the status.
        """
        return [
            agent for agent in self._agents.values()
            if agent.status == status
        ]

    def find_agents_for_task(
        self,
        required_capabilities: list[str],
        task_type: str | None = None,
    ) -> list[AgentInfo]:
        """Find agents capable of performing a task.

        Args:
            required_capabilities: Required capabilities.
            task_type: Optional task type.

        Returns:
            List of capable agents, sorted by capability match.
        """
        candidates = []

        for agent in self._agents.values():
            if agent.status not in (AgentStatus.IDLE, AgentStatus.WAITING):
                continue

            agent_caps = {cap.name for cap in agent.capabilities}
            if all(cap in agent_caps for cap in required_capabilities):
                candidates.append(agent)

        def match_score(agent: AgentInfo) -> float:
            agent_caps = {cap.name: cap for cap in agent.capabilities}
            if not required_capabilities:
                return 1.0
            return sum(
                agent_caps[cap].level / 10
                for cap in required_capabilities
                if cap in agent_caps
            ) / len(required_capabilities)

        candidates.sort(key=match_score, reverse=True)
        return candidates

    def update_status(self, agent_id: str, status: AgentStatus) -> None:
        """Update agent status.

        Args:
            agent_id: Agent ID.
            status: New status.
        """
        if agent_id in self._agents:
            self._agents[agent_id].status = status
            self._agents[agent_id].updated_at = datetime.now(timezone.utc)
            logger.info("Agent %s status updated to %s", agent_id, status.value)

    def update_heartbeat(self, agent_id: str) -> None:
        """Update agent heartbeat.

        Args:
            agent_id: Agent ID.
        """
        if agent_id in self._agents:
            self._agents[agent_id].last_heartbeat = datetime.now(timezone.utc)
            self._agents[agent_id].updated_at = datetime.now(timezone.utc)

    def get_status_summary(self) -> AgentStatusResponse:
        """Get summary of all agent statuses.

        Returns:
            Agent status response.
        """
        agents = list(self._agents.values())
        total = len(agents)
        idle = sum(1 for a in agents if a.status == AgentStatus.IDLE)
        busy = sum(1 for a in agents if a.status in (
            AgentStatus.ASSIGNED, AgentStatus.EXECUTING, AgentStatus.PREPARING
        ))
        unavailable = sum(1 for a in agents if a.status in (
            AgentStatus.UNAVAILABLE, AgentStatus.OFFLINE, AgentStatus.FAILED
        ))

        by_role = {}
        for agent in agents:
            role = agent.role.value
            by_role[role] = by_role.get(role, 0) + 1

        return AgentStatusResponse(
            total_agents=total,
            idle_agents=idle,
            busy_agents=busy,
            unavailable_agents=unavailable,
            agents_by_role=by_role,
        )

    def list_all(self) -> list[AgentInfo]:
        """List all registered agents.

        Returns:
            List of all agents.
        """
        return list(self._agents.values())

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._agents
