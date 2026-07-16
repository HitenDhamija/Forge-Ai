"""Repository importers package."""

from app.repo_intelligence.importers.base import BaseImporter
from app.repo_intelligence.importers.folder_importer import FolderImporter
from app.repo_intelligence.importers.git_importer import GitImporter
from app.repo_intelligence.importers.zip_importer import ZipImporter
from app.repo_intelligence.schemas.repository import ImportMethod


def get_importer(method: ImportMethod) -> BaseImporter:
    """Get the appropriate importer for the given method.

    Args:
        method: The import method to use.

    Returns:
        The appropriate importer instance.

    Raises:
        ValueError: If the import method is not supported.
    """
    importers = {
        ImportMethod.ZIP: ZipImporter,
        ImportMethod.GIT: GitImporter,
        ImportMethod.FOLDER: FolderImporter,
    }
    importer_class = importers.get(method)
    if importer_class is None:
        raise ValueError(f"Unknown import method: {method}")
    return importer_class()
