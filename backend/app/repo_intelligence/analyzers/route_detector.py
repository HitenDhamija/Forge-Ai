"""Route/API detection."""

import os
import re

from app.core.logging import get_logger
from app.repo_intelligence.schemas.analysis import CodeElement, RouteInfo
from app.repo_intelligence.schemas.repository import FrameworkInfo

logger = get_logger(__name__)


class RouteDetector:
    """Detects API routes and endpoints."""

    FRAMEWORK_ROUTES: dict[str, dict] = {
        "FastAPI": {
            "decorators": [
                "@app.get",
                "@app.post",
                "@app.put",
                "@app.delete",
                "@app.patch",
                "@router.get",
                "@router.post",
                "@router.put",
                "@router.delete",
                "@router.patch",
            ],
            "patterns": [
                r'@(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)'
            ],
        },
        "Flask": {
            "decorators": ["@app.route", "@blueprint.route"],
            "patterns": [r'@(?:app|blueprint)\.route\(["\']([^"\']+)'],
        },
        "Django": {
            "patterns": [r'path\(["\']([^"\']+)', r'url\(["\']([^"\']+)'],
        },
        "Express": {
            "patterns": [
                r"(?:app|router)\.(get|post|put|delete|patch)\([\"']([^\"']+)"
            ],
        },
        "Spring Boot": {
            "patterns": [
                r"@(Get|Post|Put|Delete|Patch)Mapping\([\"']([^\"']+)"
            ],
        },
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

    async def detect(
        self,
        root_path: str,
        frameworks: list[FrameworkInfo],
        code_elements: list[CodeElement],
    ) -> list[RouteInfo]:
        """Detect routes based on detected frameworks.

        Args:
            root_path: Repository root path.
            frameworks: List of detected frameworks.
            code_elements: List of extracted code elements.

        Returns:
            List of detected RouteInfo objects.
        """
        routes: list[RouteInfo] = []
        framework_names = {f.name for f in frameworks}

        for framework_name in framework_names:
            if framework_name == "FastAPI":
                routes.extend(self._detect_fastapi_routes(root_path))
            elif framework_name == "Flask":
                routes.extend(self._detect_flask_routes(root_path))
            elif framework_name == "Django":
                routes.extend(self._detect_django_routes(root_path))
            elif framework_name == "Express":
                routes.extend(self._detect_express_routes(root_path))
            elif framework_name == "Spring Boot":
                routes.extend(self._detect_spring_routes(root_path))

        seen = set()
        unique_routes = []
        for route in routes:
            key = (route.method, route.path, route.file_path)
            if key not in seen:
                seen.add(key)
                unique_routes.append(route)

        return unique_routes

    def _detect_fastapi_routes(self, root_path: str) -> list[RouteInfo]:
        """Detect FastAPI routes.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected routes.
        """
        routes = []
        pattern = re.compile(
            r'@(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)'
        )

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith((".py",)):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()

                    content = "".join(lines)
                    for match in pattern.finditer(content):
                        method = match.group(1).upper()
                        path = match.group(2)
                        line_number = content[: match.start()].count("\n") + 1

                        func_name = self._find_function_name(lines, line_number)

                        routes.append(
                            RouteInfo(
                                method=method,
                                path=path,
                                function_name=func_name,
                                file_path=os.path.relpath(file_path, root_path),
                                line_number=line_number,
                            )
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        return routes

    def _detect_flask_routes(self, root_path: str) -> list[RouteInfo]:
        """Detect Flask routes.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected routes.
        """
        routes = []
        pattern = re.compile(
            r'@(?:app|blueprint)\.route\(["\']([^"\']+)'
        )
        method_pattern = re.compile(r'methods\s*=\s*\[([^\]]+)\]')

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith((".py",)):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for match in pattern.finditer(content):
                        path = match.group(1)
                        line_number = content[: match.start()].count("\n") + 1

                        methods_match = method_pattern.search(
                            content[match.start() : match.start() + 200]
                        )
                        if methods_match:
                            methods = [
                                m.strip().strip("'\"")
                                for m in methods_match.group(1).split(",")
                            ]
                        else:
                            methods = ["GET"]

                        for method in methods:
                            routes.append(
                                RouteInfo(
                                    method=method.upper(),
                                    path=path,
                                    function_name="",
                                    file_path=os.path.relpath(file_path, root_path),
                                    line_number=line_number,
                                )
                            )
                except (OSError, UnicodeDecodeError):
                    pass

        return routes

    def _detect_django_routes(self, root_path: str) -> list[RouteInfo]:
        """Detect Django routes.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected routes.
        """
        routes = []
        patterns = [
            re.compile(r'path\(["\']([^"\']+)'),
            re.compile(r'url\(["\']([^"\']+)'),
        ]

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if filename != "urls.py":
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for pattern in patterns:
                        for match in pattern.finditer(content):
                            path = match.group(1)
                            line_number = content[: match.start()].count("\n") + 1

                            routes.append(
                                RouteInfo(
                                    method="GET",
                                    path=f"/{path}" if not path.startswith("/") else path,
                                    function_name="",
                                    file_path=os.path.relpath(file_path, root_path),
                                    line_number=line_number,
                                )
                            )
                except (OSError, UnicodeDecodeError):
                    pass

        return routes

    def _detect_express_routes(self, root_path: str) -> list[RouteInfo]:
        """Detect Express routes.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected routes.
        """
        routes = []
        pattern = re.compile(
            r"(?:app|router)\.(get|post|put|delete|patch)\([\"']([^\"']+)"
        )

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith((".js", ".ts", ".mjs")):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for match in pattern.finditer(content):
                        method = match.group(1).upper()
                        path = match.group(2)
                        line_number = content[: match.start()].count("\n") + 1

                        routes.append(
                            RouteInfo(
                                method=method,
                                path=path,
                                function_name="",
                                file_path=os.path.relpath(file_path, root_path),
                                line_number=line_number,
                            )
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        return routes

    def _detect_spring_routes(self, root_path: str) -> list[RouteInfo]:
        """Detect Spring Boot routes.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected routes.
        """
        routes = []
        pattern = re.compile(
            r"@(Get|Post|Put|Delete|Patch)Mapping\([\"']([^\"']+)"
        )

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith((".java",)):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for match in pattern.finditer(content):
                        method = match.group(1).upper()
                        path = match.group(2)
                        line_number = content[: match.start()].count("\n") + 1

                        routes.append(
                            RouteInfo(
                                method=method,
                                path=path,
                                function_name="",
                                file_path=os.path.relpath(file_path, root_path),
                                line_number=line_number,
                            )
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        return routes

    def _find_function_name(self, lines: list[str], decorator_line: int) -> str:
        """Find function name following a decorator.

        Args:
            lines: File lines.
            decorator_line: Line number of the decorator.

        Returns:
            Function name or empty string.
        """
        idx = decorator_line
        while idx < len(lines):
            line = lines[idx].strip()
            if line.startswith("def ") or line.startswith("async def "):
                match = re.search(r"(?:async\s+)?def\s+(\w+)", line)
                if match:
                    return match.group(1)
            elif line.startswith("@"):
                idx += 1
                continue
            elif line:
                break
            idx += 1
        return ""
