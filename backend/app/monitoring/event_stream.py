"""Real-time event streaming via WebSocket or Server-Sent Events."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncGenerator

from app.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_CHANNELS = ("agents", "workflows", "tools", "system", "all")


@dataclass
class StreamEvent:
    """A single event in the real-time stream."""

    id: str
    event_type: str
    channel: str
    data: dict[str, Any]
    timestamp: datetime


class EventStream:
    """Real-time event streaming with per-channel pub/sub.

    Uses asyncio.Queue for per-channel event distribution. Supports channels:
    "agents", "workflows", "tools", "system", "all".
    """

    def __init__(self, max_recent_events: int = 50) -> None:
        """Initialize the event stream.

        Args:
            max_recent_events: Maximum recent events to keep per channel.
        """
        self._max_recent = max_recent_events
        self._queues: dict[str, list[asyncio.Queue[StreamEvent]]] = {}
        self._recent: dict[str, list[StreamEvent]] = {}
        self._lock = asyncio.Lock()
        logger.info("EventStream initialized: max_recent=%d", max_recent_events)

    async def _ensure_channel(self, channel: str) -> None:
        """Ensure channel structures exist."""
        if channel not in self._queues:
            self._queues[channel] = []
            self._recent[channel] = []

    async def subscribe(self, channel: str) -> AsyncGenerator[StreamEvent, None]:
        """Subscribe to events on a channel.

        Args:
            channel: Channel name to subscribe to.

        Yields:
            StreamEvent objects as they arrive.
        """
        async with self._lock:
            await self._ensure_channel(channel)

        queue: asyncio.Queue[StreamEvent] = asyncio.Queue()
        async with self._lock:
            self._queues[channel].append(queue)

        logger.info("Subscriber added to channel: %s", channel)
        try:
            while True:
                event = await queue.get()
                yield event
        except asyncio.CancelledError:
            pass
        finally:
            async with self._lock:
                if queue in self._queues.get(channel, []):
                    self._queues[channel].remove(queue)
            logger.info("Subscriber removed from channel: %s", channel)

    async def publish(self, channel: str, event: dict[str, Any]) -> StreamEvent:
        """Publish an event to a channel.

        Events published to a specific channel are also sent to the "all" channel.

        Args:
            channel: Channel name to publish to.
            event: Event payload dictionary. Should include "event_type" key.

        Returns:
            The created StreamEvent.
        """
        async with self._lock:
            await self._ensure_channel(channel)
            await self._ensure_channel("all")

        event_type = event.pop("event_type", "unknown")
        stream_event = StreamEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            channel=channel,
            data=event,
            timestamp=datetime.now(timezone.utc),
        )

        async with self._lock:
            target_channels = [channel]
            if channel != "all":
                target_channels.append("all")

            for ch in target_channels:
                self._recent[ch].append(stream_event)
                if len(self._recent[ch]) > self._max_recent:
                    self._recent[ch] = self._recent[ch][-self._max_recent:]

                for queue in self._queues.get(ch, []):
                    try:
                        queue.put_nowait(stream_event)
                    except asyncio.QueueFull:
                        logger.warning("Queue full for channel: %s", ch)

        logger.debug(
            "Event published: channel=%s type=%s id=%s",
            channel,
            event_type,
            stream_event.id,
        )
        return stream_event

    async def get_subscribers(self, channel: str) -> int:
        """Get the number of active subscribers on a channel.

        Args:
            channel: Channel name.

        Returns:
            Number of active subscribers.
        """
        async with self._lock:
            return len(self._queues.get(channel, []))

    async def get_channels(self) -> list[str]:
        """Get all active channels with at least one subscriber or recent events.

        Returns:
            List of active channel names.
        """
        async with self._lock:
            channels = set(self._queues.keys()) | set(self._recent.keys())
            return sorted(channels)

    async def get_recent_events(
        self, channel: str, limit: int = 50
    ) -> list[StreamEvent]:
        """Get recent events on a channel.

        Args:
            channel: Channel name.
            limit: Maximum number of events to return.

        Returns:
            List of recent StreamEvent objects, newest last.
        """
        async with self._lock:
            events = self._recent.get(channel, [])
            return list(events[-limit:])

    async def cleanup(self, max_age_seconds: int = 3600) -> int:
        """Remove events older than max_age_seconds from recent history.

        Args:
            max_age_seconds: Maximum age of events to keep in seconds.

        Returns:
            Number of events removed.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        removed = 0

        async with self._lock:
            for channel in list(self._recent.keys()):
                before = len(self._recent[channel])
                self._recent[channel] = [
                    e for e in self._recent[channel] if e.timestamp >= cutoff
                ]
                removed += before - len(self._recent[channel])

        if removed > 0:
            logger.info("EventStream cleanup: removed %d expired events", removed)
        return removed
