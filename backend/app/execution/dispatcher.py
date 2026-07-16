"""Dispatcher for Execution Engine.

Dispatches tasks to appropriate agents.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentType(str, Enum):
    """Agent types."""

    SOFTWARE_ENGINEER = "software_engineer"
    QA_ENGINEER = "qa_engineer"
    REVIEWER = "reviewer"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"


@dataclass
class DispatchedTask:
    """Dispatched task."""

    task_id: str
    agent_type: AgentType
    agent_id: str | None = None
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    result: dict[str, Any] | None = None


class Dispatcher:
    """Dispatches tasks to agents."""

    def __init__(self):
        """Initialize dispatcher."""
        self._agents: dict[AgentType, str] = {
            AgentType.SOFTWARE_ENGINEER: "software-engineer",
            AgentType.QA_ENGINEER: "qa-engineer",
            AgentType.REVIEWER: "reviewer",
            AgentType.DOCUMENTATION: "documentation",
        }
        self._tasks: dict[str, list[DispatchedTask]] = {}

    async def dispatch(
        self,
        execution_id: str,
        task_id: str,
        agent_type: AgentType,
        description: str,
        parameters: dict[str, Any],
        dependencies: list[str] | None = None,
    ) -> DispatchedTask:
        """Dispatch task to agent.

        Args:
            execution_id: Execution identifier.
            task_id: Task identifier.
            agent_type: Type of agent.
            description: Task description.
            parameters: Task parameters.
            dependencies: Task dependencies.

        Returns:
            Dispatched task.
        """
        logger.info(
            "Dispatching task %s to %s",
            task_id[:8],
            agent_type.value,
        )

        task = DispatchedTask(
            task_id=task_id,
            agent_type=agent_type,
            description=description,
            parameters=parameters,
            dependencies=dependencies or [],
        )

        if execution_id not in self._tasks:
            self._tasks[execution_id] = []

        self._tasks[execution_id].append(task)

        return task

    async def execute_task(
        self,
        execution_id: str,
        task_id: str,
    ) -> dict[str, Any]:
        """Execute dispatched task.

        Args:
            execution_id: Execution identifier.
            task_id: Task identifier.

        Returns:
            Task result.
        """
        tasks = self._tasks.get(execution_id, [])
        task = next((t for t in tasks if t.task_id == task_id), None)

        if not task:
            return {"success": False, "error": "Task not found"}

        logger.info("Executing task %s with %s", task_id[:8], task.agent_type.value)

        # Route to appropriate agent
        result = await self._route_to_agent(task)

        task.status = "completed" if result.get("success") else "failed"
        task.result = result

        return result

    async def _route_to_agent(self, task: DispatchedTask) -> dict[str, Any]:
        """Route task to appropriate agent."""
        if task.agent_type == AgentType.SOFTWARE_ENGINEER:
            return await self._execute_software_engineer_task(task)
        elif task.agent_type == AgentType.QA_ENGINEER:
            return await self._execute_qa_task(task)
        elif task.agent_type == AgentType.REVIEWER:
            return await self._execute_reviewer_task(task)
        elif task.agent_type == AgentType.DOCUMENTATION:
            return await self._execute_documentation_task(task)
        else:
            return {"success": False, "error": f"Unknown agent type: {task.agent_type}"}

    async def _execute_software_engineer_task(
        self,
        task: DispatchedTask,
    ) -> dict[str, Any]:
        """Execute software engineer task."""
        # Integration with Software Engineer Agent
        logger.info("Executing software engineer task: %s", task.description)
        return {"success": True, "message": "Task executed by Software Engineer"}

    async def _execute_qa_task(
        self,
        task: DispatchedTask,
    ) -> dict[str, Any]:
        """Execute QA task."""
        # Integration with QA Agent
        logger.info("Executing QA task: %s", task.description)
        return {"success": True, "message": "Task executed by QA Engineer"}

    async def _execute_reviewer_task(
        self,
        task: DispatchedTask,
    ) -> dict[str, Any]:
        """Execute reviewer task."""
        # Integration with Review Agent
        logger.info("Executing reviewer task: %s", task.description)
        return {"success": True, "message": "Task executed by Reviewer"}

    async def _execute_documentation_task(
        self,
        task: DispatchedTask,
    ) -> dict[str, Any]:
        """Execute documentation task."""
        # Integration with Documentation Agent
        logger.info("Executing documentation task: %s", task.description)
        return {"success": True, "message": "Task executed by Documentation Agent"}

    def get_tasks(self, execution_id: str) -> list[DispatchedTask]:
        """Get tasks for execution."""
        return self._tasks.get(execution_id, [])

    def get_task(
        self,
        execution_id: str,
        task_id: str,
    ) -> DispatchedTask | None:
        """Get specific task."""
        tasks = self._tasks.get(execution_id, [])
        return next((t for t in tasks if t.task_id == task_id), None)
