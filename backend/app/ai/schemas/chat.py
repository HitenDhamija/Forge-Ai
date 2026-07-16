"""Chat request/response schemas."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Possible roles for a chat message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime | None = Field(default_factory=lambda: datetime.now(UTC))


class ChatRequest(BaseModel):
    """Request body for sending a chat message."""

    message: str = Field(..., min_length=1, description="User message content")
    model: str | None = Field(default=None, description="Model to use for generation")
    conversation_id: str | None = Field(
        default=None, description="Existing conversation ID"
    )
    stream: bool = Field(default=True, description="Enable streaming response")
    temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int | None = Field(
        default=None, ge=1, description="Maximum tokens in response"
    )


class ChatResponse(BaseModel):
    """Response body for a non-streaming chat request."""

    conversation_id: str
    message: ChatMessage
    model_used: str
    response_time_ms: float
    token_count: int | None = None


class ChatStreamChunk(BaseModel):
    """A single chunk in a streaming chat response."""

    conversation_id: str
    content: str
    done: bool = False
    model: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ConversationHistory(BaseModel):
    """Full conversation with its message history."""

    id: str
    title: str
    messages: list[ChatMessage] = Field(default_factory=list)
    model_used: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    message_count: int = 0
