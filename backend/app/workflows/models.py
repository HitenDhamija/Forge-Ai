"""SQLAlchemy models for the Workflows module."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel
from app.workflows.schemas import TaskPriority, TaskStatus, WorkflowStatus, RiskLevel


class WorkflowModel(BaseModel):
    """SQLAlchemy model for workflows."""

    __tablename__ = "workflows"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=WorkflowStatus.CREATED.value,
        nullable=False,
    )
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approval_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_level: Mapped[str] = mapped_column(
        String(20),
        default=RiskLevel.MEDIUM.value,
        nullable=False,
    )
    estimated_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    tasks: Mapped[list["WorkflowTaskModel"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan"
    )
    events: Mapped[list["WorkflowEventModel"]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan"
    )


class WorkflowTaskModel(BaseModel):
    """SQLAlchemy model for workflow tasks."""

    __tablename__ = "workflow_tasks"

    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20),
        default=TaskPriority.MEDIUM.value,
        nullable=False,
    )
    dependencies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    agent_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TaskStatus.PENDING.value,
        nullable=False,
    )
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    execution_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    workflow: Mapped["WorkflowModel"] = relationship(back_populates="tasks")


class WorkflowEventModel(BaseModel):
    """SQLAlchemy model for workflow events."""

    __tablename__ = "workflow_events"

    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    workflow: Mapped["WorkflowModel"] = relationship(back_populates="events")
