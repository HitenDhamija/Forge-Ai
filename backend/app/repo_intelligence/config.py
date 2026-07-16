"""Repository intelligence configuration."""

import os
import tempfile
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_temp_dir() -> str:
    """Return platform-appropriate temp directory."""
    return os.path.join(tempfile.gettempdir(), "forgeai", "repos")


class RepoIntelligenceSettings(BaseSettings):
    """Repository intelligence configuration."""

    model_config = SettingsConfigDict(env_prefix="REPO_")

    MAX_REPOSITORY_SIZE_MB: int = 500
    MAX_FILE_SIZE_KB: int = 1024
    MAX_FILES_TO_ANALYZE: int = 10000
    SUPPORTED_IMPORT_METHODS: list[str] = ["zip", "git", "folder"]
    GIT_TIMEOUT: int = 60
    TEMP_DIR: str = ""
    IGNORED_DIRECTORIES: list[str] = [
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "coverage",
        ".idea",
        ".vscode",
        "*.egg-info",
        "target",
    ]
    IGNORED_FILE_PATTERNS: list[str] = [
        "*.pyc",
        "*.pyo",
        "*.so",
        "*.dll",
        "*.exe",
        "*.min.js",
        "*.min.css",
        "*.map",
        "package-lock.json",
        "yarn.lock",
        "poetry.lock",
    ]

    def model_post_init(self, __context: object) -> None:
        if not self.TEMP_DIR:
            object.__setattr__(self, "TEMP_DIR", _default_temp_dir())


@lru_cache
def get_repo_settings() -> RepoIntelligenceSettings:
    """Return cached repository intelligence settings instance."""
    return RepoIntelligenceSettings()
