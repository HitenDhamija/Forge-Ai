"""Implementation Planner for Software Engineer Agent.

Plans implementation steps based on task and context.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskType(str, Enum):
    """Types of implementation tasks."""

    FEATURE = "feature"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    API_CREATION = "api_creation"
    DATABASE_MIGRATION = "database_migration"
    FRONTEND_COMPONENT = "frontend_component"
    BACKEND_SERVICE = "backend_service"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    GUIDANCE = "guidance"


class StepType(str, Enum):
    """Types of implementation steps."""

    READ_FILE = "read_file"
    ANALYZE = "analyze"
    CREATE_FILE = "create_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    CREATE_DIRECTORY = "create_directory"
    UPDATE_IMPORTS = "update_imports"
    ADD_TESTS = "add_tests"
    VALIDATE = "validate"
    REVIEW = "review"


@dataclass
class ImplementationStep:
    """Single step in implementation plan."""

    step_id: str
    step_type: StepType
    description: str
    file_path: str | None = None
    content: str | None = None
    dependencies: list[str] = field(default_factory=list)
    estimated_complexity: str = "low"
    requires_approval: bool = False


@dataclass
class ImplementationPlan:
    """Complete implementation plan."""

    task_type: TaskType
    task_description: str
    steps: list[ImplementationStep]
    affected_files: list[str]
    estimated_complexity: str
    risk_level: str
    prerequisites: list[str]
    rollback_steps: list[ImplementationStep]


class ImplementationPlanner:
    """Plans implementation steps for tasks."""

    def __init__(self):
        """Initialize implementation planner."""
        self._task_templates: dict[TaskType, list[dict[str, Any]]] = {
            TaskType.FEATURE: [
                {"step_type": StepType.READ_FILE, "description": "Read existing codebase"},
                {"step_type": StepType.ANALYZE, "description": "Analyze architecture"},
                {"step_type": StepType.CREATE_FILE, "description": "Create new module"},
                {"step_type": StepType.MODIFY_FILE, "description": "Integrate with existing code"},
                {"step_type": StepType.UPDATE_IMPORTS, "description": "Update imports"},
                {"step_type": StepType.VALIDATE, "description": "Validate implementation"},
                {"step_type": StepType.REVIEW, "description": "Self-review"},
            ],
            TaskType.BUG_FIX: [
                {"step_type": StepType.READ_FILE, "description": "Read affected file"},
                {"step_type": StepType.ANALYZE, "description": "Analyze bug cause"},
                {"step_type": StepType.MODIFY_FILE, "description": "Apply fix"},
                {"step_type": StepType.VALIDATE, "description": "Validate fix"},
                {"step_type": StepType.REVIEW, "description": "Self-review"},
            ],
            TaskType.REFACTOR: [
                {"step_type": StepType.READ_FILE, "description": "Read current implementation"},
                {"step_type": StepType.ANALYZE, "description": "Analyze refactoring scope"},
                {"step_type": StepType.MODIFY_FILE, "description": "Refactor code"},
                {"step_type": StepType.UPDATE_IMPORTS, "description": "Update imports"},
                {"step_type": StepType.VALIDATE, "description": "Validate refactoring"},
                {"step_type": StepType.REVIEW, "description": "Self-review"},
            ],
            TaskType.API_CREATION: [
                {"step_type": StepType.READ_FILE, "description": "Read existing API patterns"},
                {"step_type": StepType.ANALYZE, "description": "Analyze API structure"},
                {"step_type": StepType.CREATE_FILE, "description": "Create endpoint"},
                {"step_type": StepType.CREATE_FILE, "description": "Create schemas"},
                {"step_type": StepType.CREATE_FILE, "description": "Create service"},
                {"step_type": StepType.MODIFY_FILE, "description": "Register router"},
                {"step_type": StepType.VALIDATE, "description": "Validate API"},
                {"step_type": StepType.REVIEW, "description": "Self-review"},
            ],
        }

    async def plan(
        self,
        task_type: TaskType,
        task_description: str,
        context: dict[str, Any],
        target_files: list[str],
    ) -> ImplementationPlan:
        """Create implementation plan.

        Args:
            task_type: Type of task.
            task_description: Description of task.
            context: Repository context.
            target_files: Files to modify.

        Returns:
            Implementation plan.
        """
        logger.info("Creating implementation plan for: %s", task_type.value)

        # Get template steps
        template_steps = self._task_templates.get(task_type, [])

        # Create steps
        steps = []
        for i, template in enumerate(template_steps):
            step = ImplementationStep(
                step_id=f"step-{i + 1}",
                step_type=template["step_type"],
                description=template["description"],
                file_path=target_files[0] if target_files and i > 1 else None,
                dependencies=[f"step-{i}"] if i > 0 else [],
                estimated_complexity=self._estimate_step_complexity(template, context),
                requires_approval=template["step_type"] in [
                    StepType.CREATE_FILE,
                    StepType.MODIFY_FILE,
                    StepType.DELETE_FILE,
                ],
            )
            steps.append(step)

        # Calculate complexity
        complexity = self._calculate_complexity(steps, context)

        # Assess risk
        risk = self._assess_risk(task_type, target_files, context)

        # Create rollback steps
        rollback_steps = self._create_rollback_steps(steps)

        plan = ImplementationPlan(
            task_type=task_type,
            task_description=task_description,
            steps=steps,
            affected_files=target_files,
            estimated_complexity=complexity,
            risk_level=risk,
            prerequisites=self._identify_prerequisites(context),
            rollback_steps=rollback_steps,
        )

        logger.info(
            "Plan created: steps=%d, complexity=%s, risk=%s",
            len(steps),
            complexity,
            risk,
        )

        return plan

    def _estimate_step_complexity(
        self,
        template: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        """Estimate step complexity."""
        step_type = template["step_type"]

        if step_type in [StepType.READ_FILE, StepType.ANALYZE]:
            return "low"
        elif step_type in [StepType.CREATE_FILE, StepType.MODIFY_FILE]:
            return "medium"
        elif step_type in [StepType.DELETE_FILE, StepType.UPDATE_IMPORTS]:
            return "high"
        return "low"

    def _calculate_complexity(
        self,
        steps: list[ImplementationStep],
        context: dict[str, Any],
    ) -> str:
        """Calculate overall complexity."""
        high_count = sum(1 for s in steps if s.estimated_complexity == "high")
        medium_count = sum(1 for s in steps if s.estimated_complexity == "medium")

        if high_count > 2:
            return "high"
        if medium_count > 3:
            return "medium"
        return "low"

    def _assess_risk(
        self,
        task_type: TaskType,
        target_files: list[str],
        context: dict[str, Any],
    ) -> str:
        """Assess risk level."""
        if task_type == TaskType.DATABASE_MIGRATION:
            return "high"
        if len(target_files) > 5:
            return "medium"
        if task_type == TaskType.BUG_FIX:
            return "low"
        return "low"

    def _identify_prerequisites(self, context: dict[str, Any]) -> list[str]:
        """Identify prerequisites."""
        return ["Repository access", "Context loaded"]

    def _create_rollback_steps(
        self,
        steps: list[ImplementationStep],
    ) -> list[ImplementationStep]:
        """Create rollback steps for modification steps."""
        rollback_steps = []
        for step in steps:
            if step.step_type in [StepType.CREATE_FILE, StepType.MODIFY_FILE]:
                rollback_steps.append(
                    ImplementationStep(
                        step_id=f"rollback-{step.step_id}",
                        step_type=StepType.DELETE_FILE if step.step_type == StepType.CREATE_FILE else StepType.MODIFY_FILE,
                        description=f"Rollback: {step.description}",
                        file_path=step.file_path,
                    )
                )
        return rollback_steps
