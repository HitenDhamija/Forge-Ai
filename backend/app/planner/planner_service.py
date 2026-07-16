"""Main planner service orchestrating the Planning Engine."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.planner.complexity_analyzer import ComplexityAnalyzer
from app.planner.config import get_planner_settings
from app.planner.dependency_analyzer import DependencyAnalyzer
from app.planner.exceptions import (
    PlanNotFoundException,
    PlanningException,
)
from app.planner.intent_classifier import IntentClassifier
from app.planner.plan_generator import PlanGenerator
from app.planner.risk_analyzer import RiskAnalyzer
from app.planner.schemas.planner import (
    IntentClassification,
    Plan,
    PlanCreateRequest,
    PlanHistoryEntry,
    PlanListResponse,
    PlanStatus,
    PlanUpdateRequest,
)
from app.planner.task_decomposer import TaskDecomposer as TaskDecomposerImpl

logger = get_logger(__name__)


class PlannerService:
    """Main service orchestrating the Planning Engine.

    Coordinates intent classification, task decomposition, complexity
    analysis, dependency analysis, risk analysis, and plan generation.
    """

    def __init__(self) -> None:
        self._settings = get_planner_settings()
        self._intent_classifier = IntentClassifier()
        self._task_decomposer = TaskDecomposerImpl()
        self._complexity_analyzer = ComplexityAnalyzer()
        self._dependency_analyzer = DependencyAnalyzer()
        self._risk_analyzer = RiskAnalyzer()
        self._plan_generator = PlanGenerator()
        self._plans: dict[str, Plan] = {}
        self._history: list[PlanHistoryEntry] = []

    async def create_plan(self, request: PlanCreateRequest) -> Plan:
        """Create a new plan from a user request.

        Executes the full planning pipeline:
        1. Classify intent
        2. Decompose into tasks
        3. Analyze complexity
        4. Analyze dependencies
        5. Analyze risks
        6. Generate plan

        Args:
            request: Plan creation request.

        Returns:
            Generated Plan object.

        Raises:
            PlanningException: If plan creation fails.
        """
        try:
            classification = self._classify_intent(request.description)
            tasks = self._decompose_tasks(
                request.description, classification, request.context
            )
            complexity = self._analyze_complexity(tasks)
            dependencies = self._analyze_dependencies(tasks)
            risks = self._analyze_risks(tasks, request.description)

            plan = self._plan_generator.generate(
                title=request.title,
                description=request.description,
                tasks=tasks,
                classification=classification,
                complexity=complexity,
                dependencies=dependencies,
                risks=risks,
                context=request.context,
            )

            self._plans[plan.id] = plan
            self._add_history(plan.id, "created", {"title": plan.title})

            logger.info("Created plan '%s' (id=%s)", plan.title, plan.id)
            return plan

        except Exception as e:
            raise PlanningException(f"Failed to create plan: {e}") from e

    async def get_plan(self, plan_id: str) -> Plan:
        """Retrieve a plan by ID.

        Args:
            plan_id: The plan identifier.

        Returns:
            The Plan object.

        Raises:
            PlanNotFoundException: If plan is not found.
        """
        plan = self._plans.get(plan_id)
        if plan is None:
            raise PlanNotFoundException(f"Plan '{plan_id}' not found")
        return plan

    async def list_plans(
        self, page: int = 1, per_page: int = 20
    ) -> PlanListResponse:
        """List all plans with pagination.

        Args:
            page: Page number (1-indexed).
            per_page: Items per page.

        Returns:
            Paginated list of plans.
        """
        all_plans = list(self._plans.values())
        start = (page - 1) * per_page
        end = start + per_page
        paginated = all_plans[start:end]

        return PlanListResponse(
            plans=paginated,
            total=len(all_plans),
            page=page,
            per_page=per_page,
        )

    async def update_plan(self, plan_id: str, request: PlanUpdateRequest) -> Plan:
        """Update an existing plan.

        Args:
            plan_id: The plan identifier.
            request: Update request.

        Returns:
            Updated Plan object.

        Raises:
            PlanNotFoundException: If plan is not found.
        """
        plan = await self.get_plan(plan_id)

        if request.title is not None:
            plan.title = request.title
        if request.description is not None:
            plan.description = request.description
        if request.status is not None:
            plan = self._plan_generator.update_plan_status(plan, request.status)
        if request.metadata is not None:
            plan.metadata.update(request.metadata)

        self._add_history(plan_id, "updated", {"fields": request.model_dump(exclude_none=True)})
        return plan

    async def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan.

        Args:
            plan_id: The plan identifier.

        Returns:
            True if deleted.

        Raises:
            PlanNotFoundException: If plan is not found.
        """
        if plan_id not in self._plans:
            raise PlanNotFoundException(f"Plan '{plan_id}' not found")

        del self._plans[plan_id]
        self._add_history(plan_id, "deleted", {})
        return True

    async def get_plan_history(self, plan_id: str | None = None) -> list[PlanHistoryEntry]:
        """Get plan history.

        Args:
            plan_id: Optional plan ID to filter by.

        Returns:
            List of history entries.
        """
        if plan_id:
            return [h for h in self._history if h.plan_id == plan_id]
        return self._history[-self._settings.MAX_PLAN_HISTORY:]

    async def get_plan_summary(self, plan_id: str) -> dict[str, Any]:
        """Get summary statistics for a plan.

        Args:
            plan_id: The plan identifier.

        Returns:
            Plan summary dictionary.
        """
        plan = await self.get_plan(plan_id)
        return self._plan_generator.get_plan_summary(plan)

    def _classify_intent(self, text: str) -> IntentClassification:
        """Classify user intent."""
        return self._intent_classifier.classify(text)

    def _decompose_tasks(
        self,
        user_input: str,
        classification: IntentClassification,
        context: dict[str, Any],
    ) -> list:
        """Decompose request into tasks."""
        return self._task_decomposer.decompose(user_input, classification, context)

    def _analyze_complexity(self, tasks: list):
        """Analyze task complexity."""
        return self._complexity_analyzer.analyze(tasks)

    def _analyze_dependencies(self, tasks: list):
        """Analyze task dependencies."""
        return self._dependency_analyzer.analyze(tasks)

    def _analyze_risks(self, tasks: list, context: str):
        """Analyze risks."""
        return self._risk_analyzer.analyze(tasks, context)

    def _add_history(
        self, plan_id: str, action: str, details: dict[str, Any]
    ) -> None:
        """Add an entry to plan history."""
        from datetime import UTC, datetime

        entry = PlanHistoryEntry(
            plan_id=plan_id,
            action=action,
            timestamp=datetime.now(UTC),
            details=details,
        )
        self._history.append(entry)

        if len(self._history) > self._settings.MAX_PLAN_HISTORY:
            self._history = self._history[-self._settings.MAX_PLAN_HISTORY:]
