"""In-memory conversation manager."""

import uuid
from datetime import UTC, datetime

from app.ai.config import AISettings
from app.ai.exceptions import ConversationNotFoundException
from app.ai.schemas.chat import ChatMessage, ConversationHistory, MessageRole
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConversationManager:
    """Manages conversation history in memory.

    Architecture supports future migration to PostgreSQL by abstracting
    storage behind the public interface.
    """

    def __init__(self, settings: AISettings) -> None:
        self._settings = settings
        self._conversations: dict[str, ConversationHistory] = {}

    def create_conversation(self, model: str) -> ConversationHistory:
        """Create and return a new empty conversation.

        Args:
            model: The model that will be used for this conversation.

        Returns:
            The newly created ``ConversationHistory``.
        """
        conv_id = self._generate_id()
        conversation = ConversationHistory(
            id=conv_id,
            title="New Conversation",
            messages=[],
            model_used=model,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            message_count=0,
        )
        self._conversations[conv_id] = conversation
        logger.info("Created conversation %s with model %s", conv_id, model)
        return conversation

    def get_conversation(self, conversation_id: str) -> ConversationHistory:
        """Retrieve a conversation by ID.

        Args:
            conversation_id: The conversation identifier.

        Returns:
            The ``ConversationHistory`` object.

        Raises:
            ConversationNotFoundException: If the conversation does not exist.
        """
        conversation = self._conversations.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundException(
                f"Conversation '{conversation_id}' not found"
            )
        return conversation

    def add_message(
        self, conversation_id: str, role: str, content: str
    ) -> ChatMessage:
        """Add a message to a conversation.

        Args:
            conversation_id: Target conversation.
            role: Message role (``system``, ``user``, ``assistant``).
            content: Message text.

        Returns:
            The created ``ChatMessage``.

        Raises:
            ConversationNotFoundException: If the conversation does not exist.
        """
        conversation = self.get_conversation(conversation_id)

        message = ChatMessage(
            role=MessageRole(role),
            content=content,
            timestamp=datetime.now(UTC),
        )
        conversation.messages.append(message)
        conversation.updated_at = datetime.now(UTC)
        conversation.message_count = len(conversation.messages)

        if (
            conversation.message_count == 1
            and role == "user"
            and conversation.title == "New Conversation"
        ):
            conversation.title = self._generate_title(content)

        return message

    def get_history(
        self, conversation_id: str, limit: int = 20
    ) -> list[ChatMessage]:
        """Get message history for a conversation.

        Args:
            conversation_id: Target conversation.
            limit: Maximum number of recent messages to return.

        Returns:
            List of ``ChatMessage`` objects.

        Raises:
            ConversationNotFoundException: If the conversation does not exist.
        """
        conversation = self.get_conversation(conversation_id)
        return conversation.messages[-limit:]

    def list_conversations(self) -> list[ConversationHistory]:
        """List all conversations ordered by most recently updated.

        Returns:
            List of ``ConversationHistory`` objects.
        """
        return sorted(
            self._conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation.

        Args:
            conversation_id: The conversation to delete.

        Returns:
            ``True`` if deleted, ``False`` if not found.
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info("Deleted conversation %s", conversation_id)
            return True
        return False

    def clear_conversation(self, conversation_id: str) -> bool:
        """Clear all messages in a conversation.

        Args:
            conversation_id: The conversation to clear.

        Returns:
            ``True`` if cleared, ``False`` if not found.

        Raises:
            ConversationNotFoundException: If the conversation does not exist.
        """
        conversation = self.get_conversation(conversation_id)
        conversation.messages.clear()
        conversation.updated_at = datetime.now(UTC)
        conversation.message_count = 0
        conversation.title = "New Conversation"
        return True

    def _generate_id(self) -> str:
        """Generate a unique conversation ID."""
        return uuid.uuid4().hex[:12]

    def _generate_title(self, first_message: str) -> str:
        """Generate a conversation title from the first user message.

        Truncates to 60 characters with ellipsis if needed.
        """
        title = first_message.strip().replace("\n", " ")[:60]
        if len(first_message.strip()) > 60:
            title += "..."
        return title
