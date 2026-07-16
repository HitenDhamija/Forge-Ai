"""Streaming response lifecycle manager."""

import asyncio
from collections.abc import Awaitable, Callable

from app.ai.clients.ollama import OllamaClient
from app.ai.exceptions import StreamingException
from app.ai.schemas.chat import ChatStreamChunk
from app.core.logging import get_logger

logger = get_logger(__name__)


class StreamingHandler:
    """Manages streaming response lifecycle and cancellation."""

    def __init__(self) -> None:
        self._active_streams: dict[str, asyncio.Task[None]] = {}

    async def start_stream(
        self,
        conversation_id: str,
        ollama_client: OllamaClient,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        on_token: Callable[[ChatStreamChunk], Awaitable[None]],
        on_complete: Callable[[str], Awaitable[None]],
        on_error: Callable[[Exception], Awaitable[None]],
    ) -> None:
        """Start streaming a response and invoke callbacks for each token.

        Args:
            conversation_id: Identifier for the conversation being streamed.
            ollama_client: The Ollama client to stream from.
            model: Model identifier to use.
            messages: Chat message list.
            temperature: Sampling temperature.
            on_token: Async callback invoked for each generated token.
            on_complete: Async callback invoked when streaming finishes.
            on_error: Async callback invoked on error.
        """
        if conversation_id in self._active_streams:
            logger.warning(
                "Stream already active for conversation %s, stopping previous",
                conversation_id,
            )
            await self.stop_stream(conversation_id)

        task = asyncio.create_task(
            self._stream_loop(
                conversation_id,
                ollama_client,
                model,
                messages,
                temperature,
                on_token,
                on_complete,
                on_error,
            )
        )
        self._active_streams[conversation_id] = task
        logger.info("Started stream for conversation %s", conversation_id)

    async def _stream_loop(
        self,
        conversation_id: str,
        ollama_client: OllamaClient,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        on_token: Callable[[ChatStreamChunk], Awaitable[None]],
        on_complete: Callable[[str], Awaitable[None]],
        on_error: Callable[[Exception], Awaitable[None]],
    ) -> None:
        """Internal streaming loop with error handling and cleanup."""
        try:
            async for chunk in ollama_client.generate_stream(
                model=model,
                messages=messages,
                temperature=temperature,
            ):
                chunk.conversation_id = conversation_id
                await on_token(chunk)
                if chunk.done:
                    break
            await on_complete(conversation_id)
        except asyncio.CancelledError:
            logger.info("Stream cancelled for conversation %s", conversation_id)
        except Exception as exc:
            logger.error("Stream error for conversation %s: %s", conversation_id, exc)
            try:
                await on_error(exc)
            except Exception as cb_exc:
                logger.error("Error in on_error callback: %s", cb_exc)
        finally:
            self._active_streams.pop(conversation_id, None)

    async def stop_stream(self, conversation_id: str) -> bool:
        """Cancel an active stream.

        Args:
            conversation_id: The conversation to stop streaming.

        Returns:
            ``True`` if a stream was found and cancelled.
        """
        task = self._active_streams.get(conversation_id)
        if task is None:
            return False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        self._active_streams.pop(conversation_id, None)
        logger.info("Stopped stream for conversation %s", conversation_id)
        return True

    def is_streaming(self, conversation_id: str) -> bool:
        """Check if a conversation is currently being streamed."""
        task = self._active_streams.get(conversation_id)
        return task is not None and not task.done()

    async def stop_all(self) -> None:
        """Stop all active streams."""
        ids = list(self._active_streams.keys())
        for cid in ids:
            await self.stop_stream(cid)
        logger.info("Stopped all streams")
