"""Utility helper functions."""

from datetime import datetime
from uuid import UUID, uuid4


def generate_uuid() -> UUID:
    """Generate and return a new UUID4."""
    return uuid4()


def format_datetime(dt: datetime) -> str:
    """Format a datetime object as an ISO-8601 string.

    Args:
        dt: The datetime to format.

    Returns:
        The ISO-8601 formatted string.
    """
    return dt.isoformat()


def truncate_string(s: str, max_length: int = 100) -> str:
    """Truncate a string to the given maximum length.

    If the string exceeds ``max_length``, it is truncated and an
    ellipsis (``...``) is appended.

    Args:
        s: The string to truncate.
        max_length: The maximum allowed length (default 100).

    Returns:
        The original or truncated string.
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."
