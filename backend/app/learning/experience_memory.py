"""Long-term experience memory storage and retrieval.

Provides an interface to store, search, and retrieve experiences, patterns,
lessons, recommendations, and feedback. Manages the knowledge graph that
links related knowledge items together.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.learning.models import (
    ExperienceModel,
    FeedbackModel,
    KnowledgeGraphModel,
    LessonModel,
    PatternModel,
    RecommendationModel,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExperienceType:
    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    TESTING = "testing"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"


class OutcomeType:
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class PatternType:
    ARCHITECTURE = "architecture"
    CODING = "coding"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"


class LessonType:
    FAILURE = "failure"
    REJECTION = "rejection"
    REGRESSION = "regression"
    VIOLATION = "violation"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"


class FeedbackType:
    HELPFUL = "helpful"
    INCORRECT = "incorrect"
    NEEDS_IMPROVEMENT = "needs_improvement"
    EXCELLENT = "excellent"


class Severity:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Priority:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class KnowledgeRelation:
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"
    SUPERSEDES = "supersedes"
    CONFLICTS_WITH = "conflicts_with"
    IMPROVES = "improves"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _now_utc() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# ExperienceMemory
# ---------------------------------------------------------------------------


class ExperienceMemory:
    """Manages long-term experience memory storage and retrieval.

    Provides a unified interface for persisting engineering experiences,
    extracted patterns, lessons learned, recommendations, and feedback.
    Supports efficient searching by type, technology, tags, and outcome,
    and maintains a knowledge graph linking related items.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Store operations
    # ------------------------------------------------------------------

    async def store_experience(self, experience_data: dict[str, Any]) -> str:
        """Store a new experience record.

        Args:
            experience_data: Dictionary with experience fields including
                ``experience_type``, ``title``, ``description``, ``outcome``,
                ``solution``, ``context``, ``files_changed``, ``technologies``,
                ``tags``, and scoring fields.

        Returns:
            The generated experience ID.
        """
        experience_id = str(uuid4())
        model = ExperienceModel(
            id=experience_id,
            workflow_id=experience_data.get("workflow_id"),
            repository_id=experience_data.get("repository_id"),
            experience_type=experience_data["experience_type"],
            title=experience_data["title"],
            description=experience_data["description"],
            context=experience_data.get("context", {}),
            outcome=experience_data.get("outcome", OutcomeType.SUCCESS),
            solution=experience_data.get("solution", ""),
            files_changed=experience_data.get("files_changed", []),
            technologies=experience_data.get("technologies", []),
            tags=experience_data.get("tags", []),
            confidence=experience_data.get("confidence", 0.5),
            reuse_potential=experience_data.get("reuse_potential", 0.5),
            complexity=experience_data.get("complexity", 0.5),
            generalization_score=experience_data.get("generalization_score", 0.5),
            metadata_json=experience_data.get("metadata", {}),
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "Stored experience",
            extra={"experience_id": experience_id, "type": model.experience_type},
        )
        return experience_id

    async def store_pattern(self, pattern_data: dict[str, Any]) -> str:
        """Store a new pattern record.

        Args:
            pattern_data: Dictionary with pattern fields including
                ``pattern_type``, ``name``, ``description``, ``when_to_use``,
                ``when_not_to_use``, ``technologies``, ``tags``, and scoring.

        Returns:
            The generated pattern ID.
        """
        pattern_id = str(uuid4())
        model = PatternModel(
            id=pattern_id,
            experience_id=pattern_data.get("experience_id"),
            pattern_type=pattern_data["pattern_type"],
            name=pattern_data["name"],
            description=pattern_data["description"],
            code_example=pattern_data.get("code_example"),
            when_to_use=pattern_data.get("when_to_use", ""),
            when_not_to_use=pattern_data.get("when_not_to_use", ""),
            technologies=pattern_data.get("technologies", []),
            tags=pattern_data.get("tags", []),
            confidence=pattern_data.get("confidence", 0.5),
            success_rate=pattern_data.get("success_rate", 1.0),
            generalization_score=pattern_data.get("generalization_score", 0.5),
            metadata_json=pattern_data.get("metadata", {}),
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "Stored pattern",
            extra={"pattern_id": pattern_id, "type": model.pattern_type},
        )
        return pattern_id

    async def store_lesson(self, lesson_data: dict[str, Any]) -> str:
        """Store a new lesson record.

        Args:
            lesson_data: Dictionary with lesson fields including
                ``lesson_type``, ``title``, ``description``, ``root_cause``,
                ``avoidance_strategy``, ``severity``, ``technologies``, ``tags``.

        Returns:
            The generated lesson ID.
        """
        lesson_id = str(uuid4())
        model = LessonModel(
            id=lesson_id,
            experience_id=lesson_data.get("experience_id"),
            lesson_type=lesson_data["lesson_type"],
            title=lesson_data["title"],
            description=lesson_data["description"],
            root_cause=lesson_data.get("root_cause", ""),
            avoidance_strategy=lesson_data.get("avoidance_strategy", ""),
            severity=lesson_data.get("severity", Severity.MEDIUM),
            technologies=lesson_data.get("technologies", []),
            tags=lesson_data.get("tags", []),
            confidence=lesson_data.get("confidence", 0.5),
            times_encountered=lesson_data.get("times_encountered", 1),
            metadata_json=lesson_data.get("metadata", {}),
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "Stored lesson",
            extra={"lesson_id": lesson_id, "type": model.lesson_type},
        )
        return lesson_id

    async def store_recommendation(self, recommendation_data: dict[str, Any]) -> str:
        """Store a recommendation.

        Args:
            recommendation_data: Dictionary with recommendation fields.

        Returns:
            The generated recommendation ID.
        """
        rec_id = str(uuid4())
        model = RecommendationModel(
            id=rec_id,
            pattern_id=recommendation_data.get("source_pattern_id") or recommendation_data.get("pattern_id"),
            task_type=recommendation_data.get("task_type") or recommendation_data.get("recommendation_type", "general"),
            context_keywords=recommendation_data.get("context_keywords", []),
            recommendation=recommendation_data.get("recommendation") or recommendation_data.get("title") or recommendation_data.get("description", ""),
            confidence=recommendation_data.get("confidence", 0.5),
            priority=recommendation_data.get("priority", Priority.MEDIUM),
            technologies=recommendation_data.get("technologies", []),
            metadata_json=recommendation_data.get("metadata", {}),
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "Stored recommendation",
            extra={"recommendation_id": rec_id, "task_type": model.task_type},
        )
        return rec_id

    async def store_feedback(self, feedback_data: dict[str, Any]) -> str:
        """Store human feedback on an experience.

        Args:
            feedback_data: Dictionary with feedback fields including
                ``experience_id``, ``feedback_type``, ``rating``, ``comment``,
                ``context``.

        Returns:
            The generated feedback ID.
        """
        feedback_id = str(uuid4())
        model = FeedbackModel(
            id=feedback_id,
            experience_id=feedback_data.get("experience_id"),
            feedback_type=feedback_data["feedback_type"],
            rating=feedback_data.get("rating"),
            comment=feedback_data.get("comment"),
            context=feedback_data.get("context", {}),
            metadata_json=feedback_data.get("metadata", {}),
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "Stored feedback",
            extra={
                "feedback_id": feedback_id,
                "experience_id": model.experience_id,
                "type": model.feedback_type,
            },
        )
        return feedback_id

    # ------------------------------------------------------------------
    # Get by ID operations
    # ------------------------------------------------------------------

    async def get_experience(self, experience_id: str) -> dict[str, Any] | None:
        """Retrieve an experience by its ID.

        Args:
            experience_id: The experience UUID string.

        Returns:
            Experience dict or ``None`` if not found.
        """
        stmt = select(ExperienceModel).where(ExperienceModel.id == experience_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._experience_to_dict(model)

    async def get_pattern(self, pattern_id: str) -> dict[str, Any] | None:
        """Retrieve a pattern by its ID.

        Args:
            pattern_id: The pattern UUID string.

        Returns:
            Pattern dict or ``None`` if not found.
        """
        stmt = select(PatternModel).where(PatternModel.id == pattern_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._pattern_to_dict(model)

    async def get_lesson(self, lesson_id: str) -> dict[str, Any] | None:
        """Retrieve a lesson by its ID.

        Args:
            lesson_id: The lesson UUID string.

        Returns:
            Lesson dict or ``None`` if not found.
        """
        stmt = select(LessonModel).where(LessonModel.id == lesson_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._lesson_to_dict(model)

    # ------------------------------------------------------------------
    # Search operations
    # ------------------------------------------------------------------

    async def search_experiences(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Search experiences by type, technology, tags, outcome, or text.

        Query keys (all optional):
            ``experience_type``: Filter by experience type.
            ``outcome``: Filter by outcome.
            ``technologies``: List of technologies to match (any).
            ``tags``: List of tags to match (any).
            ``repository_id``: Filter by repository.
            ``limit``: Maximum results (default 20).

        Args:
            query: Search parameters dictionary.

        Returns:
            List of matching experience dicts.
        """
        stmt = select(ExperienceModel)

        filters = []
        if query.get("experience_type"):
            filters.append(
                ExperienceModel.experience_type == query["experience_type"]
            )
        if query.get("outcome"):
            filters.append(ExperienceModel.outcome == query["outcome"])
        if query.get("repository_id"):
            filters.append(
                ExperienceModel.repository_id == query["repository_id"]
            )
        if query.get("workflow_id"):
            filters.append(
                ExperienceModel.workflow_id == query["workflow_id"]
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Technology filter: experience must contain any of the listed techs
        techs = query.get("technologies", [])
        if techs:
            tech_filters = [
                ExperienceModel.technologies.op("LIKE")(f"%{t}%") for t in techs
            ]
            stmt = stmt.where(or_(*tech_filters))

        # Tag filter: experience must contain any of the listed tags
        tags = query.get("tags", [])
        if tags:
            tag_filters = [
                ExperienceModel.tags.op("LIKE")(f"%{t}%") for t in tags
            ]
            stmt = stmt.where(or_(*tag_filters))

        # Text search across title, description, solution
        text = query.get("text", "")
        if text:
            text_filter = or_(
                ExperienceModel.title.ilike(f"%{text}%"),
                ExperienceModel.description.ilike(f"%{text}%"),
                ExperienceModel.solution.ilike(f"%{text}%"),
            )
            stmt = stmt.where(text_filter)

        stmt = stmt.order_by(ExperienceModel.created_at.desc())
        limit = query.get("limit", 20)
        stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._experience_to_dict(m) for m in models]

    async def search_patterns(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Search patterns by type, technology, tags, or text.

        Query keys (all optional):
            ``pattern_type``: Filter by pattern type.
            ``technologies``: List of technologies to match (any).
            ``tags``: List of tags to match (any).
            ``min_confidence``: Minimum confidence threshold.
            ``limit``: Maximum results (default 20).

        Args:
            query: Search parameters dictionary.

        Returns:
            List of matching pattern dicts.
        """
        stmt = select(PatternModel)

        filters = []
        if query.get("pattern_type"):
            filters.append(PatternModel.pattern_type == query["pattern_type"])
        if query.get("min_confidence") is not None:
            filters.append(
                PatternModel.confidence >= query["min_confidence"]
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        techs = query.get("technologies", [])
        if techs:
            tech_filters = [
                PatternModel.technologies.op("LIKE")(f"%{t}%") for t in techs
            ]
            stmt = stmt.where(or_(*tech_filters))

        tags = query.get("tags", [])
        if tags:
            tag_filters = [
                PatternModel.tags.op("LIKE")(f"%{t}%") for t in tags
            ]
            stmt = stmt.where(or_(*tag_filters))

        text = query.get("text", "")
        if text:
            text_filter = or_(
                PatternModel.name.ilike(f"%{text}%"),
                PatternModel.description.ilike(f"%{text}%"),
                PatternModel.when_to_use.ilike(f"%{text}%"),
            )
            stmt = stmt.where(text_filter)

        stmt = stmt.order_by(
            PatternModel.confidence.desc(), PatternModel.usage_count.desc()
        )
        limit = query.get("limit", 20)
        stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._pattern_to_dict(m) for m in models]

    async def search_lessons(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Search lessons by type, severity, technology, tags, or text.

        Query keys (all optional):
            ``lesson_type``: Filter by lesson type.
            ``severity``: Filter by severity level.
            ``technologies``: List of technologies to match (any).
            ``tags``: List of tags to match (any).
            ``limit``: Maximum results (default 20).

        Args:
            query: Search parameters dictionary.

        Returns:
            List of matching lesson dicts.
        """
        stmt = select(LessonModel)

        filters = []
        if query.get("lesson_type"):
            filters.append(LessonModel.lesson_type == query["lesson_type"])
        if query.get("severity"):
            filters.append(LessonModel.severity == query["severity"])
        if query.get("experience_id"):
            filters.append(
                LessonModel.experience_id == query["experience_id"]
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        techs = query.get("technologies", [])
        if techs:
            tech_filters = [
                LessonModel.technologies.op("LIKE")(f"%{t}%") for t in techs
            ]
            stmt = stmt.where(or_(*tech_filters))

        tags = query.get("tags", [])
        if tags:
            tag_filters = [
                LessonModel.tags.op("LIKE")(f"%{t}%") for t in tags
            ]
            stmt = stmt.where(or_(*tag_filters))

        text = query.get("text", "")
        if text:
            text_filter = or_(
                LessonModel.title.ilike(f"%{text}%"),
                LessonModel.description.ilike(f"%{text}%"),
                LessonModel.root_cause.ilike(f"%{text}%"),
                LessonModel.avoidance_strategy.ilike(f"%{text}%"),
            )
            stmt = stmt.where(text_filter)

        stmt = stmt.order_by(LessonModel.confidence.desc())
        limit = query.get("limit", 20)
        stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._lesson_to_dict(m) for m in models]

    # ------------------------------------------------------------------
    # Recommendation retrieval
    # ------------------------------------------------------------------

    async def get_recommendations(
        self, task_context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Get recommendations relevant to a task context.

        Matches recommendations by task type and overlapping context keywords,
        then ranks by confidence and priority.

        Args:
            task_context: Dictionary with ``task_type``, ``technologies``,
                and ``context_keywords``.

        Returns:
            List of relevant recommendation dicts, sorted by relevance.
        """
        stmt = select(RecommendationModel)

        filters = []
        task_type = task_context.get("task_type")
        if task_type:
            filters.append(RecommendationModel.task_type == task_type)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Keyword overlap filter
        keywords = task_context.get("context_keywords", [])
        if keywords:
            kw_filters = [
                RecommendationModel.context_keywords.op("LIKE")(f"%{kw}%")
                for kw in keywords
            ]
            stmt = stmt.where(or_(*kw_filters))

        # Technology overlap filter
        techs = task_context.get("technologies", [])
        if techs:
            tech_filters = [
                RecommendationModel.technologies.op("LIKE")(f"%{t}%")
                for t in techs
            ]
            stmt = stmt.where(or_(*tech_filters))

        stmt = stmt.order_by(
            RecommendationModel.confidence.desc(),
        )
        stmt = stmt.limit(20)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._recommendation_to_dict(m) for m in models]

    # ------------------------------------------------------------------
    # Bulk retrieval for cross-workflow learning
    # ------------------------------------------------------------------

    async def get_all_patterns(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all stored patterns, ordered by confidence."""
        stmt = select(PatternModel).order_by(PatternModel.confidence.desc()).limit(limit)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._pattern_to_dict(m) for m in models]

    async def get_all_lessons(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all stored lessons, ordered by confidence."""
        stmt = select(LessonModel).order_by(LessonModel.confidence.desc()).limit(limit)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._lesson_to_dict(m) for m in models]

    async def get_all_experiences(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all stored experiences, ordered by created_at desc."""
        stmt = select(ExperienceModel).order_by(ExperienceModel.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._experience_to_dict(m) for m in models]

    async def get_experience_stats(self) -> dict[str, Any]:
        """Get aggregate statistics across all experiences."""
        from sqlalchemy import func as sqlfunc

        # Count by outcome
        outcome_stmt = select(
            ExperienceModel.outcome, sqlfunc.count(ExperienceModel.id)
        ).group_by(ExperienceModel.outcome)
        result = await self._session.execute(outcome_stmt)
        outcome_counts = {row[0]: row[1] for row in result.all()}

        # Count by type
        type_stmt = select(
            ExperienceModel.experience_type, sqlfunc.count(ExperienceModel.id)
        ).group_by(ExperienceModel.experience_type)
        result = await self._session.execute(type_stmt)
        type_counts = {row[0]: row[1] for row in result.all()}

        # Average confidence
        avg_stmt = select(sqlfunc.avg(ExperienceModel.confidence))
        avg_result = await self._session.execute(avg_stmt)
        avg_confidence = avg_result.scalar() or 0.0

        # Technology frequency
        all_exp = await self.get_all_experiences(limit=200)
        tech_freq: dict[str, int] = {}
        for exp in all_exp:
            for tech in exp.get("technologies", []):
                tech_freq[tech] = tech_freq.get(tech, 0) + 1

        return {
            "total": sum(outcome_counts.values()),
            "by_outcome": outcome_counts,
            "by_type": type_counts,
            "avg_confidence": round(float(avg_confidence), 2),
            "top_technologies": sorted(tech_freq.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    async def get_recent_experiences(
        self, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Retrieve the most recent experiences.

        Args:
            limit: Maximum number of experiences to return.

        Returns:
            List of recent experience dicts, newest first.
        """
        stmt = (
            select(ExperienceModel)
            .order_by(ExperienceModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._experience_to_dict(m) for m in models]

    async def get_stats(self) -> dict[str, Any]:
        """Compute aggregate learning statistics.

        Returns:
            Dictionary with total counts, average confidence, success rate,
            top technologies, top patterns, and experiences by type.
        """
        exp_count = await self._count(ExperienceModel)
        pat_count = await self._count(PatternModel)
        lesson_count = await self._count(LessonModel)
        feedback_count = await self._count(FeedbackModel)
        rec_count = await self._count(RecommendationModel)

        # Average confidence across experiences
        avg_conf_stmt = select(func.avg(ExperienceModel.confidence))
        avg_conf_result = await self._session.execute(avg_conf_stmt)
        avg_confidence = avg_conf_result.scalar() or 0.0

        # Success rate
        success_stmt = select(func.count(ExperienceModel.id)).where(
            ExperienceModel.outcome == OutcomeType.SUCCESS
        )
        success_result = await self._session.execute(success_stmt)
        success_count = success_result.scalar() or 0
        success_rate = (success_count / exp_count) if exp_count > 0 else 0.0

        # Top technologies (flattened from all experiences)
        tech_stmt = select(ExperienceModel.technologies)
        tech_result = await self._session.execute(tech_stmt)
        all_techs: dict[str, int] = {}
        for row in tech_result.scalars().all():
            if isinstance(row, list):
                for t in row:
                    all_techs[t] = all_techs.get(t, 0) + 1
        top_technologies = sorted(all_techs, key=all_techs.get, reverse=True)[:10]  # type: ignore[arg-type]

        # Top pattern names
        top_pat_stmt = (
            select(PatternModel.name, func.count(PatternModel.id).label("cnt"))
            .group_by(PatternModel.name)
            .order_by(func.count(PatternModel.id).desc())
            .limit(10)
        )
        top_pat_result = await self._session.execute(top_pat_stmt)
        top_patterns = [row[0] for row in top_pat_result.all()]

        # Experiences by type
        type_stmt = (
            select(
                ExperienceModel.experience_type,
                func.count(ExperienceModel.id).label("cnt"),
            )
            .group_by(ExperienceModel.experience_type)
            .order_by(func.count(ExperienceModel.id).desc())
        )
        type_result = await self._session.execute(type_stmt)
        experiences_by_type = {row[0]: row[1] for row in type_result.all()}

        return {
            "total_experiences": exp_count,
            "total_patterns": pat_count,
            "total_lessons": lesson_count,
            "total_feedback": feedback_count,
            "total_recommendations": rec_count,
            "average_confidence": round(float(avg_confidence), 3),
            "success_rate": round(float(success_rate), 3),
            "top_technologies": top_technologies,
            "top_patterns": top_patterns,
            "experiences_by_type": experiences_by_type,
            "generated_at": _now_utc().isoformat(),
        }

    async def get_growth_analytics(self) -> dict[str, Any]:
        """Compute growth analytics over time.

        Returns:
            Dictionary with experience time series, success rate trends,
            pattern usage over time, and summary counts.
        """
        # Experience count by date
        date_stmt = (
            select(
                func.date(ExperienceModel.created_at).label("date"),
                func.count(ExperienceModel.id).label("count"),
            )
            .group_by(func.date(ExperienceModel.created_at))
            .order_by(func.date(ExperienceModel.created_at))
        )
        date_result = await self._session.execute(date_stmt)
        experience_over_time = [
            {"date": str(row[0]), "count": row[1]} for row in date_result.all()
        ]

        # Success rate by date
        success_date_stmt = (
            select(
                func.date(ExperienceModel.created_at).label("date"),
                func.count(ExperienceModel.id).label("total"),
                func.sum(
                    func.cast(
                        ExperienceModel.outcome == OutcomeType.SUCCESS,
                        ExperienceModel.confidence.type,
                    )
                ).label("success_count"),
            )
            .group_by(func.date(ExperienceModel.created_at))
            .order_by(func.date(ExperienceModel.created_at))
        )
        success_result = await self._session.execute(success_date_stmt)
        success_rate_trends = []
        for row in success_result.all():
            total = row[1]
            successes = row[2] or 0
            rate = (successes / total) if total > 0 else 0.0
            success_rate_trends.append({
                "date": str(row[0]),
                "success_rate": round(float(rate), 3),
                "total_experiences": total,
            })

        # Pattern usage by date
        pat_date_stmt = (
            select(
                func.date(PatternModel.created_at).label("date"),
                PatternModel.name,
                func.count(PatternModel.id).label("count"),
            )
            .group_by(func.date(PatternModel.created_at), PatternModel.name)
            .order_by(func.date(PatternModel.created_at))
            .limit(100)
        )
        pat_result = await self._session.execute(pat_date_stmt)
        pattern_usage = [
            {"date": str(row[0]), "pattern_name": row[1], "count": row[2]}
            for row in pat_result.all()
        ]

        total_exp = await self._count(ExperienceModel)
        total_pat = await self._count(PatternModel)

        avg_conf_stmt = select(func.avg(ExperienceModel.confidence))
        avg_conf_result = await self._session.execute(avg_conf_stmt)
        avg_confidence = avg_conf_result.scalar() or 0.0

        return {
            "experience_over_time": experience_over_time,
            "success_rate_trends": success_rate_trends,
            "pattern_usage": pattern_usage,
            "total_experiences": total_exp,
            "total_patterns_discovered": total_pat,
            "average_confidence": round(float(avg_confidence), 3),
            "period_start": experience_over_time[0]["date"] if experience_over_time else None,
            "period_end": experience_over_time[-1]["date"] if experience_over_time else None,
        }

    # ------------------------------------------------------------------
    # Knowledge graph operations
    # ------------------------------------------------------------------

    async def create_knowledge_relation(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a relationship between two knowledge items.

        Args:
            source_type: Entity type of the source (experience, pattern, etc.).
            source_id: ID of the source entity.
            target_type: Entity type of the target.
            target_id: ID of the target entity.
            relation: Relationship type (derived_from, related_to, etc.).
            weight: Strength of the relationship (default 1.0).
            metadata: Optional metadata for the relation.
        """
        model = KnowledgeGraphModel(
            id=str(uuid4()),
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            relationship=relation,
            weight=weight,
            metadata_json=metadata or {},
        )
        self._session.add(model)
        await self._session.flush()
        logger.info(
            "Created knowledge relation",
            extra={
                "source": f"{source_type}:{source_id}",
                "target": f"{target_type}:{target_id}",
                "relation": relation,
            },
        )

    async def get_related_knowledge(
        self, entity_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        """Get all knowledge items related to an entity.

        Returns outgoing and incoming relations, including the related
        entity details where available.

        Args:
            entity_type: Entity type to search from.
            entity_id: ID of the entity.

        Returns:
            List of relation dicts with related entity info.
        """
        # Outgoing relations
        out_stmt = select(KnowledgeGraphModel).where(
            and_(
                KnowledgeGraphModel.source_type == entity_type,
                KnowledgeGraphModel.source_id == entity_id,
            )
        )
        out_result = await self._session.execute(out_stmt)
        outgoing = out_result.scalars().all()

        # Incoming relations
        in_stmt = select(KnowledgeGraphModel).where(
            and_(
                KnowledgeGraphModel.target_type == entity_type,
                KnowledgeGraphModel.target_id == entity_id,
            )
        )
        in_result = await self._session.execute(in_stmt)
        incoming = in_result.scalars().all()

        relations: list[dict[str, Any]] = []
        for rel in outgoing:
            relations.append({
                "relation_id": rel.id,
                "source_type": rel.source_type,
                "source_id": rel.source_id,
                "target_type": rel.target_type,
                "target_id": rel.target_id,
                "relationship": rel.relationship,
                "weight": rel.weight,
                "direction": "outgoing",
                "metadata": rel.metadata_json,
            })
        for rel in incoming:
            relations.append({
                "relation_id": rel.id,
                "source_type": rel.source_type,
                "source_id": rel.source_id,
                "target_type": rel.target_type,
                "target_id": rel.target_id,
                "relationship": rel.relationship,
                "weight": rel.weight,
                "direction": "incoming",
                "metadata": rel.metadata_json,
            })

        relations.sort(key=lambda r: r["weight"], reverse=True)
        return relations

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _count(self, model_class: type) -> int:
        """Return the row count for a model class."""
        stmt = select(func.count(model_class.id))
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    @staticmethod
    def _experience_to_dict(model: ExperienceModel) -> dict[str, Any]:
        """Convert an ExperienceModel to a dictionary."""
        return {
            "id": model.id,
            "workflow_id": model.workflow_id,
            "repository_id": model.repository_id,
            "experience_type": model.experience_type,
            "title": model.title,
            "description": model.description,
            "context": model.context,
            "outcome": model.outcome,
            "solution": model.solution,
            "files_changed": model.files_changed,
            "technologies": model.technologies,
            "tags": model.tags,
            "confidence": model.confidence,
            "reuse_potential": model.reuse_potential,
            "complexity": model.complexity,
            "success_rate": model.success_rate,
            "generalization_score": model.generalization_score,
            "feedback_score": model.feedback_score,
            "metadata": model.metadata_json,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }

    @staticmethod
    def _pattern_to_dict(model: PatternModel) -> dict[str, Any]:
        """Convert a PatternModel to a dictionary."""
        return {
            "id": model.id,
            "experience_id": model.experience_id,
            "pattern_type": model.pattern_type,
            "name": model.name,
            "description": model.description,
            "code_example": model.code_example,
            "when_to_use": model.when_to_use,
            "when_not_to_use": model.when_not_to_use,
            "technologies": model.technologies,
            "tags": model.tags,
            "confidence": model.confidence,
            "usage_count": model.usage_count,
            "success_count": model.success_count,
            "success_rate": model.success_rate,
            "generalization_score": model.generalization_score,
            "metadata": model.metadata_json,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }

    @staticmethod
    def _lesson_to_dict(model: LessonModel) -> dict[str, Any]:
        """Convert a LessonModel to a dictionary."""
        return {
            "id": model.id,
            "experience_id": model.experience_id,
            "lesson_type": model.lesson_type,
            "title": model.title,
            "description": model.description,
            "root_cause": model.root_cause,
            "avoidance_strategy": model.avoidance_strategy,
            "severity": model.severity,
            "technologies": model.technologies,
            "tags": model.tags,
            "confidence": model.confidence,
            "times_encountered": model.times_encountered,
            "metadata": model.metadata_json,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }

    @staticmethod
    def _recommendation_to_dict(model: RecommendationModel) -> dict[str, Any]:
        """Convert a RecommendationModel to a dictionary."""
        return {
            "id": model.id,
            "pattern_id": model.pattern_id,
            "task_type": model.task_type,
            "context_keywords": model.context_keywords,
            "recommendation": model.recommendation,
            "confidence": model.confidence,
            "priority": model.priority,
            "technologies": model.technologies,
            "metadata": model.metadata_json,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }
