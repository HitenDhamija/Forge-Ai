"""Language detection based on file extensions."""

import os
from collections import defaultdict

from app.core.logging import get_logger
from app.repo_intelligence.schemas.repository import LanguageInfo

logger = get_logger(__name__)


class LanguageDetector:
    """Detects programming languages in a repository."""

    EXTENSION_MAP: dict[str, str] = {
        ".py": "Python",
        ".pyw": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".mjs": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".h": "C",
        ".hpp": "C++",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".cs": "C#",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".less": "LESS",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bash": "Shell",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".json": "JSON",
        ".toml": "TOML",
        ".md": "Markdown",
        ".rst": "reStructuredText",
    }

    IGNORED_DIRS = {
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
        "target",
    }

    async def detect(self, root_path: str) -> list[LanguageInfo]:
        """Scan files and detect languages with line counts.

        Args:
            root_path: Path to the repository root.

        Returns:
            List of LanguageInfo objects sorted by file count descending.
        """
        language_stats: dict[str, dict] = defaultdict(
            lambda: {"file_count": 0, "total_lines": 0, "extensions": set()}
        )

        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [
                d for d in dirnames if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()

                if ext in self.EXTENSION_MAP:
                    language = self.EXTENSION_MAP[ext]
                    file_path = os.path.join(dirpath, filename)

                    line_count = self._count_lines(file_path)

                    language_stats[language]["file_count"] += 1
                    language_stats[language]["total_lines"] += line_count
                    language_stats[language]["extensions"].add(ext)

        total_files = sum(stats["file_count"] for stats in language_stats.values())

        languages = []
        for lang_name, stats in sorted(
            language_stats.items(), key=lambda x: x[1]["file_count"], reverse=True
        ):
            percentage = (stats["file_count"] / total_files * 100) if total_files > 0 else 0
            languages.append(
                LanguageInfo(
                    name=lang_name,
                    file_count=stats["file_count"],
                    total_lines=stats["total_lines"],
                    percentage=round(percentage, 2),
                    extensions=sorted(stats["extensions"]),
                )
            )

        return languages

    def _count_lines(self, file_path: str) -> int:
        """Count lines in a file safely.

        Args:
            file_path: Path to the file.

        Returns:
            Number of lines in the file, or 0 if unreadable.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except (OSError, UnicodeDecodeError):
            return 0
