"""Failure Analyzer for the Learning Engine.

Analyzes failures, rejected implementations, security issues, performance
regressions, architecture violations, and testing failures. Extracts root
causes, avoidance strategies, and creates structured lesson records.
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


class LessonType(str, Enum):
    """Classification of lesson sources."""

    FAILURE = "failure"
    REJECTION = "rejection"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    ARCHITECTURE_VIOLATION = "architecture_violation"
    TESTING_FAILURE = "testing_failure"


class Severity(str, Enum):
    """Severity level for lessons and issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Pydantic schemas (public API contracts)
# ---------------------------------------------------------------------------


class FailureAnalysisRequest(BaseModel):
    """Request to analyze a workflow failure."""

    workflow_data: dict[str, Any] = Field(default_factory=dict)
    error_data: dict[str, Any] = Field(default_factory=dict)


class RejectionAnalysisRequest(BaseModel):
    """Request to analyze a code review rejection."""

    review_data: dict[str, Any] = Field(default_factory=dict)


class SecurityAnalysisRequest(BaseModel):
    """Request to analyze a security finding."""

    security_data: dict[str, Any] = Field(default_factory=dict)


class PerformanceAnalysisRequest(BaseModel):
    """Request to analyze a performance regression."""

    perf_data: dict[str, Any] = Field(default_factory=dict)


class ArchitectureAnalysisRequest(BaseModel):
    """Request to analyze an architecture violation."""

    violation_data: dict[str, Any] = Field(default_factory=dict)


class TestingAnalysisRequest(BaseModel):
    """Request to analyze a test failure."""

    test_data: dict[str, Any] = Field(default_factory=dict)


class LessonResponse(BaseModel):
    """Structured lesson record returned to callers."""

    lesson_type: str
    title: str
    description: str
    root_cause: str
    avoidance_strategy: str
    severity: str
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    times_encountered: int = Field(default=1, ge=1)
    encountered_at: str = ""
    related_lessons: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


@dataclass
class LessonData:
    """Internal representation of a lesson record between learning modules.

    Attributes:
        lesson_type: Classification of the lesson source.
        title: Short human-readable title for the lesson.
        description: Detailed description of what happened and why.
        root_cause: Identified root cause of the failure or issue.
        avoidance_strategy: Actionable steps to prevent recurrence.
        severity: Impact severity of this lesson (critical/high/medium/low).
        technologies: Technologies involved in this failure.
        tags: Arbitrary tags for filtering and retrieval.
        confidence: Confidence score for this analysis (0.0-1.0).
    """

    lesson_type: LessonType
    title: str
    description: str
    root_cause: str
    avoidance_strategy: str
    severity: Severity = Severity.MEDIUM
    technologies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.5


# ---------------------------------------------------------------------------
# Keyword maps for root-cause extraction
# ---------------------------------------------------------------------------

_ERROR_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "null_reference": [
        "nullpointer", "none", "noneType", "attributeerror", "undefined",
        "not defined", "cannot read prop",
    ],
    "type_mismatch": [
        "typeerror", "unexpected type", "expected", "incompatible",
        "cannot convert", "argument must be",
    ],
    "import_error": [
        "modulenotfound", "importerror", "cannot import", "no module named",
        "module not found",
    ],
    "network_io": [
        "timeout", "connection refused", "connection reset", "eof",
        "broken pipe", "network", "dns", "socket",
    ],
    "permission": [
        "permission denied", "access denied", "forbidden", "unauthorized",
        "authentication", "401", "403",
    ],
    "resource_exhaustion": [
        "out of memory", "oom", "heap", "memoryerror", "disk full",
        "no space left", "too many open files", "emfile",
    ],
    "configuration": [
        "config", "env var", "environment variable", "missing key",
        "keyerror", "missing field", "validation error",
    ],
    "database": [
        "deadlock", "lock wait timeout", "unique constraint",
        "foreign key", "connection pool", "transaction",
    ],
    "concurrency": [
        "race condition", "deadlock", "thread", "async", "await",
        "concurrent", "atomic",
    ],
    "syntax": [
        "syntaxerror", "indentation", "unexpected token", "invalid syntax",
        "parse error",
    ],
}

_AVOIDANCE_STRATEGIES: dict[str, str] = {
    "null_reference": (
        "Add null/None checks before accessing attributes. Use optional "
        "chaining or guard clauses. Leverage type hints and static analysis "
        "tools to catch potential null references at development time."
    ),
    "type_mismatch": (
        "Validate input types at system boundaries using Pydantic models or "
        "runtime assertions. Use explicit type conversions and leverage "
        "mypy or similar tools for static type checking."
    ),
    "import_error": (
        "Verify all dependencies are declared in requirements files. "
        "Pin dependency versions and test imports in CI. Use try/except "
        "for optional dependencies with clear error messages."
    ),
    "network_io": (
        "Implement retry logic with exponential backoff for transient "
        "failures. Add circuit breakers for external services. Set "
        "appropriate timeouts and implement fallback behavior."
    ),
    "permission": (
        "Ensure credentials and tokens are valid and not expired. Use "
        "principle of least privilege. Implement proper RBAC checks "
        "before operation execution."
    ),
    "resource_exhaustion": (
        "Monitor resource usage and set alerting thresholds. Implement "
        "connection pooling, pagination, and streaming for large data. "
        "Use async patterns to avoid blocking on I/O."
    ),
    "configuration": (
        "Centralize configuration in validated config files or environment "
        "variables. Add startup validation to catch missing config early. "
        "Document all required and optional settings."
    ),
    "database": (
        "Use consistent ordering for multi-table operations to prevent "
        "deadlocks. Set appropriate timeouts and implement retry logic. "
        "Use connection pooling and batch operations."
    ),
    "concurrency": (
        "Use proper synchronization primitives. Prefer immutable data "
        "structures and message passing over shared state. Apply "
        "databases-level locking for critical sections."
    ),
    "syntax": (
        "Use linting and formatting tools in pre-commit hooks. Run "
        "type checkers and syntax validators in CI. Adopt consistent "
        "coding standards enforced by automated tooling."
    ),
}


# ---------------------------------------------------------------------------
# FailureAnalyzer
# ---------------------------------------------------------------------------


class FailureAnalyzer:
    """Analyzes failures, rejected implementations, and lessons learned.

    Extracts root causes from error messages and context, generates
    actionable avoidance strategies, tracks repeated failures, and
    connects related failures across workflows.
    """

    # ------------------------------------------------------------------
    # Public analysis methods
    # ------------------------------------------------------------------

    async def analyze_failure(
        self, workflow_data: dict[str, Any], error_data: dict[str, Any]
    ) -> LessonData:
        """Analyze a workflow failure and produce a structured lesson.

        Args:
            workflow_data: Dictionary containing workflow definition, tasks,
                execution results, and metadata.
            error_data: Dictionary containing error details such as message,
                traceback, error type, and context.

        Returns:
            A LessonData record capturing the failure analysis.
        """
        logger.info(
            "Analyzing workflow failure",
            extra={"workflow_id": workflow_data.get("id", "unknown")},
        )

        context = self._build_failure_context(workflow_data, error_data)
        root_cause = await self._extract_root_cause(context, error_data)
        avoidance = await self._determine_avoidance_strategy(root_cause, context)
        severity = await self._assess_severity(context)
        title = await self._extract_lesson_title(context)

        description = self._build_failure_description(context, error_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context, LessonType.FAILURE)
        confidence = self._calculate_failure_confidence(context, error_data)

        lesson = LessonData(
            lesson_type=LessonType.FAILURE,
            title=title,
            description=description,
            root_cause=root_cause,
            avoidance_strategy=avoidance,
            severity=severity,
            technologies=technologies,
            tags=tags,
            confidence=confidence,
        )

        logger.info(
            "Workflow failure analyzed",
            extra={
                "lesson_type": lesson.lesson_type.value,
                "severity": lesson.severity.value,
                "confidence": lesson.confidence,
            },
        )

        return lesson

    async def analyze_rejection(
        self, review_data: dict[str, Any]
    ) -> LessonData:
        """Analyze a code review rejection and produce a structured lesson.

        Args:
            review_data: Dictionary containing review feedback, changed files,
                reviewer comments, and rejection reasons.

        Returns:
            A LessonData record capturing the rejection analysis.
        """
        logger.info(
            "Analyzing code review rejection",
            extra={"review_id": review_data.get("id", "unknown")},
        )

        context = self._build_rejection_context(review_data)
        root_cause = await self._extract_root_cause(context, review_data)
        avoidance = await self._determine_avoidance_strategy(root_cause, context)
        severity = await self._assess_severity(context)
        title = await self._extract_lesson_title(context)

        description = self._build_rejection_description(context, review_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context, LessonType.REJECTION)
        confidence = self._calculate_rejection_confidence(review_data)

        lesson = LessonData(
            lesson_type=LessonType.REJECTION,
            title=title,
            description=description,
            root_cause=root_cause,
            avoidance_strategy=avoidance,
            severity=severity,
            technologies=technologies,
            tags=tags,
            confidence=confidence,
        )

        logger.info(
            "Rejection analyzed",
            extra={
                "lesson_type": lesson.lesson_type.value,
                "severity": lesson.severity.value,
            },
        )

        return lesson

    async def analyze_security_issue(
        self, security_data: dict[str, Any]
    ) -> LessonData:
        """Analyze a security finding and produce a structured lesson.

        Args:
            security_data: Dictionary containing vulnerability details,
                affected files, severity rating, and remediation guidance.

        Returns:
            A LessonData record capturing the security analysis.
        """
        logger.info(
            "Analyzing security issue",
            extra={"issue_id": security_data.get("id", "unknown")},
        )

        context = self._build_security_context(security_data)
        root_cause = await self._extract_root_cause(context, security_data)
        avoidance = await self._determine_avoidance_strategy(root_cause, context)
        severity = await self._assess_severity(context)
        title = await self._extract_lesson_title(context)

        description = self._build_security_description(context, security_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context, LessonType.SECURITY_ISSUE)
        confidence = self._calculate_security_confidence(security_data)

        # Security issues tend toward higher severity
        if severity == Severity.MEDIUM and self._is_security_critical(
            security_data
        ):
            severity = Severity.HIGH

        lesson = LessonData(
            lesson_type=LessonType.SECURITY_ISSUE,
            title=title,
            description=description,
            root_cause=root_cause,
            avoidance_strategy=avoidance,
            severity=severity,
            technologies=technologies,
            tags=tags,
            confidence=confidence,
        )

        logger.info(
            "Security issue analyzed",
            extra={
                "lesson_type": lesson.lesson_type.value,
                "severity": lesson.severity.value,
            },
        )

        return lesson

    async def analyze_performance_issue(
        self, perf_data: dict[str, Any]
    ) -> LessonData:
        """Analyze a performance regression and produce a structured lesson.

        Args:
            perf_data: Dictionary containing performance metrics, benchmarks,
                regression details, and affected components.

        Returns:
            A LessonData record capturing the performance analysis.
        """
        logger.info(
            "Analyzing performance issue",
            extra={"issue_id": perf_data.get("id", "unknown")},
        )

        context = self._build_performance_context(perf_data)
        root_cause = await self._extract_root_cause(context, perf_data)
        avoidance = await self._determine_avoidance_strategy(root_cause, context)
        severity = await self._assess_severity(context)
        title = await self._extract_lesson_title(context)

        description = self._build_performance_description(context, perf_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context, LessonType.PERFORMANCE_ISSUE)
        confidence = self._calculate_performance_confidence(perf_data)

        lesson = LessonData(
            lesson_type=LessonType.PERFORMANCE_ISSUE,
            title=title,
            description=description,
            root_cause=root_cause,
            avoidance_strategy=avoidance,
            severity=severity,
            technologies=technologies,
            tags=tags,
            confidence=confidence,
        )

        logger.info(
            "Performance issue analyzed",
            extra={
                "lesson_type": lesson.lesson_type.value,
                "severity": lesson.severity.value,
            },
        )

        return lesson

    async def analyze_architecture_violation(
        self, violation_data: dict[str, Any]
    ) -> LessonData:
        """Analyze an architecture violation and produce a structured lesson.

        Args:
            violation_data: Dictionary containing the violation description,
                rule broken, affected modules, and architectural context.

        Returns:
            A LessonData record capturing the architecture analysis.
        """
        logger.info(
            "Analyzing architecture violation",
            extra={"violation_id": violation_data.get("id", "unknown")},
        )

        context = self._build_architecture_context(violation_data)
        root_cause = await self._extract_root_cause(context, violation_data)
        avoidance = await self._determine_avoidance_strategy(root_cause, context)
        severity = await self._assess_severity(context)
        title = await self._extract_lesson_title(context)

        description = self._build_architecture_description(
            context, violation_data
        )
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context, LessonType.ARCHITECTURE_VIOLATION)
        confidence = self._calculate_architecture_confidence(violation_data)

        lesson = LessonData(
            lesson_type=LessonType.ARCHITECTURE_VIOLATION,
            title=title,
            description=description,
            root_cause=root_cause,
            avoidance_strategy=avoidance,
            severity=severity,
            technologies=technologies,
            tags=tags,
            confidence=confidence,
        )

        logger.info(
            "Architecture violation analyzed",
            extra={
                "lesson_type": lesson.lesson_type.value,
                "severity": lesson.severity.value,
            },
        )

        return lesson

    async def analyze_testing_failure(
        self, test_data: dict[str, Any]
    ) -> LessonData:
        """Analyze a test failure and produce a structured lesson.

        Args:
            test_data: Dictionary containing test results, failure messages,
                stack traces, and test metadata.

        Returns:
            A LessonData record capturing the testing analysis.
        """
        logger.info(
            "Analyzing testing failure",
            extra={"test_id": test_data.get("id", "unknown")},
        )

        context = self._build_testing_context(test_data)
        root_cause = await self._extract_root_cause(context, test_data)
        avoidance = await self._determine_avoidance_strategy(root_cause, context)
        severity = await self._assess_severity(context)
        title = await self._extract_lesson_title(context)

        description = self._build_testing_description(context, test_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context, LessonType.TESTING_FAILURE)
        confidence = self._calculate_testing_confidence(test_data)

        lesson = LessonData(
            lesson_type=LessonType.TESTING_FAILURE,
            title=title,
            description=description,
            root_cause=root_cause,
            avoidance_strategy=avoidance,
            severity=severity,
            technologies=technologies,
            tags=tags,
            confidence=confidence,
        )

        logger.info(
            "Testing failure analyzed",
            extra={
                "lesson_type": lesson.lesson_type.value,
                "severity": lesson.severity.value,
            },
        )

        return lesson

    # ------------------------------------------------------------------
    # Core extraction methods
    # ------------------------------------------------------------------

    async def _extract_root_cause(
        self, context: dict[str, Any], error: dict[str, Any]
    ) -> str:
        """Identify the root cause from error messages and context.

        Scans error messages, stack traces, and contextual information
        against known error category patterns to classify the root cause.

        Args:
            context: The built context dictionary.
            error: Error or issue data dictionary.

        Returns:
            A descriptive root cause string.
        """
        error_message = (
            error.get("message", "")
            or error.get("error_message", "")
            or error.get("error", "")
            or error.get("summary", "")
        ).lower()

        error_type = (
            error.get("type", "")
            or error.get("error_type", "")
            or error.get("exception_type", "")
        ).lower()

        traceback_text = (
            error.get("traceback", "")
            or error.get("stack_trace", "")
            or error.get("trace", "")
        ).lower()

        combined_text = f"{error_message} {error_type} {traceback_text}"

        # Match against known error categories
        category_scores: dict[str, int] = {}
        for category, keywords in _ERROR_CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in combined_text)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            best_category = max(category_scores, key=category_scores.get)  # type: ignore[arg-type]
            return self._format_root_cause(best_category, context, error)

        # Fallback: derive from available context
        return self._derive_root_cause_from_context(context, error)

    async def _determine_avoidance_strategy(
        self, root_cause: str, context: dict[str, Any]
    ) -> str:
        """Generate an actionable avoidance strategy for the root cause.

        Matches the identified root cause against known strategy templates
        and augments with context-specific guidance.

        Args:
            root_cause: The identified root cause string.
            context: The built context dictionary.

        Returns:
            An actionable avoidance strategy description.
        """
        root_lower = root_cause.lower()

        # Direct match against known strategies
        for category, strategy in _AVOIDANCE_STRATEGIES.items():
            category_words = category.replace("_", " ")
            if category_words in root_lower or category in root_lower:
                context_specific = self._add_context_to_strategy(
                    strategy, context
                )
                return context_specific

        # Fallback: generic strategy with context
        return self._build_generic_avoidance_strategy(context)

    async def _assess_severity(self, context: dict[str, Any]) -> str:
        """Rate the severity of a failure based on contextual signals.

        Evaluates impact radius, error frequency, and domain-specific
        risk indicators to assign a severity level.

        Args:
            context: The built context dictionary.

        Returns:
            Severity string: 'critical', 'high', 'medium', or 'low'.
        """
        score = 0

        # Error frequency signal
        times_encountered = context.get("times_encountered", 1)
        if isinstance(times_encountered, (int, float)):
            if times_encountered >= 10:
                score += 3
            elif times_encountered >= 5:
                score += 2
            elif times_encountered >= 2:
                score += 1

        # Impact radius signal (files affected)
        files = context.get("files_changed", [])
        if isinstance(files, list):
            file_count = len(files)
            if file_count >= 10:
                score += 2
            elif file_count >= 5:
                score += 1

        # Task completion signal
        tasks_total = context.get("tasks_total", 0)
        tasks_completed = context.get("tasks_completed", 0)
        if isinstance(tasks_total, (int, float)) and tasks_total > 0:
            failure_ratio = 1.0 - (tasks_completed / tasks_total)
            if failure_ratio >= 0.8:
                score += 2
            elif failure_ratio >= 0.5:
                score += 1

        # Risk level from upstream assessment
        risk_level = context.get("risk_level", "").lower()
        if risk_level in ("critical", "high"):
            score += 2
        elif risk_level == "medium":
            score += 1

        # Security-specific escalation
        lesson_type = context.get("lesson_type", "")
        if lesson_type == LessonType.SECURITY_ISSUE:
            score += 1

        # Production / deployment signals
        searchable = f"{context.get('task_description', '')} {context.get('description', '')}".lower()
        production_keywords = ["production", "deploy", "live", "release"]
        if any(kw in searchable for kw in production_keywords):
            score += 1

        # Map score to severity
        if score >= 6:
            return Severity.CRITICAL.value
        elif score >= 4:
            return Severity.HIGH.value
        elif score >= 2:
            return Severity.MEDIUM.value
        else:
            return Severity.LOW.value

    async def _extract_lesson_title(self, context: dict[str, Any]) -> str:
        """Generate a concise, descriptive title for the lesson.

        Uses existing title context, task descriptions, or error categories
        to produce a meaningful lesson title.

        Args:
            context: The built context dictionary.

        Returns:
            Title string (max 200 characters).
        """
        existing_title = context.get("title", "")
        if isinstance(existing_title, str) and existing_title.strip():
            cleaned = existing_title.strip()
            if len(cleaned) <= 200:
                return cleaned
            return cleaned[:197] + "..."

        lesson_type = context.get("lesson_type", "failure")
        task_desc = context.get("task_description", "")

        if isinstance(task_desc, str) and task_desc.strip():
            first_sentence = task_desc.split(".")[0].strip()
            if len(first_sentence) <= 160:
                return f"{lesson_type.replace('_', ' ').title()}: {first_sentence}"
            return (
                f"{lesson_type.replace('_', ' ').title()}: "
                + first_sentence[:157]
                + "..."
            )

        error_type = context.get("error_type", "")
        if isinstance(error_type, str) and error_type.strip():
            return (
                f"{lesson_type.replace('_', ' ').title()} in "
                + error_type.strip()[:140]
            )

        return f"{lesson_type.replace('_', ' ').title()} lesson"

    async def _find_similar_failures(
        self, lesson: dict[str, Any], existing: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find related failures from existing lesson records.

        Matches against lesson type, root cause keywords, technologies,
        and tags to identify semantically similar past failures.

        Args:
            lesson: The new lesson dictionary.
            existing: List of existing lesson dictionaries.

        Returns:
            List of related lesson dictionaries, ordered by relevance.
        """
        if not existing:
            return []

        lesson_type = lesson.get("lesson_type", "")
        root_cause = lesson.get("root_cause", "").lower()
        technologies = set(lesson.get("technologies", []))
        tags = set(lesson.get("tags", []))

        scored: list[tuple[dict[str, Any], float]] = []

        for other in existing:
            score = 0.0

            # Same lesson type is a strong signal
            if other.get("lesson_type") == lesson_type:
                score += 0.4

            # Root cause keyword overlap
            other_root = other.get("root_cause", "").lower()
            if root_cause and other_root:
                root_tokens = set(root_cause.split())
                other_tokens = set(other_root.split())
                if root_tokens and other_tokens:
                    overlap = len(root_tokens & other_tokens)
                    total = len(root_tokens | other_tokens)
                    if total > 0:
                        score += 0.3 * (overlap / total)

            # Technology overlap
            other_techs = set(other.get("technologies", []))
            if technologies and other_techs:
                tech_overlap = len(technologies & other_techs)
                tech_total = len(technologies | other_techs)
                if tech_total > 0:
                    score += 0.2 * (tech_overlap / tech_total)

            # Tag overlap
            other_tags = set(other.get("tags", []))
            if tags and other_tags:
                tag_overlap = len(tags & other_tags)
                tag_total = len(tags | other_tags)
                if tag_total > 0:
                    score += 0.1 * (tag_overlap / tag_total)

            if score >= 0.2:
                scored.append((other, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, _ in scored[:10]]

    async def _update_encounter_count(
        self, lesson: dict[str, Any], existing: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Track repeated failures by updating encounter counts.

        If a matching lesson exists, increments its encounter count
        and refreshes the timestamp. Otherwise returns the lesson as-is.

        Args:
            lesson: The new lesson dictionary.
            existing: List of existing lesson dictionaries.

        Returns:
            Updated lesson dictionary with encounter count set.
        """
        similar = await self._find_similar_failures(lesson, existing)

        if similar:
            most_similar = similar[0]
            existing_count = most_similar.get("times_encountered", 1)
            updated_lesson = dict(lesson)
            updated_lesson["times_encountered"] = existing_count + 1
            updated_lesson["encountered_at"] = datetime.now(UTC).isoformat()

            # Bump severity when failures repeat
            current_severity = updated_lesson.get("severity", Severity.MEDIUM.value)
            if existing_count >= 5 and current_severity != Severity.CRITICAL.value:
                updated_lesson["severity"] = Severity.HIGH.value
            elif existing_count >= 10:
                updated_lesson["severity"] = Severity.CRITICAL.value

            # Increase confidence when pattern repeats
            current_confidence = updated_lesson.get("confidence", 0.5)
            updated_lesson["confidence"] = min(
                1.0, current_confidence + 0.05 * min(existing_count, 5)
            )

            logger.info(
                "Encounter count updated",
                extra={
                    "previous_count": existing_count,
                    "new_count": updated_lesson["times_encountered"],
                },
            )

            return updated_lesson

        lesson["times_encountered"] = 1
        lesson["encountered_at"] = datetime.now(UTC).isoformat()
        return lesson

    # ------------------------------------------------------------------
    # Context builders
    # ------------------------------------------------------------------

    def _build_failure_context(
        self, workflow_data: dict[str, Any], error_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Build context from workflow and error data."""
        return {
            "lesson_type": LessonType.FAILURE.value,
            "source": "workflow",
            "workflow_id": workflow_data.get("id"),
            "repository_id": workflow_data.get("repository_id"),
            "task_type": workflow_data.get("task_type", ""),
            "task_description": (
                workflow_data.get("description")
                or workflow_data.get("task_description", "")
            ),
            "agent_type": workflow_data.get("agent_type", ""),
            "risk_level": workflow_data.get("risk_level", "medium"),
            "error_type": (
                error_data.get("type")
                or error_data.get("error_type", "")
            ),
            "error_message": (
                error_data.get("message")
                or error_data.get("error_message", "")
            ),
            "traceback": (
                error_data.get("traceback")
                or error_data.get("stack_trace", "")
            ),
            "files_changed": self._extract_files(workflow_data),
            "technologies": workflow_data.get("technologies", []),
            "tasks_total": workflow_data.get("tasks_total", 0),
            "tasks_completed": workflow_data.get("tasks_completed", 0),
            "steps": workflow_data.get("steps", []),
            "title": workflow_data.get("title", ""),
            "description": workflow_data.get("description", ""),
        }

    def _build_rejection_context(
        self, review_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Build context from review data."""
        return {
            "lesson_type": LessonType.REJECTION.value,
            "source": "code_review",
            "review_id": review_data.get("id"),
            "workflow_id": review_data.get("workflow_id"),
            "repository_id": review_data.get("repository_id"),
            "task_type": review_data.get("task_type", ""),
            "task_description": review_data.get("description", ""),
            "reviewer": review_data.get("reviewer", ""),
            "review_comments": review_data.get("comments", []),
            "rejection_reasons": review_data.get("rejection_reasons", []),
            "change_request": review_data.get("change_request", ""),
            "files_changed": self._extract_files(review_data),
            "technologies": review_data.get("technologies", []),
            "title": review_data.get("title", ""),
            "description": review_data.get("description", ""),
            "risk_level": review_data.get("risk_level", "medium"),
        }

    def _build_security_context(
        self, security_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Build context from security issue data."""
        return {
            "lesson_type": LessonType.SECURITY_ISSUE.value,
            "source": "security_scan",
            "issue_id": security_data.get("id"),
            "workflow_id": security_data.get("workflow_id"),
            "repository_id": security_data.get("repository_id"),
            "vulnerability_type": security_data.get(
                "vulnerability_type", ""
            ),
            "cve_id": security_data.get("cve_id", ""),
            "cvss_score": security_data.get("cvss_score", 0),
            "affected_files": security_data.get("affected_files", []),
            "task_description": security_data.get("description", ""),
            "files_changed": security_data.get(
                "affected_files", self._extract_files(security_data)
            ),
            "technologies": security_data.get("technologies", []),
            "remediation": security_data.get("remediation", ""),
            "title": security_data.get("title", ""),
            "description": security_data.get("description", ""),
            "risk_level": security_data.get("severity", "high"),
        }

    def _build_performance_context(
        self, perf_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Build context from performance issue data."""
        return {
            "lesson_type": LessonType.PERFORMANCE_ISSUE.value,
            "source": "performance_monitoring",
            "issue_id": perf_data.get("id"),
            "workflow_id": perf_data.get("workflow_id"),
            "repository_id": perf_data.get("repository_id"),
            "metric_name": perf_data.get("metric_name", ""),
            "baseline_value": perf_data.get("baseline_value"),
            "regressed_value": perf_data.get("regressed_value"),
            "regression_percent": perf_data.get("regression_percent", 0),
            "affected_endpoint": perf_data.get("affected_endpoint", ""),
            "task_description": perf_data.get("description", ""),
            "files_changed": self._extract_files(perf_data),
            "technologies": perf_data.get("technologies", []),
            "title": perf_data.get("title", ""),
            "description": perf_data.get("description", ""),
            "risk_level": perf_data.get("risk_level", "medium"),
        }

    def _build_architecture_context(
        self, violation_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Build context from architecture violation data."""
        return {
            "lesson_type": LessonType.ARCHITECTURE_VIOLATION.value,
            "source": "architecture_review",
            "violation_id": violation_data.get("id"),
            "workflow_id": violation_data.get("workflow_id"),
            "repository_id": violation_data.get("repository_id"),
            "rule_name": violation_data.get("rule_name", ""),
            "rule_description": violation_data.get("rule_description", ""),
            "source_module": violation_data.get("source_module", ""),
            "target_module": violation_data.get("target_module", ""),
            "dependency_type": violation_data.get("dependency_type", ""),
            "task_description": violation_data.get("description", ""),
            "files_changed": self._extract_files(violation_data),
            "technologies": violation_data.get("technologies", []),
            "title": violation_data.get("title", ""),
            "description": violation_data.get("description", ""),
            "risk_level": violation_data.get("risk_level", "medium"),
        }

    def _build_testing_context(
        self, test_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Build context from test failure data."""
        return {
            "lesson_type": LessonType.TESTING_FAILURE.value,
            "source": "test_execution",
            "test_id": test_data.get("id"),
            "workflow_id": test_data.get("workflow_id"),
            "repository_id": test_data.get("repository_id"),
            "test_name": test_data.get("test_name", ""),
            "test_file": test_data.get("test_file", ""),
            "test_type": test_data.get("test_type", ""),
            "failure_message": test_data.get("failure_message", ""),
            "expected": test_data.get("expected"),
            "actual": test_data.get("actual"),
            "is_flaky": test_data.get("is_flaky", False),
            "task_description": test_data.get("description", ""),
            "files_changed": self._extract_files(test_data),
            "technologies": test_data.get("technologies", []),
            "title": test_data.get("title", ""),
            "description": test_data.get("description", ""),
            "risk_level": test_data.get("risk_level", "low"),
        }

    # ------------------------------------------------------------------
    # Description builders
    # ------------------------------------------------------------------

    def _build_failure_description(
        self, context: dict[str, Any], error_data: dict[str, Any]
    ) -> str:
        """Build a description for a workflow failure lesson."""
        parts: list[str] = []

        task_desc = context.get("task_description", "")
        if isinstance(task_desc, str) and task_desc.strip():
            parts.append(f"Workflow task failed: {task_desc.strip()}.")

        error_type = context.get("error_type", "")
        error_message = context.get("error_message", "")
        if error_type:
            parts.append(f"Error type: {error_type}.")
        if error_message:
            parts.append(f"Error: {error_message.strip()[:300]}.")

        files = context.get("files_changed", [])
        if isinstance(files, list) and files:
            parts.append(f"Affected {len(files)} file(s).")

        return " ".join(parts) if parts else "Workflow failure analyzed."

    def _build_rejection_description(
        self, context: dict[str, Any], review_data: dict[str, Any]
    ) -> str:
        """Build a description for a rejection lesson."""
        parts: list[str] = []

        reviewer = context.get("reviewer", "")
        if reviewer:
            parts.append(f"Code review rejected by {reviewer}.")

        reasons = context.get("rejection_reasons", [])
        if isinstance(reasons, list) and reasons:
            reason_text = "; ".join(str(r) for r in reasons[:5])
            parts.append(f"Rejection reasons: {reason_text}.")

        change_request = context.get("change_request", "")
        if isinstance(change_request, str) and change_request.strip():
            parts.append(f"Requested changes: {change_request.strip()[:300]}.")

        comments = context.get("review_comments", [])
        if isinstance(comments, list) and comments:
            parts.append(f"Review contained {len(comments)} comment(s).")

        return " ".join(parts) if parts else "Code review rejection analyzed."

    def _build_security_description(
        self, context: dict[str, Any], security_data: dict[str, Any]
    ) -> str:
        """Build a description for a security issue lesson."""
        parts: list[str] = []

        vuln_type = context.get("vulnerability_type", "")
        if vuln_type:
            parts.append(f"Security vulnerability: {vuln_type}.")

        cve = context.get("cve_id", "")
        if cve:
            parts.append(f"CVE: {cve}.")

        cvss = context.get("cvss_score", 0)
        if isinstance(cvss, (int, float)) and cvss > 0:
            parts.append(f"CVSS score: {cvss}.")

        remediation = context.get("remediation", "")
        if isinstance(remediation, str) and remediation.strip():
            parts.append(f"Remediation: {remediation.strip()[:300]}.")

        return " ".join(parts) if parts else "Security issue analyzed."

    def _build_performance_description(
        self, context: dict[str, Any], perf_data: dict[str, Any]
    ) -> str:
        """Build a description for a performance issue lesson."""
        parts: list[str] = []

        metric = context.get("metric_name", "")
        baseline = context.get("baseline_value")
        regressed = context.get("regressed_value")
        if metric and baseline is not None and regressed is not None:
            parts.append(
                f"Performance regression in {metric}: "
                f"{baseline} -> {regressed}."
            )

        regression_pct = context.get("regression_percent", 0)
        if isinstance(regression_pct, (int, float)) and regression_pct > 0:
            parts.append(f"Regression: {regression_pct}%.")

        endpoint = context.get("affected_endpoint", "")
        if endpoint:
            parts.append(f"Affected endpoint: {endpoint}.")

        return " ".join(parts) if parts else "Performance regression analyzed."

    def _build_architecture_description(
        self, context: dict[str, Any], violation_data: dict[str, Any]
    ) -> str:
        """Build a description for an architecture violation lesson."""
        parts: list[str] = []

        rule = context.get("rule_name", "")
        if rule:
            parts.append(f"Architecture rule violated: {rule}.")

        source = context.get("source_module", "")
        target = context.get("target_module", "")
        if source and target:
            parts.append(f"Illegal dependency: {source} -> {target}.")

        dep_type = context.get("dependency_type", "")
        if dep_type:
            parts.append(f"Dependency type: {dep_type}.")

        rule_desc = context.get("rule_description", "")
        if isinstance(rule_desc, str) and rule_desc.strip():
            parts.append(f"Rule: {rule_desc.strip()[:300]}.")

        return (
            " ".join(parts)
            if parts
            else "Architecture violation analyzed."
        )

    def _build_testing_description(
        self, context: dict[str, Any], test_data: dict[str, Any]
    ) -> str:
        """Build a description for a testing failure lesson."""
        parts: list[str] = []

        test_name = context.get("test_name", "")
        if test_name:
            parts.append(f"Test failed: {test_name}.")

        test_type = context.get("test_type", "")
        if test_type:
            parts.append(f"Test type: {test_type}.")

        failure_msg = context.get("failure_message", "")
        if isinstance(failure_msg, str) and failure_msg.strip():
            parts.append(f"Failure: {failure_msg.strip()[:300]}.")

        expected = context.get("expected")
        actual = context.get("actual")
        if expected is not None and actual is not None:
            parts.append(f"Expected {expected}, got {actual}.")

        is_flaky = context.get("is_flaky", False)
        if is_flaky:
            parts.append("This test is marked as flaky.")

        test_file = context.get("test_file", "")
        if test_file:
            parts.append(f"Test file: {test_file}.")

        return " ".join(parts) if parts else "Test failure analyzed."

    # ------------------------------------------------------------------
    # Technology and tag extraction
    # ------------------------------------------------------------------

    _TECH_KEYWORDS: list[str] = field(default_factory=lambda: [
        "python", "javascript", "typescript", "rust", "go", "java", "c++", "ruby",
        "react", "vue", "angular", "svelte", "nextjs", "nuxt", "astro",
        "fastapi", "django", "flask", "express", "spring", "rails", "actix",
        "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch",
        "docker", "kubernetes", "terraform", "ansible", "aws", "gcp", "azure",
        "nginx", "apache", "graphql", "rest", "grpc", "websocket",
        "pytest", "jest", "mocha", "cypress", "playwright",
        "git", "github", "gitlab", "bitbucket",
        "tailwind", "css", "html", "sass", "webpack", "vite", "esbuild",
        "celery", "rabbitmq", "kafka",
        "pydantic", "sqlalchemy", "alembic",
    ])

    _EXT_TECH_MAP: dict[str, str] = field(default_factory=lambda: {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
        ".css": "css",
        ".scss": "scss",
        ".html": "html",
        ".vue": "vue",
        ".astro": "astro",
        ".sql": "sql",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".dockerfile": "docker",
        ".tf": "terraform",
        ".sh": "bash",
    })

    def _extract_technologies(self, context: dict[str, Any]) -> list[str]:
        """Extract technology stack from context."""
        found: set[str] = set()

        # From file extensions
        for f in context.get("files_changed", []):
            ext = "." + f.rsplit(".", 1)[-1].lower() if "." in f else ""
            if ext in self._EXT_TECH_MAP:
                found.add(self._EXT_TECH_MAP[ext])

        # From keyword scan across descriptive fields
        searchable = " ".join([
            context.get("task_description", ""),
            context.get("description", ""),
            context.get("title", ""),
            context.get("error_message", ""),
            context.get("failure_message", ""),
        ]).lower()

        for tech in self._TECH_KEYWORDS:
            if tech in searchable:
                found.add(tech)

        # From explicit technologies list in context
        for tech in context.get("technologies", []):
            if isinstance(tech, str) and tech.strip():
                found.add(tech.strip().lower())

        return sorted(found)

    def _extract_tags(
        self, context: dict[str, Any], lesson_type: LessonType
    ) -> list[str]:
        """Extract relevant tags for filtering and retrieval."""
        tags: set[str] = set()

        # Lesson type tag
        tags.add(f"lesson:{lesson_type.value}")

        # Source tag
        source = context.get("source", "")
        if source:
            tags.add(f"source:{source}")

        # Risk level tag
        risk_level = context.get("risk_level", "")
        if risk_level:
            tags.add(f"risk:{risk_level}")

        # Technology tags (first 5)
        technologies = context.get("technologies", [])
        if isinstance(technologies, list):
            for tech in technologies[:5]:
                if isinstance(tech, str) and tech.strip():
                    tags.add(f"tech:{tech.strip().lower()}")

        # Repository tag
        repo_id = context.get("repository_id", "")
        if repo_id:
            tags.add(f"repo:{repo_id}")

        # Agent type tag
        agent_type = context.get("agent_type", "")
        if agent_type:
            tags.add(f"agent:{agent_type}")

        # Workflow tag
        workflow_id = context.get("workflow_id", "")
        if workflow_id:
            tags.add(f"workflow:{workflow_id}")

        return sorted(tags)

    # ------------------------------------------------------------------
    # Confidence calculators
    # ------------------------------------------------------------------

    def _calculate_failure_confidence(
        self, context: dict[str, Any], error_data: dict[str, Any]
    ) -> float:
        """Calculate confidence for a failure analysis."""
        score = 0.5

        # Error message clarity
        error_message = (
            error_data.get("message", "")
            or error_data.get("error_message", "")
        )
        if isinstance(error_message, str) and len(error_message) > 20:
            score += 0.1

        # Error type present
        error_type = (
            error_data.get("type", "")
            or error_data.get("error_type", "")
        )
        if isinstance(error_type, str) and error_type.strip():
            score += 0.1

        # Traceback present
        traceback = (
            error_data.get("traceback", "")
            or error_data.get("stack_trace", "")
        )
        if isinstance(traceback, str) and len(traceback) > 50:
            score += 0.1

        # Files changed context
        files = context.get("files_changed", [])
        if isinstance(files, list) and files:
            score += 0.05

        # Step completion ratio
        tasks_total = context.get("tasks_total", 0)
        tasks_completed = context.get("tasks_completed", 0)
        if isinstance(tasks_total, (int, float)) and tasks_total > 0:
            completion_ratio = tasks_completed / tasks_total
            if completion_ratio > 0:
                score += 0.1

        return max(0.0, min(1.0, score))

    def _calculate_rejection_confidence(
        self, review_data: dict[str, Any]
    ) -> float:
        """Calculate confidence for a rejection analysis."""
        score = 0.5

        reviewer = review_data.get("reviewer", "")
        if isinstance(reviewer, str) and reviewer.strip():
            score += 0.1

        comments = review_data.get("comments", [])
        if isinstance(comments, list) and len(comments) > 0:
            score += min(0.2, len(comments) * 0.04)

        reasons = review_data.get("rejection_reasons", [])
        if isinstance(reasons, list) and len(reasons) > 0:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _calculate_security_confidence(
        self, security_data: dict[str, Any]
    ) -> float:
        """Calculate confidence for a security analysis."""
        score = 0.6

        cve = security_data.get("cve_id", "")
        if isinstance(cve, str) and cve.strip():
            score += 0.15

        cvss = security_data.get("cvss_score", 0)
        if isinstance(cvss, (int, float)) and cvss > 0:
            score += 0.1

        vuln_type = security_data.get("vulnerability_type", "")
        if isinstance(vuln_type, str) and vuln_type.strip():
            score += 0.05

        return max(0.0, min(1.0, score))

    def _calculate_performance_confidence(
        self, perf_data: dict[str, Any]
    ) -> float:
        """Calculate confidence for a performance analysis."""
        score = 0.5

        baseline = perf_data.get("baseline_value")
        regressed = perf_data.get("regressed_value")
        if baseline is not None and regressed is not None:
            score += 0.15

        regression_pct = perf_data.get("regression_percent", 0)
        if isinstance(regression_pct, (int, float)) and regression_pct > 0:
            score += 0.1

        metric_name = perf_data.get("metric_name", "")
        if isinstance(metric_name, str) and metric_name.strip():
            score += 0.05

        return max(0.0, min(1.0, score))

    def _calculate_architecture_confidence(
        self, violation_data: dict[str, Any]
    ) -> float:
        """Calculate confidence for an architecture analysis."""
        score = 0.5

        rule = violation_data.get("rule_name", "")
        if isinstance(rule, str) and rule.strip():
            score += 0.15

        source = violation_data.get("source_module", "")
        target = violation_data.get("target_module", "")
        if isinstance(source, str) and source.strip():
            score += 0.05
        if isinstance(target, str) and target.strip():
            score += 0.05

        return max(0.0, min(1.0, score))

    def _calculate_testing_confidence(
        self, test_data: dict[str, Any]
    ) -> float:
        """Calculate confidence for a testing analysis."""
        score = 0.5

        test_name = test_data.get("test_name", "")
        if isinstance(test_name, str) and test_name.strip():
            score += 0.1

        failure_msg = test_data.get("failure_message", "")
        if isinstance(failure_msg, str) and len(failure_msg) > 10:
            score += 0.1

        expected = test_data.get("expected")
        actual = test_data.get("actual")
        if expected is not None and actual is not None:
            score += 0.1

        test_file = test_data.get("test_file", "")
        if isinstance(test_file, str) and test_file.strip():
            score += 0.05

        return max(0.0, min(1.0, score))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_files(self, data: dict[str, Any]) -> list[str]:
        """Extract file paths from various data shapes."""
        files: set[str] = set()

        fc = data.get("files_changed", [])
        if isinstance(fc, list):
            for f in fc:
                if isinstance(f, str):
                    files.add(f)
                elif isinstance(f, dict):
                    path = f.get("path") or f.get("file_path") or f.get("filename", "")
                    if path:
                        files.add(path)

        for task in data.get("tasks", []):
            if not isinstance(task, dict):
                continue
            result = task.get("result") or task.get("execution_result") or {}
            if isinstance(result, dict):
                for f in result.get("files_changed", []):
                    if isinstance(f, str):
                        files.add(f)
                    elif isinstance(f, dict):
                        path = f.get("path") or f.get("file_path", "")
                        if path:
                            files.add(path)

        for step in data.get("steps", []):
            if not isinstance(step, dict):
                continue
            result = step.get("result") or {}
            if isinstance(result, dict):
                for f in result.get("files_changed", []):
                    if isinstance(f, str):
                        files.add(f)
                    elif isinstance(f, dict):
                        path = f.get("path") or f.get("file_path", "")
                        if path:
                            files.add(path)

        return sorted(files)

    def _format_root_cause(
        self, category: str, context: dict[str, Any], error: dict[str, Any]
    ) -> str:
        """Format a root cause description from a matched category."""
        readable = category.replace("_", " ").title()

        error_message = (
            error.get("message", "")
            or error.get("error_message", "")
        )
        if isinstance(error_message, str) and error_message.strip():
            short_msg = error_message.strip()[:200]
            return f"{readable}: {short_msg}"

        error_type = error.get("type", "") or error.get("error_type", "")
        if isinstance(error_type, str) and error_type.strip():
            return f"{readable}: {error_type.strip()}"

        return f"{readable} error detected"

    def _derive_root_cause_from_context(
        self, context: dict[str, Any], error: dict[str, Any]
    ) -> str:
        """Derive a root cause when no category match is found."""
        # Try from error message directly
        error_message = (
            error.get("message", "")
            or error.get("error_message", "")
            or error.get("summary", "")
        )
        if isinstance(error_message, str) and error_message.strip():
            return f"Unclassified error: {error_message.strip()[:200]}"

        # Try from task description
        task_desc = context.get("task_description", "")
        if isinstance(task_desc, str) and task_desc.strip():
            return f"Task execution failed: {task_desc.strip()[:200]}"

        lesson_type = context.get("lesson_type", "failure")
        return f"Unknown root cause for {lesson_type}"

    def _add_context_to_strategy(
        self, base_strategy: str, context: dict[str, Any]
    ) -> str:
        """Augment a strategy template with context-specific details."""
        additions: list[str] = []

        technologies = context.get("technologies", [])
        if isinstance(technologies, list) and technologies:
            tech_list = ", ".join(str(t) for t in technologies[:5])
            additions.append(f"Relevant technologies: {tech_list}.")

        lesson_type = context.get("lesson_type", "")
        if lesson_type == LessonType.SECURITY_ISSUE.value:
            additions.append(
                "Run a security audit to identify similar vulnerabilities."
            )
        elif lesson_type == LessonType.PERFORMANCE_ISSUE.value:
            additions.append(
                "Add performance benchmarks to CI to catch future regressions."
            )
        elif lesson_type == LessonType.ARCHITECTURE_VIOLATION.value:
            additions.append(
                "Document the architectural boundary and enforce it "
                "with linting or module-level import restrictions."
            )
        elif lesson_type == LessonType.TESTING_FAILURE.value:
            additions.append(
                "Add regression tests to validate the fix and prevent recurrence."
            )

        if additions:
            return f"{base_strategy} {' '.join(additions)}"
        return base_strategy

    def _build_generic_avoidance_strategy(
        self, context: dict[str, Any]
    ) -> str:
        """Build a generic avoidance strategy with context hints."""
        lesson_type = context.get("lesson_type", "failure")

        base = (
            "Investigate the underlying issue thoroughly. Add validation "
            "and error handling at the failure point. Write tests to "
            "prevent recurrence. Document the failure mode and resolution "
            "for future reference."
        )

        files = context.get("files_changed", [])
        if isinstance(files, list) and len(files) > 5:
            base += (
                " Consider whether the scope of change was appropriate "
                "and if a more incremental approach would be safer."
            )

        return base

    def _is_security_critical(self, security_data: dict[str, Any]) -> bool:
        """Check if a security issue warrants high/critical severity."""
        cvss = security_data.get("cvss_score", 0)
        if isinstance(cvss, (int, float)) and cvss >= 7.0:
            return True

        vuln_type = (
            security_data.get("vulnerability_type", "")
        ).lower()
        critical_types = [
            "rce", "remote code execution", "sql injection",
            "authentication bypass", "privilege escalation",
            "arbitrary file read", "deserialization",
        ]
        return any(ct in vuln_type for ct in critical_types)
