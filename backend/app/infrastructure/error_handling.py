from __future__ import annotations

import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, TypeVar, ParamSpec

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .logging_config import CorrelationContext

logger = logging.getLogger("forge.error")

P = ParamSpec("P")
T = TypeVar("T")


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    BAD_REQUEST = "BAD_REQUEST"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    OPERATION_TIMEOUT = "OPERATION_TIMEOUT"
    DEPENDENCY_FAILED = "DEPENDENCY_FAILED"


@dataclass
class ErrorResponse:
    error_code: ErrorCode
    message: str
    details: dict[str, Any] | None = None
    correlation_id: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    suggestion: str | None = None


class ForgeAIException(Exception):
    def __init__(
        self,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        message: str = "An unexpected error occurred",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(ForgeAIException):
    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.VALIDATION_ERROR, message, details, status_code=400)


class NotFoundException(ForgeAIException):
    def __init__(self, message: str = "Resource not found", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.NOT_FOUND, message, details, status_code=404)


class UnauthorizedException(ForgeAIException):
    def __init__(self, message: str = "Authentication required", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.UNAUTHORIZED, message, details, status_code=401)


class ForbiddenException(ForgeAIException):
    def __init__(self, message: str = "Access denied", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.FORBIDDEN, message, details, status_code=403)


class ConflictException(ForgeAIException):
    def __init__(self, message: str = "Resource conflict", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.CONFLICT, message, details, status_code=409)


class RateLimitException(ForgeAIException):
    def __init__(self, message: str = "Rate limit exceeded", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.RATE_LIMITED, message, details, status_code=429)


class InternalException(ForgeAIException):
    def __init__(self, message: str = "Internal server error", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.INTERNAL_ERROR, message, details, status_code=500)


class ServiceUnavailableException(ForgeAIException):
    def __init__(self, message: str = "Service unavailable", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.SERVICE_UNAVAILABLE, message, details, status_code=503)


class TimeoutException(ForgeAIException):
    def __init__(self, message: str = "Operation timed out", details: dict[str, Any] | None = None):
        super().__init__(ErrorCode.OPERATION_TIMEOUT, message, details, status_code=408)


class ErrorHandler:
    def __init__(self):
        self._suggestions: dict[ErrorCode, str] = {
            ErrorCode.VALIDATION_ERROR: "Check your input parameters and try again.",
            ErrorCode.NOT_FOUND: "Verify the resource identifier and ensure it exists.",
            ErrorCode.UNAUTHORIZED: "Provide valid authentication credentials.",
            ErrorCode.FORBIDDEN: "You do not have permission to perform this action.",
            ErrorCode.CONFLICT: "The resource already exists or is in a conflicting state. Retry or use a different identifier.",
            ErrorCode.RATE_LIMITED: "Too many requests. Wait before retrying.",
            ErrorCode.INTERNAL_ERROR: "An internal error occurred. Contact support if it persists.",
            ErrorCode.SERVICE_UNAVAILABLE: "The service is temporarily unavailable. Retry later.",
            ErrorCode.BAD_REQUEST: "Review the request format and parameters.",
            ErrorCode.RESOURCE_EXHAUSTED: "The resource quota has been exhausted. Upgrade or wait for reset.",
            ErrorCode.OPERATION_TIMEOUT: "The operation took too long. Simplify the request or retry.",
            ErrorCode.DEPENDENCY_FAILED: "A downstream dependency failed. Check service status.",
        }

    def handle_exception(self, exc: Exception) -> ErrorResponse:
        if isinstance(exc, ForgeAIException):
            return ErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
                correlation_id=CorrelationContext.get_correlation_id(),
                suggestion=self.get_suggestion(exc.error_code),
            )

        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred",
            details={"original_error": type(exc).__name__, "original_message": str(exc)},
            correlation_id=CorrelationContext.get_correlation_id(),
            suggestion=self.get_suggestion(ErrorCode.INTERNAL_ERROR),
        )

    def get_suggestion(self, error_code: ErrorCode) -> str:
        return self._suggestions.get(error_code, "An error occurred. Contact support if it persists.")

    def log_error(self, error_response: ErrorResponse) -> None:
        log_data = {
            "error_code": error_response.error_code.value,
            "message": error_response.message,
            "details": error_response.details,
            "correlation_id": error_response.correlation_id,
        }
        if error_response.error_code in (
            ErrorCode.INTERNAL_ERROR,
            ErrorCode.SERVICE_UNAVAILABLE,
            ErrorCode.DEPENDENCY_FAILED,
        ):
            logger.error("Error response", extra=log_data)
        else:
            logger.warning("Error response", extra=log_data)


error_handler = ErrorHandler()


async def _forge_exception_handler(request: Request, exc: ForgeAIException) -> JSONResponse:
    correlation_id = request.headers.get("X-Correlation-ID") or CorrelationContext.get_correlation_id()
    if correlation_id:
        CorrelationContext.set_correlation_id(correlation_id)

    response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        correlation_id=correlation_id,
        suggestion=error_handler.get_suggestion(exc.error_code),
    )
    error_handler.log_error(response)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": response.error_code.value,
            "message": response.message,
            "details": response.details,
            "correlation_id": response.correlation_id,
            "timestamp": response.timestamp,
            "suggestion": response.suggestion,
        },
    )


async def _generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = request.headers.get("X-Correlation-ID") or CorrelationContext.get_correlation_id()
    if correlation_id:
        CorrelationContext.set_correlation_id(correlation_id)

    response = error_handler.handle_exception(exc)
    error_handler.log_error(response)

    return JSONResponse(
        status_code=500,
        content={
            "error_code": response.error_code.value,
            "message": response.message,
            "details": response.details,
            "correlation_id": response.correlation_id,
            "timestamp": response.timestamp,
            "suggestion": response.suggestion,
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    exception_hierarchy: list[type[ForgeAIException]] = [
        ValidationException,
        NotFoundException,
        UnauthorizedException,
        ForbiddenException,
        ConflictException,
        RateLimitException,
        ServiceUnavailableException,
        TimeoutException,
        InternalException,
    ]
    for exc_cls in exception_hierarchy:
        app.add_exception_handler(exc_cls, _forge_exception_handler)  # type: ignore[arg-type]

    app.add_exception_handler(Exception, _generic_exception_handler)  # type: ignore[arg-type]


def retry(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                last_exc: Exception | None = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as exc:
                        last_exc = exc
                        if attempt < max_retries:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {exc}"
                            )
                            await asyncio.sleep(delay * (2 ** attempt))
                raise last_exc  # type: ignore[misc]

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                last_exc: Exception | None = None
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as exc:
                        last_exc = exc
                        if attempt < max_retries:
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {exc}"
                            )
                            time.sleep(delay * (2 ** attempt))
                raise last_exc  # type: ignore[misc]

            return sync_wrapper  # type: ignore[return-value]

    return decorator
