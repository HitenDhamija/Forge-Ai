"""Event system for workflow execution tracking."""

from datetime import datetime, timezone
from typing import Any

from app.workflows.schemas import EventType, WorkflowEvent
from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowEventEmitter:
    """Event emitter for workflow events.

    Collects and manages events during workflow execution.
    """

    def __init__(self, workflow_id: str) -> None:
        """Initialize the event emitter.

        Args:
            workflow_id: Workflow ID.
        """
        self.workflow_id = workflow_id
        self._events: list[WorkflowEvent] = []
        self._listeners: dict[EventType, list[Any]] = {}

    def emit(
        self,
        event_type: EventType,
        task_id: str | None = None,
        data: dict | None = None,
    ) -> WorkflowEvent:
        """Emit a workflow event.

        Args:
            event_type: Type of event.
            task_id: Optional task ID.
            data: Event data.

        Returns:
            Created event.
        """
        import uuid

        event = WorkflowEvent(
            id=str(uuid.uuid4()),
            workflow_id=self.workflow_id,
            task_id=task_id,
            event_type=event_type,
            data=data or {},
            timestamp=datetime.now(timezone.utc),
        )

        self._events.append(event)

        logger.info(
            "Event emitted: %s (workflow: %s, task: %s)",
            event_type.value,
            self.workflow_id,
            task_id,
        )

        for listener in self._listeners.get(event_type, []):
            try:
                listener(event)
            except Exception as e:
                logger.error("Event listener error: %s", str(e))

        return event

    def on(self, event_type: EventType, callback: Any) -> None:
        """Register an event listener.

        Args:
            event_type: Event type to listen for.
            callback: Callback function.
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def off(self, event_type: EventType, callback: Any) -> None:
        """Remove an event listener.

        Args:
            event_type: Event type.
            callback: Callback function to remove.
        """
        if event_type in self._listeners:
            self._listeners[event_type] = [
                cb for cb in self._listeners[event_type] if cb != callback
            ]

    def get_events(
        self,
        event_type: EventType | None = None,
        task_id: str | None = None,
    ) -> list[WorkflowEvent]:
        """Get events with optional filters.

        Args:
            event_type: Filter by event type.
            task_id: Filter by task ID.

        Returns:
            List of matching events.
        """
        events = self._events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if task_id:
            events = [e for e in events if e.task_id == task_id]

        return events

    def get_event_count(self) -> int:
        """Get total number of events.

        Returns:
            Event count.
        """
        return len(self._events)

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()
