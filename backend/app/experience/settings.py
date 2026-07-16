from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SettingsCategory(Enum):
    GENERAL = "general"
    MODELS = "models"
    AGENTS = "agents"
    PLUGINS = "plugins"
    ORGANIZATIONS = "organizations"
    SECURITY = "security"
    APPEARANCE = "appearance"
    NOTIFICATIONS = "notifications"
    DEVELOPER = "developer"


class SettingType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"
    MULTISELECT = "multiselect"
    JSON = "json"
    COLOR = "color"


@dataclass
class SettingDefinition:
    key: str
    label: str
    description: str
    type: SettingType
    category: SettingsCategory
    default: Any = None
    options: list[dict[str, str]] = field(default_factory=list)
    required: bool = False
    group: str = ""


@dataclass
class SettingValue:
    key: str
    value: Any
    updated_at: str = ""


class SettingsHub:
    def __init__(self) -> None:
        self._definitions: dict[str, SettingDefinition] = {}
        self._values: dict[str, SettingValue] = {}
        self._populate_defaults()

    def _populate_defaults(self) -> None:
        definitions: list[SettingDefinition] = [
            SettingDefinition(
                key="app_name",
                label="Application Name",
                description="The display name of your ForgeAI instance",
                type=SettingType.STRING,
                category=SettingsCategory.GENERAL,
                default="ForgeAI",
                required=True,
                group="Basic",
            ),
            SettingDefinition(
                key="app_url",
                label="Application URL",
                description="The public URL of your ForgeAI instance",
                type=SettingType.STRING,
                category=SettingsCategory.GENERAL,
                default="http://localhost:3000",
                required=True,
                group="Basic",
            ),
            SettingDefinition(
                key="timezone",
                label="Timezone",
                description="Default timezone for the application",
                type=SettingType.SELECT,
                category=SettingsCategory.GENERAL,
                default="UTC",
                options=[
                    {"value": "UTC", "label": "UTC"},
                    {"value": "America/New_York", "label": "Eastern Time"},
                    {"value": "America/Chicago", "label": "Central Time"},
                    {"value": "America/Denver", "label": "Mountain Time"},
                    {"value": "America/Los_Angeles", "label": "Pacific Time"},
                    {"value": "Europe/London", "label": "London"},
                    {"value": "Europe/Berlin", "label": "Berlin"},
                    {"value": "Asia/Tokyo", "label": "Tokyo"},
                    {"value": "Asia/Shanghai", "label": "Shanghai"},
                ],
                group="Regional",
            ),
            SettingDefinition(
                key="language",
                label="Language",
                description="Default language for the interface",
                type=SettingType.SELECT,
                category=SettingsCategory.GENERAL,
                default="en",
                options=[
                    {"value": "en", "label": "English"},
                    {"value": "es", "label": "Spanish"},
                    {"value": "fr", "label": "French"},
                    {"value": "de", "label": "German"},
                    {"value": "ja", "label": "Japanese"},
                    {"value": "zh", "label": "Chinese"},
                ],
                group="Regional",
            ),
            SettingDefinition(
                key="default_model",
                label="Default Model",
                description="The default AI model for agents and completions",
                type=SettingType.SELECT,
                category=SettingsCategory.MODELS,
                default="gpt-4o",
                options=[
                    {"value": "gpt-4o", "label": "GPT-4o"},
                    {"value": "gpt-4o-mini", "label": "GPT-4o Mini"},
                    {"value": "claude-3-opus", "label": "Claude 3 Opus"},
                    {"value": "claude-3-sonnet", "label": "Claude 3 Sonnet"},
                    {"value": "claude-3-haiku", "label": "Claude 3 Haiku"},
                    {"value": "llama-3-70b", "label": "Llama 3 70B"},
                ],
                group="Model Configuration",
            ),
            SettingDefinition(
                key="ollama_url",
                label="Ollama URL",
                description="Base URL for local Ollama instance",
                type=SettingType.STRING,
                category=SettingsCategory.MODELS,
                default="http://localhost:11434",
                group="Model Configuration",
            ),
            SettingDefinition(
                key="temperature",
                label="Temperature",
                description="Default temperature for model completions",
                type=SettingType.NUMBER,
                category=SettingsCategory.MODELS,
                default=0.7,
                group="Model Parameters",
            ),
            SettingDefinition(
                key="max_tokens",
                label="Max Tokens",
                description="Maximum tokens for model completions",
                type=SettingType.NUMBER,
                category=SettingsCategory.MODELS,
                default=4096,
                group="Model Parameters",
            ),
            SettingDefinition(
                key="theme",
                label="Theme",
                description="Visual theme for the interface",
                type=SettingType.SELECT,
                category=SettingsCategory.APPEARANCE,
                default="system",
                options=[
                    {"value": "light", "label": "Light"},
                    {"value": "dark", "label": "Dark"},
                    {"value": "system", "label": "System"},
                ],
                group="Theme",
            ),
            SettingDefinition(
                key="accent_color",
                label="Accent Color",
                description="Primary accent color for the interface",
                type=SettingType.COLOR,
                category=SettingsCategory.APPEARANCE,
                default="#6366f1",
                group="Theme",
            ),
            SettingDefinition(
                key="sidebar_collapsed",
                label="Sidebar Collapsed",
                description="Whether the sidebar starts collapsed",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.APPEARANCE,
                default=False,
                group="Layout",
            ),
            SettingDefinition(
                key="compact_mode",
                label="Compact Mode",
                description="Use compact spacing throughout the interface",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.APPEARANCE,
                default=False,
                group="Layout",
            ),
            SettingDefinition(
                key="email_enabled",
                label="Email Notifications",
                description="Enable email notifications",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.NOTIFICATIONS,
                default=True,
                group="Channels",
            ),
            SettingDefinition(
                key="workflow_notifications",
                label="Workflow Notifications",
                description="Notify on workflow completion or failure",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.NOTIFICATIONS,
                default=True,
                group="Triggers",
            ),
            SettingDefinition(
                key="agent_notifications",
                label="Agent Notifications",
                description="Notify on agent execution events",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.NOTIFICATIONS,
                default=True,
                group="Triggers",
            ),
            SettingDefinition(
                key="debug_mode",
                label="Debug Mode",
                description="Enable debug logging and verbose output",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.DEVELOPER,
                default=False,
                group="Development",
            ),
            SettingDefinition(
                key="api_logging",
                label="API Logging",
                description="Log all API requests and responses",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.DEVELOPER,
                default=False,
                group="Development",
            ),
            SettingDefinition(
                key="beta_features",
                label="Beta Features",
                description="Enable access to beta and experimental features",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.DEVELOPER,
                default=False,
                group="Development",
            ),
            SettingDefinition(
                key="session_timeout",
                label="Session Timeout (minutes)",
                description="Idle session timeout in minutes",
                type=SettingType.NUMBER,
                category=SettingsCategory.SECURITY,
                default=60,
                group="Sessions",
            ),
            SettingDefinition(
                key="mfa_enabled",
                label="Multi-Factor Authentication",
                description="Require MFA for all users",
                type=SettingType.BOOLEAN,
                category=SettingsCategory.SECURITY,
                default=False,
                group="Authentication",
            ),
            SettingDefinition(
                key="allowed_ip_ranges",
                label="Allowed IP Ranges",
                description="Comma-separated list of allowed CIDR ranges",
                type=SettingType.STRING,
                category=SettingsCategory.SECURITY,
                default="",
                group="Network",
            ),
        ]

        for definition in definitions:
            self._definitions[definition.key] = definition
            self._values[definition.key] = SettingValue(
                key=definition.key,
                value=definition.default,
                updated_at=datetime.utcnow().isoformat(),
            )

    def get_setting(self, key: str) -> SettingDefinition | None:
        return self._definitions.get(key)

    def get_settings(
        self, category: SettingsCategory | None = None
    ) -> list[SettingDefinition]:
        if category is None:
            return list(self._definitions.values())
        return [
            d for d in self._definitions.values() if d.category == category
        ]

    def get_value(self, key: str) -> Any:
        sv = self._values.get(key)
        return sv.value if sv else None

    def set_value(self, key: str, value: Any) -> bool:
        if key not in self._definitions:
            return False
        self._values[key] = SettingValue(
            key=key, value=value, updated_at=datetime.utcnow().isoformat()
        )
        return True

    def get_category(self, category: SettingsCategory) -> dict:
        definitions = self.get_settings(category)
        return {
            "category": category.value,
            "settings": [
                {
                    **{
                        "key": d.key,
                        "label": d.label,
                        "description": d.description,
                        "type": d.type.value,
                        "default": d.default,
                        "options": d.options,
                        "required": d.required,
                        "group": d.group,
                    },
                    "current_value": self.get_value(d.key),
                }
                for d in definitions
            ],
        }

    def get_all_values(self) -> dict:
        return {k: sv.value for k, sv in self._values.items()}

    def reset_setting(self, key: str) -> bool:
        definition = self._definitions.get(key)
        if definition is None:
            return False
        self._values[key] = SettingValue(
            key=key,
            value=definition.default,
            updated_at=datetime.utcnow().isoformat(),
        )
        return True

    def reset_category(self, category: SettingsCategory) -> int:
        count = 0
        for key, definition in self._definitions.items():
            if definition.category == category:
                self._values[key] = SettingValue(
                    key=key,
                    value=definition.default,
                    updated_at=datetime.utcnow().isoformat(),
                )
                count += 1
        return count

    def export_settings(self) -> dict:
        return {k: sv.value for k, sv in self._values.items()}

    def import_settings(self, settings: dict) -> int:
        count = 0
        for key, value in settings.items():
            if key in self._definitions:
                self._values[key] = SettingValue(
                    key=key,
                    value=value,
                    updated_at=datetime.utcnow().isoformat(),
                )
                count += 1
        return count

    def validate_settings(self) -> list[dict]:
        errors: list[dict] = []
        for key, definition in self._definitions.items():
            if definition.required:
                value = self.get_value(key)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    errors.append(
                        {
                            "key": key,
                            "label": definition.label,
                            "error": "This setting is required",
                        }
                    )
            if definition.type == SettingType.NUMBER:
                value = self.get_value(key)
                if value is not None:
                    try:
                        float(value)
                    except (TypeError, ValueError):
                        errors.append(
                            {
                                "key": key,
                                "label": definition.label,
                                "error": "Value must be a number",
                            }
                        )
            if definition.type == SettingType.SELECT and definition.options:
                value = self.get_value(key)
                if value is not None:
                    valid_values = [o["value"] for o in definition.options]
                    if value not in valid_values:
                        errors.append(
                            {
                                "key": key,
                                "label": definition.label,
                                "error": f"Value must be one of: {', '.join(valid_values)}",
                            }
                        )
        return errors


settings_hub = SettingsHub()
