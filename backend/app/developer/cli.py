"""CLI command definitions and registry for ForgeAI Developer Experience.

Defines the command structure, categories, and pre-built commands available
through the ForgeAI CLI interface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class CommandCategory(str, Enum):
    """Functional category for a CLI command."""

    CORE = "core"
    REPOSITORY = "repository"
    WORKFLOW = "workflow"
    AGENT = "agent"
    MEMORY = "memory"
    SYSTEM = "system"
    PLUGIN = "plugin"
    BACKUP = "backup"


@dataclass
class CommandDefinition:
    """Metadata that describes a single CLI command / sub-command."""

    name: str
    description: str
    category: CommandCategory
    usage: str = ""
    examples: list[str] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)
    handler: str = ""


@dataclass
class CLICommand:
    """Top-level CLI command that may contain sub-commands and options."""

    name: str
    description: str
    subcommands: list[CommandDefinition] = field(default_factory=list)
    options: dict[str, str] = field(default_factory=dict)
    handler: Callable[..., dict[str, Any]] | None = None


# ---------------------------------------------------------------------------
# CLI Registry
# ---------------------------------------------------------------------------

class CLIRegistry:
    """Central registry for all ForgeAI CLI commands.

    Provides registration, lookup, help generation and (simulated) execution.
    """

    def __init__(self) -> None:
        self._commands: dict[str, CLICommand] = {}
        self._register_defaults()

    # -- public API ---------------------------------------------------------

    def register_command(self, command: CLICommand) -> None:
        """Register a new CLI command."""
        self._commands[command.name] = command
        logger.debug("Registered CLI command: %s", command.name)

    def get_command(self, name: str) -> CLICommand | None:
        """Return the command with *name*, or ``None`` if not found."""
        return self._commands.get(name)

    def list_commands(self, category: CommandCategory | None = None) -> list[CLICommand]:
        """Return registered commands, optionally filtered by *category*."""
        commands = list(self._commands.values())
        if category is not None:
            commands = [
                cmd
                for cmd in commands
                if any(sub.category == category for sub in cmd.subcommands)
                or (not cmd.subcommands and category == CommandCategory.CORE)
            ]
        return sorted(commands, key=lambda c: c.name)

    def get_help(self, name: str | None = None) -> str:
        """Return human-readable help text for one or all commands."""
        if name:
            cmd = self._commands.get(name)
            if cmd is None:
                return f"No command found: {name}"
            return self._format_command_help(cmd)

        lines: list[str] = ["ForgeAI CLI - Available Commands", "=" * 40, ""]
        for cmd in sorted(self._commands.values(), key=lambda c: c.name):
            lines.append(f"  forge {cmd.name:<14} {cmd.description}")
            for sub in cmd.subcommands:
                lines.append(f"    {sub.name:<14} {sub.description}")
        lines.append("")
        lines.append("Run 'forge <command> --help' for detailed usage.")
        return "\n".join(lines)

    def execute_command(self, name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """Simulate execution of *name* with the given *args*.

        Returns a result dict with ``status``, ``command``, ``args`` and
        ``message`` keys.
        """
        cmd = self._commands.get(name)
        if cmd is None:
            return {"status": "error", "command": name, "message": f"Unknown command: {name}"}

        args = args or {}

        if cmd.handler is not None:
            try:
                return cmd.handler(**args)
            except Exception as exc:
                logger.exception("Handler failed for command %s", name)
                return {"status": "error", "command": name, "message": str(exc)}

        return {
            "status": "success",
            "command": name,
            "args": args,
            "message": f"Command '{name}' executed (simulated).",
        }

    # -- internal helpers ---------------------------------------------------

    def _format_command_help(self, cmd: CLICommand) -> str:
        lines: list[str] = [
            f"forge {cmd.name} - {cmd.description}",
            "",
            "Subcommands:",
        ]
        for sub in cmd.subcommands:
            lines.append(f"  {sub.name:<16} {sub.description}")
            if sub.usage:
                lines.append(f"    Usage: {sub.usage}")
            for example in sub.examples:
                lines.append(f"    Example: {example}")
        if cmd.options:
            lines.append("")
            lines.append("Options:")
            for opt, desc in cmd.options.items():
                lines.append(f"  {opt:<16} {desc}")
        return "\n".join(lines)

    def _register_defaults(self) -> None:
        """Register the built-in ForgeAI CLI commands."""

        # -- core ------------------------------------------------------------

        self.register_command(CLICommand(
            name="init",
            description="Initialize a new ForgeAI project in the current directory",
            options={
                "--name": "Project name",
                "--template": "Project template (minimal, standard, full)",
                "--git": "Initialize git repository (default: true)",
            },
            handler=_handle_init,
        ))

        self.register_command(CLICommand(
            name="doctor",
            description="Run system diagnostics and health checks",
            options={
                "--fix": "Attempt to fix detected issues",
                "--verbose": "Show detailed output",
            },
            handler=_handle_doctor,
        ))

        self.register_command(CLICommand(
            name="start",
            description="Start all ForgeAI services",
            options={
                "--services": "Comma-separated list of services to start",
                "--detach": "Run in background mode",
            },
            handler=_handle_start,
        ))

        self.register_command(CLICommand(
            name="stop",
            description="Stop all ForgeAI services",
            options={
                "--services": "Comma-separated list of services to stop",
                "--graceful": "Wait for in-flight operations to complete",
            },
            handler=_handle_stop,
        ))

        self.register_command(CLICommand(
            name="status",
            description="Show status of all ForgeAI services",
            options={
                "--json": "Output as JSON",
                "--watch": "Continuously refresh status",
            },
            handler=_handle_status,
        ))

        self.register_command(CLICommand(
            name="logs",
            description="View logs from ForgeAI services",
            options={
                "--service": "Filter by service name",
                "--level": "Filter by log level (debug, info, warn, error)",
                "--tail": "Number of recent lines to show",
                "--follow": "Follow log output in real time",
            },
            handler=_handle_logs,
        ))

        self.register_command(CLICommand(
            name="config",
            description="View or modify ForgeAI configuration",
            subcommands=[
                CommandDefinition(
                    name="get",
                    description="Get a configuration value",
                    category=CommandCategory.SYSTEM,
                    usage="forge config get <section>.<key>",
                    examples=["forge config get database.host"],
                ),
                CommandDefinition(
                    name="set",
                    description="Set a configuration value",
                    category=CommandCategory.SYSTEM,
                    usage="forge config set <section>.<key> <value>",
                    examples=["forge config set database.port 5432"],
                ),
                CommandDefinition(
                    name="list",
                    description="List all configuration sections",
                    category=CommandCategory.SYSTEM,
                    usage="forge config list",
                ),
                CommandDefinition(
                    name="validate",
                    description="Validate current configuration",
                    category=CommandCategory.SYSTEM,
                    usage="forge config validate",
                ),
                CommandDefinition(
                    name="reset",
                    description="Reset a section to defaults",
                    category=CommandCategory.SYSTEM,
                    usage="forge config reset <section>",
                    examples=["forge config reset database"],
                ),
            ],
            handler=_handle_config,
        ))

        # -- workflow --------------------------------------------------------

        self.register_command(CLICommand(
            name="workflow",
            description="Manage AI workflows",
            subcommands=[
                CommandDefinition(
                    name="list",
                    description="List available workflows",
                    category=CommandCategory.WORKFLOW,
                    usage="forge workflow list",
                ),
                CommandDefinition(
                    name="run",
                    description="Execute a workflow",
                    category=CommandCategory.WORKFLOW,
                    usage="forge workflow run <name> [--input <json>]",
                    examples=['forge workflow run data-pipeline --input \'{"source": "s3"}\''],
                ),
                CommandDefinition(
                    name="create",
                    description="Create a new workflow from a template",
                    category=CommandCategory.WORKFLOW,
                    usage="forge workflow create <name> --template <template>",
                ),
                CommandDefinition(
                    name="status",
                    description="Show workflow execution status",
                    category=CommandCategory.WORKFLOW,
                    usage="forge workflow status <execution-id>",
                ),
            ],
            handler=_handle_workflow,
        ))

        # -- agent -----------------------------------------------------------

        self.register_command(CLICommand(
            name="agent",
            description="Manage AI agents",
            subcommands=[
                CommandDefinition(
                    name="list",
                    description="List registered agents",
                    category=CommandCategory.AGENT,
                    usage="forge agent list",
                ),
                CommandDefinition(
                    name="start",
                    description="Start an agent",
                    category=CommandCategory.AGENT,
                    usage="forge agent start <name>",
                ),
                CommandDefinition(
                    name="stop",
                    description="Stop a running agent",
                    category=CommandCategory.AGENT,
                    usage="forge agent stop <name>",
                ),
                CommandDefinition(
                    name="logs",
                    description="View agent logs",
                    category=CommandCategory.AGENT,
                    usage="forge agent logs <name> [--tail 100]",
                ),
            ],
            handler=_handle_agent,
        ))

        # -- repository ------------------------------------------------------

        self.register_command(CLICommand(
            name="repo",
            description="Manage project repositories",
            subcommands=[
                CommandDefinition(
                    name="list",
                    description="List repositories",
                    category=CommandCategory.REPOSITORY,
                    usage="forge repo list",
                ),
                CommandDefinition(
                    name="clone",
                    description="Clone a repository",
                    category=CommandCategory.REPOSITORY,
                    usage="forge repo clone <url>",
                ),
                CommandDefinition(
                    name="sync",
                    description="Synchronize repository with remote",
                    category=CommandCategory.REPOSITORY,
                    usage="forge repo sync [<name>]",
                ),
                CommandDefinition(
                    name="status",
                    description="Show repository status",
                    category=CommandCategory.REPOSITORY,
                    usage="forge repo status [<name>]",
                ),
            ],
            handler=_handle_repo,
        ))

        # -- memory ----------------------------------------------------------

        self.register_command(CLICommand(
            name="memory",
            description="Manage agent memory and context",
            subcommands=[
                CommandDefinition(
                    name="list",
                    description="List memory stores",
                    category=CommandCategory.MEMORY,
                    usage="forge memory list",
                ),
                CommandDefinition(
                    name="search",
                    description="Search memory entries",
                    category=CommandCategory.MEMORY,
                    usage="forge memory search <query>",
                    examples=["forge memory search 'project requirements'"],
                ),
                CommandDefinition(
                    name="add",
                    description="Add a memory entry",
                    category=CommandCategory.MEMORY,
                    usage="forge memory add --content <text> --tags <tag1,tag2>",
                ),
                CommandDefinition(
                    name="purge",
                    description="Clear memory store",
                    category=CommandCategory.MEMORY,
                    usage="forge memory purge [--older-than <days>]",
                ),
            ],
            handler=_handle_memory,
        ))

        # -- knowledge graph -------------------------------------------------

        self.register_command(CLICommand(
            name="graph",
            description="Query and manage the knowledge graph",
            subcommands=[
                CommandDefinition(
                    name="stats",
                    description="Show graph statistics",
                    category=CommandCategory.SYSTEM,
                    usage="forge graph stats",
                ),
                CommandDefinition(
                    name="query",
                    description="Run a graph query",
                    category=CommandCategory.SYSTEM,
                    usage='forge graph query "<cypher-or-nl>"',
                    examples=['forge graph query "MATCH (n) RETURN count(n)"'],
                ),
                CommandDefinition(
                    name="import",
                    description="Import data into the graph",
                    category=CommandCategory.SYSTEM,
                    usage="forge graph import <file>",
                ),
            ],
            handler=_handle_graph,
        ))

        # -- backup / restore ------------------------------------------------

        self.register_command(CLICommand(
            name="backup",
            description="Create and manage backups",
            subcommands=[
                CommandDefinition(
                    name="create",
                    description="Create a new backup",
                    category=CommandCategory.BACKUP,
                    usage="forge backup create [--name <label>]",
                ),
                CommandDefinition(
                    name="list",
                    description="List available backups",
                    category=CommandCategory.BACKUP,
                    usage="forge backup list",
                ),
                CommandDefinition(
                    name="delete",
                    description="Delete a backup",
                    category=CommandCategory.BACKUP,
                    usage="forge backup delete <id>",
                ),
            ],
            handler=_handle_backup,
        ))

        self.register_command(CLICommand(
            name="restore",
            description="Restore from a backup",
            options={
                "--backup-id": "Backup identifier to restore from",
                "--confirm": "Skip confirmation prompt",
                "--services": "Comma-separated services to restore",
            },
            handler=_handle_restore,
        ))

        # -- plugin ----------------------------------------------------------

        self.register_command(CLICommand(
            name="plugin",
            description="Manage ForgeAI plugins",
            subcommands=[
                CommandDefinition(
                    name="list",
                    description="List installed plugins",
                    category=CommandCategory.PLUGIN,
                    usage="forge plugin list",
                ),
                CommandDefinition(
                    name="install",
                    description="Install a plugin from the registry",
                    category=CommandCategory.PLUGIN,
                    usage="forge plugin install <name>",
                ),
                CommandDefinition(
                    name="uninstall",
                    description="Remove an installed plugin",
                    category=CommandCategory.PLUGIN,
                    usage="forge plugin uninstall <name>",
                ),
                CommandDefinition(
                    name="enable",
                    description="Enable a plugin",
                    category=CommandCategory.PLUGIN,
                    usage="forge plugin enable <name>",
                ),
                CommandDefinition(
                    name="disable",
                    description="Disable a plugin",
                    category=CommandCategory.PLUGIN,
                    usage="forge plugin disable <name>",
                ),
            ],
            handler=_handle_plugin,
        ))


# ---------------------------------------------------------------------------
# Default command handlers (simulated)
# ---------------------------------------------------------------------------

def _handle_init(**kwargs: Any) -> dict[str, Any]:
    name = kwargs.get("name", "forge-project")
    template = kwargs.get("template", "standard")
    git = kwargs.get("git", "true")
    return {
        "status": "success",
        "command": "init",
        "message": f"Initialized project '{name}' with template '{template}' (git={git}).",
    }


def _handle_doctor(**kwargs: Any) -> dict[str, Any]:
    fix = kwargs.get("fix", False)
    verbose = kwargs.get("verbose", False)
    checks = [
        {"name": "Python version", "status": "ok", "detail": "3.11.7"},
        {"name": "Node.js version", "status": "ok", "detail": "20.11.0"},
        {"name": "PostgreSQL connection", "status": "ok", "detail": "localhost:5432"},
        {"name": "Redis connection", "status": "ok", "detail": "localhost:6379"},
        {"name": "Ollama service", "status": "warning", "detail": "Not running locally"},
        {"name": "Disk space", "status": "ok", "detail": "42.3 GB available"},
    ]
    return {
        "status": "success",
        "command": "doctor",
        "fix_requested": fix,
        "verbose": verbose,
        "checks": checks,
        "message": f"Completed {len(checks)} diagnostic checks.",
    }


def _handle_start(**kwargs: Any) -> dict[str, Any]:
    services = kwargs.get("services", "all")
    detach = kwargs.get("detach", False)
    return {
        "status": "success",
        "command": "start",
        "services": services,
        "detach": detach,
        "message": f"Started services: {services}.",
    }


def _handle_stop(**kwargs: Any) -> dict[str, Any]:
    services = kwargs.get("services", "all")
    graceful = kwargs.get("graceful", False)
    return {
        "status": "success",
        "command": "stop",
        "services": services,
        "graceful": graceful,
        "message": f"Stopped services: {services}.",
    }


def _handle_status(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "status",
        "services": {
            "api": "running",
            "worker": "running",
            "scheduler": "running",
            "memory-store": "running",
            "knowledge-graph": "running",
        },
        "message": "All services operational.",
    }


def _handle_logs(**kwargs: Any) -> dict[str, Any]:
    service = kwargs.get("service", "all")
    level = kwargs.get("level", "info")
    tail = kwargs.get("tail", "50")
    follow = kwargs.get("follow", False)
    return {
        "status": "success",
        "command": "logs",
        "filter": {"service": service, "level": level, "tail": tail},
        "follow": follow,
        "message": f"Logs for {service} (level={level}, tail={tail}).",
    }


def _handle_config(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "config",
        "message": "Configuration command executed.",
        "details": kwargs,
    }


def _handle_workflow(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "workflow",
        "message": "Workflow command executed.",
        "details": kwargs,
    }


def _handle_agent(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "agent",
        "message": "Agent command executed.",
        "details": kwargs,
    }


def _handle_repo(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "repo",
        "message": "Repository command executed.",
        "details": kwargs,
    }


def _handle_memory(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "memory",
        "message": "Memory command executed.",
        "details": kwargs,
    }


def _handle_graph(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "graph",
        "message": "Knowledge graph command executed.",
        "details": kwargs,
    }


def _handle_backup(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "backup",
        "message": "Backup command executed.",
        "details": kwargs,
    }


def _handle_restore(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "restore",
        "message": "Restore command executed.",
        "details": kwargs,
    }


def _handle_plugin(**kwargs: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "command": "plugin",
        "message": "Plugin command executed.",
        "details": kwargs,
    }


# ---------------------------------------------------------------------------
# Global registry instance
# ---------------------------------------------------------------------------

cli_registry = CLIRegistry()
