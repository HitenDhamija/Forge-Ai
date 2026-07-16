"""Unified activity feed for the enterprise experience."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class ActivityType(str, Enum):
    """Broad category of an activity."""

    workflow = "workflow"
    repository = "repository"
    learning = "learning"
    execution = "execution"
    agent = "agent"
    organization = "organization"
    system = "system"
    user = "user"


class ActivityAction(str, Enum):
    """Specific action performed during an activity."""

    created = "created"
    updated = "updated"
    deleted = "deleted"
    started = "started"
    completed = "completed"
    failed = "failed"
    approved = "approved"
    rejected = "rejected"
    deployed = "deployed"
    indexed = "indexed"


@dataclass
class Activity:
    """A single entry in the activity feed."""

    id: str
    type: ActivityType
    action: ActivityAction
    title: str
    description: str
    entity_type: str
    entity_id: str
    user_id: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    icon: str = ""


# ------------------------------------------------------------------
# Activity icons mapping
# ------------------------------------------------------------------

ACTIVITY_ICONS: dict[ActivityType, str] = {
    ActivityType.workflow: "GitMerge",
    ActivityType.repository: "GitBranch",
    ActivityType.learning: "BookOpen",
    ActivityType.execution: "Play",
    ActivityType.agent: "Bot",
    ActivityType.organization: "Building",
    ActivityType.system: "Settings",
    ActivityType.user: "User",
}


class ActivityFeed:
    """Append-only activity feed with query helpers."""

    def __init__(self) -> None:
        self._activities: dict[str, Activity] = []

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def log_activity(
        self,
        type: ActivityType,
        action: ActivityAction,
        title: str,
        description: str,
        entity_type: str,
        entity_id: str,
        user_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> Activity:
        """Record a new activity and return it."""
        activity = Activity(
            id=str(uuid.uuid4()),
            type=type,
            action=action,
            title=title,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {},
            icon=ACTIVITY_ICONS.get(type, "Info"),
        )
        self._activities.append(activity)
        return activity

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_activities(
        self,
        limit: int = 50,
        activity_type: ActivityType | None = None,
        user_id: str | None = None,
    ) -> list[Activity]:
        """Return activities with optional filters, newest first."""
        results: list[Activity] = []
        for a in reversed(self._activities):
            if activity_type is not None and a.type != activity_type:
                continue
            if user_id is not None and a.user_id != user_id:
                continue
            results.append(a)
            if len(results) >= limit:
                break
        return results

    def get_activity(self, activity_id: str) -> Activity | None:
        """Return a single activity by id or ``None``."""
        for a in self._activities:
            if a.id == activity_id:
                return a
        return None

    def get_entity_activities(
        self, entity_type: str, entity_id: str
    ) -> list[Activity]:
        """Return all activities related to a specific entity."""
        return [
            a
            for a in reversed(self._activities)
            if a.entity_type == entity_type and a.entity_id == entity_id
        ]

    def get_user_activities(
        self, user_id: str, limit: int = 20
    ) -> list[Activity]:
        """Return activities performed by *user_id*."""
        results: list[Activity] = []
        for a in reversed(self._activities):
            if a.user_id == user_id:
                results.append(a)
                if len(results) >= limit:
                    break
        return results

    def get_recent(self, limit: int = 10) -> list[Activity]:
        """Return the most recent activities."""
        return list(reversed(self._activities[-limit:]))

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate statistics about recorded activities."""
        total = len(self._activities)
        by_type: dict[str, int] = {}
        by_action: dict[str, int] = {}
        by_user: dict[str, int] = {}

        for a in self._activities:
            by_type[a.type.value] = by_type.get(a.type.value, 0) + 1
            by_action[a.action.value] = by_action.get(a.action.value, 0) + 1
            by_user[a.user_id] = by_user.get(a.user_id, 0) + 1

        return {
            "total": total,
            "by_type": by_type,
            "by_action": by_action,
            "by_user": by_user,
        }

    def clear_old(self, days: int = 30) -> int:
        """Remove activities older than *days* days.

        Returns the number of activities removed.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        before = len(self._activities)
        self._activities = [a for a in self._activities if a.timestamp >= cutoff]
        return before - len(self._activities)


# ------------------------------------------------------------------
# Global singleton
# ------------------------------------------------------------------

activity_feed = ActivityFeed()
