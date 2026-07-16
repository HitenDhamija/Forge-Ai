"""Workflow service for managing workflow execution."""

import os
from datetime import datetime, timezone
from typing import Any

from app.workflows.events import WorkflowEventEmitter
from app.workflows.execution_summary import ExecutionSummaryGenerator
from app.workflows.repository import WorkflowRepository
from app.infrastructure.notifications import notify_workflow_approved
from app.workflows.schemas import (
    EventType,
    RiskLevel,
    TaskInfo,
    TaskPriority,
    TaskRequest,
    TaskStatus,
    ValidationResult,
    WorkflowInfo,
    WorkflowRequest,
    WorkflowStatus,
)
from app.workflows.scheduler import TaskScheduler
from app.workflows.state_machine import InvalidTransitionError, TaskStateMachine, WorkflowStateMachine
from app.workflows.validator import WorkflowValidator
from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowService:
    """Service for managing workflow execution.

    The WorkflowService is the main entry point for workflow operations.
    It coordinates between the repository, scheduler, validator, and event system.
    """

    def __init__(self, repository: WorkflowRepository) -> None:
        """Initialize the workflow service.

        Args:
            repository: Workflow repository.
        """
        self.repository = repository
        self.scheduler = TaskScheduler()
        self.validator = WorkflowValidator()
        self.summary_generator = ExecutionSummaryGenerator()
        self._emitters: dict[str, WorkflowEventEmitter] = {}

    async def create_workflow(
        self,
        request: WorkflowRequest,
    ) -> WorkflowInfo:
        """Create a new workflow.

        Args:
            request: Workflow request.

        Returns:
            Created workflow info.

        Raises:
            ValueError: If workflow is invalid.
        """
        task_dicts = [
            {
                "id": f"task_{i}",
                "title": task.title,
                "description": task.description,
                "dependencies": task.dependencies,
            }
            for i, task in enumerate(request.tasks)
        ]

        validation = self.validator.validate(
            tasks=task_dicts,
            requires_approval=request.requires_approval,
            risk_level=request.risk_level.value,
        )

        if not validation.is_valid:
            raise ValueError(
                f"Invalid workflow: {'; '.join(validation.errors)}"
            )

        workflow = await self.repository.create_workflow(
            title=request.title,
            description=request.description,
            project_id=request.project_id,
            requires_approval=request.requires_approval,
            risk_level=request.risk_level.value,
            metadata=request.metadata,
        )

        for i, task_request in enumerate(request.tasks):
            await self.repository.create_task(
                workflow_id=workflow.id,
                title=task_request.title,
                description=task_request.description,
                priority=task_request.priority.value,
                dependencies=task_request.dependencies,
                agent_type=task_request.agent_type,
                estimated_duration=task_request.estimated_duration,
                metadata=task_request.metadata,
            )

        emitter = WorkflowEventEmitter(workflow.id)
        self._emitters[workflow.id] = emitter
        emitter.emit(EventType.WORKFLOW_CREATED, data={"title": request.title})

        if request.requires_approval:
            await self.repository.update_workflow_status(
                workflow.id, WorkflowStatus.WAITING_APPROVAL
            )
            emitter.emit(EventType.APPROVAL_REQUESTED)
        else:
            await self.repository.update_workflow_status(
                workflow.id, WorkflowStatus.READY
            )

        workflow = await self.repository.get_workflow(workflow.id)
        return self._to_workflow_info(workflow)

    async def get_workflow(self, workflow_id: str) -> WorkflowInfo | None:
        """Get workflow by ID.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Workflow info or None.
        """
        workflow = await self.repository.get_workflow(workflow_id)
        if workflow:
            return self._to_workflow_info(workflow)
        return None

    async def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        project_id: str | None = None,
    ) -> list[WorkflowInfo]:
        """List workflows with optional filters.

        Args:
            status: Filter by status.
            project_id: Filter by project ID.

        Returns:
            List of workflow info.
        """
        workflows = await self.repository.list_workflows(
            status=status,
            project_id=project_id,
        )
        return [self._to_workflow_info(w) for w in workflows]

    async def approve_workflow(self, workflow_id: str) -> WorkflowInfo:
        """Approve a workflow for execution.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Updated workflow info.

        Raises:
            InvalidTransitionError: If transition is invalid.
        """
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        current_status = WorkflowStatus(workflow.status)
        WorkflowStateMachine.validate_transition(
            current_status, WorkflowStatus.READY
        )

        await self.repository.update_workflow_status(
            workflow_id, WorkflowStatus.READY
        )

        emitter = self._get_emitter(workflow_id)
        emitter.emit(EventType.APPROVAL_GRANTED)

        notify_workflow_approved(os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"), workflow.name or workflow_id, workflow_id)

        workflow = await self.repository.get_workflow(workflow_id)
        return self._to_workflow_info(workflow)

    async def start_workflow(self, workflow_id: str) -> WorkflowInfo:
        """Start workflow execution.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Updated workflow info.

        Raises:
            InvalidTransitionError: If transition is invalid.
        """
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        current_status = WorkflowStatus(workflow.status)
        WorkflowStateMachine.validate_transition(
            current_status, WorkflowStatus.RUNNING
        )

        await self.repository.update_workflow_status(
            workflow_id, WorkflowStatus.RUNNING
        )

        emitter = self._get_emitter(workflow_id)
        emitter.emit(EventType.WORKFLOW_STARTED)

        queue = self.scheduler.create_queue(workflow_id)

        tasks = await self.repository.get_workflow_tasks(workflow_id)
        for task in tasks:
            queue.add_task(
                task.id,
                TaskPriority(task.priority),
                task.dependencies,
            )

        workflow = await self.repository.get_workflow(workflow_id)
        return self._to_workflow_info(workflow)

    async def pause_workflow(self, workflow_id: str) -> WorkflowInfo:
        """Pause workflow execution.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Updated workflow info.

        Raises:
            InvalidTransitionError: If transition is invalid.
        """
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        current_status = WorkflowStatus(workflow.status)
        WorkflowStateMachine.validate_transition(
            current_status, WorkflowStatus.PAUSED
        )

        await self.repository.update_workflow_status(
            workflow_id, WorkflowStatus.PAUSED
        )

        emitter = self._get_emitter(workflow_id)
        emitter.emit(EventType.WORKFLOW_PAUSED)

        workflow = await self.repository.get_workflow(workflow_id)
        return self._to_workflow_info(workflow)

    async def resume_workflow(self, workflow_id: str) -> WorkflowInfo:
        """Resume workflow execution.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Updated workflow info.

        Raises:
            InvalidTransitionError: If transition is invalid.
        """
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        current_status = WorkflowStatus(workflow.status)
        WorkflowStateMachine.validate_transition(
            current_status, WorkflowStatus.RUNNING
        )

        await self.repository.update_workflow_status(
            workflow_id, WorkflowStatus.RUNNING
        )

        emitter = self._get_emitter(workflow_id)
        emitter.emit(EventType.WORKFLOW_RESUMED)

        workflow = await self.repository.get_workflow(workflow_id)
        return self._to_workflow_info(workflow)

    async def cancel_workflow(self, workflow_id: str) -> WorkflowInfo:
        """Cancel workflow execution.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Updated workflow info.

        Raises:
            InvalidTransitionError: If transition is invalid.
        """
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        current_status = WorkflowStatus(workflow.status)
        WorkflowStateMachine.validate_transition(
            current_status, WorkflowStatus.CANCELLED
        )

        await self.repository.update_workflow_status(
            workflow_id, WorkflowStatus.CANCELLED
        )

        emitter = self._get_emitter(workflow_id)
        emitter.emit(EventType.WORKFLOW_CANCELLED)

        self.scheduler.remove_queue(workflow_id)

        workflow = await self.repository.get_workflow(workflow_id)
        return self._to_workflow_info(workflow)

    async def get_execution_summary(
        self, workflow_id: str
    ) -> dict[str, Any]:
        """Get execution summary for a workflow.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Execution summary.
        """
        workflow = await self.repository.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        tasks = await self.repository.get_workflow_tasks(workflow_id)
        events = await self.repository.get_workflow_events(workflow_id)

        task_dicts = [
            {
                "id": t.id,
                "status": t.status,
                "duration": t.duration,
            }
            for t in tasks
        ]

        workflow_events = [
            WorkflowEvent(
                id=e.id,
                workflow_id=e.workflow_id,
                task_id=e.task_id,
                event_type=EventType(e.event_type),
                data=e.data,
                timestamp=e.created_at,
            )
            for e in events
        ]

        total_duration = 0
        if workflow.started_at:
            end_time = workflow.completed_at or datetime.now(timezone.utc)
            total_duration = int((end_time - workflow.started_at).total_seconds())

        summary = self.summary_generator.generate(
            workflow_id=workflow_id,
            tasks=task_dicts,
            events=workflow_events,
            total_duration=total_duration,
        )

        return summary.model_dump()

    def _get_emitter(self, workflow_id: str) -> WorkflowEventEmitter:
        """Get or create event emitter for a workflow."""
        if workflow_id not in self._emitters:
            self._emitters[workflow_id] = WorkflowEventEmitter(workflow_id)
        return self._emitters[workflow_id]

    def _to_workflow_info(self, workflow: Any) -> WorkflowInfo:
        """Convert workflow model to info schema."""
        tasks = [
            TaskInfo(
                id=t.id,
                workflow_id=t.workflow_id,
                title=t.title,
                description=t.description,
                priority=TaskPriority(t.priority),
                dependencies=t.dependencies or [],
                agent_type=t.agent_type,
                status=TaskStatus(t.status),
                retries=t.retries,
                max_retries=t.max_retries,
                execution_result=t.execution_result,
                validation_result=t.validation_result,
                duration=t.duration,
                created_at=t.created_at,
                updated_at=t.updated_at,
                started_at=t.started_at,
                completed_at=t.completed_at,
            )
            for t in (workflow.tasks if hasattr(workflow, 'tasks') else [])
        ]

        return WorkflowInfo(
            id=workflow.id,
            project_id=workflow.project_id,
            title=workflow.title,
            description=workflow.description,
            status=WorkflowStatus(workflow.status),
            current_step=workflow.current_step,
            tasks=tasks,
            execution_log=[],
            approval_status=workflow.approval_status,
            risk_level=RiskLevel(workflow.risk_level),
            estimated_time=workflow.estimated_time,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at,
            started_at=workflow.started_at,
            completed_at=workflow.completed_at,
            metadata=workflow.metadata_json or {},
        )
