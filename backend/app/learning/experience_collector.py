"""Experience Collector for the Learning Engine.

Processes workflow execution data, QA results, reflection summaries,
and human feedback into structured experience records for long-term learning.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class ExperienceType(str, Enum):
    """Classification of engineering experiences."""

    ARCHITECTURE = "architecture"
    BUG_FIX = "bug_fix"
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    TESTING = "testing"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    FEATURE = "feature"
    CONFIGURATION = "configuration"
    INTEGRATION = "integration"


class Outcome(str, Enum):
    """Outcome of an experience."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class SourceType(str, Enum):
    """Origin of an experience record."""

    WORKFLOW = "workflow"
    EXECUTION = "execution"
    REFLECTION = "reflection"
    QA = "qa"
    FEEDBACK = "feedback"


class ExperienceData(BaseModel):
    """Structured experience record extracted from a completed workflow or operation.

    Attributes:
        experience_type: Classification of the engineering experience.
        title: Short human-readable title.
        description: Detailed description of the experience.
        context: Situational context including repo, branch, task info.
        outcome: Whether the operation succeeded, failed, or was partial.
        solution: Description of the solution or approach taken.
        files_changed: List of file paths that were modified.
        technologies: Technologies involved in this experience.
        tags: Arbitrary tags for filtering and retrieval.
        confidence: Confidence score for this experience (0.0-1.0).
        reuse_potential: How reusable this knowledge is (0.0-1.0).
        complexity: Complexity of the task (0.0-1.0).
        generalization_score: How generalizable this experience is (0.0-1.0).
        source: Origin of the experience record.
        source_id: Identifier of the source entity.
        metadata: Additional arbitrary metadata.
    """

    experience_type: ExperienceType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    outcome: Outcome = Outcome.SUCCESS
    solution: str = ""
    files_changed: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reuse_potential: float = Field(default=0.5, ge=0.0, le=1.0)
    complexity: float = Field(default=0.5, ge=0.0, le=1.0)
    generalization_score: float = Field(default=0.5, ge=0.0, le=1.0)
    source: SourceType = SourceType.WORKFLOW
    source_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@dataclass
class ExperienceCollector:
    """Collects and structures experiences from completed workflows.

    Processes execution data, QA results, reflection summaries, and human
    feedback into structured ExperienceData records suitable for storage
    in the long-term learning system.
    """

    # Known technology keywords for extraction
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
        "celery", "rabbitmq", "kafka", "grpc",
        "pydantic", "sqlalchemy", "alembic", "fastapi",
    ])

    # File extension to technology mapping
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

    async def collect_from_workflow(self, workflow_data: dict[str, Any]) -> ExperienceData:
        """Collect experience data from a completed workflow definition.

        Args:
            workflow_data: Dictionary containing workflow definition, tasks,
                execution results, and metadata.

        Returns:
            Structured ExperienceData record.
        """
        logger.info("Collecting experience from workflow: %s", workflow_data.get("id", "unknown"))

        context = self._build_context(workflow_data, SourceType.WORKFLOW)
        outcome = self._determine_outcome(workflow_data)
        files = self._extract_files(workflow_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context)

        title = self._generate_title(workflow_data)
        description = self._generate_description(workflow_data)
        solution = self._extract_solution(workflow_data)

        experience_type = self._determine_experience_type(context)

        return ExperienceData(
            experience_type=experience_type,
            title=title,
            description=description,
            context=context,
            outcome=outcome,
            solution=solution,
            files_changed=files,
            technologies=technologies,
            tags=tags,
            confidence=self._calculate_confidence(outcome, context),
            reuse_potential=self._calculate_reuse_potential(context),
            complexity=self._calculate_complexity(context),
            generalization_score=self._calculate_generalization(context),
            source=SourceType.WORKFLOW,
            source_id=workflow_data.get("id"),
            metadata=self._extract_metadata(workflow_data),
        )

    async def collect_from_execution(self, execution_data: dict[str, Any]) -> ExperienceData:
        """Collect experience from execution results.

        Args:
            execution_data: Dictionary containing execution results, steps,
                logs, file changes, and timing information.

        Returns:
            Structured ExperienceData record.
        """
        logger.info("Collecting experience from execution: %s", execution_data.get("id", "unknown"))

        context = self._build_context(execution_data, SourceType.EXECUTION)
        outcome = self._determine_outcome(execution_data)
        files = self._extract_files(execution_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context)

        title = self._generate_title(execution_data)
        description = self._generate_execution_description(execution_data)
        solution = self._extract_solution(execution_data)

        experience_type = self._determine_experience_type(context)

        return ExperienceData(
            experience_type=experience_type,
            title=title,
            description=description,
            context=context,
            outcome=outcome,
            solution=solution,
            files_changed=files,
            technologies=technologies,
            tags=tags,
            confidence=self._calculate_confidence(outcome, context),
            reuse_potential=self._calculate_reuse_potential(context),
            complexity=self._calculate_complexity(context),
            generalization_score=self._calculate_generalization(context),
            source=SourceType.EXECUTION,
            source_id=execution_data.get("id"),
            metadata=self._extract_metadata(execution_data),
        )

    async def collect_from_reflection(self, reflection_data: dict[str, Any]) -> ExperienceData:
        """Collect experience from a reflection summary.

        Args:
            reflection_data: Dictionary containing reflection analysis,
                lessons learned, patterns identified, and recommendations.

        Returns:
            Structured ExperienceData record.
        """
        logger.info("Collecting experience from reflection: %s", reflection_data.get("id", "unknown"))

        context = self._build_context(reflection_data, SourceType.REFLECTION)
        outcome = self._determine_outcome(reflection_data)
        files = self._extract_files(reflection_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context)

        title = self._generate_title(reflection_data)
        description = self._generate_reflection_description(reflection_data)
        solution = self._extract_solution(reflection_data)

        experience_type = self._determine_experience_type(context)

        return ExperienceData(
            experience_type=experience_type,
            title=title,
            description=description,
            context=context,
            outcome=outcome,
            solution=solution,
            files_changed=files,
            technologies=technologies,
            tags=tags,
            confidence=self._calculate_confidence(outcome, context),
            reuse_potential=self._calculate_reuse_potential(context),
            complexity=self._calculate_complexity(context),
            generalization_score=self._calculate_generalization(context),
            source=SourceType.REFLECTION,
            source_id=reflection_data.get("id"),
            metadata=self._extract_metadata(reflection_data),
        )

    async def collect_from_qa(self, qa_data: dict[str, Any]) -> ExperienceData:
        """Collect experience from QA results.

        Args:
            qa_data: Dictionary containing QA validation results, test
                outcomes, review feedback, and quality metrics.

        Returns:
            Structured ExperienceData record.
        """
        logger.info("Collecting experience from QA: %s", qa_data.get("id", "unknown"))

        context = self._build_context(qa_data, SourceType.QA)
        outcome = self._determine_outcome(qa_data)
        files = self._extract_files(qa_data)
        technologies = self._extract_technologies(context)
        tags = self._extract_tags(context)

        title = self._generate_title(qa_data)
        description = self._generate_qa_description(qa_data)
        solution = self._extract_solution(qa_data)

        experience_type = self._determine_experience_type(context)

        # QA results can refine confidence based on validation outcomes
        base_confidence = self._calculate_confidence(outcome, context)
        qa_boost = self._calculate_qa_confidence_boost(qa_data)

        return ExperienceData(
            experience_type=experience_type,
            title=title,
            description=description,
            context=context,
            outcome=outcome,
            solution=solution,
            files_changed=files,
            technologies=technologies,
            tags=tags,
            confidence=min(1.0, base_confidence + qa_boost),
            reuse_potential=self._calculate_reuse_potential(context),
            complexity=self._calculate_complexity(context),
            generalization_score=self._calculate_generalization(context),
            source=SourceType.QA,
            source_id=qa_data.get("id"),
            metadata=self._extract_metadata(qa_data),
        )

    # -------------------------------------------------------------------------
    # Classification and extraction helpers
    # -------------------------------------------------------------------------

    def _determine_experience_type(self, context: dict[str, Any]) -> ExperienceType:
        """Classify the experience type based on context.

        Analyses task descriptions, file changes, keywords, and agent types
        to determine the most appropriate experience classification.

        Args:
            context: The built context dictionary.

        Returns:
            The classified ExperienceType.
        """
        task_desc = context.get("task_description", "").lower()
        agent_type = context.get("agent_type", "").lower()
        task_type = context.get("task_type", "").lower()
        files = context.get("files_changed", [])

        # Check agent type first (strongest signal)
        agent_type_map: dict[str, ExperienceType] = {
            "reviewer": ExperienceType.SECURITY,
            "planner": ExperienceType.ARCHITECTURE,
            "researcher": ExperienceType.DOCUMENTATION,
            "executor": ExperienceType.FEATURE,
        }
        if agent_type in agent_type_map:
            return agent_type_map[agent_type]

        # Keyword-based classification from task description and type
        classification_keywords: dict[ExperienceType, list[str]] = {
            ExperienceType.BUG_FIX: [
                "bug", "fix", "error", "issue", "broken", "crash", "exception",
                "defect", "patch", "hotfix", "regression",
            ],
            ExperienceType.ARCHITECTURE: [
                "architecture", "design", "structure", "pattern", "refactor",
                "system", "module", "component", "service", "layout",
            ],
            ExperienceType.DEPLOYMENT: [
                "deploy", "release", "ci", "cd", "pipeline", "release",
                "rollback", "infrastructure", "provision", "migrate",
            ],
            ExperienceType.DATABASE: [
                "database", "migration", "schema", "query", "sql", "index",
                "table", "column", "seed", "backfill", "partition",
            ],
            ExperienceType.TESTING: [
                "test", "spec", "coverage", "assert", "mock", "fixture",
                "integration test", "unit test", "e2e", "coverage",
            ],
            ExperienceType.PERFORMANCE: [
                "performance", "optimize", "speed", "latency", "cache",
                "memory", "cpu", "benchmark", "profiling", "throughput",
            ],
            ExperienceType.SECURITY: [
                "security", "vulnerability", "cve", "auth", "encrypt",
                "token", "permission", "rbac", "audit", "sanitize",
            ],
            ExperienceType.DOCUMENTATION: [
                "doc", "readme", "comment", "guide", "tutorial", "changelog",
                "api doc", "javadoc", "sphinx",
            ],
            ExperienceType.REFACTORING: [
                "refactor", "cleanup", "restructure", "reorganize", "simplify",
                "extract", "rename", "move", "consolidate",
            ],
            ExperienceType.FEATURE: [
                "feature", "add", "implement", "create", "new", "introduce",
                "support", "enable", "build",
            ],
            ExperienceType.CONFIGURATION: [
                "config", "setting", "env", "environment", "variable",
                "option", "parameter", "preference",
            ],
            ExperienceType.INTEGRATION: [
                "integration", "api", "webhook", "connector", "plugin",
                "external", "third-party", "third party", "sdk",
            ],
        }

        combined_text = f"{task_desc} {task_type}"
        scores: dict[ExperienceType, int] = {}
        for exp_type, keywords in classification_keywords.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            if score > 0:
                scores[exp_type] = score

        if scores:
            return max(scores, key=scores.get)  # type: ignore[arg-type]

        # File-extension heuristics as fallback
        ext_counts: dict[str, int] = {}
        for f in files:
            ext = f.rsplit(".", 1)[-1].lower() if "." in f else ""
            ext_counts[ext] = ext_counts.get(ext, 0) + 1

        if ext_counts:
            dominant_ext = max(ext_counts, key=ext_counts.get)  # type: ignore[arg-type]
            ext_type_map: dict[str, ExperienceType] = {
                "sql": ExperienceType.DATABASE,
                "py": ExperienceType.FEATURE,
                "js": ExperienceType.FEATURE,
                "ts": ExperienceType.FEATURE,
                "yaml": ExperienceType.CONFIGURATION,
                "yml": ExperienceType.CONFIGURATION,
                "tf": ExperienceType.DEPLOYMENT,
                "md": ExperienceType.DOCUMENTATION,
                "css": ExperienceType.FEATURE,
                "html": ExperienceType.FEATURE,
                "json": ExperienceType.CONFIGURATION,
                "toml": ExperienceType.CONFIGURATION,
            }
            if dominant_ext in ext_type_map:
                return ext_type_map[dominant_ext]

        return ExperienceType.FEATURE

    def _extract_technologies(self, context: dict[str, Any]) -> list[str]:
        """Extract technology stack from context.

        Uses file extensions, task description keywords, and explicit
        technology declarations in the context.

        Args:
            context: The built context dictionary.

        Returns:
            Sorted list of unique technology names.
        """
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
            context.get("solution", ""),
            context.get("title", ""),
        ]).lower()

        for tech in self._TECH_KEYWORDS:
            if tech in searchable:
                found.add(tech)

        # From explicit technologies list in context
        for tech in context.get("technologies", []):
            if isinstance(tech, str) and tech.strip():
                found.add(tech.strip().lower())

        return sorted(found)

    def _extract_tags(self, context: dict[str, Any]) -> list[str]:
        """Extract relevant tags for filtering and retrieval.

        Tags are derived from the task type, agent type, technologies,
        and other contextual signals.

        Args:
            context: The built context dictionary.

        Returns:
            Sorted list of unique tag strings.
        """
        tags: set[str] = set()

        # Task type tag
        task_type = context.get("task_type", "")
        if task_type:
            tags.add(f"task:{task_type}")

        # Agent type tag
        agent_type = context.get("agent_type", "")
        if agent_type:
            tags.add(f"agent:{agent_type}")

        # Risk level tag
        risk_level = context.get("risk_level", "")
        if risk_level:
            tags.add(f"risk:{risk_level}")

        # Outcome tag
        outcome = context.get("outcome", "")
        if outcome:
            tags.add(f"outcome:{outcome}")

        # Technology tags (first 5 most relevant)
        technologies = context.get("technologies", [])
        if isinstance(technologies, list):
            for tech in technologies[:5]:
                if isinstance(tech, str) and tech.strip():
                    tags.add(f"tech:{tech.strip().lower()}")

        # Repository tag
        repo_id = context.get("repository_id", "")
        if repo_id:
            tags.add(f"repo:{repo_id}")

        # File pattern tags
        files = context.get("files_changed", [])
        if isinstance(files, list):
            dirs = set()
            for f in files:
                parts = f.split("/")
                if len(parts) > 1:
                    dirs.add(parts[0])
            for d in list(dirs)[:3]:
                tags.add(f"dir:{d}")

        return sorted(tags)

    # -------------------------------------------------------------------------
    # Scoring helpers
    # -------------------------------------------------------------------------

    def _calculate_confidence(self, outcome: str, context: dict[str, Any]) -> float:
        """Score confidence in this experience record (0.0-1.0).

        Factors:
            - Outcome success/failure (higher for clear outcomes).
            - Number of steps completed vs total.
            - Presence of validation results.
            - Human feedback alignment.

        Args:
            outcome: The experience outcome string.
            context: The built context dictionary.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        score = 0.5  # baseline

        # Outcome signal
        if outcome == Outcome.SUCCESS:
            score += 0.2
        elif outcome == Outcome.PARTIAL:
            score += 0.05
        else:
            score -= 0.1

        # Step completion ratio
        tasks_total = context.get("tasks_total", 0)
        tasks_completed = context.get("tasks_completed", 0)
        if isinstance(tasks_total, (int, float)) and tasks_total > 0:
            completion_ratio = tasks_completed / tasks_total
            score += completion_ratio * 0.15

        # Validation presence
        if context.get("validation_results"):
            score += 0.05

        # QA review presence
        if context.get("qa_results"):
            score += 0.05

        # Human feedback alignment
        feedback = context.get("human_feedback", {})
        if isinstance(feedback, dict):
            feedback_score = feedback.get("rating")
            if isinstance(feedback_score, (int, float)):
                score += (feedback_score / 5.0) * 0.1

        return max(0.0, min(1.0, score))

    def _calculate_reuse_potential(self, context: dict[str, Any]) -> float:
        """Score how reusable this experience knowledge is (0.0-1.0).

        Factors:
            - General applicability of the solution.
            - Number of technologies involved.
            - Whether the solution is pattern-based or ad-hoc.
            - Presence of clear steps that can be followed.

        Args:
            context: The built context dictionary.

        Returns:
            Reuse potential score between 0.0 and 1.0.
        """
        score = 0.4  # baseline

        # Pattern-based solutions are more reusable
        task_type = context.get("task_type", "").lower()
        pattern_types = {"architecture", "design", "testing", "deployment", "security"}
        if task_type in pattern_types:
            score += 0.15

        # Well-documented solutions are more reusable
        solution = context.get("solution", "")
        if isinstance(solution, str) and len(solution) > 100:
            score += 0.1

        # Fewer technology-specific details means more generalizable
        technologies = context.get("technologies", [])
        if isinstance(technologies, list) and len(technologies) <= 3:
            score += 0.1

        # Presence of step-by-step breakdown
        steps = context.get("steps", [])
        if isinstance(steps, list) and len(steps) >= 2:
            score += 0.1

        # Success outcome increases reuse confidence
        if context.get("outcome") == Outcome.SUCCESS:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _calculate_complexity(self, context: dict[str, Any]) -> float:
        """Score task complexity (0.0-1.0).

        Factors:
            - Number of files changed.
            - Number of tasks/steps involved.
            - Number of technologies used.
            - Dependencies between steps.
            - Presence of rollback points.

        Args:
            context: The built context dictionary.

        Returns:
            Complexity score between 0.0 and 1.0.
        """
        score = 0.2  # baseline

        # File count impact
        files = context.get("files_changed", [])
        if isinstance(files, list):
            file_count = len(files)
            if file_count > 20:
                score += 0.3
            elif file_count > 10:
                score += 0.2
            elif file_count > 5:
                score += 0.1

        # Task/step count impact
        tasks_total = context.get("tasks_total", 0)
        if isinstance(tasks_total, (int, float)):
            if tasks_total > 10:
                score += 0.2
            elif tasks_total > 5:
                score += 0.1

        # Technology count impact
        technologies = context.get("technologies", [])
        if isinstance(technologies, list):
            tech_count = len(technologies)
            if tech_count > 5:
                score += 0.1
            elif tech_count > 3:
                score += 0.05

        # Dependency complexity
        dependencies = context.get("dependencies", [])
        if isinstance(dependencies, list) and len(dependencies) > 3:
            score += 0.1

        # Rollback points indicate higher complexity
        if context.get("rollback_available"):
            score += 0.05

        # Risk level signal
        risk_level = context.get("risk_level", "").lower()
        if risk_level in ("critical", "high"):
            score += 0.1
        elif risk_level == "medium":
            score += 0.05

        return max(0.0, min(1.0, score))

    def _calculate_generalization(self, context: dict[str, Any]) -> float:
        """Score how generalizable this experience is (0.0-1.0).

        Factors:
            - Specificity of the task (generic vs project-specific).
            - Technology independence.
            - Whether the solution is a well-known pattern.
            - Absence of hard-coded project-specific values.

        Args:
            context: The built context dictionary.

        Returns:
            Generalization score between 0.0 and 1.0.
        """
        score = 0.5  # baseline

        # Generic task types are more generalizable
        task_type = context.get("task_type", "").lower()
        generic_types = {"testing", "documentation", "performance", "security", "architecture"}
        if task_type in generic_types:
            score += 0.1

        # Fewer technology bindings means more generalizable
        technologies = context.get("technologies", [])
        if isinstance(technologies, list):
            if len(technologies) <= 2:
                score += 0.15
            elif len(technologies) > 5:
                score -= 0.1

        # Fewer files changed means more focused/generalizable
        files = context.get("files_changed", [])
        if isinstance(files, list) and len(files) <= 3:
            score += 0.1

        # Solution that references well-known patterns
        solution = context.get("solution", "").lower()
        general_patterns = [
            "mvc", "repository pattern", "factory", "observer", "strategy",
            "singleton", "decorator", "adapter", "mediator", "pipeline",
        ]
        pattern_count = sum(1 for p in general_patterns if p in solution)
        if pattern_count > 0:
            score += min(0.15, pattern_count * 0.05)

        # Check for hard-coded project-specific values (reduces generalization)
        project_specific = ["localhost", "127.0.0.1", "hardcoded", "hardcoded"]
        searchable = f"{solution} {context.get('description', '')}".lower()
        specific_count = sum(1 for s in project_specific if s in searchable)
        if specific_count > 0:
            score -= specific_count * 0.05

        return max(0.0, min(1.0, score))

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _build_context(
        self, data: dict[str, Any], source: SourceType
    ) -> dict[str, Any]:
        """Build a normalized context dictionary from input data.

        Args:
            data: Raw input data.
            source: The source type of the data.

        Returns:
            Normalized context dictionary.
        """
        context: dict[str, Any] = {
            "source": source.value,
            "workflow_id": data.get("workflow_id") or data.get("id"),
            "repository_id": data.get("repository_id"),
            "task_type": data.get("task_type", ""),
            "task_description": data.get("description") or data.get("task_description", ""),
            "agent_type": data.get("agent_type", ""),
            "risk_level": data.get("risk_level", "medium"),
            "files_changed": self._extract_files(data),
            "technologies": data.get("technologies", []),
            "dependencies": data.get("dependencies", []),
            "rollback_available": data.get("rollback_available", False),
            "human_feedback": data.get("human_feedback", {}),
            "validation_results": data.get("validation_results"),
            "qa_results": data.get("qa_results"),
            "steps": data.get("steps", []),
            "tasks_total": data.get("tasks_total", 0),
            "tasks_completed": data.get("tasks_completed", 0),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "solution": data.get("solution", ""),
        }
        return context

    def _determine_outcome(self, data: dict[str, Any]) -> Outcome:
        """Determine the outcome from the data.

        Args:
            data: Input data dictionary.

        Returns:
            The determined Outcome.
        """
        status = (
            data.get("status", "")
            or data.get("outcome", "")
            or data.get("result", "")
        ).lower()

        if status in ("success", "completed", "passed", "passed_review"):
            return Outcome.SUCCESS
        elif status in ("partial", "partial_success", "warning"):
            return Outcome.PARTIAL
        elif status in ("failed", "failure", "error", "rejected"):
            return Outcome.FAILURE

        # Check task-level outcomes
        tasks = data.get("tasks", [])
        if isinstance(tasks, list) and tasks:
            completed = sum(1 for t in tasks if t.get("status") == "completed")
            total = len(tasks)
            if total > 0:
                ratio = completed / total
                if ratio >= 0.8:
                    return Outcome.SUCCESS
                elif ratio >= 0.5:
                    return Outcome.PARTIAL
                else:
                    return Outcome.FAILURE

        # Check step-level outcomes
        steps = data.get("steps", [])
        if isinstance(steps, list) and steps:
            completed = sum(
                1 for s in steps
                if s.get("status") in ("completed", "success")
            )
            total = len(steps)
            if total > 0:
                ratio = completed / total
                if ratio >= 0.8:
                    return Outcome.SUCCESS
                elif ratio >= 0.5:
                    return Outcome.PARTIAL
                else:
                    return Outcome.FAILURE

        return Outcome.SUCCESS

    def _extract_files(self, data: dict[str, Any]) -> list[str]:
        """Extract file paths changed from various data shapes.

        Args:
            data: Input data dictionary.

        Returns:
            Sorted list of unique file paths.
        """
        files: set[str] = set()

        # Direct files_changed
        fc = data.get("files_changed", [])
        if isinstance(fc, list):
            for f in fc:
                if isinstance(f, str):
                    files.add(f)
                elif isinstance(f, dict):
                    path = f.get("path") or f.get("file_path") or f.get("filename", "")
                    if path:
                        files.add(path)

        # From task results
        for task in data.get("tasks", []):
            if not isinstance(task, dict):
                continue
            result = task.get("result") or task.get("execution_result") or {}
            if isinstance(result, dict):
                for f in result.get("files_changed", []):
                    if isinstance(f, str):
                        files.add(f)
                    elif isinstance(f, dict):
                        path = f.get("path") or f.get("file_path") or ""
                        if path:
                            files.add(path)

        # From steps
        for step in data.get("steps", []):
            if not isinstance(step, dict):
                continue
            result = step.get("result") or {}
            if isinstance(result, dict):
                for f in result.get("files_changed", []):
                    if isinstance(f, str):
                        files.add(f)
                    elif isinstance(f, dict):
                        path = f.get("path") or f.get("file_path") or ""
                        if path:
                            files.add(path)

        return sorted(files)

    def _extract_solution(self, data: dict[str, Any]) -> str:
        """Extract solution description from data.

        Args:
            data: Input data dictionary.

        Returns:
            Solution description string.
        """
        solution = data.get("solution", "")
        if isinstance(solution, str) and solution.strip():
            return solution.strip()

        # Build from task results
        parts: list[str] = []
        for task in data.get("tasks", []):
            if not isinstance(task, dict):
                continue
            desc = task.get("description", "")
            result = task.get("result") or task.get("execution_result") or {}
            if isinstance(result, dict) and result.get("summary"):
                parts.append(result["summary"])
            elif isinstance(desc, str) and desc.strip():
                parts.append(desc.strip())

        # From reflection data
        lessons = data.get("lessons_learned", [])
        if isinstance(lessons, list):
            for lesson in lessons:
                if isinstance(lesson, dict) and lesson.get("description"):
                    parts.append(lesson["description"])

        return ". ".join(parts) if parts else ""

    def _extract_metadata(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract additional metadata from data.

        Args:
            data: Input data dictionary.

        Returns:
            Metadata dictionary.
        """
        metadata: dict[str, Any] = {}

        # Timing information
        if data.get("started_at"):
            metadata["started_at"] = str(data["started_at"])
        if data.get("completed_at"):
            metadata["completed_at"] = str(data["completed_at"])
        if data.get("duration"):
            metadata["duration_seconds"] = data["duration"]

        # Agent information
        if data.get("agent_type"):
            metadata["agent_type"] = data["agent_type"]
        if data.get("agent_id"):
            metadata["agent_id"] = data["agent_id"]

        # Execution information
        if data.get("execution_id"):
            metadata["execution_id"] = data["execution_id"]
        if data.get("commit_hash"):
            metadata["commit_hash"] = data["commit_hash"]
        if data.get("branch"):
            metadata["branch"] = data["branch"]

        # Pass through any existing metadata
        existing = data.get("metadata", {})
        if isinstance(existing, dict):
            metadata.update(existing)

        # Collector timestamp
        metadata["collected_at"] = datetime.now(UTC).isoformat()

        return metadata

    def _generate_title(self, data: dict[str, Any]) -> str:
        """Generate a concise title for the experience.

        Args:
            data: Input data dictionary.

        Returns:
            Title string (max 200 chars).
        """
        title = data.get("title", "")
        if isinstance(title, str) and title.strip():
            return title.strip()[:200]

        desc = data.get("description", "") or data.get("task_description", "")
        if isinstance(desc, str) and desc.strip():
            # Use first sentence or first 100 chars
            first_sentence = desc.split(".")[0].strip()
            if len(first_sentence) <= 200:
                return first_sentence
            return first_sentence[:197] + "..."

        task_type = data.get("task_type", "task")
        return f"{task_type} experience"

    def _generate_description(self, data: dict[str, Any]) -> str:
        """Generate a description for workflow experiences.

        Args:
            data: Input data dictionary.

        Returns:
            Description string.
        """
        desc = data.get("description", "")
        if isinstance(desc, str) and desc.strip():
            return desc.strip()

        title = data.get("title", "")
        tasks = data.get("tasks", [])
        parts: list[str] = []
        if isinstance(title, str) and title.strip():
            parts.append(title.strip())
        if isinstance(tasks, list):
            parts.append(f"Workflow with {len(tasks)} tasks.")

        return " ".join(parts) if parts else "Workflow experience."

    def _generate_execution_description(self, data: dict[str, Any]) -> str:
        """Generate a description for execution experiences.

        Args:
            data: Input data dictionary.

        Returns:
            Description string.
        """
        desc = data.get("description", "")
        if isinstance(desc, str) and desc.strip():
            return desc.strip()

        status = data.get("status", "unknown")
        tasks_total = data.get("tasks_total", 0)
        tasks_completed = data.get("tasks_completed", 0)
        files = self._extract_files(data)

        parts = [
            f"Execution {status}.",
            f"Completed {tasks_completed}/{tasks_total} tasks.",
        ]
        if files:
            parts.append(f"Changed {len(files)} files.")

        return " ".join(parts)

    def _generate_reflection_description(self, data: dict[str, Any]) -> str:
        """Generate a description for reflection experiences.

        Args:
            data: Input data dictionary.

        Returns:
            Description string.
        """
        desc = data.get("description", "") or data.get("summary", "")
        if isinstance(desc, str) and desc.strip():
            return desc.strip()

        lessons = data.get("lessons_learned", [])
        patterns = data.get("patterns", [])
        parts: list[str] = []
        if isinstance(lessons, list) and lessons:
            parts.append(f"Identified {len(lessons)} lessons.")
        if isinstance(patterns, list) and patterns:
            parts.append(f"Discovered {len(patterns)} patterns.")

        return " ".join(parts) if parts else "Reflection experience."

    def _generate_qa_description(self, data: dict[str, Any]) -> str:
        """Generate a description for QA experiences.

        Args:
            data: Input data dictionary.

        Returns:
            Description string.
        """
        desc = data.get("description", "")
        if isinstance(desc, str) and desc.strip():
            return desc.strip()

        results = data.get("results", {})
        tests_passed = 0
        tests_failed = 0
        if isinstance(results, dict):
            tests_passed = results.get("tests_passed", 0)
            tests_failed = results.get("tests_failed", 0)

        review_status = data.get("review_status", "")

        parts: list[str] = []
        if review_status:
            parts.append(f"Review status: {review_status}.")
        total = tests_passed + tests_failed
        if total > 0:
            parts.append(f"Tests: {tests_passed}/{total} passed.")

        return " ".join(parts) if parts else "QA experience."

    def _calculate_qa_confidence_boost(self, qa_data: dict[str, Any]) -> float:
        """Calculate confidence boost from QA validation.

        Args:
            qa_data: QA data dictionary.

        Returns:
            Confidence boost between 0.0 and 0.2.
        """
        boost = 0.0

        review_status = qa_data.get("review_status", "").lower()
        if review_status in ("approved", "passed", "accepted"):
            boost += 0.1
        elif review_status in ("changes_requested", "rejected"):
            boost -= 0.05

        results = qa_data.get("results", {})
        if isinstance(results, dict):
            tests_passed = results.get("tests_passed", 0)
            tests_failed = results.get("tests_failed", 0)
            total = tests_passed + tests_failed
            if total > 0:
                pass_ratio = tests_passed / total
                boost += pass_ratio * 0.1

        validation = qa_data.get("validation_results", {})
        if isinstance(validation, dict):
            if validation.get("is_valid"):
                boost += 0.05
            errors = validation.get("errors", [])
            if isinstance(errors, list) and len(errors) > 0:
                boost -= 0.05

        return max(-0.1, min(0.2, boost))
