"""Security Validator for deployment configuration.

Validates the security posture of deployment artifacts including Dockerfiles,
Docker Compose files, CI/CD pipelines, and project configuration. Detects
hardcoded secrets, unsafe Docker practices, image vulnerabilities,
dependency issues, exposed ports, and production misconfigurations.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.infrastructure.notifications import notify_security_alert

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SecuritySeverity(str, Enum):
    """Severity level of a security issue."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityCategory(str, Enum):
    """Category of security check."""

    SECRETS = "secrets"
    ENVIRONMENT = "environment"
    DOCKER = "docker"
    DEPENDENCIES = "dependencies"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    IMAGE = "image"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SecurityIssue:
    """A single security issue detected during validation."""

    category: SecurityCategory
    severity: SecuritySeverity
    title: str
    description: str
    file_path: str
    line_number: int | None = None
    recommendation: str = ""


@dataclass
class SecurityValidation:
    """Result of a full security validation run."""

    issues: list[SecurityIssue] = field(default_factory=list)
    score: float = 100.0
    categories_checked: list[SecurityCategory] = field(default_factory=list)
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0


# ---------------------------------------------------------------------------
# Constants – secret / credential patterns
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[dict[str, Any]] = [
    {
        "pattern": re.compile(
            r"""(?:password|passwd|pwd)\s*[:=]\s*['\"][^'"]+['\"]""",
            re.IGNORECASE,
        ),
        "title": "Hardcoded Password",
        "description": "A password literal is embedded directly in source code.",
        "recommendation": "Move passwords to environment variables or a secrets manager.",
    },
    {
        "pattern": re.compile(
            r"""(?:api_key|apikey|api[-_]?secret)\s*[:=]\s*['\"][^'"]+['\"]""",
            re.IGNORECASE,
        ),
        "title": "Hardcoded API Key",
        "description": "An API key is embedded directly in source code.",
        "recommendation": "Use environment variables or a vault service for API keys.",
    },
    {
        "pattern": re.compile(
            r"""(?:secret|secret_key|SECRET_KEY)\s*[:=]\s*['\"][^'"]+['\"]""",
            re.IGNORECASE,
        ),
        "title": "Hardcoded Secret",
        "description": "A secret value is embedded directly in source code.",
        "recommendation": "Use environment variables or a secrets manager.",
    },
    {
        "pattern": re.compile(
            r"""(?:token|auth_token|access_token)\s*[:=]\s*['\"][^'"]+['\"]""",
            re.IGNORECASE,
        ),
        "title": "Hardcoded Token",
        "description": "An authentication token is embedded directly in source code.",
        "recommendation": "Store tokens in environment variables.",
    },
    {
        "pattern": re.compile(
            r"""(?:AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID)\s*[:=]\s*['\"][^'"]+['\"]""",
        ),
        "title": "Hardcoded AWS Credentials",
        "description": "AWS credentials are embedded in source code.",
        "recommendation": "Use IAM roles, environment variables, or AWS Secrets Manager.",
    },
    {
        "pattern": re.compile(
            r"""(?:DATABASE_URL|MONGO_URI|REDIS_URL)\s*[:=]\s*['\"][^'"]+['\"]""",
        ),
        "title": "Hardcoded Connection String",
        "description": "A database or service connection string is hardcoded.",
        "recommendation": "Use environment variables for connection strings.",
    },
]

_SENSITIVE_PORTS: dict[int, str] = {
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    110: "POP3",
    135: "MSRPC",
    139: "NetBIOS",
    445: "SMB",
    1433: "MSSQL",
    1434: "MSSQL Browser",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    11211: "Memcached",
    27017: "MongoDB",
}


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class SecurityValidator:
    """Validates deployment security configuration.

    Usage::

        validator = SecurityValidator()
        result = await validator.validate(
            project_path="/path/to/project",
            files=["Dockerfile", "docker-compose.yml", ".env", ...],
        )
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def validate(
        self,
        project_path: str,
        files: list[str],
        analysis: dict[str, Any] | None = None,
    ) -> SecurityValidation:
        """Run a full security validation across all categories.

        Args:
            project_path: Root directory of the project.
            files: List of relative file paths in the repository.
            analysis: Optional deployment analysis dict from
                ``DeploymentAnalyzer``.

        Returns:
            A ``SecurityValidation`` summarising all detected issues.
        """
        logger.info(
            "Starting security validation: project_path=%s, file_count=%d",
            project_path,
            len(files),
        )

        all_issues: list[SecurityIssue] = []
        categories_checked: list[SecurityCategory] = []

        # Run each check category
        checks = [
            (SecurityCategory.SECRETS, self.check_secrets),
            (SecurityCategory.ENVIRONMENT, self.check_environment),
            (SecurityCategory.DOCKER, self.check_docker_security),
            (SecurityCategory.DEPENDENCIES, self.check_dependencies),
            (SecurityCategory.NETWORK, self.check_network),
            (SecurityCategory.CONFIGURATION, self.check_configuration),
            (SecurityCategory.IMAGE, self.check_image_security),
        ]

        for category, check_fn in checks:
            try:
                if category == SecurityCategory.NETWORK:
                    issues = await check_fn(project_path, files, analysis)
                else:
                    issues = await check_fn(project_path, files)
                all_issues.extend(issues)
                categories_checked.append(category)
            except Exception as exc:
                logger.error("Security check %s failed: %s", category.value, exc)

        validation = self._build_validation(all_issues, categories_checked)

        if validation.critical_count > 0:
            notify_security_alert(
                os.getenv("SMTP_FROM_EMAIL", "admin@forgeai.dev"),
                f"{validation.critical_count} critical security issue(s) found",
                f"Score: {validation.score:.0f}/100. Issues: {validation.critical_count} critical, {validation.high_count} high.",
            )

        logger.info(
            "Security validation complete: score=%.1f, total_issues=%d, "
            "critical=%d, high=%d, medium=%d, low=%d",
            validation.score,
            validation.total_issues,
            validation.critical_count,
            validation.high_count,
            validation.medium_count,
            validation.low_count,
        )

        return validation

    # ------------------------------------------------------------------
    # Secrets checks
    # ------------------------------------------------------------------

    async def check_secrets(
        self,
        project_path: str,
        files: list[str],
    ) -> list[SecurityIssue]:
        """Check for hardcoded secrets in source files.

        Scans source files for embedded passwords, API keys, tokens, and
        connection strings.  Also checks that a ``.env`` file (or template)
        exists and that ``.env`` is listed in ``.gitignore``.
        """
        issues: list[SecurityIssue] = []
        root = Path(project_path)

        # 1. Scan source files for hardcoded secrets
        source_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx",
            ".yaml", ".yml", ".json", ".toml",
            ".env", ".cfg", ".ini", ".conf",
            ".sh", ".bash",
        }

        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext not in source_extensions:
                continue

            fpath = root / fname
            if not fpath.exists():
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            lines = content.splitlines()
            for line_num, line in enumerate(lines, start=1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue

                for secret in _SECRET_PATTERNS:
                    if secret["pattern"].search(line):
                        issues.append(
                            SecurityIssue(
                                category=SecurityCategory.SECRETS,
                                severity=SecuritySeverity.CRITICAL,
                                title=secret["title"],
                                description=secret["description"],
                                file_path=fname,
                                line_number=line_num,
                                recommendation=secret["recommendation"],
                            )
                        )

        # 2. Check for missing .env file
        env_files = {".env", ".env.example", ".env.template", ".env.sample"}
        has_env = any(
            (root / ef).exists() for ef in env_files
        )
        if not has_env:
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.SECRETS,
                    severity=SecuritySeverity.MEDIUM,
                    title="No .env File Found",
                    description=(
                        "No .env, .env.example, or .env.template file found. "
                        "Environment variables may not be documented."
                    ),
                    file_path="",
                    recommendation=(
                        "Add a .env.example file documenting required "
                        "environment variables with placeholder values."
                    ),
                )
            )

        # 3. Check .gitignore for .env
        gitignore = root / ".gitignore"
        if gitignore.exists():
            try:
                gi_content = gitignore.read_text(
                    encoding="utf-8", errors="ignore"
                ).lower()
                if ".env" not in gi_content:
                    issues.append(
                        SecurityIssue(
                            category=SecurityCategory.SECRETS,
                            severity=SecuritySeverity.HIGH,
                            title=".env Not in .gitignore",
                            description=(
                                "The .env file is not listed in .gitignore "
                                "and may be committed to version control."
                            ),
                            file_path=".gitignore",
                            recommendation="Add .env to .gitignore to prevent accidental commits.",
                        )
                    )
            except OSError:
                pass
        else:
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.SECRETS,
                    severity=SecuritySeverity.MEDIUM,
                    title="Missing .gitignore",
                    description="No .gitignore file found in the project root.",
                    file_path=".gitignore",
                    recommendation="Create a .gitignore that excludes .env, secrets, and build artifacts.",
                )
            )

        return issues

    # ------------------------------------------------------------------
    # Environment variable checks
    # ------------------------------------------------------------------

    async def check_environment(
        self,
        project_path: str,
        files: list[str],
    ) -> list[SecurityIssue]:
        """Check environment variable configuration.

        Validates that environment variables are properly externalised,
        default values are not sensitive, and production configurations
        do not rely on development-only variables.
        """
        issues: list[SecurityIssue] = []
        root = Path(project_path)

        env_template_names = {
            ".env.example",
            ".env.template",
            ".env.sample",
        }

        # Parse env template files
        env_vars: dict[str, str] = {}
        for tpl_name in env_template_names:
            tpl_path = root / tpl_name
            if tpl_path.exists():
                env_vars.update(self._parse_env_file(tpl_path))

        # Check for unsafe defaults in env templates
        unsafe_defaults = re.compile(
            r"""(?:password|secret|token|key)\s*=\s*(?!$|\s*#)""",
            re.IGNORECASE,
        )
        for var_name, var_value in env_vars.items():
            if var_value and unsafe_defaults.search(f"{var_name}={var_value}"):
                # Ignore placeholder strings
                placeholder_values = {
                    "", "changeme", "your-password", "your-secret",
                    "your-api-key", "xxx", "placeholder", "todo", "fixme",
                    "replace-me", "set-me",
                }
                if var_value.lower() not in placeholder_values:
                    issues.append(
                        SecurityIssue(
                            category=SecurityCategory.ENVIRONMENT,
                            severity=SecuritySeverity.HIGH,
                            title="Sensitive Default in Env Template",
                            description=(
                                f"Variable '{var_name}' appears to have a "
                                f"real value '{var_value}' in a template file."
                            ),
                            file_path=tpl_name,
                            recommendation=(
                                "Use placeholder values in env templates. "
                                "Real secrets belong only in deployment env."
                            ),
                        )
                    )

        # Check for DEBUG / FLASK_DEBUG / NODE_ENV in production configs
        prod_config_patterns = [
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        ]
        debug_pattern = re.compile(
            r"""(?:DEBUG|FLASK_DEBUG|NODE_ENV)\s*[:=]\s*['\"]?(?:true|1|yes|on)['\"]?""",
            re.IGNORECASE,
        )
        for fname in files:
            fpath = root / fname
            if not fpath.exists():
                continue
            fname_lower = fname.lower()
            if not any(pc in fname_lower for pc in prod_config_patterns):
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for line_num, line in enumerate(content.splitlines(), start=1):
                if debug_pattern.search(line):
                    issues.append(
                        SecurityIssue(
                            category=SecurityCategory.ENVIRONMENT,
                            severity=SecuritySeverity.HIGH,
                            title="Debug Mode Enabled in Production Config",
                            description=(
                                "Debug mode appears enabled in a production "
                                "deployment configuration file."
                            ),
                            file_path=fname,
                            line_number=line_num,
                            recommendation=(
                                "Set DEBUG=false (or NODE_ENV=production) "
                                "in production configurations."
                            ),
                        )
                    )

        # Check for missing critical env vars without defaults
        critical_env_vars = {"DATABASE_URL", "SECRET_KEY", "API_KEY"}
        declared_vars = set(env_vars.keys())
        for cname in critical_env_vars:
            # Check if it is referenced in source but not in templates
            referenced = False
            in_template = cname in declared_vars
            for fname in files:
                if not any(
                    fname.endswith(ext)
                    for ext in (".py", ".js", ".ts", ".yaml", ".yml", ".toml")
                ):
                    continue
                fpath = root / fname
                if not fpath.exists():
                    continue
                try:
                    content = fpath.read_text(
                        encoding="utf-8", errors="ignore"
                    )[:131072]
                except OSError:
                    continue
                if cname in content:
                    referenced = True
                    break

            if referenced and not in_template:
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.ENVIRONMENT,
                        severity=SecuritySeverity.MEDIUM,
                        title=f"Missing Env Template for {cname}",
                        description=(
                            f"'{cname}' is referenced in code but not "
                            f"declared in any .env template file."
                        ),
                        file_path="",
                        recommendation=(
                            f"Add '{cname}' to your .env.example with "
                            f"a placeholder value."
                        ),
                    )
                )

        return issues

    # ------------------------------------------------------------------
    # Docker security checks
    # ------------------------------------------------------------------

    async def check_docker_security(
        self,
        project_path: str,
        files: list[str],
    ) -> list[SecurityIssue]:
        """Check Dockerfile and Docker Compose security.

        Validates best practices such as running as non-root, health
        checks, limited port exposure, and secrets handling.
        """
        issues: list[SecurityIssue] = []
        root = Path(project_path)

        # --- Dockerfile checks ---
        for fname in files:
            fname_lower = fname.lower()
            if not (
                fname_lower.startswith("dockerfile")
                or fname_lower.endswith(".dockerfile")
            ):
                continue

            fpath = root / fname
            if not fpath.exists():
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            lines = content.splitlines()
            issues.extend(self._check_dockerfile(lines, fname))

        # --- Docker Compose checks ---
        compose_files = [
            f for f in files
            if f.lower() in {
                "docker-compose.yml",
                "docker-compose.yaml",
                "compose.yml",
                "compose.yaml",
            }
        ]
        for fname in compose_files:
            fpath = root / fname
            if not fpath.exists():
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            lines = content.splitlines()
            issues.extend(self._check_compose(lines, fname))

        return issues

    async def check_image_security(
        self,
        project_path: str,
        files: list[str],
    ) -> list[SecurityIssue]:
        """Check Docker image tag best practices.

        Detects usage of ``:latest`` tags, unpinned versions, and
        images from untrusted registries.
        """
        issues: list[SecurityIssue] = []
        root = Path(project_path)

        for fname in files:
            fname_lower = fname.lower()
            is_dockerfile = (
                fname_lower.startswith("dockerfile")
                or fname_lower.endswith(".dockerfile")
            )
            is_compose = fname_lower in {
                "docker-compose.yml",
                "docker-compose.yaml",
                "compose.yml",
                "compose.yaml",
            }
            if not is_dockerfile and not is_compose:
                continue

            fpath = root / fname
            if not fpath.exists():
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            lines = content.splitlines()
            issues.extend(self._check_image_tags(lines, fname))

        return issues

    # ------------------------------------------------------------------
    # Dependency checks
    # ------------------------------------------------------------------

    async def check_dependencies(
        self,
        project_path: str,
        files: list[str],
    ) -> list[SecurityIssue]:
        """Check for dependency management issues.

        Flags missing lock files, overly broad version ranges, and
        known-insecure packages.
        """
        issues: list[SecurityIssue] = []
        root = Path(project_path)

        # Check for requirements.txt
        req = root / "requirements.txt"
        if req.exists():
            issues.extend(self._check_python_deps(root, files))

        # Check for package.json
        pkg = root / "package.json"
        if pkg.exists():
            issues.extend(self._check_node_deps(root, files))

        # Check for lock files
        lock_files = {
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "Pipfile.lock",
            "poetry.lock",
            "uv.lock",
        }
        has_lock = any((root / lf).exists() for lf in lock_files)
        has_pkg = req.exists() or pkg.exists() or (root / "pyproject.toml").exists()
        if has_pkg and not has_lock:
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.DEPENDENCIES,
                    severity=SecuritySeverity.MEDIUM,
                    title="No Dependency Lock File",
                    description=(
                        "No lock file found (package-lock.json, yarn.lock, "
                        "poetry.lock, etc.). Builds may not be reproducible."
                    ),
                    file_path="",
                    recommendation=(
                        "Generate and commit a lock file to ensure "
                        "deterministic builds."
                    ),
                )
            )

        return issues

    async def check_network(
        self,
        project_path: str,
        files: list[str],
        analysis: dict[str, Any] | None = None,
    ) -> list[SecurityIssue]:
        """Check network configuration and port exposure.

        Flags sensitive ports exposed to the host, overly permissive
        network bindings (``0.0.0.0``), and missing network policies
        for multi-service deployments.
        """
        issues: list[SecurityIssue] = []
        root = Path(project_path)

        # Scan Dockerfiles for EXPOSE directives
        for fname in files:
            fname_lower = fname.lower()
            if not (
                fname_lower.startswith("dockerfile")
                or fname_lower.endswith(".dockerfile")
            ):
                continue

            fpath = root / fname
            if not fpath.exists():
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for line_num, line in enumerate(content.splitlines(), start=1):
                stripped = line.strip()
                if stripped.upper().startswith("EXPOSE"):
                    ports = re.findall(r"\b(\d+)\b", stripped)
                    for port_str in ports:
                        port = int(port_str)
                        if port in _SENSITIVE_PORTS:
                            issues.append(
                                SecurityIssue(
                                    category=SecurityCategory.NETWORK,
                                    severity=SecuritySeverity.HIGH,
                                    title=f"Sensitive Port Exposed: {port}",
                                    description=(
                                        f"Port {port} ({_SENSITIVE_PORTS[port]}) "
                                        f"is exposed in {fname}. This service "
                                        f"should typically not be publicly accessible."
                                    ),
                                    file_path=fname,
                                    line_number=line_num,
                                    recommendation=(
                                        f"Avoid exposing port {port} externally. "
                                        f"If required, restrict access with "
                                        f"network policies or firewalls."
                                    ),
                                )
                            )

        # Scan compose files for port mappings
        compose_names = {
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        }
        for fname in files:
            if fname.lower() not in compose_names:
                continue

            fpath = root / fname
            if not fpath.exists():
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for line_num, line in enumerate(content.splitlines(), start=1):
                # Match port mappings like "8080:80", "127.0.0.1:5432:5432"
                port_match = re.search(r"""["']?(\d+:\d+)["']?""", line)
                if port_match:
                    mapping = port_match.group(1)
                    parts = mapping.split(":")
                    host_port = int(parts[0])
                    if host_port in _SENSITIVE_PORTS:
                        # Check if bound to 127.0.0.1
                        bound_localhost = "127.0.0.1" in line
                        if not bound_localhost:
                            issues.append(
                                SecurityIssue(
                                    category=SecurityCategory.NETWORK,
                                    severity=SecuritySeverity.HIGH,
                                    title=(
                                        f"Sensitive Port Mapped: {host_port}"
                                    ),
                                    description=(
                                        f"Port {host_port} ({_SENSITIVE_PORTS[host_port]}) "
                                        f"is mapped on all interfaces in {fname}."
                                    ),
                                    file_path=fname,
                                    line_number=line_num,
                                    recommendation=(
                                        f"Bind port {host_port} to 127.0.0.1 "
                                        f"or use a reverse proxy."
                                    ),
                                )
                            )

        # Check for network policy in multi-service compose
        has_compose = any(fname.lower() in compose_names for fname in files)
        if has_compose:
            # Detect multiple services
            for fname in files:
                if fname.lower() not in compose_names:
                    continue
                fpath = root / fname
                if not fpath.exists():
                    continue
                try:
                    content = fpath.read_text(
                        encoding="utf-8", errors="ignore"
                    )
                except OSError:
                    continue
                service_count = content.lower().count("\nservices:") + (
                    1 if content.lower().startswith("services:") else 0
                )
                if service_count <= 1:
                    # Count top-level service keys
                    in_services = False
                    svc_count = 0
                    for line in content.splitlines():
                        if line.strip().startswith("services:"):
                            in_services = True
                            continue
                        if in_services:
                            if line and not line.startswith(" ") and not line.startswith("\t"):
                                in_services = False
                            elif line.strip() and not line.strip().startswith("#"):
                                if not line.startswith(" ") and not line.startswith("\t"):
                                    pass
                                else:
                                    indent = len(line) - len(line.lstrip())
                                    if indent <= 2:
                                        svc_count += 1
                    if svc_count > 1:
                        has_networks = "networks:" in content.lower()
                        if not has_networks:
                            issues.append(
                                SecurityIssue(
                                    category=SecurityCategory.NETWORK,
                                    severity=SecuritySeverity.LOW,
                                    title="No Network Isolation Defined",
                                    description=(
                                        f"Multiple services detected in {fname} "
                                        f"but no custom network isolation is defined."
                                    ),
                                    file_path=fname,
                                    recommendation=(
                                        "Define explicit Docker networks to "
                                        "isolate services and limit lateral movement."
                                    ),
                                )
                            )
                break

        return issues

    # ------------------------------------------------------------------
    # Configuration checks
    # ------------------------------------------------------------------

    async def check_configuration(
        self,
        project_path: str,
        files: list[str],
    ) -> list[SecurityIssue]:
        """Check general security configuration.

        Validates CORS settings, TLS usage, rate limiting, logging
        configuration, and other production hardening measures.
        """
        issues: list[SecurityIssue] = []
        root = Path(project_path)

        for fname in files:
            if not any(
                fname.endswith(ext)
                for ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".yaml", ".yml")
            ):
                continue

            fpath = root / fname
            if not fpath.exists():
                continue

            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            lines = content.splitlines()

            # CORS misconfiguration
            issues.extend(self._check_cors(lines, fname))

            # Debug/logging configuration
            issues.extend(self._check_debug_config(lines, fname))

            # TLS / HTTPS enforcement
            issues.extend(self._check_tls(lines, fname))

        return issues

    # ------------------------------------------------------------------
    # Private helpers – Dockerfile checks
    # ------------------------------------------------------------------

    def _check_dockerfile(
        self, lines: list[str], file_path: str
    ) -> list[SecurityIssue]:
        """Validate a Dockerfile for security best practices."""
        issues: list[SecurityIssue] = []
        content = "\n".join(lines)

        # 1. Running as root
        has_user = any(
            line.strip().upper().startswith("USER ") for line in lines
        )
        if not has_user:
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.DOCKER,
                    severity=SecuritySeverity.HIGH,
                    title="Container Runs as Root",
                    description=(
                        "No USER instruction found in Dockerfile. The "
                        "container will run as root by default."
                    ),
                    file_path=file_path,
                    recommendation=(
                        "Add a USER instruction to run the application "
                        "as a non-root user."
                    ),
                )
            )

        # 2. Missing health check
        has_healthcheck = any(
            line.strip().upper().startswith("HEALTHCHECK ") for line in lines
        )
        if not has_healthcheck:
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.DOCKER,
                    severity=SecuritySeverity.MEDIUM,
                    title="No Health Check Defined",
                    description=(
                        "No HEALTHCHECK instruction found. Orchestrators "
                        "cannot determine container health."
                    ),
                    file_path=file_path,
                    recommendation=(
                        "Add a HEALTHCHECK instruction to enable "
                        "automatic health monitoring."
                    ),
                )
            )

        # 3. Sensitive files not excluded via .dockerignore check
        dockerignore = Path(file_path).parent / ".dockerignore"
        if not dockerignore.exists():
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.DOCKER,
                    severity=SecuritySeverity.LOW,
                    title="No .dockerignore File",
                    description=(
                        "No .dockerignore file found. Sensitive files "
                        "or build artifacts may be copied into the image."
                    ),
                    file_path=".dockerignore",
                    recommendation=(
                        "Create a .dockerignore that excludes .git, "
                        ".env, node_modules, __pycache__, and secrets."
                    ),
                )
            )

        # 4. ADD used instead of COPY
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.upper().startswith("ADD ") and not any(
                ext in stripped.lower()
                for ext in (".tar", ".gz", ".bz2", ".xz", ".zip")
            ):
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.DOCKER,
                        severity=SecuritySeverity.LOW,
                        title="Use COPY Instead of ADD",
                        description=(
                            "ADD is used where COPY would suffice. ADD "
                            "can fetch remote URLs and unpack archives "
                            "unexpectedly."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation="Prefer COPY over ADD unless archive extraction is needed.",
                    )
                )
                break

        # 5. Secrets passed via build arguments
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.upper().startswith("ARG "):
                arg_name = stripped[4:].split("=")[0].strip().upper()
                secret_indicators = {
                    "PASSWORD", "SECRET", "TOKEN", "API_KEY", "CREDENTIAL",
                    "PRIVATE_KEY", "ACCESS_KEY",
                }
                if any(si in arg_name for si in secret_indicators):
                    issues.append(
                        SecurityIssue(
                            category=SecurityCategory.DOCKER,
                            severity=SecuritySeverity.HIGH,
                            title="Secret Passed as Build Argument",
                            description=(
                                f"Build argument '{arg_name}' appears to "
                                f"contain a secret. Build args are cached "
                                f"in image layers."
                            ),
                            file_path=file_path,
                            line_number=line_num,
                            recommendation=(
                                "Use BuildKit secrets (--mount=type=secret) "
                                "or multi-stage builds to avoid leaking "
                                "secrets in image layers."
                            ),
                        )
                    )

        return issues

    # ------------------------------------------------------------------
    # Private helpers – Compose checks
    # ------------------------------------------------------------------

    def _check_compose(
        self, lines: list[str], file_path: str
    ) -> list[SecurityIssue]:
        """Validate a Docker Compose file for security best practices."""
        issues: list[SecurityIssue] = []
        content = "\n".join(lines)

        # 1. Privileged mode
        for line_num, line in enumerate(lines, start=1):
            if "privileged:" in line and "true" in line.lower():
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.DOCKER,
                        severity=SecuritySeverity.CRITICAL,
                        title="Privileged Container Mode Enabled",
                        description=(
                            "A service is running in privileged mode, "
                            "granting full host access."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=(
                            "Remove privileged: true and grant only "
                            "required capabilities via cap_add."
                        ),
                    )
                )

        # 2. Host network mode
        for line_num, line in enumerate(lines, start=1):
            if "network_mode:" in line and "host" in line.lower():
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.DOCKER,
                        severity=SecuritySeverity.HIGH,
                        title="Host Network Mode",
                        description=(
                            "A service uses host network mode, bypassing "
                            "Docker network isolation."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=(
                            "Use bridge or custom networks instead of "
                            "host network mode."
                        ),
                    )
                )

        # 3. Writable root filesystem not enforced
        # (Cannot fully validate without a linter, but flag if no read_only)
        has_read_only = "read_only:" in content.lower()
        if not has_read_only:
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.DOCKER,
                    severity=SecuritySeverity.LOW,
                    title="Root Filesystem Not Set to Read-Only",
                    description=(
                        "No read_only: true found in compose file. "
                        "Writable root filesystems increase attack surface."
                    ),
                    file_path=file_path,
                    recommendation=(
                        "Set read_only: true on services and use "
                        "tmpfs for writable directories."
                    ),
                )
            )

        # 4. Capabilities
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.lower().startswith("cap_add:"):
                if "sys_admin" in content.lower() or "all" in stripped.lower():
                    issues.append(
                        SecurityIssue(
                            category=SecurityCategory.DOCKER,
                            severity=SecuritySeverity.HIGH,
                            title="Overly Permissive Capabilities",
                            description=(
                                "Dangerous Linux capabilities (SYS_ADMIN or ALL) "
                                "are granted to a service."
                            ),
                            file_path=file_path,
                            line_number=line_num,
                            recommendation=(
                                "Grant only the minimum required capabilities."
                            ),
                        )
                    )

        return issues

    # ------------------------------------------------------------------
    # Private helpers – Image tag checks
    # ------------------------------------------------------------------

    def _check_image_tags(
        self, lines: list[str], file_path: str
    ) -> list[SecurityIssue]:
        """Check Docker image tags for :latest and missing pinning."""
        issues: list[SecurityIssue] = []
        trusted_registries = {
            "docker.io",
            "ghcr.io",
            "gcr.io",
            "quay.io",
            "mcr.microsoft.com",
            "registry.access.redhat.com",
        }

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # FROM instruction in Dockerfile
            from_match = re.match(
                r"^FROM\s+([\w./\-:]+)", stripped, re.IGNORECASE
            )
            # image: in compose
            image_match = re.match(
                r"""image:\s*['"]?([\w./\-:]+)['"]?""", stripped
            )

            image_ref = None
            if from_match:
                image_ref = from_match.group(1)
            elif image_match:
                image_ref = image_match.group(1)

            if not image_ref:
                continue

            # Check :latest tag
            if image_ref.endswith(":latest"):
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.IMAGE,
                        severity=SecuritySeverity.MEDIUM,
                        title="Using :latest Tag",
                        description=(
                            f"Image '{image_ref}' uses the :latest tag, "
                            f"which is non-deterministic and may introduce "
                            f"unexpected changes."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=(
                            "Pin images to a specific version or digest "
                            "(e.g., python:3.12-slim)."
                        ),
                    )
                )

            # Check for images without any tag
            if ":" not in image_ref and "@" not in image_ref:
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.IMAGE,
                        severity=SecuritySeverity.MEDIUM,
                        title="Image Missing Version Tag",
                        description=(
                            f"Image '{image_ref}' has no version tag, "
                            f"which defaults to :latest."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=(
                            "Pin to a specific version tag or digest."
                        ),
                    )
                )

            # Check for untrusted registries
            if "/" in image_ref:
                registry = image_ref.split("/")[0]
                if (
                    "." in registry
                    and registry not in trusted_registries
                    and not registry.startswith("localhost")
                ):
                    issues.append(
                        SecurityIssue(
                            category=SecurityCategory.IMAGE,
                            severity=SecuritySeverity.LOW,
                            title="Untrusted Image Registry",
                            description=(
                                f"Image '{image_ref}' is pulled from "
                                f"registry '{registry}' which is not in "
                                f"the list of trusted registries."
                            ),
                            file_path=file_path,
                            line_number=line_num,
                            recommendation=(
                                "Use images from trusted, verified "
                                "registries only."
                            ),
                        )
                    )

        return issues

    # ------------------------------------------------------------------
    # Private helpers – Dependency checks
    # ------------------------------------------------------------------

    def _check_python_deps(
        self, root: Path, files: list[str]
    ) -> list[SecurityIssue]:
        """Check Python dependency configuration."""
        issues: list[SecurityIssue] = []
        req = root / "requirements.txt"
        if not req.exists():
            return issues

        try:
            content = req.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return issues

        lines = content.splitlines()
        unpinned: list[str] = []
        overly_broad: list[str] = []

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("-"):
                continue

            if "==" not in stripped:
                unpinned.append(stripped)
            elif ">=" in stripped and "<" not in stripped:
                overly_broad.append(stripped)

        if unpinned:
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.DEPENDENCIES,
                    severity=SecuritySeverity.MEDIUM,
                    title="Unpinned Python Dependencies",
                    description=(
                        f"{len(unpinned)} dependencies in requirements.txt "
                        f"are not pinned to exact versions."
                    ),
                    file_path="requirements.txt",
                    recommendation=(
                        "Pin all dependencies with == to ensure "
                        "reproducible builds."
                    ),
                )
            )

        # Check for known-insecure packages
        insecure_python = {
            "django<3.2": "Django < 3.2 has known security vulnerabilities.",
            "flask<2.0": "Flask < 2.0 may have security issues.",
            "requests<2.28": "Older requests versions have security fixes.",
            "cryptography<3.4": "Older cryptography versions have vulnerabilities.",
            "pyyaml<5.4": "PyYAML < 5.4 is vulnerable to arbitrary code execution.",
            "jinja2<3.1": "Jinja2 < 3.1 has known template injection vulnerabilities.",
        }

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip().lower()
            for pkg, msg in insecure_python.items():
                pkg_name = pkg.split("<")[0].split(">")[0].split("=")[0]
                if stripped.startswith(pkg_name) and pkg.split("<")[1] in stripped:
                    issues.append(
                        SecurityIssue(
                            category=SecurityCategory.DEPENDENCIES,
                            severity=SecuritySeverity.HIGH,
                            title=f"Insecure Python Package: {pkg_name}",
                            description=msg,
                            file_path="requirements.txt",
                            line_number=line_num,
                            recommendation=f"Upgrade {pkg_name} to the latest stable version.",
                        )
                    )

        return issues

    def _check_node_deps(
        self, root: Path, files: list[str]
    ) -> list[SecurityIssue]:
        """Check Node.js dependency configuration."""
        issues: list[SecurityIssue] = []
        pkg_path = root / "package.json"
        if not pkg_path.exists():
            return issues

        import json as _json

        try:
            data = _json.loads(
                pkg_path.read_text(encoding="utf-8", errors="ignore")
            )
        except (_json.JSONDecodeError, OSError):
            return issues

        all_deps: dict[str, str] = {}
        all_deps.update(data.get("dependencies", {}))
        all_deps.update(data.get("devDependencies", {}))

        # Check for overly broad version ranges
        broad_patterns = re.compile(r"^[~^*]|^\d+\.\*$")
        broad_deps = [
            name for name, ver in all_deps.items()
            if broad_patterns.match(ver)
        ]

        if broad_deps:
            sample = broad_deps[:5]
            issues.append(
                SecurityIssue(
                    category=SecurityCategory.DEPENDENCIES,
                    severity=SecuritySeverity.MEDIUM,
                    title="Overly Broad Node.js Dependency Ranges",
                    description=(
                        f"{len(broad_deps)} dependencies use broad version "
                        f"ranges ({', '.join(sample)}{'...' if len(broad_deps) > 5 else ''})."
                    ),
                    file_path="package.json",
                    recommendation=(
                        "Use exact versions or lock files to ensure "
                        "deterministic installs."
                    ),
                )
            )

        # Known insecure packages
        insecure_node = {
            "event-stream": "event-stream 3.3.6 contained malicious code.",
            "flatmap-stream": "flatmap-stream was a supply chain attack vector.",
            "ua-parser-js": "ua-parser-js had malicious versions published.",
            "colors-js": "colors-js contained intentional breaking code.",
            "faker-js": "faker-js was sabotaged by its maintainer.",
        }

        for name in all_deps:
            if name in insecure_node:
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.DEPENDENCIES,
                        severity=SecuritySeverity.CRITICAL,
                        title=f"Insecure Node Package: {name}",
                        description=insecure_node[name],
                        file_path="package.json",
                        recommendation=f"Remove or replace {name} with a maintained alternative.",
                    )
                )

        return issues

    # ------------------------------------------------------------------
    # Private helpers – Configuration checks
    # ------------------------------------------------------------------

    def _check_cors(
        self, lines: list[str], file_path: str
    ) -> list[SecurityIssue]:
        """Check for overly permissive CORS configuration."""
        issues: list[SecurityIssue] = []

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Wildcard origin
            if re.search(
                r"""(?:allow_origins|origins)\s*[:=]\s*['\"]?\*['\"]?""",
                stripped,
                re.IGNORECASE,
            ):
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.CONFIGURATION,
                        severity=SecuritySeverity.HIGH,
                        title="CORS Wildcard Origin",
                        description=(
                            "CORS is configured to allow all origins ('*'). "
                            "This permits any website to make requests."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=(
                            "Restrict CORS to specific trusted origins."
                        ),
                    )
                )

            # Allow all methods
            if re.search(
                r"""allow_methods\s*[:=]\s*['\"]?\*['\"]?""",
                stripped,
                re.IGNORECASE,
            ):
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.CONFIGURATION,
                        severity=SecuritySeverity.MEDIUM,
                        title="CORS Allows All Methods",
                        description=(
                            "CORS is configured to allow all HTTP methods."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=(
                            "Restrict allowed methods to those actually used."
                        ),
                    )
                )

            # Allow credentials with wildcard
            if re.search(
                r"""allow_credentials\s*[:=]\s*(?:true|1)""",
                stripped,
                re.IGNORECASE,
            ) and any(
                "*" in l for l in lines[max(0, line_num - 5):line_num + 5]
            ):
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.CONFIGURATION,
                        severity=SecuritySeverity.HIGH,
                        title="CORS Credentials with Wildcard",
                        description=(
                            "CORS allows credentials with wildcard origins. "
                            "This is a security risk."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=(
                            "Never use credentials: true with wildcard origins."
                        ),
                    )
                )

        return issues

    def _check_debug_config(
        self, lines: list[str], file_path: str
    ) -> list[SecurityIssue]:
        """Check for debug mode in source configuration."""
        issues: list[SecurityIssue] = []

        debug_indicators = [
            re.compile(
                r"""(?:DEBUG|FLASK_DEBUG)\s*[:=]\s*(?:True|1|'true'|"true")""",
                re.IGNORECASE,
            ),
            re.compile(
                r"""app\.run\(.*debug\s*=\s*True""",
                re.IGNORECASE,
            ),
            re.compile(
                r"""uvicorn\.run\(.*debug\s*=\s*True""",
                re.IGNORECASE,
            ),
        ]

        for line_num, line in enumerate(lines, start=1):
            for pattern in debug_indicators:
                if pattern.search(line):
                    issues.append(
                        SecurityIssue(
                            category=SecurityCategory.CONFIGURATION,
                            severity=SecuritySeverity.MEDIUM,
                            title="Debug Mode in Source",
                            description=(
                                "Debug mode appears to be enabled or "
                                "hardcoded in source code."
                            ),
                            file_path=file_path,
                            line_number=line_num,
                            recommendation=(
                                "Control debug mode via environment "
                                "variables, not source code."
                            ),
                        )
                    )
                    break

        return issues

    def _check_tls(
        self, lines: list[str], file_path: str
    ) -> list[SecurityIssue]:
        """Check for TLS/HTTPS enforcement."""
        issues: list[SecurityIssue] = []

        content = "\n".join(lines)

        # Check for HTTP-only server bindings
        http_bind = re.compile(
            r"""(?:host|bind|listen)\s*[:=]\s*['\"]?(?:0\.0\.0\.0|127\.0\.0\.1)[:'\"]*""",
            re.IGNORECASE,
        )

        has_tls = any(
            indicator in content.lower()
            for indicator in ("ssl", "tls", "https", "certfile", "keyfile")
        )

        for line_num, line in enumerate(lines, start=1):
            if http_bind.search(line) and not has_tls:
                issues.append(
                    SecurityIssue(
                        category=SecurityCategory.CONFIGURATION,
                        severity=SecuritySeverity.MEDIUM,
                        title="HTTP Without TLS",
                        description=(
                            "Server appears to bind without TLS/HTTPS. "
                            "Traffic may be unencrypted."
                        ),
                        file_path=file_path,
                        line_number=line_num,
                        recommendation=(
                            "Enable TLS for production deployments "
                            "or use a TLS-terminating reverse proxy."
                        ),
                    )
                )
                break

        return issues

    # ------------------------------------------------------------------
    # Private helpers – Validation builder
    # ------------------------------------------------------------------

    def _parse_env_file(self, path: Path) -> dict[str, str]:
        """Parse a ``.env``-style file into a key-value dict."""
        env: dict[str, str] = {}
        try:
            for line in path.read_text(
                encoding="utf-8", errors="ignore"
            ).splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key:
                        env[key] = value
        except OSError:
            pass
        return env

    def _build_validation(
        self,
        issues: list[SecurityIssue],
        categories_checked: list[SecurityCategory],
    ) -> SecurityValidation:
        """Build a SecurityValidation from a list of issues."""
        critical = sum(
            1 for i in issues if i.severity == SecuritySeverity.CRITICAL
        )
        high = sum(
            1 for i in issues if i.severity == SecuritySeverity.HIGH
        )
        medium = sum(
            1 for i in issues if i.severity == SecuritySeverity.MEDIUM
        )
        low = sum(
            1 for i in issues if i.severity == SecuritySeverity.LOW
        )

        penalty = (
            critical * 30 + high * 20 + medium * 10 + low * 5
        )
        score = max(0.0, 100.0 - penalty)

        return SecurityValidation(
            issues=issues,
            score=score,
            categories_checked=categories_checked,
            total_issues=len(issues),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
        )
