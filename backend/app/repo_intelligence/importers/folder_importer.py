"""Local folder importer."""

import os
import shutil
from pathlib import Path

from app.core.logging import get_logger
from app.repo_intelligence.exceptions import (
    InvalidRepositoryException,
    RepositoryImportException,
)
from app.repo_intelligence.importers.base import BaseImporter

logger = get_logger(__name__)


class FolderImporter(BaseImporter):
    """Importer for local directories."""

    async def import_repository(self, source: str, target_dir: str) -> str:
        """Import a repository from a local directory.

        Copies or symlinks the source directory to the target location.

        Args:
            source: Path to the source directory.
            target_dir: Target directory to copy/link to.

        Returns:
            Path to the imported repository.

        Raises:
            RepositoryImportException: If import fails.
            InvalidRepositoryException: If source is invalid.
        """
        source_path = Path(source)

        if not source_path.exists():
            raise InvalidRepositoryException(f"Source directory does not exist: {source}")

        if not source_path.is_dir():
            raise InvalidRepositoryException(f"Source is not a directory: {source}")

        os.makedirs(target_dir, exist_ok=True)

        try:
            target_path = Path(target_dir)
            final_path = target_path / source_path.name

            if final_path.exists():
                shutil.rmtree(final_path)

            shutil.copytree(source, final_path)

            logger.info(
                "Folder import completed",
                source=source,
                target=str(final_path),
            )
            return str(final_path)

        except Exception as e:
            raise RepositoryImportException(f"Folder import failed: {e}") from e

    async def validate(self, source: str) -> bool:
        """Validate a local directory before import.

        Args:
            source: Path to the source directory.

        Returns:
            True if the directory is valid.
        """
        if not os.path.exists(source):
            return False

        if not os.path.isdir(source):
            return False

        try:
            os.listdir(source)
            return True
        except PermissionError:
            return False
