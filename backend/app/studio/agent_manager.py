"""Agent management service for the Studio interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger
import uuid

logger = get_logger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    description: str
    prompt_template: str
    capabilities: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    policies: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPerformance:
    """Performance metrics for an agent."""

    tasks_completed: int
    tasks_failed: int
    avg_duration: float
    success_rate: float
    last_active: datetime | None = None


class AgentManagerService:
    """Service for managing agents in the Studio interface.

    Provides configuration, performance tracking, and testing
    capabilities for AI agents.
    """

    def __init__(self) -> None:
        self._agents: dict[str, dict[str, Any]] = {}
        self._configs: dict[str, AgentConfig] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}

    async def list_agents(self) -> list[dict[str, Any]]:
        """List all agents with their configurations.

        Returns:
            List of agent summary dictionaries.
        """
        agents = []
        for agent_id, agent_data in self._agents.items():
            config = self._configs.get(agent_id)
            agents.append({
                "id": agent_id,
                "name": config.name if config else "Unknown",
                "description": config.description if config else "",
                "capabilities": config.capabilities if config else [],
                "tools": config.tools if config else [],
                "status": agent_data.get("status", "idle"),
                "created_at": agent_data.get("created_at", datetime.now(UTC).isoformat()),
            })
        return agents

    async def get_agent(self, agent_id: str) -> dict[str, Any]:
        """Get detailed agent information.

        Args:
            agent_id: The agent identifier.

        Returns:
            Agent detail dictionary.

        Raises:
            ValueError: If agent is not found.
        """
        agent_data = self._agents.get(agent_id)
        if agent_data is None:
            raise ValueError(f"Agent not found: {agent_id}")

        config = self._configs.get(agent_id)
        return {
            "id": agent_id,
            "name": config.name if config else "Unknown",
            "description": config.description if config else "",
            "prompt_template": config.prompt_template if config else "",
            "capabilities": config.capabilities if config else [],
            "tools": config.tools if config else [],
            "policies": config.policies if config else {},
            "status": agent_data.get("status", "idle"),
            "created_at": agent_data.get("created_at"),
            "updated_at": agent_data.get("updated_at"),
        }

    async def update_agent_config(
        self, agent_id: str, config: AgentConfig
    ) -> None:
        """Update agent configuration.

        Args:
            agent_id: The agent identifier.
            config: New agent configuration.

        Raises:
            ValueError: If agent is not found.
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        self._configs[agent_id] = config
        self._agents[agent_id]["updated_at"] = datetime.now(UTC).isoformat()

        logger.info(
            "Updated agent config: agent=%s name=%s",
            agent_id[:8],
            config.name,
        )

    async def get_agent_performance(
        self, agent_id: str
    ) -> AgentPerformance:
        """Get performance metrics for an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            AgentPerformance with metrics.

        Raises:
            ValueError: If agent is not found.
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        history = self._history.get(agent_id, [])
        completed = sum(1 for h in history if h.get("status") == "completed")
        failed = sum(1 for h in history if h.get("status") == "failed")
        total = completed + failed

        durations = [
            h["duration_ms"]
            for h in history
            if "duration_ms" in h
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        success_rate = completed / total if total > 0 else 0.0

        last_active = None
        if history:
            last_entry = max(history, key=lambda h: h.get("timestamp", ""))
            last_active = datetime.fromisoformat(last_entry["timestamp"])

        return AgentPerformance(
            tasks_completed=completed,
            tasks_failed=failed,
            avg_duration=avg_duration,
            success_rate=success_rate,
            last_active=last_active,
        )

    async def get_agent_history(
        self, agent_id: str
    ) -> list[dict[str, Any]]:
        """Get execution history for an agent.

        Args:
            agent_id: The agent identifier.

        Returns:
            List of execution history entries.

        Raises:
            ValueError: If agent is not found.
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        return list(self._history.get(agent_id, []))

    async def test_agent(
        self,
        agent_id: str,
        prompt: str,
        repository_id: str,
    ) -> dict[str, Any]:
        """Test an agent with a prompt.

        Args:
            agent_id: The agent identifier.
            prompt: Test prompt.
            repository_id: Repository context.

        Returns:
            Test result dictionary.

        Raises:
            ValueError: If agent is not found.
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")

        config = self._configs.get(agent_id)
        agent_name = config.name if config else "Unknown"

        result = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "prompt": prompt,
            "repository_id": repository_id,
            "output": f"[Test output from {agent_name}] Simulated response to: {prompt[:100]}",
            "tokens_used": len(prompt.split()) + 50,
            "latency_ms": 200.0,
            "status": "success",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        self._history.setdefault(agent_id, []).append({
            "type": "test",
            "status": "completed",
            "prompt": prompt,
            "repository_id": repository_id,
            "duration_ms": 200.0,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        logger.info(
            "Tested agent: agent=%s prompt_len=%d",
            agent_id[:8],
            len(prompt),
        )

        return result

    async def get_agent_capabilities(self) -> list[dict[str, Any]]:
        """Get available agent capabilities.

        Returns:
            List of capability definitions.
        """
        return [
            {
                "id": "code_generation",
                "name": "Code Generation",
                "description": "Generate code from natural language descriptions",
                "category": "development",
                "tools_required": ["file_system", "terminal"],
            },
            {
                "id": "code_review",
                "name": "Code Review",
                "description": "Review code for quality, security, and best practices",
                "category": "quality",
                "tools_required": ["file_system"],
            },
            {
                "id": "refactoring",
                "name": "Refactoring",
                "description": "Refactor existing code to improve structure and readability",
                "category": "development",
                "tools_required": ["file_system", "terminal"],
            },
            {
                "id": "testing",
                "name": "Test Writing",
                "description": "Write unit and integration tests",
                "category": "quality",
                "tools_required": ["file_system", "terminal"],
            },
            {
                "id": "debugging",
                "name": "Debugging",
                "description": "Identify and fix bugs in code",
                "category": "development",
                "tools_required": ["file_system", "terminal"],
            },
            {
                "id": "documentation",
                "name": "Documentation",
                "description": "Generate and update documentation",
                "category": "documentation",
                "tools_required": ["file_system"],
            },
            {
                "id": "dependency_management",
                "name": "Dependency Management",
                "description": "Manage project dependencies and packages",
                "category": "operations",
                "tools_required": ["terminal", "file_system"],
            },
            {
                "id": "architecture_analysis",
                "name": "Architecture Analysis",
                "description": "Analyze and suggest architectural improvements",
                "category": "planning",
                "tools_required": ["file_system"],
            },
            {
                "id": "database_operations",
                "name": "Database Operations",
                "description": "Manage database schemas and migrations",
                "category": "data",
                "tools_required": ["database", "terminal"],
            },
            {
                "id": "deployment",
                "name": "Deployment",
                "description": "Deploy applications to various environments",
                "category": "operations",
                "tools_required": ["terminal", "docker"],
            },
        ]

    def register_agent(
        self,
        agent_id: str,
        config: AgentConfig,
        status: str = "idle",
    ) -> None:
        """Register a new agent in the manager.

        Args:
            agent_id: The agent identifier.
            config: Agent configuration.
            status: Initial status.
        """
        self._agents[agent_id] = {
            "status": status,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        self._configs[agent_id] = config
        self._history[agent_id] = []

        logger.info(
            "Registered agent: id=%s name=%s", agent_id[:8], config.name
        )
