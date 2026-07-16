"""Dependency analyzer."""

import os
import re
import tomllib

from app.core.logging import get_logger
from app.repo_intelligence.schemas.repository import DependencyInfo

logger = get_logger(__name__)


class DependencyAnalyzer:
    """Analyzes project dependencies from manifest files."""

    MANIFEST_PATTERNS: dict[str, str] = {
        "requirements.txt": "python",
        "pyproject.toml": "python",
        "setup.py": "python",
        "Pipfile": "python",
        "package.json": "node",
        "pom.xml": "java",
        "build.gradle": "java",
        "Cargo.toml": "rust",
        "go.mod": "go",
        "composer.json": "php",
        "Gemfile": "ruby",
        "csproj": "dotnet",
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

    async def analyze(self, root_path: str) -> list[DependencyInfo]:
        """Find and parse all dependency files.

        Args:
            root_path: Path to the repository root.

        Returns:
            List of DependencyInfo objects.
        """
        dependencies: list[DependencyInfo] = []

        for root, dirs, files in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for file in files:
                file_path = os.path.join(root, file)

                if file == "requirements.txt":
                    deps = await self._parse_requirements_txt(file_path)
                    dependencies.extend(deps)
                elif file == "package.json":
                    deps = await self._parse_package_json(file_path)
                    dependencies.extend(deps)
                elif file == "pyproject.toml":
                    deps = await self._parse_pyproject_toml(file_path)
                    dependencies.extend(deps)
                elif file == "Cargo.toml":
                    deps = await self._parse_cargo_toml(file_path)
                    dependencies.extend(deps)
                elif file == "go.mod":
                    deps = await self._parse_go_mod(file_path)
                    dependencies.extend(deps)
                elif file == "pom.xml":
                    deps = await self._parse_pom_xml(file_path)
                    dependencies.extend(deps)

        return dependencies

    async def _parse_requirements_txt(self, file_path: str) -> list[DependencyInfo]:
        """Parse requirements.txt file.

        Args:
            file_path: Path to requirements.txt.

        Returns:
            List of DependencyInfo objects.
        """
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue

                    match = re.match(r"^([a-zA-Z0-9_-]+)\s*[=<>!~]+\s*(.+)$", line)
                    if match:
                        deps.append(
                            DependencyInfo(
                                name=match.group(1),
                                version=match.group(2).strip(),
                                is_production=True,
                                source_file=os.path.relpath(
                                    file_path, os.path.dirname(file_path)
                                ),
                            )
                        )
                    elif re.match(r"^[a-zA-Z0-9_-]+$", line):
                        deps.append(
                            DependencyInfo(
                                name=line,
                                version=None,
                                is_production=True,
                                source_file=os.path.relpath(
                                    file_path, os.path.dirname(file_path)
                                ),
                            )
                        )
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Failed to parse requirements.txt", error=str(e))

        return deps

    async def _parse_package_json(self, file_path: str) -> list[DependencyInfo]:
        """Parse package.json file.

        Args:
            file_path: Path to package.json.

        Returns:
            List of DependencyInfo objects.
        """
        import json

        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            for section, is_prod in [
                ("dependencies", True),
                ("devDependencies", False),
            ]:
                for name, version in data.get(section, {}).items():
                    deps.append(
                        DependencyInfo(
                            name=name,
                            version=version,
                            is_production=is_prod,
                            source_file=os.path.relpath(
                                file_path, os.path.dirname(file_path)
                            ),
                        )
                    )
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to parse package.json", error=str(e))

        return deps

    async def _parse_pyproject_toml(self, file_path: str) -> list[DependencyInfo]:
        """Parse pyproject.toml file.

        Args:
            file_path: Path to pyproject.toml.

        Returns:
            List of DependencyInfo objects.
        """
        deps = []
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)

            dependencies = data.get("project", {}).get("dependencies", [])
            for dep in dependencies:
                match = re.match(r"^([a-zA-Z0-9_-]+)\s*(.*)$", dep)
                if match:
                    deps.append(
                        DependencyInfo(
                            name=match.group(1),
                            version=match.group(2).strip() or None,
                            is_production=True,
                            source_file=os.path.relpath(
                                file_path, os.path.dirname(file_path)
                            ),
                        )
                    )

            optional_deps = data.get("project", {}).get(
                "optional-dependencies", {}
            )
            for group_deps in optional_deps.values():
                for dep in group_deps:
                    match = re.match(r"^([a-zA-Z0-9_-]+)\s*(.*)$", dep)
                    if match:
                        deps.append(
                            DependencyInfo(
                                name=match.group(1),
                                version=match.group(2).strip() or None,
                                is_production=False,
                                source_file=os.path.relpath(
                                    file_path, os.path.dirname(file_path)
                                ),
                            )
                        )
        except (OSError, tomllib.TOMLDecodeError) as e:
            logger.warning("Failed to parse pyproject.toml", error=str(e))

        return deps

    async def _parse_pom_xml(self, file_path: str) -> list[DependencyInfo]:
        """Parse pom.xml file (basic regex parsing).

        Args:
            file_path: Path to pom.xml.

        Returns:
            List of DependencyInfo objects.
        """
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            pattern = r"<dependency>\s*<groupId>(.*?)</groupId>\s*<artifactId>(.*?)</artifactId>\s*(?:<version>(.*?)</version>)?"
            for match in re.finditer(pattern, content, re.DOTALL):
                group_id, artifact_id, version = match.groups()
                deps.append(
                    DependencyInfo(
                        name=f"{group_id}:{artifact_id}",
                        version=version,
                        is_production=True,
                        source_file=os.path.relpath(
                            file_path, os.path.dirname(file_path)
                        ),
                    )
                )
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Failed to parse pom.xml", error=str(e))

        return deps

    async def _parse_cargo_toml(self, file_path: str) -> list[DependencyInfo]:
        """Parse Cargo.toml file.

        Args:
            file_path: Path to Cargo.toml.

        Returns:
            List of DependencyInfo objects.
        """
        deps = []
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)

            for section, is_prod in [
                ("dependencies", True),
                ("dev-dependencies", False),
                ("build-dependencies", False),
            ]:
                for name, value in data.get(section, {}).items():
                    if isinstance(value, dict):
                        version = value.get("version")
                    elif isinstance(value, str):
                        version = value
                    else:
                        version = None

                    deps.append(
                        DependencyInfo(
                            name=name,
                            version=version,
                            is_production=is_prod,
                            source_file=os.path.relpath(
                                file_path, os.path.dirname(file_path)
                            ),
                        )
                    )
        except (OSError, tomllib.TOMLDecodeError) as e:
            logger.warning("Failed to parse Cargo.toml", error=str(e))

        return deps

    async def _parse_go_mod(self, file_path: str) -> list[DependencyInfo]:
        """Parse go.mod file.

        Args:
            file_path: Path to go.mod.

        Returns:
            List of DependencyInfo objects.
        """
        deps = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            in_require = False
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("require ("):
                    in_require = True
                    continue
                if line == ")" and in_require:
                    in_require = False
                    continue

                if in_require or line.startswith("require "):
                    parts = line.replace("require ", "").split()
                    if len(parts) >= 2:
                        deps.append(
                            DependencyInfo(
                                name=parts[0],
                                version=parts[1] if len(parts) > 1 else None,
                                is_production=True,
                                source_file=os.path.relpath(
                                    file_path, os.path.dirname(file_path)
                                ),
                            )
                        )
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Failed to parse go.mod", error=str(e))

        return deps
