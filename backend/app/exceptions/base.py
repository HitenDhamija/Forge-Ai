"""Base exception class for ForgeAI."""


class ForgeAIException(Exception):
    """Base exception for all ForgeAI errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        self.error_code = "FORGEAI_ERROR"
        self.status_code = 500
        super().__init__(message)
