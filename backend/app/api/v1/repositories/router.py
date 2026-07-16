"""Repository API router."""

import os
import shutil
import tempfile

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.repo_intelligence.exceptions import (
    AnalysisFailedException,
    GitCloneException,
    InvalidRepositoryException,
    RepositoryImportException,
    RepositoryNotFoundException,
    RepositoryTooLargeException,
    UnsupportedLanguageException,
)
from app.repo_intelligence.schemas.analysis import AnalysisResult
from app.repo_intelligence.schemas.graph import SemanticGraph
from app.repo_intelligence.schemas.repository import (
    RepositoryCreate,
    RepositoryInfo,
)
from app.schemas.common import BaseResponse

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post("/import", response_model=BaseResponse[RepositoryInfo])
async def import_repository(request: RepositoryCreate, req: Request) -> BaseResponse[RepositoryInfo]:
    """Import a new repository.

    Supports importing from:
    - Git URL (clone)
    - ZIP file path
    - Local folder path
    """
    repo_service = req.app.state.repo_service

    try:
        result = await repo_service.create_repository(request)
        return BaseResponse(
            data=result,
            message="Repository imported successfully",
        )
    except RepositoryTooLargeException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except InvalidRepositoryException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except GitCloneException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except RepositoryImportException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Import failed: {e}",
        )


@router.post("/import/upload", response_model=BaseResponse[RepositoryInfo])
async def upload_repository(
    name: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    req: Request = None,
) -> BaseResponse[RepositoryInfo]:
    """Import a repository by uploading a ZIP file."""
    if req is None:
        return BaseResponse(status="error", message="Request object required")

    repo_service = req.app.state.repo_service

    temp_dir = tempfile.mkdtemp()
    try:
        upload_path = os.path.join(temp_dir, file.filename or "upload.zip")
        with open(upload_path, "wb") as f:
            content = await file.read()
            f.write(content)

        request = RepositoryCreate(
            name=name,
            description=description,
            import_method="zip",
            source_path=upload_path,
        )

        result = await repo_service.create_repository(request)
        return BaseResponse(
            data=result,
            message="Repository uploaded and imported successfully",
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Upload failed: {e}",
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.get("", response_model=BaseResponse[list[RepositoryInfo]])
async def list_repositories(req: Request) -> BaseResponse[list[RepositoryInfo]]:
    """List all imported repositories."""
    repo_service = req.app.state.repo_service
    repositories = await repo_service.list_repositories()
    return BaseResponse(
        data=repositories,
        message=f"Found {len(repositories)} repositories",
    )


@router.get("/{repo_id}", response_model=BaseResponse[RepositoryInfo])
async def get_repository(repo_id: str, req: Request) -> BaseResponse[RepositoryInfo]:
    """Get repository details."""
    repo_service = req.app.state.repo_service

    try:
        result = await repo_service.get_repository(repo_id)
        return BaseResponse(data=result)
    except RepositoryNotFoundException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )


@router.delete("/{repo_id}", response_model=BaseResponse[dict])
async def delete_repository(repo_id: str, req: Request) -> BaseResponse[dict]:
    """Delete a repository."""
    repo_service = req.app.state.repo_service

    try:
        await repo_service.delete_repository(repo_id)
        return BaseResponse(
            data={"deleted": True},
            message="Repository deleted successfully",
        )
    except RepositoryNotFoundException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )


@router.get("/{repo_id}/summary", response_model=BaseResponse[dict])
async def get_summary(repo_id: str, req: Request) -> BaseResponse[dict]:
    """Get repository architecture summary."""
    repo_service = req.app.state.repo_service

    try:
        result = await repo_service.get_summary(repo_id)
        return BaseResponse(data=result)
    except RepositoryNotFoundException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )


@router.get("/{repo_id}/analysis", response_model=BaseResponse[AnalysisResult])
async def get_analysis(repo_id: str, req: Request) -> BaseResponse[AnalysisResult]:
    """Get full analysis results."""
    repo_service = req.app.state.repo_service

    try:
        result = await repo_service.get_analysis(repo_id)
        return BaseResponse(data=result)
    except RepositoryNotFoundException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )


@router.get("/{repo_id}/graph", response_model=BaseResponse[SemanticGraph])
async def get_graph(repo_id: str, req: Request) -> BaseResponse[SemanticGraph]:
    """Get semantic graph."""
    repo_service = req.app.state.repo_service

    try:
        result = await repo_service.get_graph(repo_id)
        return BaseResponse(data=result)
    except RepositoryNotFoundException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
