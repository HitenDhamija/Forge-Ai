"""Agent runtime for managing agent lifecycle and execution."""

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.agents.enterprise.communication import CommunicationBus
from app.agents.enterprise.memory import AgentMemoryManager
from app.agents.enterprise.prompts import PromptManager, create_default_templates
from app.agents.enterprise.registry import AgentRegistry
from app.agents.enterprise.schemas import (
    AgentInfo,
    AgentRole,
    AgentStatus,
    Capability,
    EventType,
    Policy,
)
from app.agents.enterprise.supervisor import SupervisorAgent
from app.agents.enterprise.validators import AgentValidator
from app.agents.enterprise.specialized import create_all_agents, BaseSpecializedAgent
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentRuntime:
    """Runtime for managing agent lifecycle and execution.

    The AgentRuntime is the central coordinator for:
    - Agent registration and discovery
    - Workflow execution
    - Task assignment
    - Progress tracking
    - Event management
    """

    def __init__(self):
        """Initialize the Agent Runtime."""
        self.registry = AgentRegistry()
        self.communication = CommunicationBus()
        self.validator = AgentValidator()
        self.prompt_manager = create_default_templates()

        self.supervisor = SupervisorAgent(
            registry=self.registry,
            communication=self.communication,
        )
        self.registry.register(self.supervisor.get_info())

        self._specialized_agents: dict[str, BaseSpecializedAgent] = {}
        self._events: list[dict[str, Any]] = []
        self._workflows: dict[str, dict[str, Any]] = {}

        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all specialized agents."""
        agents = create_all_agents()

        for agent in agents:
            self._specialized_agents[agent.id] = agent
            self.registry.register(agent.get_info())

        logger.info("Agent Runtime initialized with %d agents", len(agents))

    async def process_workflow(
        self,
        workflow_id: str,
        workflow_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a workflow through the Supervisor.

        Args:
            workflow_id: Workflow ID.
            workflow_data: Complete workflow data.

        Returns:
            Processing result.
        """
        logger.info("Processing workflow: %s", workflow_id)

        self._workflows[workflow_id] = {
            "data": workflow_data,
            "status": "processing",
            "started_at": datetime.now(timezone.utc),
        }

        analysis = await self.supervisor.receive_workflow(workflow_id, workflow_data)

        self._emit_event(
            EventType.TASK_ASSIGNED,
            {"workflow_id": workflow_id, "analysis": analysis},
        )

        tasks = workflow_data.get("tasks", [])
        assignments = []

        for task in tasks:
            assignment = await self.supervisor.assign_task(workflow_id, task)
            if assignment:
                assignments.append(assignment.model_dump())

        self._workflows[workflow_id]["status"] = "assigned"
        self._workflows[workflow_id]["assignments"] = assignments

        return {
            "workflow_id": workflow_id,
            "status": "assigned",
            "analysis": analysis,
            "assignments": assignments,
        }

    async def handle_task_completion(
        self,
        task_id: str,
        agent_id: str,
        status: str,
        output: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Handle task completion.

        Args:
            task_id: Task ID.
            agent_id: Agent ID.
            status: Result status.
            output: Task output.
            error: Error message if failed.
        """
        await self.supervisor.handle_task_result(
            task_id=task_id,
            agent_id=agent_id,
            status=status,
            output=output,
            error=error,
        )

        event_type = EventType.TASK_COMPLETED if status == "completed" else EventType.TASK_FAILED
        self._emit_event(
            event_type,
            {"task_id": task_id, "agent_id": agent_id, "status": status},
        )

    def get_agent(self, agent_id: str) -> AgentInfo | None:
        """Get agent by ID.

        Args:
            agent_id: Agent ID.

        Returns:
            Agent information or None.
        """
        return self.registry.get_agent(agent_id)

    def list_agents(self) -> list[AgentInfo]:
        """List all agents.

        Returns:
            List of all agents.
        """
        return self.registry.list_all()

    def get_agents_by_role(self, role: AgentRole) -> list[AgentInfo]:
        """Get agents by role.

        Args:
            role: Agent role.

        Returns:
            List of agents with the role.
        """
        return self.registry.get_agents_by_role(role)

    def get_status_summary(self) -> dict[str, Any]:
        """Get summary of all agent statuses.

        Returns:
            Status summary.
        """
        return self.registry.get_status_summary().model_dump()

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get workflow status.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Workflow status or None.
        """
        return self._workflows.get(workflow_id)

    def get_events(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent events.

        Args:
            limit: Maximum events to return.

        Returns:
            List of events.
        """
        return self._events[-limit:]

    def _emit_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Emit an event.

        Args:
            event_type: Event type.
            data: Event data.
        """
        event = {
            "id": str(len(self._events)),
            "type": event_type.value,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._events.append(event)
        logger.info("Event emitted: %s", event_type.value)

    def register_agent(self, agent_info: AgentInfo) -> None:
        """Register a new agent.

        Args:
            agent_info: Agent information.
        """
        self.registry.register(agent_info)
        self._emit_event(EventType.AGENT_REGISTERED, {"agent_id": agent_info.id})

    def update_agent_status(self, agent_id: str, status: AgentStatus) -> None:
        """Update agent status.

        Args:
            agent_id: Agent ID.
            status: New status.
        """
        self.registry.update_status(agent_id, status)

    def agent_heartbeat(self, agent_id: str) -> None:
        """Update agent heartbeat.

        Args:
            agent_id: Agent ID.
        """
        self.registry.update_heartbeat(agent_id)
        self._emit_event(EventType.HEARTBEAT, {"agent_id": agent_id})
