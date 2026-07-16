"""Production readiness score calculator.

Evaluates multiple dimensions of production readiness and produces
a weighted overall score with actionable recommendations.
"""

from __future__ import annotations

import asyncio
import datetime
from dataclasses import dataclass, field
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ScoreDimension(str, Enum):
    """Dimensions evaluated in the production readiness score."""

    DOCKER = "docker"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MONITORING = "monitoring"
    LOGGING = "logging"
    CONFIGURATION = "configuration"
    CICD = "cicd"
    OVERALL = "overall"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ScoreItem:
    """A single scoring dimension with its result."""

    dimension: ScoreDimension
    score: float  # 0-100
    weight: float = 1.0
    details: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ProductionScore:
    """Complete production readiness assessment."""

    overall_score: float
    dimensions: list[ScoreItem] = field(default_factory=list)
    grade: str = "F"
    recommendations: list[str] = field(default_factory=list)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    @property
    def by_dimension(self) -> dict[ScoreDimension, ScoreItem]:
        return {d.dimension: d for d in self.dimensions}

    def summary(self) -> str:
        lines = [
            f"Overall: {self.overall_score:.1f}/100 (grade: {self.grade})",
            "Dimension breakdown:",
        ]
        for item in self.dimensions:
            lines.append(f"  {item.dimension.value:>20s}: {item.score:5.1f} (weight {item.weight:.0%})")
        if self.recommendations:
            lines.append("Top recommendations:")
            for rec in self.recommendations[:5]:
                lines.append(f"  - {rec}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Weight configuration
# ---------------------------------------------------------------------------

# Weights determine how much each dimension contributes to the overall score.
_DIMENSION_WEIGHTS: dict[ScoreDimension, float] = {
    ScoreDimension.DOCKER: 0.18,
    ScoreDimension.SECURITY: 0.22,
    ScoreDimension.PERFORMANCE: 0.14,
    ScoreDimension.MONITORING: 0.14,
    ScoreDimension.LOGGING: 0.12,
    ScoreDimension.CONFIGURATION: 0.10,
    ScoreDimension.CICD: 0.10,
}

# Maximum points per sub-check within each dimension.
DOCKER_CHECKS: dict[str, int] = {
    "dockerfile_exists": 20,
    "multi_stage_build": 15,
    "health_check": 15,
    "non_root_user": 10,
    "optimized_layers": 10,
    "dockerignore": 10,
    "compose_file": 10,
    "resource_limits": 10,
}

SECURITY_CHECKS: dict[str, int] = {
    "no_hardcoded_secrets": 20,
    "env_vars_secure": 15,
    "docker_security": 15,
    "dependency_scan": 15,
    "network_policies": 15,
    "cors_config": 10,
    "debug_off": 10,
}

PERFORMANCE_CHECKS: dict[str, int] = {
    "caching": 20,
    "compression": 15,
    "connection_pooling": 15,
    "load_balancing": 15,
    "resource_limits": 15,
    "cdn": 10,
    "lazy_loading": 10,
}

MONITORING_CHECKS: dict[str, int] = {
    "health_checks": 20,
    "metrics_endpoint": 20,
    "prometheus": 15,
    "grafana": 15,
    "logging": 15,
    "alerts": 15,
}

LOGGING_CHECKS: dict[str, int] = {
    "structured_logging": 25,
    "log_levels": 20,
    "log_rotation": 15,
    "error_tracking": 20,
    "audit_logging": 20,
}

CONFIGURATION_CHECKS: dict[str, int] = {
    "env_files": 20,
    "config_validation": 20,
    "secrets_management": 20,
    "environment_separation": 20,
    "feature_flags": 20,
}

CICD_CHECKS: dict[str, int] = {
    "ci_pipeline": 25,
    "automated_tests": 20,
    "linting": 15,
    "security_scans": 15,
    "deployment_pipeline": 15,
    "artifact_management": 10,
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _flag(data: dict | None, key: str) -> bool:
    """Return a boolean from *data* if *key* is present, else False."""
    if data is None:
        return False
    return bool(data.get(key))


def _has_dockerfile(analysis: dict) -> bool:
    """Check whether the project has a Dockerfile."""
    files: list[str] = analysis.get("files", [])
    return any("Dockerfile" in f for f in files)


def _has_compose(analysis: dict) -> bool:
    files: list[str] = analysis.get("files", [])
    return any("docker-compose" in f or "compose.yaml" in f for f in files)


def _has_ci(analysis: dict) -> bool:
    files: list[str] = analysis.get("files", [])
    return any(
        ".github/workflows" in f or ".gitlab-ci" in f or "Jenkinsfile" in f
        for f in files
    )


def _has_tests(analysis: dict) -> bool:
    files: list[str] = analysis.get("files", [])
    return any(
        "test_" in f or "_test" in f or "spec" in f or "__tests__" in f
        for f in files
    )


def _has_linting(analysis: dict) -> bool:
    files: list[str] = analysis.get("files", [])
    return any(
        "eslint" in f or "ruff" in f or "flake8" in f or "pylint" in f
        for f in files
    )


def _has_monitoring(analysis: dict) -> bool:
    deps: dict[str, str] = analysis.get("dependencies", {})
    monitors = {"prometheus", "grafana-client", "datadog", "statsd", "newrelic"}
    return bool(monitors & set(deps.keys()))


def _has_structured_logging(analysis: dict) -> bool:
    deps: dict[str, str] = analysis.get("dependencies", {})
    return any(
        lib in deps
        for lib in ("structlog", "structlog[dev]", "loguru", "python-json-logger")
    )


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------


class ProductionScoreCalculator:
    """Calculate production readiness across multiple dimensions."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def calculate(
        self,
        analysis: dict,
        security: dict | None = None,
        docker: dict | None = None,
        cicd: dict | None = None,
    ) -> ProductionScore:
        """Run all dimension calculations and aggregate."""
        logger.info("production_score.calculate.start")

        dimensions = await asyncio.gather(
            self.calculate_docker_score(analysis, docker),
            self.calculate_security_score(analysis, security),
            self.calculate_performance_score(analysis),
            self.calculate_monitoring_score(analysis),
            self.calculate_logging_score(analysis),
            self.calculate_configuration_score(analysis),
            self.calculate_cicd_score(analysis, cicd),
        )

        overall = self._weighted_average(dimensions)
        grade = self._calculate_grade(overall)
        recommendations = self._compile_recommendations(dimensions)

        result = ProductionScore(
            overall_score=overall,
            dimensions=list(dimensions),
            grade=grade,
            recommendations=recommendations,
        )
        logger.info(
            "production_score.calculate.done",
            score=overall,
            grade=grade,
        )
        return result

    # ------------------------------------------------------------------
    # Dimension scorers
    # ------------------------------------------------------------------

    async def calculate_docker_score(
        self, analysis: dict, docker: dict | None = None
    ) -> ScoreItem:
        details: list[str] = []
        recs: list[str] = []
        score = 0.0

        has_dockerfile = _has_dockerfile(analysis)
        if has_dockerfile:
            score += DOCKER_CHECKS["dockerfile_exists"]
            details.append("Dockerfile detected")
        else:
            recs.append("Add a Dockerfile for containerized deployments")

        docker_data = docker or {}
        if docker_data.get("multi_stage"):
            score += DOCKER_CHECKS["multi_stage_build"]
            details.append("Multi-stage build detected")
        else:
            recs.append("Use multi-stage builds to reduce image size")

        if docker_data.get("healthcheck") or _flag(docker_data, "health_check"):
            score += DOCKER_CHECKS["health_check"]
            details.append("Health check configured")
        else:
            recs.append("Add HEALTHCHECK instruction to Dockerfile")

        if docker_data.get("non_root"):
            score += DOCKER_CHECKS["non_root_user"]
            details.append("Non-root user configured")
        else:
            recs.append("Run container as non-root user for security")

        if docker_data.get("optimized"):
            score += DOCKER_CHECKS["optimized_layers"]
            details.append("Optimized layer caching detected")
        else:
            recs.append("Optimize Dockerfile layers for faster builds")

        if _has_dockerfile(analysis):
            has_ignore = any(
                ".dockerignore" in f
                for f in analysis.get("files", [])
            )
            if has_ignore:
                score += DOCKER_CHECKS["dockerignore"]
                details.append(".dockerignore file present")
            else:
                recs.append("Add a .dockerignore file to exclude unnecessary files")

        if _has_compose(analysis):
            score += DOCKER_CHECKS["compose_file"]
            details.append("Docker Compose file detected")
        else:
            recs.append("Add a docker-compose.yml for local orchestration")

        if docker_data.get("resource_limits"):
            score += DOCKER_CHECKS["resource_limits"]
            details.append("Resource limits set")
        else:
            recs.append("Set CPU and memory limits in Compose or Kubernetes")

        return ScoreItem(
            dimension=ScoreDimension.DOCKER,
            score=min(score, 100.0),
            weight=_DIMENSION_WEIGHTS[ScoreDimension.DOCKER],
            details=details,
            recommendations=recs,
        )

    async def calculate_security_score(
        self, analysis: dict, security: dict | None = None
    ) -> ScoreItem:
        details: list[str] = []
        recs: list[str] = []
        score = 0.0
        sec = security or {}

        if sec.get("no_hardcoded_secrets", True):
            score += SECURITY_CHECKS["no_hardcoded_secrets"]
            details.append("No hardcoded secrets detected")
        else:
            recs.append("Remove hardcoded secrets and use environment variables")

        if sec.get("env_vars_secure", False):
            score += SECURITY_CHECKS["env_vars_secure"]
            details.append("Environment variable security verified")
        else:
            recs.append("Validate that sensitive values are passed via secure env vars")

        if sec.get("docker_security", False):
            score += SECURITY_CHECKS["docker_security"]
            details.append("Docker security best practices applied")
        else:
            recs.append("Apply Docker security scanning and best practices")

        if sec.get("dependency_scan", False):
            score += SECURITY_CHECKS["dependency_scan"]
            details.append("Dependency vulnerability scanning enabled")
        else:
            recs.append("Enable dependency vulnerability scanning (e.g. Snyk, Dependabot)")

        if sec.get("network_policies", False):
            score += SECURITY_CHECKS["network_policies"]
            details.append("Network policies configured")
        else:
            recs.append("Define network policies to restrict inter-service traffic")

        if sec.get("cors_config", False):
            score += SECURITY_CHECKS["cors_config"]
            details.append("CORS configuration present")
        else:
            recs.append("Configure CORS to allow only trusted origins")

        if sec.get("debug_off", True):
            score += SECURITY_CHECKS["debug_off"]
            details.append("Debug mode is disabled")
        else:
            recs.append("Ensure DEBUG=False in production")

        return ScoreItem(
            dimension=ScoreDimension.SECURITY,
            score=min(score, 100.0),
            weight=_DIMENSION_WEIGHTS[ScoreDimension.SECURITY],
            details=details,
            recommendations=recs,
        )

    async def calculate_performance_score(self, analysis: dict) -> ScoreItem:
        details: list[str] = []
        recs: list[str] = []
        score = 0.0
        deps: dict[str, str] = analysis.get("dependencies", {})

        caching_libs = {"redis", "aiocache", "cachetools", "django.core.cache"}
        if caching_libs & set(deps.keys()):
            score += PERFORMANCE_CHECKS["caching"]
            details.append("Caching library detected")
        else:
            recs.append("Add a caching layer (Redis, Memcached, or in-memory)")

        compression_libs = {"brotli", "python-snappy", "fastapi-compress"}
        if compression_libs & set(deps.keys()):
            score += PERFORMANCE_CHECKS["compression"]
            details.append("Compression middleware detected")
        else:
            recs.append("Enable response compression (gzip/brotli)")

        pooling_libs = {"asyncpg", "psycopg2-pool", "sqlalchemy"}
        if pooling_libs & set(deps.keys()):
            score += PERFORMANCE_CHECKS["connection_pooling"]
            details.append("Connection pooling library detected")
        else:
            recs.append("Use connection pooling for database connections")

        load_balancers = {"gunicorn", "uvicorn[standard]", "hypercorn"}
        if load_balancers & set(deps.keys()):
            score += PERFORMANCE_CHECKS["load_balancing"]
            details.append("Process manager / load balancer detected")
        else:
            recs.append("Use a multi-worker process manager for horizontal scaling")

        resources_config = any(
            key in analysis.get("config", {})
            for key in ("deploy.resources", "replicas", "cpu", "memory")
        )
        if resources_config:
            score += PERFORMANCE_CHECKS["resource_limits"]
            details.append("Resource configuration detected")
        else:
            recs.append("Define CPU and memory resource limits")

        cdn_indicators = {"cloudfront", "boto3-cloudfront", "django-storages"}
        if cdn_indicators & set(deps.keys()):
            score += PERFORMANCE_CHECKS["cdn"]
            details.append("CDN integration detected")
        else:
            recs.append("Consider a CDN for static asset delivery")

        lazy_libs = {"react.lazy", "next/dynamic", "vue-lazyload"}
        if lazy_libs & set(deps.keys()):
            score += PERFORMANCE_CHECKS["lazy_loading"]
            details.append("Lazy loading detected")
        else:
            recs.append("Implement lazy loading for routes and heavy components")

        return ScoreItem(
            dimension=ScoreDimension.PERFORMANCE,
            score=min(score, 100.0),
            weight=_DIMENSION_WEIGHTS[ScoreDimension.PERFORMANCE],
            details=details,
            recommendations=recs,
        )

    async def calculate_monitoring_score(self, analysis: dict) -> ScoreItem:
        details: list[str] = []
        recs: list[str] = []
        score = 0.0
        deps: dict[str, str] = analysis.get("dependencies", {})
        config: dict = analysis.get("config", {})

        if config.get("healthcheck") or _flag(config, "health_endpoint"):
            score += MONITORING_CHECKS["health_checks"]
            details.append("Health check endpoint configured")
        else:
            recs.append("Add a health check endpoint for uptime monitoring")

        metrics_libs = {"prometheus-client", "statsd", "datadog", "newrelic", "boto3-cloudwatch"}
        if metrics_libs & set(deps.keys()):
            score += MONITORING_CHECKS["metrics_endpoint"]
            details.append("Metrics library detected")
        else:
            recs.append("Add a /metrics endpoint for observability")

        if "prometheus" in deps or "prometheus-client" in deps:
            score += MONITORING_CHECKS["prometheus"]
            details.append("Prometheus integration detected")
        else:
            recs.append("Integrate Prometheus for time-series metrics")

        if "grafana" in deps or _has_monitoring(analysis):
            score += MONITORING_CHECKS["grafana"]
            details.append("Grafana integration detected")
        else:
            recs.append("Add Grafana dashboards for visual monitoring")

        if _has_structured_logging(analysis) or "logging" in deps:
            score += MONITORING_CHECKS["logging"]
            details.append("Logging integration present")
        else:
            recs.append("Configure structured logging for production")

        alert_libs = {"alertmanager", "pdpyras", "pagerduty"}
        if alert_libs & set(deps.keys()):
            score += MONITORING_CHECKS["alerts"]
            details.append("Alerting integration detected")
        else:
            recs.append("Set up alerting for critical thresholds")

        return ScoreItem(
            dimension=ScoreDimension.MONITORING,
            score=min(score, 100.0),
            weight=_DIMENSION_WEIGHTS[ScoreDimension.MONITORING],
            details=details,
            recommendations=recs,
        )

    async def calculate_logging_score(self, analysis: dict) -> ScoreItem:
        details: list[str] = []
        recs: list[str] = []
        score = 0.0
        deps: dict[str, str] = analysis.get("dependencies", {})

        if _has_structured_logging(analysis):
            score += LOGGING_CHECKS["structured_logging"]
            details.append("Structured logging library detected")
        else:
            recs.append("Use structured logging (structlog, loguru, or json-logger)")

        log_level_config = any(
            key in analysis.get("config", {})
            for key in ("LOG_LEVEL", "log_level", "logging.level")
        )
        if log_level_config:
            score += LOGGING_CHECKS["log_levels"]
            details.append("Log level configuration present")
        else:
            recs.append("Configure per-environment log levels")

        rotation_libs = {"logrotate", "timedrotatingfilehandler", "logging.handlers"}
        if rotation_libs & set(deps.keys()):
            score += LOGGING_CHECKS["log_rotation"]
            details.append("Log rotation configured")
        else:
            recs.append("Enable log rotation to prevent disk exhaustion")

        error_libs = {"sentry-sdk", "sentry", "bugsnag", "rollbar", "raygun"}
        if error_libs & set(deps.keys()):
            score += LOGGING_CHECKS["error_tracking"]
            details.append("Error tracking service detected")
        else:
            recs.append("Integrate Sentry or similar for error tracking")

        audit_libs = {"structlog", "auditlog", "django-auditlog"}
        if audit_libs & set(deps.keys()):
            score += LOGGING_CHECKS["audit_logging"]
            details.append("Audit logging capability detected")
        else:
            recs.append("Add audit logging for security-sensitive operations")

        return ScoreItem(
            dimension=ScoreDimension.LOGGING,
            score=min(score, 100.0),
            weight=_DIMENSION_WEIGHTS[ScoreDimension.LOGGING],
            details=details,
            recommendations=recs,
        )

    async def calculate_configuration_score(self, analysis: dict) -> ScoreItem:
        details: list[str] = []
        recs: list[str] = []
        score = 0.0
        files: list[str] = analysis.get("files", [])
        config: dict = analysis.get("config", {})

        has_env = any(
            ".env" in f and f != ".env.example" for f in files
        )
        has_env_example = any(".env.example" in f for f in files)
        if has_env:
            score += CONFIGURATION_CHECKS["env_files"]
            details.append(".env file present")
        elif has_env_example:
            score += CONFIGURATION_CHECKS["env_files"] * 0.5
            details.append(".env.example present (no runtime .env committed)")
        else:
            recs.append("Create .env.example to document required variables")

        validation_libs = {"pydantic-settings", "pydantic", "marshmallow", "cerberus"}
        deps: dict[str, str] = analysis.get("dependencies", {})
        if validation_libs & set(deps.keys()) or config.get("config_validation"):
            score += CONFIGURATION_CHECKS["config_validation"]
            details.append("Configuration validation detected")
        else:
            recs.append("Add configuration validation (pydantic-settings, etc.)")

        secrets_mgr = {"aws-secrets-manager", "hashicorp-vault", "azure-keyvault"}
        if secrets_mgr & set(deps.keys()):
            score += CONFIGURATION_CHECKS["secrets_management"]
            details.append("External secrets manager detected")
        else:
            recs.append("Consider an external secrets manager for production secrets")

        env_separation = any(
            env in f for f in files for env in (".env.staging", ".env.production")
        )
        if env_separation or config.get("environments"):
            score += CONFIGURATION_CHECKS["environment_separation"]
            details.append("Environment separation detected")
        else:
            recs.append("Maintain separate .env files per environment")

        feature_libs = {"featuretools", "unleash-client", "flagsmith"}
        if feature_libs & set(deps.keys()) or config.get("feature_flags"):
            score += CONFIGURATION_CHECKS["feature_flags"]
            details.append("Feature flag system detected")
        else:
            recs.append("Introduce feature flags for progressive rollouts")

        return ScoreItem(
            dimension=ScoreDimension.CONFIGURATION,
            score=min(score, 100.0),
            weight=_DIMENSION_WEIGHTS[ScoreDimension.CONFIGURATION],
            details=details,
            recommendations=recs,
        )

    async def calculate_cicd_score(
        self, analysis: dict, cicd: dict | None = None
    ) -> ScoreItem:
        details: list[str] = []
        recs: list[str] = []
        score = 0.0
        ci_data = cicd or {}

        if _has_ci(analysis) or ci_data.get("has_pipeline"):
            score += CICD_CHECKS["ci_pipeline"]
            details.append("CI pipeline detected")
        else:
            recs.append("Set up a CI pipeline (GitHub Actions, GitLab CI, etc.)")

        if _has_tests(analysis) or ci_data.get("has_tests"):
            score += CICD_CHECKS["automated_tests"]
            details.append("Automated tests detected")
        else:
            recs.append("Add automated test suite to the CI pipeline")

        if _has_linting(analysis) or ci_data.get("has_linting"):
            score += CICD_CHECKS["linting"]
            details.append("Linting detected")
        else:
            recs.append("Include linting in CI (eslint, ruff, flake8)")

        if ci_data.get("security_scans"):
            score += CICD_CHECKS["security_scans"]
            details.append("Security scans in pipeline detected")
        else:
            recs.append("Add SAST/DAST security scans to CI")

        if ci_data.get("deploy_pipeline"):
            score += CICD_CHECKS["deployment_pipeline"]
            details.append("Deployment pipeline configured")
        else:
            recs.append("Configure an automated deployment pipeline")

        if ci_data.get("artifacts"):
            score += CICD_CHECKS["artifact_management"]
            details.append("Artifact management configured")
        else:
            recs.append("Set up artifact management for build outputs")

        return ScoreItem(
            dimension=ScoreDimension.CICD,
            score=min(score, 100.0),
            weight=_DIMENSION_WEIGHTS[ScoreDimension.CICD],
            details=details,
            recommendations=recs,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_grade(score: float) -> str:
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 50:
            return "D"
        return "F"

    @staticmethod
    def _weighted_average(dimensions: tuple[ScoreItem, ...]) -> float:
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0:
            return 0.0
        return sum(d.score * d.weight for d in dimensions) / total_weight

    @staticmethod
    def _compile_recommendations(dimensions: tuple[ScoreItem, ...]) -> list[str]:
        scored: list[tuple[float, str]] = []
        for dim in dimensions:
            for rec in dim.recommendations:
                scored.append((dim.weight, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        seen: set[str] = set()
        unique: list[str] = []
        for _, rec in scored:
            if rec not in seen:
                seen.add(rec)
                unique.append(rec)
        return unique
