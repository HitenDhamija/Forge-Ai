"""Repository data models."""

from enum import Enum

from pydantic import BaseModel, Field


class ImportMethod(str, Enum):
    """Supported repository import methods."""

    ZIP = "zip"
    GIT = "git"
    FOLDER = "folder"


class RepositoryStatus(str, Enum):
    """Repository processing status."""

    IMPORTING = "importing"
    ANALYZING = "analyzing"
    READY = "ready"
    ERROR = "error"


class RepositoryCreate(BaseModel):
    """Schema for creating a new repository."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    import_method: ImportMethod
    source_url: str | None = None
    source_path: str | None = None


class RepositoryInfo(BaseModel):
    """Schema for repository information."""

    id: str
    name: str
    description: str | None
    status: RepositoryStatus
    import_method: ImportMethod
    source_url: str | None
    local_path: str
    created_at: str
    analyzed_at: str | None
    error_message: str | None = None


class LanguageInfo(BaseModel):
    """Detected programming language information."""

    name: str
    file_count: int
    total_lines: int
    percentage: float
    extensions: list[str]


class FrameworkInfo(BaseModel):
    """Detected framework information."""

    name: str
    version: str | None
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: list[str]


class DependencyInfo(BaseModel):
    """Project dependency information."""

    name: str
    version: str | None
    is_production: bool
    source_file: str


class FolderInfo(BaseModel):
    """Directory structure information."""

    name: str
    path: str
    purpose: str
    file_count: int
    children: list["FolderInfo"] = []


class ArchitectureStyle(str, Enum):
    """Detected architecture style."""

    MVC = "mvc"
    CLEAN = "clean"
    LAYERED = "layered"
    MICROSERVICES = "microservices"
    MONOLITH = "monolith"
    SERVERLESS = "serverless"
    UNKNOWN = "unknown"


class ArchitectureSummary(BaseModel):
    """Architecture analysis summary."""

    style: ArchitectureStyle
    description: str
    entry_points: list[str]
    main_modules: list[str]
    authentication_detected: bool
    database_detected: bool
    api_detected: bool
    frontend_detected: bool
