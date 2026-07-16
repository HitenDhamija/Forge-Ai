"""Generic base repository using SQLAlchemy async sessions."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Abstract base repository providing CRUD operations for a model.

    Subclass this and set ``model`` to the SQLAlchemy model to get
    standard database access patterns without duplicating boilerplate.

    Args:
        session: An async SQLAlchemy session.
    """

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, id: UUID) -> T | None:
        """Retrieve a single record by its UUID primary key.

        Args:
            id: The UUID of the record to fetch.

        Returns:
            The model instance, or ``None`` if not found.
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == str(id))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: list[Any] | None = None,
    ) -> list[T]:
        """Retrieve multiple records with optional filtering.

        Args:
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.
            filters: Optional list of SQLAlchemy filter expressions.

        Returns:
            A list of model instances.
        """
        query = select(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, filters: list[Any] | None = None) -> int:
        """Count total records matching optional filters.

        Args:
            filters: Optional list of SQLAlchemy filter expressions.

        Returns:
            The total number of matching records.
        """
        query = select(func.count()).select_from(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def create(self, obj: T) -> T:
        """Persist a new model instance.

        Args:
            obj: The model instance to create.

        Returns:
            The created model instance (with database-generated fields).
        """
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T, data: dict[str, Any]) -> T:
        """Update an existing model instance with new values.

        Args:
            obj: The model instance to update.
            data: A dictionary of attribute names to new values.

        Returns:
            The updated model instance.
        """
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        """Delete a model instance.

        Args:
            obj: The model instance to delete.
        """
        await self.session.delete(obj)
        await self.session.flush()
