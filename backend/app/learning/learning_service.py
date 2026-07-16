"""Learning Service - Main orchestrator for the Learning Engine.

Coordinates experience collection, pattern extraction, knowledge compression,
failure analysis, and recommendation generation.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.logging import get_logger
from app.learning.experience_collector import ExperienceCollector
from app.learning.pattern_extractor import PatternExtractor
from app.learning.knowledge_compressor import KnowledgeCompressor
from app.learning.failure_analyzer import FailureAnalyzer
from app.learning.recommendation_engine import RecommendationEngine
from app.learning.experience_memory import ExperienceMemory

logger = get_logger(__name__)


class LearningStatus(str, Enum):
    """Status of a learning processing task."""

    PENDING = "pending"
    COLLECTING = "collecting"
    EXTRACTING = "extracting"
    COMPRESSING = "compressing"
    ANALYZING = "analyzing"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class LearningTask:
    """Represents a learning processing task."""

    def __init__(
        self,
        task_id: str,
        workflow_id: str | None = None,
        repository_id: str | None = None,
    ):
        self.task_id = task_id
        self.workflow_id = workflow_id
        self.repository_id = repository_id
        self.status = LearningStatus.PENDING
        self.experiences: list[dict] = []
        self.patterns: list[dict] = []
        self.lessons: list[dict] = []
        self.recommendations: list[dict] = []
        self.errors: list[str] = []
        self.started_at = datetime.now(timezone.utc)
        self.completed_at: datetime | None = None


class LearningService:
    """Main orchestrator for the Learning Engine.

    Processes completed workflows to extract engineering knowledge:
    1. Collect experiences from workflow data
    2. Extract reusable patterns
    3. Analyze failures and lessons
    4. Compress similar knowledge
    5. Generate recommendations for future tasks
    """

    def __init__(self, memory: ExperienceMemory | None = None, session_factory=None):
        """Initialize the learning service with all sub-modules."""
        self.collector = ExperienceCollector()
        self.pattern_extractor = PatternExtractor()
        self.compressor = KnowledgeCompressor()
        self.failure_analyzer = FailureAnalyzer()
        self.recommendation_engine = RecommendationEngine()
        self.memory = memory
        self._session_factory = session_factory
        self._tasks: dict[str, LearningTask] = {}

    async def process_workflow(
        self,
        workflow_data: dict[str, Any],
        execution_data: dict[str, Any] | None = None,
        reflection_data: dict[str, Any] | None = None,
        qa_data: dict[str, Any] | None = None,
        review_data: dict[str, Any] | None = None,
    ) -> LearningTask:
        """Process a completed workflow to extract learning.

        Args:
            workflow_data: Workflow execution data.
            execution_data: Optional execution step data.
            reflection_data: Optional reflection results.
            qa_data: Optional QA test results.
            review_data: Optional code review data.

        Returns:
            LearningTask with extracted knowledge.
        """
        task_id = str(uuid.uuid4())
        task = LearningTask(
            task_id=task_id,
            workflow_id=workflow_data.get("workflow_id"),
            repository_id=workflow_data.get("repository_id"),
        )
        self._tasks[task_id] = task

        logger.info(
            "Starting learning processing: task=%s, workflow=%s",
            task_id,
            task.workflow_id,
        )

        try:
            # Phase 1: Collect Experiences
            task.status = LearningStatus.COLLECTING
            logger.info("Phase 1: Collecting experiences")

            experience = await self.collector.collect_from_workflow(workflow_data)
            task.experiences.append(self._to_dict(experience))

            if execution_data:
                exec_exp = await self.collector.collect_from_execution(execution_data)
                task.experiences.append(self._to_dict(exec_exp))

            if reflection_data:
                ref_exp = await self.collector.collect_from_reflection(reflection_data)
                task.experiences.append(self._to_dict(ref_exp))

            if qa_data:
                qa_exp = await self.collector.collect_from_qa(qa_data)
                task.experiences.append(self._to_dict(qa_exp))

            # Phase 2: Extract Patterns
            task.status = LearningStatus.EXTRACTING
            logger.info("Phase 2: Extracting patterns")

            for exp in task.experiences:
                patterns = await self.pattern_extractor.extract_patterns(exp)
                task.patterns.extend([self._to_dict(p) for p in patterns])

            # Phase 3: Analyze Failures
            task.status = LearningStatus.ANALYZING
            logger.info("Phase 3: Analyzing failures")

            for exp in task.experiences:
                if exp.get("outcome") == "failure":
                    lesson = await self.failure_analyzer.analyze_failure(
                        workflow_data, exp
                    )
                    task.lessons.append(self._to_dict(lesson))

            if review_data and review_data.get("status") == "rejected":
                lesson = await self.failure_analyzer.analyze_rejection(review_data)
                task.lessons.append(self._to_dict(lesson))

            # Phase 4: Compress Knowledge
            task.status = LearningStatus.COMPRESSING
            logger.info("Phase 4: Compressing knowledge")

            if len(task.patterns) > 1:
                task.patterns = await self.compressor.deduplicate_patterns(
                    task.patterns
                )

            # Phase 5: Generate Recommendations (with cross-workflow learning)
            task.status = LearningStatus.STORING
            logger.info("Phase 5: Generating recommendations (cross-workflow)")

            # Query ALL past experiences, patterns, lessons from DB
            all_experiences = list(task.experiences)
            all_patterns = list(task.patterns)
            all_lessons = list(task.lessons)

            if self._session_factory:
                try:
                    from app.learning.experience_memory import ExperienceMemory
                    async with self._session_factory() as session:
                        memory = ExperienceMemory(session)
                        db_experiences = await memory.get_all_experiences(limit=100)
                        all_experiences.extend(db_experiences)
                        db_patterns = await memory.get_all_patterns(limit=100)
                        all_patterns.extend(db_patterns)
                        db_lessons = await memory.get_all_lessons(limit=100)
                        all_lessons.extend(db_lessons)
                except Exception as e:
                    logger.warning("Failed to load cross-workflow data: %s", str(e))

            task.recommendations = await self.recommendation_engine.generate_recommendations(
                task_context=workflow_data,
                past_experiences=all_experiences,
                patterns=all_patterns,
                lessons=all_lessons,
            )

            task.status = LearningStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)

            # Persist to database if session factory is available
            if self._session_factory:
                await self._persist_task(task)

            logger.info(
                "Learning completed: task=%s, experiences=%d, patterns=%d, lessons=%d",
                task_id,
                len(task.experiences),
                len(task.patterns),
                len(task.lessons),
            )

        except Exception as e:
            logger.error("Learning failed: task=%s, error=%s", task_id, str(e))
            task.status = LearningStatus.FAILED
            task.errors.append(str(e))
            task.completed_at = datetime.now(timezone.utc)

        return task

    async def _persist_task(self, task: LearningTask) -> None:
        """Persist a completed learning task to the database."""
        if not self._session_factory:
            return
        try:
            from app.learning.experience_memory import ExperienceMemory
            async with self._session_factory() as session:
                memory = ExperienceMemory(session)
                # Store experiences
                for exp_data in task.experiences:
                    await memory.store_experience(exp_data)

                # Store patterns
                for pattern_data in task.patterns:
                    await memory.store_pattern(pattern_data)

                # Store lessons
                for lesson_data in task.lessons:
                    await memory.store_lesson(lesson_data)

                # Store recommendations
                for rec_data in task.recommendations:
                    await memory.store_recommendation(rec_data)

                await session.commit()
                logger.info("Persisted task %s to database", task.task_id)
        except Exception as e:
            logger.error("Failed to persist task %s: %s", task.task_id, str(e))

    async def get_recommendations(
        self, task_context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Get recommendations for a new task based on past learning.

        Args:
            task_context: Context of the new task.

        Returns:
            List of recommendations.
        """
        all_experiences = []
        all_patterns = []
        all_lessons = []

        # Collect from in-memory tasks
        for task in self._tasks.values():
            if task.status == LearningStatus.COMPLETED:
                all_experiences.extend(task.experiences)
                all_patterns.extend(task.patterns)
                all_lessons.extend(task.lessons)

        # Collect from database if available
        if self._session_factory:
            try:
                from app.learning.experience_memory import ExperienceMemory
                async with self._session_factory() as session:
                    memory = ExperienceMemory(session)
                    db_experiences = await memory.get_all_experiences(limit=100)
                    all_experiences.extend(db_experiences)
                    db_patterns = await memory.get_all_patterns(limit=100)
                    all_patterns.extend(db_patterns)
                    db_lessons = await memory.get_all_lessons(limit=100)
                    all_lessons.extend(db_lessons)
            except Exception as e:
                logger.warning("Failed to load from database: %s", str(e))

        recommendations = await self.recommendation_engine.generate_recommendations(
            task_context=task_context,
            past_experiences=all_experiences,
            patterns=all_patterns,
            lessons=all_lessons,
        )

        return recommendations

    async def get_stats(self) -> dict[str, Any]:
        """Get learning statistics."""
        total_experiences = 0
        total_patterns = 0
        total_lessons = 0
        total_recommendations = 0
        successful = 0
        failed = 0

        # Count from in-memory tasks
        for task in self._tasks.values():
            if task.status == LearningStatus.COMPLETED:
                total_experiences += len(task.experiences)
                total_patterns += len(task.patterns)
                total_lessons += len(task.lessons)
                total_recommendations += len(task.recommendations)

                for exp in task.experiences:
                    if exp.get("outcome") == "success":
                        successful += 1
                    elif exp.get("outcome") == "failure":
                        failed += 1

        # Count from database if available
        if self._session_factory:
            try:
                from app.learning.experience_memory import ExperienceMemory
                async with self._session_factory() as session:
                    memory = ExperienceMemory(session)
                    db_stats = await memory.get_stats()
                    total_experiences += db_stats.get("total_experiences", 0)
                    total_patterns += db_stats.get("total_patterns", 0)
                    total_lessons += db_stats.get("total_lessons", 0)
                    total_recommendations += db_stats.get("total_recommendations", 0)
                    successful += db_stats.get("successful_experiences", 0)
                    failed += db_stats.get("failed_experiences", 0)
            except Exception as e:
                logger.warning("Failed to load stats from database: %s", str(e))

        total = successful + failed
        success_rate = successful / total if total > 0 else 0.0

        return {
            "total_tasks": len(self._tasks),
            "total_experiences": total_experiences,
            "total_patterns": total_patterns,
            "total_lessons": total_lessons,
            "total_recommendations": total_recommendations,
            "successful_experiences": successful,
            "failed_experiences": failed,
            "success_rate": round(success_rate, 2),
        }

    async def get_growth_analytics(self) -> dict[str, Any]:
        """Get growth analytics over time."""
        timeline = []

        # Collect from in-memory tasks
        for task in sorted(
            self._tasks.values(), key=lambda t: t.started_at
        ):
            if task.status == LearningStatus.COMPLETED:
                timeline.append(
                    {
                        "date": task.started_at.isoformat(),
                        "experiences": len(task.experiences),
                        "patterns": len(task.patterns),
                        "lessons": len(task.lessons),
                    }
                )

        # Collect from database if available
        if self._session_factory:
            try:
                from app.learning.experience_memory import ExperienceMemory
                async with self._session_factory() as session:
                    memory = ExperienceMemory(session)
                    db_growth = await memory.get_growth_analytics()
                    # Map experience_over_time to timeline format
                    for entry in db_growth.get("experience_over_time", []):
                        timeline.append({
                            "date": entry["date"],
                            "experiences": entry["count"],
                            "patterns": 0,
                            "lessons": 0,
                        })
            except Exception as e:
                logger.warning("Failed to load growth from database: %s", str(e))

        return {
            "timeline": timeline,
            "total_tasks": len(self._tasks),
        }

    def get_task(self, task_id: str) -> LearningTask | None:
        """Get a learning task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> list[LearningTask]:
        """List all learning tasks."""
        return list(self._tasks.values())

    async def list_tasks_from_db(self) -> list[dict[str, Any]]:
        """List learning tasks from the database (using experiences as proxy)."""
        tasks = []
        if self._session_factory:
            try:
                from app.learning.experience_memory import ExperienceMemory
                async with self._session_factory() as session:
                    memory = ExperienceMemory(session)
                    experiences = await memory.search_experiences({"limit": 50})
                    for exp in experiences:
                        tasks.append({
                            "task_id": exp.get("id", ""),
                            "workflow_id": exp.get("workflow_id", ""),
                            "repository_id": exp.get("repository_id", ""),
                            "status": "completed",
                            "experiences_count": 1,
                            "patterns_count": 0,
                            "lessons_count": 0,
                            "started_at": exp.get("created_at", ""),
                            "completed_at": exp.get("created_at", ""),
                        })
            except Exception as e:
                logger.warning("Failed to load tasks from database: %s", str(e))
        return tasks

    def _to_dict(self, obj: Any) -> Any:
        """Convert a dataclass or Pydantic model to a dictionary."""
        if hasattr(obj, "model_dump"):  # Pydantic v2
            return obj.model_dump()
        elif hasattr(obj, "__dataclass_fields__"):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                result[field_name] = self._to_dict(value)
            return result
        elif isinstance(obj, list):
            return [self._to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._to_dict(v) for k, v in obj.items()}
        elif hasattr(obj, "value"):  # Enum
            return obj.value
        else:
            return obj
