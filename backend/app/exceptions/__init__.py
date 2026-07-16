"""Custom exception classes for the ForgeAI application."""

from app.exceptions.base import ForgeAIException


class ForgeBaseException(Exception):
    """Base exception class for all ForgeAI application errors.

    Attributes:
        message: A human-readable description of the error.
    """

    def __init__(self, message: str = "An unexpected error occurred") -> None:
        self.message = message
        super().__init__(self.message)


class NotFoundException(ForgeBaseException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message)


class BadRequestException(ForgeBaseException):
    """Raised when the request is malformed or invalid."""

    def __init__(self, message: str = "Bad request") -> None:
        super().__init__(message)


class UnauthorizedException(ForgeBaseException):
    """Raised when the user is not authenticated."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message)


class ForbiddenException(ForgeBaseException):
    """Raised when the user lacks permission to perform the action."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message)


class ConflictException(ForgeBaseException):
    """Raised when the request conflicts with current state."""

    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message)


class ValidationException(ForgeBaseException):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message)


class InternalServerException(ForgeBaseException):
    """Raised when an internal server error occurs."""

    def __init__(self, message: str = "Internal server error") -> None:
        super().__init__(message)
