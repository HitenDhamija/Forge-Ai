"""Repository intelligence exceptions."""

from app.exceptions import ForgeBaseException


class RepositoryNotFoundException(ForgeBaseException):
    """Raised when a repository is not found."""

    def __init__(self, message: str = "Repository not found") -> None:
        super().__init__(message)


class RepositoryImportException(ForgeBaseException):
    """Raised when repository import fails."""

    def __init__(self, message: str = "Repository import failed") -> None:
        super().__init__(message)


class RepositoryTooLargeException(ForgeBaseException):
    """Raised when repository exceeds size limits."""

    def __init__(self, message: str = "Repository exceeds maximum size limit") -> None:
        super().__init__(message)


class UnsupportedLanguageException(ForgeBaseException):
    """Raised when an unsupported language is encountered."""

    def __init__(self, message: str = "Unsupported programming language") -> None:
        super().__init__(message)


class AnalysisFailedException(ForgeBaseException):
    """Raised when repository analysis fails."""

    def __init__(self, message: str = "Repository analysis failed") -> None:
        super().__init__(message)


class InvalidRepositoryException(ForgeBaseException):
    """Raised when repository structure is invalid."""

    def __init__(self, message: str = "Invalid repository structure") -> None:
        super().__init__(message)


class GitCloneException(ForgeBaseException):
    """Raised when git clone operation fails."""

    def __init__(self, message: str = "Git clone operation failed") -> None:
        super().__init__(message)
