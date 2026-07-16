"""Memory API router."""

from fastapi import APIRouter, Request

from app.memory.exceptions import (
    ChunkingException,
    EmbeddingException,
    IndexingException,
    SearchException,
    VectorStoreException,
)
from app.memory.schemas.memory import (
    ContextRequest,
    ContextResponse,
    IndexRequest,
    IndexResponse,
    MemoryStats,
    SearchRequest,
    SearchResponse,
)
from app.schemas.common import BaseResponse

router = APIRouter(prefix="/memory", tags=["Memory"])


@router.post("/index", response_model=BaseResponse[IndexResponse])
async def index_repository(
    request: IndexRequest, req: Request
) -> BaseResponse[IndexResponse]:
    """Index a repository into semantic memory."""
    memory_service = req.app.state.memory_service

    try:
        result = await memory_service.index_repository(
            repository_id=request.repository_id,
            repository_name=request.repository_name,
            analysis=request.analysis_result,
            graph=request.semantic_graph,
            force_reindex=request.force_reindex,
        )
        return BaseResponse(
            data=result,
            message="Repository indexed successfully",
        )
    except IndexingException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except EmbeddingException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except VectorStoreException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except ChunkingException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Indexing failed: {e}",
        )


@router.post("/search", response_model=BaseResponse[SearchResponse])
async def search_memory(
    request: SearchRequest, req: Request
) -> BaseResponse[SearchResponse]:
    """Search semantic memory."""
    memory_service = req.app.state.memory_service

    try:
        result = await memory_service.search(request)
        return BaseResponse(
            data=result,
            message=f"Found {result.total_results} results",
        )
    except SearchException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except VectorStoreException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Search failed: {e}",
        )


@router.post("/context", response_model=BaseResponse[ContextResponse])
async def get_context(
    request: ContextRequest, req: Request
) -> BaseResponse[ContextResponse]:
    """Get optimized context for a query."""
    memory_service = req.app.state.memory_service

    try:
        result = await memory_service.get_context(request)
        return BaseResponse(
            data=result,
            message="Context built successfully",
        )
    except SearchException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Context building failed: {e}",
        )


@router.get("/repositories", response_model=BaseResponse[list[dict]])
async def list_repositories(req: Request) -> BaseResponse[list[dict]]:
    """List all indexed repositories."""
    memory_service = req.app.state.memory_service

    try:
        result = await memory_service.list_repositories()
        return BaseResponse(
            data=result,
            message=f"Found {len(result)} repositories",
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to list repositories: {e}",
        )


@router.get("/stats", response_model=BaseResponse[MemoryStats])
async def get_stats(req: Request) -> BaseResponse[MemoryStats]:
    """Get memory statistics."""
    memory_service = req.app.state.memory_service

    try:
        result = await memory_service.get_stats()
        return BaseResponse(
            data=result,
            message="Memory statistics retrieved",
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to get stats: {e}",
        )


@router.delete("/index/{repository_id}", response_model=BaseResponse[dict])
async def delete_repository(
    repository_id: str, req: Request
) -> BaseResponse[dict]:
    """Delete memory for a repository."""
    memory_service = req.app.state.memory_service

    try:
        await memory_service.delete_repository(repository_id)
        return BaseResponse(
            data={"deleted": True, "repository_id": repository_id},
            message="Repository memory deleted successfully",
        )
    except VectorStoreException as e:
        return BaseResponse(
            status="error",
            message=str(e),
        )
    except Exception as e:
        return BaseResponse(
            status="error",
            message=f"Failed to delete repository: {e}",
        )
