"""Convenience re-export of the SQLAlchemy Base for model imports."""

from app.database.base import Base, BaseModel, TimestampMixin, UUIDMixin

__all__ = ["Base", "BaseModel", "TimestampMixin", "UUIDMixin"]
