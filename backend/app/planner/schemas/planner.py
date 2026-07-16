"""Pydantic schemas for the Planning Engine."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Classification of user intent."""

    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    CONFIGURATION = "configuration"
    RESEARCH = "research"
    UNKNOWN = "unknown"


class TaskPriority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class ComplexityLevel(str, Enum):
    """Task complexity levels."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class RiskLevel(str, Enum):
    """Risk severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlanStatus(str, Enum):
    """Plan lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of development tasks."""

    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    CONFIGURATION = "configuration"
    RESEARCH = "research"
    REFACTORING = "refactoring"


class IntentClassification(BaseModel):
    """Result of intent classification."""

    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    sub_intents: list[IntentType] = Field(default_factory=list)
    reasoning: str = ""
    keywords: list[str] = Field(default_factory=list)


class Task(BaseModel):
    """A single task in a plan."""

    id: str
    title: str
    description: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    complexity: ComplexityLevel = ComplexityLevel.MEDIUM
    estimated_hours: float = 0.0
    dependencies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DependencyInfo(BaseModel):
    """Information about a task dependency."""

    task_id: str
    dependent_task_id: str
    dependency_type: str = "blocks"
    description: str = ""


class RiskItem(BaseModel):
    """A single risk identified in the plan."""

    id: str
    title: str
    description: str
    risk_level: RiskLevel
    affected_tasks: list[str] = Field(default_factory=list)
    mitigation: str = ""
    probability: float = Field(default=0.5, ge=0.0, le=1.0)
    impact: float = Field(default=0.5, ge=0.0, le=1.0)
    category: str = "general"


class ComplexityAnalysis(BaseModel):
    """Result of complexity analysis."""

    level: ComplexityLevel
    score: float = Field(ge=0.0)
    factors: list[str] = Field(default_factory=list)
    estimated_total_hours: float = 0.0
    task_count: int = 0
    avg_task_complexity: float = 0.0


class Plan(BaseModel):
    """A complete execution plan."""

    id: str
    title: str
    description: str
    status: PlanStatus = PlanStatus.DRAFT
    tasks: list[Task] = Field(default_factory=list)
    dependencies: list[DependencyInfo] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    complexity: ComplexityAnalysis | None = None
    intent: IntentClassification | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    estimated_total_hours: float = 0.0


class PlanCreateRequest(BaseModel):
    """Request to create a new plan."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    goals: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)


class PlanUpdateRequest(BaseModel):
    """Request to update an existing plan."""

    title: str | None = None
    description: str | None = None
    status: PlanStatus | None = None
    metadata: dict[str, Any] | None = None


class PlanResponse(BaseModel):
    """Response for plan operations."""

    plan: Plan
    message: str = "Plan created successfully"


class PlanListResponse(BaseModel):
    """Response for listing plans."""

    plans: list[Plan]
    total: int
    page: int = 1
    per_page: int = 20


class PlanHistoryEntry(BaseModel):
    """An entry in the plan history."""

    plan_id: str
    action: str
    timestamp: datetime
    details: dict[str, Any] = Field(default_factory=dict)
    user_id: str | None = None
