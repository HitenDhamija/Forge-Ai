"""Pydantic schemas for the Enterprise AI Workforce module."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Roles for specialized agents."""

    SUPERVISOR = "supervisor"
    SOFTWARE_ENGINEER = "software_engineer"
    QA_ENGINEER = "qa_engineer"
    CODE_REVIEWER = "code_reviewer"
    TECHNICAL_WRITER = "technical_writer"
    DEVOPS_ENGINEER = "devops_engineer"
    DATABASE_ENGINEER = "database_engineer"
    RESEARCH_ENGINEER = "research_engineer"


class AgentStatus(str, Enum):
    """Agent operational status."""

    IDLE = "idle"
    ASSIGNED = "assigned"
    PREPARING = "preparing"
    WAITING = "waiting"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    OFFLINE = "offline"


class MessageType(str, Enum):
    """Types of messages between agents."""

    TASK_ASSIGNMENT = "task_assignment"
    TASK_ACCEPTED = "task_accepted"
    TASK_REJECTED = "task_rejected"
    PROGRESS_UPDATE = "progress_update"
    WARNING = "warning"
    FAILURE = "failure"
    SUCCESS = "success"
    INFORMATION = "information"
    REQUEST = "request"
    RESPONSE = "response"


class EventType(str, Enum):
    """Agent lifecycle events."""

    AGENT_REGISTERED = "agent_registered"
    AGENT_OFFLINE = "agent_offline"
    TASK_ASSIGNED = "task_assigned"
    TASK_ACCEPTED = "task_accepted"
    TASK_REJECTED = "task_rejected"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    HEARTBEAT = "heartbeat"


class Capability(BaseModel):
    """Agent capability definition."""

    name: str
    description: str
    level: int = Field(ge=1, le=10, description="Capability level 1-10")
    tools: list[str] = Field(default_factory=list)
    task_types: list[str] = Field(default_factory=list)


class Policy(BaseModel):
    """Agent policy definition."""

    allowed_tasks: list[str] = Field(default_factory=list)
    forbidden_tasks: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)
    repository_access: list[str] = Field(default_factory=list)
    max_concurrent_tasks: int = Field(default=1, ge=1)
    max_retries: int = Field(default=3, ge=0)
    timeout_seconds: int = Field(default=300, ge=30)


class AgentMessage(BaseModel):
    """Message for inter-agent communication via Supervisor."""

    id: str
    sender_id: str
    receiver_id: str | None = None
    message_type: MessageType
    content: dict
    timestamp: datetime
    requires_response: bool = False


class AgentMemory(BaseModel):
    """Agent memory structure."""

    short_term: list[dict] = Field(default_factory=list)
    task_memory: list[dict] = Field(default_factory=list)
    execution_context: dict = Field(default_factory=dict)
    conversation_state: list[dict] = Field(default_factory=list)


class AgentRegistration(BaseModel):
    """Agent registration request."""

    role: AgentRole
    name: str
    description: str
    capabilities: list[Capability]
    policies: Policy
    version: str = "1.0.0"


class AgentInfo(BaseModel):
    """Complete agent information."""

    id: str
    role: AgentRole
    name: str
    description: str
    status: AgentStatus
    capabilities: list[Capability]
    policies: Policy
    memory: AgentMemory
    version: str
    created_at: datetime
    updated_at: datetime
    last_heartbeat: datetime | None = None


class TaskAssignment(BaseModel):
    """Task assignment to an agent."""

    task_id: str
    workflow_id: str
    agent_id: str
    title: str
    description: str
    context: dict = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
    priority: str = "medium"
    timeout_seconds: int = 300


class TaskResult(BaseModel):
    """Result from agent task execution."""

    task_id: str
    agent_id: str
    status: str
    output: dict = Field(default_factory=dict)
    duration: int | None = None
    error: str | None = None


class AgentStatusResponse(BaseModel):
    """Agent status response."""

    total_agents: int
    idle_agents: int
    busy_agents: int
    unavailable_agents: int
    agents_by_role: dict[str, int]
