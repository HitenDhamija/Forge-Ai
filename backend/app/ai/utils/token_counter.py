"""Token counting and text length utilities."""


def estimate_token_count(text: str) -> int:
    """Estimate token count using a character-based heuristic.

    Rough estimate: 1 token is approximately 4 characters for English text.

    Args:
        text: The input string.

    Returns:
        Estimated number of tokens.
    """
    return max(1, len(text) // 4)


def validate_prompt_length(text: str, max_length: int) -> bool:
    """Check whether a prompt is within the acceptable token length.

    Args:
        text: The prompt text.
        max_length: Maximum allowed token count.

    Returns:
        ``True`` if the estimated token count is within limits.
    """
    return estimate_token_count(text) <= max_length


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to an approximate token limit.

    Args:
        text: The input string.
        max_tokens: Maximum allowed tokens.

    Returns:
        The truncated string with ``"..."`` appended if it was shortened.
    """
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."
