"""DevOps Agent for deployment automation.

Analyzes project deployment readiness and generates deployment artifacts.
Does NOT deploy applications - all deployment requires human approval.
"""

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.logging import get_logger
from app.agents.devops.deployment_analyzer import DeploymentAnalyzer
from app.agents.devops.docker_generator import DockerGenerator
from app.agents.devops.compose_generator import ComposeGenerator
from app.agents.devops.github_actions import GitHubActionsGenerator
from app.agents.devops.kubernetes_generator import KubernetesGenerator
from app.agents.devops.security_validator import SecurityValidator
from app.agents.devops.deployment_report import DeploymentReportGenerator
from app.infrastructure.notifications import notify_deployment
from app.agents.devops.production_score import ProductionScoreCalculator

logger = get_logger(__name__)


class DevOpsStatus(str, Enum):
    """DevOps agent task status."""

    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    VALIDATING = "validating"
    SCORING = "scoring"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


class ArtifactType(str, Enum):
    """Types of deployment artifacts."""

    DOCKERFILE = "dockerfile"
    COMPOSE = "compose"
    COMPOSE_DEV = "compose_dev"
    GITHUB_ACTIONS = "github_actions"
    KUBERNETES = "kubernetes"
    REPORT = "report"
    ALL = "all"


@dataclass
class DevOpsTask:
    """Context for a DevOps analysis task."""

    task_id: str
    repository_id: str
    project_path: str
    description: str
    status: DevOpsStatus = DevOpsStatus.PENDING
    artifacts: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] | None = None
    security: dict[str, Any] | None = None
    score: dict[str, Any] | None = None
    report: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class DevOpsAgent:
    """DevOps Agent for deployment automation.

    Analyzes projects and generates deployment artifacts including:
    - Dockerfiles
    - Docker Compose files
    - GitHub Actions workflows
    - Kubernetes manifests
    - Deployment reports
    - Security validation
    - Production readiness scores

    IMPORTANT: This agent does NOT deploy applications.
    All deployment actions require human approval.
    """

    def __init__(self):
        """Initialize the DevOps agent with all sub-modules."""
        self.analyzer = DeploymentAnalyzer()
        self.docker_generator = DockerGenerator()
        self.compose_generator = ComposeGenerator()
        self.github_actions_generator = GitHubActionsGenerator()
        self.kubernetes_generator = KubernetesGenerator()
        self.security_validator = SecurityValidator()
        self.report_generator = DeploymentReportGenerator()
        self.score_calculator = ProductionScoreCalculator()
        self._tasks: dict[str, DevOpsTask] = {}

    async def analyze(
        self,
        repository_id: str,
        project_path: str,
        description: str = "",
        artifact_types: list[ArtifactType] | None = None,
    ) -> DevOpsTask:
        """Run full deployment analysis and artifact generation.

        Args:
            repository_id: Repository identifier.
            project_path: Path to the project root.
            description: Optional task description.
            artifact_types: Specific artifacts to generate (None = all).

        Returns:
            DevOpsTask with all generated artifacts.
        """
        task_id = str(uuid.uuid4())

        task = DevOpsTask(
            task_id=task_id,
            repository_id=repository_id,
            project_path=project_path,
            description=description,
        )
        self._tasks[task_id] = task

        logger.info(
            "Starting DevOps analysis: task=%s, repo=%s",
            task_id,
            repository_id,
        )

        try:
            # Phase 1: Infrastructure Analysis
            task.status = DevOpsStatus.ANALYZING
            logger.info("Phase 1: Analyzing infrastructure")

            files = await self._discover_files(project_path)
            analysis = await self.analyzer.analyze(project_path, files)
            task.analysis = self._dataclass_to_dict(analysis)

            # Phase 2: Security Validation
            task.status = DevOpsStatus.VALIDATING
            logger.info("Phase 2: Validating security")

            security = await self.security_validator.validate(
                project_path, files, task.analysis
            )
            task.security = self._dataclass_to_dict(security)

            # Phase 3: Generate Artifacts
            task.status = DevOpsStatus.GENERATING
            logger.info("Phase 3: Generating deployment artifacts")

            generate_all = artifact_types is None or ArtifactType.ALL in artifact_types

            if generate_all or ArtifactType.DOCKERFILE in artifact_types:
                await self._generate_dockerfile(task)

            if generate_all or ArtifactType.COMPOSE in artifact_types:
                await self._generate_compose(task, production=True)

            if generate_all or ArtifactType.COMPOSE_DEV in artifact_types:
                await self._generate_compose(task, production=False)

            if generate_all or ArtifactType.GITHUB_ACTIONS in artifact_types:
                await self._generate_github_actions(task)

            if generate_all or ArtifactType.KUBERNETES in artifact_types:
                await self._generate_kubernetes(task)

            # Phase 4: Production Score
            task.status = DevOpsStatus.SCORING
            logger.info("Phase 4: Calculating production score")

            score = await self.score_calculator.calculate(
                analysis=task.analysis,
                security=task.security,
                docker=task.artifacts.get("dockerfile"),
                cicd=task.artifacts.get("github_actions"),
            )
            task.score = self._dataclass_to_dict(score)

            # Phase 5: Generate Report
            task.status = DevOpsStatus.REPORTING
            logger.info("Phase 5: Generating deployment report")

            report = await self.report_generator.generate(
                analysis=task.analysis,
                security=task.security,
                score=task.score,
            )
            task.report = self._dataclass_to_dict(report)

            task.status = DevOpsStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)

            notify_deployment(os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"), task.repository_id or task_id, "completed",
                              f"Score: {task.score.get('overall_score', 0) if task.score else 'N/A'}")

            logger.info(
                "DevOps analysis completed: task=%s, score=%s",
                task_id,
                task.score.get("overall_score", 0) if task.score else 0,
            )

        except Exception as e:
            logger.error("DevOps analysis failed: task=%s, error=%s", task_id, str(e))
            task.status = DevOpsStatus.FAILED
            task.errors.append(str(e))
            task.completed_at = datetime.now(timezone.utc)

            notify_deployment(os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"), task.repository_id or task_id, "failed", str(e))

        return task

    async def get_task(self, task_id: str) -> DevOpsTask | None:
        """Get a DevOps task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(
        self, status: DevOpsStatus | None = None
    ) -> list[DevOpsTask]:
        """List all DevOps tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    async def _generate_dockerfile(self, task: DevOpsTask) -> None:
        """Generate Dockerfile for the project."""
        if not task.analysis:
            return

        project_type = task.analysis.get("project_type", "node")
        result = await self.docker_generator.generate(project_type, task.analysis)
        task.artifacts["dockerfile"] = self._dataclass_to_dict(result)

    async def _generate_compose(
        self, task: DevOpsTask, production: bool = True
    ) -> None:
        """Generate Docker Compose for the project."""
        if not task.analysis:
            return

        variant = "production" if production else "development"
        result = await self.compose_generator.generate(task.analysis, variant)
        key = "compose" if production else "compose_dev"
        task.artifacts[key] = self._dataclass_to_dict(result)

    async def _generate_github_actions(self, task: DevOpsTask) -> None:
        """Generate GitHub Actions workflows."""
        result = await self.github_actions_generator.generate_full_ci_cd(
            task.analysis or {}
        )
        task.artifacts["github_actions"] = self._dataclass_to_dict(result)

    async def _generate_kubernetes(self, task: DevOpsTask) -> None:
        """Generate Kubernetes manifests."""
        if not task.analysis:
            return

        result = await self.kubernetes_generator.generate(task.analysis)
        task.artifacts["kubernetes"] = self._dataclass_to_dict(result)

    async def _discover_files(self, project_path: str) -> list[str]:
        """Discover relevant files in the project."""
        import os

        relevant_extensions = {
            ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml",
            ".toml", ".cfg", ".ini", ".env", ".env.example", ".dockerignore",
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            ".github", "requirements.txt", "pyproject.toml", "package.json",
            "next.config.js", "next.config.ts", "vite.config.ts",
        }

        files = []
        for root, dirs, filenames in os.walk(project_path):
            # Skip hidden dirs and node_modules
            dirs[:] = [
                d for d in dirs
                if not d.startswith(".") and d not in {"node_modules", "__pycache__", "venv", ".venv"}
            ]

            for filename in filenames:
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, project_path)

                # Include if extension matches or filename matches
                _, ext = os.path.splitext(filename)
                if ext in relevant_extensions or filename in relevant_extensions:
                    files.append(rel_path)

        return files

    def _dataclass_to_dict(self, obj: Any) -> Any:
        """Convert a dataclass to a dictionary recursively."""
        if hasattr(obj, "__dataclass_fields__"):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                result[field_name] = self._dataclass_to_dict(value)
            return result
        elif isinstance(obj, list):
            return [self._dataclass_to_dict(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: self._dataclass_to_dict(v) for k, v in obj.items()}
        elif hasattr(obj, "value"):  # Enum
            return obj.value
        else:
            return obj
