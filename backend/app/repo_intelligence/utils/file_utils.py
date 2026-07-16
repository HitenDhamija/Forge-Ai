"""File utilities."""

import fnmatch
import os


async def safe_read_file(file_path: str, max_size_kb: int = 1024) -> str | None:
    """Safely read a file with size limit.

    Args:
        file_path: Path to the file.
        max_size_kb: Maximum file size in kilobytes.

    Returns:
        File content as string, or None if file cannot be read.
    """
    try:
        if not os.path.exists(file_path):
            return None

        file_size = os.path.getsize(file_path)
        if file_size > max_size_kb * 1024:
            return None

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


async def count_lines(file_path: str) -> int:
    """Count lines in a file safely.

    Args:
        file_path: Path to the file.

    Returns:
        Number of lines, or 0 if file cannot be read.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeDecodeError):
        return 0


def should_ignore(path: str, ignored_patterns: list[str]) -> bool:
    """Check if path matches ignore patterns.

    Args:
        path: File or directory path.
        ignored_patterns: List of patterns to ignore.

    Returns:
        True if the path should be ignored.
    """
    basename = os.path.basename(path)

    for pattern in ignored_patterns:
        if fnmatch.fnmatch(basename, pattern):
            return True
        if fnmatch.fnmatch(path, pattern):
            return True

    return False


async def get_file_tree(root_path: str, ignored_dirs: list[str]) -> dict:
    """Build a file tree structure.

    Args:
        root_path: Root directory path.
        ignored_dirs: List of directory names to ignore.

    Returns:
        Nested dictionary representing the file tree.
    """
    tree: dict = {"name": os.path.basename(root_path), "type": "directory", "children": []}

    try:
        for entry in os.scandir(root_path):
            if entry.is_dir(follow_symlinks=False):
                if entry.name in ignored_dirs or entry.name.startswith("."):
                    continue
                child = await get_file_tree(entry.path, ignored_dirs)
                tree["children"].append(child)
            elif entry.is_file(follow_symlinks=False):
                tree["children"].append({
                    "name": entry.name,
                    "type": "file",
                    "size": os.path.getsize(entry.path),
                })
    except PermissionError:
        pass

    return tree
