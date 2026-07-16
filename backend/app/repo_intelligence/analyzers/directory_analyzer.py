"""Directory structure analyzer."""

import os
from pathlib import Path

from app.repo_intelligence.schemas.repository import FolderInfo


class DirectoryAnalyzer:
    """Analyzes directory structure and categorizes folders."""

    FOLDER_PATTERNS: dict[str, list[str]] = {
        "controllers": ["controllers", "controller", "handlers", "routes", "api"],
        "models": ["models", "model", "entities", "schemas", "domain"],
        "services": ["services", "service", "business", "logic"],
        "repositories": ["repositories", "repository", "dao", "dal", "data"],
        "middleware": ["middleware", "middlewares", "interceptors"],
        "utils": ["utils", "util", "helpers", "helper", "common", "shared"],
        "tests": ["tests", "test", "spec", "__tests__"],
        "config": ["config", "configuration", "settings", "env"],
        "database": ["database", "db", "migrations", "migrate"],
        "static": ["static", "assets", "public", "media"],
        "docs": ["docs", "documentation", "doc"],
    }

    IGNORED = {
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
        "target",
    }

    async def analyze(self, root_path: str) -> list[FolderInfo]:
        """Analyze directory structure and return categorized folders.

        Args:
            root_path: Path to the repository root.

        Returns:
            List of FolderInfo objects representing the directory structure.
        """
        if not os.path.isdir(root_path):
            return []

        folders = []
        self._walk_directory(root_path, root_path, folders)
        return folders

    def _walk_directory(
        self,
        current_path: str,
        root_path: str,
        result: list[FolderInfo],
        depth: int = 0,
        max_depth: int = 10,
    ) -> FolderInfo | None:
        """Recursively walk directory structure.

        Args:
            current_path: Current directory being analyzed.
            root_path: Repository root path.
            result: List to collect folder info.
            depth: Current recursion depth.
            max_depth: Maximum recursion depth.

        Returns:
            FolderInfo for the current directory or None.
        """
        if depth > max_depth:
            return None

        dir_name = os.path.basename(current_path)

        if self._should_ignore(dir_name):
            return None

        children: list[FolderInfo] = []
        file_count = 0

        try:
            for entry in os.scandir(current_path):
                if entry.is_dir(follow_symlinks=False):
                    child = self._walk_directory(
                        entry.path, root_path, result, depth + 1, max_depth
                    )
                    if child:
                        children.append(child)
                elif entry.is_file(follow_symlinks=False):
                    file_count += 1
        except PermissionError:
            pass

        purpose = self._categorize_folder(dir_name)
        relative_path = os.path.relpath(current_path, root_path)

        folder_info = FolderInfo(
            name=dir_name,
            path=relative_path,
            purpose=purpose,
            file_count=file_count,
            children=children,
        )

        result.append(folder_info)
        return folder_info

    def _categorize_folder(self, folder_name: str) -> str:
        """Determine the purpose of a folder based on its name.

        Args:
            folder_name: Name of the folder.

        Returns:
            Categorized purpose string.
        """
        name_lower = folder_name.lower()

        for purpose, patterns in self.FOLDER_PATTERNS.items():
            if name_lower in patterns or any(p in name_lower for p in patterns):
                return purpose

        return "other"

    def _should_ignore(self, dir_name: str) -> bool:
        """Check if directory should be ignored.

        Args:
            dir_name: Name of the directory.

        Returns:
            True if the directory should be ignored.
        """
        return dir_name in self.IGNORED or dir_name.startswith(".")
