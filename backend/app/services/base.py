"""Generic base service class."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from app.database.base import BaseModel
from app.repositories.base import BaseRepository

R = TypeVar("R", bound=BaseRepository[Any])


class BaseService(Generic[R]):
    """Base service that wraps a repository and adds business logic hooks.

    Subclass this to create domain-specific services. Override the hook
    methods to add validation, authorization, or side-effect logic.

    Args:
        repository: The repository instance used for data access.
    """

    def __init__(self, repository: R) -> None:
        self.repository = repository

    async def get_by_id(self, id: UUID) -> BaseModel | None:
        """Retrieve a single entity by ID.

        Args:
            id: The UUID of the entity.

        Returns:
            The entity instance, or ``None`` if not found.
        """
        return await self.repository.get_by_id(id)

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: list[Any] | None = None,
    ) -> list[BaseModel]:
        """Retrieve multiple entities.

        Args:
            skip: Offset for pagination.
            limit: Maximum number of results.
            filters: Optional list of filter expressions.

        Returns:
            A list of entity instances.
        """
        return await self.repository.get_all(skip=skip, limit=limit, filters=filters)

    async def count(self, filters: list[Any] | None = None) -> int:
        """Count total entities matching optional filters.

        Args:
            filters: Optional list of filter expressions.

        Returns:
            The total count.
        """
        return await self.repository.count(filters=filters)

    async def create(self, obj: BaseModel) -> BaseModel:
        """Create a new entity.

        Override this method to add pre-creation validation or
        post-creation side effects.

        Args:
            obj: The entity to persist.

        Returns:
            The created entity.
        """
        return await self.repository.create(obj)

    async def update(self, obj: BaseModel, data: dict[str, Any]) -> BaseModel:
        """Update an existing entity.

        Override this method to add pre-update validation or
        post-update side effects.

        Args:
            obj: The entity to update.
            data: Dictionary of fields to update.

        Returns:
            The updated entity.
        """
        return await self.repository.update(obj, data)

    async def delete(self, obj: BaseModel) -> None:
        """Delete an entity.

        Override this method to add pre-deletion checks or
        post-deletion cleanup.

        Args:
            obj: The entity to delete.
        """
        await self.repository.delete(obj)
