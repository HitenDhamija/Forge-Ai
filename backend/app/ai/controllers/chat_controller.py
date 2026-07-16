"""Core chat controller orchestrating the AI pipeline."""

import time
from collections.abc import AsyncGenerator
from typing import Any

from app.ai.clients.ollama import OllamaClient
from app.ai.config import AISettings
from app.ai.exceptions import (
    PromptTooLongException,
    StreamingException,
)
from app.ai.memory.conversation import ConversationManager
from app.ai.models.model_manager import ModelManager
from app.ai.prompts.registry import PromptRegistry
from app.ai.schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    MessageRole,
)
from app.ai.schemas.model import ModelListResponse, ModelSwitchResponse, OllamaStatus
from app.ai.streaming.handler import StreamingHandler
from app.ai.utils.token_counter import estimate_token_count, validate_prompt_length
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatController:
    """Orchestrates the AI chat pipeline.

    Ties together the Ollama client, model manager, prompt registry,
    conversation manager, and streaming handler into a cohesive chat
    processing pipeline.
    """

    def __init__(
        self,
        ollama_client: OllamaClient,
        model_manager: ModelManager,
        prompt_registry: PromptRegistry,
        conversation_manager: ConversationManager,
        streaming_handler: StreamingHandler,
        settings: AISettings,
    ) -> None:
        self._ollama = ollama_client
        self._models = model_manager
        self._prompts = prompt_registry
        self._conversations = conversation_manager
        self._streaming = streaming_handler
        self._settings = settings

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Process a non-streaming chat request.

        Args:
            request: The validated chat request.

        Returns:
            A ``ChatResponse`` with the assistant's reply.

        Raises:
            PromptTooLongException: If the prompt exceeds the token limit.
        """
        start = time.monotonic()

        model = request.model or await self._models.get_active_model()
        await self._models.ensure_model_available(model)

        conversation = self._get_or_create_conversation(
            request.conversation_id, model
        )
        conversation_id = conversation.id

        if not validate_prompt_length(
            request.message, self._settings.MAX_PROMPT_LENGTH
        ):
            raise PromptTooLongException(
                f"Prompt exceeds {self._settings.MAX_PROMPT_LENGTH} token limit"
            )

        self._conversations.add_message(conversation_id, "user", request.message)

        context = self._build_context(conversation_id)
        prompt = self._prompts.get_default()
        messages = prompt.build_messages(request.message, context)

        temperature = request.temperature or self._settings.TEMPERATURE
        max_tokens = request.max_tokens or self._settings.MAX_RESPONSE_TOKENS

        result = await self._ollama.generate(
            model=model,
            messages=messages,
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        assistant_content = ""
        if isinstance(result, dict):
            msg = result.get("message", {})
            assistant_content = msg.get("content", "")

        self._conversations.add_message(
            conversation_id, "assistant", assistant_content
        )

        elapsed_ms = (time.monotonic() - start) * 1000
        token_count = estimate_token_count(assistant_content)

        logger.info(
            "Chat completed: conversation=%s model=%s tokens=%d time=%.1fms",
            conversation_id,
            model,
            token_count,
            elapsed_ms,
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=ChatMessage(
                role=MessageRole.ASSISTANT,
                content=assistant_content,
            ),
            model_used=model,
            response_time_ms=round(elapsed_ms, 1),
            token_count=token_count,
        )

    async def chat_stream(
        self, request: ChatRequest
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Process a streaming chat request.

        Yields:
            ``ChatStreamChunk`` instances as tokens are generated.
        """
        model = request.model or await self._models.get_active_model()
        await self._models.ensure_model_available(model)

        conversation = self._get_or_create_conversation(
            request.conversation_id, model
        )
        conversation_id = conversation.id

        if not validate_prompt_length(
            request.message, self._settings.MAX_PROMPT_LENGTH
        ):
            raise PromptTooLongException(
                f"Prompt exceeds {self._settings.MAX_PROMPT_LENGTH} token limit"
            )

        self._conversations.add_message(conversation_id, "user", request.message)

        context = self._build_context(conversation_id)
        prompt = self._prompts.get_default()
        messages = prompt.build_messages(request.message, context)

        temperature = request.temperature or self._settings.TEMPERATURE
        max_tokens = request.max_tokens or self._settings.MAX_RESPONSE_TOKENS

        full_response = ""

        try:
            async for chunk in self._ollama.generate_stream(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                chunk.conversation_id = conversation_id
                if chunk.content:
                    full_response += chunk.content
                yield chunk
        except Exception as exc:
            logger.error("Streaming error: %s", exc)
            raise StreamingException(str(exc)) from exc
        finally:
            if full_response:
                self._conversations.add_message(
                    conversation_id, "assistant", full_response
                )

    async def stop_generation(self, conversation_id: str) -> bool:
        """Stop an active generation.

        Args:
            conversation_id: The conversation to stop.

        Returns:
            ``True`` if a stream was stopped.
        """
        return await self._streaming.stop_stream(conversation_id)

    async def get_models(self) -> ModelListResponse:
        """Get list of available models with the active model highlighted.

        Returns:
            ``ModelListResponse`` with all installed models.
        """
        models = await self._models.get_available_models()
        active = await self._models.get_active_model()
        return ModelListResponse(models=models, active_model=active)

    async def switch_model(self, model_name: str) -> ModelSwitchResponse:
        """Switch the active model.

        Args:
            model_name: Target model identifier.

        Returns:
            ``ModelSwitchResponse`` with previous and current model.
        """
        return await self._models.switch_model(model_name)

    async def get_status(self) -> OllamaStatus:
        """Get Ollama and model status.

        Returns:
            ``OllamaStatus`` with connection and model info.
        """
        return await self._models.get_ollama_status()

    def _build_context(self, conversation_id: str) -> dict[str, Any]:
        """Build context from conversation history for prompt construction."""
        if not self._settings.CONVERSATION_MEMORY_ENABLED:
            return {}

        try:
            history = self._conversations.get_history(
                conversation_id,
                limit=self._settings.CONVERSATION_MAX_MESSAGES,
            )
            return {
                "history": [
                    {"role": msg.role.value, "content": msg.content}
                    for msg in history
                ]
            }
        except Exception:
            return {}

    def _get_or_create_conversation(
        self, conversation_id: str | None, model: str
    ) -> Any:
        """Retrieve an existing conversation or create a new one."""
        if conversation_id:
            return self._conversations.get_conversation(conversation_id)
        return self._conversations.create_conversation(model)
