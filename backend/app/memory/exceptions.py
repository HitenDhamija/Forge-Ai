"""Memory-specific exceptions."""

from app.exceptions import ForgeBaseException


class EmbeddingException(ForgeBaseException):
    """Raised when embedding generation fails."""

    def __init__(self, message: str = "Failed to generate embeddings") -> None:
        super().__init__(message)


class VectorStoreException(ForgeBaseException):
    """Raised when ChromaDB operation fails."""

    def __init__(self, message: str = "Vector store operation failed") -> None:
        super().__init__(message)


class IndexingException(ForgeBaseException):
    """Raised when indexing pipeline fails."""

    def __init__(self, message: str = "Indexing pipeline failed") -> None:
        super().__init__(message)


class SearchException(ForgeBaseException):
    """Raised when search operation fails."""

    def __init__(self, message: str = "Search operation failed") -> None:
        super().__init__(message)


class ChunkingException(ForgeBaseException):
    """Raised when chunking fails."""

    def __init__(self, message: str = "Chunking failed") -> None:
        super().__init__(message)


class CollectionNotFoundException(ForgeBaseException):
    """Raised when a collection doesn't exist."""

    def __init__(self, message: str = "Collection not found") -> None:
        super().__init__(message)
