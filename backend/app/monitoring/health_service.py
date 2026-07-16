"""System health checks and status aggregation for all backend components."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

settings = get_settings()

# Default timeout for individual health checks (seconds)
DEFAULT_TIMEOUT = 2.0


class ComponentHealth(str, Enum):
    """Health status levels for system components."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentStatus:
    """Status report for a single system component."""

    name: str
    status: ComponentHealth
    latency_ms: float
    message: str
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str | None = None


class HealthService:
    """Provides health checks and status aggregation for all backend components.

    Each check is non-blocking with a configurable timeout. Results are returned
    as ComponentStatus dataclasses for consistent health reporting.
    """

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        """Initialize the health service.

        Args:
            timeout: Default timeout in seconds for each health check.
        """
        self._timeout = timeout

    async def check_backend_health(self) -> ComponentStatus:
        """Check backend API health.

        Returns:
            ComponentStatus for the backend.
        """
        start = datetime.now(timezone.utc)
        try:
            status = ComponentStatus(
                name="backend",
                status=ComponentHealth.HEALTHY,
                latency_ms=0.0,
                message="Backend is operational",
                version=settings.APP_VERSION,
            )
        except Exception as exc:
            status = ComponentStatus(
                name="backend",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Backend check failed: {exc}",
            )

        latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        status.latency_ms = round(latency, 2)
        return status

    async def check_database_health(self) -> ComponentStatus:
        """Check PostgreSQL database connectivity.

        Returns:
            ComponentStatus for the database.
        """
        start = datetime.now(timezone.utc)
        try:
            from app.database.session import async_session_factory

            async with asyncio.timeout(self._timeout):
                async with async_session_factory() as session:
                    await session.execute(
                        __import__("sqlalchemy").text("SELECT 1")
                    )

            status = ComponentStatus(
                name="database",
                status=ComponentHealth.HEALTHY,
                latency_ms=0.0,
                message="PostgreSQL connection successful",
            )
        except asyncio.TimeoutError:
            status = ComponentStatus(
                name="database",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Database check timed out after {self._timeout}s",
            )
        except ImportError:
            status = ComponentStatus(
                name="database",
                status=ComponentHealth.UNKNOWN,
                latency_ms=0.0,
                message="SQLAlchemy not available",
            )
        except Exception as exc:
            status = ComponentStatus(
                name="database",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Database check failed: {exc}",
            )

        latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        status.latency_ms = round(latency, 2)
        return status

    async def check_chromadb_health(self) -> ComponentStatus:
        """Check ChromaDB vector store connectivity.

        Returns:
            ComponentStatus for ChromaDB.
        """
        start = datetime.now(timezone.utc)
        try:
            from app.memory.config import get_memory_settings

            mem_settings = get_memory_settings()
            chroma_url = getattr(mem_settings, "CHROMA_URL", "http://localhost:8000")

            async with asyncio.timeout(self._timeout):
                import httpx

                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{chroma_url}/api/v1/heartbeat")
                    if resp.status_code == 200:
                        status = ComponentStatus(
                            name="chromadb",
                            status=ComponentHealth.HEALTHY,
                            latency_ms=0.0,
                            message="ChromaDB is reachable",
                        )
                    else:
                        status = ComponentStatus(
                            name="chromadb",
                            status=ComponentHealth.DEGRADED,
                            latency_ms=0.0,
                            message=f"ChromaDB returned status {resp.status_code}",
                        )
        except asyncio.TimeoutError:
            status = ComponentStatus(
                name="chromadb",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"ChromaDB check timed out after {self._timeout}s",
            )
        except ImportError:
            status = ComponentStatus(
                name="chromadb",
                status=ComponentHealth.UNKNOWN,
                latency_ms=0.0,
                message="httpx not available for ChromaDB check",
            )
        except Exception as exc:
            status = ComponentStatus(
                name="chromadb",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"ChromaDB check failed: {exc}",
            )

        latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        status.latency_ms = round(latency, 2)
        return status

    async def check_ollama_health(self) -> ComponentStatus:
        """Check Ollama LLM service connectivity.

        Returns:
            ComponentStatus for Ollama.
        """
        start = datetime.now(timezone.utc)
        try:
            from app.ai.config import get_ai_settings

            ai_settings = get_ai_settings()
            ollama_url = ai_settings.OLLAMA_BASE_URL

            async with asyncio.timeout(self._timeout):
                import httpx

                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{ollama_url}/api/tags")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = data.get("models", [])
                        status = ComponentStatus(
                            name="ollama",
                            status=ComponentHealth.HEALTHY,
                            latency_ms=0.0,
                            message=f"Ollama reachable with {len(models)} models",
                        )
                    else:
                        status = ComponentStatus(
                            name="ollama",
                            status=ComponentHealth.DEGRADED,
                            latency_ms=0.0,
                            message=f"Ollama returned status {resp.status_code}",
                        )
        except asyncio.TimeoutError:
            status = ComponentStatus(
                name="ollama",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Ollama check timed out after {self._timeout}s",
            )
        except ImportError:
            status = ComponentStatus(
                name="ollama",
                status=ComponentHealth.UNKNOWN,
                latency_ms=0.0,
                message="httpx not available for Ollama check",
            )
        except Exception as exc:
            status = ComponentStatus(
                name="ollama",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Ollama check failed: {exc}",
            )

        latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        status.latency_ms = round(latency, 2)
        return status

    async def check_redis_health(self) -> ComponentStatus:
        """Check Redis connectivity if configured.

        Returns:
            ComponentStatus for Redis.
        """
        start = datetime.now(timezone.utc)
        try:
            import os

            redis_url = os.environ.get("REDIS_URL", "")
            if not redis_url:
                return ComponentStatus(
                    name="redis",
                    status=ComponentHealth.UNKNOWN,
                    latency_ms=0.0,
                    message="Redis not configured",
                )

            async with asyncio.timeout(self._timeout):
                import redis.asyncio as aioredis

                async with aioredis.from_url(redis_url) as client:
                    await client.ping()

            status = ComponentStatus(
                name="redis",
                status=ComponentHealth.HEALTHY,
                latency_ms=0.0,
                message="Redis connection successful",
            )
        except asyncio.TimeoutError:
            status = ComponentStatus(
                name="redis",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Redis check timed out after {self._timeout}s",
            )
        except ImportError:
            status = ComponentStatus(
                name="redis",
                status=ComponentHealth.UNKNOWN,
                latency_ms=0.0,
                message="redis.asyncio not installed",
            )
        except Exception as exc:
            status = ComponentStatus(
                name="redis",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Redis check failed: {exc}",
            )

        latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        status.latency_ms = round(latency, 2)
        return status

    async def check_docker_health(self) -> ComponentStatus:
        """Check Docker daemon connectivity.

        Returns:
            ComponentStatus for Docker.
        """
        start = datetime.now(timezone.utc)
        try:
            async with asyncio.timeout(self._timeout):
                process = await asyncio.create_subprocess_exec(
                    "docker", "info", "--format", "{{.ServerVersion}}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    version = stdout.decode().strip()
                    status = ComponentStatus(
                        name="docker",
                        status=ComponentHealth.HEALTHY,
                        latency_ms=0.0,
                        message=f"Docker daemon running (v{version})",
                        version=version,
                    )
                else:
                    error_msg = stderr.decode().strip() or "Unknown error"
                    status = ComponentStatus(
                        name="docker",
                        status=ComponentHealth.UNHEALTHY,
                        latency_ms=0.0,
                        message=f"Docker check failed: {error_msg}",
                    )
        except asyncio.TimeoutError:
            status = ComponentStatus(
                name="docker",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Docker check timed out after {self._timeout}s",
            )
        except FileNotFoundError:
            status = ComponentStatus(
                name="docker",
                status=ComponentHealth.UNKNOWN,
                latency_ms=0.0,
                message="Docker CLI not found",
            )
        except Exception as exc:
            status = ComponentStatus(
                name="docker",
                status=ComponentHealth.UNHEALTHY,
                latency_ms=0.0,
                message=f"Docker check failed: {exc}",
            )

        latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        status.latency_ms = round(latency, 2)
        return status

    async def check_all(self, app_state: Any) -> list[ComponentStatus]:
        """Run health checks for all registered components concurrently.

        Args:
            app_state: Application state (used for component-specific checks).

        Returns:
            List of ComponentStatus for every checked component.
        """
        checks = [
            self.check_backend_health(),
            self.check_database_health(),
            self.check_chromadb_health(),
            self.check_ollama_health(),
            self.check_redis_health(),
            self.check_docker_health(),
        ]

        results = await asyncio.gather(*checks, return_exceptions=True)

        statuses: list[ComponentStatus] = []
        for result in results:
            if isinstance(result, ComponentStatus):
                statuses.append(result)
            elif isinstance(result, Exception):
                statuses.append(
                    ComponentStatus(
                        name="unknown",
                        status=ComponentHealth.UNHEALTHY,
                        latency_ms=0.0,
                        message=f"Health check raised: {result}",
                    )
                )

        logger.info(
            "Health check complete: %d components checked",
            len(statuses),
        )
        return statuses

    async def get_overall_health(self, app_state: Any) -> ComponentHealth:
        """Determine aggregate health across all components.

        The worst status among all components determines the overall health.

        Args:
            app_state: Application state.

        Returns:
            ComponentHealth representing the overall system status.
        """
        statuses = await self.check_all(app_state)

        if not statuses:
            return ComponentHealth.UNKNOWN

        status_order = {
            ComponentHealth.HEALTHY: 0,
            ComponentHealth.DEGRADED: 1,
            ComponentHealth.UNHEALTHY: 2,
            ComponentHealth.UNKNOWN: 3,
        }

        worst = max(statuses, key=lambda s: status_order.get(s.status, 3))
        return worst.status

    async def get_health_summary(self, app_state: Any) -> dict:
        """Get a full health summary with overall status and per-component details.

        Args:
            app_state: Application state.

        Returns:
            Dictionary with overall_status, components list, and timestamp.
        """
        statuses = await self.check_all(app_state)

        status_order = {
            ComponentHealth.HEALTHY: 0,
            ComponentHealth.DEGRADED: 1,
            ComponentHealth.UNHEALTHY: 2,
            ComponentHealth.UNKNOWN: 3,
        }
        overall = max(statuses, key=lambda s: status_order.get(s.status, 3)).status if statuses else ComponentHealth.UNKNOWN

        components = [
            {
                "name": s.name,
                "status": s.status.value,
                "latency_ms": s.latency_ms,
                "message": s.message,
                "last_checked": s.last_checked.isoformat(),
                "version": s.version,
            }
            for s in statuses
        ]

        healthy_count = sum(1 for s in statuses if s.status == ComponentHealth.HEALTHY)
        degraded_count = sum(1 for s in statuses if s.status == ComponentHealth.DEGRADED)
        unhealthy_count = sum(1 for s in statuses if s.status == ComponentHealth.UNHEALTHY)
        unknown_count = sum(1 for s in statuses if s.status == ComponentHealth.UNKNOWN)

        return {
            "overall_status": overall.value,
            "components": components,
            "summary": {
                "total": len(statuses),
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "unknown": unknown_count,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
