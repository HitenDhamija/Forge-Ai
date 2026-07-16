"""Analysis result models."""

from pydantic import BaseModel, Field

from app.repo_intelligence.schemas.repository import (
    ArchitectureSummary,
    DependencyInfo,
    FolderInfo,
    FrameworkInfo,
    LanguageInfo,
)


class CodeElement(BaseModel):
    """Represents a code element extracted from AST."""

    name: str
    type: str
    file_path: str
    line_start: int
    line_end: int | None = None
    docstring: str | None = None
    decorators: list[str] = []
    parent_class: str | None = None
    parameters: list[str] = []
    return_type: str | None = None
    imports: list[str] = []
    is_exported: bool = False


class RouteInfo(BaseModel):
    """Detected API route."""

    method: str
    path: str
    function_name: str
    file_path: str
    line_number: int
    middleware: list[str] = []
    authentication_required: bool = False
    parameters: list[str] = []
    response_model: str | None = None


class DatabaseModelInfo(BaseModel):
    """Detected database model."""

    name: str
    table_name: str | None = None
    file_path: str
    line_number: int
    fields: list[CodeElement] = []
    relationships: list[str] = []
    primary_key: str | None = None
    foreign_keys: list[str] = []


class ImportGraphEdge(BaseModel):
    """Import relationship edge in the dependency graph."""

    source: str
    target: str
    file_path: str


class AnalysisResult(BaseModel):
    """Complete repository analysis result."""

    repository_id: str
    analyzed_at: str
    languages: list[LanguageInfo]
    frameworks: list[FrameworkInfo]
    dependencies: list[DependencyInfo]
    folder_structure: list[FolderInfo]
    architecture: ArchitectureSummary
    code_elements: list[CodeElement]
    routes: list[RouteInfo]
    database_models: list[DatabaseModelInfo]
    import_graph: list[ImportGraphEdge]
    config_files: list[str]
    entry_points: list[str]
    total_files: int
    total_lines: int
    analysis_time_ms: float
