"""Notification center for the enterprise experience."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class NotificationType(str, Enum):
    """Types of notifications in the system."""

    workflow_started = "workflow_started"
    workflow_finished = "workflow_finished"
    agent_failed = "agent_failed"
    approval_required = "approval_required"
    deployment_ready = "deployment_ready"
    learning_updated = "learning_updated"
    plugin_installed = "plugin_installed"
    repository_indexed = "repository_indexed"
    system_alert = "system_alert"
    mention = "mention"
    comment = "comment"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class NotificationStatus(str, Enum):
    """Read status of a notification."""

    unread = "unread"
    read = "read"
    archived = "archived"


@dataclass
class Notification:
    """Represents a single notification."""

    id: str
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority
    status: NotificationStatus
    entity_type: str
    entity_id: str
    user_id: str
    created_at: datetime
    read_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class NotificationCenter:
    """Central hub for creating, querying, and managing notifications."""

    def __init__(self) -> None:
        self._notifications: dict[str, Notification] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create_notification(
        self,
        type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.medium,
        entity_type: str = "",
        entity_id: str = "",
        user_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Notification:
        """Create and store a new notification, returning it."""
        now = datetime.now(timezone.utc)
        notification = Notification(
            id=str(uuid.uuid4()),
            type=type,
            title=title,
            message=message,
            priority=priority,
            status=NotificationStatus.unread,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            created_at=now,
            metadata=metadata or {},
        )
        self._notifications[notification.id] = notification
        return notification

    def get_notifications(
        self,
        user_id: str,
        status: NotificationStatus | None = None,
        limit: int = 50,
    ) -> list[Notification]:
        """Return notifications for *user_id*, optionally filtered by status."""
        results: list[Notification] = []
        for n in self._notifications.values():
            if n.user_id != user_id:
                continue
            if status is not None and n.status != status:
                continue
            results.append(n)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]

    def get_notification(self, notification_id: str) -> Notification | None:
        """Return a single notification by id or ``None``."""
        return self._notifications.get(notification_id)

    def mark_read(self, notification_id: str) -> bool:
        """Mark a notification as read. Returns ``True`` on success."""
        n = self._notifications.get(notification_id)
        if n is None:
            return False
        n.status = NotificationStatus.read
        n.read_at = datetime.now(timezone.utc)
        return True

    def mark_all_read(self, user_id: str) -> int:
        """Mark every unread notification for *user_id* as read.

        Returns the number of notifications updated.
        """
        count = 0
        now = datetime.now(timezone.utc)
        for n in self._notifications.values():
            if n.user_id == user_id and n.status == NotificationStatus.unread:
                n.status = NotificationStatus.read
                n.read_at = now
                count += 1
        return count

    def archive(self, notification_id: str) -> bool:
        """Archive a notification. Returns ``True`` on success."""
        n = self._notifications.get(notification_id)
        if n is None:
            return False
        n.status = NotificationStatus.archived
        return True

    def delete(self, notification_id: str) -> bool:
        """Permanently remove a notification. Returns ``True`` on success."""
        if notification_id in self._notifications:
            del self._notifications[notification_id]
            return True
        return False

    def get_unread_count(self, user_id: str) -> int:
        """Return the number of unread notifications for *user_id*."""
        return sum(
            1
            for n in self._notifications.values()
            if n.user_id == user_id and n.status == NotificationStatus.unread
        )

    def get_notifications_by_type(
        self, type: NotificationType, limit: int = 20
    ) -> list[Notification]:
        """Return notifications matching *type*, newest first."""
        results = [n for n in self._notifications.values() if n.type == type]
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results[:limit]

    def get_notification_stats(self) -> dict[str, Any]:
        """Return aggregate statistics about stored notifications."""
        total = len(self._notifications)
        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_priority: dict[str, int] = {}

        for n in self._notifications.values():
            by_status[n.status.value] = by_status.get(n.status.value, 0) + 1
            by_type[n.type.value] = by_type.get(n.type.value, 0) + 1
            by_priority[n.priority.value] = by_priority.get(n.priority.value, 0) + 1

        return {
            "total": total,
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
        }

    def clear_old(self, days: int = 30) -> int:
        """Delete notifications older than *days* days.

        Returns the number of notifications removed.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        to_delete = [
            nid
            for nid, n in self._notifications.items()
            if n.created_at < cutoff
        ]
        for nid in to_delete:
            del self._notifications[nid]
        return len(to_delete)


# ------------------------------------------------------------------
# Pre-defined notification templates
# ------------------------------------------------------------------


def workflow_started_template(title: str, workflow_id: str) -> tuple[str, str]:
    """Return (title, message) for a workflow-started notification."""
    return (
        "Workflow Started",
        f"Workflow '{title}' ({workflow_id}) has been started.",
    )


def workflow_completed_template(
    title: str, workflow_id: str, duration: str
) -> tuple[str, str]:
    """Return (title, message) for a workflow-completed notification."""
    return (
        "Workflow Completed",
        f"Workflow '{title}' ({workflow_id}) completed in {duration}.",
    )


def agent_failed_template(agent_id: str, error: str) -> tuple[str, str]:
    """Return (title, message) for an agent-failed notification."""
    return (
        "Agent Failed",
        f"Agent '{agent_id}' encountered an error: {error}",
    )


def approval_required_template(
    workflow_id: str, requester: str
) -> tuple[str, str]:
    """Return (title, message) for an approval-required notification."""
    return (
        "Approval Required",
        f"User '{requester}' requires approval for workflow '{workflow_id}'.",
    )


def deployment_ready_template(
    environment: str, version: str
) -> tuple[str, str]:
    """Return (title, message) for a deployment-ready notification."""
    return (
        "Deployment Ready",
        f"Version '{version}' is ready to deploy to '{environment}'.",
    )


# ------------------------------------------------------------------
# Global singleton
# ------------------------------------------------------------------

notification_center = NotificationCenter()
