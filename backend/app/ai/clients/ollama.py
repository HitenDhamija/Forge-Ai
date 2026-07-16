"""Async HTTP client for communicating with the Ollama API."""

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.ai.config import AISettings, get_ai_settings
from app.ai.exceptions import (
    AITimeoutException,
    ModelNotFoundException,
    OllamaConnectionException,
    StreamingException,
)
from app.ai.schemas.chat import ChatStreamChunk
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaClient:
    """Async HTTP client for communicating with Ollama API.

    Handles connection management, health checks, model operations, and
    streaming chat completions against a local Ollama instance.
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        connect_timeout: int = 5,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._connect_timeout = connect_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Return the httpx client, creating it on first use."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=httpx.Timeout(
                    connect=self._connect_timeout,
                    read=self._timeout,
                    write=self._connect_timeout,
                    pool=self._connect_timeout,
                ),
                headers={"Content-Type": "application/json"},
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ConnectTimeout)),
        reraise=True,
    )
    async def health_check(self) -> bool:
        """Check if the Ollama server is reachable.

        Returns:
            ``True`` if the server responds, ``False`` otherwise.
        """
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.warning("Ollama health check failed: %s", exc)
            return False
        except Exception as exc:
            logger.error("Unexpected error during health check: %s", exc)
            return False

    async def get_version(self) -> str | None:
        """Retrieve the Ollama server version string.

        Returns:
            Version string or ``None`` if unavailable.
        """
        try:
            client = await self._get_client()
            resp = await client.get("/api/version")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("version")
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.warning("Failed to get Ollama version: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error getting Ollama version: %s", exc)
        return None

    async def list_models(self) -> list[dict[str, Any]]:
        """List all locally installed models.

        Returns:
            List of model metadata dictionaries.
        """
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("models", [])
            logger.warning("list_models returned status %s", resp.status_code)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.error("Failed to list models: %s", exc)
            raise OllamaConnectionException() from exc
        except Exception as exc:
            logger.error("Unexpected error listing models: %s", exc)
            raise OllamaConnectionException(str(exc)) from exc
        return []

    async def get_running_models(self) -> list[str]:
        """Return the names of models currently loaded in memory.

        Returns:
            List of model name strings.
        """
        try:
            client = await self._get_client()
            resp = await client.get("/api/ps")
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                return [m.get("name", "") for m in models if m.get("name")]
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.warning("Failed to get running models: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error getting running models: %s", exc)
        return []

    async def show_model(self, model_name: str) -> dict[str, Any]:
        """Get detailed information about a specific model.

        Args:
            model_name: The model identifier.

        Returns:
            Model detail dictionary.

        Raises:
            ModelNotFoundException: If the model does not exist.
            OllamaConnectionException: On connection failure.
        """
        try:
            client = await self._get_client()
            resp = await client.post(
                "/api/show", json={"name": model_name}
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                raise ModelNotFoundException(
                    f"Model '{model_name}' not found"
                )
            logger.warning(
                "show_model returned status %s for %s",
                resp.status_code,
                model_name,
            )
        except ModelNotFoundException:
            raise
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.error("Failed to show model %s: %s", model_name, exc)
            raise OllamaConnectionException() from exc
        except Exception as exc:
            logger.error("Unexpected error showing model %s: %s", model_name, exc)
            raise OllamaConnectionException(str(exc)) from exc
        return {}

    async def pull_model(self, model_name: str) -> bool:
        """Download a model from the Ollama registry.

        Args:
            model_name: The model identifier to pull.

        Returns:
            ``True`` on success.
        """
        try:
            client = await self._get_client()
            async with client.stream(
                "POST", "/api/pull", json={"name": model_name, "stream": True}
            ) as resp:
                if resp.status_code != 200:
                    logger.error("Pull failed with status %s", resp.status_code)
                    return False
                async for line in resp.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if data.get("error"):
                            logger.error("Pull error: %s", data["error"])
                            return False
            return True
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.error("Failed to pull model %s: %s", model_name, exc)
            return False
        except Exception as exc:
            logger.error("Unexpected error pulling model %s: %s", model_name, exc)
            return False

    async def delete_model(self, model_name: str) -> bool:
        """Delete a locally installed model.

        Args:
            model_name: The model identifier to delete.

        Returns:
            ``True`` on success.
        """
        try:
            client = await self._get_client()
            resp = await client.request(
                "DELETE", "/api/delete", json={"name": model_name}
            )
            return resp.status_code == 200
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.error("Failed to delete model %s: %s", model_name, exc)
            return False
        except Exception as exc:
            logger.error("Unexpected error deleting model %s: %s", model_name, exc)
            return False

    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool = True,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        max_tokens: int = 2048,
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None] | dict[str, Any]:
        """Send a chat completion request to Ollama.

        Args:
            model: Model identifier.
            messages: List of ``{"role": ..., "content": ...}`` dicts.
            stream: Whether to stream the response.
            temperature: Sampling temperature.
            top_p: Nucleus sampling probability.
            top_k: Top-k sampling parameter.
            max_tokens: Maximum tokens to generate.
            options: Additional Ollama-specific options.

        Returns:
            A dict for non-streaming, or an async generator of chunks for streaming.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "num_predict": max_tokens,
            },
        }
        if options:
            payload["options"].update(options)

        try:
            client = await self._get_client()
            if stream:
                return self._stream_response(client, payload)
            resp = await client.post("/api/chat", json=payload)
            if resp.status_code == 200:
                return resp.json()
            logger.error("generate returned status %s", resp.status_code)
            return {"message": {"role": "assistant", "content": ""}, "done": True}
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.error("generate connection error: %s", exc)
            raise OllamaConnectionException() from exc
        except Exception as exc:
            logger.error("generate unexpected error: %s", exc)
            raise

    async def _stream_response(
        self, client: httpx.AsyncClient, payload: dict[str, Any]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Yield NDJSON chunks from a streaming Ollama chat response."""
        try:
            async with client.stream("POST", "/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    logger.error(
                        "Streaming returned status %s: %s",
                        resp.status_code,
                        body.decode(errors="replace"),
                    )
                    return
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        yield data
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse stream line: %s", line[:200])
        except httpx.ReadTimeout as exc:
            logger.error("Stream read timeout: %s", exc)
            raise AITimeoutException("Streaming response timed out") from exc
        except httpx.ConnectError as exc:
            logger.error("Stream connection error: %s", exc)
            raise OllamaConnectionException() from exc
        except Exception as exc:
            logger.error("Stream unexpected error: %s", exc)
            raise StreamingException(str(exc)) from exc

    async def generate_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Stream a chat completion token by token.

        Yields:
            ``ChatStreamChunk`` instances for each generated token.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "num_predict": max_tokens,
            },
        }

        try:
            client = await self._get_client()
            async with client.stream("POST", "/api/chat", json=payload) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    logger.error(
                        "generate_stream returned status %s: %s",
                        resp.status_code,
                        body.decode(errors="replace"),
                    )
                    return
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        msg = data.get("message", {})
                        done = data.get("done", False)
                        content = msg.get("content", "") if not done else ""
                        yield ChatStreamChunk(
                            conversation_id="",
                            content=content,
                            done=done,
                            model=data.get("model", model),
                        )
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse stream line: %s", line[:200])
        except httpx.ReadTimeout as exc:
            logger.error("generate_stream timeout: %s", exc)
            raise AITimeoutException("Streaming response timed out") from exc
        except httpx.ConnectError as exc:
            logger.error("generate_stream connection error: %s", exc)
            raise OllamaConnectionException() from exc
        except (AITimeoutException, OllamaConnectionException):
            raise
        except Exception as exc:
            logger.error("generate_stream unexpected error: %s", exc)
            raise StreamingException(str(exc)) from exc

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
