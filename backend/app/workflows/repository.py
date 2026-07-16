"""Repository for workflow data access."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.workflows.models import WorkflowEventModel, WorkflowModel, WorkflowTaskModel
from app.workflows.schemas import (
    TaskInfo,
    TaskStatus,
    WorkflowEvent,
    WorkflowInfo,
    WorkflowStatus,
    EventType,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowRepository:
    """Repository for workflow data access."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Async database session.
        """
        self.session = session

    async def create_workflow(
        self,
        title: str,
        description: str,
        project_id: str | None = None,
        requires_approval: bool = True,
        risk_level: str = "medium",
        metadata: dict | None = None,
    ) -> WorkflowModel:
        """Create a new workflow.

        Args:
            title: Workflow title.
            description: Workflow description.
            project_id: Optional project ID.
            requires_approval: Whether approval is required.
            risk_level: Risk level.
            metadata: Additional metadata.

        Returns:
            Created workflow model.
        """
        workflow = WorkflowModel(
            title=title,
            description=description,
            project_id=project_id,
            requires_approval=requires_approval,
            risk_level=risk_level,
            metadata_json=metadata or {},
        )
        self.session.add(workflow)
        await self.session.flush()
        return workflow

    async def get_workflow(self, workflow_id: str) -> WorkflowModel | None:
        """Get a workflow by ID.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Workflow model or None.
        """
        stmt = (
            select(WorkflowModel)
            .options(
                selectinload(WorkflowModel.tasks),
                selectinload(WorkflowModel.events),
            )
            .where(WorkflowModel.id == workflow_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_workflows(
        self,
        status: WorkflowStatus | None = None,
        project_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WorkflowModel]:
        """List workflows with optional filters.

        Args:
            status: Filter by status.
            project_id: Filter by project ID.
            limit: Maximum results.
            offset: Results offset.

        Returns:
            List of workflow models.
        """
        stmt = select(WorkflowModel).options(
            selectinload(WorkflowModel.tasks)
        )

        if status:
            stmt = stmt.where(WorkflowModel.status == status.value)

        if project_id:
            stmt = stmt.where(WorkflowModel.project_id == project_id)

        stmt = stmt.order_by(WorkflowModel.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatus,
    ) -> WorkflowModel | None:
        """Update workflow status.

        Args:
            workflow_id: Workflow ID.
            status: New status.

        Returns:
            Updated workflow model or None.
        """
        workflow = await self.get_workflow(workflow_id)
        if workflow:
            workflow.status = status.value
            workflow.updated_at = datetime.now(timezone.utc)

            if status == WorkflowStatus.RUNNING and not workflow.started_at:
                workflow.started_at = datetime.now(timezone.utc)
            elif status in (WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
                workflow.completed_at = datetime.now(timezone.utc)

            await self.session.flush()
        return workflow

    async def create_task(
        self,
        workflow_id: str,
        title: str,
        description: str,
        priority: str = "medium",
        dependencies: list[str] | None = None,
        agent_type: str | None = None,
        estimated_duration: int | None = None,
        metadata: dict | None = None,
    ) -> WorkflowTaskModel:
        """Create a new task within a workflow.

        Args:
            workflow_id: Workflow ID.
            title: Task title.
            description: Task description.
            priority: Task priority.
            dependencies: Task dependencies.
            agent_type: Agent type to execute.
            estimated_duration: Estimated duration in seconds.
            metadata: Additional metadata.

        Returns:
            Created task model.
        """
        task = WorkflowTaskModel(
            workflow_id=workflow_id,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
            agent_type=agent_type,
            estimated_duration=estimated_duration,
            metadata_json=metadata or {},
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_task(self, task_id: str) -> WorkflowTaskModel | None:
        """Get a task by ID.

        Args:
            task_id: Task ID.

        Returns:
            Task model or None.
        """
        stmt = select(WorkflowTaskModel).where(WorkflowTaskModel.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_workflow_tasks(self, workflow_id: str) -> list[WorkflowTaskModel]:
        """Get all tasks for a workflow.

        Args:
            workflow_id: Workflow ID.

        Returns:
            List of task models.
        """
        stmt = (
            select(WorkflowTaskModel)
            .where(WorkflowTaskModel.workflow_id == workflow_id)
            .order_by(WorkflowTaskModel.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        execution_result: dict | None = None,
        validation_result: dict | None = None,
        duration: int | None = None,
    ) -> WorkflowTaskModel | None:
        """Update task status.

        Args:
            task_id: Task ID.
            status: New status.
            execution_result: Execution result.
            validation_result: Validation result.
            duration: Duration in seconds.

        Returns:
            Updated task model or None.
        """
        task = await self.get_task(task_id)
        if task:
            task.status = status.value
            task.updated_at = datetime.now(timezone.utc)

            if execution_result is not None:
                task.execution_result = execution_result
            if validation_result is not None:
                task.validation_result = validation_result
            if duration is not None:
                task.duration = duration

            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = datetime.now(timezone.utc)
            elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED):
                task.completed_at = datetime.now(timezone.utc)

            await self.session.flush()
        return task

    async def increment_task_retries(self, task_id: str) -> WorkflowTaskModel | None:
        """Increment task retry count.

        Args:
            task_id: Task ID.

        Returns:
            Updated task model or None.
        """
        task = await self.get_task(task_id)
        if task:
            task.retries += 1
            task.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
        return task

    async def create_event(
        self,
        workflow_id: str,
        event_type: EventType,
        task_id: str | None = None,
        data: dict | None = None,
    ) -> WorkflowEventModel:
        """Create a workflow event.

        Args:
            workflow_id: Workflow ID.
            event_type: Event type.
            task_id: Optional task ID.
            data: Event data.

        Returns:
            Created event model.
        """
        event = WorkflowEventModel(
            workflow_id=workflow_id,
            task_id=task_id,
            event_type=event_type.value,
            data=data or {},
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_workflow_events(
        self,
        workflow_id: str,
        limit: int = 100,
    ) -> list[WorkflowEventModel]:
        """Get events for a workflow.

        Args:
            workflow_id: Workflow ID.
            limit: Maximum results.

        Returns:
            List of event models.
        """
        stmt = (
            select(WorkflowEventModel)
            .where(WorkflowEventModel.workflow_id == workflow_id)
            .order_by(WorkflowEventModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
