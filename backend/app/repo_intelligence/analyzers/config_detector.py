"""Configuration file detection."""

import os

from app.core.logging import get_logger

logger = get_logger(__name__)


class ConfigDetector:
    """Detects and categorizes configuration files."""

    CONFIG_PATTERNS: dict[str, list[str]] = {
        "python": [
            "settings.py",
            "config.py",
            ".env",
            ".env.example",
            "alembic.ini",
            "setup.cfg",
            "tox.ini",
            "mypy.ini",
        ],
        "node": [
            ".env",
            ".env.example",
            ".eslintrc",
            ".eslintrc.js",
            ".eslintrc.json",
            ".prettierrc",
            ".prettierrc.js",
            "tsconfig.json",
            "jest.config.js",
            "jest.config.ts",
            "webpack.config.js",
            "vite.config.js",
            "vite.config.ts",
        ],
        "docker": [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            ".dockerignore",
        ],
        "ci": [
            ".github",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".circleci",
            ".travis.yml",
        ],
        "ide": [
            ".vscode",
            ".idea",
            ".editorconfig",
        ],
        "git": [
            ".gitignore",
            ".gitattributes",
        ],
    }

    IGNORED_DIRS = {
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "dist",
        "build",
        "target",
    }

    async def detect(self, root_path: str) -> list[str]:
        """Find all configuration files.

        Args:
            root_path: Repository root path.

        Returns:
            List of configuration file paths relative to root.
        """
        config_files: list[str] = []

        all_patterns = set()
        for patterns in self.CONFIG_PATTERNS.values():
            all_patterns.update(patterns)

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if filename in all_patterns:
                    rel_path = os.path.relpath(os.path.join(root, filename), root_path)
                    config_files.append(rel_path)

            for dirname in list(dirs):
                if dirname in all_patterns:
                    rel_path = os.path.relpath(os.path.join(root, dirname), root_path)
                    config_files.append(rel_path)
                    dirs.remove(dirname)

        return sorted(set(config_files))
