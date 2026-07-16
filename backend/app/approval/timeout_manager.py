"""Timeout Manager - Handles approval request timeouts.

Periodically checks for timed out requests and escalates.
"""

import asyncio
from datetime import datetime
from typing import Callable, Awaitable

from app.core.logging import get_logger
from app.approval.approval_engine import ApprovalEngine
from app.approval.models import ApprovalStatusDB

logger = get_logger(__name__)


class TimeoutManager:
    """Manages approval request timeouts.

    Responsibilities:
    - Periodically check for timed out requests
    - Auto-deny timed out requests
    - Notify callbacks on timeout
    """

    def __init__(self, approval_engine: ApprovalEngine):
        """Initialize timeout manager.

        Args:
            approval_engine: The approval engine instance.
        """
        self.approval_engine = approval_engine
        self._check_interval = 30  # seconds
        self._running = False
        self._task: asyncio.Task | None = None
        self._on_timeout_callbacks: list[Callable[[str], Awaitable[None]]] = []
        logger.info("Timeout manager initialized")

    def on_timeout(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """Register timeout callback.

        Args:
            callback: Async function called with request_id on timeout.
        """
        self._on_timeout_callbacks.append(callback)

    async def start(self) -> None:
        """Start the timeout checker."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("Timeout manager started")

    async def stop(self) -> None:
        """Stop the timeout checker."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Timeout manager stopped")

    async def _check_loop(self) -> None:
        """Main check loop."""
        while self._running:
            try:
                await self._check_timeouts()
            except Exception as e:
                logger.error("Timeout check error: %s", str(e))

            await asyncio.sleep(self._check_interval)

    async def _check_timeouts(self) -> None:
        """Check for timed out requests."""
        timed_out_count = 0

        for request_id, request in list(self.approval_engine._requests.items()):
            if request.status != ApprovalStatusDB.PENDING.value:
                continue

            if request.expires_at and datetime.utcnow() > request.expires_at:
                # Mark as timed out
                request.status = ApprovalStatusDB.TIMEOUT.value
                request.decided_at = datetime.utcnow()
                timed_out_count += 1

                logger.info("Request timed out: %s", request_id[:8])

                # Notify callbacks
                for callback in self._on_timeout_callbacks:
                    try:
                        await callback(request_id)
                    except Exception as e:
                        logger.error("Timeout callback error: %s", str(e))

        if timed_out_count > 0:
            logger.info("Timed out %d requests", timed_out_count)
