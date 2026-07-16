"""State machine for workflow and task state transitions."""

from app.workflows.schemas import TaskStatus, WorkflowStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, current_state: str, target_state: str, entity_type: str = "workflow"):
        self.current_state = current_state
        self.target_state = target_state
        self.entity_type = entity_type
        super().__init__(
            f"Invalid {entity_type} transition: {current_state} -> {target_state}"
        )


class WorkflowStateMachine:
    """State machine for workflow state transitions.

    Enforces valid state transitions and prevents invalid state changes.
    """

    VALID_TRANSITIONS: dict[WorkflowStatus, set[WorkflowStatus]] = {
        WorkflowStatus.CREATED: {
            WorkflowStatus.WAITING_APPROVAL,
            WorkflowStatus.READY,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.WAITING_APPROVAL: {
            WorkflowStatus.READY,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.READY: {
            WorkflowStatus.RUNNING,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.RUNNING: {
            WorkflowStatus.PAUSED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.PAUSED: {
            WorkflowStatus.RUNNING,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.FAILED: {
            WorkflowStatus.CREATED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.CANCELLED: set(),
        WorkflowStatus.COMPLETED: set(),
    }

    @classmethod
    def can_transition(cls, current: WorkflowStatus, target: WorkflowStatus) -> bool:
        """Check if a transition is valid.

        Args:
            current: Current workflow status.
            target: Target workflow status.

        Returns:
            True if the transition is valid.
        """
        return target in cls.VALID_TRANSITIONS.get(current, set())

    @classmethod
    def validate_transition(cls, current: WorkflowStatus, target: WorkflowStatus) -> None:
        """Validate a transition, raising an error if invalid.

        Args:
            current: Current workflow status.
            target: Target workflow status.

        Raises:
            InvalidTransitionError: If the transition is invalid.
        """
        if not cls.can_transition(current, target):
            raise InvalidTransitionError(
                current_state=current.value,
                target_state=target.value,
                entity_type="workflow",
            )

    @classmethod
    def get_valid_targets(cls, current: WorkflowStatus) -> set[WorkflowStatus]:
        """Get all valid target states from the current state.

        Args:
            current: Current workflow status.

        Returns:
            Set of valid target states.
        """
        return cls.VALID_TRANSITIONS.get(current, set()).copy()


class TaskStateMachine:
    """State machine for task state transitions.

    Enforces valid state transitions and prevents invalid state changes.
    """

    VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
        TaskStatus.PENDING: {
            TaskStatus.READY,
            TaskStatus.SKIPPED,
        },
        TaskStatus.READY: {
            TaskStatus.RUNNING,
            TaskStatus.SKIPPED,
        },
        TaskStatus.RUNNING: {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.WAITING,
        },
        TaskStatus.WAITING: {
            TaskStatus.READY,
            TaskStatus.RUNNING,
        },
        TaskStatus.FAILED: {
            TaskStatus.RETRYING,
            TaskStatus.SKIPPED,
        },
        TaskStatus.RETRYING: {
            TaskStatus.RUNNING,
            TaskStatus.FAILED,
            TaskStatus.SKIPPED,
        },
        TaskStatus.SKIPPED: set(),
        TaskStatus.COMPLETED: set(),
    }

    @classmethod
    def can_transition(cls, current: TaskStatus, target: TaskStatus) -> bool:
        """Check if a transition is valid.

        Args:
            current: Current task status.
            target: Target task status.

        Returns:
            True if the transition is valid.
        """
        return target in cls.VALID_TRANSITIONS.get(current, set())

    @classmethod
    def validate_transition(cls, current: TaskStatus, target: TaskStatus) -> None:
        """Validate a transition, raising an error if invalid.

        Args:
            current: Current task status.
            target: Target task status.

        Raises:
            InvalidTransitionError: If the transition is invalid.
        """
        if not cls.can_transition(current, target):
            raise InvalidTransitionError(
                current_state=current.value,
                target_state=target.value,
                entity_type="task",
            )

    @classmethod
    def get_valid_targets(cls, current: TaskStatus) -> set[TaskStatus]:
        """Get all valid target states from the current state.

        Args:
            current: Current task status.

        Returns:
            Set of valid target states.
        """
        return cls.VALID_TRANSITIONS.get(current, set()).copy()
