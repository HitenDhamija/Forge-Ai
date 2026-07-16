"""Approval Engine - Core approval logic.

Manages approval requests, decisions, and integration with execution.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger
from app.approval.models import (
    ApprovalRequest as ApprovalRequestModel,
    ApprovalDecision as ApprovalDecisionModel,
    ApprovalStatusDB,
)
from app.approval.schemas import (
    ApprovalRequestCreate,
    ApprovalDecisionCreate,
    ApprovalRequestResponse,
    ApprovalDecisionResponse,
    PendingApproval,
    ApprovalStats,
)

logger = get_logger(__name__)


# Timeout configuration per request type (in minutes)
TIMEOUT_CONFIG: dict[str, int | None] = {
    "auth": None,  # Never timeout for auth changes
    "database": 30,  # 30 minutes for DB migrations
    "file_delete": 15,  # 15 minutes for file deletions
    "dependency": 20,  # 20 minutes for dependency updates
    "file_modify": 10,  # 10 minutes for file modifications
    "general": 15,  # 15 minutes default
}

# Risk level scoring
RISK_SCORES: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


class ApprovalEngine:
    """Core approval engine.

    Responsibilities:
    - Create approval requests
    - Process approval/denial decisions
    - Check approval status
    - Manage timeouts
    - Auto-approve if configured
    """

    def __init__(self):
        """Initialize approval engine."""
        self._requests: dict[str, ApprovalRequestModel] = {}
        self._decisions: dict[str, ApprovalDecisionModel] = {}
        self._executions: dict[str, list[str]] = {}  # execution_id -> [request_ids]
        self._auto_approve: bool = False
        logger.info("Approval engine initialized")

    def set_auto_approve(self, enabled: bool) -> None:
        """Enable/disable auto-approval mode."""
        self._auto_approve = enabled
        logger.info("Auto-approve mode: %s", "enabled" if enabled else "disabled")

    async def create_request(
        self,
        data: ApprovalRequestCreate,
    ) -> ApprovalRequestModel:
        """Create approval request.

        Args:
            data: Request data.

        Returns:
            Created request.
        """
        request_id = str(uuid.uuid4())

        # Determine timeout from config
        timeout_minutes = data.timeout_minutes
        if timeout_minutes is None:
            timeout_minutes = TIMEOUT_CONFIG.get(data.request_type, TIMEOUT_CONFIG["general"])

        expires_at = None
        if timeout_minutes is not None:
            expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)

        request = ApprovalRequestModel(
            id=request_id,
            execution_id=data.execution_id,
            step_id=data.step_id,
            request_type=data.request_type,
            title=data.title,
            description=data.description,
            context=data.context,
            risk_level=data.risk_level,
            status=ApprovalStatusDB.PENDING.value,
            expires_at=expires_at,
        )

        self._requests[request_id] = request

        # Track by execution
        if data.execution_id not in self._executions:
            self._executions[data.execution_id] = []
        self._executions[data.execution_id].append(request_id)

        logger.info(
            "Approval request created: id=%s, type=%s, risk=%s",
            request_id[:8],
            data.request_type,
            data.risk_level,
        )

        return request

    async def decide(
        self,
        request_id: str,
        data: ApprovalDecisionCreate,
    ) -> ApprovalDecisionModel:
        """Process approval decision.

        Args:
            request_id: Request identifier.
            data: Decision data.

        Returns:
            Created decision.

        Raises:
            ValueError: If request not found or already decided.
        """
        request = self._requests.get(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")

        if request.status != ApprovalStatusDB.PENDING.value:
            raise ValueError(f"Request already decided: {request.status}")

        decision_id = str(uuid.uuid4())

        decision = ApprovalDecisionModel(
            id=decision_id,
            request_id=request_id,
            decision=data.decision,
            reason=data.reason,
            decided_by=data.decided_by,
        )

        self._decisions[decision_id] = decision

        # Update request
        request.status = ApprovalStatusDB.APPROVED.value if data.decision == "approved" else ApprovalStatusDB.DENIED.value
        request.decided_at = datetime.utcnow()
        request.decided_by = data.decided_by

        logger.info(
            "Approval decision: request=%s, decision=%s, by=%s",
            request_id[:8],
            data.decision,
            data.decided_by,
        )

        return decision

    async def check_timeout(self, request_id: str) -> bool:
        """Check if request has timed out.

        Args:
            request_id: Request identifier.

        Returns:
            True if timed out.
        """
        request = self._requests.get(request_id)
        if not request:
            return False

        if request.status != ApprovalStatusDB.PENDING.value:
            return False

        if request.expires_at and datetime.utcnow() > request.expires_at:
            request.status = ApprovalStatusDB.TIMEOUT.value
            request.decided_at = datetime.utcnow()
            logger.info("Approval request timed out: %s", request_id[:8])
            return True

        return False

    async def cancel_request(self, request_id: str) -> bool:
        """Cancel a pending request.

        Args:
            request_id: Request identifier.

        Returns:
            True if cancelled.
        """
        request = self._requests.get(request_id)
        if not request:
            return False

        if request.status != ApprovalStatusDB.PENDING.value:
            return False

        request.status = ApprovalStatusDB.CANCELLED.value
        request.decided_at = datetime.utcnow()
        logger.info("Approval request cancelled: %s", request_id[:8])
        return True

    async def get_request(self, request_id: str) -> ApprovalRequestModel | None:
        """Get request by ID."""
        return self._requests.get(request_id)

    async def get_pending_for_execution(self, execution_id: str) -> list[PendingApproval]:
        """Get all pending approvals for an execution.

        Args:
            execution_id: Execution identifier.

        Returns:
            List of pending approvals.
        """
        request_ids = self._executions.get(execution_id, [])
        pending = []

        for req_id in request_ids:
            request = self._requests.get(req_id)
            if not request:
                continue

            # Check timeout
            await self.check_timeout(req_id)

            if request.status == ApprovalStatusDB.PENDING.value:
                pending.append(PendingApproval(
                    request_id=request.id,
                    execution_id=request.execution_id,
                    step_id=request.step_id,
                    title=request.title,
                    description=request.description,
                    risk_level=request.risk_level,
                    created_at=request.created_at,
                    expires_at=request.expires_at,
                    request_type=request.request_type,
                ))

        return pending

    async def get_stats(self) -> ApprovalStats:
        """Get approval statistics.

        Returns:
            Approval statistics.
        """
        all_requests = list(self._requests.values())
        total = len(all_requests)

        if total == 0:
            return ApprovalStats(
                total_requests=0,
                pending=0,
                approved=0,
                denied=0,
                timed_out=0,
                approval_rate=0.0,
                average_decision_time_minutes=0.0,
            )

        pending = sum(1 for r in all_requests if r.status == ApprovalStatusDB.PENDING.value)
        approved = sum(1 for r in all_requests if r.status == ApprovalStatusDB.APPROVED.value)
        denied = sum(1 for r in all_requests if r.status == ApprovalStatusDB.DENIED.value)
        timed_out = sum(1 for r in all_requests if r.status == ApprovalStatusDB.TIMEOUT.value)

        approval_rate = (approved / (approved + denied)) * 100 if (approved + denied) > 0 else 0.0

        # Calculate average decision time
        decision_times = []
        for r in all_requests:
            if r.decided_at and r.created_at:
                delta = (r.decided_at - r.created_at).total_seconds() / 60
                decision_times.append(delta)

        avg_time = sum(decision_times) / len(decision_times) if decision_times else 0.0

        return ApprovalStats(
            total_requests=total,
            pending=pending,
            approved=approved,
            denied=denied,
            timed_out=timed_out,
            approval_rate=round(approval_rate, 1),
            average_decision_time_minutes=round(avg_time, 1),
        )

    async def get_decision(self, request_id: str) -> ApprovalDecisionModel | None:
        """Get decision for a request."""
        for decision in self._decisions.values():
            if decision.request_id == request_id:
                return decision
        return None

    async def is_approved(self, request_id: str) -> bool:
        """Check if a request was approved."""
        request = self._requests.get(request_id)
        if not request:
            return False
        return request.status == ApprovalStatusDB.APPROVED.value
