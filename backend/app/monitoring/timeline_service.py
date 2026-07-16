"""Chronological event timeline generation from all system activities."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class TimelineEventType(str, Enum):
    """Types of timeline events across the system."""

    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    AGENT_ASSIGNED = "agent_assigned"
    TOOL_CALLED = "tool_called"
    TOOL_COMPLETED = "tool_completed"
    REFLECTION_STARTED = "reflection_started"
    QA_STARTED = "qa_started"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    MEMORY_INDEXED = "memory_indexed"
    MEMORY_SEARCHED = "memory_searched"
    LEARNING_PROCESSED = "learning_processed"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    SYSTEM_HEALTH_CHECK = "system_health_check"


class EventSeverity(str, Enum):
    """Severity level for timeline events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class TimelineEvent:
    """A single event on the system timeline."""

    id: str
    event_type: TimelineEventType
    source: str
    title: str
    description: str
    metadata: dict[str, Any]
    severity: EventSeverity
    timestamp: datetime


class TimelineService:
    """Generates chronological event timelines from all system activities.

    Stores events in-memory with configurable retention. Provides filtered
    views for workflows, agents, tools, and error events.
    """

    def __init__(self, retention_hours: float = 48.0) -> None:
        """Initialize the timeline service.

        Args:
            retention_hours: How long to keep events in memory.
        """
        self._retention = timedelta(hours=retention_hours)
        self._events: list[TimelineEvent] = []
        logger.info("TimelineService initialized: retention=%.1fh", retention_hours)

    async def record_event(
        self,
        event_type: TimelineEventType,
        source: str,
        title: str,
        description: str = "",
        metadata: dict[str, Any] | None = None,
        severity: EventSeverity = EventSeverity.INFO,
    ) -> TimelineEvent:
        """Record a new event on the timeline.

        Args:
            event_type: Type of event.
            source: Origin of the event (agent/tool/workflow/system).
            title: Short event title.
            description: Detailed event description.
            metadata: Additional context data.
            severity: Event severity level.

        Returns:
            The recorded TimelineEvent.
        """
        event = TimelineEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            source=source,
            title=title,
            description=description,
            metadata=metadata or {},
            severity=severity,
            timestamp=datetime.now(timezone.utc),
        )
        self._events.append(event)
        logger.info(
            "Timeline event: type=%s source=%s title=%s severity=%s",
            event_type.value,
            source,
            title,
            severity.value,
        )
        return event

    async def get_timeline(
        self,
        hours: int = 24,
        event_type: TimelineEventType | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> list[TimelineEvent]:
        """Get filtered timeline events.

        Args:
            hours: Number of hours of history to retrieve.
            event_type: Optional event type filter.
            source: Optional source filter.
            limit: Maximum number of events to return.

        Returns:
            List of matching TimelineEvent objects, newest first.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        events = [e for e in self._events if e.timestamp >= cutoff]

        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]

        if source is not None:
            events = [e for e in events if e.source == source]

        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]

    async def get_workflow_timeline(self, workflow_id: str) -> list[TimelineEvent]:
        """Get timeline events for a specific workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            List of TimelineEvent objects for the workflow, newest first.
        """
        events = [
            e for e in self._events
            if e.metadata.get("workflow_id") == workflow_id
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events

    async def get_agent_timeline(
        self, agent_id: str, hours: int = 24
    ) -> list[TimelineEvent]:
        """Get timeline events for a specific agent.

        Args:
            agent_id: Agent identifier.
            hours: Number of hours of history to retrieve.

        Returns:
            List of TimelineEvent objects for the agent, newest first.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        events = [
            e for e in self._events
            if e.timestamp >= cutoff and e.metadata.get("agent_id") == agent_id
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events

    async def get_tool_timeline(
        self, tool_id: str, hours: int = 24
    ) -> list[TimelineEvent]:
        """Get timeline events for a specific tool.

        Args:
            tool_id: Tool identifier.
            hours: Number of hours of history to retrieve.

        Returns:
            List of TimelineEvent objects for the tool, newest first.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        events = [
            e for e in self._events
            if e.timestamp >= cutoff and e.metadata.get("tool_id") == tool_id
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events

    async def get_error_timeline(self, hours: int = 24) -> list[TimelineEvent]:
        """Get only error and warning events from the timeline.

        Args:
            hours: Number of hours of history to retrieve.

        Returns:
            List of error/warning TimelineEvent objects, newest first.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        events = [
            e for e in self._events
            if e.timestamp >= cutoff and e.severity in (EventSeverity.ERROR, EventSeverity.WARNING)
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events

    async def get_overview(self) -> dict[str, Any]:
        """Get timeline overview statistics.

        Returns:
            Dictionary with aggregate timeline stats.
        """
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(hours=24)

        recent_1h = [e for e in self._events if e.timestamp >= last_hour]
        recent_24h = [e for e in self._events if e.timestamp >= last_day]

        event_type_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}
        severity_counts: dict[str, int] = {}

        for event in recent_24h:
            event_type_counts[event.event_type.value] = (
                event_type_counts.get(event.event_type.value, 0) + 1
            )
            source_counts[event.source] = source_counts.get(event.source, 0) + 1
            severity_counts[event.severity.value] = (
                severity_counts.get(event.severity.value, 0) + 1
            )

        return {
            "total_events": len(self._events),
            "events_last_hour": len(recent_1h),
            "events_last_24h": len(recent_24h),
            "event_type_breakdown": event_type_counts,
            "source_breakdown": source_counts,
            "severity_breakdown": severity_counts,
        }

    async def cleanup(self, retention_hours: float | None = None) -> int:
        """Remove events older than the retention period.

        Args:
            retention_hours: Override retention period. Uses instance default if None.

        Returns:
            Number of events removed.
        """
        retention = (
            timedelta(hours=retention_hours)
            if retention_hours is not None
            else self._retention
        )
        cutoff = datetime.now(timezone.utc) - retention
        before = len(self._events)
        self._events = [e for e in self._events if e.timestamp >= cutoff]
        removed = before - len(self._events)

        if removed > 0:
            logger.info("Timeline cleanup: removed %d expired events", removed)
        return removed
