"""GitHub Actions Workflow Generator.

Generates GitHub Actions workflow files for CI/CD pipelines
following best practices for caching, matrix builds, concurrency,
environment protection, and artifact handling.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import yaml

from app.core.logging import get_logger

logger = get_logger(__name__)


class WorkflowType(str, Enum):
    """Types of GitHub Actions workflows."""

    BUILD = "build"
    TEST = "test"
    LINT = "lint"
    DEPLOY = "deploy"
    SECURITY_SCAN = "security_scan"
    DEPENDENCY_SCAN = "dependency_scan"
    CONTAINER_BUILD = "container_build"
    FULL_CI_CD = "full_ci_cd"


@dataclass
class TriggerConfig:
    """Configuration for workflow triggers."""

    push_branches: list[str] = field(default_factory=lambda: ["main", "develop"])
    pull_request_branches: list[str] = field(default_factory=lambda: ["main", "develop"])
    schedule: str | None = None
    workflow_dispatch: bool = True


@dataclass
class StepConfig:
    """Configuration for a workflow step."""

    name: str
    uses: str | None = None
    run: str | None = None
    with_args: dict[str, Any] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
    if_condition: str | None = None


@dataclass
class JobConfig:
    """Configuration for a workflow job."""

    name: str
    runs_on: str = "ubuntu-latest"
    steps: list[StepConfig] = field(default_factory=list)
    needs: list[str] = field(default_factory=list)
    environment: str | None = None
    secrets: dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowConfig:
    """Configuration for a GitHub Actions workflow."""

    name: str
    on_triggers: TriggerConfig = field(default_factory=TriggerConfig)
    jobs: list[JobConfig] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    permissions: dict[str, str] = field(default_factory=dict)


@dataclass
class GitHubActionsResult:
    """Result of GitHub Actions workflow generation."""

    workflows: list[dict[str, Any]] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Return the number of generated workflows."""
        return len(self.workflows)


class GitHubActionsGenerator:
    """Generates GitHub Actions workflow files."""

    def __init__(self) -> None:
        """Initialize GitHub Actions generator."""
        self._yaml_dumper = yaml.SafeDumper

    async def generate(
        self,
        workflow_types: list[WorkflowType],
        config: dict[str, Any] | None = None,
    ) -> GitHubActionsResult:
        """Generate workflows for specified types.

        Args:
            workflow_types: List of workflow types to generate.
            config: Optional configuration overrides.

        Returns:
            GitHubActionsResult containing generated workflows.
        """
        logger.info("Generating workflows: types=%s", [wt.value for wt in workflow_types])
        config = config or {}
        result = GitHubActionsResult()

        for workflow_type in workflow_types:
            if workflow_type == WorkflowType.BUILD:
                workflow = await self.generate_build_workflow(config)
            elif workflow_type == WorkflowType.TEST:
                workflow = await self.generate_test_workflow(config)
            elif workflow_type == WorkflowType.LINT:
                workflow = await self.generate_lint_workflow(config)
            elif workflow_type == WorkflowType.DEPLOY:
                workflow = await self.generate_deploy_workflow(config)
            elif workflow_type == WorkflowType.SECURITY_SCAN:
                workflow = await self.generate_security_scan(config)
            elif workflow_type == WorkflowType.DEPENDENCY_SCAN:
                workflow = await self.generate_dependency_scan(config)
            elif workflow_type == WorkflowType.CONTAINER_BUILD:
                workflow = await self.generate_container_build(config)
            elif workflow_type == WorkflowType.FULL_CI_CD:
                full_result = await self.generate_full_ci_cd(config)
                result.workflows.extend(full_result.workflows)
                continue
            else:
                logger.warning("Unknown workflow type: %s", workflow_type)
                continue

            if workflow:
                result.workflows.append(workflow)

        logger.info("Generated %d workflows", result.count)
        return result

    async def generate_build_workflow(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a build workflow.

        Args:
            config: Build configuration.

        Returns:
            Workflow dict with filename, content, and type.
        """
        logger.info("Generating build workflow")

        language = config.get("language", "python")
        language_version = config.get("language_version", "3.12")

        triggers = self._build_triggers(config.get("triggers", {}))

        steps = self._build_common_steps(config)
        steps.extend(self._build_language_steps(language, language_version, config))
        steps.extend(self._build_upload_artifact_steps("build-output", config))

        job = JobConfig(
            name="build",
            runs_on=config.get("runs_on", "ubuntu-latest"),
            steps=steps,
        )

        workflow = WorkflowConfig(
            name="Build",
            on_triggers=triggers,
            jobs=[job],
            env=self._build_global_env(config),
            permissions={"contents": "read"},
        )

        return self._serialize_workflow(workflow, "build.yml")

    async def generate_test_workflow(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a test workflow with matrix builds.

        Args:
            config: Test configuration.

        Returns:
            Workflow dict with filename, content, and type.
        """
        logger.info("Generating test workflow")

        language = config.get("language", "python")
        matrix = config.get("matrix", self._default_matrix(language))

        triggers = self._build_triggers(config.get("triggers", {}))

        steps = self._build_common_steps(config)

        if language == "python":
            steps.extend([
                StepConfig(
                    name="Install dependencies",
                    run="pip install -r requirements.txt",
                ),
                StepConfig(
                    name="Run tests",
                    run="python -m pytest --cov=. --cov-report=xml -v",
                    env={"PYTHONPATH": "."},
                ),
                StepConfig(
                    name="Upload coverage",
                    uses="actions/upload-artifact@v4",
                    with_args={"name": "coverage-report", "path": "coverage.xml"},
                ),
            ])
        elif language == "node":
            steps.extend([
                StepConfig(
                    name="Install dependencies",
                    run="npm ci",
                ),
                StepConfig(
                    name="Run tests",
                    run="npm test -- --coverage",
                ),
                StepConfig(
                    name="Upload coverage",
                    uses="actions/upload-artifact@v4",
                    with_args={"name": "coverage-report", "path": "coverage/lcov.info"},
                ),
            ])

        job = JobConfig(
            name="test",
            runs_on="${{ matrix.os }}",
            steps=steps,
        )

        workflow_dict = self._serialize_workflow(
            WorkflowConfig(
                name="Tests",
                on_triggers=triggers,
                jobs=[job],
                env=self._build_global_env(config),
                permissions={"contents": "read"},
            ),
            "test.yml",
        )

        workflow_dict["content"]["jobs"]["test"]["strategy"] = {
            "matrix": matrix,
            "fail-fast": False,
        }

        return workflow_dict

    async def generate_lint_workflow(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a linting workflow.

        Args:
            config: Lint configuration.

        Returns:
            Workflow dict with filename, content, and type.
        """
        logger.info("Generating lint workflow")

        language = config.get("language", "python")
        triggers = self._build_triggers(config.get("triggers", {}))

        steps = self._build_common_steps(config)

        if language == "python":
            steps.extend([
                StepConfig(
                    name="Install dependencies",
                    run="pip install ruff mypy",
                ),
                StepConfig(
                    name="Run ruff linter",
                    run="ruff check .",
                ),
                StepConfig(
                    name="Run ruff formatter check",
                    run="ruff format --check .",
                ),
                StepConfig(
                    name="Run type checking",
                    run="mypy .",
                ),
            ])
        elif language == "node":
            steps.extend([
                StepConfig(
                    name="Install dependencies",
                    run="npm ci",
                ),
                StepConfig(
                    name="Run ESLint",
                    run="npm run lint",
                ),
                StepConfig(
                    name="Run type checking",
                    run="npm run typecheck",
                ),
            ])

        job = JobConfig(
            name="lint",
            runs_on=config.get("runs_on", "ubuntu-latest"),
            steps=steps,
        )

        return self._serialize_workflow(
            WorkflowConfig(
                name="Lint",
                on_triggers=triggers,
                jobs=[job],
                env=self._build_global_env(config),
                permissions={"contents": "read"},
            ),
            "lint.yml",
        )

    async def generate_deploy_workflow(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a deployment workflow with environment protection.

        Args:
            config: Deploy configuration.

        Returns:
            Workflow dict with filename, content, and type.
        """
        logger.info("Generating deploy workflow")

        environment = config.get("environment", "production")
        deploy_command = config.get("deploy_command", "echo 'Deploying...'")

        triggers = TriggerConfig(
            push_branches=["main"],
            pull_request_branches=[],
            workflow_dispatch=True,
        )

        steps = [
            StepConfig(
                name="Checkout code",
                uses="actions/checkout@v4",
            ),
            StepConfig(
                name="Download artifact",
                uses="actions/download-artifact@v4",
                with_args={"name": "build-output", "path": "./dist"},
            ),
            StepConfig(
                name="Deploy",
                run=deploy_command,
                env={
                    "DEPLOY_ENVIRONMENT": environment,
                    "DEPLOY_TOKEN": "${{ secrets.DEPLOY_TOKEN }}",
                },
            ),
            StepConfig(
                name="Notify deployment",
                if_condition="success()",
                run="echo 'Deployment to ${{ env.DEPLOY_ENVIRONMENT }} successful'",
            ),
            StepConfig(
                name="Notify failure",
                if_condition="failure()",
                run="echo 'Deployment failed' && exit 1",
            ),
        ]

        job = JobConfig(
            name="deploy",
            runs_on=config.get("runs_on", "ubuntu-latest"),
            steps=steps,
            environment=environment,
        )

        workflow = WorkflowConfig(
            name="Deploy",
            on_triggers=triggers,
            jobs=[job],
            env=self._build_global_env(config),
            permissions={"contents": "read", "deployments": "write"},
        )

        return self._serialize_workflow(workflow, "deploy.yml")

    async def generate_security_scan(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a security scanning workflow.

        Args:
            config: Security scan configuration.

        Returns:
            Workflow dict with filename, content, and type.
        """
        logger.info("Generating security scan workflow")

        triggers = TriggerConfig(
            push_branches=["main", "develop"],
            pull_request_branches=["main"],
            schedule="0 6 * * 1",
            workflow_dispatch=True,
        )

        steps = [
            StepConfig(
                name="Checkout code",
                uses="actions/checkout@v4",
            ),
            StepConfig(
                name="Run Trivy vulnerability scanner",
                uses="aquasecurity/trivy-action@master",
                with_args={
                    "scan-type": "fs",
                    "scan-ref": ".",
                    "format": "sarif",
                    "output": "trivy-results.sarif",
                },
            ),
            StepConfig(
                name="Upload Trivy scan results",
                uses="github/codeql-action/upload-sarif@v3",
                if_condition="always()",
                with_args={"sarif_file": "trivy-results.sarif"},
            ),
            StepConfig(
                name="Run CodeQL analysis",
                uses="github/codeql-action/analyze@v3",
                with_args={
                    "category": "/language:python",
                },
            ),
            StepConfig(
                name="Secret scanning",
                uses="trufflesecurity/trufflehog@main",
                with_args={
                    "extra_args": "--only-verified",
                },
            ),
        ]

        job = JobConfig(
            name="security",
            runs_on=config.get("runs_on", "ubuntu-latest"),
            steps=steps,
        )

        return self._serialize_workflow(
            WorkflowConfig(
                name="Security Scan",
                on_triggers=triggers,
                jobs=[job],
                env=self._build_global_env(config),
                permissions={"contents": "read", "security-events": "write"},
            ),
            "security.yml",
        )

    async def generate_dependency_scan(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a dependency scanning workflow.

        Args:
            config: Dependency scan configuration.

        Returns:
            Workflow dict with filename, content, and type.
        """
        logger.info("Generating dependency scan workflow")

        language = config.get("language", "python")

        triggers = TriggerConfig(
            push_branches=["main"],
            pull_request_branches=["main"],
            schedule="0 8 * * 1",
            workflow_dispatch=True,
        )

        steps = [
            StepConfig(
                name="Checkout code",
                uses="actions/checkout@v4",
            ),
        ]

        if language == "python":
            steps.extend([
                StepConfig(
                    name="Set up Python",
                    uses="actions/setup-python@v5",
                    with_args={"python-version": config.get("language_version", "3.12")},
                ),
                StepConfig(
                    name="Install pip-audit",
                    run="pip install pip-audit",
                ),
                StepConfig(
                    name="Audit dependencies",
                    run="pip-audit -r requirements.txt --output deps-audit.json --format json",
                ),
                StepConfig(
                    name="Upload audit report",
                    uses="actions/upload-artifact@v4",
                    with_args={"name": "dependency-audit", "path": "deps-audit.json"},
                ),
            ])
        elif language == "node":
            steps.extend([
                StepConfig(
                    name="Set up Node.js",
                    uses="actions/setup-node@v4",
                    with_args={"node-version": config.get("language_version", "20")},
                ),
                StepConfig(
                    name="Install dependencies",
                    run="npm ci",
                ),
                StepConfig(
                    name="Run npm audit",
                    run="npm audit --json > deps-audit.json || true",
                ),
                StepConfig(
                    name="Upload audit report",
                    uses="actions/upload-artifact@v4",
                    with_args={"name": "dependency-audit", "path": "deps-audit.json"},
                ),
            ])

        job = JobConfig(
            name="dependency-scan",
            runs_on=config.get("runs_on", "ubuntu-latest"),
            steps=steps,
        )

        return self._serialize_workflow(
            WorkflowConfig(
                name="Dependency Scan",
                on_triggers=triggers,
                jobs=[job],
                env=self._build_global_env(config),
                permissions={"contents": "read"},
            ),
            "dependency-scan.yml",
        )

    async def generate_container_build(
        self,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a container build and push workflow.

        Args:
            config: Container build configuration.

        Returns:
            Workflow dict with filename, content, and type.
        """
        logger.info("Generating container build workflow")

        registry = config.get("registry", "ghcr.io")
        image_name = config.get("image_name", "${{ github.repository }}")
        dockerfile = config.get("dockerfile", "Dockerfile")

        triggers = TriggerConfig(
            push_branches=["main"],
            pull_request_branches=[],
            workflow_dispatch=True,
        )

        steps = [
            StepConfig(
                name="Checkout code",
                uses="actions/checkout@v4",
            ),
            StepConfig(
                name="Set up Docker Buildx",
                uses="docker/setup-buildx-action@v3",
            ),
            StepConfig(
                name="Log in to Container Registry",
                uses="docker/login-action@v3",
                with_args={
                    "registry": registry,
                    "username": "${{ github.actor }}",
                    "password": "${{ secrets.GITHUB_TOKEN }}",
                },
            ),
            StepConfig(
                name="Extract metadata",
                id="meta",
                uses="docker/metadata-action@v5",
                with_args={
                    "images": f"{registry}/{image_name}",
                    "tags": [
                        "type=ref,event=branch",
                        "type=ref,event=pr",
                        "type=semver,pattern={{version}}",
                        "type=sha",
                    ],
                },
            ),
            StepConfig(
                name="Build and push",
                uses="docker/build-push-action@v5",
                with_args={
                    "context": ".",
                    "file": dockerfile,
                    "push": "${{ github.event_name != 'pull_request' }}",
                    "tags": "${{ steps.meta.outputs.tags }}",
                    "labels": "${{ steps.meta.outputs.labels }}",
                    "cache-from": "type=gha",
                    "cache-to": "type=gha,mode=max",
                },
            ),
        ]

        job = JobConfig(
            name="container",
            runs_on=config.get("runs_on", "ubuntu-latest"),
            steps=steps,
        )

        return self._serialize_workflow(
            WorkflowConfig(
                name="Container Build",
                on_triggers=triggers,
                jobs=[job],
                env=self._build_global_env(config),
                permissions={"contents": "read", "packages": "write"},
            ),
            "container.yml",
        )

    async def generate_full_ci_cd(
        self,
        config: dict[str, Any],
    ) -> GitHubActionsResult:
        """Generate a complete CI/CD pipeline with all workflows.

        Args:
            config: Full CI/CD configuration.

        Returns:
            GitHubActionsResult with all workflows.
        """
        logger.info("Generating full CI/CD pipeline")

        result = GitHubActionsResult()

        workflow_generators = [
            (WorkflowType.BUILD, self.generate_build_workflow),
            (WorkflowType.TEST, self.generate_test_workflow),
            (WorkflowType.LINT, self.generate_lint_workflow),
            (WorkflowType.DEPLOY, self.generate_deploy_workflow),
            (WorkflowType.SECURITY_SCAN, self.generate_security_scan),
            (WorkflowType.DEPENDENCY_SCAN, self.generate_dependency_scan),
            (WorkflowType.CONTAINER_BUILD, self.generate_container_build),
        ]

        for workflow_type, generator in workflow_generators:
            workflow = await generator(config)
            if workflow:
                result.workflows.append(workflow)

        logger.info("Full CI/CD pipeline generated: %d workflows", result.count)
        return result

    def _build_triggers(
        self,
        trigger_overrides: dict[str, Any],
    ) -> TriggerConfig:
        """Build trigger configuration from overrides.

        Args:
            trigger_overrides: Trigger configuration overrides.

        Returns:
            TriggerConfig instance.
        """
        return TriggerConfig(
            push_branches=trigger_overrides.get(
                "push_branches", ["main", "develop"]
            ),
            pull_request_branches=trigger_overrides.get(
                "pull_request_branches", ["main", "develop"]
            ),
            schedule=trigger_overrides.get("schedule"),
            workflow_dispatch=trigger_overrides.get("workflow_dispatch", True),
        )

    def _build_common_steps(
        self,
        config: dict[str, Any],
    ) -> list[StepConfig]:
        """Build common workflow steps.

        Args:
            config: Workflow configuration.

        Returns:
            List of common StepConfig instances.
        """
        steps = [
            StepConfig(
                name="Checkout code",
                uses="actions/checkout@v4",
            ),
        ]

        cache_enabled = config.get("cache", True)
        if cache_enabled:
            language = config.get("language", "python")
            if language == "python":
                steps.append(
                    StepConfig(
                        name="Cache pip",
                        uses="actions/cache@v4",
                        with_args={
                            "path": "~/.cache/pip",
                            "key": "${{ runner.os }}-pip-${{ hashFiles('**/requirements*.txt') }}",
                            "restore-keys": "${{ runner.os }}-pip-",
                        },
                    )
                )
            elif language == "node":
                steps.append(
                    StepConfig(
                        name="Cache npm",
                        uses="actions/cache@v4",
                        with_args={
                            "path": "~/.npm",
                            "key": "${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}",
                            "restore-keys": "${{ runner.os }}-node-",
                        },
                    )
                )

        return steps

    def _build_language_steps(
        self,
        language: str,
        version: str,
        config: dict[str, Any],
    ) -> list[StepConfig]:
        """Build language-specific setup and build steps.

        Args:
            language: Programming language.
            version: Language version.
            config: Workflow configuration.

        Returns:
            List of language-specific StepConfig instances.
        """
        steps: list[StepConfig] = []

        if language == "python":
            steps.extend([
                StepConfig(
                    name="Set up Python",
                    uses="actions/setup-python@v5",
                    with_args={"python-version": version},
                ),
                StepConfig(
                    name="Install dependencies",
                    run="pip install -r requirements.txt",
                ),
                StepConfig(
                    name="Build",
                    run="python -m build",
                ),
            ])
        elif language == "node":
            steps.extend([
                StepConfig(
                    name="Set up Node.js",
                    uses="actions/setup-node@v4",
                    with_args={"node-version": version},
                ),
                StepConfig(
                    name="Install dependencies",
                    run="npm ci",
                ),
                StepConfig(
                    name="Build",
                    run="npm run build",
                ),
            ])

        custom_build_command = config.get("build_command")
        if custom_build_command:
            steps.append(
                StepConfig(
                    name="Custom build",
                    run=custom_build_command,
                )
            )

        return steps

    def _build_upload_artifact_steps(
        self,
        artifact_name: str,
        config: dict[str, Any],
    ) -> list[StepConfig]:
        """Build artifact upload steps.

        Args:
            artifact_name: Name of the artifact.
            config: Workflow configuration.

        Returns:
            List of StepConfig instances for artifact upload.
        """
        upload_artifacts = config.get("upload_artifacts", True)
        if not upload_artifacts:
            return []

        artifact_path = config.get("artifact_path", "dist")
        return [
            StepConfig(
                name="Upload artifact",
                uses="actions/upload-artifact@v4",
                with_args={
                    "name": artifact_name,
                    "path": artifact_path,
                    "retention-days": config.get("artifact_retention_days", 7),
                },
            ),
        ]

    def _build_global_env(
        self,
        config: dict[str, Any],
    ) -> dict[str, str]:
        """Build global environment variables.

        Args:
            config: Workflow configuration.

        Returns:
            Dict of environment variables.
        """
        env: dict[str, str] = {
            "PYTHONUNBUFFERED": "1",
        }

        custom_env = config.get("env", {})
        env.update(custom_env)

        return env

    def _default_matrix(self, language: str) -> dict[str, Any]:
        """Build default matrix for language.

        Args:
            language: Programming language.

        Returns:
            Default matrix configuration.
        """
        if language == "python":
            return {
                "os": ["ubuntu-latest"],
                "python-version": ["3.10", "3.11", "3.12"],
            }
        if language == "node":
            return {
                "os": ["ubuntu-latest"],
                "node-version": ["18", "20", "22"],
            }
        return {"os": ["ubuntu-latest"]}

    def _serialize_workflow(
        self,
        workflow: WorkflowConfig,
        filename: str,
    ) -> dict[str, Any]:
        """Serialize a WorkflowConfig to a workflow dict.

        Args:
            workflow: WorkflowConfig instance.
            filename: Output filename.

        Returns:
            Dict with filename, content, and type.
        """
        triggers = self._serialize_triggers(workflow.on_triggers)

        jobs = {}
        for job in workflow.jobs:
            jobs[job.name] = self._serialize_job(job)

        content: dict[str, Any] = {
            "name": workflow.name,
            "on": triggers,
            "jobs": jobs,
        }

        if workflow.env:
            content["env"] = workflow.env

        if workflow.permissions:
            content["permissions"] = workflow.permissions

        return {
            "filename": filename,
            "content": content,
            "type": filename.replace(".yml", ""),
        }

    def _serialize_triggers(
        self,
        triggers: TriggerConfig,
    ) -> dict[str, Any]:
        """Serialize triggers to dict.

        Args:
            triggers: TriggerConfig instance.

        Returns:
            Serialized triggers dict.
        """
        on_config: dict[str, Any] = {}

        push_config: dict[str, Any] = {}
        if triggers.push_branches:
            push_config["branches"] = triggers.push_branches
        if push_config:
            on_config["push"] = push_config

        pr_config: dict[str, Any] = {}
        if triggers.pull_request_branches:
            pr_config["branches"] = triggers.pull_request_branches
        if pr_config:
            on_config["pull_request"] = pr_config

        if triggers.schedule:
            on_config["schedule"] = [{"cron": triggers.schedule}]

        if triggers.workflow_dispatch:
            on_config["workflow_dispatch"] = {}

        return on_config

    def _serialize_job(
        self,
        job: JobConfig,
    ) -> dict[str, Any]:
        """Serialize a job to dict.

        Args:
            job: JobConfig instance.

        Returns:
            Serialized job dict.
        """
        job_dict: dict[str, Any] = {
            "runs-on": job.runs_on,
        }

        if job.needs:
            if len(job.needs) == 1:
                job_dict["needs"] = job.needs[0]
            else:
                job_dict["needs"] = job.needs

        if job.environment:
            job_dict["environment"] = job.environment

        steps = []
        for step in job.steps:
            steps.append(self._serialize_step(step))
        job_dict["steps"] = steps

        return job_dict

    def _serialize_step(
        self,
        step: StepConfig,
    ) -> dict[str, Any]:
        """Serialize a step to dict.

        Args:
            step: StepConfig instance.

        Returns:
            Serialized step dict.
        """
        step_dict: dict[str, str | dict[str, Any]] = {"name": step.name}

        if step.uses:
            step_dict["uses"] = step.uses

        if step.run:
            step_dict["run"] = step.run

        if step.with_args:
            step_dict["with"] = step.with_args

        if step.env:
            step_dict["env"] = step.env

        if step.if_condition:
            step_dict["if"] = step.if_condition

        return step_dict
