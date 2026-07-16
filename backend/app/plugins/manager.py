from __future__ import annotations

import time
from dataclasses import dataclass, field

from .loader import plugin_loader
from .marketplace import plugin_marketplace
from .registry import PluginCategory, PluginStatus, plugin_registry
from .templates import plugin_template_registry


@dataclass
class PluginLog:
    plugin_id: str
    level: str
    message: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class PluginMetrics:
    plugin_id: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    avg_response_ms: float = 0.0
    last_called: float | None = None


class PluginManager:
    def __init__(self) -> None:
        self._logs: dict[str, list[PluginLog]] = {}
        self._metrics: dict[str, PluginMetrics] = {}
        self._backups: list[dict] = []

    def install_plugin(self, plugin_id: str, source: str = "marketplace") -> dict:
        if source == "marketplace":
            result = plugin_marketplace.install_plugin(plugin_id)
            if not result.get("success"):
                return result
        else:
            existing = plugin_registry.get_plugin(plugin_id)
            if existing is None:
                return {"success": False, "error": f"Plugin '{plugin_id}' not found"}

        self._log(plugin_id, "info", f"Plugin installed from {source}")
        self._init_metrics(plugin_id)

        return {
            "success": True,
            "plugin_id": plugin_id,
            "source": source,
            "message": f"Plugin '{plugin_id}' installed successfully",
        }

    def uninstall_plugin(self, plugin_id: str) -> dict:
        plugin = plugin_registry.get_plugin(plugin_id)
        if plugin is not None:
            plugin_loader.unload_plugin(plugin_id)

        result = plugin_marketplace.uninstall_plugin(plugin_id)
        if not result.get("success") and "not installed" not in result.get("error", ""):
            return result

        self._logs.pop(plugin_id, None)
        self._metrics.pop(plugin_id, None)

        self._log(plugin_id, "info", "Plugin uninstalled")

        return {
            "success": True,
            "plugin_id": plugin_id,
            "message": f"Plugin '{plugin_id}' uninstalled successfully",
        }

    def update_plugin(self, plugin_id: str) -> dict:
        plugin = plugin_registry.get_plugin(plugin_id)
        if plugin is not None:
            plugin.status = PluginStatus.updating

        result = plugin_marketplace.update_plugin(plugin_id)
        if not result.get("success"):
            if plugin is not None:
                plugin.status = PluginStatus.active
            return result

        if plugin is not None:
            plugin.status = PluginStatus.active

        self._log(plugin_id, "info", "Plugin updated")
        return result

    def enable_plugin(self, plugin_id: str) -> dict:
        success = plugin_registry.enable_plugin(plugin_id)
        if not success:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found"}

        self._log(plugin_id, "info", "Plugin enabled")
        return {"success": True, "plugin_id": plugin_id, "message": "Plugin enabled"}

    def disable_plugin(self, plugin_id: str) -> dict:
        success = plugin_registry.disable_plugin(plugin_id)
        if not success:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found"}

        self._log(plugin_id, "info", "Plugin disabled")
        return {"success": True, "plugin_id": plugin_id, "message": "Plugin disabled"}

    def get_plugin_status(self, plugin_id: str) -> dict:
        plugin = plugin_registry.get_plugin(plugin_id)
        if plugin is None:
            return {"plugin_id": plugin_id, "status": "not_found"}

        return {
            "plugin_id": plugin_id,
            "status": plugin.status.value,
            "enabled": plugin.enabled,
            "version": plugin.manifest.version,
            "name": plugin.manifest.name,
            "category": plugin.manifest.category.value,
            "installed_at": plugin.installed_at,
            "error_message": plugin.error_message,
            "update_available": plugin.update_available,
        }

    def get_all_plugins(self) -> list[dict]:
        plugins = plugin_registry.list_plugins()
        return [
            {
                "plugin_id": p.manifest.id,
                "name": p.manifest.name,
                "version": p.manifest.version,
                "status": p.status.value,
                "enabled": p.enabled,
                "category": p.manifest.category.value,
            }
            for p in plugins
        ]

    def search_plugins(self, query: str) -> list[dict]:
        marketplace_results = plugin_marketplace.search_plugins(query)
        installed = {p.manifest.id for p in plugin_registry.list_plugins()}

        results: list[dict] = []
        for mp in marketplace_results:
            pid = mp.manifest.get("id", "")
            results.append({
                "plugin_id": pid,
                "name": mp.manifest.get("name", ""),
                "description": mp.manifest.get("description", ""),
                "version": mp.manifest.get("version", ""),
                "category": mp.manifest.get("category", ""),
                "downloads": mp.downloads,
                "rating": mp.rating,
                "installed": pid in installed,
                "verified": mp.verified,
            })
        return results

    def validate_plugin(self, plugin_id: str) -> dict:
        plugin = plugin_registry.get_plugin(plugin_id)
        if plugin is None:
            return {"valid": False, "error": "Plugin not found in registry"}

        errors: list[str] = []
        warnings: list[str] = []

        manifest = plugin.manifest
        if not manifest.name:
            errors.append("Missing plugin name")
        if not manifest.version:
            errors.append("Missing plugin version")
        if not manifest.author:
            warnings.append("Missing author information")

        deps_valid = plugin_registry.validate_dependencies(plugin_id)
        if not deps_valid:
            missing = [
                d for d in plugin.manifest.dependencies
                if d not in plugin_registry._plugins
            ]
            errors.append(f"Missing dependencies: {', '.join(missing)}")

        instance = plugin_loader.get_plugin_instance(plugin_id)
        if instance is None and plugin.status == PluginStatus.active:
            warnings.append("Plugin is marked active but has no loaded instance")

        return {
            "valid": len(errors) == 0,
            "plugin_id": plugin_id,
            "errors": errors,
            "warnings": warnings,
            "has_instance": instance is not None,
            "dependencies_valid": deps_valid,
        }

    def get_plugin_logs(self, plugin_id: str) -> list[dict]:
        logs = self._logs.get(plugin_id, [])
        return [
            {
                "level": log.level,
                "message": log.message,
                "timestamp": log.timestamp,
            }
            for log in logs
        ]

    def restart_plugin(self, plugin_id: str) -> dict:
        plugin = plugin_registry.get_plugin(plugin_id)
        if plugin is None:
            return {"success": False, "error": f"Plugin '{plugin_id}' not found"}

        plugin.status = PluginStatus.updating
        self._log(plugin_id, "info", "Plugin restart initiated")

        plugin_loader.shutdown_plugin(plugin_id)

        initialized = plugin_loader.initialize_plugin(plugin_id)
        if not initialized:
            plugin.status = PluginStatus.error
            plugin.error_message = "Failed to reinitialize plugin"
            return {"success": False, "error": "Failed to reinitialize plugin"}

        plugin.status = PluginStatus.active
        self._log(plugin_id, "info", "Plugin restarted successfully")

        return {
            "success": True,
            "plugin_id": plugin_id,
            "message": "Plugin restarted successfully",
        }

    def get_plugin_metrics(self, plugin_id: str) -> dict:
        metrics = self._metrics.get(plugin_id)
        if metrics is None:
            return {
                "plugin_id": plugin_id,
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "avg_response_ms": 0.0,
                "last_called": None,
            }

        return {
            "plugin_id": metrics.plugin_id,
            "total_calls": metrics.total_calls,
            "successful_calls": metrics.successful_calls,
            "failed_calls": metrics.failed_calls,
            "success_rate": (
                round(metrics.successful_calls / metrics.total_calls * 100, 2)
                if metrics.total_calls > 0
                else 0.0
            ),
            "avg_response_ms": metrics.avg_response_ms,
            "last_called": metrics.last_called,
        }

    def backup_plugins(self) -> dict:
        plugins = plugin_registry.list_plugins()
        backup_data: list[dict] = []

        for plugin in plugins:
            backup_data.append({
                "plugin_id": plugin.manifest.id,
                "manifest": {
                    "id": plugin.manifest.id,
                    "name": plugin.manifest.name,
                    "version": plugin.manifest.version,
                    "author": plugin.manifest.author,
                    "description": plugin.manifest.description,
                    "category": plugin.manifest.category.value,
                    "permissions": plugin.manifest.permissions,
                    "dependencies": plugin.manifest.dependencies,
                    "tags": plugin.manifest.tags,
                },
                "config": plugin.config,
                "enabled": plugin.enabled,
            })

        backup = {
            "timestamp": time.time(),
            "plugin_count": len(backup_data),
            "plugins": backup_data,
        }
        self._backups.append(backup)

        return {
            "success": True,
            "backup_count": len(self._backups),
            "plugin_count": len(backup_data),
            "timestamp": backup["timestamp"],
        }

    def restore_plugins(self, backup: dict) -> dict:
        plugins_data = backup.get("plugins", [])
        restored: list[str] = []
        errors: list[str] = []

        for plugin_data in plugins_data:
            plugin_id = plugin_data.get("plugin_id", "")
            try:
                manifest_data = plugin_data.get("manifest", {})
                category = PluginCategory(manifest_data.get("category", "tool"))

                from .registry import PluginManifest

                manifest = PluginManifest(
                    id=manifest_data.get("id", plugin_id),
                    name=manifest_data.get("name", ""),
                    version=manifest_data.get("version", "0.1.0"),
                    author=manifest_data.get("author", ""),
                    description=manifest_data.get("description", ""),
                    category=category,
                    permissions=manifest_data.get("permissions", []),
                    dependencies=manifest_data.get("dependencies", []),
                    tags=manifest_data.get("tags", []),
                )

                plugin_registry.register_plugin(manifest)
                plugin = plugin_registry.get_plugin(plugin_id)
                if plugin is not None:
                    plugin.config.update(plugin_data.get("config", {}))
                    if plugin_data.get("enabled", True):
                        plugin_registry.enable_plugin(plugin_id)

                restored.append(plugin_id)
            except Exception as e:
                errors.append(f"Failed to restore {plugin_id}: {str(e)}")

        return {
            "success": len(errors) == 0,
            "restored": restored,
            "errors": errors,
            "total_restored": len(restored),
        }

    def get_marketplace_stats(self) -> dict:
        marketplace_plugins = plugin_marketplace.list_popular(limit=1000)
        installed_plugins = plugin_registry.list_plugins()
        categories = plugin_marketplace.list_categories()

        total_downloads = sum(p.downloads for p in marketplace_plugins)
        avg_rating = (
            round(
                sum(p.rating for p in marketplace_plugins) / len(marketplace_plugins),
                2,
            )
            if marketplace_plugins
            else 0.0
        )

        by_category: dict[str, int] = {}
        for plugin in installed_plugins:
            cat = plugin.manifest.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "marketplace": {
                "total_plugins": len(marketplace_plugins),
                "total_downloads": total_downloads,
                "average_rating": avg_rating,
                "categories": len(categories),
            },
            "installed": {
                "total": len(installed_plugins),
                "by_category": by_category,
                "active": len(
                    [
                        p
                        for p in installed_plugins
                        if p.status == PluginStatus.active
                    ]
                ),
            },
            "registry": plugin_registry.get_registry_stats(),
        }

    def _log(self, plugin_id: str, level: str, message: str) -> None:
        if plugin_id not in self._logs:
            self._logs[plugin_id] = []
        self._logs[plugin_id].append(
            PluginLog(plugin_id=plugin_id, level=level, message=message)
        )

    def _init_metrics(self, plugin_id: str) -> None:
        if plugin_id not in self._metrics:
            self._metrics[plugin_id] = PluginMetrics(plugin_id=plugin_id)


plugin_manager = PluginManager()
