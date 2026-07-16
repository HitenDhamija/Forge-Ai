"""Task decomposition for the Planning Engine."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from app.core.logging import get_logger
from app.planner.config import get_planner_settings
from app.planner.exceptions import TaskDecompositionException
from app.planner.schemas.planner import (
    ComplexityLevel,
    IntentClassification,
    IntentType,
    Task,
    TaskPriority,
    TaskType,
)

logger = get_logger(__name__)

INTENT_TASK_TEMPLATES: dict[IntentType, list[dict[str, Any]]] = {
    IntentType.FEATURE_DEVELOPMENT: [
        {"title": "Analyze requirements", "type": TaskType.RESEARCH, "priority": TaskPriority.HIGH},
        {"title": "Design implementation approach", "type": TaskType.RESEARCH, "priority": TaskPriority.HIGH},
        {"title": "Implement core functionality", "type": TaskType.IMPLEMENTATION, "priority": TaskPriority.HIGH},
        {"title": "Write unit tests", "type": TaskType.TESTING, "priority": TaskPriority.MEDIUM},
        {"title": "Write integration tests", "type": TaskType.TESTING, "priority": TaskPriority.MEDIUM},
        {"title": "Update documentation", "type": TaskType.DOCUMENTATION, "priority": TaskPriority.LOW},
        {"title": "Code review", "type": TaskType.REVIEW, "priority": TaskPriority.MEDIUM},
    ],
    IntentType.BUG_FIX: [
        {"title": "Reproduce the bug", "type": TaskType.RESEARCH, "priority": TaskPriority.CRITICAL},
        {"title": "Identify root cause", "type": TaskType.RESEARCH, "priority": TaskPriority.CRITICAL},
        {"title": "Implement fix", "type": TaskType.IMPLEMENTATION, "priority": TaskPriority.HIGH},
        {"title": "Write regression test", "type": TaskType.TESTING, "priority": TaskPriority.HIGH},
        {"title": "Verify fix in all environments", "type": TaskType.TESTING, "priority": TaskPriority.MEDIUM},
    ],
    IntentType.REFACTORING: [
        {"title": "Analyze current code structure", "type": TaskType.RESEARCH, "priority": TaskPriority.HIGH},
        {"title": "Create refactoring plan", "type": TaskType.RESEARCH, "priority": TaskPriority.HIGH},
        {"title": "Apply refactoring changes", "type": TaskType.REFACTORING, "priority": TaskPriority.HIGH},
        {"title": "Ensure all tests pass", "type": TaskType.TESTING, "priority": TaskPriority.HIGH},
        {"title": "Update affected documentation", "type": TaskType.DOCUMENTATION, "priority": TaskPriority.LOW},
    ],
    IntentType.DOCUMENTATION: [
        {"title": "Identify documentation gaps", "type": TaskType.RESEARCH, "priority": TaskPriority.MEDIUM},
        {"title": "Draft documentation content", "type": TaskType.DOCUMENTATION, "priority": TaskPriority.HIGH},
        {"title": "Review and refine", "type": TaskType.REVIEW, "priority": TaskPriority.MEDIUM},
        {"title": "Publish documentation", "type": TaskType.DOCUMENTATION, "priority": TaskPriority.LOW},
    ],
    IntentType.TESTING: [
        {"title": "Identify test coverage gaps", "type": TaskType.RESEARCH, "priority": TaskPriority.HIGH},
        {"title": "Write test cases", "type": TaskType.TESTING, "priority": TaskPriority.HIGH},
        {"title": "Add test fixtures and mocks", "type": TaskType.TESTING, "priority": TaskPriority.MEDIUM},
        {"title": "Run full test suite", "type": TaskType.TESTING, "priority": TaskPriority.MEDIUM},
        {"title": "Review test results", "type": TaskType.REVIEW, "priority": TaskPriority.LOW},
    ],
    IntentType.DEPLOYMENT: [
        {"title": "Verify build passes", "type": TaskType.TESTING, "priority": TaskPriority.CRITICAL},
        {"title": "Prepare deployment artifacts", "type": TaskType.CONFIGURATION, "priority": TaskPriority.HIGH},
        {"title": "Deploy to staging", "type": TaskType.DEPLOYMENT, "priority": TaskPriority.HIGH},
        {"title": "Run smoke tests", "type": TaskType.TESTING, "priority": TaskPriority.HIGH},
        {"title": "Deploy to production", "type": TaskType.DEPLOYMENT, "priority": TaskPriority.CRITICAL},
        {"title": "Monitor deployment", "type": TaskType.REVIEW, "priority": TaskPriority.MEDIUM},
    ],
    IntentType.CONFIGURATION: [
        {"title": "Identify configuration needs", "type": TaskType.RESEARCH, "priority": TaskPriority.MEDIUM},
        {"title": "Update configuration files", "type": TaskType.CONFIGURATION, "priority": TaskPriority.HIGH},
        {"title": "Test configuration changes", "type": TaskType.TESTING, "priority": TaskPriority.MEDIUM},
        {"title": "Document configuration", "type": TaskType.DOCUMENTATION, "priority": TaskPriority.LOW},
    ],
    IntentType.RESEARCH: [
        {"title": "Define research questions", "type": TaskType.RESEARCH, "priority": TaskPriority.HIGH},
        {"title": "Gather information", "type": TaskType.RESEARCH, "priority": TaskPriority.MEDIUM},
        {"title": "Analyze findings", "type": TaskType.RESEARCH, "priority": TaskPriority.MEDIUM},
        {"title": "Summarize results", "type": TaskType.DOCUMENTATION, "priority": TaskPriority.LOW},
    ],
}

DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    {"title": "Analyze the request", "type": TaskType.RESEARCH, "priority": TaskPriority.HIGH},
    {"title": "Plan implementation", "type": TaskType.RESEARCH, "priority": TaskPriority.MEDIUM},
    {"title": "Implement changes", "type": TaskType.IMPLEMENTATION, "priority": TaskPriority.HIGH},
    {"title": "Test changes", "type": TaskType.TESTING, "priority": TaskPriority.MEDIUM},
    {"title": "Review and document", "type": TaskType.REVIEW, "priority": TaskPriority.LOW},
]


class TaskDecomposer:
    """Decomposes user requests into actionable tasks based on classified intent.

    Uses intent classification results and task templates to generate
    a structured list of tasks with dependencies and priorities.
    """

    def __init__(self) -> None:
        self._settings = get_planner_settings()

    def decompose(
        self,
        user_input: str,
        classification: IntentClassification,
        context: dict[str, Any] | None = None,
    ) -> list[Task]:
        """Decompose a user request into tasks.

        Args:
            user_input: The original user request.
            classification: Result of intent classification.
            context: Optional additional context.

        Returns:
            List of Task objects with dependencies set up.

        Raises:
            TaskDecompositionException: If decomposition fails.
        """
        if not user_input or not user_input.strip():
            raise TaskDecompositionException("User input cannot be empty")

        if classification is None:
            raise TaskDecompositionException("Classification is required")

        try:
            templates = self._get_templates(classification)
            tasks = self._generate_tasks(templates, user_input, context or {})
            tasks = self._assign_dependencies(tasks, classification)
            tasks = self._estimate_complexities(tasks, user_input)

            if len(tasks) > self._settings.MAX_TASKS_PER_PLAN:
                tasks = tasks[: self._settings.MAX_TASKS_PER_PLAN]
                logger.warning(
                    "Task count exceeded maximum, truncated to %d",
                    self._settings.MAX_TASKS_PER_PLAN,
                )

            logger.info(
                "Decomposed request into %d tasks (intent=%s)",
                len(tasks),
                classification.intent.value,
            )
            return tasks

        except TaskDecompositionException:
            raise
        except Exception as e:
            raise TaskDecompositionException(f"Task decomposition failed: {e}") from e

    def _get_templates(self, classification: IntentClassification) -> list[dict[str, Any]]:
        """Get task templates based on intent classification."""
        templates = INTENT_TASK_TEMPLATES.get(classification.intent, DEFAULT_TEMPLATES)

        if classification.confidence < 0.3:
            templates = DEFAULT_TEMPLATES

        return templates

    def _generate_tasks(
        self,
        templates: list[dict[str, Any]],
        user_input: str,
        context: dict[str, Any],
    ) -> list[Task]:
        """Generate Task objects from templates."""
        tasks: list[Task] = []
        keywords = self._extract_keywords(user_input)

        for i, template in enumerate(templates):
            task_id = self._generate_task_id(template["title"], i)
            description = self._build_task_description(template["title"], keywords, context)

            task = Task(
                id=task_id,
                title=template["title"],
                description=description,
                task_type=template["type"],
                priority=template["priority"],
                tags=keywords[:5],
                metadata={
                    "template_index": i,
                    "source": "decomposition",
                },
            )
            tasks.append(task)

        return tasks

    def _assign_dependencies(
        self, tasks: list[Task], classification: IntentClassification
    ) -> list[Task]:
        """Assign dependency relationships between tasks."""
        if len(tasks) <= 1:
            return tasks

        for i in range(1, len(tasks)):
            if tasks[i].task_type == TaskType.IMPLEMENTATION:
                research_tasks = [
                    t.id for t in tasks[:i] if t.task_type == TaskType.RESEARCH
                ]
                tasks[i].dependencies = research_tasks

            elif tasks[i].task_type == TaskType.TESTING:
                impl_tasks = [
                    t.id for t in tasks[:i] if t.task_type == TaskType.IMPLEMENTATION
                ]
                if impl_tasks:
                    tasks[i].dependencies = impl_tasks

            elif tasks[i].task_type == TaskType.REVIEW:
                tasks[i].dependencies = [tasks[i - 1].id]

            elif tasks[i].task_type == TaskType.DOCUMENTATION:
                impl_tasks = [
                    t.id
                    for t in tasks[:i]
                    if t.task_type in (TaskType.IMPLEMENTATION, TaskType.REFACTORING)
                ]
                if impl_tasks:
                    tasks[i].dependencies = [impl_tasks[-1]]

            elif tasks[i].task_type == TaskType.DEPLOYMENT:
                test_tasks = [
                    t.id for t in tasks[:i] if t.task_type == TaskType.TESTING
                ]
                if test_tasks:
                    tasks[i].dependencies = test_tasks

        return tasks

    def _estimate_complexities(
        self, tasks: list[Task], user_input: str
    ) -> list[Task]:
        """Estimate complexity and hours for each task."""
        input_length = len(user_input)
        word_count = len(user_input.split())

        for task in tasks:
            if task.task_type == TaskType.IMPLEMENTATION:
                task.complexity = ComplexityLevel.COMPLEX
                task.estimated_hours = max(2.0, min(word_count * 0.1, 16.0))
            elif task.task_type == TaskType.RESEARCH:
                task.complexity = ComplexityLevel.MEDIUM
                task.estimated_hours = max(1.0, min(word_count * 0.05, 8.0))
            elif task.task_type == TaskType.TESTING:
                task.complexity = ComplexityLevel.MEDIUM
                task.estimated_hours = max(1.0, min(word_count * 0.08, 8.0))
            elif task.task_type == TaskType.DOCUMENTATION:
                task.complexity = ComplexityLevel.SIMPLE
                task.estimated_hours = max(0.5, min(word_count * 0.03, 4.0))
            elif task.task_type == TaskType.REVIEW:
                task.complexity = ComplexityLevel.SIMPLE
                task.estimated_hours = max(0.5, min(word_count * 0.02, 2.0))
            elif task.task_type == TaskType.DEPLOYMENT:
                task.complexity = ComplexityLevel.MEDIUM
                task.estimated_hours = max(1.0, 4.0)
            else:
                task.complexity = ComplexityLevel.SIMPLE
                task.estimated_hours = 1.0

        return tasks

    def _generate_task_id(self, title: str, index: int) -> str:
        """Generate a unique task ID."""
        hash_input = f"{title}-{index}"
        hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"task-{index:03d}-{hash_val}"

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract meaningful keywords from user input."""
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        stop_words = {
            "the", "and", "for", "are", "but", "not", "you", "all",
            "can", "had", "her", "was", "one", "our", "out", "has",
            "have", "from", "this", "that", "with", "they", "been",
            "said", "each", "which", "their", "will", "other",
            "about", "many", "then", "them", "would", "make", "like",
            "into", "time", "very", "when", "come", "could", "more",
        }
        return list(dict.fromkeys(w for w in words if w not in stop_words))

    def _build_task_description(
        self, title: str, keywords: list[str], context: dict[str, Any]
    ) -> str:
        """Build a detailed description for a task."""
        keyword_str = ", ".join(keywords[:3]) if keywords else "the requested changes"
        description = f"{title} related to {keyword_str}."

        if context:
            context_parts = []
            for key, value in context.items():
                if isinstance(value, str):
                    context_parts.append(f"{key}: {value}")
            if context_parts:
                description += f" Context: {'; '.join(context_parts)}."

        return description

    def get_supported_intents(self) -> list[IntentType]:
        """Return list of intents with custom templates."""
        return list(INTENT_TASK_TEMPLATES.keys())
