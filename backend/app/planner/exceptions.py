"""Planner-specific exceptions."""

from app.exceptions import ForgeBaseException


class PlanningException(ForgeBaseException):
    """General planning error."""

    def __init__(self, message: str = "Planning operation failed") -> None:
        super().__init__(message)


class IntentClassificationException(ForgeBaseException):
    """Failed to classify intent."""

    def __init__(self, message: str = "Failed to classify intent") -> None:
        super().__init__(message)


class TaskDecompositionException(ForgeBaseException):
    """Failed to decompose tasks."""

    def __init__(self, message: str = "Failed to decompose tasks") -> None:
        super().__init__(message)


class PlanNotFoundException(ForgeBaseException):
    """Plan not found."""

    def __init__(self, message: str = "Plan not found") -> None:
        super().__init__(message)


class PlanGenerationException(ForgeBaseException):
    """Failed to generate plan."""

    def __init__(self, message: str = "Failed to generate plan") -> None:
        super().__init__(message)
