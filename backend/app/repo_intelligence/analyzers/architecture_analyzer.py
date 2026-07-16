"""Architecture style detection."""

import os

from app.core.logging import get_logger
from app.repo_intelligence.schemas.analysis import DatabaseModelInfo, RouteInfo
from app.repo_intelligence.schemas.repository import (
    ArchitectureSummary,
    ArchitectureStyle,
    FolderInfo,
    FrameworkInfo,
)

logger = get_logger(__name__)


class ArchitectureAnalyzer:
    """Analyzes overall architecture style."""

    async def analyze(
        self,
        root_path: str,
        folder_structure: list[FolderInfo],
        frameworks: list[FrameworkInfo],
        routes: list[RouteInfo],
        database_models: list[DatabaseModelInfo],
    ) -> ArchitectureSummary:
        """Determine architecture style from analysis results.

        Args:
            root_path: Repository root path.
            folder_structure: List of folder information.
            frameworks: List of detected frameworks.
            routes: List of detected routes.
            database_models: List of detected database models.

        Returns:
            ArchitectureSummary with detected style and metadata.
        """
        framework_names = {f.name for f in frameworks}
        folder_purposes = {f.purpose for f in folder_structure}

        style = ArchitectureStyle.UNKNOWN
        description = "Unable to determine architecture style"

        if self._detect_clean_architecture(folder_structure):
            style = ArchitectureStyle.CLEAN
            description = "Clean Architecture with domain, application, and infrastructure layers"
        elif self._detect_mvc(folder_structure):
            style = ArchitectureStyle.MVC
            description = "MVC pattern with models, views/controllers, and services"
        elif self._detect_layered(folder_structure):
            style = ArchitectureStyle.LAYERED
            description = "Layered architecture with separate presentation, business, and data layers"
        elif self._detect_microservices(root_path, folder_structure):
            style = ArchitectureStyle.MICROSERVICES
            description = "Microservices architecture with multiple independent services"
        elif self._detect_serverless(root_path, frameworks):
            style = ArchitectureStyle.SERVERLESS
            description = "Serverless architecture using cloud functions"
        elif routes or database_models:
            style = ArchitectureStyle.MONOLITH
            description = "Monolithic application"

        entry_points = self._detect_entry_points(root_path, frameworks)
        main_modules = self._detect_main_modules(folder_structure)

        has_auth = self._detect_authentication(root_path, folder_purposes)
        has_db = len(database_models) > 0
        has_api = len(routes) > 0
        has_frontend = "frontend" in folder_purposes or "client" in folder_purposes

        return ArchitectureSummary(
            style=style,
            description=description,
            entry_points=entry_points,
            main_modules=main_modules,
            authentication_detected=has_auth,
            database_detected=has_db,
            api_detected=has_api,
            frontend_detected=has_frontend,
        )

    def _detect_mvc(self, folders: list[FolderInfo]) -> bool:
        """Check for MVC pattern (models, views/controllers, services).

        Args:
            folders: List of folder information.

        Returns:
            True if MVC pattern is detected.
        """
        purposes = {f.purpose for f in folders}
        has_models = "models" in purposes
        has_views = "controllers" in purposes or "views" in purposes
        has_services = "services" in purposes

        return has_models and (has_views or has_services)

    def _detect_clean_architecture(self, folders: list[FolderInfo]) -> bool:
        """Check for clean architecture (domain, application, infrastructure).

        Args:
            folders: List of folder information.

        Returns:
            True if clean architecture is detected.
        """
        folder_names = {f.name.lower() for f in folders}
        domain_names = {"domain", "entities", "core"}
        app_names = {"application", "usecases", "use_cases", "services"}
        infra_names = {"infrastructure", "infra", "adapters", "external"}

        has_domain = bool(folder_names & domain_names)
        has_app = bool(folder_names & app_names)
        has_infra = bool(folder_names & infra_names)

        return has_domain and (has_app or has_infra)

    def _detect_layered(self, folders: list[FolderInfo]) -> bool:
        """Check for layered architecture.

        Args:
            folders: List of folder information.

        Returns:
            True if layered architecture is detected.
        """
        purposes = {f.purpose for f in folders}
        layer_names = {"presentation", "business", "data", "api", "repositories"}

        matched_layers = purposes & layer_names
        return len(matched_layers) >= 2

    def _detect_microservices(
        self, root_path: str, folders: list[FolderInfo]
    ) -> bool:
        """Check for microservices architecture.

        Args:
            root_path: Repository root path.
            folders: List of folder information.

        Returns:
            True if microservices architecture is detected.
        """
        service_indicators = {"services", "microservices", "modules", "apps"}
        folder_names = {f.name.lower() for f in folders}

        if folder_names & service_indicators:
            docker_files = [
                f for f in os.listdir(root_path)
                if f.startswith("docker-compose")
            ]
            if docker_files:
                return True

        return False

    def _detect_serverless(self, root_path: str, frameworks: list[FrameworkInfo]) -> bool:
        """Check for serverless architecture.

        Args:
            root_path: Repository root path.
            frameworks: List of detected frameworks.

        Returns:
            True if serverless architecture is detected.
        """
        serverless_indicators = {
            "AWS Lambda",
            "Azure Functions",
            "Google Cloud Functions",
            "Vercel",
            "Netlify",
        }
        framework_names = {f.name for f in frameworks}

        if framework_names & serverless_indicators:
            return True

        serverless_files = [
            "serverless.yml",
            "serverless.yaml",
            "sam-template.yaml",
            "template.yml",
        ]

        for file in serverless_files:
            if os.path.exists(os.path.join(root_path, file)):
                return True

        return False

    def _detect_entry_points(
        self, root_path: str, frameworks: list[FrameworkInfo]
    ) -> list[str]:
        """Find main entry points.

        Args:
            root_path: Repository root path.
            frameworks: List of detected frameworks.

        Returns:
            List of entry point file paths.
        """
        entry_points = []

        common_entries = [
            "main.py",
            "app.py",
            "manage.py",
            "server.js",
            "index.js",
            "index.ts",
            "app.js",
            "main.ts",
            "Program.cs",
            "Startup.cs",
        ]

        for entry in common_entries:
            if os.path.exists(os.path.join(root_path, entry)):
                entry_points.append(entry)

        return entry_points

    def _detect_main_modules(self, folders: list[FolderInfo]) -> list[str]:
        """Detect main modules from folder structure.

        Args:
            folders: List of folder information.

        Returns:
            List of main module names.
        """
        main_purposes = {"controllers", "services", "models", "repositories", "api"}
        return [
            f.name
            for f in folders
            if f.purpose in main_purposes and f.file_count > 0
        ][:10]

    def _detect_authentication(
        self, root_path: str, folder_purposes: set[str]
    ) -> bool:
        """Detect authentication implementation.

        Args:
            root_path: Repository root path.
            folder_purposes: Set of folder purposes.

        Returns:
            True if authentication is detected.
        """
        auth_indicators = {"auth", "authentication", "authorization", "middleware"}
        if folder_purposes & auth_indicators:
            return True

        auth_files = [
            "auth.py",
            "authentication.py",
            "middleware.py",
            "auth.js",
            "auth.ts",
        ]

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in {"node_modules", ".venv", "venv", "__pycache__", ".git"}
            ]

            for filename in filenames:
                if filename in auth_files:
                    return True

        return False
