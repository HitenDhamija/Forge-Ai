"""Style Analyzer for Software Engineer Agent.

Analyzes coding style and conventions in the repository.
"""

from typing import Any
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class StyleProfile:
    """Coding style profile for a repository."""

    naming_conventions: dict[str, str]
    import_style: str
    docstring_format: str
    type_hint_style: str
    error_handling: str
    logging_pattern: str
    test_pattern: str
    max_line_length: int
    indent_style: str
    quote_style: str


class StyleAnalyzer:
    """Analyzes coding style and conventions."""

    def __init__(self):
        """Initialize style analyzer."""
        self._profiles: dict[str, StyleProfile] = {}

    async def analyze(
        self,
        repository_id: str,
        files: list[dict[str, Any]],
    ) -> StyleProfile:
        """Analyze coding style from repository files.

        Args:
            repository_id: Repository identifier.
            files: List of file contents to analyze.

        Returns:
            Style profile.
        """
        logger.info("Analyzing style for repository %s", repository_id)

        profile = StyleProfile(
            naming_conventions=await self._analyze_naming(files),
            import_style=await self._analyze_imports(files),
            docstring_format=await self._analyze_docstrings(files),
            type_hint_style=await self._analyze_type_hints(files),
            error_handling=await self._analyze_error_handling(files),
            logging_pattern=await self._analyze_logging(files),
            test_pattern=await self._analyze_tests(files),
            max_line_length=self._detect_line_length(files),
            indent_style=self._detect_indent_style(files),
            quote_style=self._detect_quote_style(files),
        )

        self._profiles[repository_id] = profile

        logger.info(
            "Style profile created: naming=%s, imports=%s, docstrings=%s",
            profile.naming_conventions,
            profile.import_style,
            profile.docstring_format,
        )

        return profile

    async def _analyze_naming(self, files: list[dict[str, Any]]) -> dict[str, str]:
        """Analyze naming conventions."""
        conventions = {
            "functions": "snake_case",
            "classes": "PascalCase",
            "variables": "snake_case",
            "constants": "UPPER_SNAKE_CASE",
            "modules": "snake_case",
        }

        for file in files:
            content = file.get("content", "")
            if "class " in content:
                # Detect class naming
                pass
            if "def " in content:
                # Detect function naming
                pass

        return conventions

    async def _analyze_imports(self, files: list[dict[str, Any]]) -> str:
        """Analyze import style."""
        stdlib_first = 0
        third_party_first = 0

        for file in files:
            content = file.get("content", "")
            lines = content.split("\n")

            import_section = []
            for line in lines:
                if line.startswith("import ") or line.startswith("from "):
                    import_section.append(line)
                elif import_section:
                    break

            if import_section:
                # Check if stdlib imports come first
                stdlib_modules = {"os", "sys", "json", "typing", "datetime"}
                first_import = import_section[0].split()[1].split(".")[0]
                if first_import in stdlib_modules:
                    stdlib_first += 1
                else:
                    third_party_first += 1

        return "stdlib-first" if stdlib_first > third_party_first else "mixed"

    async def _analyze_docstrings(self, files: list[dict[str, Any]]) -> str:
        """Analyze docstring format."""
        google_style = 0
        numpy_style = 0
        sphinx_style = 0

        for file in files:
            content = file.get("content", "")
            if '"""Args:' in content or '"""Returns:' in content:
                google_style += 1
            elif '"""Parameters' in content or '"""Returns' in content:
                numpy_style += 1
            elif ':param ' in content or ':return:' in content:
                sphinx_style += 1

        if google_style >= numpy_style and google_style >= sphinx_style:
            return "google"
        elif numpy_style >= sphinx_style:
            return "numpy"
        return "sphinx"

    async def _analyze_type_hints(self, files: list[dict[str, Any]]) -> str:
        """Analyze type hint style."""
        inline_hints = 0
        comment_hints = 0

        for file in files:
            content = file.get("content", "")
            for line in content.split("\n"):
                if ":" in line and "->" in line:
                    inline_hints += 1
                if "# type:" in line:
                    comment_hints += 1

        return "inline" if inline_hints > comment_hints else "comment"

    async def _analyze_error_handling(self, files: list[dict[str, Any]]) -> str:
        """Analyze error handling pattern."""
        specific_exceptions = 0
        bare_except = 0

        for file in files:
            content = file.get("content", "")
            if "except Exception" in content or "except:" in content:
                bare_except += 1
            if "except (" in content or "except ValueError" in content:
                specific_exceptions += 1

        return "specific" if specific_exceptions > bare_except else "general"

    async def _analyze_logging(self, files: list[dict[str, Any]]) -> str:
        """Analyze logging pattern."""
        for file in files:
            content = file.get("content", "")
            if "from app.core.logging import get_logger" in content:
                return "app-logger"
            if "import logging" in content:
                return "stdlib-logging"
        return "print"

    async def _analyze_tests(self, files: list[dict[str, Any]]) -> str:
        """Analyze test patterns."""
        for file in files:
            content = file.get("content", "")
            if "import pytest" in content:
                return "pytest"
            if "import unittest" in content:
                return "unittest"
        return "unknown"

    def _detect_line_length(self, files: list[dict[str, Any]]) -> int:
        """Detect max line length."""
        max_length = 88  # Default for Black
        for file in files:
            content = file.get("content", "")
            for line in content.split("\n"):
                if len(line) > max_length:
                    max_length = len(line)
        return min(max_length, 120)

    def _detect_indent_style(self, files: list[dict[str, Any]]) -> str:
        """Detect indent style."""
        spaces = 0
        tabs = 0

        for file in files:
            content = file.get("content", "")
            for line in content.split("\n"):
                if line.startswith("\t"):
                    tabs += 1
                elif line.startswith("    "):
                    spaces += 1

        return "tabs" if tabs > spaces else "spaces"

    def _detect_quote_style(self, files: list[dict[str, Any]]) -> str:
        """Detect quote style."""
        double_quotes = 0
        single_quotes = 0

        for file in files:
            content = file.get("content", "")
            double_quotes += content.count('"')
            single_quotes += content.count("'")

        return "double" if double_quotes > single_quotes else "single"

    def get_profile(self, repository_id: str) -> StyleProfile | None:
        """Get cached style profile."""
        return self._profiles.get(repository_id)
