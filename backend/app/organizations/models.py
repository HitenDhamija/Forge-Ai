"""SQLAlchemy models for the Organizations module."""

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseModel


class OrganizationModel(BaseModel):
    """SQLAlchemy model for organizations."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    repositories: Mapped[list["OrganizationRepositoryModel"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    shared_knowledge: Mapped[list["SharedKnowledgeModel"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    workflow_templates: Mapped[list["WorkflowTemplateModel"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    collaborations: Mapped[list["CollaborationModel"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    comparison_results: Mapped[list["ComparisonResultModel"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )


class OrganizationRepositoryModel(BaseModel):
    """SQLAlchemy model for organization repository mappings."""

    __tablename__ = "organization_repositories"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    repository_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    repository_name: Mapped[str] = mapped_column(String(200), nullable=False)
    repository_path: Mapped[str] = mapped_column(String(500), nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    organization: Mapped["OrganizationModel"] = relationship(back_populates="repositories")


class SharedKnowledgeModel(BaseModel):
    """SQLAlchemy model for shared organizational knowledge."""

    __tablename__ = "shared_knowledge"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    source_repository_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    organization: Mapped["OrganizationModel"] = relationship(back_populates="shared_knowledge")


class WorkflowTemplateModel(BaseModel):
    """SQLAlchemy model for workflow templates."""

    __tablename__ = "workflow_templates"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    template_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    organization: Mapped["OrganizationModel"] = relationship(back_populates="workflow_templates")


class CollaborationModel(BaseModel):
    """SQLAlchemy model for collaborative interactions."""

    __tablename__ = "collaborations"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    collaboration_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    organization: Mapped["OrganizationModel"] = relationship(back_populates="collaborations")


class ComparisonResultModel(BaseModel):
    """SQLAlchemy model for repository comparison results."""

    __tablename__ = "comparison_results"

    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    repository_a_id: Mapped[str] = mapped_column(String(36), nullable=False)
    repository_b_id: Mapped[str] = mapped_column(String(36), nullable=False)
    comparison_type: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    organization: Mapped["OrganizationModel"] = relationship(back_populates="comparison_results")
