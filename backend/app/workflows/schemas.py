"""Pydantic schemas for the Workflows module."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    CREATED = "created"
    WAITING_APPROVAL = "waiting_approval"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPLETED = "completed"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Workflow risk levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, Enum):
    """Workflow event types."""

    WORKFLOW_CREATED = "workflow_created"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_RETRYING = "task_retrying"
    TASK_SKIPPED = "task_skipped"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"


class TaskRequest(BaseModel):
    """Request to create a task within a workflow."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: list[str] = Field(default_factory=list)
    agent_type: str | None = None
    estimated_duration: int | None = None
    metadata: dict = Field(default_factory=dict)


class WorkflowRequest(BaseModel):
    """Request to create a new workflow."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    project_id: str | None = None
    tasks: list[TaskRequest] = Field(..., min_length=1)
    requires_approval: bool = True
    risk_level: RiskLevel = RiskLevel.MEDIUM
    metadata: dict = Field(default_factory=dict)


class TaskInfo(BaseModel):
    """Information about a task."""

    id: str
    workflow_id: str
    title: str
    description: str
    priority: TaskPriority
    dependencies: list[str]
    agent_type: str | None
    status: TaskStatus
    retries: int
    max_retries: int
    execution_result: dict | None
    validation_result: dict | None
    duration: int | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class WorkflowInfo(BaseModel):
    """Information about a workflow."""

    id: str
    project_id: str | None
    title: str
    description: str
    status: WorkflowStatus
    current_step: int
    tasks: list[TaskInfo]
    execution_log: list[dict]
    approval_status: str | None
    risk_level: RiskLevel
    estimated_time: int | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    metadata: dict


class WorkflowEvent(BaseModel):
    """Event from workflow execution."""

    id: str
    workflow_id: str
    task_id: str | None
    event_type: EventType
    data: dict
    timestamp: datetime


class ExecutionSummary(BaseModel):
    """Summary of workflow execution."""

    workflow_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    skipped_tasks: int
    total_duration: int
    events: list[WorkflowEvent]
    success_rate: float
    average_task_duration: float


class ValidationResult(BaseModel):
    """Result of workflow validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    dependency_cycles: list[list[str]]
    ready_tasks: list[str]
