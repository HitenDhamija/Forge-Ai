"""Recommendation Engine for the Learning Engine.

Generates recommendations for future tasks based on past experience,
patterns, and lessons. Retrieves relevant context and suggests
approaches, architectures, security practices, and testing strategies.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class RecommendationType(str, Enum):
    """Classification of recommendation types."""

    APPROACH = "approach"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    TESTING = "testing"
    AVOIDANCE = "avoidance"
    GENERAL = "general"


class Priority(str, Enum):
    """Priority level for recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RelevanceSignal(str, Enum):
    """Signals used to compute relevance scores."""

    TECHNOLOGY_MATCH = "technology_match"
    TASK_TYPE_MATCH = "task_type_match"
    TAG_MATCH = "tag_match"
    TEXT_SIMILARITY = "text_similarity"
    OUTCOME_WEIGHT = "outcome_weight"


# ---------------------------------------------------------------------------
# Pydantic schemas (public API contracts)
# ---------------------------------------------------------------------------


class RecommendationItem(BaseModel):
    """Single recommendation entry."""

    id: str
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: Priority
    confidence: float = Field(..., ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source_experience_id: str | None = None
    source_pattern_id: str | None = None
    source_lesson_id: str | None = None
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    rationale: str = ""


class RecommendationResponse(BaseModel):
    """Full recommendation response for a task context."""

    recommendations: list[RecommendationItem] = Field(default_factory=list)
    summary: str = ""
    task_keywords: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RelevanceConfig(BaseModel):
    """Configuration for relevance scoring weights."""

    technology_weight: float = Field(
        default=0.30, ge=0.0, le=1.0,
        description="Weight for technology overlap.",
    )
    task_type_weight: float = Field(
        default=0.25, ge=0.0, le=1.0,
        description="Weight for task type match.",
    )
    tag_weight: float = Field(
        default=0.20, ge=0.0, le=1.0,
        description="Weight for tag overlap.",
    )
    text_weight: float = Field(
        default=0.15, ge=0.0, le=1.0,
        description="Weight for textual similarity.",
    )
    outcome_weight: float = Field(
        default=0.10, ge=0.0, le=1.0,
        description="Weight for outcome alignment.",
    )


# ---------------------------------------------------------------------------
# Internal dataclasses
# ---------------------------------------------------------------------------


@dataclass
class _RelevanceScore:
    """Breakdown of relevance scoring signals."""

    technology_score: float = 0.0
    task_type_score: float = 0.0
    tag_score: float = 0.0
    text_score: float = 0.0
    outcome_score: float = 0.0
    total: float = 0.0


@dataclass
class _RecommendationContext:
    """Internal context built from task and knowledge base."""

    task_type: str = ""
    task_description: str = ""
    technologies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    risk_level: str = "medium"


@dataclass
class _RankedRecommendation:
    """Internal recommendation with ranking metadata."""

    item: RecommendationItem
    relevance: _RelevanceScore
    composite_score: float = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric tokens from text."""
    import re
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------------------
# RecommendationEngine
# ---------------------------------------------------------------------------


class RecommendationEngine:
    """Generates recommendations for future tasks based on past experience.

    Analyzes task context against stored experiences, patterns, and lessons
    to produce ranked, actionable recommendations.
    """

    def __init__(self, config: RelevanceConfig | None = None) -> None:
        self.config = config or RelevanceConfig()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_recommendations(
        self,
        task_context: dict[str, Any],
        past_experiences: list[dict[str, Any]],
        patterns: list[dict[str, Any]],
        lessons: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate genuine, actionable recommendations for a new task.

        Uses cross-workflow learning to provide specific guidance based on
        actual past experiences, detected patterns, and lessons learned.

        Args:
            task_context: Current task context including type, description,
                technologies, and other metadata.
            past_experiences: List of past experience records (from DB + current).
            patterns: List of extracted patterns (from DB + current).
            lessons: List of lessons learned (from DB + current).

        Returns:
            List of recommendation dictionaries sorted by priority.
        """
        logger.info(
            "Generating recommendations",
            extra={
                "task_type": task_context.get("task_type", ""),
                "experience_count": len(past_experiences),
                "pattern_count": len(patterns),
                "lesson_count": len(lessons),
            },
        )

        ctx = self._build_context(task_context)
        recommendations: list[dict[str, Any]] = []

        # --- 1. Pattern-based recommendations ---
        relevant_patterns = await self.find_relevant_patterns(ctx.__dict__, patterns)
        for pattern in relevant_patterns[:3]:
            confidence = pattern.get("confidence", 0.5)
            recommendations.append({
                "title": f"Apply pattern: {pattern.get('name', 'Unknown')}",
                "description": (
                    f"{pattern.get('description', '')}\n\n"
                    f"When to use: {pattern.get('when_to_use', 'When this pattern fits the problem.')}\n"
                    f"Avoid when: {pattern.get('when_not_to_use', 'When simpler alternatives exist.')}"
                ),
                "recommendation_type": "pattern",
                "source_pattern_id": pattern.get("id"),
                "source_name": pattern.get("name"),
                "technologies": pattern.get("technologies", []),
                "tags": pattern.get("tags", []) + ["pattern-based"],
                "confidence": confidence,
            })

        # --- 2. Experience-based recommendations ---
        similar_experiences = await self.find_similar_experiences(
            ctx.__dict__, past_experiences
        )

        # Group experiences by outcome
        successes = [e for e in similar_experiences if e.get("outcome") == "success"]
        failures = [e for e in similar_experiences if e.get("outcome") == "failure"]

        # Success recommendations
        for exp in successes[:2]:
            solution = exp.get("solution", "")
            files = exp.get("files_changed", [])
            desc_parts = [f"This approach worked before for a similar task ({exp.get('title', 'unknown')})."]
            if solution:
                desc_parts.append(f"\nSolution: {solution}")
            if files:
                desc_parts.append(f"\nFiles involved: {', '.join(files[:3])}")
            if not solution and not files:
                desc_parts.append(f"\nTechnologies used: {', '.join(exp.get('technologies', [])[:3])}")
            recommendations.append({
                "title": f"Reuse approach from: {exp.get('title', 'past task')}",
                "description": "\n".join(desc_parts),
                "recommendation_type": "proven",
                "source_experience_id": exp.get("id"),
                "source_name": exp.get("title"),
                "technologies": exp.get("technologies", []),
                "tags": ["proven", "reuse", "success"],
                "confidence": exp.get("confidence", 0.6),
            })

        # Failure avoidance recommendations
        for exp in failures[:2]:
            solution = exp.get("solution", "")
            desc_parts = [f"This approach failed before ({exp.get('title', 'unknown')})."]
            if solution:
                desc_parts.append(f"\nRoot cause: {solution}")
            desc_parts.append(f"\nUse a different approach for this task type.")
            recommendations.append({
                "title": f"Avoid: {exp.get('title', 'past failure')}",
                "description": "\n".join(desc_parts),
                "recommendation_type": "avoidance",
                "source_experience_id": exp.get("id"),
                "source_name": exp.get("title"),
                "technologies": exp.get("technologies", []),
                "tags": ["avoidance", "lesson", "failure"],
                "confidence": exp.get("confidence", 0.5),
            })

        # --- 3. Lesson-based recommendations ---
        relevant_lessons = await self.find_relevant_lessons(ctx.__dict__, lessons)
        for lesson in relevant_lessons[:2]:
            recommendations.append({
                "title": f"Watch out: {lesson.get('title', 'known issue')}",
                "description": (
                    f"Root cause: {lesson.get('root_cause', 'Unknown')}\n\n"
                    f"How to avoid: {lesson.get('avoidance_strategy', 'Follow best practices.')}\n\n"
                    f"Encountered {lesson.get('times_encountered', 1)} times."
                ),
                "recommendation_type": "lesson",
                "source_lesson_id": lesson.get("id"),
                "source_name": lesson.get("title"),
                "technologies": lesson.get("technologies", []),
                "tags": ["lesson", "warning"],
                "confidence": lesson.get("confidence", 0.6),
            })

        # --- 4. Technology-specific recommendations ---
        tech_recs = self._generate_tech_recommendations(ctx)
        recommendations.extend(tech_recs)

        # --- 5. Task-type specific recommendations ---
        task_recs = self._generate_task_recommendations(ctx, patterns, lessons)
        recommendations.extend(task_recs)

        # Enrich and rank
        enriched = self._enrich_recommendations(
            recommendations, ctx, relevant_patterns, relevant_lessons
        )
        ranked = self._rank_recommendations(enriched)

        logger.info(
            "Generated %d recommendations",
            len(ranked),
            extra={"task_type": ctx.task_type},
        )

        return ranked

    def _generate_tech_recommendations(self, ctx: "_RecommendationContext") -> list[dict[str, Any]]:
        """Generate technology-specific recommendations."""
        recs = []
        techs = [t.lower() for t in ctx.technologies]

        tech_guidance = {
            "python": {
                "title": "Python best practices",
                "description": "Use type hints, virtual environments, and linting (ruff/black). Consider async for I/O-bound tasks.",
                "tags": ["python", "best-practice"],
            },
            "fastapi": {
                "title": "FastAPI patterns",
                "description": "Use dependency injection, Pydantic models for validation, and async endpoints. Structure: routers/ → services/ → repositories.",
                "tags": ["fastapi", "api"],
            },
            "react": {
                "title": "React patterns",
                "description": "Use custom hooks for logic reuse, avoid prop drilling, prefer composition over inheritance. Consider React Query for server state.",
                "tags": ["react", "frontend"],
            },
            "typescript": {
                "title": "TypeScript safety",
                "description": "Enable strict mode, use discriminated unions for state, prefer interfaces for public APIs.",
                "tags": ["typescript", "safety"],
            },
            "docker": {
                "title": "Docker best practices",
                "description": "Use multi-stage builds, minimize layers, use .dockerignore, never run as root in production.",
                "tags": ["docker", "devops"],
            },
            "postgresql": {
                "title": "PostgreSQL patterns",
                "description": "Use transactions for multi-step operations, add indexes on frequently queried columns, use connection pooling.",
                "tags": ["postgresql", "database"],
            },
            "sqlalchemy": {
                "title": "SQLAlchemy patterns",
                "description": "Use async sessions, avoid N+1 queries with joinedload, use batch operations for bulk inserts.",
                "tags": ["sqlalchemy", "orm"],
            },
        }

        for tech in techs:
            if tech in tech_guidance:
                g = tech_guidance[tech]
                recs.append({
                    "title": g["title"],
                    "description": g["description"],
                    "recommendation_type": "technology",
                    "technologies": [tech],
                    "tags": g["tags"],
                    "confidence": 0.6,
                })

        return recs

    def _generate_task_recommendations(
        self,
        ctx: "_RecommendationContext",
        patterns: list[dict],
        lessons: list[dict],
    ) -> list[dict[str, Any]]:
        """Generate task-type specific recommendations."""
        recs = []
        task_type = ctx.task_type.lower() if ctx.task_type else ""

        task_guidance = {
            "feature": {
                "title": "Feature implementation checklist",
                "description": (
                    "1. Define acceptance criteria first\n"
                    "2. Write tests before implementation\n"
                    "3. Implement in small, testable increments\n"
                    "4. Update documentation\n"
                    "5. Consider edge cases and error handling"
                ),
            },
            "bug_fix": {
                "title": "Bug fix process",
                "description": (
                    "1. Reproduce the bug reliably\n"
                    "2. Write a failing test that captures the bug\n"
                    "3. Fix the test (now passes)\n"
                    "4. Check for similar bugs in related code\n"
                    "5. Add regression test"
                ),
            },
            "api": {
                "title": "API endpoint design",
                "description": (
                    "1. Use proper HTTP methods (GET/POST/PUT/DELETE)\n"
                    "2. Validate input with schemas\n"
                    "3. Handle errors consistently\n"
                    "4. Add rate limiting for public endpoints\n"
                    "5. Document with OpenAPI/Swagger"
                ),
            },
            "refactor": {
                "title": "Refactoring safety",
                "description": (
                    "1. Ensure existing tests pass before refactoring\n"
                    "2. Make small, incremental changes\n"
                    "3. Run tests after each change\n"
                    "4. Don't mix refactoring with feature changes\n"
                    "5. Update imports and references"
                ),
            },
            "migration": {
                "title": "Database migration safety",
                "description": (
                    "1. Write reversible migrations\n"
                    "2. Test with production-like data volume\n"
                    "3. Add indexes before deploying\n"
                    "4. Plan rollback strategy\n"
                    "5. Run migrations in a transaction"
                ),
            },
        }

        # Match task type
        for key, guidance in task_guidance.items():
            if key in task_type:
                recs.append({
                    "title": guidance["title"],
                    "description": guidance["description"],
                    "recommendation_type": "task-guidance",
                    "technologies": ctx.technologies,
                    "tags": ["task-type", key],
                    "confidence": 0.5,
                })
                break

        # Risk-based recommendations
        if ctx.risk_level in ("high", "critical"):
            recs.append({
                "title": "High-risk task: extra precautions",
                "description": (
                    "This is a high-risk task. Consider:\n"
                    "1. Create a feature branch\n"
                    "2. Add comprehensive tests\n"
                    "3. Set up monitoring/alerting\n"
                    "4. Prepare rollback plan\n"
                    "5. Do a code review before merging"
                ),
                "recommendation_type": "risk",
                "technologies": ctx.technologies,
                "tags": ["risk", "high-priority"],
                "confidence": 0.7,
            })

        return recs

    async def find_relevant_patterns(
        self,
        task_context: dict[str, Any],
        patterns: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Find patterns matching the current task.

        Args:
            task_context: Current task context.
            patterns: All available patterns.

        Returns:
            Patterns sorted by relevance, most relevant first.
        """
        scored: list[tuple[dict[str, Any], float]] = []
        for pattern in patterns:
            relevance = self._calculate_relevance(task_context, pattern)
            if relevance >= 0.2:
                scored.append((pattern, relevance))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored]

    async def find_relevant_lessons(
        self,
        task_context: dict[str, Any],
        lessons: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Find lessons that apply to the current task.

        Args:
            task_context: Current task context.
            lessons: All available lessons.

        Returns:
            Lessons sorted by relevance, most relevant first.
        """
        scored: list[tuple[dict[str, Any], float]] = []
        for lesson in lessons:
            relevance = self._calculate_relevance(task_context, lesson)
            if relevance >= 0.2:
                scored.append((lesson, relevance))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [l for l, _ in scored]

    async def find_similar_experiences(
        self,
        task_context: dict[str, Any],
        experiences: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Find past experiences similar to the current task.

        Args:
            task_context: Current task context.
            experiences: All available past experiences.

        Returns:
            Experiences sorted by relevance, most relevant first.
        """
        scored: list[tuple[dict[str, Any], float]] = []
        for experience in experiences:
            relevance = self._calculate_relevance(task_context, experience)
            if relevance >= 0.2:
                scored.append((experience, relevance))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored]

    async def generate_approach_recommendation(
        self,
        context: dict[str, Any],
        patterns: list[dict[str, Any]],
    ) -> str:
        """Suggest an implementation approach based on patterns.

        Args:
            context: Task context dictionary.
            patterns: Relevant patterns.

        Returns:
            Implementation approach recommendation string.
        """
        if not patterns:
            task_type = context.get("task_type", "task")
            return (
                f"No established patterns found for this {task_type}. "
                f"Consider breaking the task into smaller, testable units "
                f"and implementing incrementally."
            )

        top_pattern = patterns[0]
        pattern_name = top_pattern.get("name", "established approach")
        when_to_use = top_pattern.get("when_to_use", "")
        confidence = top_pattern.get("confidence", 0.5)

        parts = [
            f"Based on {len(patterns)} relevant pattern(s), "
            f"the recommended approach is to follow the '{pattern_name}' pattern."
        ]

        if when_to_use:
            parts.append(f"Guidance: {when_to_use}")

        if confidence >= 0.7:
            parts.append(
                "This pattern has high confidence from previous successful applications."
            )
        elif confidence >= 0.5:
            parts.append(
                "This pattern has moderate confidence; validate against current requirements."
            )
        else:
            parts.append(
                "This pattern has low confidence; adapt carefully to the current context."
            )

        task_techs = context.get("technologies", [])
        pattern_techs = top_pattern.get("technologies", [])
        if task_techs and pattern_techs:
            overlap = set(t.lower() for t in task_techs) & set(
                t.lower() for t in pattern_techs
            )
            if overlap:
                parts.append(
                    f"Technology alignment: {', '.join(sorted(overlap))}."
                )

        return " ".join(parts)

    async def generate_architecture_recommendation(
        self,
        context: dict[str, Any],
        patterns: list[dict[str, Any]],
    ) -> str:
        """Suggest an architecture based on patterns and context.

        Args:
            context: Task context dictionary.
            patterns: Relevant patterns.

        Returns:
            Architecture recommendation string.
        """
        arch_patterns = [
            p for p in patterns
            if p.get("pattern_type") == "architecture"
        ]

        if not arch_patterns:
            task_type = context.get("task_type", "task")
            complexity = context.get("complexity", 0.5)
            if complexity > 0.7:
                return (
                    f"This {task_type} has high complexity. "
                    f"Consider a layered architecture with clear separation "
                    f"of concerns: presentation, business logic, and data access layers."
                )
            return (
                f"For this {task_type}, a straightforward modular architecture "
                f"with clear interfaces between components is recommended."
            )

        top = arch_patterns[0]
        name = top.get("name", "layered architecture")
        description = top.get("description", "")
        confidence = top.get("confidence", 0.5)

        parts = [
            f"Recommended architecture: {name}."
        ]

        if description:
            parts.append(f"Description: {description}")

        when_not = top.get("when_not_to_use", "")
        if when_not:
            parts.append(f"Caution: {when_not}")

        files = context.get("files_changed", [])
        if files:
            dirs = set()
            for f in files:
                parts_list = f.split("/")
                if len(parts_list) > 1:
                    dirs.add(parts_list[0])
            if dirs:
                parts.append(
                    f"Existing module structure: {', '.join(sorted(dirs))}. "
                    f"Align new architecture with this structure."
                )

        if confidence >= 0.7:
            parts.append("This architecture has been validated in similar past projects.")
        else:
            parts.append(
                "Consider prototyping the architecture before full implementation."
            )

        return " ".join(parts)

    async def generate_security_recommendation(
        self,
        context: dict[str, Any],
        lessons: list[dict[str, Any]],
    ) -> str:
        """Provide security guidance based on lessons and context.

        Args:
            context: Task context dictionary.
            lessons: Relevant lessons (especially security-related).

        Returns:
            Security recommendation string.
        """
        security_lessons = [
            l for l in lessons
            if l.get("lesson_type") in ("security_issue", "violation")
            or "security" in l.get("tags", [])
        ]

        if not security_lessons:
            task_type = context.get("task_type", "task")
            return (
                f"No specific security lessons found for this {task_type}. "
                f"Follow standard security practices: validate all inputs, "
                f"use parameterized queries, encrypt sensitive data at rest "
                f"and in transit, and implement proper authentication and "
                f"authorization checks."
            )

        parts = [
            f"Security warnings from {len(security_lessons)} past lesson(s):"
        ]

        for lesson in security_lessons[:3]:
            title = lesson.get("title", "Unknown issue")
            severity = lesson.get("severity", "medium")
            avoidance = lesson.get("avoidance_strategy") or lesson.get(
                "recommendation", ""
            )
            parts.append(
                f"- [{severity.upper()}] {title}: {avoidance}"
            )

        risk_level = context.get("risk_level", "medium")
        if risk_level in ("high", "critical"):
            parts.append(
                "This task is high-risk. Apply defense-in-depth: "
                "input validation, output encoding, least-privilege access, "
                "and comprehensive audit logging."
            )

        return " ".join(parts)

    async def generate_testing_recommendation(
        self,
        context: dict[str, Any],
        patterns: list[dict[str, Any]],
    ) -> str:
        """Suggest a testing strategy based on patterns.

        Args:
            context: Task context dictionary.
            patterns: Relevant patterns.

        Returns:
            Testing strategy recommendation string.
        """
        testing_patterns = [
            p for p in patterns
            if p.get("pattern_type") == "testing"
        ]

        if not testing_patterns:
            task_type = context.get("task_type", "task")
            complexity = context.get("complexity", 0.5)
            if complexity > 0.6:
                return (
                    f"This {task_type} has moderate-to-high complexity. "
                    f"Apply the test pyramid: many unit tests at the base, "
                    f"fewer integration tests, and minimal end-to-end tests. "
                    f"Mock external dependencies for isolation."
                )
            return (
                f"Standard testing for this {task_type}: write unit tests "
                f"for core logic, integration tests for external boundaries, "
                f"and ensure edge cases are covered."
            )

        top = testing_patterns[0]
        name = top.get("name", "test pyramid")
        description = top.get("description", "")
        confidence = top.get("confidence", 0.5)

        parts = [f"Testing strategy: {name}."]

        if description:
            parts.append(f"Approach: {description}")

        techs = context.get("technologies", [])
        test_frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "go": "testing",
            "rust": "cargo test",
            "java": "junit",
        }
        detected_frameworks = []
        for tech in techs:
            fw = test_frameworks.get(tech.lower())
            if fw and fw not in detected_frameworks:
                detected_frameworks.append(fw)
        if detected_frameworks:
            parts.append(
                f"Suggested frameworks: {', '.join(detected_frameworks)}."
            )

        files = context.get("files_changed", [])
        test_files = [f for f in files if "test" in f.lower() or "spec" in f.lower()]
        if not test_files:
            parts.append(
                "No test files detected in changed files. "
                "Ensure corresponding tests are created or updated."
            )

        if confidence >= 0.7:
            parts.append(
                "This testing approach has been validated in similar past tasks."
            )

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Scoring and ranking
    # ------------------------------------------------------------------

    def _calculate_relevance(
        self, task: dict[str, Any], item: dict[str, Any]
    ) -> float:
        """Score how relevant an item is to the current task.

        Computes a weighted combination of technology overlap, task type
        match, tag overlap, textual similarity, and outcome alignment.

        Args:
            task: Current task context.
            item: The experience, pattern, or lesson to score.

        Returns:
            Relevance score between 0.0 and 1.0.
        """
        cfg = self.config

        task_techs = set(t.lower() for t in task.get("technologies", []))
        item_techs = set(t.lower() for t in item.get("technologies", []))
        tech_score = _jaccard(task_techs, item_techs)

        task_type = task.get("task_type", "").lower()
        item_type = (
            item.get("experience_type", "")
            or item.get("pattern_type", "")
            or item.get("lesson_type", "")
        ).lower()
        type_score = 1.0 if task_type and task_type == item_type else 0.0

        task_tags = set(t.lower() for t in task.get("tags", []))
        item_tags = set(t.lower() for t in item.get("tags", []))
        tag_score = _jaccard(task_tags, item_tags)

        task_text = _tokenize(
            f"{task.get('task_description', '')} {task.get('title', '')} "
            f"{' '.join(task.get('keywords', []))}"
        )
        item_text = _tokenize(
            f"{item.get('description', '')} {item.get('title', '')} "
            f"{item.get('solution', '')} {item.get('name', '')}"
        )
        text_score = _jaccard(task_text, item_text)

        task_outcome = task.get("outcome", "").lower()
        item_outcome = item.get("outcome", "").lower()
        if task_outcome and item_outcome:
            outcome_score = 1.0 if task_outcome == item_outcome else 0.3
        else:
            outcome_score = 0.5

        total = (
            cfg.technology_weight * tech_score
            + cfg.task_type_weight * type_score
            + cfg.tag_weight * tag_score
            + cfg.text_weight * text_score
            + cfg.outcome_weight * outcome_score
        )

        return round(min(1.0, max(0.0, total)), 4)

    def _rank_recommendations(
        self, recommendations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Sort recommendations by priority and relevance.

        Orders by priority (high > medium > low), then by confidence,
        then by relevance score.

        Args:
            recommendations: List of recommendation dictionaries.

        Returns:
            Sorted list of recommendations.
        """
        priority_order = {Priority.HIGH.value: 0, Priority.MEDIUM.value: 1, Priority.LOW.value: 2}

        def sort_key(rec: dict[str, Any]) -> tuple[int, float, float]:
            priority_val = priority_order.get(rec.get("priority", "low"), 2)
            confidence = rec.get("confidence", 0.0)
            relevance = rec.get("relevance_score", 0.0)
            return (priority_val, -confidence, -relevance)

        return sorted(recommendations, key=sort_key)

    def _generate_summary(self, recommendations: list[dict[str, Any]]) -> str:
        """Generate a human-readable summary of recommendations.

        Args:
            recommendations: List of recommendation dictionaries.

        Returns:
            Summary string.
        """
        if not recommendations:
            return "No recommendations available for this task."

        high = sum(1 for r in recommendations if r.get("priority") == "high")
        medium = sum(1 for r in recommendations if r.get("priority") == "medium")
        low = sum(1 for r in recommendations if r.get("priority") == "low")

        type_counts: dict[str, int] = {}
        for r in recommendations:
            rtype = r.get("recommendation_type", "general")
            type_counts[rtype] = type_counts.get(rtype, 0) + 1

        parts = [f"Generated {len(recommendations)} recommendation(s)."]
        if high:
            parts.append(f"{high} high priority.")
        if medium:
            parts.append(f"{medium} medium priority.")
        if low:
            parts.append(f"{low} low priority.")

        type_parts = [f"{count} {rtype}" for rtype, count in type_counts.items()]
        if type_parts:
            parts.append(f"Types: {', '.join(type_parts)}.")

        return " ".join(parts)

    def _determine_priority(self, recommendation: dict[str, Any]) -> str:
        """Determine the priority level for a recommendation.

        Factors in confidence, severity, outcome, and type.

        Args:
            recommendation: Recommendation dictionary.

        Returns:
            Priority level string.
        """
        confidence = recommendation.get("confidence", 0.5)
        recommendation_type = recommendation.get("recommendation_type", "general")
        severity = recommendation.get("severity", "medium")

        if recommendation_type == "avoidance":
            if severity in ("critical", "high") or confidence >= 0.8:
                return Priority.HIGH.value
            return Priority.MEDIUM.value

        if confidence >= 0.8:
            return Priority.HIGH.value
        if confidence >= 0.5:
            return Priority.MEDIUM.value
        return Priority.LOW.value

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_context(self, task_context: dict[str, Any]) -> _RecommendationContext:
        """Build internal context from task data.

        Args:
            task_context: Raw task context dictionary.

        Returns:
            Normalized _RecommendationContext.
        """
        return _RecommendationContext(
            task_type=task_context.get("task_type", ""),
            task_description=task_context.get("task_description", "")
            or task_context.get("description", ""),
            technologies=task_context.get("technologies", []),
            tags=task_context.get("tags", []),
            keywords=task_context.get("context_keywords", [])
            or task_context.get("keywords", []),
            files_changed=task_context.get("files_changed", []),
            risk_level=task_context.get("risk_level", "medium"),
        )

    def _enrich_recommendations(
        self,
        recommendations: list[dict[str, Any]],
        ctx: _RecommendationContext,
        patterns: list[dict[str, Any]],
        lessons: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Enrich recommendation dicts with computed fields.

        Adds id, priority, confidence, relevance_score, and rationale
        to each recommendation.

        Args:
            recommendations: Raw recommendation dictionaries.
            ctx: Task context.
            patterns: Relevant patterns.
            lessons: Relevant lessons.

        Returns:
            Enriched recommendation dictionaries.
        """
        import uuid

        enriched: list[dict[str, Any]] = []
        for rec in recommendations:
            rec_id = str(uuid.uuid4())
            pattern_id = rec.get("source_pattern_id")
            lesson_id = rec.get("source_lesson_id")
            source_exp_id = rec.get("source_experience_id")

            confidence = 0.5
            relevance_score = 0.0

            if pattern_id:
                for p in patterns:
                    if p.get("id") == pattern_id:
                        confidence = p.get("confidence", 0.5)
                        relevance_score = self._calculate_relevance(
                            ctx.__dict__, p
                        )
                        break

            if lesson_id:
                for l in lessons:
                    if l.get("id") == lesson_id:
                        confidence = l.get("confidence", 0.5)
                        relevance_score = self._calculate_relevance(
                            ctx.__dict__, l
                        )
                        break

            if source_exp_id and relevance_score == 0.0:
                relevance_score = 0.4

            priority = self._determine_priority({
                "confidence": confidence,
                "recommendation_type": rec.get("recommendation_type", "general"),
                "severity": rec.get("severity", "medium"),
            })

            rationale = self._build_rationale(rec, patterns, lessons, ctx)

            enriched.append({
                **rec,
                "id": rec_id,
                "priority": priority,
                "confidence": confidence,
                "relevance_score": relevance_score,
                "rationale": rationale,
            })

        return enriched

    def _build_rationale(
        self,
        rec: dict[str, Any],
        patterns: list[dict[str, Any]],
        lessons: list[dict[str, Any]],
        ctx: _RecommendationContext,
    ) -> str:
        """Build a rationale string explaining why this recommendation was made.

        Args:
            rec: Recommendation dictionary.
            patterns: Relevant patterns.
            lessons: Relevant lessons.
            ctx: Task context.

        Returns:
            Rationale string.
        """
        parts: list[str] = []
        rtype = rec.get("recommendation_type", "general")
        source_name = rec.get("source_name", "")

        if rtype == "pattern":
            parts.append(f"Detected pattern: {source_name}" if source_name else "Based on detected code pattern.")
        elif rtype == "proven":
            parts.append(f"Worked before: {source_name}" if source_name else "Based on a successful past experience.")
        elif rtype == "avoidance":
            parts.append(f"Failed before: {source_name}" if source_name else "Based on a past failure.")
        elif rtype == "lesson":
            parts.append(f"Known issue: {source_name}" if source_name else "Based on a recorded lesson.")
        elif rtype == "technology":
            parts.append("Technology-specific best practice.")
        elif rtype == "task-guidance":
            parts.append("Task-type specific guidance.")
        elif rtype == "risk":
            parts.append("High-risk task requires extra precautions.")
        else:
            parts.append("Based on cross-workflow analysis.")

        task_techs = set(t.lower() for t in ctx.technologies)
        rec_techs = set(t.lower() for t in rec.get("technologies", []))
        overlap = task_techs & rec_techs
        if overlap:
            parts.append(f"Matching technologies: {', '.join(sorted(overlap))}.")

        if ctx.risk_level in ("high", "critical"):
            parts.append(f"Risk level: {ctx.risk_level}.")

        confidence = rec.get("confidence", 0.5)
        if confidence >= 0.7:
            parts.append("High confidence based on multiple data points.")
        elif confidence >= 0.5:
            parts.append("Moderate confidence.")

        return " ".join(parts)
