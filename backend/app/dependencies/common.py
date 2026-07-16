"""Common FastAPI dependencies."""

from fastapi import Query, Request

from app.schemas.common import PaginationParams


def get_request_id(request: Request) -> str:
    """Extract the request ID from the request state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The request ID string set by the ``RequestIdMiddleware``.

    Raises:
        RuntimeError: If the request ID is not present in request state.
    """
    request_id: str | None = getattr(request.state, "request_id", None)
    if request_id is None:
        raise RuntimeError("Request ID not found in request state.")
    return request_id


def get_current_page(
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    page: int = Query(1, ge=1, description="Page number"),
) -> PaginationParams:
    """FastAPI dependency that extracts pagination parameters from query strings.

    Args:
        per_page: Number of items per page (default 20, max 100).
        page: Page number (default 1).

    Returns:
        A ``PaginationParams`` instance with validated values.
    """
    return PaginationParams(page=page, per_page=per_page)
