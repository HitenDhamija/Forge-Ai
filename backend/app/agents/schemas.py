"""Pydantic schemas for the Agents module."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents available in the system."""

    PLANNER = "planner"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    RESEARCHER = "researcher"
    ORCHESTRATOR = "orchestrator"


class AgentStatus(str, Enum):
    """Current status of an agent."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolType(str, Enum):
    """Types of tools available to agents."""

    FILE = "file"
    SEARCH = "search"
    GIT = "git"
    SHELL = "shell"
    WEB = "web"
    AI = "ai"
    CUSTOM = "custom"


class AgentConfig(BaseModel):
    """Configuration for an agent instance."""

    max_iterations: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    tools: list[str] = Field(default_factory=list)
    custom_instructions: str | None = None


class ToolDefinition(BaseModel):
    """Definition of a tool available to agents."""

    name: str
    description: str
    tool_type: ToolType
    parameters: dict[str, dict] = Field(default_factory=dict)
    required_permissions: list[str] = Field(default_factory=list)


class AgentInfo(BaseModel):
    """Information about an available agent."""

    id: str
    name: str
    agent_type: AgentType
    description: str
    status: AgentStatus
    available_tools: list[str]
    config: AgentConfig
    created_at: datetime
    updated_at: datetime


class TaskRequest(BaseModel):
    """Request to create a new task."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    agent_type: AgentType = AgentType.PLANNER
    priority: TaskPriority = TaskPriority.MEDIUM
    context: dict = Field(default_factory=dict)
    tools_allowed: list[str] | None = None
    max_iterations: int = Field(default=10, ge=1, le=100)


class TaskStep(BaseModel):
    """A single step within a task execution plan."""

    id: str
    step_number: int
    description: str
    tool_to_use: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TaskInfo(BaseModel):
    """Information about a task."""

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    agent_id: str | None = None
    agent_type: AgentType
    steps: list[TaskStep] = Field(default_factory=list)
    context: dict = Field(default_factory=dict)
    result: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AgentMessage(BaseModel):
    """Message for inter-agent communication."""

    id: str
    sender_id: str
    receiver_id: str | None = None
    content: str
    message_type: str = "info"
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime


class TaskProgress(BaseModel):
    """Progress update for a task."""

    task_id: str
    current_step: int
    total_steps: int
    status: TaskStatus
    message: str | None = None
    timestamp: datetime


class AgentMetrics(BaseModel):
    """Metrics for agent performance tracking."""

    agent_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_execution_time: float = 0.0
    total_tokens_used: int = 0
    last_active: datetime | None = None
