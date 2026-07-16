"""Approval API Endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import Any

from app.core.dependencies import get_current_user
from app.approval.approval_engine import ApprovalEngine
from app.approval.schemas import (
    ApprovalRequestCreate,
    ApprovalDecisionCreate,
    ApprovalRequestResponse,
    ApprovalDecisionResponse,
    PendingApproval,
    ApprovalStats,
)

router = APIRouter()


def get_approval_engine(request: Request) -> ApprovalEngine:
    return request.app.state.approval_engine


class CreateApprovalRequest(BaseModel):
    """Request to create approval request."""

    execution_id: str
    step_id: str
    request_type: str = Field(..., description="Type: auth, database, file_delete, dependency, general")
    title: str
    description: str | None = None
    context: dict[str, Any] | None = None
    risk_level: str = Field(default="medium", description="low, medium, high, critical")
    timeout_minutes: int | None = Field(default=None, description="Timeout in minutes")


class DecideApprovalRequest(BaseModel):
    """Request to decide on approval."""

    decision: str = Field(..., description="approved or denied")
    reason: str | None = None
    decided_by: str = Field(default="human", description="Who made the decision")


class PendingApprovalsResponse(BaseModel):
    """Pending approvals response."""

    execution_id: str
    pending: list[PendingApproval]
    total: int


@router.post("/approval/request", response_model=ApprovalRequestResponse)
async def create_approval(
    request: Request,
    body: CreateApprovalRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create approval request."""
    engine = get_approval_engine(request)

    data = ApprovalRequestCreate(
        execution_id=body.execution_id,
        step_id=body.step_id,
        request_type=body.request_type,
        title=body.title,
        description=body.description,
        context=body.context,
        risk_level=body.risk_level,
        timeout_minutes=body.timeout_minutes,
    )

    req = await engine.create_request(data)

    return ApprovalRequestResponse(
        id=req.id,
        execution_id=req.execution_id,
        step_id=req.step_id,
        request_type=req.request_type,
        title=req.title,
        description=req.description,
        context=req.context,
        risk_level=req.risk_level,
        status=req.status,
        created_at=req.created_at,
        expires_at=req.expires_at,
        decided_at=req.decided_at,
        decided_by=req.decided_by,
    )


@router.post("/approval/{request_id}/decide", response_model=ApprovalDecisionResponse)
async def decide_approval(
    request: Request,
    request_id: str,
    body: DecideApprovalRequest,
    current_user: dict = Depends(get_current_user),
):
    """Decide on approval request."""
    engine = get_approval_engine(request)

    data = ApprovalDecisionCreate(
        decision=body.decision,
        reason=body.reason,
        decided_by=body.decided_by,
    )

    try:
        decision = await engine.decide(request_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ApprovalDecisionResponse(
        id=decision.id,
        request_id=decision.request_id,
        decision=decision.decision,
        reason=decision.reason,
        decided_by=decision.decided_by,
        decided_at=decision.decided_at,
    )


@router.get("/approval/{request_id}", response_model=ApprovalRequestResponse)
async def get_approval(
    request: Request,
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get approval request."""
    engine = get_approval_engine(request)

    req = await engine.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    return ApprovalRequestResponse(
        id=req.id,
        execution_id=req.execution_id,
        step_id=req.step_id,
        request_type=req.request_type,
        title=req.title,
        description=req.description,
        context=req.context,
        risk_level=req.risk_level,
        status=req.status,
        created_at=req.created_at,
        expires_at=req.expires_at,
        decided_at=req.decided_at,
        decided_by=req.decided_by,
    )


@router.get("/approval/pending/{execution_id}", response_model=PendingApprovalsResponse)
async def get_pending_approvals(
    request: Request,
    execution_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get pending approvals for execution."""
    engine = get_approval_engine(request)

    pending = await engine.get_pending_for_execution(execution_id)

    return PendingApprovalsResponse(
        execution_id=execution_id,
        pending=pending,
        total=len(pending),
    )


@router.post("/approval/{request_id}/cancel")
async def cancel_approval(
    request: Request,
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel pending approval request."""
    engine = get_approval_engine(request)

    cancelled = await engine.cancel_request(request_id)
    if not cancelled:
        raise HTTPException(status_code=400, detail="Cannot cancel request")

    return {"success": True, "message": "Request cancelled"}


@router.get("/approval/stats", response_model=ApprovalStats)
async def get_approval_stats(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get approval statistics."""
    engine = get_approval_engine(request)

    stats = await engine.get_stats()
    return stats


@router.post("/approval/auto-approve")
async def set_auto_approve(
    request: Request,
    enabled: bool = True,
    current_user: dict = Depends(get_current_user),
):
    """Enable/disable auto-approval mode."""
    engine = get_approval_engine(request)

    engine.set_auto_approve(enabled)

    return {
        "success": True,
        "auto_approve": enabled,
        "message": "Auto-approve " + ("enabled" if enabled else "disabled"),
    }
