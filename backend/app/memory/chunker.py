"""Semantic chunker for code repositories."""

import hashlib
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.memory.config import MemorySettings
from app.memory.exceptions import ChunkingException
from app.memory.schemas.memory import ChunkType, SemanticChunk
from app.repo_intelligence.schemas.analysis import (
    AnalysisResult,
    CodeElement,
    DatabaseModelInfo,
    RouteInfo,
)
from app.repo_intelligence.schemas.repository import FolderInfo, FrameworkInfo

logger = get_logger(__name__)


class SemanticChunker:
    """Chunks code by engineering meaning, not random splits."""

    def __init__(self, settings: MemorySettings):
        self._settings = settings

    def chunk_repository(
        self,
        repository_id: str,
        repository_name: str,
        analysis: AnalysisResult,
    ) -> list[SemanticChunk]:
        """Create semantic chunks from repository analysis."""
        chunks: list[SemanticChunk] = []

        try:
            # Chunk: Repository overview
            chunks.append(
                self._chunk_repository_overview(repository_id, repository_name, analysis)
            )

            # Chunk: Each framework
            for fw in analysis.frameworks:
                chunk = self._chunk_framework(repository_id, repository_name, fw, analysis)
                if chunk:
                    chunks.append(chunk)

            # Chunk: Architecture
            chunks.append(
                self._chunk_architecture(repository_id, repository_name, analysis)
            )

            # Chunk: Each module/folder
            for folder in analysis.folder_structure:
                chunks.extend(
                    self._chunk_folder(repository_id, repository_name, folder, analysis)
                )

            # Chunk: Each class
            for element in analysis.code_elements:
                if element.type == "class":
                    chunk = self._chunk_class(repository_id, repository_name, element, analysis)
                    if chunk:
                        chunks.append(chunk)

            # Chunk: Each function (top-level and methods)
            for element in analysis.code_elements:
                if element.type in ("function", "method"):
                    chunk = self._chunk_function(
                        repository_id, repository_name, element, analysis
                    )
                    if chunk:
                        chunks.append(chunk)

            # Chunk: Routes
            for route in analysis.routes:
                chunk = self._chunk_route(repository_id, repository_name, route, analysis)
                if chunk:
                    chunks.append(chunk)

            # Chunk: Database models
            for model in analysis.database_models:
                chunk = self._chunk_database_model(
                    repository_id, repository_name, model, analysis
                )
                if chunk:
                    chunks.append(chunk)

            # Chunk: Dependencies summary
            chunks.append(
                self._chunk_dependencies(repository_id, repository_name, analysis)
            )

            logger.info(
                "Chunked repository: repo=%s chunks=%d", repository_id, len(chunks)
            )
            return [c for c in chunks if c is not None]

        except Exception as e:
            raise ChunkingException(f"Failed to chunk repository: {e}") from e

    def _chunk_repository_overview(
        self,
        repo_id: str,
        repo_name: str,
        analysis: AnalysisResult,
    ) -> SemanticChunk:
        """Create overview chunk for the repository."""
        languages = ", ".join([l.name for l in analysis.languages[:5]])
        frameworks = ", ".join([f.name for f in analysis.frameworks[:5]])

        parts = [
            f"Repository: {repo_name}",
            f"ID: {repo_id}",
            f"Languages: {languages}" if languages else None,
            f"Frameworks: {frameworks}" if frameworks else None,
            f"Total Files: {analysis.total_files}",
            f"Total Lines: {analysis.total_lines}",
            f"Architecture Style: {analysis.architecture.style.value}",
            f"Description: {analysis.architecture.description}",
            f"Entry Points: {', '.join(analysis.entry_points[:10])}" if analysis.entry_points else None,
            f"Config Files: {', '.join(analysis.config_files[:10])}" if analysis.config_files else None,
        ]

        content = self._build_content([p for p in parts if p])

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "purpose": "repository_overview",
            "tags": ["overview", "repository"],
        }

        return SemanticChunk(
            id=self._generate_chunk_id(repo_id, "repository", "overview"),
            repository_id=repo_id,
            chunk_type=ChunkType.REPOSITORY,
            content=content,
            metadata=metadata,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _chunk_framework(
        self,
        repo_id: str,
        repo_name: str,
        framework: FrameworkInfo,
        analysis: AnalysisResult,
    ) -> SemanticChunk | None:
        """Create chunk for a framework."""
        if not framework:
            return None

        parts = [
            f"Framework: {framework.name}",
            f"Version: {framework.version}" if framework.version else None,
            f"Confidence: {framework.confidence:.2f}",
            f"Evidence: {', '.join(framework.evidence[:5])}" if framework.evidence else None,
            f"Repository: {repo_name}",
        ]

        content = self._build_content([p for p in parts if p])

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "framework": framework.name,
            "purpose": "framework_info",
            "tags": ["framework", framework.name.lower()],
        }

        return SemanticChunk(
            id=self._generate_chunk_id(repo_id, "framework", framework.name),
            repository_id=repo_id,
            chunk_type=ChunkType.CONFIG,
            content=content,
            metadata=metadata,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _chunk_architecture(
        self,
        repo_id: str,
        repo_name: str,
        analysis: AnalysisResult,
    ) -> SemanticChunk:
        """Create architecture chunk."""
        arch = analysis.architecture

        parts = [
            f"Architecture Overview for {repo_name}",
            f"Style: {arch.style.value}",
            f"Description: {arch.description}",
            f"Main Modules: {', '.join(arch.main_modules[:10])}" if arch.main_modules else None,
            f"Entry Points: {', '.join(arch.entry_points[:10])}" if arch.entry_points else None,
            f"Authentication Detected: {arch.authentication_detected}",
            f"Database Detected: {arch.database_detected}",
            f"API Detected: {arch.api_detected}",
            f"Frontend Detected: {arch.frontend_detected}",
        ]

        content = self._build_content([p for p in parts if p])

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "purpose": "architecture_overview",
            "tags": ["architecture", arch.style.value],
        }

        return SemanticChunk(
            id=self._generate_chunk_id(repo_id, "architecture", "overview"),
            repository_id=repo_id,
            chunk_type=ChunkType.REPOSITORY,
            content=content,
            metadata=metadata,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _chunk_folder(
        self,
        repo_id: str,
        repo_name: str,
        folder: FolderInfo,
        analysis: AnalysisResult,
    ) -> list[SemanticChunk]:
        """Create chunks for a folder/module."""
        chunks = []

        # Main folder chunk
        parts = [
            f"Module: {folder.name}",
            f"Path: {folder.path}",
            f"Purpose: {folder.purpose}",
            f"File Count: {folder.file_count}",
        ]

        # Find related code elements in this folder
        related_elements = [
            e for e in analysis.code_elements
            if folder.path in e.file_path
        ][:20]  # Limit to 20 elements

        if related_elements:
            element_names = [e.name for e in related_elements]
            parts.append(f"Key Elements: {', '.join(element_names)}")

        content = self._build_content(parts)

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "module_path": folder.path,
            "purpose": folder.purpose,
            "tags": ["module", folder.name.lower()],
        }

        chunks.append(
            SemanticChunk(
                id=self._generate_chunk_id(repo_id, "module", folder.path),
                repository_id=repo_id,
                chunk_type=ChunkType.MODULE,
                content=content,
                metadata=metadata,
                created_at=datetime.now(UTC).isoformat(),
            )
        )

        return chunks

    def _chunk_class(
        self,
        repo_id: str,
        repo_name: str,
        element: CodeElement,
        analysis: AnalysisResult,
    ) -> SemanticChunk | None:
        """Create chunk for a class."""
        if not element or element.type != "class":
            return None

        parts = [
            f"Class: {element.name}",
            f"File: {element.file_path}",
            f"Lines: {element.line_start}-{element.line_end or 'N/A'}",
        ]

        if element.docstring:
            parts.append(f"Description: {element.docstring}")

        if element.decorators:
            parts.append(f"Decorators: {', '.join(element.decorators)}")

        if element.parameters:
            parts.append(f"Parameters: {', '.join(element.parameters)}")

        if element.parent_class:
            parts.append(f"Inherits From: {element.parent_class}")

        # Find related methods
        methods = [
            e for e in analysis.code_elements
            if e.type == "method" and e.parent_class == element.name
        ]
        if methods:
            method_names = [m.name for m in methods[:15]]
            parts.append(f"Methods: {', '.join(method_names)}")

        # Find related imports
        if element.imports:
            parts.append(f"Imports: {', '.join(element.imports[:10])}")

        content = self._build_content(parts)

        # Extract language from file path
        language = self._extract_language(element.file_path)

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "class_name": element.name,
            "file_path": element.file_path,
            "line_start": element.line_start,
            "line_end": element.line_end,
            "language": language,
            "purpose": "class_definition",
            "tags": ["class", element.name.lower(), language] if language else ["class", element.name.lower()],
        }

        return SemanticChunk(
            id=self._generate_chunk_id(repo_id, "class", element.name),
            repository_id=repo_id,
            chunk_type=ChunkType.CLASS,
            content=content,
            metadata=metadata,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _chunk_function(
        self,
        repo_id: str,
        repo_name: str,
        element: CodeElement,
        analysis: AnalysisResult,
    ) -> SemanticChunk | None:
        """Create chunk for a function or method."""
        if not element or element.type not in ("function", "method"):
            return None

        parts = [
            f"{'Method' if element.type == 'method' else 'Function'}: {element.name}",
            f"File: {element.file_path}",
            f"Lines: {element.line_start}-{element.line_end or 'N/A'}",
        ]

        if element.parent_class:
            parts.append(f"Class: {element.parent_class}")

        if element.docstring:
            parts.append(f"Description: {element.docstring}")

        if element.parameters:
            parts.append(f"Parameters: {', '.join(element.parameters)}")

        if element.return_type:
            parts.append(f"Returns: {element.return_type}")

        if element.decorators:
            parts.append(f"Decorators: {', '.join(element.decorators)}")

        if element.imports:
            parts.append(f"Imports: {', '.join(element.imports[:10])}")

        content = self._build_content(parts)

        language = self._extract_language(element.file_path)

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "function_name": element.name,
            "file_path": element.file_path,
            "line_start": element.line_start,
            "line_end": element.line_end,
            "language": language,
            "purpose": "function_definition",
            "tags": ["function", element.name.lower(), language] if language else ["function", element.name.lower()],
        }

        return SemanticChunk(
            id=self._generate_chunk_id(
                repo_id,
                "method" if element.type == "method" else "function",
                f"{element.parent_class}.{element.name}" if element.parent_class else element.name,
            ),
            repository_id=repo_id,
            chunk_type=ChunkType.FUNCTION,
            content=content,
            metadata=metadata,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _chunk_route(
        self,
        repo_id: str,
        repo_name: str,
        route: RouteInfo,
        analysis: AnalysisResult,
    ) -> SemanticChunk | None:
        """Create chunk for an API route."""
        if not route:
            return None

        parts = [
            f"API Route: {route.method.upper()} {route.path}",
            f"Function: {route.function_name}",
            f"File: {route.file_path}",
            f"Line: {route.line_number}",
        ]

        if route.authentication_required:
            parts.append("Authentication Required: Yes")

        if route.middleware:
            parts.append(f"Middleware: {', '.join(route.middleware)}")

        if route.parameters:
            parts.append(f"Parameters: {', '.join(route.parameters)}")

        if route.response_model:
            parts.append(f"Response Model: {route.response_model}")

        # Find related function documentation
        for element in analysis.code_elements:
            if element.name == route.function_name and element.docstring:
                parts.append(f"Description: {element.docstring}")
                break

        content = self._build_content(parts)

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "file_path": route.file_path,
            "line_start": route.line_number,
            "purpose": "api_route",
            "tags": ["api", "route", route.method.lower(), route.path],
        }

        return SemanticChunk(
            id=self._generate_chunk_id(
                repo_id, "route", f"{route.method}:{route.path}"
            ),
            repository_id=repo_id,
            chunk_type=ChunkType.ROUTE,
            content=content,
            metadata=metadata,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _chunk_database_model(
        self,
        repo_id: str,
        repo_name: str,
        model: DatabaseModelInfo,
        analysis: AnalysisResult,
    ) -> SemanticChunk | None:
        """Create chunk for a database model."""
        if not model:
            return None

        parts = [
            f"Database Model: {model.name}",
            f"Table: {model.table_name}" if model.table_name else None,
            f"File: {model.file_path}",
            f"Line: {model.line_number}",
        ]

        if model.primary_key:
            parts.append(f"Primary Key: {model.primary_key}")

        if model.foreign_keys:
            parts.append(f"Foreign Keys: {', '.join(model.foreign_keys)}")

        if model.relationships:
            parts.append(f"Relationships: {', '.join(model.relationships)}")

        if model.fields:
            field_names = [f.name for f in model.fields[:15]]
            parts.append(f"Fields: {', '.join(field_names)}")

        content = self._build_content([p for p in parts if p])

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "file_path": model.file_path,
            "line_start": model.line_number,
            "purpose": "database_model",
            "tags": ["database", "model", model.name.lower()],
        }

        return SemanticChunk(
            id=self._generate_chunk_id(repo_id, "database", model.name),
            repository_id=repo_id,
            chunk_type=ChunkType.DATABASE,
            content=content,
            metadata=metadata,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _chunk_dependencies(
        self,
        repo_id: str,
        repo_name: str,
        analysis: AnalysisResult,
    ) -> SemanticChunk:
        """Create dependencies summary chunk."""
        parts = [
            f"Dependencies for {repo_name}",
            f"Total Dependencies: {len(analysis.dependencies)}",
        ]

        # Group by production vs development
        prod_deps = [d for d in analysis.dependencies if d.is_production]
        dev_deps = [d for d in analysis.dependencies if not d.is_production]

        if prod_deps:
            prod_names = [f"{d.name}@{d.version or 'latest'}" for d in prod_deps[:20]]
            parts.append(f"Production Dependencies ({len(prod_deps)}): {', '.join(prod_names)}")

        if dev_deps:
            dev_names = [f"{d.name}@{d.version or 'latest'}" for d in dev_deps[:10]]
            parts.append(f"Development Dependencies ({len(dev_deps)}): {', '.join(dev_names)}")

        content = self._build_content(parts)

        metadata = {
            "repository_id": repo_id,
            "repository_name": repo_name,
            "purpose": "dependencies_overview",
            "tags": ["dependencies", "packages"],
        }

        return SemanticChunk(
            id=self._generate_chunk_id(repo_id, "dependencies", "overview"),
            repository_id=repo_id,
            chunk_type=ChunkType.REPOSITORY,
            content=content,
            metadata=metadata,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _generate_chunk_id(self, repo_id: str, chunk_type: str, name: str) -> str:
        """Generate deterministic chunk ID."""
        return hashlib.sha256(f"{repo_id}:{chunk_type}:{name}".encode()).hexdigest()[:16]

    def _build_content(self, parts: list[str]) -> str:
        """Build chunk content from parts, respecting token limit."""
        content = "\n\n".join(parts)
        # Truncate if too long
        max_chars = self._settings.CHUNK_MAX_TOKENS * 4
        if len(content) > max_chars:
            content = content[:max_chars] + "..."
        return content

    def _extract_language(self, file_path: str) -> str | None:
        """Extract programming language from file path."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".h": "c",
            ".swift": "swift",
            ".kt": "kotlin",
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return None
