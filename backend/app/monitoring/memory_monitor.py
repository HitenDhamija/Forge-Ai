"""Memory system monitoring for operations, retrieval performance, and cache efficiency."""

import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class MemoryOperationType(str, Enum):
    """Types of memory operations."""

    INDEX = "index"
    SEARCH = "search"
    CONTEXT = "context"
    DELETE = "delete"


@dataclass
class MemoryOperationRecord:
    """Record of a single memory operation."""

    operation_type: MemoryOperationType
    repository_id: str
    query: str
    duration_ms: float
    results_count: int
    chunks_retrieved: int
    timestamp: datetime
    success: bool


@dataclass
class MemoryStatusSnapshot:
    """Current memory system status snapshot."""

    total_chunks: int
    total_repositories: int
    collections: list[dict]
    embedding_model: str
    avg_search_time: float
    total_searches: int
    cache_hit_rate: float
    storage_size_mb: float


class MemoryMonitor:
    """Monitors memory system operations, retrieval performance, and cache efficiency.

    Stores operation history in-memory with timestamps for real-time analytics.
    """

    def __init__(self) -> None:
        self._history: list[MemoryOperationRecord] = []
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    def _records_for_type(
        self, operation_type: MemoryOperationType | None = None
    ) -> list[MemoryOperationRecord]:
        if operation_type is None:
            return list(self._history)
        return [r for r in self._history if r.operation_type == operation_type]

    @staticmethod
    def _percentile(values: list[float], pct: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * pct / 100)
        idx = min(idx, len(sorted_vals) - 1)
        return sorted_vals[idx]

    async def snapshot(self, memory_service) -> MemoryStatusSnapshot:
        """Get current memory system state.

        Args:
            memory_service: MemoryService instance with get_stats().

        Returns:
            MemoryStatusSnapshot with current metrics.
        """
        stats = await memory_service.get_stats()

        search_records = self._records_for_type(MemoryOperationType.SEARCH)
        search_latencies = [r.duration_ms for r in search_records]
        avg_search = statistics.mean(search_latencies) if search_latencies else 0.0

        total_cache = self._cache_hits + self._cache_misses
        cache_rate = (self._cache_hits / total_cache * 100) if total_cache else 0.0

        return MemoryStatusSnapshot(
            total_chunks=stats.total_chunks,
            total_repositories=stats.total_repositories,
            collections=[
                {"name": c.name, "count": c.count} for c in stats.collections
            ],
            embedding_model=stats.embedding_model,
            avg_search_time=round(avg_search, 2),
            total_searches=len(search_records),
            cache_hit_rate=round(cache_rate, 2),
            storage_size_mb=round(
                (stats.storage_size_bytes or 0) / (1024 * 1024), 2
            ),
        )

    async def record_operation(
        self,
        operation_type: MemoryOperationType,
        repository_id: str,
        query: str,
        duration_ms: float,
        results_count: int,
        chunks_retrieved: int,
        success: bool,
    ) -> None:
        """Record a memory operation event.

        Args:
            operation_type: Type of operation performed.
            repository_id: Repository the operation targets.
            query: Query string (empty for non-search operations).
            duration_ms: Operation duration in milliseconds.
            results_count: Number of results returned.
            chunks_retrieved: Number of chunks retrieved.
            success: Whether the operation succeeded.
        """
        record = MemoryOperationRecord(
            operation_type=operation_type,
            repository_id=repository_id,
            query=query,
            duration_ms=duration_ms,
            results_count=results_count,
            chunks_retrieved=chunks_retrieved,
            timestamp=datetime.now(timezone.utc),
            success=success,
        )
        self._history.append(record)

        logger.info(
            "Memory operation recorded: type=%s repo=%s dur=%.1fms results=%d success=%s",
            operation_type.value,
            repository_id,
            duration_ms,
            results_count,
            success,
        )

    async def get_operation_history(
        self,
        operation_type: MemoryOperationType | None = None,
        hours: int = 24,
    ) -> list[MemoryOperationRecord]:
        """Get operation history within a time window.

        Args:
            operation_type: Optional filter by operation type.
            hours: Lookback window in hours.

        Returns:
            List of MemoryOperationRecord sorted by timestamp descending.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        records = [
            r
            for r in self._records_for_type(operation_type)
            if r.timestamp >= cutoff
        ]
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records

    async def get_retrieval_performance(self) -> dict:
        """Get retrieval performance metrics.

        Returns:
            Dictionary with avg time, percentiles, and throughput.
        """
        search_records = self._records_for_type(MemoryOperationType.SEARCH)
        latencies = [r.duration_ms for r in search_records]

        now = datetime.now(timezone.utc)
        recent = [
            r for r in search_records if r.timestamp >= now - timedelta(hours=1)
        ]

        if not latencies:
            return {
                "total_searches": 0,
                "avg_time_ms": 0.0,
                "p50_time_ms": 0.0,
                "p95_time_ms": 0.0,
                "p99_time_ms": 0.0,
                "min_time_ms": 0.0,
                "max_time_ms": 0.0,
                "throughput_per_hour": 0,
                "avg_results": 0.0,
            }

        return {
            "total_searches": len(search_records),
            "avg_time_ms": round(statistics.mean(latencies), 2),
            "p50_time_ms": round(self._percentile(latencies, 50), 2),
            "p95_time_ms": round(self._percentile(latencies, 95), 2),
            "p99_time_ms": round(self._percentile(latencies, 99), 2),
            "min_time_ms": round(min(latencies), 2),
            "max_time_ms": round(max(latencies), 2),
            "throughput_per_hour": len(recent),
            "avg_results": round(
                statistics.mean([r.results_count for r in search_records]), 2
            ),
        }

    async def get_cache_stats(self) -> dict:
        """Get cache hit/miss statistics.

        Returns:
            Dictionary with cache hit rate and counts.
        """
        total = self._cache_hits + self._cache_misses
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "total_requests": total,
            "hit_rate": round(
                (self._cache_hits / total * 100) if total else 0.0, 2
            ),
        }

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self._cache_hits += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self._cache_misses += 1

    async def get_overview(self) -> dict:
        """Get aggregate memory monitoring overview.

        Returns:
            Dictionary with operation counts, avg latencies by type,
            and error rates.
        """
        op_counts: dict[str, int] = {}
        op_latencies: dict[str, list[float]] = {}
        op_errors: dict[str, int] = {}

        for record in self._history:
            key = record.operation_type.value
            op_counts[key] = op_counts.get(key, 0) + 1
            op_latencies.setdefault(key, []).append(record.duration_ms)
            if not record.success:
                op_errors[key] = op_errors.get(key, 0) + 1

        total = len(self._history)
        errors = sum(1 for r in self._history if not r.success)

        by_type: dict[str, dict] = {}
        for key in op_counts:
            by_type[key] = {
                "count": op_counts[key],
                "avg_latency_ms": round(
                    statistics.mean(op_latencies[key]), 2
                ),
                "error_count": op_errors.get(key, 0),
                "error_rate": round(
                    (op_errors.get(key, 0) / op_counts[key] * 100)
                    if op_counts[key]
                    else 0.0,
                    2,
                ),
            }

        return {
            "total_operations": total,
            "error_rate": round(errors / total * 100, 2) if total else 0.0,
            "by_operation_type": by_type,
        }
