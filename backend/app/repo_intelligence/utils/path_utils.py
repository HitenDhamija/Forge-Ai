"""Path utilities."""

import os


def normalize_path(path: str) -> str:
    """Normalize a file path.

    Args:
        path: Path to normalize.

    Returns:
        Normalized path with forward slashes.
    """
    return os.path.normpath(path).replace("\\", "/")


def get_relative_path(path: str, root: str) -> str:
    """Get path relative to root.

    Args:
        path: Full path.
        root: Root path to make relative to.

    Returns:
        Relative path string.
    """
    return os.path.relpath(path, root)


def ensure_directory(path: str) -> None:
    """Create directory if it doesn't exist.

    Args:
        path: Directory path to create.
    """
    os.makedirs(path, exist_ok=True)
