"""ZIP file importer."""

import os
import zipfile
from pathlib import Path

from app.core.logging import get_logger
from app.repo_intelligence.exceptions import RepositoryImportException, InvalidRepositoryException
from app.repo_intelligence.importers.base import BaseImporter

logger = get_logger(__name__)


class ZipImporter(BaseImporter):
    """Importer for ZIP archive files."""

    async def import_repository(self, source: str, target_dir: str) -> str:
        """Import a repository from a ZIP file.

        Args:
            source: Path to the ZIP file.
            target_dir: Target directory to extract to.

        Returns:
            Path to the extracted repository root.

        Raises:
            RepositoryImportException: If extraction fails.
            InvalidRepositoryException: If the ZIP is invalid.
        """
        if not os.path.exists(source):
            raise RepositoryImportException(f"ZIP file not found: {source}")

        if not zipfile.is_zipfile(source):
            raise InvalidRepositoryException(f"Invalid ZIP file: {source}")

        os.makedirs(target_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(source, "r") as zip_ref:
                zip_ref.extractall(target_dir)

            extracted_path = self._find_repository_root(target_dir)
            logger.info("ZIP import completed", source=source, target=extracted_path)
            return extracted_path
        except zipfile.BadZipFile as e:
            raise RepositoryImportException(f"Failed to extract ZIP: {e}") from e
        except Exception as e:
            raise RepositoryImportException(f"ZIP import failed: {e}") from e

    async def validate(self, source: str) -> bool:
        """Validate a ZIP file before import.

        Args:
            source: Path to the ZIP file.

        Returns:
            True if the ZIP file is valid.
        """
        if not os.path.exists(source):
            return False

        if not zipfile.is_zipfile(source):
            return False

        try:
            with zipfile.ZipFile(source, "r") as zip_ref:
                bad_file = zip_ref.testzip()
                return bad_file is None
        except Exception:
            return False

    def _find_repository_root(self, target_dir: str) -> str:
        """Find the repository root within extracted directory.

        If the ZIP contains a single top-level directory, use that as root.

        Args:
            target_dir: The directory where ZIP was extracted.

        Returns:
            Path to the repository root.
        """
        entries = [
            e
            for e in os.listdir(target_dir)
            if not e.startswith(".") or e == ".gitignore"
        ]

        if len(entries) == 1:
            single_entry = os.path.join(target_dir, entries[0])
            if os.path.isdir(single_entry):
                return single_entry

        return target_dir
