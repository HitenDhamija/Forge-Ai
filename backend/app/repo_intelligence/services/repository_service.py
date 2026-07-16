"""Repository management service."""

import os
import shutil
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger
from app.repo_intelligence.config import RepoIntelligenceSettings
from app.repo_intelligence.exceptions import (
    RepositoryNotFoundException,
    RepositoryTooLargeException,
)
from app.repo_intelligence.graph.semantic_graph import SemanticGraphBuilder
from app.repo_intelligence.importers import get_importer
from app.repo_intelligence.schemas.analysis import AnalysisResult
from app.repo_intelligence.schemas.graph import SemanticGraph
from app.repo_intelligence.schemas.repository import (
    RepositoryCreate,
    RepositoryInfo,
    RepositoryStatus,
)

logger = get_logger(__name__)


class RepositoryService:
    """Manages repository lifecycle."""

    def __init__(
        self,
        settings: RepoIntelligenceSettings,
        analysis_service: Any = None,
    ):
        """Initialize repository service.

        Args:
            settings: Repository intelligence settings.
            analysis_service: Optional analysis service instance.
        """
        self._settings = settings
        self._analysis_service = analysis_service
        self._repositories: dict[str, RepositoryInfo] = {}
        self._analysis_results: dict[str, AnalysisResult] = {}
        self._graphs: dict[str, SemanticGraph] = {}

        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    async def create_repository(self, request: RepositoryCreate) -> RepositoryInfo:
        """Create and import a new repository.

        Args:
            request: Repository creation request.

        Returns:
            RepositoryInfo for the created repository.

        Raises:
            RepositoryTooLargeException: If repository exceeds size limits.
        """
        repo_id = str(uuid.uuid4())
        repo_dir = os.path.join(self._settings.TEMP_DIR, repo_id)

        info = RepositoryInfo(
            id=repo_id,
            name=request.name,
            description=request.description,
            status=RepositoryStatus.IMPORTING,
            import_method=request.import_method,
            source_url=request.source_url,
            local_path=repo_dir,
            created_at=datetime.now(UTC).isoformat(),
            analyzed_at=None,
        )
        self._repositories[repo_id] = info

        try:
            importer = get_importer(request.import_method)

            source = request.source_url or request.source_path
            if not source:
                from app.repo_intelligence.exceptions import InvalidRepositoryException
                raise InvalidRepositoryException("Source URL or path is required")

            local_path = await importer.import_repository(source, repo_dir)
            info.local_path = local_path
            info.status = RepositoryStatus.ANALYZING

            if self._analysis_service:
                try:
                    analysis_result, graph = await self._analysis_service.analyze(
                        repo_id, local_path
                    )
                    self._analysis_results[repo_id] = analysis_result
                    self._graphs[repo_id] = graph
                    info.status = RepositoryStatus.READY
                    info.analyzed_at = datetime.now(UTC).isoformat()
                except Exception as e:
                    logger.error("Analysis failed", repo_id=repo_id, error=str(e))
                    info.status = RepositoryStatus.ERROR
                    info.error_message = str(e)
            else:
                info.status = RepositoryStatus.READY

            logger.info("Repository created", repo_id=repo_id, name=request.name)

        except Exception as e:
            info.status = RepositoryStatus.ERROR
            info.error_message = str(e)
            logger.error("Repository creation failed", repo_id=repo_id, error=str(e))
            raise

        return info

    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        """Get repository by ID.

        Args:
            repo_id: Repository identifier.

        Returns:
            RepositoryInfo for the repository.

        Raises:
            RepositoryNotFoundException: If repository is not found.
        """
        info = self._repositories.get(repo_id)
        if info is None:
            raise RepositoryNotFoundException(f"Repository {repo_id} not found")
        return info

    async def list_repositories(self) -> list[RepositoryInfo]:
        """List all repositories.

        Returns:
            List of RepositoryInfo objects.
        """
        return list(self._repositories.values())

    async def delete_repository(self, repo_id: str) -> bool:
        """Delete a repository and its analysis.

        Args:
            repo_id: Repository identifier.

        Returns:
            True if deleted successfully.

        Raises:
            RepositoryNotFoundException: If repository is not found.
        """
        if repo_id not in self._repositories:
            raise RepositoryNotFoundException(f"Repository {repo_id} not found")

        info = self._repositories[repo_id]

        try:
            if os.path.exists(info.local_path):
                shutil.rmtree(info.local_path)
        except OSError as e:
            logger.warning("Failed to delete repository files", error=str(e))

        del self._repositories[repo_id]
        self._analysis_results.pop(repo_id, None)
        self._graphs.pop(repo_id, None)

        logger.info("Repository deleted", repo_id=repo_id)
        return True

    async def get_analysis(self, repo_id: str) -> AnalysisResult:
        """Get analysis results for a repository.

        Args:
            repo_id: Repository identifier.

        Returns:
            AnalysisResult for the repository.

        Raises:
            RepositoryNotFoundException: If repository is not found.
        """
        if repo_id not in self._repositories:
            raise RepositoryNotFoundException(f"Repository {repo_id} not found")

        result = self._analysis_results.get(repo_id)
        if result is None:
            raise RepositoryNotFoundException(
                f"Analysis not found for repository {repo_id}"
            )
        return result

    async def get_graph(self, repo_id: str) -> SemanticGraph:
        """Get semantic graph for a repository.

        Args:
            repo_id: Repository identifier.

        Returns:
            SemanticGraph for the repository.

        Raises:
            RepositoryNotFoundException: If repository is not found.
        """
        if repo_id not in self._repositories:
            raise RepositoryNotFoundException(f"Repository {repo_id} not found")

        graph = self._graphs.get(repo_id)
        if graph is None:
            raise RepositoryNotFoundException(
                f"Graph not found for repository {repo_id}"
            )
        return graph

    async def get_summary(self, repo_id: str) -> dict[str, Any]:
        """Get human-readable summary of a repository.

        Args:
            repo_id: Repository identifier.

        Returns:
            Dictionary with repository summary.
        """
        info = await self.get_repository(repo_id)

        summary: dict[str, Any] = {
            "id": info.id,
            "name": info.name,
            "description": info.description,
            "status": info.status,
            "created_at": info.created_at,
            "analyzed_at": info.analyzed_at,
        }

        result = self._analysis_results.get(repo_id)
        if result:
            summary["languages"] = [
                {"name": l.name, "percentage": l.percentage}
                for l in result.languages
            ]
            summary["frameworks"] = [
                {"name": f.name, "confidence": f.confidence}
                for f in result.frameworks
            ]
            summary["architecture"] = {
                "style": result.architecture.style,
                "description": result.architecture.description,
            }
            summary["stats"] = {
                "total_files": result.total_files,
                "total_lines": result.total_lines,
                "routes_count": len(result.routes),
                "models_count": len(result.database_models),
                "dependencies_count": len(result.dependencies),
            }

        return summary
