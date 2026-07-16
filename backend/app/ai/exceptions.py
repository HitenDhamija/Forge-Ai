"""AI-specific exception classes."""

from app.exceptions import ForgeBaseException


class OllamaConnectionException(ForgeBaseException):
    """Cannot connect to Ollama server."""

    def __init__(self, message: str = "Cannot connect to Ollama server") -> None:
        super().__init__(message)


class OllamaNotInstalledException(ForgeBaseException):
    """Ollama is not installed or not found."""

    def __init__(self, message: str = "Ollama is not installed or not found") -> None:
        super().__init__(message)


class ModelNotFoundException(ForgeBaseException):
    """Requested model is not available locally."""

    def __init__(self, message: str = "Model not found") -> None:
        super().__init__(message)


class ModelLoadingException(ForgeBaseException):
    """Model failed to load."""

    def __init__(self, message: str = "Failed to load model") -> None:
        super().__init__(message)


class StreamingException(ForgeBaseException):
    """Streaming error occurred."""

    def __init__(self, message: str = "Streaming error occurred") -> None:
        super().__init__(message)


class PromptTooLongException(ForgeBaseException):
    """Prompt exceeds maximum allowed length."""

    def __init__(self, message: str = "Prompt exceeds maximum allowed length") -> None:
        super().__init__(message)


class ConversationNotFoundException(ForgeBaseException):
    """Conversation not found."""

    def __init__(self, message: str = "Conversation not found") -> None:
        super().__init__(message)


class ModelSwitchException(ForgeBaseException):
    """Failed to switch model."""

    def __init__(self, message: str = "Failed to switch model") -> None:
        super().__init__(message)


class AITimeoutException(ForgeBaseException):
    """Request timed out."""

    def __init__(self, message: str = "Request timed out") -> None:
        super().__init__(message)
