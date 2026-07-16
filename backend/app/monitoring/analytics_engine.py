"""Analytics engine for generating trends, activity breakdowns, and reports from collected metrics."""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class TimeRange(str, Enum):
    """Time range for analytics queries."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class AnalyticsPeriod:
    """A labelled time period for analytics."""

    start_time: datetime
    end_time: datetime
    label: str


@dataclass
class ActivityData:
    """Activity data for a single period."""

    period: AnalyticsPeriod
    workflows_started: int
    workflows_completed: int
    tasks_completed: int
    tools_used: int
    memory_searches: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TrendData:
    """Trend comparison between current and previous periods."""

    metric_name: str
    current_value: float
    previous_value: float
    change_percent: float
    direction: str  # "up", "down", or "stable"


class AnalyticsEngine:
    """Generates analytics, trends, and reports from in-memory monitor data.

    Pulls data from workflow, tool, memory, agent, and execution monitors
    to produce time-based activity breakdowns and trend analysis.
    """

    def __init__(
        self,
        workflow_monitor: Any = None,
        tool_monitor: Any = None,
        memory_monitor: Any = None,
        agent_monitor: Any = None,
        execution_monitor: Any = None,
    ) -> None:
        """Initialize the analytics engine.

        Args:
            workflow_monitor: WorkflowMonitor instance.
            tool_monitor: ToolMonitor instance.
            memory_monitor: MemoryMonitor instance.
            agent_monitor: AgentMonitor instance.
            execution_monitor: ExecutionMonitor instance.
        """
        self._workflow_monitor = workflow_monitor
        self._tool_monitor = tool_monitor
        self._memory_monitor = memory_monitor
        self._agent_monitor = agent_monitor
        self._execution_monitor = execution_monitor

    async def get_daily_activity(self, days: int = 7) -> list[ActivityData]:
        """Get daily activity breakdown for the past N days.

        Args:
            days: Number of days to look back (default 7).

        Returns:
            List of ActivityData, one per day, most recent first.
        """
        now = datetime.now(timezone.utc)
        activities: list[ActivityData] = []

        for i in range(days):
            day_start = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            label = day_start.strftime("%Y-%m-%d")

            activity = await self._aggregate_activity(day_start, day_end, label)
            activities.append(activity)

        logger.debug("Generated daily activity for %d days", days)
        return activities

    async def get_weekly_activity(self, weeks: int = 4) -> list[ActivityData]:
        """Get weekly activity breakdown for the past N weeks.

        Args:
            weeks: Number of weeks to look back (default 4).

        Returns:
            List of ActivityData, one per week, most recent first.
        """
        now = datetime.now(timezone.utc)
        activities: list[ActivityData] = []

        for i in range(weeks):
            week_start = (now - timedelta(weeks=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            week_start -= timedelta(days=week_start.weekday())
            week_end = week_start + timedelta(weeks=1)
            label = f"W{week_start.isocalendar()[1]} {week_start.year}"

            activity = await self._aggregate_activity(week_start, week_end, label)
            activities.append(activity)

        logger.debug("Generated weekly activity for %d weeks", weeks)
        return activities

    async def get_monthly_activity(self, months: int = 12) -> list[ActivityData]:
        """Get monthly activity breakdown for the past N months.

        Args:
            months: Number of months to look back (default 12).

        Returns:
            List of ActivityData, one per month, most recent first.
        """
        now = datetime.now(timezone.utc)
        activities: list[ActivityData] = []

        for i in range(months):
            ref = now - timedelta(days=30 * i)
            month_start = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
            label = month_start.strftime("%B %Y")

            activity = await self._aggregate_activity(month_start, month_end, label)
            activities.append(activity)

        logger.debug("Generated monthly activity for %d months", months)
        return activities

    async def get_execution_time_trend(self, time_range: TimeRange) -> TrendData:
        """Get execution time trend comparing current vs previous period.

        Args:
            time_range: The time range to analyze.

        Returns:
            TrendData with execution time comparison.
        """
        now = datetime.now(timezone.utc)
        duration = self._time_range_duration(time_range)
        current_start = now - duration
        previous_start = current_start - duration

        current_avg = await self._avg_execution_time(current_start, now)
        previous_avg = await self._avg_execution_time(previous_start, current_start)

        return self._build_trend("execution_time_ms", current_avg, previous_avg)

    async def get_success_rate_trend(self, time_range: TimeRange) -> TrendData:
        """Get success rate trend comparing current vs previous period.

        Args:
            time_range: The time range to analyze.

        Returns:
            TrendData with success rate comparison.
        """
        now = datetime.now(timezone.utc)
        duration = self._time_range_duration(time_range)
        current_start = now - duration
        previous_start = current_start - duration

        current_rate = await self._success_rate(current_start, now)
        previous_rate = await self._success_rate(previous_start, current_start)

        return self._build_trend("success_rate", current_rate, previous_rate)

    async def get_most_active_agent(self) -> dict:
        """Get the most active agent based on task completions.

        Returns:
            Dictionary with agent_id, name, and task count.
        """
        if not self._agent_monitor:
            return {"agent_id": None, "name": None, "tasks_completed": 0}

        snapshots = await self._agent_monitor.snapshot()
        if not snapshots:
            return {"agent_id": None, "name": None, "tasks_completed": 0}

        top = max(snapshots, key=lambda s: s.tasks_completed)
        return {
            "agent_id": top.agent_id,
            "name": top.name,
            "agent_type": top.agent_type,
            "tasks_completed": top.tasks_completed,
            "tasks_failed": top.tasks_failed,
            "avg_execution_time": top.avg_execution_time,
        }

    async def get_most_used_tool(self) -> dict:
        """Get the most used tool based on execution count.

        Returns:
            Dictionary with tool_id and usage count.
        """
        if not self._tool_monitor:
            return {"tool_id": None, "total_calls": 0}

        overview = await self._tool_monitor.get_overview()
        slowest = await self._tool_monitor.get_slowest_tools(limit=100)

        if not slowest:
            return {"tool_id": None, "total_calls": 0}

        tool_calls: dict[str, int] = {}
        for record in self._tool_monitor._history:
            tool_calls[record.tool_id] = tool_calls.get(record.tool_id, 0) + 1

        if not tool_calls:
            return {"tool_id": None, "total_calls": 0}

        top_tool_id = max(tool_calls, key=tool_calls.get)
        perf = await self._tool_monitor.get_tool_performance(top_tool_id)

        return {
            "tool_id": top_tool_id,
            "total_calls": perf["total_calls"],
            "avg_latency_ms": perf["avg_latency_ms"],
            "error_rate": perf["error_rate"],
        }

    async def get_failure_trends(self, time_range: TimeRange) -> list[dict]:
        """Get failure trends over time for the specified range.

        Args:
            time_range: The time range to analyze.

        Returns:
            List of dictionaries with period label and failure count.
        """
        now = datetime.now(timezone.utc)
        duration = self._time_range_duration(time_range)
        start = now - duration

        failures: list[dict] = []

        if self._workflow_monitor:
            for record in self._workflow_monitor._workflows.values():
                if record.status.value == "failed" and record.completed_at:
                    if start <= record.completed_at.replace(tzinfo=timezone.utc) <= now:
                        failures.append({
                            "type": "workflow",
                            "id": record.workflow_id,
                            "title": record.title,
                            "timestamp": record.completed_at.isoformat(),
                        })

        if self._execution_monitor:
            for exec_id, records in self._execution_monitor._records.items():
                for record in records:
                    if record.status.value == "failed":
                        ts = record.timestamp
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        if start <= ts <= now:
                            failures.append({
                                "type": "execution",
                                "id": exec_id,
                                "event_type": record.event_type,
                                "timestamp": record.timestamp.isoformat(),
                            })

        if self._tool_monitor:
            for record in self._tool_monitor._history:
                if not record.success:
                    if start <= record.timestamp <= now:
                        failures.append({
                            "type": "tool",
                            "id": record.tool_id,
                            "operation": record.operation,
                            "error": record.error,
                            "timestamp": record.timestamp.isoformat(),
                        })

        failures.sort(key=lambda f: f.get("timestamp", ""), reverse=True)
        logger.debug("Found %d failures in %s range", len(failures), time_range.value)
        return failures

    async def get_repository_stats(self) -> dict:
        """Get repository analytics from memory and repo intelligence.

        Returns:
            Dictionary with repository-level statistics.
        """
        total_repos = 0
        total_chunks = 0
        collections: list[dict] = []

        if self._memory_monitor:
            overview = await self._memory_monitor.get_overview()
            retrieval = await self._memory_monitor.get_retrieval_performance()

            total_chunks = retrieval.get("total_searches", 0)

        if hasattr(self, "_memory_service") and self._memory_service:
            try:
                stats = await self._memory_service.get_stats()
                total_repos = getattr(stats, "total_repositories", 0)
                total_chunks = getattr(stats, "total_chunks", 0)
                collections = [
                    {"name": c.name, "count": c.count}
                    for c in getattr(stats, "collections", [])
                ]
            except Exception:
                logger.debug("Failed to get memory stats for repository analytics")

        return {
            "total_repositories": total_repos,
            "total_chunks": total_chunks,
            "collections": collections,
        }

    async def get_learning_growth(self) -> dict:
        """Get learning growth metrics over time.

        Returns:
            Dictionary with learning progression data.
        """
        total_experiences = 0
        total_patterns = 0
        total_lessons = 0
        success_rate = 0.0

        if self._execution_monitor:
            perf = await self._execution_monitor.get_execution_performance()
            success_rate = perf.get("success_rate", 0.0)

        return {
            "total_experiences": total_experiences,
            "total_patterns": total_patterns,
            "total_lessons": total_lessons,
            "success_rate": round(success_rate, 4),
            "growth_indicators": {
                "pattern_recognition": total_patterns > 0,
                "experience_accumulation": total_experiences > 0,
                "lesson_capture": total_lessons > 0,
            },
        }

    async def get_overview_analytics(self) -> dict:
        """Get high-level analytics summary across all monitors.

        Returns:
            Dictionary with aggregated analytics overview.
        """
        workflow_perf = {}
        tool_overview = {}
        agent_overview = {}
        execution_perf = {}
        memory_overview = {}

        if self._workflow_monitor:
            workflow_perf = await self._workflow_monitor.get_workflow_performance()

        if self._tool_monitor:
            tool_overview = await self._tool_monitor.get_overview()

        if self._agent_monitor:
            agent_overview = await self._agent_monitor.get_overview()

        if self._execution_monitor:
            execution_perf = await self._execution_monitor.get_execution_performance()

        if self._memory_monitor:
            memory_overview = await self._memory_monitor.get_overview()

        return {
            "workflows": workflow_perf,
            "tools": tool_overview,
            "agents": agent_overview,
            "execution": execution_perf,
            "memory": memory_overview,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _aggregate_activity(
        self,
        start: datetime,
        end: datetime,
        label: str,
    ) -> ActivityData:
        """Aggregate activity counts for a given time period.

        Args:
            start: Period start time (inclusive).
            end: Period end time (exclusive).
            label: Human-readable period label.

        Returns:
            ActivityData with aggregated counts.
        """
        workflows_started = 0
        workflows_completed = 0
        tasks_completed = 0
        tools_used = 0
        memory_searches = 0

        if self._workflow_monitor:
            for record in self._workflow_monitor._workflows.values():
                if record.started_at:
                    started = record.started_at
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=timezone.utc)
                    if start <= started < end:
                        workflows_started += 1
                if record.completed_at:
                    completed = record.completed_at
                    if completed.tzinfo is None:
                        completed = completed.replace(tzinfo=timezone.utc)
                    if start <= completed < end:
                        workflows_completed += 1
                tasks_completed += record.tasks_completed

        if self._tool_monitor:
            seen_tools: set[str] = set()
            for record in self._tool_monitor._history:
                ts = record.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if start <= ts < end:
                    seen_tools.add(record.tool_id)
            tools_used = len(seen_tools)

        if self._memory_monitor:
            for record in self._memory_monitor._history:
                ts = record.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if start <= ts < end:
                    memory_searches += 1

        return ActivityData(
            period=AnalyticsPeriod(start_time=start, end_time=end, label=label),
            workflows_started=workflows_started,
            workflows_completed=workflows_completed,
            tasks_completed=tasks_completed,
            tools_used=tools_used,
            memory_searches=memory_searches,
        )

    async def _avg_execution_time(
        self, start: datetime, end: datetime
    ) -> float:
        """Calculate average execution time for completed workflows in a window.

        Args:
            start: Window start (inclusive).
            end: Window end (exclusive).

        Returns:
            Average execution time in milliseconds, or 0.0 if none found.
        """
        durations: list[float] = []

        if self._workflow_monitor:
            for record in self._workflow_monitor._workflows.values():
                if record.duration > 0 and record.completed_at:
                    completed = record.completed_at
                    if completed.tzinfo is None:
                        completed = completed.replace(tzinfo=timezone.utc)
                    if start <= completed < end:
                        durations.append(record.duration * 1000)

        if self._execution_monitor:
            for records in self._execution_monitor._records.values():
                for record in records:
                    if record.event_type == "complete":
                        dur = record.data.get("duration_seconds", 0.0)
                        if dur > 0:
                            ts = record.timestamp
                            if ts.tzinfo is None:
                                ts = ts.replace(tzinfo=timezone.utc)
                            if start <= ts < end:
                                durations.append(dur * 1000)

        return round(statistics.mean(durations), 2) if durations else 0.0

    async def _success_rate(
        self, start: datetime, end: datetime
    ) -> float:
        """Calculate success rate for completed workflows in a window.

        Args:
            start: Window start (inclusive).
            end: Window end (exclusive).

        Returns:
            Success rate as a float between 0.0 and 1.0.
        """
        completed = 0
        failed = 0

        if self._workflow_monitor:
            for record in self._workflow_monitor._workflows.values():
                if record.completed_at:
                    ts = record.completed_at
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if start <= ts < end:
                        if record.status.value == "completed":
                            completed += 1
                        elif record.status.value == "failed":
                            failed += 1

        total = completed + failed
        return round(completed / total, 4) if total > 0 else 0.0

    @staticmethod
    def _time_range_duration(time_range: TimeRange) -> timedelta:
        """Get the timedelta for a TimeRange enum value.

        Args:
            time_range: The time range.

        Returns:
            Corresponding timedelta duration.
        """
        mapping = {
            TimeRange.HOUR: timedelta(hours=1),
            TimeRange.DAY: timedelta(days=1),
            TimeRange.WEEK: timedelta(weeks=1),
            TimeRange.MONTH: timedelta(days=30),
        }
        return mapping.get(time_range, timedelta(days=1))

    @staticmethod
    def _build_trend(
        metric_name: str,
        current_value: float,
        previous_value: float,
    ) -> TrendData:
        """Build a TrendData from current and previous values.

        Args:
            metric_name: Name of the metric.
            current_value: Current period value.
            previous_value: Previous period value.

        Returns:
            TrendData with computed direction and change percentage.
        """
        if previous_value == 0 and current_value == 0:
            change_percent = 0.0
            direction = "stable"
        elif previous_value == 0:
            change_percent = 100.0
            direction = "up"
        else:
            change_percent = round(
                ((current_value - previous_value) / abs(previous_value)) * 100, 2
            )
            if change_percent > 0.01:
                direction = "up"
            elif change_percent < -0.01:
                direction = "down"
            else:
                direction = "stable"

        return TrendData(
            metric_name=metric_name,
            current_value=round(current_value, 4),
            previous_value=round(previous_value, 4),
            change_percent=change_percent,
            direction=direction,
        )
