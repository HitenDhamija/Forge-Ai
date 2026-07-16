"""Execution Logger for Execution Engine.

Logs execution events and activities.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class LogEntry:
    """Single log entry."""

    timestamp: datetime
    level: LogLevel
    message: str
    execution_id: str
    step_id: str | None = None
    agent_id: str | None = None
    tool_id: str | None = None
    details: dict[str, Any] | None = None


@dataclass
class ExecutionLog:
    """Complete execution log."""

    execution_id: str
    entries: list[LogEntry] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class ExecutionLogger:
    """Logs execution events."""

    def __init__(self):
        """Initialize execution logger."""
        self._logs: dict[str, ExecutionLog] = {}

    def create_log(self, execution_id: str) -> ExecutionLog:
        """Create new execution log."""
        log = ExecutionLog(execution_id=execution_id)
        self._logs[execution_id] = log
        return log

    def log(
        self,
        execution_id: str,
        level: LogLevel,
        message: str,
        step_id: str | None = None,
        agent_id: str | None = None,
        tool_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> LogEntry:
        """Add log entry."""
        log = self._logs.get(execution_id)
        if not log:
            log = self.create_log(execution_id)

        entry = LogEntry(
            timestamp=datetime.utcnow(),
            level=level,
            message=message,
            execution_id=execution_id,
            step_id=step_id,
            agent_id=agent_id,
            tool_id=tool_id,
            details=details,
        )

        log.entries.append(entry)

        # Also log to system logger
        log_method = getattr(logger, level.value, logger.info)
        log_method("Execution %s: %s", execution_id[:8], message)

        return entry

    def get_log(self, execution_id: str) -> ExecutionLog | None:
        """Get execution log."""
        return self._logs.get(execution_id)

    def get_entries(
        self,
        execution_id: str,
        level: LogLevel | None = None,
        limit: int = 100,
    ) -> list[LogEntry]:
        """Get log entries."""
        log = self._logs.get(execution_id)
        if not log:
            return []

        entries = log.entries
        if level:
            entries = [e for e in entries if e.level == level]

        return entries[-limit:]

    def complete_log(self, execution_id: str) -> None:
        """Mark log as completed."""
        log = self._logs.get(execution_id)
        if log:
            log.completed_at = datetime.utcnow()

    def get_summary(self, execution_id: str) -> dict[str, Any]:
        """Get log summary."""
        log = self._logs.get(execution_id)
        if not log:
            return {}

        return {
            "execution_id": execution_id,
            "total_entries": len(log.entries),
            "debug_count": sum(1 for e in log.entries if e.level == LogLevel.DEBUG),
            "info_count": sum(1 for e in log.entries if e.level == LogLevel.INFO),
            "warning_count": sum(1 for e in log.entries if e.level == LogLevel.WARNING),
            "error_count": sum(1 for e in log.entries if e.level == LogLevel.ERROR),
            "critical_count": sum(1 for e in log.entries if e.level == LogLevel.CRITICAL),
            "started_at": log.started_at.isoformat(),
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        }
