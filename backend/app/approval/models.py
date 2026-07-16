"""Approval database models."""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database.base import Base


class ApprovalStatusDB(str, enum.Enum):
    """Approval request status for database."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ApprovalRequest(Base):
    """Approval request model."""

    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("executions.id"), nullable=False)
    step_id = Column(String, nullable=False)
    request_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    context = Column(JSON, nullable=True)
    risk_level = Column(String, default="medium")
    status = Column(String, default=ApprovalStatusDB.PENDING.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String, nullable=True)

    # Relationships
    decisions = relationship("ApprovalDecision", back_populates="request", cascade="all, delete-orphan")


class ApprovalDecision(Base):
    """Approval decision model."""

    __tablename__ = "approval_decisions"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("approval_requests.id"), nullable=False)
    decision = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    decided_by = Column(String, nullable=False)
    decided_at = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column("metadata", JSON, nullable=True)

    # Relationships
    request = relationship("ApprovalRequest", back_populates="decisions")
