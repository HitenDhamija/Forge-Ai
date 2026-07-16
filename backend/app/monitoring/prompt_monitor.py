"""Prompt Monitor for tracking prompt template usage, performance, and quality metrics."""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptMetricType(str, Enum):
    """Types of prompt metrics tracked."""

    LATENCY = "latency"
    TOKENS = "tokens"
    CONFIDENCE = "confidence"
    SUCCESS_RATE = "success_rate"


@dataclass
class PromptRecord:
    """Record of a single prompt execution."""

    prompt_id: str
    template_name: str
    version: str
    model_used: str
    prompt_tokens: int
    response_tokens: int
    latency_ms: float
    confidence: float
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PromptStatusSnapshot:
    """Current state summary of prompt performance."""

    total_prompts: int
    avg_latency: float
    avg_tokens: float
    avg_confidence: float
    success_rate: float
    models_used: list[str]
    top_templates: list[dict[str, Any]]


class PromptMonitor:
    """Monitors prompt template usage, performance, and quality metrics.

    Stores records in-memory only. Never stores actual prompt content.
    """

    def __init__(self) -> None:
        """Initialize prompt monitor."""
        self._records: list[PromptRecord] = []
        self._record_index: dict[str, list[int]] = {}

    async def record_prompt(
        self,
        template_name: str,
        version: str,
        model_used: str,
        prompt_tokens: int,
        response_tokens: int,
        latency_ms: float,
        confidence: float,
        success: bool,
    ) -> PromptRecord:
        """Record a prompt execution.

        Args:
            template_name: Name of the prompt template.
            version: Template version identifier.
            model_used: Model that processed the prompt.
            prompt_tokens: Number of tokens in the prompt.
            response_tokens: Number of tokens in the response.
            latency_ms: Latency in milliseconds.
            confidence: Model confidence score (0.0 - 1.0).
            success: Whether the prompt succeeded.

        Returns:
            The created PromptRecord.
        """
        import uuid

        record = PromptRecord(
            prompt_id=str(uuid.uuid4()),
            template_name=template_name,
            version=version,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            response_tokens=response_tokens,
            latency_ms=latency_ms,
            confidence=confidence,
            success=success,
            timestamp=datetime.utcnow(),
        )

        idx = len(self._records)
        self._records.append(record)

        if template_name not in self._record_index:
            self._record_index[template_name] = []
        self._record_index[template_name].append(idx)

        logger.info(
            "Prompt recorded: template=%s, model=%s, latency=%.1fms, success=%s",
            template_name,
            model_used,
            latency_ms,
            success,
        )

        return record

    async def get_prompt_history(
        self,
        template_name: str,
        hours: int = 24,
    ) -> list[PromptRecord]:
        """Get prompt history for a template within a time window.

        Args:
            template_name: Template to filter by.
            hours: Lookback window in hours.

        Returns:
            List of matching PromptRecords.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        indices = self._record_index.get(template_name, [])

        return [
            self._records[i]
            for i in indices
            if i < len(self._records) and self._records[i].timestamp >= cutoff
        ]

    async def get_prompt_performance(self, template_name: str) -> dict[str, Any]:
        """Get performance metrics for a specific template.

        Args:
            template_name: Template to analyze.

        Returns:
            Dictionary with performance metrics.
        """
        indices = self._record_index.get(template_name, [])
        records = [self._records[i] for i in indices if i < len(self._records)]

        if not records:
            return {
                "template_name": template_name,
                "total_calls": 0,
                "avg_latency_ms": 0.0,
                "avg_prompt_tokens": 0.0,
                "avg_response_tokens": 0.0,
                "avg_confidence": 0.0,
                "success_rate": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
            }

        latencies = sorted(r.latency_ms for r in records)
        total = len(records)
        successes = sum(1 for r in records if r.success)

        return {
            "template_name": template_name,
            "total_calls": total,
            "avg_latency_ms": sum(r.latency_ms for r in records) / total,
            "avg_prompt_tokens": sum(r.prompt_tokens for r in records) / total,
            "avg_response_tokens": sum(r.response_tokens for r in records) / total,
            "avg_confidence": sum(r.confidence for r in records) / total,
            "success_rate": successes / total,
            "p50_latency_ms": latencies[int(total * 0.5)],
            "p95_latency_ms": latencies[int(total * 0.95)],
            "p99_latency_ms": latencies[int(total * 0.99)],
        }

    async def get_model_performance(self) -> dict[str, Any]:
        """Get per-model performance metrics.

        Returns:
            Dictionary keyed by model name with performance stats.
        """
        model_records: dict[str, list[PromptRecord]] = {}
        for record in self._records:
            if record.model_used not in model_records:
                model_records[record.model_used] = []
            model_records[record.model_used].append(record)

        result: dict[str, Any] = {}
        for model, records in model_records.items():
            total = len(records)
            successes = sum(1 for r in records if r.success)
            result[model] = {
                "total_calls": total,
                "avg_latency_ms": sum(r.latency_ms for r in records) / total,
                "avg_tokens": sum(r.prompt_tokens + r.response_tokens for r in records) / total,
                "avg_confidence": sum(r.confidence for r in records) / total,
                "success_rate": successes / total,
            }

        return result

    async def get_snapshot(self) -> PromptStatusSnapshot:
        """Get current state summary.

        Returns:
            PromptStatusSnapshot with aggregated metrics.
        """
        if not self._records:
            return PromptStatusSnapshot(
                total_prompts=0,
                avg_latency=0.0,
                avg_tokens=0.0,
                avg_confidence=0.0,
                success_rate=0.0,
                models_used=[],
                top_templates=[],
            )

        total = len(self._records)
        successes = sum(1 for r in self._records if r.success)

        template_counts: dict[str, int] = {}
        for record in self._records:
            template_counts[record.template_name] = (
                template_counts.get(record.template_name, 0) + 1
            )

        top_templates = sorted(
            template_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return PromptStatusSnapshot(
            total_prompts=total,
            avg_latency=sum(r.latency_ms for r in self._records) / total,
            avg_tokens=sum(
                r.prompt_tokens + r.response_tokens for r in self._records
            )
            / total,
            avg_confidence=sum(r.confidence for r in self._records) / total,
            success_rate=successes / total,
            models_used=list({r.model_used for r in self._records}),
            top_templates=[
                {"template": name, "count": count} for name, count in top_templates
            ],
        )

    async def get_overview(self) -> dict[str, Any]:
        """Get prompt monitoring overview.

        Returns:
            Dictionary with overview metrics and recent activity.
        """
        snapshot = await self.get_snapshot()
        model_perf = await self.get_model_performance()

        recent_cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_records = [
            r for r in self._records if r.timestamp >= recent_cutoff
        ]

        return {
            "snapshot": {
                "total_prompts": snapshot.total_prompts,
                "avg_latency": snapshot.avg_latency,
                "avg_tokens": snapshot.avg_tokens,
                "avg_confidence": snapshot.avg_confidence,
                "success_rate": snapshot.success_rate,
                "models_used": snapshot.models_used,
                "top_templates": snapshot.top_templates,
            },
            "model_performance": model_perf,
            "recent_activity": {
                "prompts_last_hour": len(recent_records),
                "avg_latency_last_hour": (
                    sum(r.latency_ms for r in recent_records) / len(recent_records)
                    if recent_records
                    else 0.0
                ),
                "success_rate_last_hour": (
                    sum(1 for r in recent_records if r.success) / len(recent_records)
                    if recent_records
                    else 0.0
                ),
            },
        }

    def _sanitize_prompt(self, text: str) -> str:
        """Remove sensitive data before storage.

        Strips API keys, tokens, passwords, and other secrets.

        Args:
            text: Prompt text to sanitize.

        Returns:
            Sanitized text with secrets redacted.
        """
        patterns = [
            (r"(?i)(api[_-]?key|token|secret|password|credential)\s*[=:]\s*\S+", r"\1=[REDACTED]"),
            (r"(?i)bearer\s+\S+", "Bearer [REDACTED]"),
            (r"(?i)authorization:\s*\S+", "Authorization: [REDACTED]"),
            (r"\b[A-Za-z0-9]{32,}\b", "[REDACTED]"),
            (r"(?i)(aws[_-]?access[_-]?key|aws[_-]?secret)\s*[=:]\s*\S+", r"\1=[REDACTED]"),
            (r"(?i)(sk|pk|rk)_[a-zA-Z0-9]{20,}", "[REDACTED]"),
        ]

        sanitized = text
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized)

        return sanitized
