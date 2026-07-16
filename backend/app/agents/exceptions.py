"""Exception hierarchy for the Agents module."""

from app.exceptions.base import ForgeAIException


class AgentException(ForgeAIException):
    """Base exception for agent-related errors."""

    def __init__(self, message: str, agent_id: str | None = None):
        self.agent_id = agent_id
        super().__init__(message=message)


class AgentNotFoundError(AgentException):
    """Raised when an agent is not found."""

    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent not found: {agent_id}",
            agent_id=agent_id,
        )
        self.error_code = "AGENT_NOT_FOUND"
        self.status_code = 404


class AgentTimeoutError(AgentException):
    """Raised when an agent execution times out."""

    def __init__(self, agent_id: str, timeout: int):
        super().__init__(
            message=f"Agent {agent_id} timed out after {timeout}s",
            agent_id=agent_id,
        )
        self.error_code = "AGENT_TIMEOUT"
        self.status_code = 408


class AgentExecutionError(AgentException):
    """Raised when an agent encounters an execution error."""

    def __init__(self, message: str, agent_id: str, details: dict | None = None):
        super().__init__(message=message, agent_id=agent_id)
        self.details = details or {}
        self.error_code = "AGENT_EXECUTION_ERROR"
        self.status_code = 500


class ToolNotFoundError(AgentException):
    """Raised when a requested tool is not available."""

    def __init__(self, tool_name: str, agent_id: str | None = None):
        super().__init__(
            message=f"Tool not found: {tool_name}",
            agent_id=agent_id,
        )
        self.tool_name = tool_name
        self.error_code = "TOOL_NOT_FOUND"
        self.status_code = 404


class ToolExecutionError(AgentException):
    """Raised when a tool fails to execute."""

    def __init__(self, tool_name: str, message: str, agent_id: str | None = None):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {message}",
            agent_id=agent_id,
        )
        self.tool_name = tool_name
        self.error_code = "TOOL_EXECUTION_ERROR"
        self.status_code = 500


class TaskNotFoundError(AgentException):
    """Raised when a task is not found."""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task not found: {task_id}",
        )
        self.task_id = task_id
        self.error_code = "TASK_NOT_FOUND"
        self.status_code = 404


class TaskCancelledError(AgentException):
    """Raised when attempting to operate on a cancelled task."""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task has been cancelled: {task_id}",
        )
        self.task_id = task_id
        self.error_code = "TASK_CANCELLED"
        self.status_code = 409
