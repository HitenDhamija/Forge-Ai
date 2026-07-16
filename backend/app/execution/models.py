"""Execution database models."""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database.base import Base


class ExecutionStatusDB(str, enum.Enum):
    """Execution status for database."""

    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class Execution(Base):
    """Execution model."""

    __tablename__ = "executions"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    repository_id = Column(String, nullable=False)
    status = Column(String, default=ExecutionStatusDB.PENDING.value)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    execution_duration = Column(Float, default=0.0)
    summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    steps = relationship("ExecutionStep", back_populates="execution", cascade="all, delete-orphan")
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan")
    rollback_points = relationship("RollbackPoint", back_populates="execution", cascade="all, delete-orphan")


class ExecutionStep(Base):
    """Execution step model."""

    __tablename__ = "execution_steps"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    task_id = Column(String, nullable=False)
    agent_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, default={})
    dependencies = Column(JSON, default=[])
    requires_approval = Column(Integer, default=0)
    status = Column(String, default="pending")
    result = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    execution = relationship("Execution", back_populates="steps")


class ExecutionLog(Base):
    """Execution log model."""

    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    step_id = Column(String, nullable=True)
    level = Column(String, default="info")
    message = Column(Text, nullable=False)
    agent_id = Column(String, nullable=True)
    tool_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    execution = relationship("Execution", back_populates="logs")


class RollbackPoint(Base):
    """Rollback point model."""

    __tablename__ = "rollback_points"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    step_id = Column(String, nullable=False)
    checkpoint_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)
    git_commit_hash = Column(String, nullable=True)
    branch_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    execution = relationship("Execution", back_populates="rollback_points")


class ExecutionArtifact(Base):
    """Execution artifact model."""

    __tablename__ = "execution_artifacts"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    artifact_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
