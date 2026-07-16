"""Orchestrator for managing agents and task execution."""

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from app.agents.agent_base import AgentBase
from app.agents.config import get_agent_settings
from app.agents.exceptions import (
    AgentNotFoundError,
    AgentTimeoutError,
    TaskCancelledError,
    TaskNotFoundError,
)
from app.infrastructure.notifications import notify_task_completed, notify_task_failed
from app.agents.schemas import (
    AgentStatus,
    AgentType,
    TaskInfo,
    TaskPriority,
    TaskRequest,
    TaskStatus,
)
from app.agents.tools.registry import ToolRegistry
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentOrchestrator:
    """Orchestrator for managing agents and coordinating task execution.

    The orchestrator is responsible for:
    - Managing agent instances
    - Routing tasks to appropriate agents
    - Tracking task status and progress
    - Handling concurrent execution
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        """Initialize the orchestrator.

        Args:
            tool_registry: Registry of available tools.
        """
        self.tool_registry = tool_registry
        self.settings = get_agent_settings()
        self._agents: dict[str, AgentBase] = {}
        self._tasks: dict[str, TaskInfo] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}

    def register_agent(self, agent: AgentBase) -> None:
        """Register an agent with the orchestrator.

        Args:
            agent: Agent instance to register.
        """
        self._agents[agent.id] = agent
        logger.info(
            "Agent registered: %s (%s) - %s",
            agent.name,
            agent.id,
            agent.agent_type.value,
        )

    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the orchestrator.

        Args:
            agent_id: ID of the agent to remove.
        """
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            if agent.status == AgentStatus.RUNNING:
                logger.warning(" unregistering running agent: %s", agent_id)
            del self._agents[agent_id]
            logger.info("Agent unregistered: %s", agent_id)

    def get_agent(self, agent_id: str) -> AgentBase:
        """Get an agent by ID.

        Args:
            agent_id: ID of the agent to retrieve.

        Returns:
            The requested agent instance.

        Raises:
            AgentNotFoundError: If the agent is not found.
        """
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id)
        return self._agents[agent_id]

    def get_agents_by_type(self, agent_type: AgentType) -> list[AgentBase]:
        """Get all agents of a specific type.

        Args:
            agent_type: Type of agents to retrieve.

        Returns:
            List of agents matching the specified type.
        """
        return [
            agent for agent in self._agents.values()
            if agent.agent_type == agent_type
        ]

    def get_available_agents(self) -> list[AgentBase]:
        """Get all agents that are idle and available for tasks.

        Returns:
            List of available agents.
        """
        return [
            agent for agent in self._agents.values()
            if agent.status == AgentStatus.IDLE
        ]

    def list_agents(self) -> list[dict[str, Any]]:
        """List all registered agents.

        Returns:
            List of agent information dictionaries.
        """
        return [agent.get_info().model_dump() for agent in self._agents.values()]

    async def submit_task(self, request: TaskRequest) -> TaskInfo:
        """Submit a new task for execution.

        Args:
            request: Task request containing task details.

        Returns:
            TaskInfo with the created task details.
        """
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        task = TaskInfo(
            id=task_id,
            title=request.title,
            description=request.description,
            status=TaskStatus.QUEUED,
            priority=request.priority,
            agent_type=request.agent_type,
            context=request.context,
            created_at=now,
            updated_at=now,
        )

        self._tasks[task_id] = task
        logger.info("Task submitted: %s - %s", task_id, request.title)

        agent = self._find_best_agent(request)
        if agent:
            task.agent_id = agent.id
            await self._start_task(task, agent)
        else:
            logger.warning("No available agent for task %s", task_id)

        return task

    def _find_best_agent(self, request: TaskRequest) -> AgentBase | None:
        """Find the best available agent for a task.

        Args:
            request: Task request.

        Returns:
            Best available agent or None.
        """
        available = [
            agent for agent in self._agents.values()
            if (
                agent.status == AgentStatus.IDLE
                and agent.agent_type == request.agent_type
            )
        ]

        if not available:
            return None

        return min(available, key=lambda a: self._count_running_tasks(a.id))

    def _count_running_tasks(self, agent_id: str) -> int:
        """Count running tasks for an agent."""
        return sum(
            1 for task in self._tasks.values()
            if task.agent_id == agent_id and task.status == TaskStatus.RUNNING
        )

    async def _start_task(self, task: TaskInfo, agent: AgentBase) -> None:
        """Start executing a task with an agent.

        Args:
            task: Task to execute.
            agent: Agent to execute the task.
        """
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)

        async def _run():
            try:
                result = await agent.run(task.id, **task.context)
                task.status = TaskStatus.COMPLETED
                task.result = result.get("result", {})
                task.completed_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                notify_task_completed(os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"), task.name or task.id, task.id, str(task.result)[:200])
            except AgentTimeoutError:
                task.status = TaskStatus.FAILED
                task.error = "Task timed out"
                task.completed_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                notify_task_failed(os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"), task.name or task.id, task.id, "Task timed out")
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                notify_task_failed(os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"), task.name or task.id, task.id, str(e))

        self._running_tasks[task.id] = asyncio.create_task(_run())

    async def cancel_task(self, task_id: str) -> TaskInfo:
        """Cancel a running task.

        Args:
            task_id: ID of the task to cancel.

        Returns:
            Updated TaskInfo.

        Raises:
            TaskNotFoundError: If the task is not found.
        """
        task = self.get_task(task_id)

        if task.status not in (TaskStatus.QUEUED, TaskStatus.RUNNING):
            raise TaskCancelledError(task_id)

        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]

        if task.agent_id:
            agent = self.get_agent(task.agent_id)
            await agent.stop()

        task.status = TaskStatus.CANCELLED
        task.updated_at = datetime.now(timezone.utc)

        logger.info("Task cancelled: %s", task_id)
        return task

    def get_task(self, task_id: str) -> TaskInfo:
        """Get task by ID.

        Args:
            task_id: ID of the task to retrieve.

        Returns:
            The requested TaskInfo.

        Raises:
            TaskNotFoundError: If the task is not found.
        """
        if task_id not in self._tasks:
            raise TaskNotFoundError(task_id)
        return self._tasks[task_id]

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        agent_type: AgentType | None = None,
    ) -> list[TaskInfo]:
        """List tasks with optional filters.

        Args:
            status: Filter by task status.
            agent_type: Filter by agent type.

        Returns:
            List of matching tasks.
        """
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if agent_type:
            tasks = [t for t in tasks if t.agent_type == agent_type]

        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def get_metrics(self) -> dict[str, Any]:
        """Get orchestrator metrics.

        Returns:
            Dictionary containing metrics.
        """
        tasks = list(self._tasks.values())
        return {
            "total_agents": len(self._agents),
            "idle_agents": sum(
                1 for a in self._agents.values()
                if a.status == AgentStatus.IDLE
            ),
            "running_agents": sum(
                1 for a in self._agents.values()
                if a.status == AgentStatus.RUNNING
            ),
            "total_tasks": len(tasks),
            "completed_tasks": sum(
                1 for t in tasks if t.status == TaskStatus.COMPLETED
            ),
            "failed_tasks": sum(
                1 for t in tasks if t.status == TaskStatus.FAILED
            ),
            "running_tasks": sum(
                1 for t in tasks if t.status == TaskStatus.RUNNING
            ),
            "queued_tasks": sum(
                1 for t in tasks if t.status == TaskStatus.QUEUED
            ),
        }
