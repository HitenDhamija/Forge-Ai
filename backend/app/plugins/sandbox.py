"""Plugin sandboxing for isolation and security in ForgeAI Plugin Marketplace."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SandboxConfig:
    """Configuration for a plugin sandbox."""
    max_memory_mb: int = 256
    max_cpu_percent: float = 50.0
    network_access: bool = False
    file_access: bool = False
    database_access: bool = False
    allowed_hosts: list[str] = field(default_factory=list)


@dataclass
class SandboxViolation:
    """Record of a sandbox violation."""
    plugin_id: str
    violation_type: str
    details: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ResourceUsage:
    """Resource usage snapshot for a plugin."""
    memory_mb: float
    cpu_percent: float
    network_requests: int
    file_operations: int


@dataclass
class _SandboxState:
    """Internal state for a single sandbox."""
    sandbox_id: str
    plugin_id: str
    config: SandboxConfig
    violations: list[SandboxViolation] = field(default_factory=list)
    resource_usage: ResourceUsage = field(
        default_factory=lambda: ResourceUsage(memory_mb=0.0, cpu_percent=0.0, network_requests=0, file_operations=0)
    )
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


default_config = SandboxConfig(
    max_memory_mb=256,
    max_cpu_percent=50.0,
    network_access=False,
    file_access=False,
    database_access=False,
    allowed_hosts=[],
)


class PluginSandbox:
    """Manages sandboxed execution environments for plugins."""

    def __init__(self, config: SandboxConfig) -> None:
        self._default_config = config
        self._sandboxes: dict[str, _SandboxState] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def create_sandbox(self, plugin_id: str) -> str:
        sandbox_id = f"sandbox-{uuid.uuid4().hex[:12]}"
        state = _SandboxState(
            sandbox_id=sandbox_id,
            plugin_id=plugin_id,
            config=SandboxConfig(
                max_memory_mb=self._default_config.max_memory_mb,
                max_cpu_percent=self._default_config.max_cpu_percent,
                network_access=self._default_config.network_access,
                file_access=self._default_config.file_access,
                database_access=self._default_config.database_access,
                allowed_hosts=list(self._default_config.allowed_hosts),
            ),
        )
        self._sandboxes[plugin_id] = state
        return sandbox_id

    def destroy_sandbox(self, plugin_id: str) -> None:
        self._sandboxes.pop(plugin_id, None)

    # ------------------------------------------------------------------
    # Permission checks
    # ------------------------------------------------------------------

    def check_permission(self, plugin_id: str, permission: str) -> bool:
        state = self._sandboxes.get(plugin_id)
        if state is None:
            return False

        cfg = state.config
        permission_map: dict[str, bool] = {
            "network_access": cfg.network_access,
            "file_access": cfg.file_access,
            "database_access": cfg.database_access,
        }

        if permission in permission_map:
            return permission_map[permission]

        return False

    def is_host_allowed(self, plugin_id: str, host: str) -> bool:
        state = self._sandboxes.get(plugin_id)
        if state is None:
            return False
        return host in state.config.allowed_hosts

    # ------------------------------------------------------------------
    # Violations
    # ------------------------------------------------------------------

    def log_violation(self, plugin_id: str, violation_type: str, details: str) -> None:
        state = self._sandboxes.get(plugin_id)
        if state is None:
            return
        state.violations.append(SandboxViolation(
            plugin_id=plugin_id,
            violation_type=violation_type,
            details=details,
        ))

    def get_violations(self, plugin_id: str) -> list[SandboxViolation]:
        state = self._sandboxes.get(plugin_id)
        if state is None:
            return []
        return list(state.violations)

    # ------------------------------------------------------------------
    # Resource monitoring
    # ------------------------------------------------------------------

    def get_resource_usage(self, plugin_id: str) -> ResourceUsage:
        state = self._sandboxes.get(plugin_id)
        if state is None:
            return ResourceUsage(memory_mb=0.0, cpu_percent=0.0, network_requests=0, file_operations=0)
        return state.resource_usage

    def check_resource_limits(self, plugin_id: str) -> bool:
        """Return True if the plugin is within all resource limits."""
        state = self._sandboxes.get(plugin_id)
        if state is None:
            return False

        usage = state.resource_usage
        cfg = state.config

        if usage.memory_mb > cfg.max_memory_mb:
            self.log_violation(plugin_id, "memory_exceeded", f"{usage.memory_mb:.1f}MB > {cfg.max_memory_mb}MB limit")
            return False
        if usage.cpu_percent > cfg.max_cpu_percent:
            self.log_violation(plugin_id, "cpu_exceeded", f"{usage.cpu_percent:.1f}% > {cfg.max_cpu_percent}% limit")
            return False
        return True

    def update_resource_usage(self, plugin_id: str, usage: ResourceUsage) -> None:
        state = self._sandboxes.get(plugin_id)
        if state is not None:
            state.resource_usage = usage

    # ------------------------------------------------------------------
    # Isolation testing
    # ------------------------------------------------------------------

    def isolation_check(self, plugin_id: str) -> dict:
        state = self._sandboxes.get(plugin_id)
        if state is None:
            return {"status": "no_sandbox", "checks_passed": 0, "checks_failed": 0, "details": []}

        checks: list[dict[str, Any]] = []

        network_ok = self.check_permission(plugin_id, "network_access") == state.config.network_access
        checks.append({"name": "network_isolation", "passed": network_ok})

        file_ok = self.check_permission(plugin_id, "file_access") == state.config.file_access
        checks.append({"name": "filesystem_isolation", "passed": file_ok})

        db_ok = self.check_permission(plugin_id, "database_access") == state.config.database_access
        checks.append({"name": "database_isolation", "passed": db_ok})

        resource_ok = self.check_resource_limits(plugin_id)
        checks.append({"name": "resource_limits", "passed": resource_ok})

        passed = sum(1 for c in checks if c["passed"])
        failed = len(checks) - passed

        return {
            "status": "passed" if failed == 0 else "failed",
            "checks_passed": passed,
            "checks_failed": failed,
            "details": checks,
        }

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_sandbox_stats(self) -> dict:
        total = len(self._sandboxes)
        total_violations = sum(len(s.violations) for s in self._sandboxes.values())
        configs = {
            "memory_limit_mb": self._default_config.max_memory_mb,
            "cpu_limit_percent": self._default_config.max_cpu_percent,
            "network_access": self._default_config.network_access,
            "file_access": self._default_config.file_access,
            "database_access": self._default_config.database_access,
        }
        return {
            "active_sandboxes": total,
            "total_violations": total_violations,
            "default_config": configs,
        }


plugin_sandbox = PluginSandbox(default_config)
