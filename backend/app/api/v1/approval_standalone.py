"""Standalone approval API — matches frontend ExecutionCenter expectations."""

import uuid
from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/approval", tags=["Approval"])

_pending_approvals: list[dict[str, Any]] = []


class ApprovalRequest(BaseModel):
    workflow_id: str | None = None
    execution_id: str | None = None
    action: str
    description: str = ""


# Frontend calls GET /approval/pending/{executionId}
@router.get("/pending")
@router.get("/pending/{execution_id}")
async def get_pending(execution_id: str | None = None):
    if execution_id:
        items = [a for a in _pending_approvals if a.get("execution_id") == execution_id]
    else:
        items = _pending_approvals
    return {"status": "success", "data": items}


# Frontend calls POST /approval/{requestId}/decide
@router.post("/{request_id}/decide")
async def decide(request_id: str, data: dict[str, Any]):
    decision = data.get("decision", "approved")
    reason = data.get("reason", "")

    # Remove from pending
    global _pending_approvals
    _pending_approvals = [a for a in _pending_approvals if a["id"] != request_id]

    result = {
        "id": request_id,
        "decision": decision,
        "reason": reason,
        "decided_at": datetime.now(UTC).isoformat(),
    }
    return {"status": "success", "data": result}


@router.post("/approve")
async def approve(data: dict[str, Any]):
    approval_id = data.get("approval_id", str(uuid.uuid4()))
    global _pending_approvals
    _pending_approvals = [a for a in _pending_approvals if a["id"] != approval_id]

    result = {
        "id": approval_id,
        "status": "approved",
        "approved_at": datetime.now(UTC).isoformat(),
    }
    return {"status": "success", "data": result}


@router.post("/reject")
async def reject(data: dict[str, Any]):
    approval_id = data.get("approval_id", "")
    reason = data.get("reason", "")
    global _pending_approvals
    _pending_approvals = [a for a in _pending_approvals if a["id"] != approval_id]

    result = {
        "id": approval_id,
        "status": "rejected",
        "reason": reason,
        "rejected_at": datetime.now(UTC).isoformat(),
    }
    return {"status": "success", "data": result}


@router.get("/history")
async def get_history():
    return {"status": "success", "data": []}


@router.get("/{approval_id}")
async def get_approval(approval_id: str):
    a = next((a for a in _pending_approvals if a["id"] == approval_id), None)
    if not a:
        return {"status": "error", "message": "Approval not found"}
    return {"status": "success", "data": a}
