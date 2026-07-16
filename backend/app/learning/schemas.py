"""Pydantic schemas for the Learning Engine API."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ExperienceType(str, Enum):
    """Classification of development experiences."""

    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    TESTING = "testing"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"


class OutcomeType(str, Enum):
    """Outcome of an executed workflow."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class PatternType(str, Enum):
    """Category of discovered patterns."""

    ARCHITECTURE = "architecture"
    CODING = "coding"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"


class LessonType(str, Enum):
    """Type of lesson learned from an experience."""

    FAILURE = "failure"
    REJECTION = "rejection"
    REGRESSION = "regression"
    VIOLATION = "violation"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"


class FeedbackType(str, Enum):
    """User feedback classification."""

    HELPFUL = "helpful"
    INCORRECT = "incorrect"
    NEEDS_IMPROVEMENT = "needs_improvement"
    EXCELLENT = "excellent"


class Severity(str, Enum):
    """Severity level for issues and lessons."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Priority(str, Enum):
    """Priority level for recommendations and patterns."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class KnowledgeRelation(str, Enum):
    """Relationship type between knowledge items."""

    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"
    SUPERSEDES = "supersedes"
    CONFLICTS_WITH = "conflicts_with"
    IMPROVES = "improves"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ProcessWorkflowRequest(BaseModel):
    """Request to process a completed workflow into an experience."""

    workflow_id: str = Field(..., min_length=1, max_length=100)
    repository_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    outcome: OutcomeType
    files_changed: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    """Request to submit feedback on a learning experience."""

    experience_id: str = Field(..., min_length=1, max_length=100)
    feedback_type: FeedbackType
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class PatternSearchRequest(BaseModel):
    """Request to search for discovered patterns."""

    pattern_type: PatternType | None = None
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    query: str | None = Field(default=None, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)


class RecommendationRequest(BaseModel):
    """Request to get recommendations for a new task."""

    task_type: ExperienceType
    context_keywords: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ExperiencePattern(BaseModel):
    """Pattern associated with an experience."""

    id: str
    pattern_type: PatternType
    name: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    occurrences: int
    tags: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ExperienceLesson(BaseModel):
    """Lesson associated with an experience."""

    id: str
    lesson_type: LessonType
    title: str
    description: str
    severity: Severity
    recommendation: str

    class Config:
        from_attributes = True


class ExperienceFeedback(BaseModel):
    """Feedback entry for an experience."""

    id: str
    feedback_type: FeedbackType
    rating: int = Field(..., ge=1, le=5)
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ExperienceResponse(BaseModel):
    """Full experience record with related patterns, lessons, and feedback."""

    id: str
    workflow_id: str
    repository_id: str
    title: str
    description: str
    experience_type: ExperienceType
    outcome: OutcomeType
    confidence: float = Field(..., ge=0.0, le=1.0)
    files_changed: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    patterns: list[ExperiencePattern] = Field(default_factory=list)
    lessons: list[ExperienceLesson] = Field(default_factory=list)
    feedback: list[ExperienceFeedback] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatternResponse(BaseModel):
    """Discovered pattern details with usage statistics."""

    id: str
    pattern_type: PatternType
    name: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    occurrences: int
    success_rate: float = Field(..., ge=0.0, le=1.0)
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LessonResponse(BaseModel):
    """Lesson learned details."""

    id: str
    lesson_type: LessonType
    title: str
    description: str
    severity: Severity
    recommendation: str
    experience_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    occurrences: int
    technologies: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecommendationItem(BaseModel):
    """Single recommendation entry."""

    id: str
    title: str
    description: str
    priority: Priority
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_experience_id: str | None = None
    source_pattern_id: str | None = None
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    """Recommendations for a new task based on learned knowledge."""

    recommendations: list[RecommendationItem] = Field(default_factory=list)
    context_keywords: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        from_attributes = True


class FeedbackResponse(BaseModel):
    """Acknowledgement of submitted feedback."""

    id: str
    experience_id: str
    feedback_type: FeedbackType
    rating: int = Field(..., ge=1, le=5)
    acknowledged: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class LearningStatsResponse(BaseModel):
    """Aggregate statistics for the learning engine."""

    total_experiences: int = 0
    total_patterns: int = 0
    total_lessons: int = 0
    total_feedback: int = 0
    average_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    top_technologies: list[str] = Field(default_factory=list)
    top_patterns: list[str] = Field(default_factory=list)
    experiences_by_type: dict[str, int] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        from_attributes = True


class ExperienceTimeSeries(BaseModel):
    """Experience data point over time."""

    date: datetime
    count: int
    success_count: int
    failure_count: int


class SuccessRateTrend(BaseModel):
    """Success rate data point over time."""

    date: datetime
    success_rate: float = Field(..., ge=0.0, le=1.0)
    total_experiences: int


class PatternUsageEntry(BaseModel):
    """Pattern usage data point over time."""

    date: datetime
    pattern_name: str
    count: int


class GrowthAnalyticsResponse(BaseModel):
    """Growth and analytics data for the learning engine."""

    experience_over_time: list[ExperienceTimeSeries] = Field(default_factory=list)
    success_rate_trends: list[SuccessRateTrend] = Field(default_factory=list)
    pattern_usage: list[PatternUsageEntry] = Field(default_factory=list)
    total_experiences: int = 0
    total_patterns_discovered: int = 0
    average_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    period_start: datetime | None = None
    period_end: datetime | None = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Internal dataclasses (for passing data between learning modules)
# ---------------------------------------------------------------------------

@dataclass
class ExperienceData:
    """Internal representation of experience data between learning modules."""

    workflow_id: str
    repository_id: str
    title: str
    description: str
    experience_type: ExperienceType
    outcome: OutcomeType
    files_changed: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class PatternData:
    """Internal representation of pattern data between learning modules."""

    pattern_type: PatternType
    name: str
    description: str
    confidence: float = 0.0
    occurrences: int = 0
    technologies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


@dataclass
class LessonData:
    """Internal representation of lesson data between learning modules."""

    lesson_type: LessonType
    title: str
    description: str
    severity: Severity
    recommendation: str
    experience_id: str = ""
    confidence: float = 0.0
    occurrences: int = 0
    technologies: list[str] = field(default_factory=list)
