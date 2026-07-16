"""Rollback Engine for Execution Engine.

Handles rollback operations when execution fails.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class RollbackStatus(str, Enum):
    """Rollback status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RollbackOperation:
    """Single rollback operation."""

    operation_id: str
    operation_type: str
    target: str
    original_state: dict[str, Any]
    status: RollbackStatus = RollbackStatus.PENDING
    error: str | None = None


@dataclass
class RollbackResult:
    """Complete rollback result."""

    execution_id: str
    status: RollbackStatus
    operations: list[RollbackOperation]
    summary: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class RollbackEngine:
    """Handles rollback operations."""

    def __init__(self):
        """Initialize rollback engine."""
        self._rollbacks: dict[str, RollbackResult] = {}

    async def rollback(
        self,
        execution_id: str,
        checkpoint_data: dict[str, Any],
        files_modified: list[str],
        git_branch: str | None = None,
        git_commit: str | None = None,
    ) -> RollbackResult:
        """Execute rollback.

        Args:
            execution_id: Execution identifier.
            checkpoint_data: Checkpoint data to restore.
            files_modified: List of modified files.
            git_branch: Git branch to rollback.
            git_commit: Git commit to rollback to.

        Returns:
            Rollback result.
        """
        logger.info("Starting rollback for execution %s", execution_id[:8])

        operations = []

        # Rollback files
        for file_path in files_modified:
            op = RollbackOperation(
                operation_id=f"rollback-file-{file_path}",
                operation_type="file_rollback",
                target=file_path,
                original_state=checkpoint_data.get(file_path, {}),
            )
            operations.append(op)

        # Rollback git if needed
        if git_branch and git_commit:
            op = RollbackOperation(
                operation_id=f"rollback-git-{git_branch}",
                operation_type="git_rollback",
                target=git_branch,
                original_state={"commit": git_commit},
            )
            operations.append(op)

        # Execute rollback operations
        for op in operations:
            try:
                await self._execute_rollback_operation(op)
                op.status = RollbackStatus.COMPLETED
            except Exception as e:
                op.status = RollbackStatus.FAILED
                op.error = str(e)
                logger.error("Rollback operation failed: %s", str(e))

        # Determine overall status
        all_completed = all(op.status == RollbackStatus.COMPLETED for op in operations)
        any_failed = any(op.status == RollbackStatus.FAILED for op in operations)

        if all_completed:
            status = RollbackStatus.COMPLETED
        elif any_failed:
            status = RollbackStatus.FAILED
        else:
            status = RollbackStatus.IN_PROGRESS

        result = RollbackResult(
            execution_id=execution_id,
            status=status,
            operations=operations,
            summary=self._generate_summary(operations),
            completed_at=datetime.utcnow(),
        )

        self._rollbacks[execution_id] = result

        logger.info(
            "Rollback completed: execution=%s, status=%s, operations=%d",
            execution_id[:8],
            status.value,
            len(operations),
        )

        return result

    async def _execute_rollback_operation(
        self,
        operation: RollbackOperation,
    ) -> None:
        """Execute single rollback operation."""
        if operation.operation_type == "file_rollback":
            await self._rollback_file(operation)
        elif operation.operation_type == "git_rollback":
            await self._rollback_git(operation)

    async def _rollback_file(self, operation: RollbackOperation) -> None:
        """Rollback file changes."""
        # Integration with filesystem MCP
        logger.info("Rolling back file: %s", operation.target)

    async def _rollback_git(self, operation: RollbackOperation) -> None:
        """Rollback git changes."""
        # Integration with git MCP
        logger.info("Rolling back git: %s", operation.target)

    def _generate_summary(self, operations: list[RollbackOperation]) -> str:
        """Generate rollback summary."""
        completed = sum(1 for op in operations if op.status == RollbackStatus.COMPLETED)
        failed = sum(1 for op in operations if op.status == RollbackStatus.FAILED)

        return f"Rolled back {completed} operations, {failed} failed"

    def get_rollback(self, execution_id: str) -> RollbackResult | None:
        """Get rollback result."""
        return self._rollbacks.get(execution_id)
