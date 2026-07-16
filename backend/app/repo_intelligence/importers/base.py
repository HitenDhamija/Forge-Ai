"""Base importer interface."""

from abc import ABC, abstractmethod


class BaseImporter(ABC):
    """Abstract base class for repository importers."""

    @abstractmethod
    async def import_repository(self, source: str, target_dir: str) -> str:
        """Import a repository and return the local path.

        Args:
            source: The source path or URL.
            target_dir: The target directory to import to.

        Returns:
            The local path where the repository was imported.
        """
        ...

    @abstractmethod
    async def validate(self, source: str) -> bool:
        """Validate the source before import.

        Args:
            source: The source path or URL to validate.

        Returns:
            True if the source is valid, False otherwise.
        """
        ...
