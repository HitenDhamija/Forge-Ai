"""Checkpoint Manager for Execution Engine.

Manages execution checkpoints for rollback support.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from app.core.logging import get_logger

logger = get_logger(__name__)


class CheckpointType(str, Enum):
    """Checkpoint types."""

    FILE_SNAPSHOT = "file_snapshot"
    GIT_COMMIT = "git_commit"
    DATABASE_STATE = "database_state"
    CONFIGURATION = "configuration"


@dataclass
class Checkpoint:
    """Execution checkpoint."""

    checkpoint_id: str
    execution_id: str
    step_id: str
    checkpoint_type: CheckpointType
    description: str
    data: dict[str, Any]
    git_commit_hash: str | None = None
    branch_name: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class CheckpointManager:
    """Manages execution checkpoints."""

    def __init__(self):
        """Initialize checkpoint manager."""
        self._checkpoints: dict[str, list[Checkpoint]] = {}

    async def create_checkpoint(
        self,
        execution_id: str,
        step_id: str,
        checkpoint_type: CheckpointType,
        description: str,
        data: dict[str, Any],
        git_commit_hash: str | None = None,
        branch_name: str | None = None,
    ) -> Checkpoint:
        """Create a checkpoint.

        Args:
            execution_id: Execution identifier.
            step_id: Step identifier.
            checkpoint_type: Type of checkpoint.
            description: Checkpoint description.
            data: Checkpoint data.
            git_commit_hash: Optional git commit hash.
            branch_name: Optional branch name.

        Returns:
            Created checkpoint.
        """
        checkpoint_id = str(uuid.uuid4())

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            execution_id=execution_id,
            step_id=step_id,
            checkpoint_type=checkpoint_type,
            description=description,
            data=data,
            git_commit_hash=git_commit_hash,
            branch_name=branch_name,
        )

        if execution_id not in self._checkpoints:
            self._checkpoints[execution_id] = []

        self._checkpoints[execution_id].append(checkpoint)

        logger.info(
            "Checkpoint created: id=%s, execution=%s, type=%s",
            checkpoint_id[:8],
            execution_id[:8],
            checkpoint_type.value,
        )

        return checkpoint

    async def get_checkpoint(
        self,
        execution_id: str,
        checkpoint_id: str,
    ) -> Checkpoint | None:
        """Get checkpoint."""
        checkpoints = self._checkpoints.get(execution_id, [])
        for cp in checkpoints:
            if cp.checkpoint_id == checkpoint_id:
                return cp
        return None

    async def get_latest_checkpoint(
        self,
        execution_id: str,
    ) -> Checkpoint | None:
        """Get latest checkpoint for execution."""
        checkpoints = self._checkpoints.get(execution_id, [])
        return checkpoints[-1] if checkpoints else None

    async def get_checkpoints(
        self,
        execution_id: str,
    ) -> list[Checkpoint]:
        """Get all checkpoints for execution."""
        return self._checkpoints.get(execution_id, [])

    async def rollback_to_checkpoint(
        self,
        execution_id: str,
        checkpoint_id: str,
    ) -> dict[str, Any]:
        """Rollback to specific checkpoint.

        Args:
            execution_id: Execution identifier.
            checkpoint_id: Checkpoint to rollback to.

        Returns:
            Rollback result.
        """
        checkpoint = await self.get_checkpoint(execution_id, checkpoint_id)
        if not checkpoint:
            return {"success": False, "error": "Checkpoint not found"}

        logger.info(
            "Rolling back to checkpoint: id=%s, execution=%s",
            checkpoint_id[:8],
            execution_id[:8],
        )

        # Return rollback instructions
        return {
            "success": True,
            "checkpoint": {
                "id": checkpoint.checkpoint_id,
                "type": checkpoint.checkpoint_type.value,
                "description": checkpoint.description,
                "git_commit_hash": checkpoint.git_commit_hash,
                "branch_name": checkpoint.branch_name,
            },
            "rollback_data": checkpoint.data,
        }

    async def delete_checkpoints(self, execution_id: str) -> None:
        """Delete all checkpoints for execution."""
        self._checkpoints.pop(execution_id, None)
        logger.info("Deleted checkpoints for execution %s", execution_id[:8])
