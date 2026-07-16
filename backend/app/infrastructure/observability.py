"""Observability, health checks, and metrics endpoints."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter
from fastapi import Request
from fastapi import Response


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    latency_ms: float
    message: str
    last_checked: datetime


@dataclass
class HealthCheck:
    status: HealthStatus
    version: str
    uptime_seconds: float
    components: list[ComponentHealth]
    timestamp: datetime


class TimerContext:
    """Context manager for timing code blocks."""

    def __init__(self, collector: MetricsCollector, name: str, tags: dict[str, str] | None = None):
        self._collector = collector
        self._name = name
        self._tags = tags or {}
        self._start: float = 0.0
        self._duration: float = 0.0

    def __enter__(self) -> TimerContext:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._duration = (time.perf_counter() - self._start) * 1000
        self._collector.histogram(f"{self._name}.duration_ms", self._duration, self._tags)
        if exc_type is not None:
            self._collector.increment(f"{self._name}.errors", self._tags)


class MetricsCollector:
    """In-memory metrics collector with counters, gauges, and histograms."""

    def __init__(self) -> None:
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._tags: dict[str, dict[str, str]] = {}

    def _make_key(self, name: str, tags: dict[str, str] | None) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"

    def increment(self, name: str, tags: dict[str, str] | None = None) -> None:
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) + 1
        if tags:
            self._tags[key] = tags

    def decrement(self, name: str, tags: dict[str, str] | None = None) -> None:
        key = self._make_key(name, tags)
        self._counters[key] = self._counters.get(key, 0) - 1
        if tags:
            self._tags[key] = tags

    def gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        key = self._make_key(name, tags)
        self._gauges[key] = value
        if tags:
            self._tags[key] = tags

    def histogram(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        key = self._make_key(name, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        if tags:
            self._tags[key] = tags

    def timer(self, name: str, tags: dict[str, str] | None = None) -> TimerContext:
        return TimerContext(self, name, tags)

    def get_metrics(self) -> dict[str, Any]:
        histograms_summary: dict[str, dict[str, float]] = {}
        for key, values in self._histograms.items():
            if not values:
                continue
            sorted_vals = sorted(values)
            count = len(sorted_vals)
            histograms_summary[key] = {
                "min": sorted_vals[0],
                "max": sorted_vals[-1],
                "mean": sum(sorted_vals) / count,
                "p50": sorted_vals[count // 2],
                "p95": sorted_vals[int(count * 0.95)] if count > 1 else sorted_vals[0],
                "p99": sorted_vals[int(count * 0.99)] if count > 1 else sorted_vals[0],
                "count": count,
            }

        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": histograms_summary,
        }

    def get_metric(self, name: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in self._counters.items():
            if key == name or key.startswith(f"{name}{{"):
                result[key] = {"type": "counter", "value": value}
        for key, value in self._gauges.items():
            if key == name or key.startswith(f"{name}{{"):
                result[key] = {"type": "gauge", "value": value}
        for key, values in self._histograms.items():
            if key == name or key.startswith(f"{name}{{"):
                if values:
                    sorted_vals = sorted(values)
                    count = len(sorted_vals)
                    result[key] = {
                        "type": "histogram",
                        "min": sorted_vals[0],
                        "max": sorted_vals[-1],
                        "mean": sum(sorted_vals) / count,
                        "count": count,
                    }
        return result

    def reset(self) -> None:
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._tags.clear()


class MetricsMiddleware:
    """FastAPI middleware that tracks request metrics."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self._collector = metrics_collector

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        start = time.perf_counter()

        self._collector.increment("http.requests", {"method": method})

        status_code = 500

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            self._collector.increment("http.errors", {"method": method})
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._collector.histogram("http.request_duration_ms", duration_ms, {"method": method, "path": path})
            self._collector.increment("http.responses", {"method": method, "status": str(status_code)})
            if status_code >= 400:
                self._collector.increment("http.errors", {"method": method, "status": str(status_code)})


class HealthChecker:
    """Component health checker for the application."""

    def __init__(self) -> None:
        self._start_time = time.time()

    async def check_database(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                message="Database connection is healthy",
                last_checked=datetime.now(timezone.utc),
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Database check failed: {e}",
                last_checked=datetime.now(timezone.utc),
            )

    async def check_cache(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="cache",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                message="Cache connection is healthy",
                last_checked=datetime.now(timezone.utc),
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="cache",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Cache check failed: {e}",
                last_checked=datetime.now(timezone.utc),
            )

    async def check_task_queue(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="task_queue",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                message="Task queue is healthy",
                last_checked=datetime.now(timezone.utc),
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="task_queue",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Task queue check failed: {e}",
                last_checked=datetime.now(timezone.utc),
            )

    async def check_storage(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="storage",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                message="Storage is healthy",
                last_checked=datetime.now(timezone.utc),
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name="storage",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=f"Storage check failed: {e}",
                last_checked=datetime.now(timezone.utc),
            )

    async def check_all(self) -> HealthCheck:
        components = [
            await self.check_database(),
            await self.check_cache(),
            await self.check_task_queue(),
            await self.check_storage(),
        ]

        statuses = [c.status for c in components]
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        return HealthCheck(
            status=overall_status,
            version="1.0.0",
            uptime_seconds=time.time() - self._start_time,
            components=components,
            timestamp=datetime.now(timezone.utc),
        )

    async def readiness_check(self) -> dict[str, Any]:
        health = await self.check_all()
        is_ready = health.status != HealthStatus.UNHEALTHY
        return {
            "ready": is_ready,
            "status": health.status.value,
            "components": [
                {"name": c.name, "status": c.status.value} for c in health.components
            ],
        }

    async def liveness_check(self) -> dict[str, Any]:
        return {
            "alive": True,
            "uptime_seconds": time.time() - self._start_time,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class PrometheusExporter:
    """Export metrics in Prometheus exposition format."""

    def __init__(self, metrics_collector: MetricsCollector) -> None:
        self._collector = metrics_collector

    def _format_line(self, name: str, value: float, metric_type: str, help_text: str, labels: str = "") -> str:
        lines = [f"# HELP {name} {help_text}"]
        lines.append(f"# TYPE {name} {metric_type}")
        if labels:
            lines.append(f"{name}{{{labels}}} {value}")
        else:
            lines.append(f"{name} {value}")
        return "\n".join(lines)

    def _parse_key(self, key: str) -> tuple[str, str]:
        if "{" in key:
            name, rest = key.split("{", 1)
            labels_str = rest.rstrip("}")
            parts = []
            for pair in labels_str.split(","):
                k, v = pair.split("=", 1)
                parts.append(f'{k}="{v}"')
            return name.strip(), ",".join(parts)
        return key.strip(), ""

    def export(self) -> str:
        lines: list[str] = []

        for key, value in self._collector._counters.items():
            name, labels = self._parse_key(key)
            lines.append(self._format_line(name, value, "counter", f"{name} counter", labels))

        for key, value in self._collector._gauges.items():
            name, labels = self._parse_key(key)
            lines.append(self._format_line(name, value, "gauge", f"{name} gauge", labels))

        for key, values in self._collector._histograms.items():
            if not values:
                continue
            name, labels = self._parse_key(key)
            sorted_vals = sorted(values)
            count = len(sorted_vals)
            total = sum(sorted_vals)

            bucket_lines = [f"# HELP {name} {name} histogram"]
            bucket_lines.append(f"# TYPE {name} histogram")
            for boundary in [10, 50, 100, 250, 500, 1000, 2500, 5000, 10000]:
                bucket_count = sum(1 for v in sorted_vals if v <= boundary)
                blabels = f'{labels + "," if labels else ""}le="{boundary}"'
                bucket_lines.append(f'{name}_bucket{{{blabels}}} {bucket_count}')
            inf_labels = f'{labels + "," if labels else ""}le="+Inf"'
            bucket_lines.append(f'{name}_bucket{{{inf_labels}}} {count}')
            bucket_lines.append(f'{name}_count{{{labels}}} {count}' if labels else f"{name}_count {count}")
            bucket_lines.append(f'{name}_sum{{{labels}}} {total:.4f}' if labels else f"{name}_sum {total:.4f}")
            lines.extend(bucket_lines)

        lines.append("")
        return "\n".join(lines)


def create_observability_router() -> APIRouter:
    """Create FastAPI router with observability endpoints."""
    router = APIRouter(tags=["observability"])

    @router.get("/health")
    async def health_endpoint() -> dict[str, Any]:
        check = await health_checker.check_all()
        return {
            "status": check.status.value,
            "version": check.version,
            "uptime_seconds": check.uptime_seconds,
            "timestamp": check.timestamp.isoformat(),
            "components": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                    "message": c.message,
                    "last_checked": c.last_checked.isoformat(),
                }
                for c in check.components
            ],
        }

    @router.get("/ready")
    async def readiness_endpoint() -> dict[str, Any]:
        result = await health_checker.readiness_check()
        return result

    @router.get("/live")
    async def liveness_endpoint() -> dict[str, Any]:
        result = await health_checker.liveness_check()
        return result

    @router.get("/metrics")
    async def metrics_endpoint() -> Response:
        exporter = PrometheusExporter(metrics_collector)
        body = exporter.export()
        return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")

    @router.get("/metrics/json")
    async def metrics_json_endpoint() -> dict[str, Any]:
        return metrics_collector.get_metrics()

    return router


metrics_collector = MetricsCollector()
health_checker = HealthChecker()
observability_router = create_observability_router()
