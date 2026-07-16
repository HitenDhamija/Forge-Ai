"""Standard response schemas used across the API."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseStatus(str, Enum):
    """Enumeration of possible API response statuses."""

    SUCCESS = "success"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"


class BaseResponse(BaseModel, Generic[T]):
    """Standard API response envelope.

    Attributes:
        status: The response status.
        message: A human-readable message.
        data: Optional payload.
        timestamp: ISO-8601 UTC timestamp of the response.
        request_id: Correlation identifier for the request.
    """

    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = "OK"
    data: T | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response envelope.

    Attributes:
        status: Always ``ResponseStatus.ERROR``.
        message: A human-readable error summary.
        errors: Optional list of detailed error objects.
        timestamp: ISO-8601 UTC timestamp of the response.
        request_id: Correlation identifier for the request.
    """

    status: ResponseStatus = ResponseStatus.ERROR
    message: str
    errors: list[dict[str, Any]] | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response envelope.

    Attributes:
        status: The response status.
        message: A human-readable message.
        data: List of items for the current page.
        timestamp: ISO-8601 UTC timestamp of the response.
        request_id: Correlation identifier for the request.
        page: Current page number (1-indexed).
        per_page: Number of items per page.
        total: Total number of items across all pages.
        total_pages: Total number of pages.
    """

    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = "OK"
    data: list[T] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str | None = None
    page: int = 1
    per_page: int = 20
    total: int = 0
    total_pages: int = 0


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints.

    Attributes:
        page: Page number (1-indexed, default 1).
        per_page: Items per page (default 20, max 100).
    """

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class HealthResponse(BaseModel):
    """Response for the health check endpoint.

    Attributes:
        status: Service health status.
        version: Application version string.
        environment: Current deployment environment.
    """

    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"
