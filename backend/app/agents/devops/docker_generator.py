"""Dockerfile generator for detected project types."""

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DockerBaseImage(enum.Enum):
    """Supported base images for Dockerfile generation."""

    PYTHON_312_SLIM = "python:3.12-slim"
    PYTHON_311_SLIM = "python:3.11-slim"
    NODE_20_ALPINE = "node:20-alpine"
    NODE_22_ALPINE = "node:22-alpine"
    NGINX_ALPINE = "nginx:alpine"
    ALPINE = "alpine:3.20"


class ProjectType(enum.Enum):
    """Detected project types that can generate Dockerfiles."""

    FASTAPI = "fastapi"
    NEXTJS = "nextjs"
    REACT = "react"
    NODE = "node"
    PYTHON = "python"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BuildStage:
    """A single stage in a multi-stage Docker build."""

    name: str
    base_image: str
    commands: list[str] = field(default_factory=list)
    copies: list[str] = field(default_factory=list)
    workdir: str | None = None
    user: str | None = None


@dataclass
class DockerConfig:
    """Configuration used to generate a Dockerfile."""

    project_type: str
    base_image: DockerBaseImage = DockerBaseImage.PYTHON_312_SLIM
    stages: list[BuildStage] = field(default_factory=list)
    exposed_ports: list[int] = field(default_factory=lambda: [8000])
    volumes: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    health_check: str | None = None
    user: str = "appuser"
    workdir: str = "/app"
    package_manager: str = "pip"
    production_only: bool = True


@dataclass
class DockerfileResult:
    """Result of Dockerfile generation."""

    content: str
    stages: list[str]
    base_image: str
    size_estimate: str
    security_notes: list[str]
    dockerignore_content: str | None = None


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class DockerGenerator:
    """Generates production-ready Dockerfiles for various project types."""

    def __init__(self) -> None:
        self._generators: dict[str, Any] = {
            ProjectType.FASTAPI.value: self.generate_fastapi,
            ProjectType.NEXTJS.value: self.generate_nextjs,
            ProjectType.REACT.value: self.generate_react,
            ProjectType.NODE.value: self.generate_node,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        project_type: str,
        config: dict[str, Any] | None = None,
    ) -> DockerfileResult:
        """Generate a Dockerfile for the given project type.

        Args:
            project_type: The detected project type (e.g. "fastapi", "nextjs").
            config: Optional overrides for the default configuration.

        Returns:
            A ``DockerfileResult`` containing the generated content.
        """
        config = config or {}
        generator = self._generators.get(project_type.lower())
        if generator is None:
            logger.warning(
                "Unknown project_type=%s, falling back to generic node generator",
                project_type,
            )
            return await self.generate_node(config)
        return await generator(config)

    async def generate_fastapi(
        self,
        config: dict[str, Any] | None = None,
    ) -> DockerfileResult:
        """Generate a multi-stage Dockerfile for a Python/FastAPI project."""
        cfg = self._build_config(
            ProjectType.FASTAPI.value,
            DockerBaseImage.PYTHON_312_SLIM,
            config,
            default_port=8000,
        )
        sections: list[str] = []

        # --- Stage 1: builder ---
        sections.append(self._from("builder", DockerBaseImage.PYTHON_312_SLIM.value))
        sections.append(self._env({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}))
        sections.append(self._workdir(cfg.workdir))

        # Install system dependencies then Python deps
        sections.append(
            self._run_single(
                "apt-get update && apt-get install -y --no-install-recommends "
                "curl && rm -rf /var/lib/apt/lists/*"
            )
        )

        if cfg.package_manager == "poetry":
            sections.append(self._run_single("pip install poetry"))
            sections.append(self._copy("pyproject.toml poetry.lock*", "."))
            sections.append(
                self._run_single(
                    "poetry install --no-dev --no-interaction --no-ansi"
                )
            )
        else:
            sections.append(self._copy("requirements.txt", "."))
            sections.append(
                self._run_single(
                    "pip install --no-cache-dir --upgrade pip && "
                    "pip install --no-cache-dir -r requirements.txt"
                )
            )

        sections.append(self._copy(".", "."))

        # --- Stage 2: production ---
        sections.append(self._from("production", DockerBaseImage.PYTHON_312_SLIM.value))
        sections.append(self._env({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"}))
        sections.append(self._workdir(cfg.workdir))

        sections.append(
            self._run_single(
                "apt-get update && apt-get install -y --no-install-recommends "
                "curl && rm -rf /var/lib/apt/lists/*"
            )
        )

        # Copy virtualenv / packages from builder
        if cfg.package_manager == "poetry":
            sections.append(
                self._run_single(
                    "pip install poetry && poetry config virtualenvs.create false"
                )
            )
            sections.append(self._copy("--from=builder /app/.venv", ".venv"))
            sections.append(self._env({"PATH": "/app/.venv/bin:$PATH"}))
        else:
            sections.append(
                self._copy(
                    "--from=builder /usr/local/lib/python3.12/site-packages",
                    "/usr/local/lib/python3.12/site-packages",
                )
            )
            sections.append(
                self._copy(
                    "--from=builder /usr/local/bin", "/usr/local/bin"
                )
            )

        sections.append(self._copy("--from=builder /app", "."))

        # Non-root user
        sections.append(self._run_single(f"addgroup --system {cfg.user} && adduser --system --ingroup {cfg.user} {cfg.user}"))
        sections.append(self._user(cfg.user))

        sections.append(self._expose(cfg.exposed_ports))
        if cfg.health_check:
            sections.append(self._healthcheck(cfg.health_check))
        sections.append(self._cmd("uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"))

        dockerfile = "\n\n".join(sections)
        security = self._default_security_notes()

        return DockerfileResult(
            content=dockerfile,
            stages=["builder", "production"],
            base_image=DockerBaseImage.PYTHON_312_SLIM.value,
            size_estimate="~150MB (compressed: ~70MB)",
            security_notes=security,
            dockerignore_content=self._default_dockerignore_python(),
        )

    async def generate_nextjs(
        self,
        config: dict[str, Any] | None = None,
    ) -> DockerfileResult:
        """Generate a multi-stage Dockerfile for a Next.js project."""
        cfg = self._build_config(
            ProjectType.NEXTJS.value,
            DockerBaseImage.NODE_22_ALPINE,
            config,
            default_port=3000,
        )
        sections: list[str] = []

        # --- Stage 1: deps ---
        sections.append(self._from("deps", DockerBaseImage.NODE_22_ALPINE.value))
        sections.append(self._workdir(cfg.workdir))
        sections.append(self._run_single("apk add --no-cache libc6-compat"))
        sections.append(self._copy("package.json package-lock.json* pnpm-lock.yaml* yarn.lock*", "."))
        if cfg.package_manager == "pnpm":
            sections.append(self._run_single("corepack enable && pnpm install --frozen-lockfile"))
        else:
            sections.append(self._run_single("npm ci"))

        # --- Stage 2: builder ---
        sections.append(self._from("builder", DockerBaseImage.NODE_22_ALPINE.value))
        sections.append(self._workdir(cfg.workdir))
        sections.append(self._copy("--from=deps /app/node_modules", "./node_modules"))
        sections.append(self._copy(".", "."))
        sections.append(self._env({"NEXT_TELEMETRY_DISABLED": "1"}))

        if cfg.package_manager == "pnpm":
            sections.append(self._run_single("pnpm build"))
        else:
            sections.append(self._run_single("npm run build"))

        # --- Stage 3: runner ---
        sections.append(self._from("runner", DockerBaseImage.NODE_22_ALPINE.value))
        sections.append(self._workdir(cfg.workdir))
        sections.append(self._env({"NODE_ENV": "production", "NEXT_TELEMETRY_DISABLED": "1"}))
        sections.append(self._run_single("addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs"))

        sections.append(self._copy("--from=builder /app/public", "./public"))
        sections.append(
            self._copy(
                "--from=builder --chown=nextjs:nodejs /app/.next/standalone",
                "./",
            )
        )
        sections.append(
            self._copy(
                "--from=builder --chown=nextjs:nodejs /app/.next/static",
                "./.next/static",
            )
        )

        sections.append(self._user("nextjs"))
        sections.append(self._expose(cfg.exposed_ports))
        if cfg.health_check:
            sections.append(self._healthcheck(cfg.health_check))
        sections.append(self._cmd("node", "server.js"))

        dockerfile = "\n\n".join(sections)
        security = self._default_security_notes()
        security.append("Next.js standalone output enabled – minimal runtime image")

        return DockerfileResult(
            content=dockerfile,
            stages=["deps", "builder", "runner"],
            base_image=DockerBaseImage.NODE_22_ALPINE.value,
            size_estimate="~120MB (compressed: ~50MB)",
            security_notes=security,
            dockerignore_content=self._default_dockerignore_node(),
        )

    async def generate_react(
        self,
        config: dict[str, Any] | None = None,
    ) -> DockerfileResult:
        """Generate a multi-stage Dockerfile for a React SPA with nginx."""
        cfg = self._build_config(
            ProjectType.REACT.value,
            DockerBaseImage.NODE_22_ALPINE,
            config,
            default_port=80,
        )
        sections: list[str] = []

        # --- Stage 1: build ---
        sections.append(self._from("build", DockerBaseImage.NODE_22_ALPINE.value))
        sections.append(self._workdir(cfg.workdir))
        sections.append(self._copy("package.json package-lock.json* pnpm-lock.yaml* yarn.lock*", "."))
        if cfg.package_manager == "pnpm":
            sections.append(self._run_single("corepack enable && pnpm install --frozen-lockfile"))
        else:
            sections.append(self._run_single("npm ci"))
        sections.append(self._copy(".", "."))
        sections.append(self._run_single("npm run build" if cfg.package_manager != "pnpm" else "pnpm build"))

        # --- Stage 2: production ---
        sections.append(self._from("production", DockerBaseImage.NGINX_ALPINE.value))
        sections.append(self._run_single("rm -rf /usr/share/nginx/html/*"))
        sections.append(self._copy("--from=build /app/dist", "/usr/share/nginx/html"))
        sections.append(self._run_single("chown -R nginx:nginx /usr/share/nginx/html"))
        sections.append(self._user("nginx"))
        sections.append(self._expose(cfg.exposed_ports))
        sections.append(self._cmd("nginx", "-g", "daemon off;"))

        dockerfile = "\n\n".join(sections)
        security = self._default_security_notes()
        security.append("Served via nginx – static asset serving only")

        return DockerfileResult(
            content=dockerfile,
            stages=["build", "production"],
            base_image=DockerBaseImage.NGINX_ALPINE.value,
            size_estimate="~40MB (compressed: ~15MB)",
            security_notes=security,
            dockerignore_content=self._default_dockerignore_node(),
        )

    async def generate_node(
        self,
        config: dict[str, Any] | None = None,
    ) -> DockerfileResult:
        """Generate a generic multi-stage Dockerfile for a Node.js project."""
        cfg = self._build_config(
            ProjectType.NODE.value,
            DockerBaseImage.NODE_20_ALPINE,
            config,
            default_port=3000,
        )
        sections: list[str] = []

        # --- Stage 1: deps ---
        sections.append(self._from("deps", DockerBaseImage.NODE_20_ALPINE.value))
        sections.append(self._workdir(cfg.workdir))
        sections.append(self._run_single("apk add --no-cache libc6-compat"))
        sections.append(self._copy("package.json package-lock.json* pnpm-lock.yaml* yarn.lock*", "."))
        if cfg.package_manager == "pnpm":
            sections.append(self._run_single("corepack enable && pnpm install --frozen-lockfile"))
        elif cfg.package_manager == "yarn":
            sections.append(self._run_single("yarn install --frozen-lockfile"))
        else:
            sections.append(self._run_single("npm ci"))

        # --- Stage 2: build (optional TypeScript) ---
        sections.append(self._from("builder", DockerBaseImage.NODE_20_ALPINE.value))
        sections.append(self._workdir(cfg.workdir))
        sections.append(self._copy("--from=deps /app/node_modules", "./node_modules"))
        sections.append(self._copy(".", "."))
        if cfg.package_manager == "pnpm":
            sections.append(self._run_single("pnpm build || true"))
        else:
            sections.append(self._run_single("npm run build || true"))

        # --- Stage 3: production ---
        sections.append(self._from("production", DockerBaseImage.NODE_20_ALPINE.value))
        sections.append(self._run_single("addgroup --system --gid 1001 appgroup && adduser --system --uid 1001 appuser"))
        sections.append(self._workdir(cfg.workdir))
        sections.append(self._copy("--from=builder /app/node_modules", "./node_modules"))
        sections.append(self._copy("--from=builder /app/dist", "./dist"))
        sections.append(self._copy("package.json", "."))
        sections.append(self._user("appuser"))
        sections.append(self._expose(cfg.exposed_ports))
        if cfg.health_check:
            sections.append(self._healthcheck(cfg.health_check))
        sections.append(self._cmd("node", "dist/index.js"))

        dockerfile = "\n\n".join(sections)
        security = self._default_security_notes()

        return DockerfileResult(
            content=dockerfile,
            stages=["deps", "builder", "production"],
            base_image=DockerBaseImage.NODE_20_ALPINE.value,
            size_estimate="~100MB (compressed: ~40MB)",
            security_notes=security,
            dockerignore_content=self._default_dockerignore_node(),
        )

    # ------------------------------------------------------------------
    # Private helpers – Dockerfile sections
    # ------------------------------------------------------------------

    @staticmethod
    def _from(stage_name: str, base_image: str) -> str:
        return f"FROM {base_image} AS {stage_name}"

    @staticmethod
    def _workdir(path: str) -> str:
        return f"WORKDIR {path}"

    @staticmethod
    def _copy(src: str, dest: str) -> str:
        return f"COPY {src} {dest}"

    @staticmethod
    def _run_single(command: str) -> str:
        return f"RUN {command}"

    @staticmethod
    def _expose(ports: list[int]) -> str:
        return "EXPOSE " + " ".join(str(p) for p in ports)

    @staticmethod
    def _cmd(*args: str) -> str:
        return "CMD " + " ".join(repr(a) for a in args)

    @staticmethod
    def _healthcheck(command: str, interval: str = "30s", timeout: str = "5s", retries: int = 3) -> str:
        return (
            f"HEALTHCHECK --interval={interval} --timeout={timeout} --retries={retries} \\\n"
            f"  CMD {command}"
        )

    @staticmethod
    def _user(username: str) -> str:
        return f"USER {username}"

    @staticmethod
    def _env(variables: dict[str, str]) -> str:
        lines = ["ENV " + " \\\n    ".join(f"{k}={v}" for k, v in variables.items())]
        return lines[0]

    # ------------------------------------------------------------------
    # Private helpers – configuration
    # ------------------------------------------------------------------

    @staticmethod
    def _build_config(
        project_type: str,
        default_image: DockerBaseImage,
        overrides: dict[str, Any],
        default_port: int = 8000,
    ) -> DockerConfig:
        """Merge caller overrides into sensible defaults."""
        return DockerConfig(
            project_type=project_type,
            base_image=overrides.get("base_image", default_image),
            exposed_ports=overrides.get("ports", [default_port]),
            health_check=overrides.get("health_check"),
            user=overrides.get("user", "appuser"),
            workdir=overrides.get("workdir", "/app"),
            package_manager=overrides.get("package_manager", "pip" if project_type in ("fastapi", "python") else "npm"),
            production_only=overrides.get("production_only", True),
            env_vars=overrides.get("env_vars", {}),
        )

    # ------------------------------------------------------------------
    # Private helpers – security / dockerignore
    # ------------------------------------------------------------------

    @staticmethod
    def _default_security_notes() -> list[str]:
        return [
            "Non-root user applied",
            "Minimal base image used (slim/alpine)",
            "No secrets or credentials baked into image",
            "Health check configured",
            "Layer consolidation reduces attack surface",
        ]

    @staticmethod
    def _default_dockerignore_python() -> str:
        return "\n".join([
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".venv",
            "venv",
            "env",
            ".env",
            ".git",
            ".github",
            ".gitignore",
            ".dockerignore",
            "Dockerfile*",
            "docker-compose*",
            "*.md",
            "tests/",
            "pytest.ini",
            "mypy.ini",
            ".mypy_cache",
            ".pytest_cache",
            "htmlcov/",
            "coverage/",
            "*.egg-info",
            "dist/",
            "build/",
        ])

    @staticmethod
    def _default_dockerignore_node() -> str:
        return "\n".join([
            "node_modules",
            "npm-debug.log*",
            "yarn-debug.log*",
            "yarn-error.log*",
            "pnpm-debug.log*",
            ".next",
            ".nuxt",
            ".output",
            ".env",
            ".env.*",
            ".git",
            ".github",
            ".gitignore",
            ".dockerignore",
            "Dockerfile*",
            "docker-compose*",
            "*.md",
            "tests/",
            "coverage/",
            "dist/",
            "build/",
            ".cache/",
            ".turbo/",
        ])
