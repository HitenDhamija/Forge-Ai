"""Central metrics collection module for the ForgeAI monitoring platform.

Collects and aggregates metrics from all system components including agents,
workflows, tools, memory, execution, and learning systems.
"""

import time
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system metrics will be limited")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MetricType(str, Enum):
    """Type of metric being recorded."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricCategory(str, Enum):
    """Category of metric for grouping and filtering."""

    SYSTEM = "system"
    AGENT = "agent"
    WORKFLOW = "workflow"
    TOOL = "tool"
    MEMORY = "memory"
    PROMPT = "prompt"
    EXECUTION = "execution"
    LEARNING = "learning"


# ---------------------------------------------------------------------------
# Internal dataclasses
# ---------------------------------------------------------------------------

@dataclass
class MetricPoint:
    """Single metric data point."""

    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class MetricSeries:
    """Time series of metric data points."""

    name: str
    points: list[MetricPoint] = field(default_factory=list)
    category: MetricCategory = MetricCategory.SYSTEM
    description: str = ""


# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------

class SystemMetrics(BaseModel):
    """System-level resource metrics."""

    cpu_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    memory_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    disk_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    gpu_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    network_io: dict[str, int] = Field(default_factory=dict)
    uptime: float = Field(default=0.0, ge=0.0)


class AgentMetrics(BaseModel):
    """Agent orchestration metrics."""

    total_agents: int = Field(default=0, ge=0)
    idle_agents: int = Field(default=0, ge=0)
    running_agents: int = Field(default=0, ge=0)
    error_agents: int = Field(default=0, ge=0)
    total_tasks: int = Field(default=0, ge=0)
    completed_tasks: int = Field(default=0, ge=0)
    failed_tasks: int = Field(default=0, ge=0)
    avg_latency: float = Field(default=0.0, ge=0.0)


class WorkflowMetrics(BaseModel):
    """Workflow execution metrics."""

    total_workflows: int = Field(default=0, ge=0)
    running: int = Field(default=0, ge=0)
    completed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    avg_duration: float = Field(default=0.0, ge=0.0)
    approval_pending: int = Field(default=0, ge=0)


class ToolMetrics(BaseModel):
    """Tool registry and execution metrics."""

    total_tools: int = Field(default=0, ge=0)
    healthy: int = Field(default=0, ge=0)
    offline: int = Field(default=0, ge=0)
    avg_latency: float = Field(default=0.0, ge=0.0)
    total_calls: int = Field(default=0, ge=0)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class MemoryMetrics(BaseModel):
    """Semantic memory metrics."""

    total_chunks: int = Field(default=0, ge=0)
    total_repositories: int = Field(default=0, ge=0)
    search_count: int = Field(default=0, ge=0)
    avg_search_time: float = Field(default=0.0, ge=0.0)
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class ExecutionMetrics(BaseModel):
    """Execution engine metrics."""

    total_executions: int = Field(default=0, ge=0)
    running: int = Field(default=0, ge=0)
    completed: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    avg_duration: float = Field(default=0.0, ge=0.0)


class LearningMetrics(BaseModel):
    """Learning engine metrics."""

    total_experiences: int = Field(default=0, ge=0)
    total_patterns: int = Field(default=0, ge=0)
    total_lessons: int = Field(default=0, ge=0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class MetricsOverview(BaseModel):
    """High-level overview of all system metrics."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    system: SystemMetrics = Field(default_factory=SystemMetrics)
    agents: AgentMetrics = Field(default_factory=AgentMetrics)
    workflows: WorkflowMetrics = Field(default_factory=WorkflowMetrics)
    tools: ToolMetrics = Field(default_factory=ToolMetrics)
    memory: MemoryMetrics = Field(default_factory=MemoryMetrics)
    execution: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    learning: LearningMetrics = Field(default_factory=LearningMetrics)


# ---------------------------------------------------------------------------
# Metrics Collector
# ---------------------------------------------------------------------------

class MetricsCollector:
    """Central metrics collection and aggregation service.

    Collects metrics from all system components and stores them in-memory
    with configurable retention. Thread-safe for concurrent access.
    """

    def __init__(self, retention_hours: float = 24.0) -> None:
        """Initialize the metrics collector.

        Args:
            retention_hours: How long to keep metric history in memory.
        """
        self._retention = timedelta(hours=retention_hours)
        self._metric_store: dict[str, MetricSeries] = {}
        self._lock = threading.Lock()
        self._start_time = time.monotonic()
        self._counters: dict[str, float] = defaultdict(float)
        logger.info(
            "MetricsCollector initialized: retention=%.1fh psutil=%s",
            retention_hours,
            PSUTIL_AVAILABLE,
        )

    def _get_or_create_series(
        self,
        name: str,
        category: MetricCategory,
        description: str = "",
    ) -> MetricSeries:
        """Get or create a metric series by name."""
        if name not in self._metric_store:
            self._metric_store[name] = MetricSeries(
                name=name,
                category=category,
                description=description,
            )
        return self._metric_store[name]

    def _evict_old_points(self, series: MetricSeries) -> None:
        """Remove data points older than retention period."""
        cutoff = datetime.now(UTC) - self._retention
        series.points = [p for p in series.points if p.timestamp >= cutoff]

    # ------------------------------------------------------------------
    # Recording methods
    # ------------------------------------------------------------------

    def record_metric(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
        metric_type: MetricType = MetricType.GAUGE,
        category: MetricCategory = MetricCategory.SYSTEM,
        description: str = "",
    ) -> None:
        """Record a single metric data point.

        Args:
            name: Metric name (e.g. 'agent.latency_ms').
            value: Metric value.
            labels: Optional key-value labels for dimensional metrics.
            metric_type: Type of metric (counter, gauge, histogram, summary).
            category: Category for grouping.
            description: Human-readable description.
        """
        point = MetricPoint(
            name=name,
            value=value,
            labels=labels or {},
            metric_type=metric_type,
        )

        with self._lock:
            series = self._get_or_create_series(name, category, description)
            series.points.append(point)
            self._evict_old_points(series)

            if metric_type == MetricType.COUNTER:
                self._counters[name] += value

        logger.debug(
            "Metric recorded: name=%s value=%.2f type=%s category=%s",
            name,
            value,
            metric_type.value,
            category.value,
        )

    def increment_counter(
        self,
        name: str,
        amount: float = 1.0,
        labels: dict[str, str] | None = None,
        category: MetricCategory = MetricCategory.SYSTEM,
    ) -> None:
        """Increment a counter metric.

        Args:
            name: Counter name.
            amount: Amount to increment by.
            labels: Optional labels.
            category: Metric category.
        """
        with self._lock:
            self._counters[name] += amount
        self.record_metric(
            name=name,
            value=self._counters[name],
            labels=labels,
            metric_type=MetricType.COUNTER,
            category=category,
        )

    def get_counter(self, name: str) -> float:
        """Get current counter value."""
        return self._counters.get(name, 0.0)

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_metric_series(
        self,
        name: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> MetricSeries:
        """Get metric history for a given name and time range.

        Args:
            name: Metric name.
            start_time: Start of time range (inclusive). None for all history.
            end_time: End of time range (inclusive). None for now.

        Returns:
            MetricSeries with filtered points.
        """
        with self._lock:
            series = self._metric_store.get(name)
            if series is None:
                return MetricSeries(name=name)

            points = series.points
            if start_time:
                points = [p for p in points if p.timestamp >= start_time]
            if end_time:
                points = [p for p in points if p.timestamp <= end_time]

            return MetricSeries(
                name=series.name,
                points=list(points),
                category=series.category,
                description=series.description,
            )

    def list_metric_names(self, category: MetricCategory | None = None) -> list[str]:
        """List all stored metric names, optionally filtered by category."""
        with self._lock:
            if category is None:
                return list(self._metric_store.keys())
            return [
                name
                for name, series in self._metric_store.items()
                if series.category == category
            ]

    # ------------------------------------------------------------------
    # System metrics collection
    # ------------------------------------------------------------------

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect CPU, memory, disk, GPU, and network metrics.

        Returns:
            SystemMetrics with current resource utilization.
        """
        metrics = SystemMetrics()

        if PSUTIL_AVAILABLE:
            try:
                metrics.cpu_percent = psutil.cpu_percent(interval=0.1)
            except Exception:
                logger.debug("Failed to collect CPU metric", exc_info=True)

            try:
                mem = psutil.virtual_memory()
                metrics.memory_percent = mem.percent
            except Exception:
                logger.debug("Failed to collect memory metric", exc_info=True)

            try:
                disk = psutil.disk_usage("/")
                metrics.disk_percent = disk.percent
            except Exception:
                logger.debug("Failed to collect disk metric", exc_info=True)

            try:
                net = psutil.net_io_counters()
                metrics.network_io = {
                    "bytes_sent": net.bytes_sent,
                    "bytes_recv": net.bytes_recv,
                    "packets_sent": net.packets_sent,
                    "packets_recv": net.packets_recv,
                }
            except Exception:
                logger.debug("Failed to collect network metric", exc_info=True)

        metrics.uptime = time.monotonic() - self._start_time

        self.record_metric("system.cpu_percent", metrics.cpu_percent, category=MetricCategory.SYSTEM)
        self.record_metric("system.memory_percent", metrics.memory_percent, category=MetricCategory.SYSTEM)
        self.record_metric("system.disk_percent", metrics.disk_percent, category=MetricCategory.SYSTEM)
        self.record_metric("system.uptime", metrics.uptime, category=MetricCategory.SYSTEM)

        return metrics

    # ------------------------------------------------------------------
    # Component metrics collection
    # ------------------------------------------------------------------

    async def collect_agent_metrics(self, orchestrator: Any) -> AgentMetrics:
        """Collect metrics from the agent orchestrator.

        Args:
            orchestrator: AgentOrchestrator instance with agent state.

        Returns:
            AgentMetrics with current agent status.
        """
        metrics = AgentMetrics()

        try:
            agents = getattr(orchestrator, "_agents", {})
            metrics.total_agents = len(agents)

            for agent in agents.values():
                status = getattr(agent, "status", "unknown")
                if status == "idle":
                    metrics.idle_agents += 1
                elif status == "running":
                    metrics.running_agents += 1
                elif status == "error":
                    metrics.error_agents += 1

            metrics.total_tasks = getattr(orchestrator, "_total_tasks", 0)
            metrics.completed_tasks = getattr(orchestrator, "_completed_tasks", 0)
            metrics.failed_tasks = getattr(orchestrator, "_failed_tasks", 0)
            metrics.avg_latency = getattr(orchestrator, "_avg_latency", 0.0)
        except Exception:
            logger.warning("Failed to collect agent metrics", exc_info=True)

        self.record_metric("agent.total", metrics.total_agents, category=MetricCategory.AGENT)
        self.record_metric("agent.running", metrics.running_agents, category=MetricCategory.AGENT)
        self.record_metric("agent.errors", metrics.error_agents, category=MetricCategory.AGENT)
        self.record_metric("agent.avg_latency", metrics.avg_latency, category=MetricCategory.AGENT)

        return metrics

    async def collect_workflow_metrics(self, workflow_service: Any) -> WorkflowMetrics:
        """Collect metrics from the workflow service.

        Args:
            workflow_service: WorkflowService instance with workflow state.

        Returns:
            WorkflowMetrics with current workflow status.
        """
        metrics = WorkflowMetrics()

        try:
            workflows = getattr(workflow_service, "_workflows", {})
            metrics.total_workflows = len(workflows)

            for wf in workflows.values():
                status = getattr(wf, "status", "unknown")
                if status == "running":
                    metrics.running += 1
                elif status == "completed":
                    metrics.completed += 1
                elif status == "failed":
                    metrics.failed += 1
                elif status == "approval_pending":
                    metrics.approval_pending += 1

            durations = []
            for wf in workflows.values():
                dur = getattr(wf, "duration", None)
                if dur is not None:
                    durations.append(dur)
            if durations:
                metrics.avg_duration = sum(durations) / len(durations)
        except Exception:
            logger.warning("Failed to collect workflow metrics", exc_info=True)

        self.record_metric("workflow.total", metrics.total_workflows, category=MetricCategory.WORKFLOW)
        self.record_metric("workflow.running", metrics.running, category=MetricCategory.WORKFLOW)
        self.record_metric("workflow.failed", metrics.failed, category=MetricCategory.WORKFLOW)
        self.record_metric("workflow.avg_duration", metrics.avg_duration, category=MetricCategory.WORKFLOW)

        return metrics

    async def collect_tool_metrics(self, tool_registry: Any) -> ToolMetrics:
        """Collect metrics from the tool registry.

        Args:
            tool_registry: ToolRegistry instance with tool definitions.

        Returns:
            ToolMetrics with current tool status.
        """
        metrics = ToolMetrics()

        try:
            definitions = tool_registry.list_tools() if hasattr(tool_registry, "list_tools") else []
            metrics.total_tools = len(definitions)

            for defn in definitions:
                health = getattr(defn, "health", None)
                if health:
                    status = getattr(health, "status", None)
                    if status and hasattr(status, "value"):
                        status_val = status.value
                    else:
                        status_val = str(status) if status else "unknown"
                    if status_val == "healthy":
                        metrics.healthy += 1
                    elif status_val == "offline":
                        metrics.offline += 1

            metrics.total_calls = tool_registry.get_counter("tool.calls") if hasattr(tool_registry, "get_counter") else 0
            error_calls = tool_registry.get_counter("tool.errors") if hasattr(tool_registry, "get_counter") else 0
            metrics.error_rate = (error_calls / metrics.total_calls) if metrics.total_calls > 0 else 0.0
        except Exception:
            logger.warning("Failed to collect tool metrics", exc_info=True)

        self.record_metric("tool.total", metrics.total_tools, category=MetricCategory.TOOL)
        self.record_metric("tool.healthy", metrics.healthy, category=MetricCategory.TOOL)
        self.record_metric("tool.offline", metrics.offline, category=MetricCategory.TOOL)
        self.record_metric("tool.error_rate", metrics.error_rate, category=MetricCategory.TOOL)

        return metrics

    async def collect_memory_metrics(self, memory_service: Any) -> MemoryMetrics:
        """Collect metrics from the memory service.

        Args:
            memory_service: MemoryService instance.

        Returns:
            MemoryMetrics with current memory status.
        """
        metrics = MemoryMetrics()

        try:
            if hasattr(memory_service, "get_stats"):
                stats = await memory_service.get_stats()
                metrics.total_chunks = getattr(stats, "total_chunks", 0)
                metrics.total_repositories = getattr(stats, "total_repositories", 0)

            metrics.search_count = int(self.get_counter("memory.searches"))
            avg_time = self.get_counter("memory.avg_search_time")
            count = self.get_counter("memory.search_time_count")
            metrics.avg_search_time = (avg_time / count) if count > 0 else 0.0
            metrics.cache_hit_rate = self.get_counter("memory.cache_hit_rate")
        except Exception:
            logger.warning("Failed to collect memory metrics", exc_info=True)

        self.record_metric("memory.total_chunks", metrics.total_chunks, category=MetricCategory.MEMORY)
        self.record_metric("memory.repositories", metrics.total_repositories, category=MetricCategory.MEMORY)
        self.record_metric("memory.search_count", metrics.search_count, category=MetricCategory.MEMORY)
        self.record_metric("memory.avg_search_time", metrics.avg_search_time, category=MetricCategory.MEMORY)

        return metrics

    async def collect_execution_metrics(self, execution_runtime: Any) -> ExecutionMetrics:
        """Collect metrics from the execution runtime.

        Args:
            execution_runtime: ExecutionRuntime instance.

        Returns:
            ExecutionMetrics with current execution status.
        """
        metrics = ExecutionMetrics()

        try:
            executions = getattr(execution_runtime, "_executions", {})
            metrics.total_executions = len(executions)

            for ex in executions.values():
                status = getattr(ex, "status", "unknown")
                if hasattr(status, "value"):
                    status_val = status.value
                else:
                    status_val = str(status)
                if status_val == "running":
                    metrics.running += 1
                elif status_val == "completed":
                    metrics.completed += 1
                elif status_val == "failed":
                    metrics.failed += 1

            durations = []
            for ex in executions.values():
                dur = getattr(ex, "execution_duration", None)
                if dur is not None:
                    durations.append(dur)
            if durations:
                metrics.avg_duration = sum(durations) / len(durations)
        except Exception:
            logger.warning("Failed to collect execution metrics", exc_info=True)

        self.record_metric("execution.total", metrics.total_executions, category=MetricCategory.EXECUTION)
        self.record_metric("execution.running", metrics.running, category=MetricCategory.EXECUTION)
        self.record_metric("execution.failed", metrics.failed, category=MetricCategory.EXECUTION)
        self.record_metric("execution.avg_duration", metrics.avg_duration, category=MetricCategory.EXECUTION)

        return metrics

    async def collect_learning_metrics(self, learning_service: Any) -> LearningMetrics:
        """Collect metrics from the learning service.

        Args:
            learning_service: LearningService instance.

        Returns:
            LearningMetrics with current learning status.
        """
        metrics = LearningMetrics()

        try:
            if hasattr(learning_service, "get_stats"):
                stats = await learning_service.get_stats()
                metrics.total_experiences = getattr(stats, "total_experiences", 0)
                metrics.total_patterns = getattr(stats, "total_patterns", 0)
                metrics.total_lessons = getattr(stats, "total_lessons", 0)
                metrics.success_rate = getattr(stats, "success_rate", 0.0)
        except Exception:
            logger.warning("Failed to collect learning metrics", exc_info=True)

        self.record_metric("learning.experiences", metrics.total_experiences, category=MetricCategory.LEARNING)
        self.record_metric("learning.patterns", metrics.total_patterns, category=MetricCategory.LEARNING)
        self.record_metric("learning.lessons", metrics.total_lessons, category=MetricCategory.LEARNING)
        self.record_metric("learning.success_rate", metrics.success_rate, category=MetricCategory.LEARNING)

        return metrics

    # ------------------------------------------------------------------
    # Aggregate collection
    # ------------------------------------------------------------------

    async def collect_all(self, app_state: Any) -> dict[str, Any]:
        """Collect metrics from all system components.

        Args:
            app_state: Application state containing all service instances.
                       Expected attributes: orchestrator, workflow_service,
                       tool_registry, memory_service, execution_runtime,
                       learning_service.

        Returns:
            Dictionary with all collected metric categories.
        """
        results: dict[str, Any] = {}

        results["system"] = await self.collect_system_metrics()

        orchestrator = getattr(app_state, "orchestrator", None)
        if orchestrator:
            results["agents"] = await self.collect_agent_metrics(orchestrator)
        else:
            results["agents"] = AgentMetrics()

        workflow_service = getattr(app_state, "workflow_service", None)
        if workflow_service:
            results["workflows"] = await self.collect_workflow_metrics(workflow_service)
        else:
            results["workflows"] = WorkflowMetrics()

        tool_registry = getattr(app_state, "tool_registry", None)
        if tool_registry:
            results["tools"] = await self.collect_tool_metrics(tool_registry)
        else:
            results["tools"] = ToolMetrics()

        memory_service = getattr(app_state, "memory_service", None)
        if memory_service:
            results["memory"] = await self.collect_memory_metrics(memory_service)
        else:
            results["memory"] = MemoryMetrics()

        execution_runtime = getattr(app_state, "execution_runtime", None)
        if execution_runtime:
            results["execution"] = await self.collect_execution_metrics(execution_runtime)
        else:
            results["execution"] = ExecutionMetrics()

        learning_service = getattr(app_state, "learning_service", None)
        if learning_service:
            results["learning"] = await self.collect_learning_metrics(learning_service)
        else:
            results["learning"] = LearningMetrics()

        logger.info(
            "Metrics collected: system cpu=%.1f%% mem=%.1f%% agents=%d workflows=%d tools=%d",
            results["system"].cpu_percent,
            results["system"].memory_percent,
            results["agents"].total_agents,
            results["workflows"].total_workflows,
            results["tools"].total_tools,
        )

        return results

    # ------------------------------------------------------------------
    # Overview
    # ------------------------------------------------------------------

    async def get_overview(self, app_state: Any | None = None) -> MetricsOverview:
        """Get a high-level overview of all system metrics.

        Args:
            app_state: Optional application state. If provided, collects
                       fresh metrics. Otherwise returns last recorded values.

        Returns:
            MetricsOverview with all metric categories.
        """
        if app_state is not None:
            collected = await self.collect_all(app_state)
            return MetricsOverview(
                system=collected.get("system", SystemMetrics()),
                agents=collected.get("agents", AgentMetrics()),
                workflows=collected.get("workflows", WorkflowMetrics()),
                tools=collected.get("tools", ToolMetrics()),
                memory=collected.get("memory", MemoryMetrics()),
                execution=collected.get("execution", ExecutionMetrics()),
                learning=collected.get("learning", LearningMetrics()),
            )

        return MetricsOverview()

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def cleanup(self) -> int:
        """Remove all expired metric data points.

        Returns:
            Number of data points removed.
        """
        removed = 0
        cutoff = datetime.now(UTC) - self._retention

        with self._lock:
            for series in self._metric_store.values():
                before = len(series.points)
                series.points = [p for p in series.points if p.timestamp >= cutoff]
                removed += before - len(series.points)

        if removed > 0:
            logger.info("Metric cleanup: removed %d expired data points", removed)
        return removed

    def get_store_size(self) -> int:
        """Get total number of metric data points in memory."""
        with self._lock:
            return sum(len(s.points) for s in self._metric_store.values())
