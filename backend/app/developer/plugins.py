"""Plugin system for extensibility."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


class PluginType(Enum):
    AGENT = "agent"
    TOOL = "tool"
    PROMPT = "prompt"
    WORKFLOW = "workflow"
    MEMORY_PROVIDER = "memory_provider"
    STORAGE_PROVIDER = "storage_provider"
    AUTH = "auth"
    VISUALIZATION = "visualization"


class PluginStatus(Enum):
    INSTALLED = "installed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    author: str
    type: PluginType
    entry_point: str
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    min_platform_version: str = "1.0.0"


@dataclass
class Plugin:
    manifest: PluginManifest
    status: PluginStatus
    config: dict[str, Any] = field(default_factory=dict)
    installed_at: datetime = field(default_factory=datetime.utcnow)
    enabled: bool = True
    error_message: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class PluginAPI:
    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._hooks: dict[str, dict[str, Callable]] = {}
        self._load_builtins()

    def _load_builtins(self) -> None:
        builtins = [
            PluginManifest(
                name="ollama-provider",
                version="1.0.0",
                description="Ollama AI provider for local model inference",
                author="ForgeAI",
                type=PluginType.AGENT,
                entry_point="plugins.ollama_provider:OllamaProvider",
                config_schema={"base_url": {"type": "string", "default": "http://localhost:11434"}, "model": {"type": "string", "default": "llama2"}},
            ),
            PluginManifest(
                name="local-storage",
                version="1.0.0",
                description="Local file storage provider",
                author="ForgeAI",
                type=PluginType.STORAGE_PROVIDER,
                entry_point="plugins.local_storage:LocalStorage",
                config_schema={"root_path": {"type": "string", "default": "./data"}},
            ),
            PluginManifest(
                name="jwt-auth",
                version="1.0.0",
                description="JWT authentication plugin",
                author="ForgeAI",
                type=PluginType.AUTH,
                entry_point="plugins.jwt_auth:JWTAuth",
                config_schema={"secret_key": {"type": "string", "required": True}, "algorithm": {"type": "string", "default": "HS256"}},
            ),
            PluginManifest(
                name="redis-cache",
                version="1.0.0",
                description="Redis caching provider",
                author="ForgeAI",
                type=PluginType.MEMORY_PROVIDER,
                entry_point="plugins.redis_cache:RedisCache",
                config_schema={"host": {"type": "string", "default": "localhost"}, "port": {"type": "integer", "default": 6379}},
            ),
            PluginManifest(
                name="postgres-db",
                version="1.0.0",
                description="PostgreSQL database provider",
                author="ForgeAI",
                type=PluginType.STORAGE_PROVIDER,
                entry_point="plugins.postgres_db:PostgresDB",
                config_schema={"connection_string": {"type": "string", "required": True}},
            ),
        ]
        for manifest in builtins:
            self.register_plugin(manifest)

    def register_plugin(self, manifest: PluginManifest) -> str:
        errors = self.validate_plugin(manifest)
        if errors:
            raise ValueError(f"Plugin validation failed: {', '.join(errors)}")
        for existing in self._plugins.values():
            if existing.manifest.name == manifest.name:
                raise ValueError(f"Plugin '{manifest.name}' is already registered")
        plugin = Plugin(manifest=manifest, status=PluginStatus.INSTALLED)
        self._plugins[plugin.id] = plugin
        self._hooks[plugin.id] = {}
        return plugin.id

    def unregister_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self._plugins:
            return False
        del self._plugins[plugin_id]
        del self._hooks[plugin_id]
        return True

    def get_plugin(self, plugin_id: str) -> Plugin:
        if plugin_id not in self._plugins:
            raise KeyError(f"Plugin '{plugin_id}' not found")
        return self._plugins[plugin_id]

    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> list[Plugin]:
        plugins = list(self._plugins.values())
        if plugin_type is not None:
            plugins = [p for p in plugins if p.manifest.type == plugin_type]
        return plugins

    def enable_plugin(self, plugin_id: str) -> bool:
        plugin = self.get_plugin(plugin_id)
        plugin.enabled = True
        plugin.status = PluginStatus.ACTIVE
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        plugin = self.get_plugin(plugin_id)
        plugin.enabled = False
        plugin.status = PluginStatus.INACTIVE
        return True

    def get_plugin_config(self, plugin_id: str) -> dict:
        plugin = self.get_plugin(plugin_id)
        return plugin.config.copy()

    def update_plugin_config(self, plugin_id: str, config: dict) -> None:
        plugin = self.get_plugin(plugin_id)
        plugin.config.update(config)

    def validate_plugin(self, manifest: PluginManifest) -> list[str]:
        errors: list[str] = []
        if not manifest.name:
            errors.append("Plugin name is required")
        if not manifest.version:
            errors.append("Plugin version is required")
        if not manifest.entry_point:
            errors.append("Plugin entry_point is required")
        if manifest.version and not all(c.isdigit() or c == "." for c in manifest.version):
            errors.append("Plugin version must be semver format")
        return errors

    def get_plugin_api(self, plugin_id: str) -> dict:
        plugin = self.get_plugin(plugin_id)
        return {
            "id": plugin.id,
            "name": plugin.manifest.name,
            "version": plugin.manifest.version,
            "type": plugin.manifest.type.value,
            "status": plugin.status.value,
            "hooks": list(self._hooks.get(plugin_id, {}).keys()),
        }

    def execute_plugin_hook(self, plugin_id: str, hook: str, data: dict) -> dict:
        plugin = self.get_plugin(plugin_id)
        if not plugin.enabled:
            raise RuntimeError(f"Plugin '{plugin.manifest.name}' is disabled")
        hooks = self._hooks.get(plugin_id, {})
        if hook not in hooks:
            return {"status": "no_handler", "hook": hook, "data": data}
        try:
            result = hooks[hook](data)
            return {"status": "success", "result": result}
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error_message = str(e)
            return {"status": "error", "error": str(e)}


plugin_api = PluginAPI()
