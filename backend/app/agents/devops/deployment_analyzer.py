"""Deployment Analyzer for infrastructure detection and deployment requirements.

Analyzes a project repository to detect infrastructure components,
determine deployment strategies, and identify required environment variables.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class InfrastructureType(str, Enum):
    """Detected infrastructure types."""

    FASTAPI = "fastapi"
    NEXTJS = "nextjs"
    REACT = "react"
    NODE = "node"
    POSTGRES = "postgres"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    REDIS = "redis"
    CHROMADB = "chromadb"
    OLLAMA = "ollama"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    DOCKER = "docker"


class DeploymentStrategy(str, Enum):
    """Available deployment strategies."""

    DOCKER = "docker"
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    RENDER = "render"
    RAILWAY = "railway"
    AWS_EC2 = "aws_ec2"
    AZURE_VM = "azure_vm"
    GCP_VM = "gcp_vm"


class AnalysisStatus(str, Enum):
    """Status of the analysis process."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class InfrastructureComponent:
    """A detected infrastructure component."""

    type: InfrastructureType
    name: str
    version: str = ""
    port: int | None = None
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentAnalysis:
    """Result of a deployment analysis."""

    project_type: InfrastructureType | None = None
    components: list[InfrastructureComponent] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    ports: list[int] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    strategy: DeploymentStrategy = DeploymentStrategy.DOCKER
    docker_present: bool = False
    compose_present: bool = False
    ci_cd_present: bool = False
    status: AnalysisStatus = AnalysisStatus.PENDING
    recommendations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detection helpers (per infrastructure type)
# ---------------------------------------------------------------------------

# File-name / directory patterns used for quick detection
_FASTAPI_PATTERNS = ("main.py", "app.py", "server.py")
_NEXTJS_CONFIG = ("next.config.js", "next.config.mjs", "next.config.ts")
_REACT_CONFIG = ("react-scripts", "vite.config")
_NODE_INDICATORS = ("package.json",)

_DB_CONN_STRINGS: dict[InfrastructureType, list[str]] = {
    InfrastructureType.POSTGRES: [
        "postgresql://",
        "postgres://",
        "postgresql+asyncpg://",
        "postgresql+psycopg2://",
        "postgresql+aiopg://",
        "DATABASE_URL",
    ],
    InfrastructureType.MYSQL: [
        "mysql://",
        "mysql+aiomysql://",
        "mysql+pymysql://",
        "mysql+asyncmy://",
    ],
    InfrastructureType.SQLITE: [
        "sqlite://",
        "sqlite+aiosqlite://",
        ".db",
        ".sqlite",
    ],
}

_INFRA_FILE_MARKERS: dict[str, InfrastructureType] = {
    "dockerfile": InfrastructureType.DOCKER,
    "docker-compose.yml": InfrastructureType.DOCKER,
    "docker-compose.yaml": InfrastructureType.DOCKER,
    ".github/workflows": InfrastructureType.DOCKER,
}

_PROMETHEUS_INDICATORS = [
    "prometheus",
    "prometheus_client",
    "prometheus-metrics",
    "PROMETHEUS_",
]

_GRAFANA_INDICATORS = [
    "grafana",
    "grafana_api",
    "GF_",
    "grafana.ini",
]

_OLLAMA_INDICATORS = [
    "ollama",
    "OLLAMA_",
    "llama.cpp",
]

_CHROMADB_INDICATORS = [
    "chromadb",
    "chroma",
    "CHROMA_",
    "chroma_client",
]

_REDIS_INDICATORS = [
    "redis://",
    "redis+aioredis://",
    "REDIS_URL",
    "aioredis",
    "redis",
]


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------


class DeploymentAnalyzer:
    """Analyzes project repositories to detect infrastructure and deployment needs.

    Usage::

        analyzer = DeploymentAnalyzer()
        analysis = await analyzer.analyze(project_path="/path/to/project", files=[...])
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(
        self,
        project_path: str,
        files: list[str],
    ) -> DeploymentAnalysis:
        """Run a full infrastructure analysis on the given project.

        Args:
            project_path: Root directory of the project.
            files: List of relative file paths in the repository.

        Returns:
            A ``DeploymentAnalysis`` describing detected components and
            recommended deployment strategy.
        """
        logger.info(
            "Starting deployment analysis: project_path=%s, file_count=%d",
            project_path,
            len(files),
        )

        analysis = DeploymentAnalysis()
        analysis.status = AnalysisStatus.IN_PROGRESS

        try:
            root = Path(project_path)
            file_set = {f.replace("\\", "/") for f in files}

            # --- Detect existing Docker / CI infrastructure -----------
            analysis.docker_present = self._detect_docker(file_set)
            analysis.compose_present = self._detect_compose(file_set)
            analysis.ci_cd_present = self._detect_ci_cd(file_set)

            # --- Detect application frameworks -----------------------
            detected_components: list[InfrastructureComponent] = []

            detected_components.extend(
                self._detect_frameworks(root, file_set)
            )

            # --- Detect databases ------------------------------------
            detected_components.extend(
                self._detect_databases(root, file_set)
            )

            # --- Detect supporting services --------------------------
            detected_components.extend(self._detect_redis(root, file_set))
            detected_components.extend(self._detect_chromadb(root, file_set))
            detected_components.extend(self._detect_ollama(root, file_set))
            detected_components.extend(self._detect_prometheus(root, file_set))
            detected_components.extend(self._detect_grafana(root, file_set))

            analysis.components = detected_components

            # --- Derive project type ---------------------------------
            analysis.project_type = self._determine_project_type(
                detected_components
            )

            # --- Extract environment variables -----------------------
            analysis.env_vars = await self._extract_env_vars(root, file_set)

            # --- Derive ports / volumes / services -------------------
            analysis.ports = self._collect_ports(detected_components)
            analysis.services = self._collect_services(detected_components)
            analysis.volumes = self._collect_volumes(detected_components)

            # --- Choose deployment strategy --------------------------
            analysis.strategy = self._recommend_strategy(analysis)

            # --- Recommendations ------------------------------------
            analysis.recommendations = self._build_recommendations(analysis)

            analysis.status = AnalysisStatus.COMPLETED

            logger.info(
                "Analysis completed: project_type=%s, components=%d, strategy=%s",
                analysis.project_type,
                len(analysis.components),
                analysis.strategy,
            )

        except Exception as exc:
            logger.error("Deployment analysis failed: %s", exc)
            analysis.status = AnalysisStatus.FAILED

        return analysis

    # ------------------------------------------------------------------
    # Docker / Compose / CI detection
    # ------------------------------------------------------------------

    def _detect_docker(self, file_set: set[str]) -> bool:
        """Return ``True`` if a Dockerfile is present."""
        return any(
            f.lower().startswith("dockerfile") for f in file_set
        )

    def _detect_compose(self, file_set: set[str]) -> bool:
        """Return ``True`` if a docker-compose file is present."""
        compose_names = {
            "docker-compose.yml",
            "docker-compose.yaml",
            "compose.yml",
            "compose.yaml",
        }
        return any(f in compose_names or f.endswith("/" + n) for n in compose_names for f in file_set)

    def _detect_ci_cd(self, file_set: set[str]) -> bool:
        """Return ``True`` if CI/CD workflow files are present."""
        ci_markers = (".github/workflows", ".gitlab-ci.yml", ".circleci", "Jenkinsfile", ".travis.yml")
        return any(m in f for f in file_set for m in ci_markers)

    # ------------------------------------------------------------------
    # Framework detection
    # ------------------------------------------------------------------

    def _detect_frameworks(
        self, root: Path, file_set: set[str]
    ) -> list[InfrastructureComponent]:
        """Detect application frameworks (FastAPI, Next.js, React, Node)."""
        components: list[InfrastructureComponent] = []

        # FastAPI detection
        if self._is_fastapi(root, file_set):
            version = self._extract_version_from_requirements(root, "fastapi")
            components.append(
                InfrastructureComponent(
                    type=InfrastructureType.FASTAPI,
                    name="FastAPI",
                    version=version,
                    port=8000,
                    config={"server": "uvicorn", "workers": 1},
                )
            )

        # Next.js detection
        if self._is_nextjs(file_set):
            version = self._extract_version_from_package_json(root, "next")
            components.append(
                InfrastructureComponent(
                    type=InfrastructureType.NEXTJS,
                    name="Next.js",
                    version=version,
                    port=3000,
                    config={"renderer": "node"},
                )
            )

        # React (non-Next.js) detection
        if self._is_react(root, file_set) and not self._is_nextjs(file_set):
            version = self._extract_version_from_package_json(root, "react")
            components.append(
                InfrastructureComponent(
                    type=InfrastructureType.REACT,
                    name="React",
                    version=version,
                    port=3000,
                    config={"renderer": "spa"},
                )
            )

        # Node.js backend detection (Express, Koa, NestJS, etc.)
        if self._is_node_backend(root, file_set) and not self._is_fastapi(
            root, file_set
        ):
            version = self._extract_node_version(root)
            components.append(
                InfrastructureComponent(
                    type=InfrastructureType.NODE,
                    name="Node.js",
                    version=version,
                    port=3000,
                    config={"runtime": "node"},
                )
            )

        return components

    def _is_fastapi(self, root: Path, file_set: set[str]) -> bool:
        """Detect FastAPI usage."""
        req = root / "requirements.txt"
        if req.exists():
            try:
                content = req.read_text(encoding="utf-8", errors="ignore")
                if "fastapi" in content.lower():
                    return True
            except OSError:
                pass

        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                content = pyproject.read_text(encoding="utf-8", errors="ignore")
                if "fastapi" in content.lower():
                    return True
            except OSError:
                pass

        # Check Python source files for FastAPI imports
        for fname in file_set:
            if not fname.endswith(".py"):
                continue
            try:
                fpath = root / fname
                if fpath.exists():
                    content = fpath.read_text(
                        encoding="utf-8", errors="ignore"
                    )[:8192]
                    if "fastapi" in content.lower() and (
                        "FastAPI()" in content or "from fastapi" in content
                    ):
                        return True
            except OSError:
                continue
        return False

    def _is_nextjs(self, file_set: set[str]) -> bool:
        """Detect Next.js usage."""
        return any(cfg in file_set for cfg in _NEXTJS_CONFIG)

    def _is_react(self, root: Path, file_set: set[str]) -> bool:
        """Detect React usage (including CRA and Vite React)."""
        pkg = root / "package.json"
        if pkg.exists():
            try:
                data = json.loads(
                    pkg.read_text(encoding="utf-8", errors="ignore")
                )
                deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }
                if "react" in deps:
                    return True
            except (json.JSONDecodeError, OSError):
                pass
        return False

    def _is_node_backend(self, root: Path, file_set: set[str]) -> bool:
        """Detect Node.js backend frameworks (Express, Koa, NestJS, Fastify)."""
        backend_frameworks = {"express", "koa", "@nestjs/core", "fastify", "hapi"}
        pkg = root / "package.json"
        if pkg.exists():
            try:
                data = json.loads(
                    pkg.read_text(encoding="utf-8", errors="ignore")
                )
                deps = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }
                if any(fw in deps for fw in backend_frameworks):
                    return True
            except (json.JSONDecodeError, OSError):
                pass
        return False

    # ------------------------------------------------------------------
    # Database detection
    # ------------------------------------------------------------------

    def _detect_databases(
        self, root: Path, file_set: set[str]
    ) -> list[InfrastructureComponent]:
        """Detect database usage from source files and config."""
        components: list[InfrastructureComponent] = []
        seen: set[InfrastructureType] = set()

        for fname in file_set:
            try:
                fpath = root / fname
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :65536
                ]
            except OSError:
                continue

            for db_type, indicators in _DB_CONN_STRINGS.items():
                if db_type in seen:
                    continue
                if any(ind in content for ind in indicators):
                    components.append(self._make_db_component(db_type))
                    seen.add(db_type)

        # Also check requirements / pyproject for DB drivers
        req = root / "requirements.txt"
        if req.exists():
            try:
                req_text = req.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                req_text = ""

            if InfrastructureType.POSTGRES not in seen and (
                "psycopg2" in req_text or "asyncpg" in req_text or "aiopg" in req_text
            ):
                components.append(self._make_db_component(InfrastructureType.POSTGRES))
                seen.add(InfrastructureType.POSTGRES)

            if InfrastructureType.MYSQL not in seen and (
                "pymysql" in req_text or "aiomysql" in req_text or "asyncmy" in req_text
            ):
                components.append(self._make_db_component(InfrastructureType.MYSQL))
                seen.add(InfrastructureType.MYSQL)

        return components

    @staticmethod
    def _make_db_component(db_type: InfrastructureType) -> InfrastructureComponent:
        """Create a component for the given database type."""
        defaults: dict[InfrastructureType, tuple[str, int | None]] = {
            InfrastructureType.POSTGRES: ("PostgreSQL", 5432),
            InfrastructureType.MYSQL: ("MySQL", 3306),
            InfrastructureType.SQLITE: ("SQLite", None),
        }
        name, port = defaults.get(db_type, (db_type.value, None))
        return InfrastructureComponent(
            type=db_type,
            name=name,
            port=port,
        )

    # ------------------------------------------------------------------
    # Supporting services detection
    # ------------------------------------------------------------------

    def _detect_redis(
        self, root: Path, file_set: set[str]
    ) -> list[InfrastructureComponent]:
        """Detect Redis usage."""
        for fname in file_set:
            try:
                fpath = root / fname
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :65536
                ]
                if any(ind in content for ind in _REDIS_INDICATORS):
                    return [
                        InfrastructureComponent(
                            type=InfrastructureType.REDIS,
                            name="Redis",
                            port=6379,
                        )
                    ]
            except OSError:
                continue
        return []

    def _detect_chromadb(
        self, root: Path, file_set: set[str]
    ) -> list[InfrastructureComponent]:
        """Detect ChromaDB usage."""
        for fname in file_set:
            try:
                fpath = root / fname
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :65536
                ]
                if any(ind in content for ind in _CHROMADB_INDICATORS):
                    return [
                        InfrastructureComponent(
                            type=InfrastructureType.CHROMADB,
                            name="ChromaDB",
                            port=8000,
                            config={"persist_directory": "./chroma_data"},
                        )
                    ]
            except OSError:
                continue
        return []

    def _detect_ollama(
        self, root: Path, file_set: set[str]
    ) -> list[InfrastructureComponent]:
        """Detect Ollama usage."""
        for fname in file_set:
            try:
                fpath = root / fname
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :65536
                ]
                if any(ind in content for ind in _OLLAMA_INDICATORS):
                    return [
                        InfrastructureComponent(
                            type=InfrastructureType.OLLAMA,
                            name="Ollama",
                            port=11434,
                        )
                    ]
            except OSError:
                continue
        return []

    def _detect_prometheus(
        self, root: Path, file_set: set[str]
    ) -> list[InfrastructureComponent]:
        """Detect Prometheus usage."""
        for fname in file_set:
            try:
                fpath = root / fname
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :65536
                ]
                if any(ind in content for ind in _PROMETHEUS_INDICATORS):
                    return [
                        InfrastructureComponent(
                            type=InfrastructureType.PROMETHEUS,
                            name="Prometheus",
                            port=9090,
                        )
                    ]
            except OSError:
                continue
        return []

    def _detect_grafana(
        self, root: Path, file_set: set[str]
    ) -> list[InfrastructureComponent]:
        """Detect Grafana usage."""
        for fname in file_set:
            try:
                fpath = root / fname
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :65536
                ]
                if any(ind in content for ind in _GRAFANA_INDICATORS):
                    return [
                        InfrastructureComponent(
                            type=InfrastructureType.GRAFANA,
                            name="Grafana",
                            port=3000,
                        )
                    ]
            except OSError:
                continue
        return []

    # ------------------------------------------------------------------
    # Environment variable extraction
    # ------------------------------------------------------------------

    async def _extract_env_vars(
        self, root: Path, file_set: set[str]
    ) -> dict[str, str]:
        """Extract required environment variables from code and config files.

        Scans ``.env.example``, ``.env.template``, ``.env.sample``,
        ``requirements.txt``, ``pyproject.toml``, ``package.json``, and
        Python/TypeScript source files for ``os.environ`` / ``process.env``
        references.

        Returns:
            Dictionary mapping variable names to placeholder descriptions.
        """
        env_vars: dict[str, str] = {}

        # 1. Check dedicated env template files
        env_templates = [
            ".env.example",
            ".env.template",
            ".env.sample",
            ".env.dev",
        ]
        for tpl in env_templates:
            tpl_path = root / tpl
            if tpl_path.exists():
                env_vars.update(self._parse_env_file(tpl_path))

        # 2. Scan source files for env var references
        env_var_pattern = re.compile(
            r"""(?:os\.environ(?:\.get\(|\[|\.get\())"""  # Python
            r"""|(?:process\.env\.)"""  # Node.js
            r"""|(?:ENV\s+)"""  # Dockerfile
        )
        var_name_pattern = re.compile(
            r"""(?:os\.environ(?:\.get\(|\[)["']?([A-Z_][A-Z0-9_]*)["']?)"""  # Python dict / get
            r"""|(?:os\.environ\.get\(["']([A-Z_][A-Z0-9_]*)["']"""  # Python .get with default
            r"""|(?:process\.env\.([A-Z_][A-Z0-9_]*))"""  # Node.js
        )

        for fname in file_set:
            try:
                fpath = root / fname
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :131072
                ]
            except OSError:
                continue

            for match in var_name_pattern.finditer(content):
                var_name = next(g for g in match.groups() if g is not None)
                if var_name and var_name not in env_vars:
                    env_vars[var_name] = f"Required by {fname}"

        # 3. Inferring common env vars from detected components
        inferred = self._infer_env_vars(root, file_set)
        for k, v in inferred.items():
            if k not in env_vars:
                env_vars[k] = v

        return env_vars

    def _parse_env_file(self, path: Path) -> dict[str, str]:
        """Parse a ``.env``-style file and return key-value pairs."""
        env: dict[str, str] = {}
        try:
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key:
                        env[key] = value if value else f"Placeholder from {path.name}"
        except OSError:
            pass
        return env

    def _infer_env_vars(
        self, root: Path, file_set: set[str]
    ) -> dict[str, str]:
        """Infer common environment variables based on detected infrastructure."""
        inferred: dict[str, str] = {}

        # Check for database URL references
        for fname in file_set:
            try:
                fpath = root / fname
                if not fpath.exists():
                    continue
                content = fpath.read_text(encoding="utf-8", errors="ignore")[
                    :65536
                ]
            except OSError:
                continue

            if "DATABASE_URL" in content:
                inferred.setdefault("DATABASE_URL", "PostgreSQL connection string")
            if "REDIS_URL" in content or "redis://" in content:
                inferred.setdefault("REDIS_URL", "Redis connection string")
            if "CHROMA_" in content or "chromadb" in content.lower():
                inferred.setdefault(
                    "CHROMA_HOST", "ChromaDB host (default: localhost)"
                )
                inferred.setdefault(
                    "CHROMA_PORT", "ChromaDB port (default: 8000)"
                )
            if "ollama" in content.lower() or "OLLAMA_" in content:
                inferred.setdefault(
                    "OLLAMA_HOST", "Ollama host (default: http://localhost:11434)"
                )
            if "PROMETHEUS_" in content:
                inferred.setdefault(
                    "PROMETHEUS_PORT", "Prometheus metrics port (default: 9090)"
                )
            if "GF_" in content or "grafana" in content.lower():
                inferred.setdefault(
                    "GF_SECURITY_ADMIN_PASSWORD", "Grafana admin password"
                )

        return inferred

    # ------------------------------------------------------------------
    # Project type determination
    # ------------------------------------------------------------------

    def _determine_project_type(
        self, components: list[InfrastructureComponent]
    ) -> InfrastructureType | None:
        """Determine the primary project type from detected components."""
        type_priority: list[InfrastructureType] = [
            InfrastructureType.FASTAPI,
            InfrastructureType.NEXTJS,
            InfrastructureType.REACT,
            InfrastructureType.NODE,
        ]
        detected_types = {c.type for c in components}
        for candidate in type_priority:
            if candidate in detected_types:
                return candidate
        return None

    # ------------------------------------------------------------------
    # Ports / services / volumes collection
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_ports(components: list[InfrastructureComponent]) -> list[int]:
        """Collect unique non-None ports from detected components."""
        ports: list[int] = []
        seen: set[int] = set()
        for comp in components:
            if comp.port is not None and comp.port not in seen:
                ports.append(comp.port)
                seen.add(comp.port)
        return ports

    @staticmethod
    def _collect_services(components: list[InfrastructureComponent]) -> list[str]:
        """Collect service names from detected components."""
        return [comp.name.lower().replace(" ", "-") for comp in components]

    @staticmethod
    def _collect_volumes(components: list[InfrastructureComponent]) -> list[str]:
        """Determine required Docker volumes based on components."""
        volumes: list[str] = []
        for comp in components:
            if comp.type == InfrastructureType.SQLITE:
                volumes.append("./data:/app/data")
            if comp.type == InfrastructureType.CHROMADB:
                persist_dir = comp.config.get("persist_directory", "./chroma_data")
                volumes.append(f"{persist_dir}:/app/chroma_data")
            if comp.type in (
                InfrastructureType.POSTGRES,
                InfrastructureType.MYSQL,
            ):
                volumes.append(f"{comp.type.value}_data:/var/lib/{comp.type.value}/data")
        return volumes

    # ------------------------------------------------------------------
    # Strategy recommendation
    # ------------------------------------------------------------------

    def _recommend_strategy(self, analysis: DeploymentAnalysis) -> DeploymentStrategy:
        """Recommend a deployment strategy based on detected components."""
        if analysis.compose_present:
            return DeploymentStrategy.DOCKER_COMPOSE

        if analysis.docker_present:
            return DeploymentStrategy.DOCKER

        has_external_services = any(
            comp.type
            in (
                InfrastructureType.POSTGRES,
                InfrastructureType.MYSQL,
                InfrastructureType.REDIS,
                InfrastructureType.OLLAMA,
                InfrastructureType.PROMETHEUS,
                InfrastructureType.GRAFANA,
            )
            for comp in analysis.components
        )

        if has_external_services:
            return DeploymentStrategy.DOCKER_COMPOSE

        if analysis.project_type in (
            InfrastructureType.REACT,
            InfrastructureType.NEXTJS,
        ):
            return DeploymentStrategy.DOCKER

        return DeploymentStrategy.DOCKER

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    def _build_recommendations(self, analysis: DeploymentAnalysis) -> list[str]:
        """Build deployment recommendations based on the analysis."""
        recs: list[str] = []

        if not analysis.docker_present:
            recs.append(
                "No Dockerfile detected. Consider adding one for consistent builds."
            )

        if not analysis.compose_present and len(analysis.components) > 1:
            recs.append(
                "Multiple services detected. Consider adding a docker-compose.yml."
            )

        if analysis.env_vars:
            recs.append(
                f"Ensure {len(analysis.env_vars)} environment variables are "
                "configured in your deployment target."
            )

        if any(
            comp.type == InfrastructureType.SQLITE for comp in analysis.components
        ):
            recs.append(
                "SQLite detected. For production, consider migrating to "
                "PostgreSQL or MySQL for concurrency and scalability."
            )

        if any(
            comp.type == InfrastructureType.OLLAMA for comp in analysis.components
        ):
            recs.append(
                "Ollama detected. Ensure the Ollama service is accessible "
                "and models are pre-downloaded in the deployment image."
            )

        if any(
            comp.type == InfrastructureType.CHROMADB for comp in analysis.components
        ):
            recs.append(
                "ChromaDB detected. Configure persistent storage for "
                "vector data across restarts."
            )

        if not analysis.ci_cd_present:
            recs.append(
                "No CI/CD pipeline detected. Consider adding GitHub Actions "
                "for automated testing and deployment."
            )

        return recs

    # ------------------------------------------------------------------
    # Version extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_version_from_requirements(
        root: Path, package: str
    ) -> str:
        """Extract the version of *package* from ``requirements.txt``."""
        req = root / "requirements.txt"
        if not req.exists():
            return ""
        try:
            for line in req.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith(package) and ("==" in line or ">=" in line):
                    _, _, ver = line.partition("==")
                    if ver:
                        return ver.strip()
                    _, _, ver = line.partition(">=")
                    return ver.strip() if ver else ""
        except OSError:
            pass
        return ""

    @staticmethod
    def _extract_version_from_package_json(
        root: Path, package: str
    ) -> str:
        """Extract the version of *package* from ``package.json``."""
        pkg = root / "package.json"
        if not pkg.exists():
            return ""
        try:
            data = json.loads(
                pkg.read_text(encoding="utf-8", errors="ignore")
            )
            deps = {
                **data.get("dependencies", {}),
                **data.get("devDependencies", {}),
            }
            version = deps.get(package, "")
            return version.lstrip("^~>=<")
        except (json.JSONDecodeError, OSError):
            return ""

    @staticmethod
    def _extract_node_version(root: Path) -> str:
        """Extract the Node.js engine version from ``package.json``."""
        pkg = root / "package.json"
        if not pkg.exists():
            return ""
        try:
            data = json.loads(
                pkg.read_text(encoding="utf-8", errors="ignore")
            )
            engines = data.get("engines", {})
            return engines.get("node", "")
        except (json.JSONDecodeError, OSError):
            return ""
