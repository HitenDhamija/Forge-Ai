"""Plan generation for the Planning Engine."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger
from app.planner.config import get_planner_settings
from app.planner.exceptions import PlanGenerationException
from app.planner.schemas.planner import (
    ComplexityAnalysis,
    DependencyInfo,
    IntentClassification,
    Plan,
    PlanStatus,
    RiskItem,
    Task,
)

logger = get_logger(__name__)


class PlanGenerator:
    """Generates complete execution plans from tasks, dependencies, and risks.

    Orchestrates the assembly of a Plan object from its constituent parts.
    """

    def __init__(self) -> None:
        self._settings = get_planner_settings()

    def generate(
        self,
        title: str,
        description: str,
        tasks: list[Task],
        classification: IntentClassification,
        complexity: ComplexityAnalysis,
        dependencies: list[DependencyInfo],
        risks: list[RiskItem],
        context: dict[str, Any] | None = None,
    ) -> Plan:
        """Generate a complete plan.

        Args:
            title: Plan title.
            description: Plan description.
            tasks: Decomposed tasks.
            classification: Intent classification result.
            complexity: Complexity analysis result.
            dependencies: Dependency relationships.
            risks: Identified risks.
            context: Optional additional context.

        Returns:
            Complete Plan object.

        Raises:
            PlanGenerationException: If plan generation fails.
        """
        if not tasks:
            raise PlanGenerationException("Cannot generate plan with no tasks")

        try:
            plan_id = self._generate_plan_id(title)
            now = datetime.now(UTC)

            total_hours = self._calculate_total_hours(tasks, risks)
            metadata = self._build_metadata(classification, context or {})

            plan = Plan(
                id=plan_id,
                title=title,
                description=description,
                status=PlanStatus.DRAFT,
                tasks=tasks,
                dependencies=dependencies,
                risks=risks,
                complexity=complexity,
                intent=classification,
                metadata=metadata,
                created_at=now,
                updated_at=now,
                estimated_total_hours=total_hours,
            )

            logger.info(
                "Generated plan '%s' with %d tasks, %.1f estimated hours",
                title,
                len(tasks),
                total_hours,
            )
            return plan

        except PlanGenerationException:
            raise
        except Exception as e:
            raise PlanGenerationException(f"Plan generation failed: {e}") from e

    def _generate_plan_id(self, title: str) -> str:
        """Generate a unique plan ID."""
        timestamp = datetime.now(UTC).isoformat()
        hash_input = f"{title}-{timestamp}"
        hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        return f"plan-{hash_val}"

    def _calculate_total_hours(
        self, tasks: list[Task], risks: list[RiskItem]
    ) -> float:
        """Calculate total estimated hours including risk buffer."""
        base_hours = sum(t.estimated_hours for t in tasks)
        risk_buffer = self._calculate_risk_buffer(risks)
        total = base_hours * (1 + risk_buffer)
        return round(total, 1)

    def _calculate_risk_buffer(self, risks: list[RiskItem]) -> float:
        """Calculate time buffer based on identified risks."""
        if not risks:
            return 0.0

        high_risk_count = sum(
            1 for r in risks
            if r.risk_level.value in ("high", "critical")
        )

        if high_risk_count >= 3:
            return 0.3
        elif high_risk_count >= 1:
            return 0.15
        elif risks:
            return 0.05
        return 0.0

    def _build_metadata(
        self, classification: IntentClassification, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Build plan metadata."""
        metadata: dict[str, Any] = {
            "generator_version": "1.0.0",
            "intent": classification.intent.value,
            "confidence": classification.confidence,
        }
        if context:
            metadata["context"] = context
        return metadata

    def update_plan_status(self, plan: Plan, new_status: PlanStatus) -> Plan:
        """Update plan status with validation.

        Args:
            plan: The plan to update.
            new_status: The new status.

        Returns:
            Updated Plan object.

        Raises:
            PlanGenerationException: If status transition is invalid.
        """
        valid_transitions = {
            PlanStatus.DRAFT: [PlanStatus.ACTIVE, PlanStatus.CANCELLED],
            PlanStatus.ACTIVE: [PlanStatus.COMPLETED, PlanStatus.FAILED, PlanStatus.CANCELLED],
            PlanStatus.COMPLETED: [],
            PlanStatus.FAILED: [PlanStatus.ACTIVE],
            PlanStatus.CANCELLED: [PlanStatus.DRAFT],
        }

        allowed = valid_transitions.get(plan.status, [])
        if new_status not in allowed:
            raise PlanGenerationException(
                f"Invalid status transition from {plan.status.value} to {new_status.value}"
            )

        plan.status = new_status
        plan.updated_at = datetime.now(UTC)
        return plan

    def get_plan_summary(self, plan: Plan) -> dict[str, Any]:
        """Generate a summary of the plan.

        Args:
            plan: The plan to summarize.

        Returns:
            Dictionary with plan summary statistics.
        """
        task_stats: dict[str, int] = {}
        for task in plan.tasks:
            status = task.status.value
            task_stats[status] = task_stats.get(status, 0) + 1

        risk_stats: dict[str, int] = {}
        for risk in plan.risks:
            level = risk.risk_level.value
            risk_stats[level] = risk_stats.get(level, 0) + 1

        return {
            "plan_id": plan.id,
            "title": plan.title,
            "status": plan.status.value,
            "task_count": len(plan.tasks),
            "task_stats": task_stats,
            "risk_count": len(plan.risks),
            "risk_stats": risk_stats,
            "estimated_hours": plan.estimated_total_hours,
            "complexity": plan.complexity.level.value if plan.complexity else "unknown",
            "intent": plan.intent.intent.value if plan.intent else "unknown",
        }
