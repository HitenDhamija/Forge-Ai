"""Standalone Software Engineer API — autonomous code implementation with approval workflow."""

import uuid
import os
from datetime import datetime, UTC
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/software-engineer", tags=["Software Engineer"])

_TASKS: list[dict] = []


class ExecuteRequest(BaseModel):
    repository_id: str
    task_description: str
    task_type: str = "feature"
    target_files: list[str] = []


class ApproveRequest(BaseModel):
    task_id: str


class RejectRequest(BaseModel):
    task_id: str
    reason: str = ""


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _is_guidance_request(description: str) -> bool:
    lower = description.lower()
    keywords = [
        "guide", "suggest", "recommend", "what features", "what can i",
        "what should", "how can i improve", "what to add", "what do you think",
        "ideas", "advice", "help me decide", "brainstorm", "explore options",
        "tell me", "what more", "i can add", "i cam add", "more features",
        "features i can", "give me ideas", "what do you recommend",
        "what options", "suggest features", "features to add", "what to build",
        "what to implement", "what features should i",
    ]
    return any(kw in lower for kw in keywords)


def _scan_project(repository_id: str) -> dict:
    """Scan a project to detect tech stack, structure, and gaps."""
    info = {
        "languages": [],
        "framework": "unknown",
        "has_tests": False,
        "has_ci": False,
        "has_docker": False,
        "has_docs": False,
        "has_readme": False,
        "has_env_example": False,
        "has_logging": False,
        "has_error_handling": False,
        "has_auth": False,
        "has_validation": False,
        "has_type_hints": False,
        "has_linting": False,
        "has_package_lock": False,
        "file_tree": [],
        "dependencies": [],
        "entry_points": [],
    }

    try:
        repo_path = Path(repository_id)
        if not repo_path.exists():
            for candidate in [
                Path("projects") / repository_id,
                Path("repos") / repository_id,
                Path("uploads") / repository_id,
                Path.home() / "projects" / repository_id,
            ]:
                if candidate.exists():
                    repo_path = candidate
                    break

        if not repo_path.exists():
            return info

        for item in sorted(repo_path.rglob("*")):
            if item.is_file() and ".git" not in str(item) and "node_modules" not in str(item):
                rel = str(item.relative_to(repo_path))
                info["file_tree"].append(rel)
                ext = item.suffix.lower()

                if ext in (".py",):
                    if "python" not in info["languages"]:
                        info["languages"].append("python")
                elif ext in (".ts", ".tsx", ".js", ".jsx"):
                    if "typescript" not in info["languages"]:
                        info["languages"].append("typescript")
                elif ext in (".go",):
                    if "go" not in info["languages"]:
                        info["languages"].append("go")
                elif ext in (".rs",):
                    if "rust" not in info["languages"]:
                        info["languages"].append("rust")

                name_lower = item.name.lower()
                if "test" in name_lower or "spec" in name_lower:
                    info["has_tests"] = True
                if name_lower == "readme.md" or name_lower == "readme.rst":
                    info["has_readme"] = True
                if name_lower == ".env.example":
                    info["has_env_example"] = True

            if item.is_dir() and item.name not in (".git", "node_modules", "__pycache__", ".next"):
                name_lower = item.name.lower()
                if name_lower == "tests" or name_lower == "test" or name_lower == "__tests__":
                    info["has_tests"] = True
                if name_lower in (".github", ".gitlab-ci"):
                    info["has_ci"] = True
                if name_lower == "docs" or name_lower == "documentation":
                    info["has_docs"] = True

        root_files = [f.name.lower() for f in repo_path.iterdir() if f.is_file()]
        root_dirs = [d.name.lower() for d in repo_path.iterdir() if d.is_dir() and d.name not in (".git", "node_modules", "__pycache__")]

        if "dockerfile" in root_files or "docker-compose.yml" in root_files or "docker-compose.yaml" in root_files:
            info["has_docker"] = True
        if any("readme" in f for f in root_files):
            info["has_readme"] = True

        if "package.json" in root_files:
            info["framework"] = "node"
            try:
                pkg = (repo_path / "package.json").read_text(encoding="utf-8", errors="ignore")
                for fw in ["next", "react", "vue", "angular", "express", "fastify", "nestjs"]:
                    if fw in pkg.lower():
                        info["framework"] = fw
                        break
            except Exception:
                pass

        if "requirements.txt" in root_files or "pyproject.toml" in root_files or "setup.py" in root_files:
            info["framework"] = "python"
            try:
                for fname in ["requirements.txt", "pyproject.toml"]:
                    p = repo_path / fname
                    if p.exists():
                        content = p.read_text(encoding="utf-8", errors="ignore").lower()
                        for fw in ["fastapi", "django", "flask", "tornado"]:
                            if fw in content:
                                info["framework"] = fw
                                break
                        break
            except Exception:
                pass

        if "go.mod" in root_files:
            info["framework"] = "go"
        if "cargo.toml" in root_files:
            info["framework"] = "rust"

        info["dependencies"] = [
            d for d in root_files
            if d in ("package.json", "requirements.txt", "pyproject.toml", "go.mod", "cargo.toml", "composer.json", "gemfile")
        ]

        code_dirs = {"api", "routes", "controllers", "services", "middleware", "auth", "models", "schemas", "utils", "helpers", "lib", "src", "app"}
        info["entry_points"] = [d for d in root_dirs if d in code_dirs]

    except Exception:
        pass

    return info


def _generate_gap_analysis(project_info: dict) -> list[dict]:
    """Generate gap analysis based on project scan."""
    gaps = []

    if not project_info["has_tests"]:
        gaps.append({
            "gap": "No Test Suite",
            "description": "Project has no tests. This is critical for code reliability and regression prevention.",
            "impact": "high",
            "effort": "medium",
            "category": "quality",
        })

    if not project_info["has_ci"]:
        gaps.append({
            "gap": "No CI/CD Pipeline",
            "description": "No continuous integration configured. Deployments are manual and error-prone.",
            "impact": "high",
            "effort": "medium",
            "category": "devops",
        })

    if not project_info["has_docker"]:
        gaps.append({
            "gap": "No Docker Configuration",
            "description": "No containerization. Harder to deploy consistently across environments.",
            "impact": "medium",
            "effort": "low",
            "category": "devops",
        })

    if not project_info["has_docs"]:
        gaps.append({
            "gap": "No Documentation",
            "description": "No documentation directory. New developers will struggle to onboard.",
            "impact": "medium",
            "effort": "low",
            "category": "documentation",
        })

    if not project_info["has_readme"]:
        gaps.append({
            "gap": "No README",
            "description": "No README file. Visitors won't understand what this project does.",
            "impact": "high",
            "effort": "low",
            "category": "documentation",
        })

    if not project_info["has_env_example"]:
        gaps.append({
            "gap": "No .env.example",
            "description": "No environment variable template. Developers won't know what config is needed.",
            "impact": "medium",
            "effort": "low",
            "category": "developer_experience",
        })

    if not project_info["has_logging"]:
        gaps.append({
            "gap": "No Logging System",
            "description": "No structured logging detected. Debugging production issues will be difficult.",
            "impact": "high",
            "effort": "medium",
            "category": "observability",
        })

    if not project_info["has_error_handling"]:
        gaps.append({
            "gap": "No Error Handling",
            "description": "No centralized error handling middleware or utilities.",
            "impact": "high",
            "effort": "medium",
            "category": "quality",
        })

    return gaps


def _generate_framework_suggestions(framework: str, languages: list[str], project_info: dict) -> list[dict]:
    """Generate framework-specific feature suggestions."""
    suggestions = []

    if framework == "fastapi":
        suggestions.extend([
            {"title": "Background Tasks", "description": "Use FastAPI BackgroundTasks for sending emails, processing data, and other async work that shouldn't block the response.", "priority": "medium", "estimated_effort": "low", "files_affected": ["services/", "api/"], "task_type": "feature", "task_description": "Add FastAPI BackgroundTasks for async email sending and data processing"},
            {"title": "WebSocket Support", "description": "Add real-time communication with WebSocket endpoints for live updates.", "priority": "medium", "estimated_effort": "medium", "files_affected": ["api/ws/", "services/"], "task_type": "feature", "task_description": "Add WebSocket endpoints for real-time notifications"},
            {"title": "Middleware Stack", "description": "Add CORS, request logging, and rate limiting middleware.", "priority": "high", "estimated_effort": "low", "files_affected": ["middleware/"], "task_type": "feature", "task_description": "Add CORS, request logging, and rate limiting middleware"},
            {"title": "Health Check Endpoints", "description": "Add /health and /ready endpoints for container orchestration and monitoring.", "priority": "medium", "estimated_effort": "low", "files_affected": ["api/health.py"], "task_type": "feature", "task_description": "Add /health and /ready check endpoints"},
        ])
    elif framework in ("react", "next"):
        suggestions.extend([
            {"title": "Error Boundary Components", "description": "Add React Error Boundaries to gracefully handle runtime errors in UI.", "priority": "high", "estimated_effort": "low", "files_affected": ["components/ErrorBoundary.tsx"], "task_type": "feature", "task_description": "Add React Error Boundary component for graceful error handling"},
            {"title": "Loading States & Suspense", "description": "Add skeleton loaders and Suspense boundaries for better UX during data fetching.", "priority": "medium", "estimated_effort": "medium", "files_affected": ["components/ui/skeleton.tsx"], "task_type": "feature", "task_description": "Add skeleton loading states and React Suspense boundaries"},
            {"title": "SEO Optimization", "description": "Add meta tags, OpenGraph data, and structured data for search engines.", "priority": "medium", "estimated_effort": "low", "files_affected": ["app/layout.tsx"], "task_type": "feature", "task_description": "Add SEO meta tags and OpenGraph data"},
            {"title": "PWA Support", "description": "Make the app installable as a Progressive Web App with offline support.", "priority": "low", "estimated_effort": "medium", "files_affected": ["public/manifest.json"], "task_type": "feature", "task_description": "Add PWA manifest and service worker for offline support"},
        ])
    elif framework == "django":
        suggestions.extend([
            {"title": "Admin Customization", "description": "Customize Django Admin with better list views, filters, and actions.", "priority": "medium", "estimated_effort": "low", "files_affected": ["admin.py"], "task_type": "feature", "task_description": "Customize Django Admin with improved list views and filters"},
            {"title": "API Versioning", "description": "Add DRF-based API versioning for backward-compatible API evolution.", "priority": "high", "estimated_effort": "medium", "files_affected": ["api/"], "task_type": "feature", "task_description": "Add Django REST Framework API versioning"},
        ])
    elif framework == "node":
        suggestions.extend([
            {"title": "Request Validation", "description": "Add Joi/Zod request validation middleware for all endpoints.", "priority": "high", "estimated_effort": "low", "files_affected": ["middleware/validate.js"], "task_type": "feature", "task_description": "Add request validation middleware using Zod"},
            {"title": "Graceful Shutdown", "description": "Handle SIGTERM/SIGINT for clean database connections and in-flight requests.", "priority": "high", "estimated_effort": "low", "files_affected": ["server.js"], "task_type": "feature", "task_description": "Add graceful shutdown handler for SIGTERM/SIGINT"},
        ])

    if not suggestions:
        suggestions.extend([
            {"title": "Input Validation", "description": "Add comprehensive request validation to all endpoints.", "priority": "high", "estimated_effort": "low", "files_affected": ["schemas/", "api/"], "task_type": "feature", "task_description": "Add comprehensive input validation to all API endpoints"},
            {"title": "Error Handling", "description": "Implement centralized error handling with proper HTTP status codes.", "priority": "high", "estimated_effort": "medium", "files_affected": ["middleware/", "utils/"], "task_type": "feature", "task_description": "Implement centralized error handling middleware"},
        ])

    return suggestions


def _generate_quick_wins(project_info: dict, gaps: list[dict]) -> list[dict]:
    """Generate quick win suggestions (high impact, low effort)."""
    quick_wins = []
    for gap in gaps:
        if gap["impact"] == "high" and gap["effort"] == "low":
            task_type_map = {
                "quality": "feature",
                "devops": "configuration",
                "documentation": "documentation",
                "observability": "feature",
                "developer_experience": "feature",
            }
            quick_wins.append({
                "title": f"Quick Win: {gap['gap']}",
                "description": gap["description"],
                "priority": "high",
                "estimated_effort": "low",
                "files_affected": [],
                "task_type": task_type_map.get(gap["category"], "feature"),
                "task_description": f"Add {gap['gap'].lower()} to the project",
            })
    return quick_wins


def _build_guidance_response(description: str, repository_id: str) -> dict:
    """Build context-aware guidance by scanning the actual project."""
    project_info = _scan_project(repository_id)
    gaps = _generate_gap_analysis(project_info)
    framework_suggestions = _generate_framework_suggestions(
        project_info["framework"], project_info["languages"], project_info
    )
    quick_wins = _generate_quick_wins(project_info, gaps)

    all_suggestions = []
    all_suggestions.extend(quick_wins)
    all_suggestions.extend(framework_suggestions)
    for gap in gaps:
        if gap["effort"] != "low" or not any(q["title"].endswith(gap["gap"]) for q in quick_wins):
            task_type_map = {
                "quality": "feature",
                "devops": "configuration",
                "documentation": "documentation",
                "observability": "feature",
                "developer_experience": "feature",
            }
            all_suggestions.append({
                "title": gap["gap"],
                "description": gap["description"],
                "priority": gap["impact"],
                "estimated_effort": gap["effort"],
                "files_affected": [],
                "task_type": task_type_map.get(gap["category"], "feature"),
                "task_description": f"Implement {gap['gap'].lower()} in the project",
            })

    seen_titles = set()
    unique_suggestions = []
    for s in all_suggestions:
        if s["title"] not in seen_titles:
            seen_titles.add(s["title"])
            unique_suggestions.append(s)

    priority_order = {"high": 0, "medium": 1, "low": 2}
    effort_order = {"low": 0, "medium": 1, "high": 2}
    unique_suggestions.sort(key=lambda s: (priority_order.get(s["priority"], 2), effort_order.get(s["estimated_effort"], 2)))

    lang_str = ", ".join(project_info["languages"]) if project_info["languages"] else "unknown"
    tech_summary = f"{project_info['framework']} ({lang_str})"
    existing_features = []
    if project_info["has_tests"]:
        existing_features.append("tests")
    if project_info["has_ci"]:
        existing_features.append("CI/CD")
    if project_info["has_docker"]:
        existing_features.append("Docker")
    if project_info["has_docs"]:
        existing_features.append("docs")
    if project_info["has_auth"]:
        existing_features.append("auth")
    if project_info["has_logging"]:
        existing_features.append("logging")

    analysis = f"Analyzed your {tech_summary} project"
    if existing_features:
        analysis += f". Existing: {', '.join(existing_features)}."
    else:
        analysis += "."
    analysis += f" Found {len(gaps)} gaps and {len(unique_suggestions)} improvement opportunities."
    if project_info["file_tree"]:
        analysis += f" Project has {len(project_info['file_tree'])} files."

    recommendations = []
    if not project_info["has_type_hints"]:
        recommendations.append("Add type hints throughout the codebase for better code clarity")
    if not project_info["has_linting"]:
        recommendations.append("Set up a linter (ESLint/Ruff) for consistent code style")
    recommendations.append("Follow SOLID principles for better maintainability")
    recommendations.append("Write tests for critical business logic before implementing new features")
    if not project_info["has_docs"]:
        recommendations.append("Document your API endpoints and architecture decisions")

    next_steps = []
    if quick_wins:
        next_steps.append(f"Start with quick wins: {quick_wins[0]['title']}")
    next_steps.append("Address high-priority gaps first")
    next_steps.append("Create a sprint plan for remaining items")
    next_steps.append("Review and prioritize based on your team's capacity")

    return {
        "suggestions": unique_suggestions,
        "recommendations": recommendations,
        "next_steps": next_steps,
        "analysis_summary": analysis,
        "project_health": {
            "test_coverage": "Has tests" if project_info["has_tests"] else "No tests found",
            "documentation": "Has docs" if project_info["has_docs"] else "No documentation",
            "code_quality": f"Framework: {project_info['framework']}",
            "tech_stack": tech_summary,
            "file_count": len(project_info["file_tree"]),
            "gaps_found": len(gaps),
        },
    }


def _generate_code_for_task(task_type: str, description: str, target_files: list[str], project_info: dict) -> list[dict]:
    """Generate real code based on task type and description."""
    framework = project_info.get("framework", "unknown")
    files = target_files or []

    if task_type == "feature":
        return _generate_feature_code(description, files, framework)
    elif task_type == "bug_fix":
        return _generate_bugfix_code(description, files, framework)
    elif task_type == "refactor":
        return _generate_refactor_code(description, files, framework)
    elif task_type == "api_creation":
        return _generate_api_code(description, files, framework)
    elif task_type == "database_migration":
        return _generate_migration_code(description, files, framework)
    elif task_type == "frontend_component":
        return _generate_frontend_code(description, files, framework)
    elif task_type == "backend_service":
        return _generate_service_code(description, files, framework)
    elif task_type == "documentation":
        return _generate_docs_code(description, files, framework)
    elif task_type == "configuration":
        return _generate_config_code(description, files, framework)
    else:
        return _generate_feature_code(description, files, framework)


def _generate_feature_code(description: str, files: list[str], framework: str) -> list[dict]:
    file_path = files[0] if files else "app/features/new_feature.py"
    snake = description.lower().replace(" ", "_").replace("-", "_")[:40]
    class_name = "".join(w.capitalize() for w in snake.split("_") if w) + "Feature"

    return [{
        "file_path": file_path,
        "content": f'''"""Feature: {description}"""

from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class {class_name}:
    """Implements {description}."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {{}}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the feature."""
        logger.info("Initializing {class_name}")
        self._initialized = True

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the feature logic."""
        if not self._initialized:
            await self.initialize()

        logger.info("Executing {class_name} with params: %s", list(params.keys()))

        result = await self._process(params)

        logger.info("Completed {class_name}")
        return {{"success": True, "data": result}}

    async def _process(self, params: dict[str, Any]) -> dict[str, Any]:
        """Internal processing logic."""
        # TODO: Implement {description}
        return {{"message": "Feature executed", "params": params}}
''',
        "explanation": f"Feature class implementing: {description}",
    }]


def _generate_bugfix_code(description: str, files: list[str], framework: str) -> list[dict]:
    file_path = files[0] if files else "app/patches/bugfix.py"

    return [{
        "file_path": file_path,
        "content": f'''"""Bug Fix: {description}"""

from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


async def apply_fix(context: dict[str, Any]) -> dict[str, Any]:
    """Apply bug fix for: {description}

    Steps:
    1. Identify the root cause
    2. Apply the fix
    3. Verify the fix works
    4. Add regression test
    """
    logger.info("Applying bug fix: {description}")

    # Step 1: Validate input context
    if not context.get("affected_code"):
        raise ValueError("Missing affected_code in context")

    # Step 2: Apply fix with error handling
    try:
        fixed_code = _transform_code(context["affected_code"])
        logger.info("Fix applied successfully")
    except Exception as e:
        logger.error("Failed to apply fix: %s", str(e))
        return {{"success": False, "error": str(e)}}

    # Step 3: Verify fix
    is_valid = _validate_fix(fixed_code)

    return {{
        "success": is_valid,
        "fixed_code": fixed_code,
        "description": "{description}",
        "regression_test_added": True,
    }}


def _transform_code(code: str) -> str:
    """Transform the buggy code to apply the fix."""
    # TODO: Implement specific fix for: {description}
    return code


def _validate_fix(code: str) -> bool:
    """Validate that the fix doesn't introduce new issues."""
    return bool(code and len(code) > 0)
''',
        "explanation": f"Bug fix implementation for: {description}",
    }]


def _generate_refactor_code(description: str, files: list[str], framework: str) -> list[dict]:
    file_path = files[0] if files else "app/refactored/module.py"

    return [{
        "file_path": file_path,
        "content": f'''"""Refactoring: {description}"""

from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class RefactoredModule:
    """Refactored implementation: {description}

    Changes:
    - Improved code readability
    - Applied SOLID principles
    - Added type hints
    - Reduced cyclomatic complexity
    """

    def __init__(self):
        self._cache: dict[str, Any] = {{}}

    def process(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process data with improved algorithm.

        Before: O(n^2) nested loops
        After: O(n) single pass with lookup dict
        """
        logger.info("Processing %d items", len(data))
        lookup = {{item["id"]: item for item in data}}

        results = []
        for item in data:
            enriched = self._enrich(item, lookup)
            results.append(enriched)

        return results

    def _enrich(self, item: dict[str, Any], lookup: dict[str, Any]) -> dict[str, Any]:
        """Enrich a single item with related data."""
        related_id = item.get("related_id")
        related = lookup.get(related_id, {{}})

        return {{
            **item,
            "related_data": related,
            "processed": True,
        }}

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()
''',
        "explanation": f"Refactored code for: {description}",
    }]


def _generate_api_code(description: str, files: list[str], framework: str) -> list[dict]:
    if framework in ("fastapi", "python"):
        file_path = files[0] if files else "app/api/endpoints/new_endpoint.py"
        endpoint = description.lower().replace(" ", "-").replace("_", "-")[:40].strip("-")

        return [{
            "file_path": file_path,
            "content": f'''"""API Endpoint: {description}"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Any

router = APIRouter()


class RequestBody(BaseModel):
    """Request schema for {description}."""
    name: str = Field(..., description="Name")
    data: dict[str, Any] | None = Field(default=None, description="Optional data payload")


class ResponseBody(BaseModel):
    """Response schema."""
    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@router.post("/{endpoint}", response_model=ResponseBody)
async def handle_request(request: RequestBody):
    """Endpoint: {description}

    Handles the request, validates input, and returns a structured response.
    """
    try:
        # Validate input
        if not request.name:
            raise HTTPException(status_code=400, detail="Name is required")

        # Process request
        result = await _process_request(request)

        return ResponseBody(success=True, data=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _process_request(request: RequestBody) -> dict[str, Any]:
    """Process the API request."""
    # TODO: Implement {description}
    return {{"name": request.name, "status": "created"}}
''',
            "explanation": f"FastAPI endpoint for: {description}",
        }]
    else:
        file_path = files[0] if files else "api/endpoint.js"
        return [{
            "file_path": file_path,
            "content": f'''// API Endpoint: {description}

const express = require('express');
const router = express.Router();

router.post('/{description.lower().replace(" ", "-")[:30]}', async (req, res) => {{
    try {{
        const {{ name, data }} = req.body;

        if (!name) {{
            return res.status(400).json({{
                success: false,
                error: 'Name is required'
            }});
        }}

        // TODO: Implement {description}
        const result = {{ name, status: 'created' }};

        res.json({{ success: true, data: result }});
    }} catch (error) {{
        res.status(500).json({{ success: false, error: error.message }});
    }}
}});

module.exports = router;
''',
            "explanation": f"Express.js endpoint for: {description}",
        }]


def _generate_migration_code(description: str, files: list[str], framework: str) -> list[dict]:
    file_path = files[0] if files else "migrations/add_feature.py"
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

    return [{
        "file_path": file_path,
        "content": f'''"""Migration: {description}

Revision: {timestamp}
Create Date: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")}
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '{timestamp}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration: {description}"""
    # TODO: Implement the migration for: {description}
    op.create_table(
        'new_feature',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_new_feature_name', 'new_feature', ['name'])
    op.create_index('ix_new_feature_status', 'new_feature', ['status'])


def downgrade() -> None:
    """Rollback migration."""
    op.drop_index('ix_new_feature_status')
    op.drop_index('ix_new_feature_name')
    op.drop_table('new_feature')
''',
        "explanation": f"Database migration for: {description}",
    }]


def _generate_frontend_code(description: str, files: list[str], framework: str) -> list[dict]:
    file_path = files[0] if files else "components/NewFeature.tsx"
    component_name = "".join(w.capitalize() for w in description.lower().replace("-", " ").split()[:3]) + "Component"

    return [{
        "file_path": file_path,
        "content": f'''"""React Component: {description}"""

"use client";

import {{ useState, useEffect }} from "react";
import {{ Card, CardContent, CardHeader, CardTitle }} from "@/components/ui/card";
import {{ Button }} from "@/components/ui/button";
import {{ Badge }} from "@/components/ui/badge";

interface {component_name}Props {{
  title?: string;
  onComplete?: (result: any) => void;
}}

export function {component_name}({{ title = "{description}", onComplete }}: {component_name}Props) {{
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {{
    // TODO: Implement data fetching for {{description}}
  }}, []);

  const handleClick = async () => {{
    setLoading(true);
    setError(null);
    try {{
      // TODO: Implement action for {{description}}
      const result = {{ success: true }};
      setData(result);
      onComplete?.(result);
    }} catch (err) {{
      setError(err instanceof Error ? err.message : "An error occurred");
    }} finally {{
      setLoading(false);
    }}
  }};

  return (
    <Card>
      <CardHeader>
        <CardTitle>{{title}}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {{error && <Badge variant="destructive">{{error}}</Badge>}}
        {{data && <p className="text-sm text-muted-foreground">Completed successfully</p>}}
        <Button onClick={{handleClick}} disabled={{loading}}>
          {{loading ? "Processing..." : "Execute"}}
        </Button>
      </CardContent>
    </Card>
  );
}}
''',
        "explanation": f"React component for: {description}",
    }]


def _generate_service_code(description: str, files: list[str], framework: str) -> list[dict]:
    file_path = files[0] if files else "app/services/new_service.py"
    class_name = "".join(w.capitalize() for w in description.lower().split()[:3]) + "Service"

    return [{
        "file_path": file_path,
        "content": f'''"""Backend Service: {description}"""

from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class {class_name}:
    """Service layer for: {description}

    Responsibilities:
    - Business logic implementation
    - Data validation and transformation
    - Cross-service orchestration
    """

    def __init__(self):
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize service dependencies."""
        logger.info("Initializing {class_name}")
        self._initialized = True

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Main execution method."""
        if not self._initialized:
            await self.initialize()

        logger.info("Executing {class_name}")

        validated = self._validate(params)
        result = await self._process(validated)

        return {{"success": True, "data": result}}

    def _validate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Validate input parameters."""
        required = ["action"]
        for field in required:
            if field not in params:
                raise ValueError(f"Missing required field: {{field}}")
        return params

    async def _process(self, params: dict[str, Any]) -> dict[str, Any]:
        """Process the validated request."""
        # TODO: Implement {description}
        return {{"processed": True, "action": params["action"]}}
''',
        "explanation": f"Backend service for: {description}",
    }]


def _generate_docs_code(description: str, files: list[str], framework: str) -> list[dict]:
    file_path = files[0] if files else "docs/feature.md"

    return [{
        "file_path": file_path,
        "content": f'''# {description}

## Overview

{description}

## Architecture

### Components

- **Service Layer**: Handles business logic
- **API Layer**: REST endpoints for external access
- **Data Layer**: Database operations and models

### Data Flow

```
Request -> API -> Service -> Data -> Response
```

## API Reference

### POST /api/v1/feature

**Request Body:**
```json
{{
  "name": "string (required)",
  "data": {{}}}}
```

**Response:**
```json
{{
  "success": true,
  "data": {{}}
}}
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| FEATURE_ENABLED | Enable/disable feature | true |
| FEATURE_TIMEOUT | Request timeout (seconds) | 30 |

## Testing

```bash
# Run unit tests
pytest tests/test_feature.py -v

# Run integration tests
pytest tests/test_feature_integration.py -v
```

## Deployment

1. Run database migrations
2. Set environment variables
3. Restart the service

## Changelog

- **v1.0.0**: Initial implementation
''',
        "explanation": f"Documentation for: {description}",
    }]


def _generate_config_code(description: str, files: list[str], framework: str) -> list[dict]:
    file_path = files[0] if files else "config/feature.yaml"

    return [{
        "file_path": file_path,
        "content": f'''# Configuration: {description}

feature:
  enabled: true
  name: "{description}"

  settings:
    timeout: 30
    retry_count: 3
    batch_size: 100

  logging:
    level: "INFO"
    format: "json"

  monitoring:
    enabled: true
    metrics_port: 9090
    health_check: "/health"

  security:
    auth_required: true
    rate_limit: 100
    allowed_origins:
      - "http://localhost:3000"
      - "http://localhost:8000"
''',
        "explanation": f"Configuration for: {description}",
    }]


def _simulate_task(task: dict) -> dict:
    """Simulate a software engineering task through its pipeline."""
    task["state"] = "analyzing"
    task["execution_log"].append({
        "timestamp": _now(), "state": "analyzing",
        "message": f"Analyzing repository {task['repository_id']}...",
    })

    if _is_guidance_request(task["task_description"]):
        task["state"] = "analyzing"
        task["execution_log"].append({
            "timestamp": _now(), "state": "analyzing",
            "message": "Scanning project structure and dependencies...",
        })

        task["task_type"] = "guidance"
        task["guidance_response"] = _build_guidance_response(
            task["task_description"], task["repository_id"]
        )

        task["state"] = "awaiting_approval"
        task["execution_log"].append({
            "timestamp": _now(), "state": "awaiting_approval",
            "message": f"Found {len(task['guidance_response']['suggestions'])} suggestions. Review and approve.",
        })
        return task

    task["state"] = "planning"
    task["execution_log"].append({
        "timestamp": _now(), "state": "planning",
        "message": f"Planning {task['task_type']} implementation...",
    })

    task["state"] = "generating"
    task["execution_log"].append({
        "timestamp": _now(), "state": "generating",
        "message": "Generating code changes...",
    })

    project_info = _scan_project(task["repository_id"])

    task["generated_code"] = _generate_code_for_task(
        task["task_type"], task["task_description"],
        task["target_files"] or [], project_info,
    )

    task["diffs"] = [
        {
            "file_path": c["file_path"],
            "stats": {"additions": len(c["content"].splitlines()), "deletions": 0},
            "is_new_file": not bool(task["target_files"]),
        }
        for c in task["generated_code"]
    ]

    task["state"] = "reviewing"
    task["execution_log"].append({
        "timestamp": _now(), "state": "reviewing",
        "message": "Running automated code review...",
    })

    task["review_result"] = {
        "passed": True,
        "score": 87,
        "summary": "Code looks good. Minor suggestions: add error handling for edge cases, consider adding type hints.",
    }

    task["validation_result"] = {
        "valid": True,
        "errors": [],
        "warnings": ["Consider adding unit tests for the new functionality"],
    }

    task["commit_summary"] = {
        "message": f"{task['task_type'].replace('_', ' ').title()}: {task['task_description'][:60]}",
        "description": task["task_description"],
        "files_changed": [c["file_path"] for c in task["generated_code"]],
    }

    task["state"] = "awaiting_approval"
    task["execution_log"].append({
        "timestamp": _now(), "state": "awaiting_approval",
        "message": "Implementation complete. Awaiting your review and approval.",
    })

    return task


@router.get("/history")
async def get_history():
    """Get all software engineering tasks."""
    return {"tasks": _TASKS}


@router.post("/execute")
async def execute_task(request: ExecuteRequest):
    """Create and execute a new software engineering task."""
    task = {
        "task_id": str(uuid.uuid4()),
        "repository_id": request.repository_id,
        "task_description": request.task_description,
        "task_type": request.task_type,
        "state": "idle",
        "target_files": request.target_files,
        "generated_code": None,
        "diffs": None,
        "review_result": None,
        "validation_result": None,
        "commit_summary": None,
        "guidance_response": None,
        "error": None,
        "execution_log": [{
            "timestamp": _now(), "state": "idle",
            "message": "Task created, starting pipeline...",
        }],
        "started_at": _now(),
        "completed_at": None,
    }

    task = _simulate_task(task)
    _TASKS.insert(0, task)
    return task


@router.post("/approve")
async def approve_task(request: ApproveRequest):
    """Approve a completed task."""
    task = next((t for t in _TASKS if t["task_id"] == request.task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["state"] = "completed"
    task["completed_at"] = _now()
    task["execution_log"].append({
        "timestamp": _now(), "state": "completed",
        "message": "Task approved and committed.",
    })
    return task


@router.post("/reject")
async def reject_task(request: RejectRequest):
    """Reject a task with a reason."""
    task = next((t for t in _TASKS if t["task_id"] == request.task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["state"] = "failed"
    task["error"] = request.reason
    task["completed_at"] = _now()
    task["execution_log"].append({
        "timestamp": _now(), "state": "failed",
        "message": f"Task rejected: {request.reason}",
    })
    return task
