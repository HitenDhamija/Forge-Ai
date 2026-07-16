"""Configuration center for the ForgeAI Developer Experience.

Provides a centralised, section-based configuration store with defaults,
validation, import/export, and convenience accessors for common subsystems.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class ConfigProfile(str, Enum):
    """Runtime configuration profile."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class ConfigSection:
    """A named group of related configuration settings."""

    name: str
    description: str
    settings: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Default configuration values
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, dict[str, Any]] = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "forgeai",
        "user": "forgeai",
        "password": "",
        "pool_size": 10,
        "max_overflow": 20,
        "echo": False,
        "ssl_mode": "prefer",
    },
    "cache": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
        "password": "",
        "key_prefix": "forge:",
        "default_ttl": 3600,
        "max_connections": 50,
    },
    "security": {
        "jwt_secret": "CHANGE-ME-IN-PRODUCTION",
        "jwt_algorithm": "HS256",
        "jwt_expiration_minutes": 30,
        "jwt_refresh_expiration_days": 7,
        "cors_origins": ["http://localhost:3000"],
        "cors_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "rate_limit_requests": 100,
        "rate_limit_window_seconds": 60,
        "password_min_length": 8,
        "password_require_uppercase": True,
        "password_require_digit": True,
        "password_require_special": True,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        "output": "console",
        "file_path": "logs/forgeai.log",
        "max_bytes": 10485760,
        "backup_count": 5,
        "json_format": False,
    },
    "monitoring": {
        "enabled": True,
        "metrics_port": 9090,
        "health_check_path": "/health",
        "health_check_interval_seconds": 30,
        "alerting_enabled": False,
        "alerting_webhook": "",
        "tracing_enabled": False,
        "tracing_endpoint": "",
    },
    "ai": {
        "provider": "ollama",
        "model": "llama3",
        "ollama_host": "http://localhost:11434",
        "ollama_timeout_seconds": 120,
        "embedding_model": "nomic-embed-text",
        "max_tokens": 4096,
        "temperature": 0.7,
        "top_p": 0.9,
        "context_window": 8192,
        "streaming": True,
    },
    "storage": {
        "backend": "local",
        "local_path": "./data/storage",
        "s3_bucket": "",
        "s3_region": "us-east-1",
        "s3_access_key": "",
        "s3_secret_key": "",
        "max_upload_size_mb": 50,
        "allowed_extensions": ["txt", "json", "csv", "pdf", "md", "yaml", "yml"],
    },
}


# ---------------------------------------------------------------------------
# Configuration Center
# ---------------------------------------------------------------------------

class ConfigurationCenter:
    """Central store for all ForgeAI configuration.

    Configuration is organised into named *sections*, each containing a flat
    dictionary of key-value pairs.  Defaults are loaded on init and can be
    overridden via ``set`` or bulk ``import_config``.
    """

    def __init__(self, profile: ConfigProfile | None = None) -> None:
        self.profile = profile or ConfigProfile.DEVELOPMENT
        self._sections: dict[str, ConfigSection] = {}
        self._init_defaults()

    # -- core accessors -----------------------------------------------------

    def get(self, section: str, key: str | None = None) -> Any:
        """Return a config value.

        If *key* is ``None`` the entire section dict is returned.
        Raises ``KeyError`` when *key* does not exist within *section*.
        """
        sec = self._sections.get(section)
        if sec is None:
            raise KeyError(f"Unknown config section: {section}")
        if key is None:
            return copy.deepcopy(sec.settings)
        if key not in sec.settings:
            raise KeyError(f"Key '{key}' not found in section '{section}'")
        return copy.deepcopy(sec.settings[key])

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a single config value."""
        if section not in self._sections:
            self._sections[section] = ConfigSection(
                name=section,
                description=f"Dynamically created section: {section}",
            )
        self._sections[section].settings[key] = value
        logger.debug("Config set: %s.%s = %s", section, key, value)

    def get_section(self, section: str) -> ConfigSection:
        """Return the full ``ConfigSection`` object for *section*."""
        sec = self._sections.get(section)
        if sec is None:
            raise KeyError(f"Unknown config section: {section}")
        return copy.deepcopy(sec)

    def list_sections(self) -> list[str]:
        """Return the names of all registered sections."""
        return sorted(self._sections.keys())

    # -- bulk operations ----------------------------------------------------

    def export_config(self) -> dict[str, Any]:
        """Export the entire configuration as a plain dict."""
        return {name: copy.deepcopy(sec.settings) for name, sec in self._sections.items()}

    def import_config(self, config: dict[str, Any]) -> None:
        """Merge *config* into the current store.

        Top-level keys are section names; values must be dicts of key-value
        pairs.  Existing keys are overwritten.
        """
        for section_name, settings in config.items():
            if not isinstance(settings, dict):
                logger.warning("Skipping non-dict config entry: %s", section_name)
                continue
            if section_name in self._sections:
                self._sections[section_name].settings.update(settings)
            else:
                self._sections[section_name] = ConfigSection(
                    name=section_name,
                    description=f"Imported section: {section_name}",
                    settings=settings,
                )

    def validate(self) -> list[dict[str, Any]]:
        """Run validation rules against the current config.

        Returns a list of issue dicts, each with ``section``, ``key``,
        ``level`` (``error`` | ``warning``) and ``message``.
        """
        issues: list[dict[str, Any]] = []

        # security checks
        sec = self._sections.get("security")
        if sec:
            jwt_secret = sec.settings.get("jwt_secret", "")
            if jwt_secret in ("", "CHANGE-ME-IN-PRODUCTION"):
                issues.append({
                    "section": "security",
                    "key": "jwt_secret",
                    "level": "error",
                    "message": "JWT secret must be changed from the default value.",
                })
            min_len = sec.settings.get("password_min_length", 0)
            if min_len < 8:
                issues.append({
                    "section": "security",
                    "key": "password_min_length",
                    "level": "warning",
                    "message": "Password minimum length should be at least 8.",
                })

        # database checks
        db = self._sections.get("database")
        if db:
            if not db.settings.get("password"):
                issues.append({
                    "section": "database",
                    "key": "password",
                    "level": "warning",
                    "message": "Database password is empty.",
                })

        # ai checks
        ai = self._sections.get("ai")
        if ai:
            temp = ai.settings.get("temperature", 0.7)
            if temp > 1.0:
                issues.append({
                    "section": "ai",
                    "key": "temperature",
                    "level": "warning",
                    "message": "Temperature above 1.0 may produce incoherent output.",
                })

        return issues

    # -- defaults -----------------------------------------------------------

    def get_defaults(self) -> dict[str, Any]:
        """Return the default configuration values."""
        return copy.deepcopy(_DEFAULTS)

    def reset_section(self, section: str) -> None:
        """Reset *section* back to its default values."""
        defaults = _DEFAULTS.get(section)
        if defaults is None:
            raise KeyError(f"No defaults defined for section: {section}")
        self._sections[section] = ConfigSection(
            name=section,
            description=self._sections[section].description if section in self._sections else section,
            settings=copy.deepcopy(defaults),
        )
        logger.info("Reset config section to defaults: %s", section)

    # -- convenience accessors ----------------------------------------------

    def get_database_config(self) -> dict[str, Any]:
        """Return the ``database`` section as a plain dict."""
        return self.get("database")

    def get_cache_config(self) -> dict[str, Any]:
        """Return the ``cache`` section as a plain dict."""
        return self.get("cache")

    def get_security_config(self) -> dict[str, Any]:
        """Return the ``security`` section as a plain dict."""
        return self.get("security")

    def get_logging_config(self) -> dict[str, Any]:
        """Return the ``logging`` section as a plain dict."""
        return self.get("logging")

    def get_monitoring_config(self) -> dict[str, Any]:
        """Return the ``monitoring`` section as a plain dict."""
        return self.get("monitoring")

    # -- internal -----------------------------------------------------------

    def _init_defaults(self) -> None:
        """Populate sections from the default values."""
        for section_name, settings in _DEFAULTS.items():
            self._sections[section_name] = ConfigSection(
                name=section_name,
                description=f"{section_name.capitalize()} configuration",
                settings=copy.deepcopy(settings),
            )


# ---------------------------------------------------------------------------
# Global configuration center instance
# ---------------------------------------------------------------------------

config_center = ConfigurationCenter()
