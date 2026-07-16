from __future__ import annotations

import importlib
import importlib.util
import os
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from .registry import PluginCategory, plugin_registry


@dataclass
class LoadResult:
    success: bool
    plugin_id: str | None = None
    error: str | None = None
    duration_ms: float = 0.0


class PluginBase(Protocol):
    def initialize(self) -> None: ...
    def shutdown(self) -> None: ...
    def get_config_schema(self) -> dict: ...


class PluginLoader:
    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}
        self._modules: dict[str, Any] = {}

    def load_plugin(self, plugin_path: str) -> LoadResult:
        start = time.time()
        try:
            manifest_path = os.path.join(plugin_path, "manifest.json")
            if not os.path.exists(manifest_path):
                return LoadResult(success=False, error="manifest.json not found")

            import json

            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["category"] = PluginCategory(data["category"])
            from .registry import PluginManifest

            manifest = PluginManifest(**data)
            plugin_id = plugin_registry.register_plugin(manifest)

            entry_point = manifest.entry_point or "main"
            module_path = os.path.join(plugin_path, f"{entry_point}.py")
            if not os.path.exists(module_path):
                module_path = os.path.join(plugin_path, entry_point, "__init__.py")

            spec = importlib.util.spec_from_file_location(plugin_id, module_path)
            if spec is None or spec.loader is None:
                return LoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    error="Could not load module spec",
                )

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._modules[plugin_id] = module

            duration = (time.time() - start) * 1000
            return LoadResult(
                success=True, plugin_id=plugin_id, duration_ms=duration
            )
        except Exception as exc:
            duration = (time.time() - start) * 1000
            return LoadResult(success=False, error=str(exc), duration_ms=duration)

    def unload_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self._modules:
            return False
        self.shutdown_plugin(plugin_id)
        del self._modules[plugin_id]
        self._instances.pop(plugin_id, None)
        plugin_registry.unregister_plugin(plugin_id)
        return True

    def reload_plugin(self, plugin_id: str) -> LoadResult:
        plugin = plugin_registry.get_plugin(plugin_id)
        if plugin is None:
            return LoadResult(success=False, error="Plugin not found in registry")
        self.unload_plugin(plugin_id)
        return self.load_plugin(os.path.dirname(str(plugin.manifest)))

    def initialize_plugin(self, plugin_id: str) -> bool:
        module = self._modules.get(plugin_id)
        if module is None:
            return False
        try:
            plugin_class = getattr(module, "Plugin", None)
            if plugin_class is None:
                return False
            instance = plugin_class()
            instance.initialize()
            self._instances[plugin_id] = instance
            plugin = plugin_registry.get_plugin(plugin_id)
            if plugin is not None:
                from .registry import PluginStatus

                plugin.status = PluginStatus.active
            return True
        except Exception:
            return False

    def shutdown_plugin(self, plugin_id: str) -> bool:
        instance = self._instances.get(plugin_id)
        if instance is None:
            return False
        try:
            instance.shutdown()
        finally:
            self._instances.pop(plugin_id, None)
            plugin = plugin_registry.get_plugin(plugin_id)
            if plugin is not None:
                from .registry import PluginStatus

                plugin.status = PluginStatus.inactive
        return True

    def get_plugin_instance(self, plugin_id: str) -> Any | None:
        return self._instances.get(plugin_id)

    def call_plugin_hook(
        self, plugin_id: str, hook: str, *args: Any, **kwargs: Any
    ) -> Any:
        instance = self._instances.get(plugin_id)
        if instance is None:
            return None
        method = getattr(instance, hook, None)
        if method is None or not callable(method):
            return None
        return method(*args, **kwargs)

    def load_all_plugins(self) -> list[LoadResult]:
        results: list[LoadResult] = []
        plugins_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "installed"
        )
        if not os.path.isdir(plugins_dir):
            return results
        for entry in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, entry)
            if os.path.isdir(plugin_path):
                result = self.load_plugin(plugin_path)
                results.append(result)
                if result.success and result.plugin_id is not None:
                    self.initialize_plugin(result.plugin_id)
        return results

    def unload_all_plugins(self) -> None:
        for plugin_id in list(self._instances.keys()):
            self.unload_plugin(plugin_id)


class AgentPluginLoader(PluginLoader):
    def load_plugin(self, plugin_path: str) -> LoadResult:
        result = super().load_plugin(plugin_path)
        if result.success and result.plugin_id:
            plugin = plugin_registry.get_plugin(result.plugin_id)
            if plugin is not None:
                plugin.config["plugin_type"] = "agent"
        return result


class ToolPluginLoader(PluginLoader):
    def load_plugin(self, plugin_path: str) -> LoadResult:
        result = super().load_plugin(plugin_path)
        if result.success and result.plugin_id:
            plugin = plugin_registry.get_plugin(result.plugin_id)
            if plugin is not None:
                plugin.config["plugin_type"] = "tool"
        return result


class UIPluginLoader(PluginLoader):
    def load_plugin(self, plugin_path: str) -> LoadResult:
        result = super().load_plugin(plugin_path)
        if result.success and result.plugin_id:
            plugin = plugin_registry.get_plugin(result.plugin_id)
            if plugin is not None:
                plugin.config["plugin_type"] = "ui"
        return result


plugin_loader = PluginLoader()
