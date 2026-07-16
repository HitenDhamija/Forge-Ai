"""Configuration for the Agents module."""

from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    """Settings for agent execution."""

    MAX_CONCURRENT_AGENTS: int = 5
    AGENT_TIMEOUT_SECONDS: int = 300
    MAX_TASK_RETRIES: int = 3
    ENABLE_SHELL_EXECUTION: bool = False
    ENABLE_FILE_MODIFICATION: bool = True
    ALLOWED_FILE_EXTENSIONS: list[str] = [
        ".py", ".ts", ".tsx", ".js", ".jsx",
        ".json", ".yaml", ".yml", ".toml",
        ".md", ".txt", ".html", ".css",
    ]
    BLOCKED_DIRECTORIES: list[str] = [
        ".git", "node_modules", "__pycache__",
        ".venv", "venv", "env",
    ]

    model_config = {"env_prefix": "AGENT_"}


_agent_settings: AgentSettings | None = None


def get_agent_settings() -> AgentSettings:
    """Get or create agent settings singleton."""
    global _agent_settings
    if _agent_settings is None:
        _agent_settings = AgentSettings()
    return _agent_settings
