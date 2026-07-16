"""Event system for tool execution tracking."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.tools.schemas import EventType, ToolEvent
from app.core.logging import get_logger

logger = get_logger(__name__)

ToolEventType = EventType


class ToolEventEmitter:
    """Event emitter for tool execution events.

    Collects and manages events during tool execution.
    """

    def __init__(self):
        """Initialize the event emitter."""
        self._events: list[ToolEvent] = []
        self._listeners: dict[EventType, list[Any]] = {}

    def emit(
        self,
        event_type: EventType,
        tool_id: str,
        request_id: str | None = None,
        agent_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> ToolEvent:
        """Emit a tool event.

        Args:
            event_type: Type of event.
            tool_id: Tool ID.
            request_id: Optional request ID.
            agent_id: Optional agent ID.
            data: Event data.

        Returns:
            Created event.
        """
        event = ToolEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            tool_id=tool_id,
            request_id=request_id,
            agent_id=agent_id,
            data=data or {},
            timestamp=datetime.now(timezone.utc),
        )

        self._events.append(event)

        logger.info(
            "Event emitted: %s (tool: %s, request: %s)",
            event_type.value,
            tool_id,
            request_id,
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
        tool_id: str | None = None,
        request_id: str | None = None,
        limit: int = 100,
    ) -> list[ToolEvent]:
        """Get events with optional filters.

        Args:
            event_type: Filter by event type.
            tool_id: Filter by tool ID.
            request_id: Filter by request ID.
            limit: Maximum events to return.

        Returns:
            List of matching events.
        """
        events = self._events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if tool_id:
            events = [e for e in events if e.tool_id == tool_id]

        if request_id:
            events = [e for e in events if e.request_id == request_id]

        return events[-limit:]

    def get_event_count(self) -> int:
        """Get total number of events.

        Returns:
            Event count.
        """
        return len(self._events)

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()
