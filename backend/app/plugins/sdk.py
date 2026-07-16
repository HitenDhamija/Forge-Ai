"""Plugin SDK for developers building ForgeAI plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class PluginAPI:
    """API surface exposed to a single plugin for accessing platform features."""

    def __init__(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id

    # ------------------------------------------------------------------
    # Repositories
    # ------------------------------------------------------------------

    def get_repositories(self) -> list[dict]:
        return []

    def get_repository(self, repo_id: str) -> dict:
        return {"id": repo_id, "name": "", "owner": ""}

    def analyze_repository(self, repo_id: str) -> dict:
        return {"repo_id": repo_id, "analysis": {}}

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def search_memory(self, query: str) -> list[dict]:
        return []

    def add_memory(self, content: dict) -> str:
        return ""

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    def get_agents(self) -> list[dict]:
        return []

    def execute_agent(self, agent_id: str, task: str) -> dict:
        return {"agent_id": agent_id, "task": task, "result": {}}

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    def get_workflows(self) -> list[dict]:
        return []

    def execute_workflow(self, workflow_id: str, data: dict) -> dict:
        return {"workflow_id": workflow_id, "status": "completed", "result": {}}

    # ------------------------------------------------------------------
    # Knowledge & metrics
    # ------------------------------------------------------------------

    def get_knowledge_graph(self) -> dict:
        return {"nodes": [], "edges": []}

    def get_metrics(self) -> dict:
        return {"memory_usage_mb": 0.0, "cpu_percent": 0.0}

    # ------------------------------------------------------------------
    # Events & notifications
    # ------------------------------------------------------------------

    def log_event(self, event_type: str, data: dict) -> None:
        pass

    def send_notification(self, title: str, message: str) -> None:
        pass


# ------------------------------------------------------------------
# Built-in plugin examples
# ------------------------------------------------------------------

BUILTIN_EXAMPLES: list[dict[str, Any]] = [
    {
        "id": "github_plugin",
        "name": "GitHub Integration",
        "description": "Interact with GitHub repositories, issues, and pull requests.",
        "entry_point": "plugins.github.main:GitHubPlugin",
        "version": "1.0.0",
        "author": "ForgeAI",
        "permissions": ["read_repositories", "access_network"],
        "config_schema": {
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "GitHub personal access token"},
                "org": {"type": "string", "description": "GitHub organisation to monitor"},
            },
            "required": ["token"],
        },
    },
    {
        "id": "slack_plugin",
        "name": "Slack Notifications",
        "description": "Send notifications to Slack channels.",
        "entry_point": "plugins.slack.main:SlackPlugin",
        "version": "1.0.0",
        "author": "ForgeAI",
        "permissions": ["access_network"],
        "config_schema": {
            "type": "object",
            "properties": {
                "webhook_url": {"type": "string", "description": "Slack incoming webhook URL"},
                "channel": {"type": "string", "description": "Default channel"},
            },
            "required": ["webhook_url"],
        },
    },
    {
        "id": "jira_plugin",
        "name": "Jira Workflow",
        "description": "Create and manage Jira issues and workflows.",
        "entry_point": "plugins.jira.main:JiraPlugin",
        "version": "1.0.0",
        "author": "ForgeAI",
        "permissions": ["read_repositories", "write_repositories", "access_network"],
        "config_schema": {
            "type": "object",
            "properties": {
                "base_url": {"type": "string", "description": "Jira instance URL"},
                "email": {"type": "string", "description": "Jira account email"},
                "api_token": {"type": "string", "description": "Jira API token"},
            },
            "required": ["base_url", "email", "api_token"],
        },
    },
    {
        "id": "docker_plugin",
        "name": "Docker Deployment",
        "description": "Build and deploy Docker containers.",
        "entry_point": "plugins.docker.main:DockerPlugin",
        "version": "1.0.0",
        "author": "ForgeAI",
        "permissions": ["access_network", "write_files", "execute_workflows"],
        "config_schema": {
            "type": "object",
            "properties": {
                "registry": {"type": "string", "description": "Docker registry URL"},
                "image_prefix": {"type": "string", "description": "Image name prefix"},
            },
        },
    },
    {
        "id": "custom_agent_plugin",
        "name": "Custom Agent Example",
        "description": "Example plugin that registers a custom agent.",
        "entry_point": "plugins.custom_agent.main:CustomAgentPlugin",
        "version": "1.0.0",
        "author": "ForgeAI",
        "permissions": ["manage_agents", "read_memory", "write_memory"],
        "config_schema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Name of the custom agent"},
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of agent capabilities",
                },
            },
            "required": ["agent_name"],
        },
    },
]


# ------------------------------------------------------------------
# PluginSDK
# ------------------------------------------------------------------

class PluginSDK:
    """High-level SDK for plugin creation, validation, and management."""

    def __init__(self) -> None:
        self._apis: dict[str, PluginAPI] = {}

    def create_plugin(self, config: dict) -> dict:
        scaffold = {
            "id": config.get("id", "my_plugin"),
            "name": config.get("name", "My Plugin"),
            "version": config.get("version", "0.1.0"),
            "description": config.get("description", ""),
            "author": config.get("author", ""),
            "entry_point": f"plugins.{config.get('id', 'my_plugin')}.main:{config.get('class_name', 'MyPlugin')}",
            "permissions": config.get("permissions", []),
            "dependencies": config.get("dependencies", []),
            "config_schema": config.get("config_schema", {"type": "object", "properties": {}}),
        }
        return {"status": "created", "manifest": scaffold}

    def get_api(self, plugin_id: str) -> PluginAPI:
        if plugin_id not in self._apis:
            self._apis[plugin_id] = PluginAPI(plugin_id)
        return self._apis[plugin_id]

    def get_sdk_docs(self) -> dict:
        return {
            "title": "ForgeAI Plugin SDK",
            "version": "1.0.0",
            "sections": [
                {
                    "title": "Getting Started",
                    "content": (
                        "Create a plugin by defining a manifest dict with id, name, version, "
                        "entry_point, and permissions. Use PluginAPI to interact with the platform."
                    ),
                },
                {
                    "title": "PluginAPI Reference",
                    "content": "The PluginAPI provides access to repositories, memory, agents, workflows, and more.",
                    "methods": [
                        "get_repositories() -> list[dict]",
                        "get_repository(repo_id: str) -> dict",
                        "analyze_repository(repo_id: str) -> dict",
                        "search_memory(query: str) -> list[dict]",
                        "add_memory(content: dict) -> str",
                        "get_agents() -> list[dict]",
                        "execute_agent(agent_id: str, task: str) -> dict",
                        "get_workflows() -> list[dict]",
                        "execute_workflow(workflow_id: str, data: dict) -> dict",
                        "get_knowledge_graph() -> dict",
                        "get_metrics() -> dict",
                        "log_event(event_type: str, data: dict) -> None",
                        "send_notification(title: str, message: str) -> None",
                    ],
                },
                {
                    "title": "Permissions",
                    "content": "Declare required permissions in your manifest. Available: read_repositories, write_repositories, read_memory, write_memory, execute_workflows, manage_agents, access_network, read_files, write_files, manage_plugins.",
                },
            ],
        }

    def get_examples(self) -> list[dict]:
        return list(BUILTIN_EXAMPLES)

    def validate_plugin_code(self, code: str) -> dict:
        issues: list[dict[str, str]] = []
        warnings: list[str] = []

        if "import os" in code and "subprocess" not in code:
            warnings.append("Direct os module usage detected. Prefer using PluginAPI methods.")

        dangerous = ["eval(", "exec(", "os.system(", "__import__("]
        for pattern in dangerous:
            if pattern in code:
                issues.append({
                    "severity": "error",
                    "message": f"Potentially dangerous call detected: {pattern}",
                })

        if "class " not in code:
            warnings.append("No class definition found. Plugins should define a plugin class.")

        if "def __init__" not in code and "class " in code:
            warnings.append("Plugin class is missing an __init__ method.")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }


plugin_sdk = PluginSDK()
