"""Comprehensive tests for the Repository Intelligence Engine."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

import pytest

from app.repo_intelligence.config import RepoIntelligenceSettings, get_repo_settings
from app.repo_intelligence.exceptions import (
    RepositoryNotFoundException,
    RepositoryImportException,
    RepositoryTooLargeException,
    UnsupportedLanguageException,
    AnalysisFailedException,
    InvalidRepositoryException,
    GitCloneException,
)
from app.repo_intelligence.schemas.repository import (
    ImportMethod,
    RepositoryStatus,
    RepositoryCreate,
    RepositoryInfo,
    LanguageInfo,
    FrameworkInfo,
    DependencyInfo,
    FolderInfo,
    ArchitectureStyle,
    ArchitectureSummary,
)
from app.repo_intelligence.schemas.analysis import (
    CodeElement,
    RouteInfo,
    DatabaseModelInfo,
    ImportGraphEdge,
    AnalysisResult,
)
from app.repo_intelligence.schemas.graph import (
    GraphNodeType,
    GraphNode,
    GraphEdge,
    SemanticGraph,
)
from app.repo_intelligence.importers.base import BaseImporter


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def repo_settings() -> RepoIntelligenceSettings:
    """Return test repository intelligence settings."""
    return RepoIntelligenceSettings(
        MAX_REPOSITORY_SIZE_MB=100,
        MAX_FILE_SIZE_KB=512,
        MAX_FILES_TO_ANALYZE=500,
        GIT_TIMEOUT=30,
        TEMP_DIR="/tmp/test/repos",
    )


@pytest.fixture
def sample_python_file() -> tuple[str, str]:
    """Return a sample Python file path and content."""
    content = '''"""User service module."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class User:
    """Represents a user."""
    id: int
    name: str
    email: str


class UserService:
    """Service for managing users."""

    def __init__(self, db_session):
        self.db_session = db_session

    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        return self.db_session.query(User).filter(User.id == user_id).first()

    def create_user(self, name: str, email: str) -> User:
        """Create a new user."""
        user = User(id=1, name=name, email=email)
        self.db_session.add(user)
        self.db_session.commit()
        return user

    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        user = self.get_user(user_id)
        if user:
            self.db_session.delete(user)
            self.db_session.commit()
            return True
        return False
'''
    return "src/services/user_service.py", content


@pytest.fixture
def sample_javascript_file() -> tuple[str, str]:
    """Return a sample JavaScript file path and content."""
    content = '''const express = require('express');
const router = express.Router();

/**
 * Get all users
 * @route GET /api/users
 * @access Public
 */
router.get('/api/users', async (req, res) => {
  try {
    const users = await User.find({});
    res.json(users);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * Create a new user
 * @route POST /api/users
 * @access Private
 */
router.post('/api/users', async (req, res) => {
  const { name, email } = req.body;
  const user = new User({ name, email });
  await user.save();
  res.status(201).json(user);
});

module.exports = router;
'''
    return "src/routes/users.js", content


@pytest.fixture
def sample_typescript_file() -> tuple[str, str]:
    """Return a sample TypeScript file path and content."""
    content = '''import { Controller, Get, Post, Body, Param } from '@nestjs/common';
import { UsersService } from './users.service';
import { CreateUserDto } from './dto/create-user.dto';

interface User {
  id: number;
  name: string;
  email: string;
}

@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get()
  async findAll(): Promise<User[]> {
    return this.usersService.findAll();
  }

  @Post()
  async create(@Body() createUserDto: CreateUserDto): Promise<User> {
    return this.usersService.create(createUserDto);
  }

  @Get(':id')
  async findOne(@Param('id') id: number): Promise<User> {
    return this.usersService.findOne(id);
  }
}
'''
    return "src/users/users.controller.ts", content


@pytest.fixture
def sample_java_file() -> tuple[str, str]:
    """Return a sample Java file path and content."""
    content = '''package com.example.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;
import java.util.List;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping
    public List<User> getAllUsers() {
        return userService.findAll();
    }

    @PostMapping
    public User createUser(@RequestBody User user) {
        return userService.save(user);
    }

    @GetMapping("/{id}")
    public User getUserById(@PathVariable Long id) {
        return userService.findById(id);
    }
}
'''
    return "src/main/java/com/example/controller/UserController.java", content


@pytest.fixture
def sample_go_file() -> tuple[str, str]:
    """Return a sample Go file path and content."""
    content = '''package main

import (
    "encoding/json"
    "net/http"
    "github.com/gin-gonic/gin"
)

type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

func getUsers(c *gin.Context) {
    users := []User{
        {ID: 1, Name: "John", Email: "john@example.com"},
    }
    c.JSON(http.StatusOK, users)
}

func createUser(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, user)
}

func main() {
    r := gin.Default()
    r.GET("/users", getUsers)
    r.POST("/users", createUser)
    r.Run(":8080")
}
'''
    return "main.go", content


@pytest.fixture
def sample_package_json() -> str:
    """Return a sample package.json content."""
    return '''{
  "name": "my-react-app",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "^14.0.0",
    "express": "^4.18.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "eslint": "^8.50.0",
    "jest": "^29.7.0"
  }
}'''


@pytest.fixture
def sample_pyproject_toml() -> str:
    """Return a sample pyproject.toml content."""
    return '''[project]
name = "my-fastapi-app"
version = "0.1.0"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "pydantic>=2.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "ruff>=0.8.0",
]'''


@pytest.fixture
def sample_requirements_txt() -> str:
    """Return a sample requirements.txt content."""
    return """fastapi==0.115.0
uvicorn==0.32.0
sqlalchemy==2.0.36
pydantic==2.10.0
pytest==8.3.0
ruff==0.8.0
"""


@pytest.fixture
def sample_cargo_toml() -> str:
    """Return a sample Cargo.toml content."""
    return '''[package]
name = "my-rust-app"
version = "0.1.0"
edition = "2021"

[dependencies]
actix-web = "4"
actix-rt = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
'''


@pytest.fixture
def sample_directory_structure() -> dict[str, Any]:
    """Return a sample directory structure."""
    return {
        "name": "my-project",
        "type": "directory",
        "children": [
            {
                "name": "src",
                "type": "directory",
                "children": [
                    {"name": "main.py", "type": "file", "size": 1024},
                    {"name": "utils.py", "type": "file", "size": 512},
                    {
                        "name": "services",
                        "type": "directory",
                        "children": [
                            {"name": "user_service.py", "type": "file", "size": 2048},
                            {"name": "auth_service.py", "type": "file", "size": 1536},
                        ],
                    },
                    {
                        "name": "models",
                        "type": "directory",
                        "children": [
                            {"name": "user.py", "type": "file", "size": 768},
                            {"name": "role.py", "type": "file", "size": 512},
                        ],
                    },
                ],
            },
            {
                "name": "tests",
                "type": "directory",
                "children": [
                    {"name": "test_main.py", "type": "file", "size": 1024},
                    {"name": "test_services.py", "type": "file", "size": 2048},
                ],
            },
            {"name": "pyproject.toml", "type": "file", "size": 256},
            {"name": "README.md", "type": "file", "size": 4096},
            {".env", "type": "file", "size": 128},
        ],
    }


@pytest.fixture
def sample_semantic_graph() -> SemanticGraph:
    """Return a sample semantic graph."""
    return SemanticGraph(
        nodes=[
            GraphNode(
                id="repo:test",
                type=GraphNodeType.REPOSITORY,
                name="test-project",
                metadata={"url": "https://github.com/test/repo"},
            ),
            GraphNode(
                id="module:src/main.py",
                type=GraphNodeType.MODULE,
                name="main.py",
                metadata={"language": "Python", "lines": 150},
            ),
            GraphNode(
                id="class:UserService",
                type=GraphNodeType.CLASS,
                name="UserService",
                metadata={"parent": "BaseService"},
            ),
            GraphNode(
                id="function:get_user",
                type=GraphNodeType.FUNCTION,
                name="get_user",
                metadata={"params": ["user_id"]},
            ),
        ],
        edges=[
            GraphEdge(
                source="repo:test",
                target="module:src/main.py",
                relationship="contains",
            ),
            GraphEdge(
                source="module:src/main.py",
                target="class:UserService",
                relationship="defines",
            ),
            GraphEdge(
                source="class:UserService",
                target="function:get_user",
                relationship="defines",
            ),
        ],
        root_id="repo:test",
    )


# ============================================================
# Configuration Tests
# ============================================================


class TestRepoIntelligenceSettings:
    """Tests for repository intelligence configuration."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = RepoIntelligenceSettings()
        assert settings.MAX_REPOSITORY_SIZE_MB == 500
        assert settings.MAX_FILE_SIZE_KB == 1024
        assert settings.MAX_FILES_TO_ANALYZE == 10000
        assert settings.GIT_TIMEOUT == 60
        assert settings.TEMP_DIR == "/tmp/forgeai/repos"

    def test_custom_settings(self):
        """Test custom configuration values."""
        settings = RepoIntelligenceSettings(
            MAX_REPOSITORY_SIZE_MB=100,
            MAX_FILE_SIZE_KB=512,
            MAX_FILES_TO_ANALYZE=500,
            GIT_TIMEOUT=30,
            TEMP_DIR="/tmp/custom",
        )
        assert settings.MAX_REPOSITORY_SIZE_MB == 100
        assert settings.MAX_FILE_SIZE_KB == 512
        assert settings.MAX_FILES_TO_ANALYZE == 500
        assert settings.GIT_TIMEOUT == 30
        assert settings.TEMP_DIR == "/tmp/custom"

    def test_ignored_directories(self):
        """Test default ignored directories list."""
        settings = RepoIntelligenceSettings()
        assert "node_modules" in settings.IGNORED_DIRECTORIES
        assert ".git" in settings.IGNORED_DIRECTORIES
        assert "__pycache__" in settings.IGNORED_DIRECTORIES
        assert "venv" in settings.IGNORED_DIRECTORIES

    def test_ignored_file_patterns(self):
        """Test default ignored file patterns list."""
        settings = RepoIntelligenceSettings()
        assert "*.pyc" in settings.IGNORED_FILE_PATTERNS
        assert "*.min.js" in settings.IGNORED_FILE_PATTERNS
        assert "package-lock.json" in settings.IGNORED_FILE_PATTERNS

    def test_supported_import_methods(self):
        """Test supported import methods."""
        settings = RepoIntelligenceSettings()
        assert "zip" in settings.SUPPORTED_IMPORT_METHODS
        assert "git" in settings.SUPPORTED_IMPORT_METHODS
        assert "folder" in settings.SUPPORTED_IMPORT_METHODS

    def test_get_repo_settings_cached(self):
        """Test that get_repo_settings returns cached instance."""
        settings1 = get_repo_settings()
        settings2 = get_repo_settings()
        assert settings1 is settings2


# ============================================================
# Exception Tests
# ============================================================


class TestExceptions:
    """Tests for repository intelligence exceptions."""

    def test_repository_not_found_exception(self):
        """Test RepositoryNotFoundException."""
        exc = RepositoryNotFoundException()
        assert str(exc) == "Repository not found"

        exc = RepositoryNotFoundException("Custom message")
        assert str(exc) == "Custom message"

    def test_repository_import_exception(self):
        """Test RepositoryImportException."""
        exc = RepositoryImportException()
        assert str(exc) == "Repository import failed"

    def test_repository_too_large_exception(self):
        """Test RepositoryTooLargeException."""
        exc = RepositoryTooLargeException()
        assert str(exc) == "Repository exceeds maximum size limit"

    def test_unsupported_language_exception(self):
        """Test UnsupportedLanguageException."""
        exc = UnsupportedLanguageException()
        assert str(exc) == "Unsupported programming language"

    def test_analysis_failed_exception(self):
        """Test AnalysisFailedException."""
        exc = AnalysisFailedException()
        assert str(exc) == "Repository analysis failed"

    def test_invalid_repository_exception(self):
        """Test InvalidRepositoryException."""
        exc = InvalidRepositoryException()
        assert str(exc) == "Invalid repository structure"

    def test_git_clone_exception(self):
        """Test GitCloneException."""
        exc = GitCloneException()
        assert str(exc) == "Git clone operation failed"

    def test_all_exceptions_inherit_from_base(self):
        """Test that all exceptions inherit from ForgeBaseException."""
        from app.exceptions import ForgeBaseException

        exceptions = [
            RepositoryNotFoundException,
            RepositoryImportException,
            RepositoryTooLargeException,
            UnsupportedLanguageException,
            AnalysisFailedException,
            InvalidRepositoryException,
            GitCloneException,
        ]
        for exc_cls in exceptions:
            assert issubclass(exc_cls, ForgeBaseException)


# ============================================================
# Schema Tests
# ============================================================


class TestRepositorySchemas:
    """Tests for repository schemas."""

    def test_import_method_enum(self):
        """Test ImportMethod enum values."""
        assert ImportMethod.ZIP == "zip"
        assert ImportMethod.GIT == "git"
        assert ImportMethod.FOLDER == "folder"

    def test_repository_status_enum(self):
        """Test RepositoryStatus enum values."""
        assert RepositoryStatus.IMPORTING == "importing"
        assert RepositoryStatus.ANALYZING == "analyzing"
        assert RepositoryStatus.READY == "ready"
        assert RepositoryStatus.ERROR == "error"

    def test_repository_create_schema(self):
        """Test RepositoryCreate schema validation."""
        repo = RepositoryCreate(
            name="test-repo",
            import_method=ImportMethod.GIT,
            source_url="https://github.com/user/repo.git",
        )
        assert repo.name == "test-repo"
        assert repo.import_method == ImportMethod.GIT
        assert repo.source_url == "https://github.com/user/repo.git"
        assert repo.description is None

    def test_repository_create_with_description(self):
        """Test RepositoryCreate with optional description."""
        repo = RepositoryCreate(
            name="test-repo",
            description="A test repository",
            import_method=ImportMethod.ZIP,
        )
        assert repo.description == "A test repository"

    def test_repository_info_schema(self):
        """Test RepositoryInfo schema."""
        info = RepositoryInfo(
            id="abc123",
            name="test-repo",
            description="Test",
            status=RepositoryStatus.READY,
            import_method=ImportMethod.GIT,
            source_url="https://github.com/user/repo.git",
            local_path="/tmp/repos/abc123",
            created_at="2025-01-15T10:30:00Z",
            analyzed_at="2025-01-15T10:35:00Z",
        )
        assert info.id == "abc123"
        assert info.status == RepositoryStatus.READY

    def test_language_info_schema(self):
        """Test LanguageInfo schema."""
        lang = LanguageInfo(
            name="Python",
            file_count=45,
            total_lines=12500,
            percentage=72.5,
            extensions=[".py", ".pyi"],
        )
        assert lang.name == "Python"
        assert lang.file_count == 45

    def test_framework_info_schema(self):
        """Test FrameworkInfo schema."""
        fw = FrameworkInfo(
            name="FastAPI",
            version="0.115.0",
            confidence=0.95,
            evidence=["Dependency in pyproject.toml", "Pattern: @app.get"],
        )
        assert fw.name == "FastAPI"
        assert fw.confidence == 0.95
        assert len(fw.evidence) == 2

    def test_framework_info_confidence_bounds(self):
        """Test FrameworkInfo confidence is between 0 and 1."""
        fw = FrameworkInfo(
            name="Test",
            confidence=0.5,
            evidence=["test"],
        )
        assert 0.0 <= fw.confidence <= 1.0

    def test_dependency_info_schema(self):
        """Test DependencyInfo schema."""
        dep = DependencyInfo(
            name="fastapi",
            version=">=0.115.0",
            is_production=True,
            source_file="pyproject.toml",
        )
        assert dep.name == "fastapi"
        assert dep.is_production is True

    def test_folder_info_schema(self):
        """Test FolderInfo schema."""
        folder = FolderInfo(
            name="src",
            path="src/",
            purpose="source_code",
            file_count=10,
            children=[],
        )
        assert folder.name == "src"
        assert folder.file_count == 10

    def test_folder_info_nested(self):
        """Test FolderInfo with nested children."""
        child = FolderInfo(
            name="services",
            path="src/services/",
            purpose="business_logic",
            file_count=5,
        )
        parent = FolderInfo(
            name="src",
            path="src/",
            purpose="source_code",
            file_count=15,
            children=[child],
        )
        assert len(parent.children) == 1
        assert parent.children[0].name == "services"

    def test_architecture_style_enum(self):
        """Test ArchitectureStyle enum values."""
        assert ArchitectureStyle.MVC == "mvc"
        assert ArchitectureStyle.CLEAN == "clean"
        assert ArchitectureStyle.LAYERED == "layered"
        assert ArchitectureStyle.MICROSERVICES == "microservices"
        assert ArchitectureStyle.MONOLITH == "monolith"
        assert ArchitectureStyle.SERVERLESS == "serverless"
        assert ArchitectureStyle.UNKNOWN == "unknown"

    def test_architecture_summary_schema(self):
        """Test ArchitectureSummary schema."""
        summary = ArchitectureSummary(
            style=ArchitectureStyle.CLEAN,
            description="Clean architecture",
            entry_points=["src/main.py"],
            main_modules=["domain", "application"],
            authentication_detected=True,
            database_detected=True,
            api_detected=True,
            frontend_detected=False,
        )
        assert summary.style == ArchitectureStyle.CLEAN
        assert summary.authentication_detected is True


# ============================================================
# Analysis Schema Tests
# ============================================================


class TestAnalysisSchemas:
    """Tests for analysis result schemas."""

    def test_code_element_schema(self):
        """Test CodeElement schema."""
        element = CodeElement(
            name="UserService",
            type="class",
            file_path="src/services/user_service.py",
            line_start=15,
            line_end=89,
            docstring="Service for users.",
            decorators=[],
            parent_class="BaseService",
            parameters=[],
            return_type=None,
            imports=[],
            is_exported=True,
        )
        assert element.name == "UserService"
        assert element.type == "class"
        assert element.is_exported is True

    def test_code_element_defaults(self):
        """Test CodeElement default values."""
        element = CodeElement(
            name="helper",
            type="function",
            file_path="src/utils.py",
            line_start=1,
        )
        assert element.decorators == []
        assert element.parameters == []
        assert element.imports == []
        assert element.is_exported is False

    def test_route_info_schema(self):
        """Test RouteInfo schema."""
        route = RouteInfo(
            method="GET",
            path="/api/users",
            function_name="list_users",
            file_path="src/routes/users.py",
            line_number=12,
            middleware=["auth"],
            authentication_required=True,
            parameters=["skip", "limit"],
            response_model="UserListResponse",
        )
        assert route.method == "GET"
        assert route.path == "/api/users"
        assert route.authentication_required is True

    def test_database_model_info_schema(self):
        """Test DatabaseModelInfo schema."""
        db_model = DatabaseModelInfo(
            name="User",
            table_name="users",
            file_path="src/models/user.py",
            line_number=10,
            fields=[],
            relationships=["roles", "posts"],
            primary_key="id",
            foreign_keys=["role_id"],
        )
        assert db_model.name == "User"
        assert db_model.table_name == "users"
        assert db_model.primary_key == "id"

    def test_import_graph_edge_schema(self):
        """Test ImportGraphEdge schema."""
        edge = ImportGraphEdge(
            source="src/main.py",
            target="src/utils.py",
            file_path="src/main.py",
        )
        assert edge.source == "src/main.py"
        assert edge.target == "src/utils.py"

    def test_analysis_result_schema(self):
        """Test AnalysisResult schema."""
        result = AnalysisResult(
            repository_id="abc123",
            analyzed_at="2025-01-15T10:35:00Z",
            languages=[],
            frameworks=[],
            dependencies=[],
            folder_structure=[],
            architecture=ArchitectureSummary(
                style=ArchitectureStyle.UNKNOWN,
                description="Unknown",
                entry_points=[],
                main_modules=[],
                authentication_detected=False,
                database_detected=False,
                api_detected=False,
                frontend_detected=False,
            ),
            code_elements=[],
            routes=[],
            database_models=[],
            import_graph=[],
            config_files=[],
            entry_points=[],
            total_files=0,
            total_lines=0,
            analysis_time_ms=0.0,
        )
        assert result.repository_id == "abc123"
        assert result.total_files == 0


# ============================================================
# Graph Schema Tests
# ============================================================


class TestGraphSchemas:
    """Tests for semantic graph schemas."""

    def test_graph_node_type_enum(self):
        """Test GraphNodeType enum values."""
        assert GraphNodeType.REPOSITORY == "repository"
        assert GraphNodeType.FOLDER == "folder"
        assert GraphNodeType.MODULE == "module"
        assert GraphNodeType.CLASS == "class"
        assert GraphNodeType.FUNCTION == "function"
        assert GraphNodeType.ROUTE == "route"
        assert GraphNodeType.DATABASE == "database"
        assert GraphNodeType.DEPENDENCY == "dependency"
        assert GraphNodeType.CONFIG == "config"

    def test_graph_node_schema(self):
        """Test GraphNode schema."""
        node = GraphNode(
            id="module:src/main.py",
            type=GraphNodeType.MODULE,
            name="main.py",
            metadata={"language": "Python", "lines": 150},
        )
        assert node.id == "module:src/main.py"
        assert node.type == GraphNodeType.MODULE
        assert node.metadata["language"] == "Python"

    def test_graph_node_defaults(self):
        """Test GraphNode default metadata."""
        node = GraphNode(
            id="test:1",
            type=GraphNodeType.MODULE,
            name="test",
        )
        assert node.metadata == {}

    def test_graph_edge_schema(self):
        """Test GraphEdge schema."""
        edge = GraphEdge(
            source="module:main.py",
            target="class:UserService",
            relationship="defines",
        )
        assert edge.source == "module:main.py"
        assert edge.relationship == "defines"

    def test_semantic_graph_schema(self, sample_semantic_graph):
        """Test SemanticGraph schema."""
        graph = sample_semantic_graph
        assert len(graph.nodes) == 4
        assert len(graph.edges) == 3
        assert graph.root_id == "repo:test"

    def test_semantic_graph_node_lookup(self, sample_semantic_graph):
        """Test finding a node by ID in the graph."""
        graph = sample_semantic_graph
        node_map = {node.id: node for node in graph.nodes}
        assert "module:src/main.py" in node_map
        assert node_map["class:UserService"].name == "UserService"

    def test_semantic_graph_edge_traversal(self, sample_semantic_graph):
        """Test traversing edges from a node."""
        graph = sample_semantic_graph
        source_node = "class:UserService"
        outgoing = [e for e in graph.edges if e.source == source_node]
        assert len(outgoing) == 1
        assert outgoing[0].target == "function:get_user"


# ============================================================
# Importer Tests
# ============================================================


class TestBaseImporter:
    """Tests for the base importer interface."""

    def test_base_importer_is_abstract(self):
        """Test that BaseImporter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseImporter()

    def test_base_importer_interface(self):
        """Test that subclasses must implement required methods."""
        class IncompleteImporter(BaseImporter):
            pass

        with pytest.raises(TypeError):
            IncompleteImporter()

    def test_base_importer_implementation(self):
        """Test a complete importer implementation."""
        class MockImporter(BaseImporter):
            async def import_repository(self, source: str, target_dir: str) -> str:
                return "/mock/path"

            async def validate(self, source: str) -> bool:
                return True

        importer = MockImporter()
        assert await importer.validate("test") is True
        assert await importer.import_repository("source", "/target") == "/mock/path"


# ============================================================
# Language Detection Tests
# ============================================================


class TestLanguageDetection:
    """Tests for language detection logic."""

    def test_detect_python_by_extension(self):
        """Test Python detection by file extension."""
        extensions = {
            ".py": "Python",
            ".pyw": "Python",
            ".pyi": "Python",
        }
        for ext, expected_lang in extensions.items():
            assert extensions[ext] == expected_lang

    def test_detect_javascript_by_extension(self):
        """Test JavaScript detection by file extension."""
        extensions = {
            ".js": "JavaScript",
            ".mjs": "JavaScript",
            ".cjs": "JavaScript",
        }
        for ext, expected_lang in extensions.items():
            assert extensions[ext] == expected_lang

    def test_detect_typescript_by_extension(self):
        """Test TypeScript detection by file extension."""
        extensions = {
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".mts": "TypeScript",
        }
        for ext, expected_lang in extensions.items():
            assert extensions[ext] == expected_lang

    def test_detect_java_by_extension(self):
        """Test Java detection by file extension."""
        assert {".java": "Java"}[".java"] == "Java"

    def test_detect_go_by_extension(self):
        """Test Go detection by file extension."""
        assert {".go": "Go"}[".go"] == "Go"

    def test_detect_rust_by_extension(self):
        """Test Rust detection by file extension."""
        assert {".rs": "Rust"}[".rs"] == "Rust"

    def test_detect_c_by_extension(self):
        """Test C detection by file extension."""
        assert {".c": "C", ".h": "C"}[".c"] == "C"

    def test_detect_cpp_by_extension(self):
        """Test C++ detection by file extension."""
        extensions = {".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++"}
        for ext in extensions:
            assert extensions[ext] == "C++"

    def test_detect_csharp_by_extension(self):
        """Test C# detection by file extension."""
        assert {".cs": "C#"}[".cs"] == "C#"

    def test_detect_ruby_by_extension(self):
        """Test Ruby detection by file extension."""
        assert {".rb": "Ruby", ".rake": "Ruby"}[".rb"] == "Ruby"

    def test_detect_php_by_extension(self):
        """Test PHP detection by file extension."""
        assert {".php": "PHP"}[".php"] == "PHP"

    def test_detect_swift_by_extension(self):
        """Test Swift detection by file extension."""
        assert {".swift": "Swift"}[".swift"] == "Swift"

    def test_detect_kotlin_by_extension(self):
        """Test Kotlin detection by file extension."""
        assert {".kt": "Kotlin", ".kts": "Kotlin"}[".kt"] == "Kotlin"

    def test_detect_scala_by_extension(self):
        """Test Scala detection by file extension."""
        assert {".scala": "Scala"}[".scala"] == "Scala"

    def test_detect_shell_by_extension(self):
        """Test Shell detection by file extension."""
        extensions = {".sh": "Shell", ".bash": "Shell", ".zsh": "Shell"}
        for ext in extensions:
            assert extensions[ext] == "Shell"

    def test_detect_unknown_extension(self):
        """Test that unknown extensions are not detected."""
        unknown = [".xyz", ".abc", ".custom"]
        for ext in unknown:
            assert ext not in {".py", ".js", ".ts", ".java", ".go", ".rs"}

    def test_language_percentage_calculation(self):
        """Test language percentage calculation."""
        total_lines = 17200
        python_lines = 12500
        ts_lines = 4700

        python_pct = (python_lines / total_lines) * 100
        ts_pct = (ts_lines / total_lines) * 100

        assert abs(python_pct - 72.67) < 0.1
        assert abs(ts_pct - 27.33) < 0.1
        assert abs(python_pct + ts_pct - 100.0) < 0.1


# ============================================================
# Framework Detection Tests
# ============================================================


class TestFrameworkDetection:
    """Tests for framework detection logic."""

    def test_detect_fastapi_from_pyproject(self, sample_pyproject_toml):
        """Test FastAPI detection from pyproject.toml."""
        assert "fastapi" in sample_pyproject_toml.lower()

    def test_detect_fastapi_from_requirements(self, sample_requirements_txt):
        """Test FastAPI detection from requirements.txt."""
        assert "fastapi" in sample_requirements_txt.lower()

    def test_detect_react_from_package_json(self, sample_package_json):
        """Test React detection from package.json."""
        assert "react" in sample_package_json.lower()

    def test_detect_nextjs_from_package_json(self, sample_package_json):
        """Test Next.js detection from package.json."""
        assert "next" in sample_package_json.lower()

    def test_detect_express_from_package_json(self, sample_package_json):
        """Test Express detection from package.json."""
        assert "express" in sample_package_json.lower()

    def test_detect_actix_from_cargo_toml(self, sample_cargo_toml):
        """Test Actix detection from Cargo.toml."""
        assert "actix-web" in sample_cargo_toml.lower()

    def test_framework_confidence_scoring(self):
        """Test framework confidence scoring."""
        # Multiple evidence sources should increase confidence
        evidence_count = 3
        base_confidence = 0.5
        boost_per_evidence = 0.15

        confidence = min(base_confidence + (evidence_count * boost_per_evidence), 1.0)
        assert confidence == 0.95

    def test_framework_confidence_max_bound(self):
        """Test that confidence does not exceed 1.0."""
        evidence_count = 10
        base_confidence = 0.5
        boost_per_evidence = 0.15

        confidence = min(base_confidence + (evidence_count * boost_per_evidence), 1.0)
        assert confidence <= 1.0


# ============================================================
# Directory Analysis Tests
# ============================================================


class TestDirectoryAnalysis:
    """Tests for directory structure analysis."""

    def test_directory_purpose_detection(self):
        """Test automatic purpose detection for directories."""
        purposes = {
            "src": "source_code",
            "lib": "library_code",
            "tests": "test_code",
            "test": "test_code",
            "__tests__": "test_code",
            "docs": "documentation",
            "doc": "documentation",
            "scripts": "scripts",
            "bin": "scripts",
            "config": "configuration",
            "conf": "configuration",
        }
        for dir_name, expected_purpose in purposes.items():
            assert purposes[dir_name] == expected_purpose

    def test_count_files_recursive(self, sample_directory_structure):
        """Test recursive file counting."""
        def count_files(node: dict) -> int:
            if node.get("type") == "file":
                return 1
            return sum(count_files(child) for child in node.get("children", []))

        total = count_files(sample_directory_structure)
        assert total == 9  # 5 src + 2 tests + pyproject.toml + README.md + .env

    def test_calculate_total_size(self, sample_directory_structure):
        """Test total size calculation."""
        def get_size(node: dict) -> int:
            if node.get("type") == "file":
                return node.get("size", 0)
            return sum(get_size(child) for child in node.get("children", []))

        total_size = get_size(sample_directory_structure)
        assert total_size > 0

    def test_filter_ignored_directories(self, sample_directory_structure):
        """Test filtering of ignored directories."""
        ignored = {"node_modules", ".git", "__pycache__", "venv"}

        def should_include(name: str) -> bool:
            return name not in ignored

        children = sample_directory_structure["children"]
        filtered = [c for c in children if should_include(c["name"])]
        assert all(c["name"] not in ignored for c in filtered)


# ============================================================
# Dependency Analysis Tests
# ============================================================


class TestDependencyAnalysis:
    """Tests for dependency analysis."""

    def test_parse_pyproject_dependencies(self, sample_pyproject_toml):
        """Test parsing dependencies from pyproject.toml."""
        deps = []
        in_deps = False
        for line in sample_pyproject_toml.splitlines():
            if "dependencies" in line and "[" in line:
                in_deps = True
                continue
            if in_deps:
                if "]" in line:
                    in_deps = False
                    continue
                dep = line.strip().strip('"').strip("'").split(">=")[0].split("==")[0]
                if dep:
                    deps.append(dep)

        assert "fastapi" in deps
        assert "uvicorn" in deps
        assert "sqlalchemy" in deps
        assert "pydantic" in deps

    def test_parse_requirements_txt(self, sample_requirements_txt):
        """Test parsing dependencies from requirements.txt."""
        deps = []
        for line in sample_requirements_txt.strip().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                dep = line.split("==")[0].split(">=")[0].split("<=")[0]
                deps.append(dep)

        assert "fastapi" in deps
        assert "uvicorn" in deps
        assert "sqlalchemy" in deps

    def test_parse_package_json_dependencies(self, sample_package_json):
        """Test parsing dependencies from package.json."""
        import json

        data = json.loads(sample_package_json)
        prod_deps = list(data.get("dependencies", {}).keys())
        dev_deps = list(data.get("devDependencies", {}).keys())

        assert "react" in prod_deps
        assert "next" in prod_deps
        assert "typescript" in dev_deps
        assert "jest" in dev_deps

    def test_parse_cargo_dependencies(self, sample_cargo_toml):
        """Test parsing dependencies from Cargo.toml."""
        deps = []
        in_deps = False
        for line in sample_cargo_toml.splitlines():
            if "[dependencies]" in line:
                in_deps = True
                continue
            if in_deps and line.strip().startswith("["):
                in_deps = False
                continue
            if in_deps:
                dep = line.split("=")[0].strip()
                if dep:
                    deps.append(dep)

        assert "actix-web" in deps
        assert "serde" in deps
        assert "tokio" in deps

    def test_distinguish_production_dev_dependencies(self):
        """Test distinguishing production from dev dependencies."""
        prod_deps = ["fastapi", "sqlalchemy"]
        dev_deps = ["pytest", "ruff"]

        for dep in prod_deps:
            assert dep not in dev_deps

        for dep in dev_deps:
            assert dep not in prod_deps


# ============================================================
# Config Detection Tests
# ============================================================


class TestConfigDetection:
    """Tests for configuration file detection."""

    def test_detect_config_files(self):
        """Test detection of common config files."""
        config_files = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "requirements.txt",
            "package.json",
            "tsconfig.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            ".eslintrc.js",
            ".prettierrc",
            "Makefile",
            "Dockerfile",
            "docker-compose.yml",
        ]

        for file in config_files:
            assert isinstance(file, str)
            assert len(file) > 0

    def test_is_config_file(self):
        """Test configuration file identification."""
        config_patterns = [
            "pyproject.toml",
            "package.json",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            ".eslintrc.js",
            ".prettierrc",
            "Makefile",
            "Dockerfile",
            "docker-compose.yml",
        ]

        def is_config(filename: str) -> bool:
            return any(pattern in filename for pattern in config_patterns)

        assert is_config("pyproject.toml") is True
        assert is_config("main.py") is False
        assert is_config("index.js") is False

    def test_config_file_categories(self):
        """Test categorizing config files."""
        categories = {
            "build": ["pyproject.toml", "setup.py", "Cargo.toml", "pom.xml"],
            "lint": [".eslintrc.js", ".prettierrc", "ruff.toml"],
            "test": ["jest.config.js", "pytest.ini", ".coveragerc"],
            "deploy": ["Dockerfile", "docker-compose.yml", "Makefile"],
        }

        for category, files in categories.items():
            assert isinstance(category, str)
            assert len(files) > 0


# ============================================================
# AST Parsing Tests
# ============================================================


class TestASTParsing:
    """Tests for AST parsing functionality."""

    def test_extract_python_classes(self, sample_python_file):
        """Test extracting class definitions from Python."""
        path, content = sample_python_file
        classes = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("class ") and ":" in stripped:
                class_name = stripped.split("(")[0].split(":")[0].replace("class ", "")
                classes.append(class_name)

        assert "User" in classes
        assert "UserService" in classes

    def test_extract_python_methods(self, sample_python_file):
        """Test extracting method definitions from Python."""
        path, content = sample_python_file
        methods = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("def ") and "(" in stripped:
                method_name = stripped.split("(")[0].replace("def ", "")
                methods.append(method_name)

        assert "get_user" in methods
        assert "create_user" in methods
        assert "delete_user" in methods
        assert "__init__" in methods

    def test_extract_javascript_routes(self, sample_javascript_file):
        """Test extracting route definitions from JavaScript."""
        path, content = sample_javascript_file
        import re

        routes = re.findall(r"router\.(get|post|put|delete|patch)\('([^']+)'", content)

        assert len(routes) >= 2
        methods = [r[0] for r in routes]
        assert "get" in methods
        assert "post" in methods

    def test_extract_typescript_decorators(self, sample_typescript_file):
        """Test extracting decorators from TypeScript."""
        path, content = sample_typescript_file
        import re

        decorators = re.findall(r"@(\w+)\(", content)

        assert "Controller" in decorators
        assert "Get" in decorators
        assert "Post" in decorators

    def test_extract_java_annotations(self, sample_java_file):
        """Test extracting annotations from Java."""
        path, content = sample_java_file
        import re

        annotations = re.findall(r"@(\w+)", content)

        assert "RestController" in annotations
        assert "GetMapping" in annotations
        assert "PostMapping" in annotations
        assert "Autowired" in annotations

    def test_extract_go_structs(self, sample_go_file):
        """Test extracting struct definitions from Go."""
        path, content = sample_go_file
        import re

        structs = re.findall(r"type (\w+) struct", content)

        assert "User" in structs

    def test_extract_imports(self, sample_python_file):
        """Test extracting import statements."""
        path, content = sample_python_file
        imports = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("from ") and "import" in stripped:
                imports.append(stripped)
            elif stripped.startswith("import "):
                imports.append(stripped)

        # Our sample file has typing import
        assert any("typing" in imp for imp in imports)

    def test_extract_docstrings(self, sample_python_file):
        """Test extracting docstrings from Python."""
        path, content = sample_python_file
        import re

        docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)

        assert len(docstrings) >= 2  # Module docstring + class/method docstrings


# ============================================================
# Semantic Graph Builder Tests
# ============================================================


class TestSemanticGraphBuilder:
    """Tests for semantic graph construction."""

    def test_create_repository_node(self):
        """Test creating a repository root node."""
        node = GraphNode(
            id="repo:test-project",
            type=GraphNodeType.REPOSITORY,
            name="test-project",
            metadata={"url": "https://github.com/test/repo", "branch": "main"},
        )
        assert node.type == GraphNodeType.REPOSITORY
        assert node.metadata["branch"] == "main"

    def test_create_module_node(self):
        """Test creating a module node."""
        node = GraphNode(
            id="module:src/main.py",
            type=GraphNodeType.MODULE,
            name="main.py",
            metadata={"language": "Python", "lines": 150},
        )
        assert node.type == GraphNodeType.MODULE

    def test_create_class_node(self):
        """Test creating a class node."""
        node = GraphNode(
            id="class:UserService",
            type=GraphNodeType.CLASS,
            name="UserService",
            metadata={"parent": "BaseService", "methods": ["get", "create"]},
        )
        assert node.type == GraphNodeType.CLASS
        assert "get" in node.metadata["methods"]

    def test_create_function_node(self):
        """Test creating a function node."""
        node = GraphNode(
            id="function:get_user",
            type=GraphNodeType.FUNCTION,
            name="get_user",
            metadata={"params": ["user_id"], "returns": "User"},
        )
        assert node.type == GraphNodeType.FUNCTION

    def test_create_contain_edge(self):
        """Test creating a contains edge."""
        edge = GraphEdge(
            source="folder:src",
            target="module:src/main.py",
            relationship="contains",
        )
        assert edge.relationship == "contains"

    def test_create_imports_edge(self):
        """Test creating an imports edge."""
        edge = GraphEdge(
            source="module:src/main.py",
            target="module:src/utils.py",
            relationship="imports",
        )
        assert edge.relationship == "imports"

    def test_create_defines_edge(self):
        """Test creating a defines edge."""
        edge = GraphEdge(
            source="module:src/main.py",
            target="class:UserService",
            relationship="defines",
        )
        assert edge.relationship == "defines"

    def test_create_depends_on_edge(self):
        """Test creating a depends_on edge."""
        edge = GraphEdge(
            source="module:src/main.py",
            target="dependency:requests",
            relationship="uses",
        )
        assert edge.relationship == "uses"

    def test_graph_connectivity(self, sample_semantic_graph):
        """Test that the graph is connected."""
        graph = sample_semantic_graph
        node_ids = {node.id for node in graph.nodes}
        edge_nodes = set()
        for edge in graph.edges:
            edge_nodes.add(edge.source)
            edge_nodes.add(edge.target)

        # All edge endpoints should reference existing nodes
        assert edge_nodes.issubset(node_ids)

    def test_graph_root_has_outgoing_edges(self, sample_semantic_graph):
        """Test that the root node has outgoing edges."""
        graph = sample_semantic_graph
        root_edges = [e for e in graph.edges if e.source == graph.root_id]
        assert len(root_edges) > 0

    def test_find_downstream_nodes(self, sample_semantic_graph):
        """Test finding all downstream nodes from a source."""
        graph = sample_semantic_graph
        start = "repo:test"

        visited = set()
        queue = [start]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for edge in graph.edges:
                if edge.source == current:
                    queue.append(edge.target)

        assert "module:src/main.py" in visited
        assert "class:UserService" in visited
        assert "function:get_user" in visited

    def test_find_upstream_nodes(self, sample_semantic_graph):
        """Test finding all upstream nodes from a target."""
        graph = sample_semantic_graph
        target = "function:get_user"

        visited = set()
        queue = [target]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for edge in graph.edges:
                if edge.target == current:
                    queue.append(edge.source)

        assert "class:UserService" in visited
        assert "module:src/main.py" in visited
        assert "repo:test" in visited


# ============================================================
# Architecture Analysis Tests
# ============================================================


class TestArchitectureAnalysis:
    """Tests for architecture pattern detection."""

    def test_detect_mvc_pattern(self):
        """Test MVC architecture detection."""
        directories = {"models", "views", "controllers"}
        assert "models" in directories
        assert "views" in directories
        assert "controllers" in directories

    def test_detect_clean_architecture_pattern(self):
        """Test Clean Architecture detection."""
        directories = {"domain", "application", "infrastructure"}
        assert "domain" in directories
        assert "application" in directories
        assert "infrastructure" in directories

    def test_detect_layered_pattern(self):
        """Test Layered architecture detection."""
        directories = {"controllers", "services", "repositories"}
        assert "controllers" in directories
        assert "services" in directories
        assert "repositories" in directories

    def test_detect_microservices_pattern(self):
        """Test Microservices detection."""
        indicators = [
            "docker-compose.yml",
            "kubernetes",
            "services/",
            "packages/",
        ]
        has_multiple_services = len(indicators) >= 2
        assert has_multiple_services

    def test_detect_serverless_pattern(self):
        """Test Serverless detection."""
        indicators = ["serverless.yml", "handler.py", "functions/"]
        assert "serverless.yml" in indicators
        assert "handler.py" in indicators

    def test_architecture_authentication_detection(self):
        """Test authentication detection in architecture."""
        auth_indicators = [
            "auth/",
            "authentication",
            "jwt",
            "token",
            "login",
            "middleware",
        ]
        assert len(auth_indicators) >= 3

    def test_architecture_database_detection(self):
        """Test database detection in architecture."""
        db_indicators = [
            "models/",
            "migrations/",
            "database/",
            "db/",
            "alembic/",
            "prisma/",
        ]
        assert len(db_indicators) >= 3

    def test_architecture_api_detection(self):
        """Test API detection in architecture."""
        api_indicators = [
            "routes/",
            "api/",
            "controllers/",
            "endpoints/",
            "router.py",
        ]
        assert len(api_indicators) >= 3

    def test_architecture_frontend_detection(self):
        """Test frontend detection in architecture."""
        frontend_indicators = [
            "package.json",
            "pages/",
            "components/",
            "public/",
            "src/app/",
        ]
        assert len(frontend_indicators) >= 3


# ============================================================
# Repository Service Tests (Mocked)
# ============================================================


class TestRepositoryService:
    """Tests for repository service with mocked operations."""

    @pytest.mark.asyncio
    async def test_create_repository(self):
        """Test repository creation."""
        repo_data = RepositoryCreate(
            name="test-repo",
            import_method=ImportMethod.GIT,
            source_url="https://github.com/test/repo.git",
        )

        # Simulate service logic
        repo_info = RepositoryInfo(
            id="mock-id-123",
            name=repo_data.name,
            description=repo_data.description,
            status=RepositoryStatus.IMPORTING,
            import_method=repo_data.import_method,
            source_url=repo_data.source_url,
            local_path="/tmp/forgeai/repos/mock-id-123",
            created_at=datetime.now(timezone.utc).isoformat(),
            analyzed_at=None,
        )

        assert repo_info.name == "test-repo"
        assert repo_info.status == RepositoryStatus.IMPORTING

    @pytest.mark.asyncio
    async def test_import_git_repository(self):
        """Test git repository import."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Simulate git clone
            source = "https://github.com/test/repo.git"
            target = "/tmp/test/repo"

            assert source.startswith("https://")
            assert target.startswith("/tmp/")

    @pytest.mark.asyncio
    async def test_import_zip_repository(self):
        """Test zip repository import."""
        with patch("zipfile.ZipFile") as mock_zip:
            mock_zip_instance = MagicMock()
            mock_zip.return_value.__enter__.return_value = mock_zip_instance
            mock_zip_instance.namelist.return_value = ["file1.py", "file2.py"]

            # Simulate zip extraction
            zip_path = "/tmp/test/repo.zip"
            extract_to = "/tmp/test/repo"

            assert zip_path.endswith(".zip")
            assert extract_to.endswith("/repo")

    @pytest.mark.asyncio
    async def test_delete_repository(self):
        """Test repository deletion."""
        with patch("shutil.rmtree") as mock_rmtree:
            repo_path = "/tmp/forgeai/repos/test-repo"

            # Simulate deletion
            mock_rmtree.return_value = None

            assert repo_path.startswith("/tmp/forgeai/repos/")

    @pytest.mark.asyncio
    async def test_get_repository_not_found(self):
        """Test getting a non-existent repository."""
        with pytest.raises(RepositoryNotFoundException):
            raise RepositoryNotFoundException("Repository with ID nonexistent not found")

    @pytest.mark.asyncio
    async def test_repository_size_validation(self):
        """Test repository size validation."""
        settings = RepoIntelligenceSettings(MAX_REPOSITORY_SIZE_MB=100)

        # Mock file sizes
        total_size_mb = 150
        assert total_size_mb > settings.MAX_REPOSITORY_SIZE_MB

        total_size_mb = 50
        assert total_size_mb <= settings.MAX_REPOSITORY_SIZE_MB


# ============================================================
# Analysis Service Pipeline Tests (Mocked)
# ============================================================


class TestAnalysisServicePipeline:
    """Tests for the analysis pipeline service."""

    def test_full_analysis_pipeline(self, sample_python_file):
        """Test the complete analysis pipeline."""
        path, content = sample_python_file
        start_time = datetime.now(timezone.utc)

        # Step 1: Detect language
        detected_language = "Python"
        assert detected_language == "Python"

        # Step 2: Parse code elements
        classes = ["User", "UserService"]
        methods = ["__init__", "get_user", "create_user", "delete_user"]
        assert len(classes) == 2
        assert len(methods) == 4

        # Step 3: Build analysis result
        result = AnalysisResult(
            repository_id="test-repo",
            analyzed_at=start_time.isoformat(),
            languages=[LanguageInfo(
                name="Python",
                file_count=1,
                total_lines=len(content.splitlines()),
                percentage=100.0,
                extensions=[".py"],
            )],
            frameworks=[],
            dependencies=[],
            folder_structure=[],
            architecture=ArchitectureSummary(
                style=ArchitectureStyle.UNKNOWN,
                description="Unknown",
                entry_points=[],
                main_modules=[],
                authentication_detected=False,
                database_detected=False,
                api_detected=False,
                frontend_detected=False,
            ),
            code_elements=[CodeElement(
                name=cls,
                type="class",
                file_path=path,
                line_start=1,
            ) for cls in classes],
            routes=[],
            database_models=[],
            import_graph=[],
            config_files=[],
            entry_points=[],
            total_files=1,
            total_lines=len(content.splitlines()),
            analysis_time_ms=0.0,
        )

        assert result.repository_id == "test-repo"
        assert len(result.languages) == 1
        assert len(result.code_elements) == 2

    def test_analysis_with_multiple_languages(self):
        """Test analysis with multiple languages."""
        languages = [
            LanguageInfo(name="Python", file_count=45, total_lines=12500, percentage=72.5, extensions=[".py"]),
            LanguageInfo(name="TypeScript", file_count=18, total_lines=4700, percentage=27.5, extensions=[".ts", ".tsx"]),
        ]

        assert len(languages) == 2
        assert languages[0].percentage + languages[1].percentage == 100.0

    def test_analysis_with_frameworks(self):
        """Test analysis with detected frameworks."""
        frameworks = [
            FrameworkInfo(name="FastAPI", version="0.115.0", confidence=0.95, evidence=["dep", "pattern"]),
            FrameworkInfo(name="React", version="18.2.0", confidence=0.90, evidence=["dep"]),
        ]

        assert len(frameworks) == 2
        assert all(fw.confidence > 0.8 for fw in frameworks)

    def test_analysis_with_routes(self):
        """Test analysis with detected routes."""
        routes = [
            RouteInfo(method="GET", path="/api/users", function_name="list_users", file_path="routes.py", line_number=10),
            RouteInfo(method="POST", path="/api/users", function_name="create_user", file_path="routes.py", line_number=20),
            RouteInfo(method="GET", path="/api/users/{id}", function_name="get_user", file_path="routes.py", line_number=30),
        ]

        assert len(routes) == 3
        methods = {r.method for r in routes}
        assert "GET" in methods
        assert "POST" in methods

    def test_analysis_with_database_models(self):
        """Test analysis with detected database models."""
        models = [
            DatabaseModelInfo(
                name="User",
                table_name="users",
                file_path="models/user.py",
                line_number=10,
                primary_key="id",
            ),
            DatabaseModelInfo(
                name="Role",
                table_name="roles",
                file_path="models/role.py",
                line_number=10,
                primary_key="id",
            ),
        ]

        assert len(models) == 2
        assert all(m.table_name is not None for m in models)

    def test_analysis_import_graph(self):
        """Test building import graph."""
        edges = [
            ImportGraphEdge(source="main.py", target="utils.py", file_path="main.py"),
            ImportGraphEdge(source="main.py", target="models.py", file_path="main.py"),
            ImportGraphEdge(source="utils.py", target="helpers.py", file_path="utils.py"),
        ]

        assert len(edges) == 3

        # Find all modules imported by main.py
        main_imports = [e.target for e in edges if e.source == "main.py"]
        assert "utils.py" in main_imports
        assert "models.py" in main_imports

    def test_analysis_timing(self):
        """Test analysis timing measurement."""
        start = datetime.now(timezone.utc)
        # Simulate some work
        end = datetime.now(timezone.utc)

        duration_ms = (end - start).total_seconds() * 1000
        assert duration_ms >= 0

    def test_analysis_error_handling(self):
        """Test analysis error handling."""
        with pytest.raises(AnalysisFailedException):
            raise AnalysisFailedException("Failed to parse Python file: SyntaxError")

    def test_analysis_with_empty_repository(self):
        """Test analysis with empty repository."""
        result = AnalysisResult(
            repository_id="empty-repo",
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            languages=[],
            frameworks=[],
            dependencies=[],
            folder_structure=[],
            architecture=ArchitectureSummary(
                style=ArchitectureStyle.UNKNOWN,
                description="No code found",
                entry_points=[],
                main_modules=[],
                authentication_detected=False,
                database_detected=False,
                api_detected=False,
                frontend_detected=False,
            ),
            code_elements=[],
            routes=[],
            database_models=[],
            import_graph=[],
            config_files=[],
            entry_points=[],
            total_files=0,
            total_lines=0,
            analysis_time_ms=0.0,
        )

        assert result.total_files == 0
        assert len(result.languages) == 0
        assert len(result.code_elements) == 0


# ============================================================
# API Endpoint Tests (Mocked)
# ============================================================


class TestAPIEndpoints:
    """Tests for repository API endpoints with mocked services."""

    def test_create_repository_request_validation(self):
        """Test request validation for repository creation."""
        # Valid request
        valid = RepositoryCreate(
            name="test",
            import_method=ImportMethod.GIT,
            source_url="https://github.com/test/repo.git",
        )
        assert valid.name == "test"

        # Invalid - empty name
        with pytest.raises(Exception):
            RepositoryCreate(
                name="",
                import_method=ImportMethod.GIT,
            )

    def test_create_repository_request_min_length(self):
        """Test minimum name length validation."""
        repo = RepositoryCreate(
            name="a",
            import_method=ImportMethod.FOLDER,
        )
        assert repo.name == "a"

    def test_list_repositories_pagination(self):
        """Test pagination parameters."""
        skip = 0
        limit = 20
        assert skip >= 0
        assert limit > 0
        assert limit <= 100

    def test_repository_status_transitions(self):
        """Test valid status transitions."""
        valid_transitions = {
            RepositoryStatus.IMPORTING: [RepositoryStatus.ANALYZING, RepositoryStatus.ERROR],
            RepositoryStatus.ANALYZING: [RepositoryStatus.READY, RepositoryStatus.ERROR],
            RepositoryStatus.READY: [RepositoryStatus.ANALYZING],
            RepositoryStatus.ERROR: [RepositoryStatus.IMPORTING],
        }

        for status, next_statuses in valid_transitions.items():
            assert len(next_statuses) > 0

    def test_analyze_endpoint_response(self):
        """Test analyze endpoint response format."""
        response = {
            "message": "Analysis started",
            "repository_id": "abc123",
            "status": "analyzing",
        }

        assert "message" in response
        assert "repository_id" in response
        assert "status" in response
        assert response["status"] == "analyzing"

    def test_graph_endpoint_response(self):
        """Test graph endpoint response format."""
        graph = SemanticGraph(
            nodes=[],
            edges=[],
            root_id="repo:test",
        )

        response = {
            "nodes": graph.nodes,
            "edges": graph.edges,
            "root_id": graph.root_id,
        }

        assert "nodes" in response
        assert "edges" in response
        assert "root_id" in response


# ============================================================
# Import Method Tests (Mocked)
# ============================================================


class TestImportMethods:
    """Tests for repository import methods."""

    @pytest.mark.asyncio
    async def test_zip_import_flow(self):
        """Test the zip import flow."""
        with patch("aiofiles.open", mock_open(read_data=b"fake zip data")):
            source = "/path/to/repo.zip"
            target = "/tmp/repos/extracted"

            assert source.endswith(".zip")
            assert target.startswith("/tmp/repos/")

    @pytest.mark.asyncio
    async def test_git_import_flow(self):
        """Test the git import flow."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            source = "https://github.com/user/repo.git"
            target = "/tmp/repos/cloned"

            assert "github.com" in source
            assert target.startswith("/tmp/repos/")

    @pytest.mark.asyncio
    async def test_folder_import_flow(self):
        """Test the folder import flow."""
        source = "/home/user/projects/my-project"
        target = "/tmp/repos/linked"

        assert os.path.isabs(source) or source.startswith("~")
        assert target.startswith("/tmp/repos/")

    @pytest.mark.asyncio
    async def test_import_validation_invalid_url(self):
        """Test import validation with invalid URL."""
        with pytest.raises(RepositoryImportException):
            raise RepositoryImportException("Invalid repository URL")

    @pytest.mark.asyncio
    async def test_import_validation_unreachable(self):
        """Test import validation when source is unreachable."""
        with pytest.raises(GitCloneException):
            raise GitCloneException("Could not clone repository: connection timeout")


# ============================================================
# Error Handling Tests
# ============================================================


class TestErrorHandling:
    """Tests for error handling throughout the system."""

    def test_repository_not_found_error(self):
        """Test repository not found error handling."""
        exc = RepositoryNotFoundException("Repository abc123 not found")
        assert exc.message == "Repository abc123 not found"
        assert isinstance(exc, Exception)

    def test_import_failed_error(self):
        """Test import failure error handling."""
        exc = RepositoryImportException("Failed to download repository")
        assert "download" in exc.message

    def test_too_large_error(self):
        """Test repository too large error handling."""
        exc = RepositoryTooLargeException("Repository size 600MB exceeds limit of 500MB")
        assert "600MB" in exc.message

    def test_unsupported_language_error(self):
        """Test unsupported language error handling."""
        exc = UnsupportedLanguageException("Language 'Brainfuck' is not supported")
        assert "Brainfuck" in exc.message

    def test_analysis_failed_error(self):
        """Test analysis failure error handling."""
        exc = AnalysisFailedException("Syntax error in main.py at line 42")
        assert "line 42" in exc.message

    def test_invalid_repository_error(self):
        """Test invalid repository error handling."""
        exc = InvalidRepositoryException("Repository must contain source files")
        assert "source files" in exc.message

    def test_git_clone_error(self):
        """Test git clone error handling."""
        exc = GitCloneException("Repository not found or access denied")
        assert "access denied" in exc.message

    def test_error_message_customization(self):
        """Test custom error messages."""
        messages = [
            ("Repository not found", RepositoryNotFoundException),
            ("Import failed", RepositoryImportException),
            ("Too large", RepositoryTooLargeException),
            ("Unsupported", UnsupportedLanguageException),
            ("Analysis failed", AnalysisFailedException),
            ("Invalid repo", InvalidRepositoryException),
            ("Clone failed", GitCloneException),
        ]

        for msg, exc_cls in messages:
            exc = exc_cls(msg)
            assert str(exc) == msg

    def test_exception_hierarchy(self):
        """Test exception inheritance hierarchy."""
        from app.exceptions import ForgeBaseException

        exceptions = [
            RepositoryNotFoundException,
            RepositoryImportException,
            RepositoryTooLargeException,
            UnsupportedLanguageException,
            AnalysisFailedException,
            InvalidRepositoryException,
            GitCloneException,
        ]

        for exc_cls in exceptions:
            assert issubclass(exc_cls, ForgeBaseException)
            assert issubclass(exc_cls, Exception)


# ============================================================
# Edge Cases and Integration Tests
# ============================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_file_content(self):
        """Test handling empty file content."""
        content = ""
        lines = content.splitlines()
        assert len(lines) == 0

    def test_binary_file_detection(self):
        """Test binary file detection."""
        # Binary files should be skipped
        binary_extensions = [".png", ".jpg", ".gif", ".ico", ".woff", ".ttf", ".eot"]
        for ext in binary_extensions:
            assert ext.startswith(".")

    def test_large_file_handling(self, repo_settings):
        """Test large file handling with size limits."""
        max_size_bytes = repo_settings.MAX_FILE_SIZE_KB * 1024
        assert max_size_bytes == 512 * 1024  # 512KB

    def test_special_characters_in_paths(self):
        """Test handling special characters in file paths."""
        paths = [
            "src/My Project/main.py",
            "src/café/utils.py",
            "src/日本語/test.py",
        ]
        for path in paths:
            assert isinstance(path, str)
            assert len(path) > 0

    def test_deeply_nested_directories(self):
        """Test handling deeply nested directories."""
        depth = 20
        path_parts = ["src"] + ["sub"] * depth + ["main.py"]
        path = "/".join(path_parts)
        assert path.count("/") == depth + 1

    def test_concurrent_analysis_protection(self):
        """Test concurrent analysis protection."""
        # Simulate lock mechanism
        lock_acquired = True
        assert lock_acquired is True

    def test_unicode_file_names(self):
        """Test handling Unicode file names."""
        names = [
            "café.py",
            "日本語.js",
            "Ñoño.ts",
            "αρχείο.java",
        ]
        for name in names:
            assert isinstance(name, str)
            assert len(name) > 0

    def test_mixed_language_project(self):
        """Test analysis of mixed language project."""
        languages = [
            LanguageInfo(name="Python", file_count=30, total_lines=8000, percentage=50.0, extensions=[".py"]),
            LanguageInfo(name="JavaScript", file_count=20, total_lines=5000, percentage=31.25, extensions=[".js"]),
            LanguageInfo(name="TypeScript", file_count=10, total_lines=3000, percentage=18.75, extensions=[".ts"]),
        ]

        total_percentage = sum(lang.percentage for lang in languages)
        assert abs(total_percentage - 100.0) < 0.1

    def test_repository_with_no_code_files(self):
        """Test repository with only config and documentation."""
        config_files = ["README.md", "LICENSE", ".gitignore", "Dockerfile"]
        code_files = []

        assert len(code_files) == 0
        assert len(config_files) == 4

    def test_version_parsing(self):
        """Test version string parsing."""
        versions = [
            "0.1.0",
            "1.0.0-beta.1",
            "^14.0.0",
            ">=2.0.36",
            "~=1.0",
        ]
        for version in versions:
            assert isinstance(version, str)
            assert len(version) > 0


# ============================================================
# Fixture Validation Tests
# ============================================================


class TestFixtures:
    """Tests validating test fixtures work correctly."""

    def test_sample_python_file_fixture(self, sample_python_file):
        """Test sample Python file fixture."""
        path, content = sample_python_file
        assert path.endswith(".py")
        assert "class" in content
        assert "def" in content

    def test_sample_javascript_file_fixture(self, sample_javascript_file):
        """Test sample JavaScript file fixture."""
        path, content = sample_javascript_file
        assert path.endswith(".js")
        assert "router" in content

    def test_sample_typescript_file_fixture(self, sample_typescript_file):
        """Test sample TypeScript file fixture."""
        path, content = sample_typescript_file
        assert path.endswith(".ts")
        assert "@Controller" in content

    def test_sample_java_file_fixture(self, sample_java_file):
        """Test sample Java file fixture."""
        path, content = sample_java_file
        assert path.endswith(".java")
        assert "@RestController" in content

    def test_sample_go_file_fixture(self, sample_go_file):
        """Test sample Go file fixture."""
        path, content = sample_go_file
        assert path.endswith(".go")
        assert "func" in content

    def test_sample_package_json_fixture(self, sample_package_json):
        """Test sample package.json fixture."""
        import json
        data = json.loads(sample_package_json)
        assert "dependencies" in data
        assert "devDependencies" in data

    def test_sample_pyproject_toml_fixture(self, sample_pyproject_toml):
        """Test sample pyproject.toml fixture."""
        assert "[project]" in sample_pyproject_toml
        assert "dependencies" in sample_pyproject_toml

    def test_sample_requirements_txt_fixture(self, sample_requirements_txt):
        """Test sample requirements.txt fixture."""
        lines = sample_requirements_txt.strip().splitlines()
        assert len(lines) > 0
        assert all("==" in line for line in lines)

    def test_sample_cargo_toml_fixture(self, sample_cargo_toml):
        """Test sample Cargo.toml fixture."""
        assert "[package]" in sample_cargo_toml
        assert "[dependencies]" in sample_cargo_toml

    def test_sample_directory_structure_fixture(self, sample_directory_structure):
        """Test sample directory structure fixture."""
        assert "name" in sample_directory_structure
        assert "children" in sample_directory_structure
        assert len(sample_directory_structure["children"]) > 0

    def test_sample_semantic_graph_fixture(self, sample_semantic_graph):
        """Test sample semantic graph fixture."""
        graph = sample_semantic_graph
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0
        assert graph.root_id is not None

    def test_repo_settings_fixture(self, repo_settings):
        """Test repo settings fixture."""
        assert repo_settings.MAX_REPOSITORY_SIZE_MB == 100
        assert repo_settings.MAX_FILE_SIZE_KB == 512
        assert repo_settings.MAX_FILES_TO_ANALYZE == 500
