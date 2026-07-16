"""Framework detection."""

import os
import re

from app.core.logging import get_logger
from app.repo_intelligence.schemas.repository import DependencyInfo, FrameworkInfo

logger = get_logger(__name__)


class FrameworkDetector:
    """Detects frameworks based on file patterns, dependencies, and code patterns."""

    FRAMEWORK_SIGNALS: dict[str, dict] = {
        "FastAPI": {
            "files": ["main.py", "app.py"],
            "imports": ["fastapi", "FastAPI"],
            "dependencies": ["fastapi"],
            "patterns": [r"@app\.get", r"@app\.post", r"APIRouter"],
        },
        "Flask": {
            "files": ["app.py", "wsgi.py"],
            "imports": ["flask", "Flask"],
            "dependencies": ["flask"],
            "patterns": [r"@app\.route", r"Blueprint"],
        },
        "Django": {
            "files": ["manage.py", "settings.py", "wsgi.py"],
            "imports": ["django"],
            "dependencies": ["django"],
            "patterns": [r"urlpatterns", r"views\.py", r"models\.py"],
        },
        "Express": {
            "files": ["server.js", "app.js", "index.js"],
            "imports": ["express"],
            "dependencies": ["express"],
            "patterns": [r"app\.get\(", r"app\.post\(", r"router\."],
        },
        "Next.js": {
            "files": ["next.config.js", "next.config.mjs", "next.config.ts"],
            "imports": ["next"],
            "dependencies": ["next"],
            "patterns": [
                r"getServerSideProps",
                r"getStaticProps",
                r"use client",
                r"use server",
            ],
        },
        "React": {
            "files": ["App.tsx", "App.jsx", "App.js"],
            "imports": ["react"],
            "dependencies": ["react"],
            "patterns": [r"useState", r"useEffect", r"Component"],
        },
        "Vue": {
            "files": ["vue.config.js", "nuxt.config.js"],
            "imports": ["vue"],
            "dependencies": ["vue"],
            "patterns": [r"<template>", r"defineComponent"],
        },
        "Spring Boot": {
            "files": ["Application.java", "pom.xml"],
            "imports": ["org.springframework"],
            "dependencies": ["spring-boot"],
            "patterns": [
                r"@SpringBootApplication",
                r"@RestController",
                r"@RequestMapping",
            ],
        },
        "NestJS": {
            "files": ["main.ts", "nest-cli.json"],
            "imports": ["@nestjs"],
            "dependencies": ["@nestjs/core"],
            "patterns": [r"@Controller", r"@Injectable", r"@Module"],
        },
        "Laravel": {
            "files": ["artisan", "composer.json"],
            "imports": ["illuminate"],
            "dependencies": ["laravel/framework"],
            "patterns": [r"Route::", r"Controller", r"Eloquent"],
        },
        "ASP.NET": {
            "files": ["Program.cs", "Startup.cs"],
            "imports": ["Microsoft.AspNetCore"],
            "dependencies": ["Microsoft.AspNetCore"],
            "patterns": [r"\[HttpGet\]", r"\[HttpPost\]", r"Controller"],
        },
    }

    async def detect(
        self, root_path: str, dependencies: list[DependencyInfo]
    ) -> list[FrameworkInfo]:
        """Detect frameworks using multiple signals.

        Args:
            root_path: Path to the repository root.
            dependencies: List of detected dependencies.

        Returns:
            List of detected frameworks sorted by confidence descending.
        """
        frameworks: list[FrameworkInfo] = []

        for framework_name, signals in self.FRAMEWORK_SIGNALS.items():
            evidence: list[str] = []
            confidence = 0.0

            file_evidence = self._check_file_signals(root_path, signals)
            if file_evidence:
                evidence.extend(file_evidence)
                confidence += 0.3

            import_evidence = self._check_import_signals(root_path, signals)
            if import_evidence:
                evidence.extend(import_evidence)
                confidence += 0.3

            dep_evidence = self._check_dependency_signals(dependencies, signals)
            if dep_evidence:
                evidence.extend(dep_evidence)
                confidence += 0.25

            pattern_evidence = self._check_pattern_signals(root_path, signals)
            if pattern_evidence:
                evidence.extend(pattern_evidence)
                confidence += 0.15

            if confidence > 0:
                frameworks.append(
                    FrameworkInfo(
                        name=framework_name,
                        version=None,
                        confidence=min(confidence, 1.0),
                        evidence=evidence[:10],
                    )
                )

        frameworks.sort(key=lambda f: f.confidence, reverse=True)
        return frameworks

    def _check_file_signals(self, root_path: str, signals: dict) -> list[str]:
        """Check for framework-specific files.

        Args:
            root_path: Repository root path.
            signals: Framework signals dictionary.

        Returns:
            List of evidence strings.
        """
        evidence = []
        target_files = signals.get("files", [])

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in {"node_modules", ".venv", "venv", "__pycache__", ".git"}
            ]

            for file in files:
                if file in target_files:
                    rel_path = os.path.relpath(os.path.join(root, file), root_path)
                    evidence.append(f"Found file: {rel_path}")

        return evidence

    def _check_import_signals(self, root_path: str, signals: dict) -> list[str]:
        """Check for framework-specific imports in code.

        Args:
            root_path: Repository root path.
            signals: Framework signals dictionary.

        Returns:
            List of evidence strings.
        """
        evidence = []
        target_imports = signals.get("imports", [])
        checked_files = 0
        max_files = 100

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in {"node_modules", ".venv", "venv", "__pycache__", ".git"}
            ]

            for file in files:
                if checked_files >= max_files:
                    return evidence

                if not any(
                    file.endswith(ext)
                    for ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".java"]
                ):
                    continue

                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(10000)
                        for imp in target_imports:
                            if imp in content:
                                rel_path = os.path.relpath(file_path, root_path)
                                evidence.append(
                                    f"Import '{imp}' found in {rel_path}"
                                )
                                break
                except (OSError, UnicodeDecodeError):
                    pass

                checked_files += 1

        return evidence

    def _check_dependency_signals(
        self, dependencies: list[DependencyInfo], signals: dict
    ) -> list[str]:
        """Check for framework-specific dependencies.

        Args:
            dependencies: List of detected dependencies.
            signals: Framework signals dictionary.

        Returns:
            List of evidence strings.
        """
        evidence = []
        target_deps = signals.get("dependencies", [])
        dep_names = {d.name.lower() for d in dependencies}

        for target_dep in target_deps:
            if target_dep.lower() in dep_names:
                evidence.append(f"Dependency '{target_dep}' found")

        return evidence

    def _check_pattern_signals(self, root_path: str, signals: dict) -> list[str]:
        """Check for framework-specific code patterns.

        Args:
            root_path: Repository root path.
            signals: Framework signals dictionary.

        Returns:
            List of evidence strings.
        """
        evidence = []
        patterns = signals.get("patterns", [])
        compiled_patterns = [re.compile(p) for p in patterns]
        checked_files = 0
        max_files = 100

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in {"node_modules", ".venv", "venv", "__pycache__", ".git"}
            ]

            for file in files:
                if checked_files >= max_files:
                    return evidence

                if not any(
                    file.endswith(ext)
                    for ext in [".py", ".js", ".ts", ".jsx", ".tsx", ".java"]
                ):
                    continue

                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(10000)
                        for pattern in compiled_patterns:
                            if pattern.search(content):
                                rel_path = os.path.relpath(file_path, root_path)
                                evidence.append(
                                    f"Pattern '{pattern.pattern}' found in {rel_path}"
                                )
                                break
                except (OSError, UnicodeDecodeError):
                    pass

                checked_files += 1

        return evidence
