"""SQLAlchemy models for the Learning Engine module.

Stores engineering experiences, patterns, lessons, recommendations,
feedback, and knowledge graph relationships.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class ExperienceModel(BaseModel):
    """Stores completed workflow experiences for long-term learning."""

    __tablename__ = "experiences"

    workflow_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    repository_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    experience_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # architecture, bug_fix, deployment, database, testing, performance, security, documentation, refactoring
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    outcome: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # success, failure, partial
    solution: Mapped[str] = mapped_column(Text, nullable=False)
    files_changed: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    technologies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    reuse_potential: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    complexity: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    generalization_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    feedback_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    patterns: Mapped[list["PatternModel"]] = relationship(
        back_populates="experience", cascade="all, delete-orphan"
    )
    lessons: Mapped[list["LessonModel"]] = relationship(
        back_populates="experience", cascade="all, delete-orphan"
    )
    feedbacks: Mapped[list["FeedbackModel"]] = relationship(
        back_populates="experience", cascade="all, delete-orphan"
    )


class PatternModel(BaseModel):
    """Stores reusable engineering patterns extracted from experiences."""

    __tablename__ = "patterns"

    experience_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("experiences.id", ondelete="SET NULL"), nullable=True
    )
    pattern_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # architecture, coding, security, deployment, testing, database, frontend, backend
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    code_example: Mapped[str | None] = mapped_column(Text, nullable=True)
    when_to_use: Mapped[str] = mapped_column(Text, nullable=False)
    when_not_to_use: Mapped[str] = mapped_column(Text, nullable=False)
    technologies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    generalization_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    experience: Mapped["ExperienceModel | None"] = relationship(back_populates="patterns")
    recommendations: Mapped[list["RecommendationModel"]] = relationship(
        back_populates="pattern", cascade="all, delete-orphan"
    )


class LessonModel(BaseModel):
    """Stores lessons learned from failures and rejected implementations."""

    __tablename__ = "lessons"

    experience_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("experiences.id", ondelete="SET NULL"), nullable=True
    )
    lesson_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # failure, rejection, regression, violation, security_issue, performance_issue
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    avoidance_strategy: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # critical, high, medium, low
    technologies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    times_encountered: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    experience: Mapped["ExperienceModel | None"] = relationship(back_populates="lessons")


class RecommendationModel(BaseModel):
    """Stores recommendations for future tasks based on past experience."""

    __tablename__ = "recommendations"

    pattern_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("patterns.id", ondelete="SET NULL"), nullable=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    context_keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # high, medium, low
    technologies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    pattern: Mapped["PatternModel | None"] = relationship(back_populates="recommendations")


class FeedbackModel(BaseModel):
    """Stores human feedback on experiences and recommendations."""

    __tablename__ = "feedback"

    experience_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("experiences.id", ondelete="SET NULL"), nullable=True
    )
    feedback_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # helpful, incorrect, needs_improvement, excellent
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    experience: Mapped["ExperienceModel | None"] = relationship(back_populates="feedbacks")


class KnowledgeGraphModel(BaseModel):
    """Stores relationships between experiences, patterns, and lessons."""

    __tablename__ = "knowledge_graph"

    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # experience, pattern, lesson, recommendation
    source_id: Mapped[str] = mapped_column(String(36), nullable=False)
    target_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # experience, pattern, lesson, recommendation
    target_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relationship: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # derived_from, related_to, supersedes, conflicts_with, improves
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
