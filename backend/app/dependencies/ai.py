"""AI dependency injection for FastAPI."""

from fastapi import Request

from app.ai.clients.ollama import OllamaClient
from app.ai.controllers.chat_controller import ChatController
from app.ai.memory.conversation import ConversationManager
from app.ai.models.model_manager import ModelManager
from app.ai.prompts.registry import PromptRegistry


def get_chat_controller(request: Request) -> ChatController:
    """Return the chat controller from app state."""
    return request.app.state.chat_controller


def get_ollama_client(request: Request) -> OllamaClient:
    """Return the Ollama client from app state."""
    return request.app.state.ollama_client


def get_model_manager(request: Request) -> ModelManager:
    """Return the model manager from app state."""
    return request.app.state.model_manager


def get_conversation_manager(request: Request) -> ConversationManager:
    """Return the conversation manager from app state."""
    return request.app.state.conversation_manager


def get_prompt_registry(request: Request) -> PromptRegistry:
    """Return the prompt registry from app state."""
    return request.app.state.prompt_registry
