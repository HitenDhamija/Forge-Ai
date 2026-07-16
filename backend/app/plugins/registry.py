from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PluginCategory(Enum):
    agent = "agent"
    tool = "tool"
    workflow = "workflow"
    prompt = "prompt"
    knowledge = "knowledge"
    memory = "memory"
    ui = "ui"
    visualization = "visualization"
    deployment = "deployment"
    analytics = "analytics"
    notification = "notification"
    integration = "integration"


class PluginStatus(Enum):
    installed = "installed"
    active = "active"
    inactive = "inactive"
    error = "error"
    updating = "updating"
    deprecated = "deprecated"


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    author: str
    description: str
    category: PluginCategory
    permissions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    min_platform_version: str = "0.1.0"
    entry_point: str = "main"
    frontend_entry: str | None = None
    backend_entry: str | None = None
    config_schema: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    icon: str | None = None
    homepage: str | None = None
    repository: str | None = None


@dataclass
class InstalledPlugin:
    manifest: PluginManifest
    status: PluginStatus = PluginStatus.installed
    config: dict = field(default_factory=dict)
    installed_at: float = field(default_factory=time.time)
    enabled: bool = True
    error_message: str | None = None
    update_available: str | None = None


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, InstalledPlugin] = {}

    def register_plugin(self, manifest: PluginManifest) -> str:
        plugin_id = manifest.id
        self._plugins[plugin_id] = InstalledPlugin(manifest=manifest)
        return plugin_id

    def unregister_plugin(self, plugin_id: str) -> bool:
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            return True
        return False

    def get_plugin(self, plugin_id: str) -> InstalledPlugin | None:
        return self._plugins.get(plugin_id)

    def list_plugins(
        self,
        category: PluginCategory | None = None,
        status: PluginStatus | None = None,
    ) -> list[InstalledPlugin]:
        results: list[InstalledPlugin] = []
        for plugin in self._plugins.values():
            if category is not None and plugin.manifest.category != category:
                continue
            if status is not None and plugin.status != status:
                continue
            results.append(plugin)
        return results

    def get_active_plugins(self) -> list[InstalledPlugin]:
        return self.list_plugins(status=PluginStatus.active)

    def enable_plugin(self, plugin_id: str) -> bool:
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return False
        plugin.enabled = True
        plugin.status = PluginStatus.active
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return False
        plugin.enabled = False
        plugin.status = PluginStatus.inactive
        return True

    def update_plugin_config(self, plugin_id: str, config: dict) -> None:
        plugin = self.get_plugin(plugin_id)
        if plugin is not None:
            plugin.config.update(config)

    def get_plugin_config(self, plugin_id: str) -> dict:
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return {}
        return dict(plugin.config)

    def check_updates(self) -> list[dict]:
        updates: list[dict] = []
        for plugin in self._plugins.values():
            if plugin.update_available is not None:
                updates.append(
                    {
                        "plugin_id": plugin.manifest.id,
                        "current_version": plugin.manifest.version,
                        "available_version": plugin.update_available,
                    }
                )
        return updates

    def get_dependencies(self, plugin_id: str) -> list[str]:
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            return []
        return list(plugin.manifest.dependencies)

    def validate_dependencies(self, plugin_id: str) -> bool:
        deps = self.get_dependencies(plugin_id)
        return all(dep in self._plugins for dep in deps)

    def get_registry_stats(self) -> dict:
        total = len(self._plugins)
        by_status: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for plugin in self._plugins.values():
            status_key = plugin.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1
            cat_key = plugin.manifest.category.value
            by_category[cat_key] = by_category.get(cat_key, 0) + 1
        return {
            "total": total,
            "by_status": by_status,
            "by_category": by_category,
        }


plugin_registry = PluginRegistry()
