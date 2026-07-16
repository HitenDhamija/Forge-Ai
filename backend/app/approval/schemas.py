"""Approval Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any


class ApprovalRequestCreate(BaseModel):
    """Schema for creating an approval request."""

    execution_id: str
    step_id: str
    request_type: str = Field(..., description="Type: auth, database, file_delete, dependency, general")
    title: str
    description: str | None = None
    context: dict[str, Any] | None = None
    risk_level: str = Field(default="medium", description="low, medium, high, critical")
    timeout_minutes: int | None = Field(default=None, description="Timeout in minutes, None=never")


class ApprovalDecisionCreate(BaseModel):
    """Schema for creating an approval decision."""

    decision: str = Field(..., description="approved or denied")
    reason: str | None = None
    decided_by: str = Field(default="human", description="Who made the decision")


class ApprovalRequestResponse(BaseModel):
    """Schema for approval request response."""

    id: str
    execution_id: str
    step_id: str
    request_type: str
    title: str
    description: str | None
    context: dict[str, Any] | None
    risk_level: str
    status: str
    created_at: datetime
    expires_at: datetime | None
    decided_at: datetime | None
    decided_by: str | None

    class Config:
        from_attributes = True


class ApprovalDecisionResponse(BaseModel):
    """Schema for approval decision response."""

    id: str
    request_id: str
    decision: str
    reason: str | None
    decided_by: str
    decided_at: datetime

    class Config:
        from_attributes = True


class ApprovalStats(BaseModel):
    """Approval statistics."""

    total_requests: int
    pending: int
    approved: int
    denied: int
    timed_out: int
    approval_rate: float
    average_decision_time_minutes: float


class PendingApproval(BaseModel):
    """Pending approval for polling."""

    request_id: str
    execution_id: str
    step_id: str
    title: str
    description: str | None
    risk_level: str
    created_at: datetime
    expires_at: datetime | None
    request_type: str
