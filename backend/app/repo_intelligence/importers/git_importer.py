"""Git clone importer."""

import asyncio
import os

from app.core.config import get_settings
from app.core.logging import get_logger
from app.repo_intelligence.config import get_repo_settings
from app.repo_intelligence.exceptions import GitCloneException, InvalidRepositoryException
from app.repo_intelligence.importers.base import BaseImporter

logger = get_logger(__name__)


class GitImporter(BaseImporter):
    """Importer for Git repositories via clone."""

    async def import_repository(self, source: str, target_dir: str) -> str:
        """Import a repository by cloning from a Git URL.

        Args:
            source: Git repository URL.
            target_dir: Target directory to clone into.

        Returns:
            Path to the cloned repository.

        Raises:
            GitCloneException: If clone operation fails.
            InvalidRepositoryException: If the source URL is invalid.
        """
        settings = get_repo_settings()

        if not source:
            raise InvalidRepositoryException("Git URL is required")

        os.makedirs(target_dir, exist_ok=True)

        clone_cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--single-branch",
            source,
            target_dir,
        ]

        try:
            logger.info("Starting git clone", url=source, target=target_dir)

            process = await asyncio.create_subprocess_exec(
                *clone_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=settings.GIT_TIMEOUT
            )

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                raise GitCloneException(f"Git clone failed: {error_msg}")

            logger.info("Git clone completed", url=source, target=target_dir)
            return target_dir

        except asyncio.TimeoutError:
            if process:
                process.kill()
            raise GitCloneException(
                f"Git clone timed out after {settings.GIT_TIMEOUT} seconds"
            )
        except FileNotFoundError:
            raise GitCloneException("Git is not installed or not in PATH")
        except Exception as e:
            raise GitCloneException(f"Git clone failed: {e}") from e

    async def validate(self, source: str) -> bool:
        """Validate a Git URL before cloning.

        Args:
            source: Git repository URL.

        Returns:
            True if the URL appears valid.
        """
        if not source:
            return False

        valid_prefixes = [
            "https://",
            "http://",
            "git://",
            "ssh://",
            "git@",
        ]

        return any(source.startswith(prefix) for prefix in valid_prefixes)
