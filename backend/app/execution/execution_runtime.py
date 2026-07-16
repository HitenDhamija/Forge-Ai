"""Execution Runtime for Execution Engine.

Main orchestrator for controlled execution.
"""

import os
from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

from app.core.logging import get_logger
from app.execution.dispatcher import Dispatcher, AgentType, DispatchedTask
from app.execution.checkpoint_manager import CheckpointManager, CheckpointType
from app.execution.rollback_engine import RollbackEngine, RollbackStatus
from app.infrastructure.notifications import notify_task_completed, notify_task_failed
from app.execution.validation_engine import ValidationEngine
from app.execution.execution_logger import ExecutionLogger, LogLevel
from app.execution.progress_tracker import ProgressTracker, TaskStatus
from app.execution.execution_summary import ExecutionSummaryGenerator, ExecutionSummary
from app.approval.approval_engine import ApprovalEngine
from app.approval.schemas import ApprovalRequestCreate

logger = get_logger(__name__)


class ExecutionStatus(str, Enum):
    """Execution status."""

    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


@dataclass
class ExecutionStep:
    """Single execution step."""

    step_id: str
    task_id: str
    agent_type: AgentType
    description: str
    parameters: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    requires_approval: bool = False
    status: str = "pending"
    result: dict[str, Any] | None = None


@dataclass
class Execution:
    """Complete execution."""

    execution_id: str
    workflow_id: str
    repository_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    steps: list[ExecutionStep] = field(default_factory=list)
    current_step: str | None = None
    files_modified: list[str] = field(default_factory=list)
    files_created: list[str] = field(default_factory=list)
    files_deleted: list[str] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    summary: ExecutionSummary | None = None


class ExecutionRuntime:
    """Main execution runtime.

    Responsibilities:
    - Load approved workflow
    - Validate approvals
    - Load execution context
    - Dispatch tasks
    - Track progress
    - Pause/Resume/Cancel execution
    - Generate execution logs
    """

    def __init__(self, approval_engine: ApprovalEngine | None = None):
        """Initialize execution runtime.

        Args:
            approval_engine: Optional approval engine for human-in-the-loop.
        """
        self.dispatcher = Dispatcher()
        self.checkpoint_manager = CheckpointManager()
        self.rollback_engine = RollbackEngine()
        self.validation_engine = ValidationEngine()
        self.logger = ExecutionLogger()
        self.progress_tracker = ProgressTracker()
        self.summary_generator = ExecutionSummaryGenerator()
        self.approval_engine = approval_engine
        self._executions: dict[str, Execution] = {}
        self._pending_approvals: dict[str, str] = {}  # step_id -> request_id
        self._approval_results: dict[str, bool] = {}  # step_id -> approved

    async def start_execution(
        self,
        workflow_id: str,
        repository_id: str,
        steps: list[dict[str, Any]],
    ) -> Execution:
        """Start execution.

        Args:
            workflow_id: Workflow identifier.
            repository_id: Repository identifier.
            steps: Execution steps.

        Returns:
            Execution context.
        """
        execution_id = str(uuid.uuid4())

        execution = Execution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            repository_id=repository_id,
        )

        # Create execution steps
        for i, step_data in enumerate(steps):
            step = ExecutionStep(
                step_id=f"step-{i + 1}",
                task_id=step_data.get("task_id", str(uuid.uuid4())),
                agent_type=AgentType(step_data.get("agent_type", "software_engineer")),
                description=step_data.get("description", ""),
                parameters=step_data.get("parameters", {}),
                dependencies=step_data.get("dependencies", []),
                requires_approval=step_data.get("requires_approval", False),
            )
            execution.steps.append(step)

        self._executions[execution_id] = execution

        # Initialize logging
        self.logger.create_log(execution_id)

        # Initialize progress
        self.progress_tracker.create_progress(execution_id, len(steps))

        logger.info(
            "Execution started: id=%s, workflow=%s, steps=%d",
            execution_id[:8],
            workflow_id[:8],
            len(steps),
        )

        self.logger.log(
            execution_id,
            LogLevel.INFO,
            f"Execution started with {len(steps)} steps",
        )

        return execution

    async def run_execution(
        self,
        execution_id: str,
    ) -> Execution:
        """Run execution.

        Args:
            execution_id: Execution identifier.

        Returns:
            Updated execution.
        """
        execution = self._executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution not found: {execution_id}")

        execution.status = ExecutionStatus.RUNNING
        self.progress_tracker.update_execution_status(execution_id, "running")

        self.logger.log(execution_id, LogLevel.INFO, "Execution started")

        try:
            # Create initial checkpoint
            await self.checkpoint_manager.create_checkpoint(
                execution_id=execution_id,
                step_id="start",
                checkpoint_type=CheckpointType.GIT_COMMIT,
                description="Initial checkpoint before execution",
                data={"files": execution.files_modified},
            )

            # Execute steps in order
            for step in execution.steps:
                # Check dependencies
                if not await self._check_dependencies(execution, step):
                    self.logger.log(
                        execution_id,
                        LogLevel.WARNING,
                        f"Skipping step {step.step_id} due to unmet dependencies",
                    )
                    continue

                # Check if paused
                if execution.status == ExecutionStatus.PAUSED:
                    self.logger.log(execution_id, LogLevel.INFO, "Execution paused")
                    break

                # Execute step
                await self._execute_step(execution, step)

            # Generate summary
            if execution.status != ExecutionStatus.PAUSED:
                execution.status = ExecutionStatus.COMPLETED
                execution.completed_at = datetime.utcnow()

                execution.summary = await self.summary_generator.generate(
                    execution_id=execution_id,
                    workflow_id=execution.workflow_id,
                    status="completed",
                    tasks=[
                        {"status": step.status, "description": step.description}
                        for step in execution.steps
                    ],
                    files_modified=execution.files_modified,
                    files_created=execution.files_created,
                    files_deleted=execution.files_deleted,
                    commits=execution.commits,
                    warnings=execution.warnings,
                    errors=execution.errors,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                )

                self.logger.log(execution_id, LogLevel.INFO, "Execution completed")
                self.progress_tracker.update_execution_status(execution_id, "completed")

                completed_count = sum(1 for s in execution.steps if s.status == "completed")
                notify_task_completed(os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"), f"Execution {execution_id[:8]}", execution_id,
                                     f"{completed_count}/{len(execution.steps)} steps completed")

        except Exception as e:
            logger.error("Execution failed: %s", str(e))
            execution.status = ExecutionStatus.FAILED
            execution.errors.append(str(e))
            execution.completed_at = datetime.utcnow()

            self.logger.log(execution_id, LogLevel.ERROR, f"Execution failed: {str(e)}")
            self.progress_tracker.update_execution_status(execution_id, "failed")

            notify_task_failed(os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"), f"Execution {execution_id[:8]}", execution_id, str(e))

            # Auto rollback on failure
            await self._auto_rollback(execution)

        self.logger.complete_log(execution_id)

        return execution

    async def pause_execution(
        self,
        execution_id: str,
    ) -> Execution | None:
        """Pause execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return None

        if execution.status != ExecutionStatus.RUNNING:
            return None

        execution.status = ExecutionStatus.PAUSED
        self.progress_tracker.update_execution_status(execution_id, "paused")
        self.logger.log(execution_id, LogLevel.INFO, "Execution paused")

        logger.info("Execution paused: %s", execution_id[:8])
        return execution

    async def resume_execution(
        self,
        execution_id: str,
    ) -> Execution | None:
        """Resume execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return None

        if execution.status != ExecutionStatus.PAUSED:
            return None

        execution.status = ExecutionStatus.RUNNING
        self.progress_tracker.update_execution_status(execution_id, "running")
        self.logger.log(execution_id, LogLevel.INFO, "Execution resumed")

        # Continue execution
        return await self.run_execution(execution_id)

    async def cancel_execution(
        self,
        execution_id: str,
    ) -> Execution | None:
        """Cancel execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return None

        execution.status = ExecutionStatus.FAILED
        execution.completed_at = datetime.utcnow()
        self.progress_tracker.update_execution_status(execution_id, "cancelled")
        self.logger.log(execution_id, LogLevel.INFO, "Execution cancelled")

        logger.info("Execution cancelled: %s", execution_id[:8])
        return execution

    async def rollback_execution(
        self,
        execution_id: str,
    ) -> dict[str, Any]:
        """Rollback execution."""
        execution = self._executions.get(execution_id)
        if not execution:
            return {"success": False, "error": "Execution not found"}

        execution.status = ExecutionStatus.ROLLING_BACK
        self.logger.log(execution_id, LogLevel.INFO, "Starting rollback")

        # Get latest checkpoint
        checkpoint = await self.checkpoint_manager.get_latest_checkpoint(execution_id)
        if not checkpoint:
            return {"success": False, "error": "No checkpoint available"}

        # Execute rollback
        result = await self.rollback_engine.rollback(
            execution_id=execution_id,
            checkpoint_data=checkpoint.data,
            files_modified=execution.files_modified,
            git_branch=checkpoint.branch_name,
            git_commit=checkpoint.git_commit_hash,
        )

        if result.status == RollbackStatus.COMPLETED:
            execution.status = ExecutionStatus.ROLLED_BACK
            self.logger.log(execution_id, LogLevel.INFO, "Rollback completed")
        else:
            execution.status = ExecutionStatus.FAILED
            self.logger.log(execution_id, LogLevel.ERROR, "Rollback failed")

        return {
            "success": result.status == RollbackStatus.COMPLETED,
            "message": result.summary,
        }

    async def _execute_step(
        self,
        execution: Execution,
        step: ExecutionStep,
    ) -> None:
        """Execute single step."""
        self.logger.log(
            execution.execution_id,
            LogLevel.INFO,
            f"Executing step: {step.description}",
            step_id=step.step_id,
        )

        self.progress_tracker.update_task(
            execution.execution_id,
            step.task_id,
            status=TaskStatus.RUNNING,
        )

        execution.current_step = step.step_id

        # Check if approval required
        if step.requires_approval:
            if self.approval_engine:
                self.logger.log(
                    execution.execution_id,
                    LogLevel.INFO,
                    f"Step requires approval: {step.description}",
                )
                self.progress_tracker.update_task(
                    execution.execution_id,
                    step.task_id,
                    status=TaskStatus.WAITING_APPROVAL,
                )

                # Create approval request
                request = await self.approval_engine.create_request(
                    ApprovalRequestCreate(
                        execution_id=execution.execution_id,
                        step_id=step.step_id,
                        request_type=self._get_request_type(step),
                        title=f"Approve: {step.description}",
                        description=f"Execution step requires approval before proceeding.",
                        context={
                            "agent_type": step.agent_type.value,
                            "parameters": step.parameters,
                        },
                        risk_level=self._get_risk_level(step),
                    )
                )

                self._pending_approvals[step.step_id] = request.id

                # Wait for approval (polling)
                approved = await self._wait_for_approval(step.step_id)

                if approved:
                    self.logger.log(
                        execution.execution_id,
                        LogLevel.INFO,
                        f"Step approved: {step.description}",
                    )
                else:
                    self.logger.log(
                        execution.execution_id,
                        LogLevel.WARNING,
                        f"Step denied: {step.description}",
                    )
                    step.status = "skipped"
                    self.progress_tracker.update_task(
                        execution.execution_id,
                        step.task_id,
                        status=TaskStatus.SKIPPED,
                    )
                    return
            else:
                # No approval engine, auto-skip
                self.logger.log(
                    execution.execution_id,
                    LogLevel.WARNING,
                    f"Step requires approval but no approval engine: {step.description}",
                )
                step.status = "skipped"
                return

        # Dispatch to agent
        task = await self.dispatcher.dispatch(
            execution_id=execution.execution_id,
            task_id=step.task_id,
            agent_type=step.agent_type,
            description=step.description,
            parameters=step.parameters,
            dependencies=step.dependencies,
        )

        # Execute task
        result = await self.dispatcher.execute_task(
            execution.execution_id,
            step.task_id,
        )

        step.status = "completed" if result.get("success") else "failed"
        step.result = result

        if result.get("success"):
            self.progress_tracker.update_task(
                execution.execution_id,
                step.task_id,
                status=TaskStatus.COMPLETED,
                progress=100.0,
            )
        else:
            self.progress_tracker.update_task(
                execution.execution_id,
                step.task_id,
                status=TaskStatus.FAILED,
                error=result.get("error"),
            )

    def _get_request_type(self, step: ExecutionStep) -> str:
        """Determine request type from step."""
        desc = step.description.lower()
        if "auth" in desc or "login" in desc or "password" in desc:
            return "auth"
        elif "database" in desc or "migration" in desc or "sql" in desc:
            return "database"
        elif "delete" in desc or "remove" in desc:
            return "file_delete"
        elif "depend" in desc or "package" in desc or "npm" in desc:
            return "dependency"
        else:
            return "file_modify"

    def _get_risk_level(self, step: ExecutionStep) -> str:
        """Determine risk level from step."""
        desc = step.description.lower()
        if "delete" in desc or "remove" in desc or "drop" in desc:
            return "critical"
        elif "auth" in desc or "security" in desc or "password" in desc:
            return "high"
        elif "database" in desc or "migration" in desc:
            return "high"
        else:
            return "medium"

    async def _wait_for_approval(self, step_id: str, timeout: int = 300) -> bool:
        """Wait for approval decision.

        Args:
            step_id: Step to wait for.
            timeout: Maximum wait time in seconds.

        Returns:
            True if approved.
        """
        import asyncio

        elapsed = 0
        poll_interval = 1

        while elapsed < timeout:
            # Check if decision was made
            if step_id in self._approval_results:
                return self._approval_results[step_id]

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # Timeout - deny by default
        return False

    async def approve_step(
        self,
        execution_id: str,
        step_id: str,
        approved: bool,
        reason: str | None = None,
        decided_by: str = "human",
    ) -> bool:
        """Approve or deny a step.

        Args:
            execution_id: Execution identifier.
            step_id: Step identifier.
            approved: Whether approved.
            reason: Optional reason.
            decided_by: Who decided.

        Returns:
            True if decision recorded.
        """
        request_id = self._pending_approvals.get(step_id)
        if not request_id:
            return False

        if self.approval_engine:
            from app.approval.schemas import ApprovalDecisionCreate

            decision = "approved" if approved else "denied"
            await self.approval_engine.decide(
                request_id,
                ApprovalDecisionCreate(
                    decision=decision,
                    reason=reason,
                    decided_by=decided_by,
                ),
            )

        # Store result for polling
        self._approval_results[step_id] = approved

        # Clean up
        self._pending_approvals.pop(step_id, None)

        return True

    def get_pending_approvals(self, execution_id: str) -> list[str]:
        """Get pending approval step IDs."""
        return [
            step_id
            for step_id, req_id in self._pending_approvals.items()
        ]

    async def _check_dependencies(
        self,
        execution: Execution,
        step: ExecutionStep,
    ) -> bool:
        """Check if dependencies are met."""
        if not step.dependencies:
            return True

        for dep_id in step.dependencies:
            dep_step = next(
                (s for s in execution.steps if s.step_id == dep_id),
                None,
            )
            if not dep_step or dep_step.status != "completed":
                return False

        return True

    async def _auto_rollback(self, execution: Execution) -> None:
        """Auto rollback on failure."""
        if execution.files_modified or execution.files_created:
            self.logger.log(
                execution.execution_id,
                LogLevel.INFO,
                "Auto rollback triggered",
            )
            await self.rollback_execution(execution.execution_id)

    def get_execution(self, execution_id: str) -> Execution | None:
        """Get execution."""
        return self._executions.get(execution_id)

    def list_executions(
        self,
        status: ExecutionStatus | None = None,
    ) -> list[Execution]:
        """List executions."""
        executions = list(self._executions.values())
        if status:
            executions = [e for e in executions if e.status == status]
        return executions
