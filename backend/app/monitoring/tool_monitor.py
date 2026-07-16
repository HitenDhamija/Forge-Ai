"""Tool execution monitoring, health tracking, and performance metrics."""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolHealthStatus(str, Enum):
    """Tool health classification."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class ToolExecutionRecord:
    """Record of a single tool execution."""

    tool_id: str
    operation: str
    duration_ms: float
    success: bool
    error: str | None
    timestamp: datetime
    agent_id: str


@dataclass
class ToolStatusSnapshot:
    """Current status snapshot for a tool."""

    tool_id: str
    name: str
    provider: str
    status: str
    total_calls: int
    success_count: int
    error_count: int
    avg_latency: float
    p95_latency: float
    last_used: datetime | None
    health_status: ToolHealthStatus


class ToolMonitor:
    """Monitors tool execution, health, and performance metrics.

    Stores execution history in-memory with timestamps for real-time
    analytics and health determination.
    """

    def __init__(self) -> None:
        self._history: list[ToolExecutionRecord] = []

    def _records_for_tool(self, tool_id: str) -> list[ToolExecutionRecord]:
        return [r for r in self._history if r.tool_id == tool_id]

    @staticmethod
    def _percentile(values: list[float], pct: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * pct / 100)
        idx = min(idx, len(sorted_vals) - 1)
        return sorted_vals[idx]

    async def snapshot(self, tool_registry) -> list[ToolStatusSnapshot]:
        """Get current tool states from the registry.

        Args:
            tool_registry: ToolRegistry instance with list_tools().

        Returns:
            List of ToolStatusSnapshot for every registered tool.
        """
        snapshots: list[ToolStatusSnapshot] = []
        definitions = tool_registry.list_tools()

        for defn in definitions:
            records = self._records_for_tool(defn.id)
            latencies = [r.duration_ms for r in records]
            errors = sum(1 for r in records if not r.success)
            last_used = max((r.timestamp for r in records), default=None)

            avg_lat = statistics.mean(latencies) if latencies else 0.0
            p95_lat = self._percentile(latencies, 95)

            health = await self.get_tool_health(defn.id)

            snapshots.append(
                ToolStatusSnapshot(
                    tool_id=defn.id,
                    name=defn.name,
                    provider=defn.provider.value,
                    status=defn.health.status.value,
                    total_calls=len(records),
                    success_count=len(records) - errors,
                    error_count=errors,
                    avg_latency=round(avg_lat, 2),
                    p95_latency=round(p95_lat, 2),
                    last_used=last_used,
                    health_status=health,
                )
            )

        return snapshots

    async def record_execution(
        self,
        tool_id: str,
        operation: str,
        duration_ms: float,
        success: bool,
        error: str | None,
        agent_id: str,
    ) -> None:
        """Record a tool execution event.

        Args:
            tool_id: Tool identifier.
            operation: Operation that was executed.
            duration_ms: Execution duration in milliseconds.
            success: Whether execution succeeded.
            error: Error message if execution failed.
            agent_id: Agent that invoked the tool.
        """
        record = ToolExecutionRecord(
            tool_id=tool_id,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            timestamp=datetime.now(timezone.utc),
            agent_id=agent_id,
        )
        self._history.append(record)

        logger.info(
            "Tool execution recorded: tool=%s op=%s dur=%.1fms success=%s",
            tool_id,
            operation,
            duration_ms,
            success,
        )

    async def get_tool_history(
        self,
        tool_id: str,
        hours: int = 24,
    ) -> list[ToolExecutionRecord]:
        """Get execution history for a tool within a time window.

        Args:
            tool_id: Tool identifier.
            hours: Lookback window in hours.

        Returns:
            List of ToolExecutionRecord sorted by timestamp descending.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        records = [
            r for r in self._records_for_tool(tool_id) if r.timestamp >= cutoff
        ]
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records

    async def get_tool_performance(self, tool_id: str) -> dict:
        """Get performance metrics for a tool.

        Args:
            tool_id: Tool identifier.

        Returns:
            Dictionary with latency percentiles, throughput, and error rate.
        """
        records = self._records_for_tool(tool_id)
        latencies = [r.duration_ms for r in records]

        if not records:
            return {
                "tool_id": tool_id,
                "total_calls": 0,
                "avg_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "min_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "throughput_per_hour": 0.0,
                "error_rate": 0.0,
            }

        errors = sum(1 for r in records if not r.success)

        now = datetime.now(timezone.utc)
        recent = [r for r in records if r.timestamp >= now - timedelta(hours=1)]
        throughput = len(recent)

        return {
            "tool_id": tool_id,
            "total_calls": len(records),
            "avg_latency_ms": round(statistics.mean(latencies), 2),
            "p50_latency_ms": round(self._percentile(latencies, 50), 2),
            "p95_latency_ms": round(self._percentile(latencies, 95), 2),
            "p99_latency_ms": round(self._percentile(latencies, 99), 2),
            "min_latency_ms": round(min(latencies), 2),
            "max_latency_ms": round(max(latencies), 2),
            "throughput_per_hour": throughput,
            "error_rate": round(errors / len(records) * 100, 2),
        }

    async def get_tool_health(self, tool_id: str) -> ToolHealthStatus:
        """Determine health status for a tool based on recent executions.

        Health logic:
        - OFFLINE: no executions in last hour
        - UNHEALTHY: error rate > 50%
        - DEGRADED: error rate > 20%
        - HEALTHY: otherwise

        Args:
            tool_id: Tool identifier.

        Returns:
            Current health status.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=1)
        recent = [r for r in self._records_for_tool(tool_id) if r.timestamp >= cutoff]

        if not recent:
            return ToolHealthStatus.OFFLINE

        errors = sum(1 for r in recent if not r.success)
        error_rate = errors / len(recent)

        if error_rate > 0.5:
            return ToolHealthStatus.UNHEALTHY
        if error_rate > 0.2:
            return ToolHealthStatus.DEGRADED
        return ToolHealthStatus.HEALTHY

    async def get_slowest_tools(self, limit: int = 10) -> list[dict]:
        """Get tools sorted by average latency descending.

        Args:
            limit: Maximum number of tools to return.

        Returns:
            List of dicts with tool_id and avg_latency_ms.
        """
        tool_ids = {r.tool_id for r in self._history}
        per_tool: list[dict] = []

        for tid in tool_ids:
            records = self._records_for_tool(tid)
            avg = statistics.mean([r.duration_ms for r in records])
            per_tool.append({"tool_id": tid, "avg_latency_ms": round(avg, 2)})

        per_tool.sort(key=lambda t: t["avg_latency_ms"], reverse=True)
        return per_tool[:limit]

    async def get_error_prone_tools(self, limit: int = 10) -> list[dict]:
        """Get tools sorted by error rate descending.

        Args:
            limit: Maximum number of tools to return.

        Returns:
            List of dicts with tool_id, error_rate, and total_calls.
        """
        tool_ids = {r.tool_id for r in self._history}
        per_tool: list[dict] = []

        for tid in tool_ids:
            records = self._records_for_tool(tid)
            total = len(records)
            errors = sum(1 for r in records if not r.success)
            rate = (errors / total * 100) if total else 0.0
            per_tool.append({
                "tool_id": tid,
                "error_rate": round(rate, 2),
                "total_calls": total,
            })

        per_tool.sort(key=lambda t: t["error_rate"], reverse=True)
        return per_tool[:limit]

    async def get_overview(self) -> dict:
        """Get aggregate tool monitoring overview.

        Returns:
            Dictionary with total tools, total calls, avg latency,
            error rate, and health breakdown.
        """
        tool_ids = {r.tool_id for r in self._history}
        total = len(self._history)
        errors = sum(1 for r in self._history if not r.success)
        latencies = [r.duration_ms for r in self._history]

        health_counts = {s: 0 for s in ToolHealthStatus}
        for tid in tool_ids:
            h = await self.get_tool_health(tid)
            health_counts[h] += 1

        return {
            "total_unique_tools": len(tool_ids),
            "total_executions": total,
            "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else 0.0,
            "error_rate": round(errors / total * 100, 2) if total else 0.0,
            "health_breakdown": {s.value: c for s, c in health_counts.items()},
        }
