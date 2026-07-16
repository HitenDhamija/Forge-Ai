"""Docker Compose file generator for project infrastructure."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

import yaml

from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ComposeVariant(enum.Enum):
    """Supported compose file variants."""

    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"


class RestartPolicy(enum.Enum):
    """Docker restart policies."""

    NO = "no"
    ALWAYS = "always"
    UNLESS_STOPPED = "unless-stopped"
    ON_FAILURE = "on-failure"


class NetworkDriver(enum.Enum):
    """Supported network drivers."""

    BRIDGE = "bridge"
    HOST = "host"
    OVERLAY = "overlay"
    NONE = "none"


class VolumeDriver(enum.Enum):
    """Supported volume drivers."""

    LOCAL = "local"


# ---------------------------------------------------------------------------
# Dataclasses – configuration
# ---------------------------------------------------------------------------


@dataclass
class HealthCheck:
    """Container health check configuration."""

    test: list[str]
    interval: str = "30s"
    timeout: str = "10s"
    retries: int = 3
    start_period: str = "15s"


@dataclass
class DeployResources:
    """Resource limits / reservations for deploy mode."""

    cpus: float | None = None
    memory: str | None = None


@dataclass
class DeployConfig:
    """Docker Compose ``deploy`` configuration."""

    replicas: int = 1
    resources: DeployResources | None = None


@dataclass
class ServiceConfig:
    """Full configuration for a single Docker Compose service."""

    name: str
    image: str
    ports: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
    env_vars: dict[str, str] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    health_check: HealthCheck | None = None
    restart_policy: RestartPolicy = RestartPolicy.UNLESS_STOPPED
    networks: list[str] = field(default_factory=list)
    deploy_config: DeployConfig | None = None
    command: str | None = None
    entrypoint: str | None = None
    environment: list[str] = field(default_factory=list)


@dataclass
class NetworkConfig:
    """Docker Compose network definition."""

    name: str
    driver: NetworkDriver = NetworkDriver.BRIDGE
    external: bool = False


@dataclass
class VolumeConfig:
    """Docker Compose volume definition."""

    name: str
    driver: VolumeDriver = VolumeDriver.LOCAL
    external: bool = False


@dataclass
class ComposeConfig:
    """Aggregate compose configuration before serialisation."""

    version: str = "3.9"
    services: dict[str, ServiceConfig] = field(default_factory=dict)
    networks: dict[str, NetworkConfig] = field(default_factory=dict)
    volumes: dict[str, VolumeConfig] = field(default_factory=dict)


@dataclass
class ComposeResult:
    """Result returned after compose generation."""

    content: str
    variant: ComposeVariant
    services_count: int
    volumes_count: int
    networks_count: int
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NETWORK_INTERNAL = "internal"
_DEFAULT_NETWORK = "app-network"

_DEFAULT_SERVICES: dict[str, dict[str, Any]] = {
    "backend": {
        "image": "python:3.12-slim",
        "ports": ["8000:8000"],
        "health": {
            "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "20s",
        },
    },
    "frontend": {
        "image": "node:20-alpine",
        "ports": ["3000:3000"],
        "health": {
            "test": ["CMD", "curl", "-f", "http://localhost:3000/health"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "15s",
        },
    },
    "postgres": {
        "image": "postgres:16-alpine",
        "ports": ["5432:5432"],
        "volumes": ["postgres-data:/var/lib/postgresql/data"],
        "env": {
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "POSTGRES_DB": "app",
        },
        "health": {
            "test": ["CMD-SHELL", "pg_isready -U postgres"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5,
            "start_period": "10s",
        },
    },
    "redis": {
        "image": "redis:7-alpine",
        "ports": ["6379:6379"],
        "volumes": ["redis-data:/data"],
        "health": {
            "test": ["CMD", "redis-cli", "ping"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5,
            "start_period": "5s",
        },
    },
    "chromadb": {
        "image": "chromadb/chroma:latest",
        "ports": ["8001:8000"],
        "volumes": ["chroma-data:/chroma/chroma"],
        "health": {
            "test": ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "15s",
        },
    },
    "ollama": {
        "image": "ollama/ollama:latest",
        "ports": ["11434:11434"],
        "volumes": ["ollama-data:/root/.ollama"],
        "health": {
            "test": ["CMD", "curl", "-f", "http://localhost:11434/"],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "30s",
        },
    },
}

_SERVICE_COMPONENT_MAP: dict[str, str] = {
    "python": "backend",
    "fastapi": "backend",
    "flask": "backend",
    "django": "backend",
    "node": "frontend",
    "react": "frontend",
    "vue": "frontend",
    "next": "frontend",
    "astro": "frontend",
    "svelte": "frontend",
    "postgres": "postgres",
    "postgresql": "postgres",
    "redis": "redis",
    "chromadb": "chromadb",
    "chroma": "chromadb",
    "ollama": "ollama",
    "llm": "ollama",
}

_DEV_PORT_OFFSET: int = 10000


# ---------------------------------------------------------------------------
# ComposeGenerator
# ---------------------------------------------------------------------------


class ComposeGenerator:
    """Generates Docker Compose files from project analysis results."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        analysis: dict[str, Any],
        variant: ComposeVariant = ComposeVariant.PRODUCTION,
    ) -> ComposeResult:
        """Generate a compose file for the requested variant."""
        logger.info("Generating compose file", variant=variant.value)

        if variant is ComposeVariant.DEVELOPMENT:
            return await self.generate_development(analysis)
        if variant is ComposeVariant.TESTING:
            return await self.generate_testing(analysis)
        return await self.generate_production(analysis)

    async def generate_production(
        self,
        analysis: dict[str, Any],
    ) -> ComposeResult:
        """Generate an optimised production compose file."""
        config = ComposeConfig(version="3.9")
        notes: list[str] = []

        detected = self._resolve_services(analysis)

        for svc_name, svc_def in detected.items():
            config.services[svc_name] = self._build_service(
                svc_name,
                svc_def,
                variant=ComposeVariant.PRODUCTION,
            )

        self._add_default_network(config)
        self._add_required_volumes(config, detected)

        content = self._serialise(config)
        logger.info(
            "Production compose generated",
            services=len(config.services),
        )
        return ComposeResult(
            content=content,
            variant=ComposeVariant.PRODUCTION,
            services_count=len(config.services),
            volumes_count=len(config.volumes),
            networks_count=len(config.networks),
            notes=notes,
        )

    async def generate_development(
        self,
        analysis: dict[str, Any],
    ) -> ComposeResult:
        """Generate a development compose with hot-reload and debug ports."""
        config = ComposeConfig(version="3.9")
        notes: list[str] = [
            "Development mode: hot-reload enabled",
            "Debug ports mapped via offset",
        ]

        detected = self._resolve_services(analysis)

        for svc_name, svc_def in detected.items():
            config.services[svc_name] = self._build_service(
                svc_name,
                svc_def,
                variant=ComposeVariant.DEVELOPMENT,
            )

        self._add_default_network(config)
        self._add_required_volumes(config, detected)

        content = self._serialise(config)
        logger.info(
            "Development compose generated",
            services=len(config.services),
        )
        return ComposeResult(
            content=content,
            variant=ComposeVariant.DEVELOPMENT,
            services_count=len(config.services),
            volumes_count=len(config.volumes),
            networks_count=len(config.networks),
            notes=notes,
        )

    async def generate_testing(
        self,
        analysis: dict[str, Any],
    ) -> ComposeResult:
        """Generate a testing compose file (minimal, fast teardown)."""
        config = ComposeConfig(version="3.9")
        notes: list[str] = ["Testing mode: ephemeral volumes"]

        detected = self._resolve_services(analysis)

        for svc_name, svc_def in detected.items():
            config.services[svc_name] = self._build_service(
                svc_name,
                svc_def,
                variant=ComposeVariant.TESTING,
            )

        self._add_default_network(config)

        content = self._serialise(config)
        logger.info(
            "Testing compose generated",
            services=len(config.services),
        )
        return ComposeResult(
            content=content,
            variant=ComposeVariant.TESTING,
            services_count=len(config.services),
            volumes_count=len(config.volumes),
            networks_count=len(config.networks),
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Private helpers – service / network / volume building
    # ------------------------------------------------------------------

    def _resolve_services(
        self,
        analysis: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """Map detected project components to service definitions."""
        services: dict[str, dict[str, Any]] = {}
        components: list[str] = analysis.get("components", [])
        detected_names: list[str] = analysis.get("detected_services", [])

        all_identifiers = [
            *[_lower(c) for c in components],
            *[_lower(d) for d in detected_names],
        ]

        mapped: set[str] = set()
        for identifier in all_identifiers:
            if identifier in _SERVICE_COMPONENT_MAP:
                svc_name = _SERVICE_COMPONENT_MAP[identifier]
                if svc_name not in mapped:
                    mapped.add(svc_name)
                    services[svc_name] = _DEFAULT_SERVICES[svc_name].copy()

        if not services:
            logger.warning(
                "No known services detected – adding backend as default",
            )
            services["backend"] = _DEFAULT_SERVICES["backend"].copy()

        return services

    def _build_service(
        self,
        name: str,
        definition: dict[str, Any],
        *,
        variant: ComposeVariant,
    ) -> ServiceConfig:
        """Construct a ``ServiceConfig`` from a raw definition dict."""
        image: str = definition.get("image", f"{name}:latest")
        raw_ports: list[str] = list(definition.get("ports", []))
        raw_volumes: list[str] = list(definition.get("volumes", []))
        raw_env: dict[str, str] = dict(definition.get("env", {}))
        depends_on: list[str] = list(definition.get("depends_on", []))

        health_data = definition.get("health")
        health_check = self._build_health_check(health_data)

        restart = RestartPolicy.UNLESS_STOPPED
        if variant is ComposeVariant.TESTING:
            restart = RestartPolicy.NO

        deploy_cfg: DeployConfig | None = None
        if variant is ComposeVariant.PRODUCTION:
            deploy_cfg = DeployConfig(
                replicas=1,
                resources=DeployResources(cpus=1.0, memory="512m"),
            )

        ports = self._adjust_ports(name, raw_ports, variant)
        volumes = self._adjust_volumes(name, raw_volumes, variant)
        env_vars = dict(raw_env)

        return ServiceConfig(
            name=name,
            image=image,
            ports=ports,
            volumes=volumes,
            env_vars=env_vars,
            depends_on=depends_on,
            health_check=health_check,
            restart_policy=restart,
            networks=[_DEFAULT_NETWORK],
            deploy_config=deploy_cfg,
        )

    def _build_health_check(
        self,
        data: dict[str, Any] | None,
    ) -> HealthCheck | None:
        if data is None:
            return None
        return HealthCheck(
            test=data.get("test", ["CMD", "true"]),
            interval=data.get("interval", "30s"),
            timeout=data.get("timeout", "10s"),
            retries=data.get("retries", 3),
            start_period=data.get("start_period", "15s"),
        )

    # ------------------------------------------------------------------
    # Private helpers – port / volume adjustment
    # ------------------------------------------------------------------

    @staticmethod
    def _adjust_ports(
        name: str,
        ports: list[str],
        variant: ComposeVariant,
    ) -> list[str]:
        """Map ports depending on variant."""
        if variant is ComposeVariant.PRODUCTION:
            return ports
        adjusted: list[str] = []
        for port in ports:
            parts = port.split(":")
            if len(parts) == 2:
                host_port = int(parts[0]) + _DEV_PORT_OFFSET if variant is ComposeVariant.DEVELOPMENT else int(parts[0])
                adjusted.append(f"{host_port}:{parts[1]}")
            else:
                adjusted.append(port)
        return adjusted

    @staticmethod
    def _adjust_volumes(
        name: str,
        volumes: list[str],
        variant: ComposeVariant,
    ) -> list[str]:
        """Adjust volume definitions for the variant."""
        if variant is ComposeVariant.TESTING:
            return [v for v in volumes if not v.startswith("./")]
        return volumes

    # ------------------------------------------------------------------
    # Private helpers – networks / volumes defaults
    # ------------------------------------------------------------------

    def _add_default_network(self, config: ComposeConfig) -> None:
        config.networks[_DEFAULT_NETWORK] = NetworkConfig(
            name=_DEFAULT_NETWORK,
            driver=NetworkDriver.BRIDGE,
        )

    def _add_required_volumes(
        self,
        config: ComposeConfig,
        detected: dict[str, dict[str, Any]],
    ) -> None:
        volume_names: set[str] = set()
        for svc_def in detected.values():
            for vol in svc_def.get("volumes", []):
                if ":" in vol:
                    vol_name = vol.split(":")[0]
                    if "/" not in vol_name:
                        volume_names.add(vol_name)

        for vol_name in sorted(volume_names):
            config.volumes[vol_name] = VolumeConfig(name=vol_name)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def _serialise(self, config: ComposeConfig) -> str:
        """Serialise ``ComposeConfig`` to a YAML string."""
        data: dict[str, Any] = {"version": config.version}

        # Services
        services_block: dict[str, Any] = {}
        for name, svc in config.services.items():
            entry: dict[str, Any] = {
                "image": svc.image,
                "restart": svc.restart_policy.value,
                "networks": list(svc.networks),
            }
            if svc.ports:
                entry["ports"] = list(svc.ports)
            if svc.volumes:
                entry["volumes"] = list(svc.volumes)
            if svc.env_vars:
                entry["environment"] = dict(svc.env_vars)
            if svc.environment:
                entry["environment"] = entry.get("environment", [])
                entry["environment"].extend(svc.environment)
            if svc.depends_on:
                entry["depends_on"] = list(svc.depends_on)
            if svc.command:
                entry["command"] = svc.command
            if svc.entrypoint:
                entry["entrypoint"] = svc.entrypoint
            if svc.health_check:
                entry["healthcheck"] = {
                    "test": svc.health_check.test,
                    "interval": svc.health_check.interval,
                    "timeout": svc.health_check.timeout,
                    "retries": svc.health_check.retries,
                    "start_period": svc.health_check.start_period,
                }
            if svc.deploy_config:
                deploy: dict[str, Any] = {
                    "replicas": svc.deploy_config.replicas,
                }
                if svc.deploy_config.resources:
                    res: dict[str, Any] = {}
                    if svc.deploy_config.resources.cpus is not None:
                        res["cpus"] = str(svc.deploy_config.resources.cpus)
                    if svc.deploy_config.resources.memory is not None:
                        res["memory"] = svc.deploy_config.resources.memory
                    if res:
                        deploy["resources"] = {"limits": res}
                entry["deploy"] = deploy
            services_block[name] = entry

        data["services"] = services_block

        # Networks
        if config.networks:
            networks_block: dict[str, Any] = {}
            for net_name, net_cfg in config.networks.items():
                net_entry: dict[str, Any] = {"driver": net_cfg.driver.value}
                if net_cfg.external:
                    net_entry["external"] = True
                networks_block[net_name] = net_entry
            data["networks"] = networks_block

        # Volumes
        if config.volumes:
            volumes_block: dict[str, Any] = {}
            for vol_name, vol_cfg in config.volumes.items():
                vol_entry: dict[str, Any] = {"driver": vol_cfg.driver.value}
                if vol_cfg.external:
                    vol_entry["external"] = True
                volumes_block[vol_name] = vol_entry
            data["volumes"] = volumes_block

        return yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _lower(value: Any) -> str:
    return str(value).strip().lower()
