"""Deployment report generator for comprehensive infrastructure analysis.

Produces structured deployment reports covering infrastructure overview,
container layout, security findings, production readiness, scaling,
rollback, and monitoring strategies.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ReportFormat(Enum):
    """Supported report output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


class SeverityLevel(Enum):
    """Severity levels for report sections and findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReadinessStatus(Enum):
    """Production readiness statuses."""

    READY = "ready"
    NEEDS_WORK = "needs_work"
    NOT_READY = "not_ready"


# ---------------------------------------------------------------------------
# Dataclasses – report building blocks
# ---------------------------------------------------------------------------


@dataclass
class ReportSection:
    """A single section within a deployment report."""

    title: str
    content: str
    severity: SeverityLevel = SeverityLevel.INFO
    order: int = 0
    subsections: list[ReportSection] = field(default_factory=list)


@dataclass
class ServiceEntry:
    """Description of a single service in the deployment."""

    name: str
    image: str
    ports: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    health_check: str | None = None


@dataclass
class Connection:
    """A connection between two services in the infrastructure diagram."""

    source: str
    target: str
    protocol: str = "tcp"
    port: int | None = None


@dataclass
class InfrastructureDiagram:
    """Visual representation of the deployment topology."""

    services: list[ServiceEntry] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    description: str = ""


@dataclass
class ContainerSpec:
    """Specification for a single container."""

    name: str
    image: str
    ports: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    restart_policy: str = "unless-stopped"
    health_check: str | None = None


@dataclass
class VolumeSpec:
    """Definition of a persistent volume."""

    name: str
    mount_path: str
    driver: str = "local"
    read_only: bool = False


@dataclass
class ScalingConfig:
    """Scaling configuration for a service."""

    service: str
    min_replicas: int = 1
    max_replicas: int = 5
    cpu_threshold: int = 70
    memory_threshold: int = 80


@dataclass
class RollbackConfig:
    """Rollback strategy configuration."""

    strategy: str = "rolling"
    max_unavailable: str = "25%"
    max_surge: str = "25%"
    revision_history: int = 10
    auto_rollback: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring and alerting configuration."""

    metrics_enabled: bool = True
    metrics_port: int = 9090
    log_driver: str = "json-file"
    log_max_size: str = "10m"
    log_max_file: int = 3
    alert_endpoints: list[str] = field(default_factory=list)
    health_check_interval: str = "30s"


@dataclass
class DeploymentPlan:
    """Complete deployment plan with all infrastructure details."""

    strategy: str = "docker_compose"
    containers: list[ContainerSpec] = field(default_factory=list)
    ports: list[int] = field(default_factory=list)
    volumes: list[VolumeSpec] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    scaling: list[ScalingConfig] = field(default_factory=list)
    rollback: RollbackConfig = field(default_factory=RollbackConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)


@dataclass
class DeploymentReport:
    """Full deployment report output."""

    project_name: str
    timestamp: str = ""
    sections: list[ReportSection] = field(default_factory=list)
    plan: DeploymentPlan = field(default_factory=DeploymentPlan)
    diagram: InfrastructureDiagram = field(default_factory=InfrastructureDiagram)
    score: int = 0
    format: ReportFormat = ReportFormat.MARKDOWN

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# DeploymentReportGenerator
# ---------------------------------------------------------------------------


class DeploymentReportGenerator:
    """Generates comprehensive deployment reports from analysis data.

    Usage::

        generator = DeploymentReportGenerator()
        report = await generator.generate(
            analysis=analysis_dict,
            security=security_dict,
            score=score_dict,
        )
        rendered = await generator.format_report(report, ReportFormat.MARKDOWN)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        analysis: dict[str, Any],
        security: dict[str, Any],
        score: dict[str, Any],
        format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> DeploymentReport:
        """Generate a full deployment report from analysis results.

        Args:
            analysis: Output from ``DeploymentAnalyzer.analyze``.
            security: Security scan findings.
            score: Readiness score breakdown.
            format: Desired output format.

        Returns:
            A populated ``DeploymentReport``.
        """
        project_name = analysis.get("project_name", "unknown-project")
        logger.info("Generating deployment report", project=project_name, format=format.value)

        sections: list[ReportSection] = []
        sections.append(await self.generate_infrastructure_section(analysis))
        sections.append(await self.generate_deployment_section(analysis))
        sections.append(await self.generate_security_section(security))
        sections.append(await self.generate_scaling_section(analysis))
        sections.append(await self.generate_rollback_section(analysis))
        sections.append(await self.generate_monitoring_section(analysis))

        plan = await self._build_deployment_plan(analysis)
        diagram = await self.generate_diagram(analysis)
        readiness_score = self._compute_score(score)

        report = DeploymentReport(
            project_name=project_name,
            sections=sections,
            plan=plan,
            diagram=diagram,
            score=readiness_score,
            format=format,
        )

        logger.info(
            "Deployment report generated",
            project=project_name,
            sections=len(sections),
            score=readiness_score,
        )
        return report

    # ------------------------------------------------------------------
    # Section generators
    # ------------------------------------------------------------------

    async def generate_infrastructure_section(
        self,
        analysis: dict[str, Any],
    ) -> ReportSection:
        """Generate the infrastructure overview section."""
        components = analysis.get("components", [])
        project_type = analysis.get("project_type", "unknown")
        docker_present = analysis.get("docker_present", False)
        compose_present = analysis.get("compose_present", False)
        ci_cd_present = analysis.get("ci_cd_present", False)

        lines: list[str] = []
        lines.append(f"**Project Type:** {project_type}")
        lines.append(f"**Docker:** {'Present' if docker_present else 'Not detected'}")
        lines.append(f"**Docker Compose:** {'Present' if compose_present else 'Not detected'}")
        lines.append(f"**CI/CD Pipeline:** {'Present' if ci_cd_present else 'Not detected'}")

        if components:
            lines.append("")
            lines.append("### Detected Components")
            for comp in components:
                if isinstance(comp, dict):
                    name = comp.get("name", comp.get("type", "unknown"))
                    version = comp.get("version", "")
                    port = comp.get("port")
                    port_str = f" (port {port})" if port else ""
                    lines.append(f"- {name} {version}{port_str}")
                else:
                    lines.append(f"- {comp}")

        env_vars = analysis.get("env_vars", {})
        if env_vars:
            lines.append("")
            lines.append(f"### Environment Variables ({len(env_vars)} required)")
            for var_name in sorted(env_vars):
                lines.append(f"- `{var_name}`")

        content = "\n".join(lines)
        severity = SeverityLevel.HIGH if not docker_present else SeverityLevel.INFO

        return ReportSection(
            title="Infrastructure Overview",
            content=content,
            severity=severity,
            order=1,
        )

    async def generate_deployment_section(
        self,
        analysis: dict[str, Any],
    ) -> ReportSection:
        """Generate the deployment strategy and container layout section."""
        strategy = analysis.get("strategy", "docker")
        services = analysis.get("services", [])
        ports = analysis.get("ports", [])
        volumes = analysis.get("volumes", [])

        lines: list[str] = []
        lines.append(f"**Recommended Strategy:** {strategy}")
        lines.append("")

        if services:
            lines.append("### Services")
            for svc in services:
                lines.append(f"- {svc}")
            lines.append("")

        if ports:
            lines.append("### Exposed Ports")
            for port in ports:
                lines.append(f"- `{port}`")
            lines.append("")

        if volumes:
            lines.append("### Volumes")
            for vol in volumes:
                lines.append(f"- {vol}")

        recommendations = analysis.get("recommendations", [])
        if recommendations:
            lines.append("")
            lines.append("### Recommendations")
            for rec in recommendations:
                lines.append(f"- {rec}")

        content = "\n".join(lines)
        return ReportSection(
            title="Deployment Strategy",
            content=content,
            severity=SeverityLevel.INFO,
            order=2,
        )

    async def generate_security_section(
        self,
        security: dict[str, Any],
    ) -> ReportSection:
        """Generate the security findings section."""
        findings = security.get("findings", [])
        secrets_exposed = security.get("secrets_exposed", [])
        vulnerabilities = security.get("vulnerabilities", [])
        overall_risk = security.get("overall_risk", "unknown")

        lines: list[str] = []
        lines.append(f"**Overall Risk Level:** {overall_risk}")
        lines.append("")

        if secrets_exposed:
            lines.append("### Exposed Secrets")
            for secret in secrets_exposed:
                if isinstance(secret, dict):
                    name = secret.get("name", "unknown")
                    location = secret.get("location", "")
                    lines.append(f"- **{name}** — {location}")
                else:
                    lines.append(f"- {secret}")
            lines.append("")

        if vulnerabilities:
            lines.append("### Vulnerabilities")
            for vuln in vulnerabilities:
                if isinstance(vuln, dict):
                    severity = vuln.get("severity", "unknown")
                    description = vuln.get("description", str(vuln))
                    lines.append(f"- [{severity.upper()}] {description}")
                else:
                    lines.append(f"- {vuln}")
            lines.append("")

        if findings:
            lines.append("### Security Findings")
            for finding in findings:
                if isinstance(finding, dict):
                    title = finding.get("title", finding.get("name", "finding"))
                    desc = finding.get("description", "")
                    sev = finding.get("severity", "info")
                    lines.append(f"- [{sev.upper()}] **{title}**: {desc}")
                else:
                    lines.append(f"- {finding}")

        if not secrets_exposed and not vulnerabilities and not findings:
            lines.append("No security findings reported.")

        content = "\n".join(lines)
        severity = (
            SeverityLevel.CRITICAL
            if secrets_exposed
            else SeverityLevel.HIGH
            if vulnerabilities
            else SeverityLevel.INFO
        )

        return ReportSection(
            title="Security Findings",
            content=content,
            severity=severity,
            order=3,
        )

    async def generate_scaling_section(
        self,
        analysis: dict[str, Any],
    ) -> ReportSection:
        """Generate the scaling strategy section."""
        services = analysis.get("services", [])
        components = analysis.get("components", [])

        lines: list[str] = []
        lines.append("### Horizontal Scaling")
        lines.append("Configure autoscaling for stateless services based on CPU/memory thresholds.")
        lines.append("")

        if services:
            lines.append("**Scalable Services:**")
            for svc in services:
                lines.append(f"- {svc}: min=1, max=5 replicas (CPU threshold: 70%)")
            lines.append("")

        lines.append("### Vertical Scaling")
        lines.append("Increase resource limits for compute-intensive services as needed.")
        lines.append("")

        has_database = any(
            (isinstance(c, dict) and c.get("type") in ("postgres", "mysql", "sqlite"))
            or (hasattr(c, "type") and str(getattr(c, "type", "")) in ("postgres", "mysql", "sqlite"))
            for c in components
        )
        if has_database:
            lines.append("### Database Scaling")
            lines.append("- Use read replicas for PostgreSQL/MySQL")
            lines.append("- Consider connection pooling (PgBouncer, ProxySQL)")
            lines.append("- Monitor connection counts and query performance")

        content = "\n".join(lines)
        return ReportSection(
            title="Scaling Strategy",
            content=content,
            severity=SeverityLevel.INFO,
            order=4,
        )

    async def generate_rollback_section(
        self,
        analysis: dict[str, Any],
    ) -> ReportSection:
        """Generate the rollback strategy section."""
        strategy = analysis.get("strategy", "docker")

        lines: list[str] = []
        lines.append("### Rollback Strategy")
        lines.append("")

        if strategy in ("docker_compose", "docker"):
            lines.append("**Strategy:** Rolling update with automatic rollback")
            lines.append("- Max unavailable: 25%")
            lines.append("- Max surge: 25%")
            lines.append("- Revision history: 10")
            lines.append("- Auto-rollback on health check failure: Enabled")
        elif strategy == "kubernetes":
            lines.append("**Strategy:** Kubernetes rolling update")
            lines.append("- maxUnavailable: 25%")
            lines.append("- maxSurge: 25%")
            lines.append("- revisionHistoryLimit: 10")
            lines.append("- Progressive delivery with canary analysis")
        else:
            lines.append(f"**Strategy:** {strategy} default rollback")
            lines.append("- Maintain previous version images")
            lines.append("- Enable automatic rollback on failure")

        lines.append("")
        lines.append("### Rollback Procedure")
        lines.append("1. Detect failure via health checks or monitoring alerts")
        lines.append("2. Pause deployment to stop further rollout")
        lines.append("3. Automatically revert to last known good revision")
        lines.append("4. Verify service health after rollback")
        lines.append("5. Notify team of rollback event and root cause")

        content = "\n".join(lines)
        return ReportSection(
            title="Rollback Strategy",
            content=content,
            severity=SeverityLevel.INFO,
            order=5,
        )

    async def generate_monitoring_section(
        self,
        analysis: dict[str, Any],
    ) -> ReportSection:
        """Generate the monitoring strategy section."""
        components = analysis.get("components", [])

        has_prometheus = any(
            (isinstance(c, dict) and c.get("type") == "prometheus")
            or (hasattr(c, "type") and str(getattr(c, "type", "")) == "prometheus")
            for c in components
        )
        has_grafana = any(
            (isinstance(c, dict) and c.get("type") == "grafana")
            or (hasattr(c, "type") and str(getattr(c, "type", "")) == "grafana")
            for c in components
        )

        lines: list[str] = []
        lines.append("### Metrics Collection")
        if has_prometheus:
            lines.append("- **Prometheus** configured for metrics scraping")
            lines.append("- Scrape interval: 15s")
            lines.append("- Retention: 15 days")
        else:
            lines.append("- Deploy Prometheus for metrics collection")
            lines.append("- Configure service-specific exporters")
        lines.append("")

        lines.append("### Dashboards")
        if has_grafana:
            lines.append("- **Grafana** dashboards available")
            lines.append("- Pre-configured panels for service health")
        else:
            lines.append("- Deploy Grafana for visualization")
            lines.append("- Create dashboards for key service metrics")
        lines.append("")

        lines.append("### Alerting")
        lines.append("- CPU usage > 80% for 5 minutes")
        lines.append("- Memory usage > 85% for 5 minutes")
        lines.append("- Disk usage > 90%")
        lines.append("- Service health check failures (3 consecutive)")
        lines.append("- Error rate > 5% over 10 minutes")
        lines.append("")

        lines.append("### Logging")
        lines.append("- Centralized log aggregation")
        lines.append("- Structured JSON logging")
        lines.append("- Log retention: 30 days")
        lines.append("- Error log alerts for critical failures")

        content = "\n".join(lines)
        return ReportSection(
            title="Monitoring Strategy",
            content=content,
            severity=SeverityLevel.INFO,
            order=6,
        )

    # ------------------------------------------------------------------
    # Diagram generator
    # ------------------------------------------------------------------

    async def generate_diagram(
        self,
        analysis: dict[str, Any],
    ) -> InfrastructureDiagram:
        """Generate an infrastructure diagram from analysis data."""
        components = analysis.get("components", [])
        services: list[ServiceEntry] = []
        connections: list[Connection] = []

        component_map: dict[str, ServiceEntry] = {}

        for comp in components:
            if isinstance(comp, dict):
                name = comp.get("name", comp.get("type", "service"))
                image = comp.get("image", f"{name}:latest")
                ports = [str(p) for p in comp.get("ports", []) if p]
                port_num = comp.get("port")
                if port_num and not ports:
                    ports = [str(port_num)]
                env = list(comp.get("env_vars", {}).keys()) if isinstance(comp.get("env_vars"), dict) else []
                depends = comp.get("depends_on", []) if isinstance(comp.get("depends_on"), list) else []

                entry = ServiceEntry(
                    name=name,
                    image=image,
                    ports=ports,
                    env_vars=env,
                    depends_on=depends,
                )
                services.append(entry)
                component_map[name.lower()] = entry
            else:
                name = str(comp)
                entry = ServiceEntry(name=name, image=f"{name}:latest")
                services.append(entry)
                component_map[name.lower()] = entry

        for entry in services:
            for dep in entry.depends_on:
                target = component_map.get(dep.lower())
                if target:
                    connections.append(
                        Connection(source=entry.name, target=target.name, protocol="tcp")
                    )

        description = self._build_diagram_description(services, connections)

        return InfrastructureDiagram(
            services=services,
            connections=connections,
            description=description,
        )

    # ------------------------------------------------------------------
    # Report formatting
    # ------------------------------------------------------------------

    async def format_report(
        self,
        report: DeploymentReport,
        format: ReportFormat,
    ) -> str:
        """Format a deployment report into the requested format.

        Args:
            report: The populated deployment report.
            format: Target format (JSON, MARKDOWN, or HTML).

        Returns:
            The formatted report string.
        """
        if format is ReportFormat.JSON:
            return await self._format_json(report)
        if format is ReportFormat.HTML:
            return await self._format_html(report)
        return await self._format_markdown(report)

    # ------------------------------------------------------------------
    # Private helpers – plan builder
    # ------------------------------------------------------------------

    async def _build_deployment_plan(
        self,
        analysis: dict[str, Any],
    ) -> DeploymentPlan:
        """Construct a ``DeploymentPlan`` from analysis data."""
        strategy = analysis.get("strategy", "docker_compose")
        services = analysis.get("services", [])
        ports = analysis.get("ports", [])
        volumes_raw = analysis.get("volumes", [])
        env_vars_raw = analysis.get("env_vars", {})

        containers: list[ContainerSpec] = []
        for svc in services:
            svc_name = svc if isinstance(svc, str) else str(svc)
            containers.append(
                ContainerSpec(
                    name=svc_name,
                    image=f"{svc_name}:latest",
                )
            )

        volumes: list[VolumeSpec] = []
        for vol in volumes_raw:
            if isinstance(vol, str):
                parts = vol.split(":")
                mount = parts[1] if len(parts) > 1 else f"/data/{parts[0]}"
                volumes.append(VolumeSpec(name=parts[0], mount_path=mount))

        secrets = [
            k for k in env_vars_raw
            if any(
                kw in k.upper()
                for kw in ("SECRET", "KEY", "TOKEN", "PASSWORD", "CREDENTIAL")
            )
        ]

        scaling = [
            ScalingConfig(service=svc if isinstance(svc, str) else str(svc))
            for svc in services
        ]

        return DeploymentPlan(
            strategy=strategy,
            containers=containers,
            ports=list(ports),
            volumes=volumes,
            secrets=secrets,
            scaling=scaling,
        )

    # ------------------------------------------------------------------
    # Private helpers – score
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_score(score: dict[str, Any]) -> int:
        """Extract or compute an overall readiness score (0-100)."""
        overall = score.get("overall", score.get("score", 0))
        try:
            value = int(overall)
            return max(0, min(100, value))
        except (TypeError, ValueError):
            return 0

    # ------------------------------------------------------------------
    # Private helpers – diagram description
    # ------------------------------------------------------------------

    @staticmethod
    def _build_diagram_description(
        services: list[ServiceEntry],
        connections: list[Connection],
    ) -> str:
        """Build a human-readable description of the infrastructure diagram."""
        parts: list[str] = []
        parts.append(f"Infrastructure consists of {len(services)} service(s)")
        if connections:
            parts.append(f"with {len(connections)} inter-service connection(s)")
        return ". ".join(parts) + "."

    # ------------------------------------------------------------------
    # Private helpers – Markdown formatter
    # ------------------------------------------------------------------

    @staticmethod
    async def _format_markdown(report: DeploymentReport) -> str:
        """Render the report as Markdown."""
        lines: list[str] = []

        lines.append(f"# Deployment Report: {report.project_name}")
        lines.append("")
        lines.append(f"**Generated:** {report.timestamp}")
        lines.append(f"**Readiness Score:** {report.score}/100")
        lines.append(f"**Strategy:** {report.plan.strategy}")
        lines.append("")

        sorted_sections = sorted(report.sections, key=lambda s: s.order)
        for section in sorted_sections:
            lines.append(f"## {section.title}")
            if section.severity is not SeverityLevel.INFO:
                lines.append(f"> Severity: {section.severity.value.upper()}")
                lines.append("")
            lines.append(section.content)
            lines.append("")

            for sub in section.subsections:
                lines.append(f"### {sub.title}")
                lines.append(sub.content)
                lines.append("")

        if report.diagram.services:
            lines.append("## Infrastructure Diagram")
            lines.append("")
            lines.append(report.diagram.description)
            lines.append("")
            lines.append("### Services")
            for svc in report.diagram.services:
                port_str = f" — ports: {', '.join(svc.ports)}" if svc.ports else ""
                lines.append(f"- **{svc.name}** ({svc.image}){port_str}")
            lines.append("")

            if report.diagram.connections:
                lines.append("### Connections")
                for conn in report.diagram.connections:
                    port_str = f":{conn.port}" if conn.port else ""
                    lines.append(f"- {conn.source} → {conn.target} ({conn.protocol}{port_str})")
                lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers – JSON formatter
    # ------------------------------------------------------------------

    @staticmethod
    async def _format_json(report: DeploymentReport) -> str:
        """Render the report as JSON."""
        data: dict[str, Any] = {
            "project_name": report.project_name,
            "timestamp": report.timestamp,
            "score": report.score,
            "plan": {
                "strategy": report.plan.strategy,
                "containers": [
                    {
                        "name": c.name,
                        "image": c.image,
                        "ports": c.ports,
                        "volumes": c.volumes,
                        "env_vars": c.env_vars,
                        "depends_on": c.depends_on,
                        "restart_policy": c.restart_policy,
                        "health_check": c.health_check,
                    }
                    for c in report.plan.containers
                ],
                "ports": report.plan.ports,
                "volumes": [
                    {
                        "name": v.name,
                        "mount_path": v.mount_path,
                        "driver": v.driver,
                        "read_only": v.read_only,
                    }
                    for v in report.plan.volumes
                ],
                "secrets": report.plan.secrets,
                "scaling": [
                    {
                        "service": s.service,
                        "min_replicas": s.min_replicas,
                        "max_replicas": s.max_replicas,
                        "cpu_threshold": s.cpu_threshold,
                        "memory_threshold": s.memory_threshold,
                    }
                    for s in report.plan.scaling
                ],
                "rollback": {
                    "strategy": report.plan.rollback.strategy,
                    "max_unavailable": report.plan.rollback.max_unavailable,
                    "max_surge": report.plan.rollback.max_surge,
                    "revision_history": report.plan.rollback.revision_history,
                    "auto_rollback": report.plan.rollback.auto_rollback,
                },
                "monitoring": {
                    "metrics_enabled": report.plan.monitoring.metrics_enabled,
                    "metrics_port": report.plan.monitoring.metrics_port,
                    "log_driver": report.plan.monitoring.log_driver,
                    "log_max_size": report.plan.monitoring.log_max_size,
                    "log_max_file": report.plan.monitoring.log_max_file,
                    "alert_endpoints": report.plan.monitoring.alert_endpoints,
                    "health_check_interval": report.plan.monitoring.health_check_interval,
                },
            },
            "diagram": {
                "services": [
                    {
                        "name": s.name,
                        "image": s.image,
                        "ports": s.ports,
                        "env_vars": s.env_vars,
                        "depends_on": s.depends_on,
                        "health_check": s.health_check,
                    }
                    for s in report.diagram.services
                ],
                "connections": [
                    {
                        "source": c.source,
                        "target": c.target,
                        "protocol": c.protocol,
                        "port": c.port,
                    }
                    for c in report.diagram.connections
                ],
                "description": report.diagram.description,
            },
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "severity": s.severity.value,
                    "order": s.order,
                }
                for s in sorted(report.sections, key=lambda x: x.order)
            ],
        }

        return json.dumps(data, indent=2, default=str)

    # ------------------------------------------------------------------
    # Private helpers – HTML formatter
    # ------------------------------------------------------------------

    @staticmethod
    async def _format_html(report: DeploymentReport) -> str:
        """Render the report as HTML."""
        parts: list[str] = []
        parts.append("<!DOCTYPE html>")
        parts.append("<html lang=\"en\">")
        parts.append("<head>")
        parts.append("  <meta charset=\"UTF-8\">")
        parts.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        parts.append(f"  <title>Deployment Report — {report.project_name}</title>")
        parts.append("  <style>")
        parts.append("    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; color: #1a1a1a; }")
        parts.append("    h1 { border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; }")
        parts.append("    h2 { color: #1e40af; margin-top: 2rem; }")
        parts.append("    h3 { color: #374151; }")
        parts.append("    .meta { color: #6b7280; margin-bottom: 1.5rem; }")
        parts.append("    .score { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-weight: bold; }")
        parts.append("    .score-high { background: #d1fae5; color: #065f46; }")
        parts.append("    .score-mid { background: #fef3c7; color: #92400e; }")
        parts.append("    .score-low { background: #fee2e2; color: #991b1b; }")
        parts.append("    .severity-critical { color: #991b1b; font-weight: bold; }")
        parts.append("    .severity-high { color: #c2410c; font-weight: bold; }")
        parts.append("    .severity-medium { color: #a16207; }")
        parts.append("    .severity-low { color: #0369a1; }")
        parts.append("    ul { padding-left: 1.5rem; }")
        parts.append("    li { margin-bottom: 0.25rem; }")
        parts.append("    code { background: #f3f4f6; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.9em; }")
        parts.append("    pre { background: #f9fafb; border: 1px solid #e5e7eb; padding: 1rem; border-radius: 8px; overflow-x: auto; }")
        parts.append("  </style>")
        parts.append("</head>")
        parts.append("<body>")
        parts.append(f"  <h1>Deployment Report — {report.project_name}</h1>")
        parts.append(f"  <div class=\"meta\">Generated: {report.timestamp} | Strategy: {report.plan.strategy}</div>")

        score = report.score
        if score >= 80:
            score_cls = "score-high"
        elif score >= 50:
            score_cls = "score-mid"
        else:
            score_cls = "score-low"
        parts.append(f"  <p>Readiness Score: <span class=\"score {score_cls}\">{score}/100</span></p>")

        sorted_sections = sorted(report.sections, key=lambda s: s.order)
        for section in sorted_sections:
            parts.append(f"  <h2>{section.title}</h2>")
            if section.severity is not SeverityLevel.INFO:
                parts.append(f"  <p class=\"severity-{section.severity.value}\">Severity: {section.severity.value.upper()}</p>")
            parts.append(f"  <div>{_markdown_to_html(section.content)}</div>")

        if report.diagram.services:
            parts.append("  <h2>Infrastructure Diagram</h2>")
            parts.append(f"  <p>{report.diagram.description}</p>")
            parts.append("  <h3>Services</h3>")
            parts.append("  <ul>")
            for svc in report.diagram.services:
                port_str = f" — {', '.join(svc.ports)}" if svc.ports else ""
                parts.append(f"    <li><strong>{svc.name}</strong> ({svc.image}){port_str}</li>")
            parts.append("  </ul>")

        parts.append("</body>")
        parts.append("</html>")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Utility – minimal Markdown to HTML converter
# ---------------------------------------------------------------------------


def _markdown_to_html(text: str) -> str:
    """Convert a subset of Markdown to HTML for the HTML report."""
    import re

    lines = text.split("\n")
    html_lines: list[str] = []

    for line in lines:
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("- **") and "**" in line[4:]:
            match = re.match(r"^- \*\*(.+?)\*\*:?\s*(.*)", line)
            if match:
                html_lines.append(f"<li><strong>{match.group(1)}</strong>: {match.group(2)}</li>")
            else:
                html_lines.append(f"<li>{line[2:]}</li>")
        elif line.startswith("- `") and line.endswith("`"):
            html_lines.append(f"<li><code>{line[3:-1]}</code></li>")
        elif line.startswith("- "):
            html_lines.append(f"<li>{line[2:]}</li>")
        elif line.startswith("> "):
            html_lines.append(f"<blockquote><em>{line[2:]}</em></blockquote>")
        elif line.strip() == "":
            html_lines.append("")
        else:
            processed = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)
            html_lines.append(f"<p>{processed}</p>")

    return "\n".join(html_lines)
