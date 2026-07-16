"""Agent memory system for short-term and task memory."""

from datetime import datetime, timezone
from typing import Any

from app.agents.enterprise.schemas import AgentMemory
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentMemoryManager:
    """Manages agent memory including short-term and task memory.

    Every agent has:
    - Short-Term Memory: Recent interactions and context
    - Task Memory: History of completed tasks
    - Execution Context: Current task context
    - Conversation State: Current conversation state

    Agents do NOT own:
    - Long-Term Memory (belongs to Memory Engine)
    - Repository Memory (belongs to Memory Engine)
    """

    def __init__(self, max_short_term: int = 50, max_task_memory: int = 100):
        """Initialize the memory manager.

        Args:
            max_short_term: Maximum items in short-term memory.
            max_task_memory: Maximum items in task memory.
        """
        self.max_short_term = max_short_term
        self.max_task_memory = max_task_memory
        self._memory = AgentMemory()

    def add_short_term(self, item: dict[str, Any]) -> None:
        """Add item to short-term memory.

        Args:
            item: Memory item to add.
        """
        item["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._memory.short_term.append(item)

        if len(self._memory.short_term) > self.max_short_term:
            self._memory.short_term = self._memory.short_term[-self.max_short_term:]

    def add_task_memory(self, task_result: dict[str, Any]) -> None:
        """Add completed task to task memory.

        Args:
            task_result: Task result to remember.
        """
        task_result["completed_at"] = datetime.now(timezone.utc).isoformat()
        self._memory.task_memory.append(task_result)

        if len(self._memory.task_memory) > self.max_task_memory:
            self._memory.task_memory = self._memory.task_memory[-self.max_task_memory:]

    def update_execution_context(self, context: dict[str, Any]) -> None:
        """Update current execution context.

        Args:
            context: New context to merge.
        """
        self._memory.execution_context.update(context)

    def clear_execution_context(self) -> None:
        """Clear execution context."""
        self._memory.execution_context = {}

    def add_conversation(self, role: str, content: str) -> None:
        """Add conversation entry.

        Args:
            role: Message role (user/assistant/system).
            content: Message content.
        """
        self._memory.conversation_state.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def get_short_term(self, limit: int = 10) -> list[dict]:
        """Get recent short-term memory items.

        Args:
            limit: Maximum items to return.

        Returns:
            List of recent memory items.
        """
        return self._memory.short_term[-limit:]

    def get_task_memory(self, limit: int = 10) -> list[dict]:
        """Get recent task memory items.

        Args:
            limit: Maximum items to return.

        Returns:
            List of recent task results.
        """
        return self._memory.task_memory[-limit:]

    def get_execution_context(self) -> dict[str, Any]:
        """Get current execution context.

        Returns:
            Current context dictionary.
        """
        return self._memory.execution_context.copy()

    def get_conversation(self, limit: int = 20) -> list[dict]:
        """Get recent conversation entries.

        Args:
            limit: Maximum entries to return.

        Returns:
            List of conversation entries.
        """
        return self._memory.conversation_state[-limit:]

    def get_memory(self) -> AgentMemory:
        """Get complete memory state.

        Returns:
            Complete agent memory.
        """
        return self._memory.copy()

    def set_memory(self, memory: AgentMemory) -> None:
        """Set memory state.

        Args:
            memory: Memory state to set.
        """
        self._memory = memory

    def clear(self) -> None:
        """Clear all memory."""
        self._memory = AgentMemory()

    def search_task_memory(self, query: str) -> list[dict]:
        """Search task memory for relevant entries.

        Args:
            query: Search query.

        Returns:
            List of matching task results.
        """
        query_lower = query.lower()
        results = []

        for task in self._memory.task_memory:
            title = task.get("title", "").lower()
            description = task.get("description", "").lower()
            if query_lower in title or query_lower in description:
                results.append(task)

        return results
