"""Base class for all agents in the system."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.agents.config import get_agent_settings
from app.agents.exceptions import AgentExecutionError, AgentTimeoutError
from app.agents.schemas import (
    AgentConfig,
    AgentInfo,
    AgentStatus,
    AgentType,
    TaskStatus,
)
from app.agents.tools.registry import ToolRegistry
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentBase(ABC):
    """Abstract base class for all agents.

    All agents must inherit from this class and implement the execute method.
    Agents are autonomous entities that can perform tasks using available tools.
    """

    def __init__(
        self,
        name: str,
        description: str,
        agent_type: AgentType,
        tool_registry: ToolRegistry,
        config: AgentConfig | None = None,
    ):
        """Initialize the agent.

        Args:
            name: Human-readable name for this agent.
            description: Description of what this agent does.
            agent_type: Type of agent.
            tool_registry: Registry of available tools.
            config: Agent configuration.
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.agent_type = agent_type
        self.tool_registry = tool_registry
        self.config = config or AgentConfig()
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.settings = get_agent_settings()

        self._current_task_id: str | None = None
        self._iteration_count = 0
        self._tokens_used = 0

    @abstractmethod
    async def execute(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        """Execute the agent's task.

        This is the main method that subclasses must implement.
        It should contain the agent's core logic.

        Args:
            task_id: ID of the task to execute.
            **kwargs: Additional execution parameters.

        Returns:
            Dictionary containing execution results.

        Raises:
            AgentExecutionError: If execution fails.
            AgentTimeoutError: If execution times out.
        """
        pass

    async def run(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        """Run the agent with timeout and error handling.

        This is the entry point for executing tasks. It wraps the execute method
        with timeout handling and error management.

        Args:
            task_id: ID of the task to execute.
            **kwargs: Additional execution parameters.

        Returns:
            Dictionary containing execution results.
        """
        self.status = AgentStatus.RUNNING
        self._current_task_id = task_id
        self._iteration_count = 0
        self.updated_at = datetime.now(timezone.utc)

        logger.info(
            "Agent %s (%s) starting task %s",
            self.name,
            self.id,
            task_id,
        )

        try:
            result = await self.execute(task_id, **kwargs)

            self.status = AgentStatus.IDLE
            self._current_task_id = None
            self.updated_at = datetime.now(timezone.utc)

            logger.info(
                "Agent %s completed task %s",
                self.name,
                task_id,
            )

            return {
                "success": True,
                "agent_id": self.id,
                "task_id": task_id,
                "result": result,
                "iterations": self._iteration_count,
                "tokens_used": self._tokens_used,
            }

        except AgentTimeoutError:
            self.status = AgentStatus.ERROR
            self._current_task_id = None
            self.updated_at = datetime.now(timezone.utc)

            logger.error(
                "Agent %s timed out on task %s",
                self.name,
                task_id,
            )

            raise

        except Exception as e:
            self.status = AgentStatus.ERROR
            self._current_task_id = None
            self.updated_at = datetime.now(timezone.utc)

            logger.error(
                "Agent %s failed on task %s: %s",
                self.name,
                task_id,
                str(e),
            )

            raise AgentExecutionError(
                message=str(e),
                agent_id=self.id,
                details={"task_id": task_id},
            )

    async def stop(self) -> None:
        """Stop the agent's current execution."""
        self.status = AgentStatus.STOPPED
        self._current_task_id = None
        self.updated_at = datetime.now(timezone.utc)

        logger.info("Agent %s stopped", self.name)

    def increment_iterations(self) -> None:
        """Increment the iteration counter and check against max."""
        self._iteration_count += 1
        if self._iteration_count > self.config.max_iterations:
            raise AgentTimeoutError(
                agent_id=self.id,
                timeout=self.config.timeout_seconds,
            )

    def add_tokens(self, count: int) -> None:
        """Track token usage."""
        self._tokens_used += count

    def get_info(self) -> AgentInfo:
        """Get information about this agent.

        Returns:
            AgentInfo containing agent metadata.
        """
        return AgentInfo(
            id=self.id,
            name=self.name,
            agent_type=self.agent_type,
            description=self.description,
            status=self.status,
            available_tools=self.tool_registry.get_available_tool_names(),
            config=self.config,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def get_available_tools(self) -> list[str]:
        """Get list of available tool names."""
        return self.tool_registry.get_available_tool_names()

    def has_tool(self, tool_name: str) -> bool:
        """Check if a tool is available to this agent."""
        return tool_name in self.tool_registry

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} ({self.agent_type.value})>"
