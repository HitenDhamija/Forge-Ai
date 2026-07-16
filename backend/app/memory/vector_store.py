"""ChromaDB vector store for semantic memory."""

from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.logging import get_logger
from app.memory.config import MemorySettings
from app.memory.exceptions import VectorStoreException

logger = get_logger(__name__)


class VectorStore:
    """ChromaDB vector store for semantic memory."""

    def __init__(self, settings: MemorySettings):
        self._settings = settings
        self._client: Any = None
        self._collections: dict[str, Any] = {}

    async def _get_client(self) -> chromadb.ClientAPI:
        """Get or create ChromaDB client."""
        if self._client is None:
            try:
                self._client = chromadb.Client(
                    ChromaSettings(
                        chroma_server_host=self._settings.CHROMA_HOST,
                        chroma_server_http_port=self._settings.CHROMA_PORT,
                        anonymized_telemetry=False,
                    )
                )
                logger.info(
                    "Connected to ChromaDB: host=%s port=%d",
                    self._settings.CHROMA_HOST,
                    self._settings.CHROMA_PORT,
                )
            except Exception as e:
                raise VectorStoreException(f"Failed to connect to ChromaDB: {e}") from e
        return self._client

    async def get_collection(self, name: str) -> Any:
        """Get or create a collection."""
        if name not in self._collections:
            try:
                client = await self._get_client()
                self._collections[name] = client.get_or_create_collection(
                    name=name, metadata={"hnsw:space": "cosine"}
                )
                logger.debug("Got collection: %s", name)
            except VectorStoreException:
                raise
            except Exception as e:
                raise VectorStoreException(
                    f"Failed to get collection {name}: {e}"
                ) from e
        return self._collections[name]

    async def add_documents(
        self,
        collection_name: str,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Add documents to a collection."""
        try:
            collection = await self.get_collection(collection_name)
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info(
                "Added %d documents to collection %s", len(ids), collection_name
            )
        except VectorStoreException:
            raise
        except Exception as e:
            raise VectorStoreException(
                f"Failed to add documents to {collection_name}: {e}"
            ) from e

    async def search(
        self,
        collection_name: str,
        query_embedding: list[float],
        top_k: int = 20,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search a collection."""
        try:
            collection = await self.get_collection(collection_name)
            return collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"],
            )
        except VectorStoreException:
            raise
        except Exception as e:
            raise VectorStoreException(
                f"Failed to search collection {collection_name}: {e}"
            ) from e

    async def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        try:
            client = await self._get_client()
            client.delete_collection(name)
            self._collections.pop(name, None)
            logger.info("Deleted collection: %s", name)
        except VectorStoreException:
            raise
        except Exception as e:
            raise VectorStoreException(
                f"Failed to delete collection {name}: {e}"
            ) from e

    async def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        try:
            client = await self._get_client()
            collections = client.list_collections()
            stats: dict[str, Any] = {"collections": [], "total_documents": 0}
            for col_name in collections:
                col = client.get_collection(col_name)
                count = col.count()
                stats["collections"].append({"name": col_name, "count": count})
                stats["total_documents"] += count
            return stats
        except VectorStoreException:
            raise
        except Exception as e:
            raise VectorStoreException(
                f"Failed to get stats: {e}"
            ) from e

    async def delete_documents(self, collection_name: str, where: dict[str, Any]) -> None:
        """Delete documents matching criteria."""
        try:
            collection = await self.get_collection(collection_name)
            collection.delete(where=where)
            logger.info(
                "Deleted documents from %s with filter: %s", collection_name, where
            )
        except VectorStoreException:
            raise
        except Exception as e:
            raise VectorStoreException(
                f"Failed to delete documents from {collection_name}: {e}"
            ) from e
