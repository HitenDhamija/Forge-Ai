"""Communication model for agent coordination via Supervisor."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.agents.enterprise.schemas import AgentMessage, MessageType
from app.core.logging import get_logger

logger = get_logger(__name__)


class CommunicationBus:
    """Message bus for agent communication.

    Agents NEVER communicate directly.
    All communication flows through the Supervisor via this bus.
    """

    def __init__(self):
        """Initialize the communication bus."""
        self._messages: list[AgentMessage] = []
        self._pending_responses: dict[str, AgentMessage] = {}

    def create_message(
        self,
        sender_id: str,
        message_type: MessageType,
        content: dict[str, Any],
        receiver_id: str | None = None,
        requires_response: bool = False,
    ) -> AgentMessage:
        """Create a new message.

        Args:
            sender_id: ID of the sending agent.
            message_type: Type of message.
            content: Message content.
            receiver_id: Optional receiver ID (None for broadcast).
            requires_response: Whether response is required.

        Returns:
            Created message.
        """
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            timestamp=datetime.now(timezone.utc),
            requires_response=requires_response,
        )

        self._messages.append(message)
        logger.info(
            "Message created: %s from %s to %s",
            message_type.value,
            sender_id,
            receiver_id or "broadcast",
        )

        return message

    def get_messages(
        self,
        receiver_id: str | None = None,
        message_type: MessageType | None = None,
        limit: int = 50,
    ) -> list[AgentMessage]:
        """Get messages with optional filters.

        Args:
            receiver_id: Filter by receiver ID.
            message_type: Filter by message type.
            limit: Maximum messages to return.

        Returns:
            List of matching messages.
        """
        messages = self._messages

        if receiver_id:
            messages = [
                m for m in messages
                if m.receiver_id == receiver_id or m.receiver_id is None
            ]

        if message_type:
            messages = [m for m in messages if m.message_type == message_type]

        return messages[-limit:]

    def get_pending_responses(self, agent_id: str) -> list[AgentMessage]:
        """Get messages awaiting response from an agent.

        Args:
            agent_id: Agent ID.

        Returns:
            List of messages requiring response.
        """
        return [
            m for m in self._messages
            if m.receiver_id == agent_id
            and m.requires_response
            and m.id not in self._pending_responses
        ]

    def mark_response_sent(self, message_id: str) -> None:
        """Mark that a response has been sent for a message.

        Args:
            message_id: Original message ID.
        """
        if message_id in self._messages:
            self._pending_responses[message_id] = self._messages[-1]

    def create_task_assignment(
        self,
        supervisor_id: str,
        agent_id: str,
        task_id: str,
        workflow_id: str,
        title: str,
        description: str,
        context: dict[str, Any] | None = None,
        required_capabilities: list[str] | None = None,
        priority: str = "medium",
    ) -> AgentMessage:
        """Create a task assignment message.

        Args:
            supervisor_id: Supervisor agent ID.
            agent_id: Target agent ID.
            task_id: Task ID.
            workflow_id: Workflow ID.
            title: Task title.
            description: Task description.
            context: Additional context.
            required_capabilities: Required capabilities.
            priority: Task priority.

        Returns:
            Task assignment message.
        """
        return self.create_message(
            sender_id=supervisor_id,
            receiver_id=agent_id,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={
                "task_id": task_id,
                "workflow_id": workflow_id,
                "title": title,
                "description": description,
                "context": context or {},
                "required_capabilities": required_capabilities or [],
                "priority": priority,
            },
            requires_response=True,
        )

    def create_progress_update(
        self,
        agent_id: str,
        supervisor_id: str,
        task_id: str,
        progress: int,
        message: str,
    ) -> AgentMessage:
        """Create a progress update message.

        Args:
            agent_id: Reporting agent ID.
            supervisor_id: Supervisor ID.
            task_id: Task ID.
            progress: Progress percentage (0-100).
            message: Progress message.

        Returns:
            Progress update message.
        """
        return self.create_message(
            sender_id=agent_id,
            receiver_id=supervisor_id,
            message_type=MessageType.PROGRESS_UPDATE,
            content={
                "task_id": task_id,
                "progress": progress,
                "message": message,
            },
        )

    def create_task_result(
        self,
        agent_id: str,
        supervisor_id: str,
        task_id: str,
        status: str,
        output: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> AgentMessage:
        """Create a task result message.

        Args:
            agent_id: Agent ID.
            supervisor_id: Supervisor ID.
            task_id: Task ID.
            status: Result status.
            output: Task output.
            error: Error message if failed.

        Returns:
            Task result message.
        """
        message_type = MessageType.SUCCESS if status == "completed" else MessageType.FAILURE

        return self.create_message(
            sender_id=agent_id,
            receiver_id=supervisor_id,
            message_type=message_type,
            content={
                "task_id": task_id,
                "status": status,
                "output": output or {},
                "error": error,
            },
        )

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._pending_responses.clear()
