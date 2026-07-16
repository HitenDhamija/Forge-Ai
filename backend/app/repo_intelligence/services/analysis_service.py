"""Analysis orchestration service."""

import os
import time
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.repo_intelligence.analyzers.architecture_analyzer import ArchitectureAnalyzer
from app.repo_intelligence.analyzers.ast_parser import ASTParser
from app.repo_intelligence.analyzers.config_detector import ConfigDetector
from app.repo_intelligence.analyzers.database_detector import DatabaseDetector
from app.repo_intelligence.analyzers.dependency_analyzer import DependencyAnalyzer
from app.repo_intelligence.analyzers.directory_analyzer import DirectoryAnalyzer
from app.repo_intelligence.analyzers.framework_detector import FrameworkDetector
from app.repo_intelligence.analyzers.language_detector import LanguageDetector
from app.repo_intelligence.analyzers.route_detector import RouteDetector
from app.repo_intelligence.config import RepoIntelligenceSettings
from app.repo_intelligence.graph.semantic_graph import SemanticGraphBuilder
from app.repo_intelligence.schemas.analysis import AnalysisResult
from app.repo_intelligence.schemas.graph import SemanticGraph

logger = get_logger(__name__)


class AnalysisService:
    """Orchestrates the full repository analysis pipeline."""

    def __init__(self, settings: RepoIntelligenceSettings):
        """Initialize analysis service.

        Args:
            settings: Repository intelligence settings.
        """
        self._settings = settings
        self._dir_analyzer = DirectoryAnalyzer()
        self._lang_detector = LanguageDetector()
        self._framework_detector = FrameworkDetector()
        self._dep_analyzer = DependencyAnalyzer()
        self._ast_parser = ASTParser()
        self._route_detector = RouteDetector()
        self._db_detector = DatabaseDetector()
        self._config_detector = ConfigDetector()
        self._arch_analyzer = ArchitectureAnalyzer()
        self._graph_builder = SemanticGraphBuilder()

    async def analyze(
        self, repo_id: str, repo_path: str
    ) -> tuple[AnalysisResult, SemanticGraph]:
        """Run the full analysis pipeline.

        Args:
            repo_id: Repository identifier.
            repo_path: Path to the repository root.

        Returns:
            Tuple of AnalysisResult and SemanticGraph.

        Raises:
            AnalysisFailedException: If analysis fails.
        """
        start_time = time.monotonic()

        logger.info("Starting repository analysis", repo_id=repo_id, path=repo_path)

        folder_structure = await self._dir_analyzer.analyze(repo_path)

        languages = await self._lang_detector.detect(repo_path)

        dependencies = await self._dep_analyzer.analyze(repo_path)

        frameworks = await self._framework_detector.detect(repo_path, dependencies)

        config_files = await self._config_detector.detect(repo_path)

        primary_lang = languages[0].name.lower() if languages else "python"
        code_elements = await self._ast_parser.parse_directory(
            repo_path, primary_lang
        )

        routes = await self._route_detector.detect(
            repo_path, frameworks, code_elements
        )

        database_models = await self._db_detector.detect(
            repo_path, frameworks, code_elements
        )

        architecture = await self._arch_analyzer.analyze(
            repo_path, folder_structure, frameworks, routes, database_models
        )

        elapsed_ms = (time.monotonic() - start_time) * 1000

        total_files = self._count_files(repo_path)
        total_lines = sum(l.total_lines for l in languages)

        result = AnalysisResult(
            repository_id=repo_id,
            analyzed_at=datetime.now(UTC).isoformat(),
            languages=languages,
            frameworks=frameworks,
            dependencies=dependencies,
            folder_structure=folder_structure,
            architecture=architecture,
            code_elements=code_elements,
            routes=routes,
            database_models=database_models,
            import_graph=[],
            config_files=config_files,
            entry_points=architecture.entry_points,
            total_files=total_files,
            total_lines=total_lines,
            analysis_time_ms=round(elapsed_ms, 1),
        )

        graph = self._graph_builder.build(
            repository_id=repo_id,
            repository_name=os.path.basename(repo_path),
            folder_structure=folder_structure,
            code_elements=code_elements,
            routes=routes,
            database_models=database_models,
            dependencies=dependencies,
            config_files=config_files,
        )

        logger.info(
            "Repository analysis completed",
            repo_id=repo_id,
            elapsed_ms=round(elapsed_ms, 1),
            languages=len(languages),
            frameworks=len(frameworks),
            routes=len(routes),
            models=len(database_models),
        )

        return result, graph

    def _count_files(self, root_path: str) -> int:
        """Count total files in repository.

        Args:
            root_path: Repository root path.

        Returns:
            Total file count.
        """
        count = 0
        ignored_dirs = {
            "node_modules",
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            "dist",
            "build",
            "target",
        }

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d for d in dirs if d not in ignored_dirs and not d.startswith(".")
            ]
            count += len(filenames)

        return count
