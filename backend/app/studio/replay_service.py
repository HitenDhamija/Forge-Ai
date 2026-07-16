"""Execution replay service for recording and replaying workflow execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from app.core.logging import get_logger
import uuid

logger = get_logger(__name__)


@dataclass
class ReplayEvent:
    """A single recorded event during workflow execution."""

    timestamp: datetime
    event_type: str
    node_id: str
    agent_id: str = ""
    tool_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass
class ReplayState:
    """Current state of a replay session."""

    execution_id: str
    workflow_id: str
    events: list[ReplayEvent] = field(default_factory=list)
    current_index: int = 0
    status: str = "ready"
    speed: float = 1.0


class ReplayStatus(str, Enum):
    """Replay session status."""

    READY = "ready"
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"


class ReplayService:
    """Service for recording and replaying workflow execution events.

    Stores replay data in-memory and provides step-through
    navigation for debugging and analysis.
    """

    def __init__(self) -> None:
        self._replays: dict[str, ReplayState] = {}

    async def start_replay(self, execution_id: str) -> str:
        """Start a replay session for an execution.

        Args:
            execution_id: The execution to replay.

        Returns:
            The replay session ID.
        """
        replay = ReplayState(
            execution_id=execution_id,
            workflow_id=execution_id,
            status=ReplayStatus.READY.value,
        )

        self._replays[execution_id] = replay
        logger.info("Started replay session: execution=%s", execution_id[:8])
        return execution_id

    async def get_replay(self, execution_id: str) -> ReplayState:
        """Get the current replay state.

        Args:
            execution_id: The execution identifier.

        Returns:
            The ReplayState.

        Raises:
            ValueError: If replay session is not found.
        """
        replay = self._replays.get(execution_id)
        if replay is None:
            raise ValueError(f"Replay not found: {execution_id}")
        return replay

    async def step_forward(self, execution_id: str) -> ReplayEvent | None:
        """Step forward to the next event.

        Args:
            execution_id: The execution identifier.

        Returns:
            The next ReplayEvent or None if at end.
        """
        replay = await self.get_replay(execution_id)

        if replay.current_index >= len(replay.events) - 1:
            replay.status = ReplayStatus.COMPLETED.value
            return None

        replay.current_index += 1
        event = replay.events[replay.current_index]

        logger.debug(
            "Stepped forward: execution=%s index=%d event=%s",
            execution_id[:8],
            replay.current_index,
            event.event_type,
        )

        return event

    async def step_backward(self, execution_id: str) -> ReplayEvent | None:
        """Step backward to the previous event.

        Args:
            execution_id: The execution identifier.

        Returns:
            The previous ReplayEvent or None if at start.
        """
        replay = await self.get_replay(execution_id)

        if replay.current_index <= 0:
            return None

        replay.current_index -= 1
        event = replay.events[replay.current_index]

        logger.debug(
            "Stepped backward: execution=%s index=%d event=%s",
            execution_id[:8],
            replay.current_index,
            event.event_type,
        )

        return event

    async def seek_to(
        self, execution_id: str, index: int
    ) -> ReplayEvent | None:
        """Seek to a specific event index.

        Args:
            execution_id: The execution identifier.
            index: Target event index.

        Returns:
            The event at the target index or None if out of range.
        """
        replay = await self.get_replay(execution_id)

        if index < 0 or index >= len(replay.events):
            return None

        replay.current_index = index
        event = replay.events[index]

        logger.debug(
            "Seeked to index: execution=%s index=%d",
            execution_id[:8],
            index,
        )

        return event

    async def get_events(
        self, execution_id: str
    ) -> list[ReplayEvent]:
        """Get all recorded events for an execution.

        Args:
            execution_id: The execution identifier.

        Returns:
            List of ReplayEvent instances.
        """
        replay = await self.get_replay(execution_id)
        return list(replay.events)

    async def get_event_detail(
        self, execution_id: str, event_index: int
    ) -> dict[str, Any]:
        """Get detailed information about a specific event.

        Args:
            execution_id: The execution identifier.
            event_index: The event index.

        Returns:
            Event detail dictionary.
        """
        replay = await self.get_replay(execution_id)

        if event_index < 0 or event_index >= len(replay.events):
            return {"error": "Event index out of range"}

        event = replay.events[event_index]
        total_events = len(replay.events)

        return {
            "execution_id": execution_id,
            "event_index": event_index,
            "total_events": total_events,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "node_id": event.node_id,
            "agent_id": event.agent_id,
            "tool_id": event.tool_id,
            "data": event.data,
            "duration_ms": event.duration_ms,
            "is_current": event_index == replay.current_index,
            "is_first": event_index == 0,
            "is_last": event_index == total_events - 1,
            "progress": (event_index + 1) / total_events if total_events > 0 else 0,
        }

    async def record_event(
        self, execution_id: str, event: ReplayEvent
    ) -> None:
        """Record a new event for an execution.

        Args:
            execution_id: The execution identifier.
            event: The ReplayEvent to record.
        """
        replay = await self.get_replay(execution_id)
        replay.events.append(event)

        logger.debug(
            "Recorded event: execution=%s type=%s node=%s",
            execution_id[:8],
            event.event_type,
            event.node_id[:8] if event.node_id else "none",
        )

    async def get_replay_summary(
        self, execution_id: str
    ) -> dict[str, Any]:
        """Get a summary of the replay.

        Args:
            execution_id: The execution identifier.

        Returns:
            Replay summary dictionary.
        """
        replay = await self.get_replay(execution_id)
        events = replay.events

        if not events:
            return {
                "execution_id": execution_id,
                "total_events": 0,
                "status": replay.status,
                "current_index": 0,
            }

        event_types: dict[str, int] = {}
        for e in events:
            event_types[e.event_type] = event_types.get(e.event_type, 0) + 1

        total_duration = sum(e.duration_ms for e in events)

        start_time = events[0].timestamp
        end_time = events[-1].timestamp
        wall_clock_ms = (end_time - start_time).total_seconds() * 1000

        agent_ids = list({e.agent_id for e in events if e.agent_id})
        tool_ids = list({e.tool_id for e in events if e.tool_id})
        node_ids = list({e.node_id for e in events if e.node_id})

        return {
            "execution_id": execution_id,
            "workflow_id": replay.workflow_id,
            "total_events": len(events),
            "current_index": replay.current_index,
            "status": replay.status,
            "speed": replay.speed,
            "event_types": event_types,
            "total_duration_ms": total_duration,
            "wall_clock_ms": wall_clock_ms,
            "agent_ids": agent_ids,
            "tool_ids": tool_ids,
            "node_ids": node_ids,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }
