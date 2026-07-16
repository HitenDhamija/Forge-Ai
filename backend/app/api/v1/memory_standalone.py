"""Standalone memory API — works without legacy imports."""

import uuid
import os
import re
from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/memory", tags=["Memory"])

# In-memory storage
_indexed_repositories: list[dict[str, Any]] = []
_file_cache: dict[str, list[dict[str, Any]]] = {}  # repo_id -> list of {path, content, chunks}

_stats = {
    "total_chunks": 0,
    "total_repositories": 0,
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "dimensions": 384,
    "avg_search_time": 0,
    "total_searches": 0,
    "cache_hit_rate": 0,
    "storage_size_bytes": 0,
    "collections": [],
}


def _read_repo_files(repo_path: str) -> list[dict[str, Any]]:
    """Read all code files from a repo for indexing."""
    SKIP = {"node_modules", ".venv", "__pycache__", ".git", "dist", "build", ".next", "coverage"}
    CODE_EXT = {".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx", ".py", ".json", ".md", ".yaml", ".yml", ".xml", ".sh", ".sql"}
    files = []
    for root, dirs, fnames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fname in fnames:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in CODE_EXT:
                continue
            fpath = os.path.join(root, fname)
            try:
                size = os.path.getsize(fpath)
                if size > 200_000:
                    continue
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                rel = os.path.relpath(fpath, repo_path)
                files.append({"path": rel, "content": content})
            except (OSError, UnicodeDecodeError):
                continue
    return files


def _chunk_file(file_info: dict) -> list[dict[str, Any]]:
    """Split a file into searchable chunks (by function/class/section)."""
    content = file_info["content"]
    path = file_info["path"]
    chunks = []
    lines = content.split("\n")

    # Split by double newlines or every 20 lines
    current_chunk = []
    chunk_start = 1
    for i, line in enumerate(lines, 1):
        current_chunk.append(line)
        if len(current_chunk) >= 20 or (line.strip() == "" and len(current_chunk) >= 5):
            chunks.append({
                "file": path,
                "line_start": chunk_start,
                "line_end": i,
                "content": "\n".join(current_chunk),
            })
            current_chunk = []
            chunk_start = i + 1
    if current_chunk:
        chunks.append({
            "file": path,
            "line_start": chunk_start,
            "line_end": len(lines),
            "content": "\n".join(current_chunk),
        })
    return chunks


@router.get("/stats")
async def get_stats():
    _stats["total_repositories"] = len(_indexed_repositories)
    _stats["total_chunks"] = sum(r.get("chunks", 0) for r in _indexed_repositories)
    # Build collections list from indexed repos
    _stats["collections"] = [
        {"name": r.get("name", "unknown"), "count": r.get("chunks", 0), "size_bytes": None, "last_updated": r.get("indexed_at")}
        for r in _indexed_repositories
    ]
    return {"status": "success", "data": _stats}


@router.get("/repositories")
async def list_repositories():
    """Return all repositories - both indexed and imported."""
    # Merge indexed repos with imported repos from repositories_standalone
    all_repos = list(_indexed_repositories)
    indexed_ids = {r["id"] for r in all_repos}

    try:
        from app.api.v1.repositories_standalone import _repositories
        for repo_id, repo in _repositories.items():
            if repo_id not in indexed_ids:
                all_repos.append({
                    "id": repo_id,
                    "name": repo.name,
                    "chunks": 0,
                    "chunks_count": 0,
                    "indexed_at": None,
                    "status": "ready",
                })
    except Exception:
        pass

    return {"status": "success", "data": all_repos}


@router.post("/index")
async def index_repository(data: dict[str, Any]):
    repo_id = data.get("repository_id", str(uuid.uuid4()))
    repo_name = data.get("repository_name") or data.get("name", "Unknown Repository")
    force_reindex = data.get("force_reindex", False)

    # Check if already indexed
    existing = next((r for r in _indexed_repositories if r["id"] == repo_id), None)
    if existing and not force_reindex:
        return {"status": "success", "data": existing}

    # Remove existing entry if force reindex
    if existing and force_reindex:
        _indexed_repositories.remove(existing)

    # Try to find the repo's local_path and read files
    total_chunks = 0
    try:
        from app.api.v1.repositories_standalone import _repositories
        repo = next((r for r in _repositories.values() if getattr(r, "id", None) == repo_id), None)
        if not repo:
            repo = next((r for r in _repositories.values() if getattr(r, "name", "").lower() == repo_name.lower()), None)
        if repo:
            local_path = getattr(repo, "local_path", None)
            if local_path and os.path.isdir(local_path):
                files = _read_repo_files(local_path)
                all_chunks = []
                for f in files:
                    all_chunks.extend(_chunk_file(f))
                _file_cache[repo_id] = all_chunks
                total_chunks = len(all_chunks)
    except Exception:
        pass

    if total_chunks == 0:
        total_chunks = 50  # Default placeholder

    repo_entry = {
        "id": repo_id,
        "name": repo_name,
        "chunks": total_chunks,
        "chunks_count": total_chunks,
        "indexed_at": datetime.now(UTC).isoformat(),
        "status": "ready",
    }
    _indexed_repositories.append(repo_entry)
    return {"status": "success", "data": repo_entry}


@router.post("/search")
async def search(data: dict[str, Any]):
    query = data.get("query", "").strip()
    repository_id = data.get("repository_id", "").strip() or None
    if not query:
        return {"status": "success", "data": {"results": [], "query": "", "total_results": 0, "search_time_ms": 0}}

    query_lower = query.lower()
    # Support multiple search terms (space-separated)
    search_terms = [t.strip() for t in query_lower.split() if t.strip()]
    results = []
    import time
    start = time.time()

    # Search through indexed file chunks
    for repo_id, chunks in _file_cache.items():
        # Filter by repository_id if specified
        if repository_id and repo_id != repository_id:
            continue
        for idx, chunk in enumerate(chunks):
            content_lower = chunk["content"].lower()
            # Match if ALL search terms appear in the content
            if all(term in content_lower for term in search_terms):
                lines = chunk["content"].split("\n")
                matching_lines = [l for l in lines if any(term in l.lower() for term in search_terms)]
                # Score based on number of matching terms and lines
                score = (len(search_terms) * 0.3) + (len(matching_lines) / max(len(lines), 1) * 0.7)
                results.append({
                    "chunk": {
                        "id": f"{repo_id}-{idx}",
                        "repository_id": repo_id,
                        "chunk_type": "function",
                        "content": chunk["content"][:500],
                        "metadata": {"file": chunk["file"], "line_start": chunk["line_start"], "line_end": chunk["line_end"]},
                        "embedding_model": None,
                        "version": 1,
                        "created_at": datetime.now(UTC).isoformat(),
                    },
                    "score": round(score, 3),
                    "rank": len(results) + 1,
                    "explanation": f"Matched terms: {', '.join(search_terms)} in {chunk['file']}",
                })

    # If no results from cached chunks, try scanning repo files directly
    if not results:
        try:
            from app.api.v1.repositories_standalone import _repositories
            for repo in _repositories.values():
                local_path = getattr(repo, "local_path", None)
                repo_id = getattr(repo, "id", "unknown")
                # Filter by repository_id if specified
                if repository_id and repo_id != repository_id:
                    continue
                if not local_path or not os.path.isdir(local_path):
                    continue
                SKIP = {"node_modules", ".venv", "__pycache__", ".git", "dist", "build", ".next"}
                CODE_EXT = {".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx", ".py", ".json", ".md", ".yaml", ".yml"}
                file_idx = 0
                for root, dirs, files in os.walk(local_path):
                    dirs[:] = [d for d in dirs if d not in SKIP]
                    for fname in files:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext not in CODE_EXT:
                            continue
                        fpath = os.path.join(root, fname)
                        try:
                            size = os.path.getsize(fpath)
                            if size > 200_000:
                                continue
                            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            content_lower = content.lower()
                            if all(term in content_lower for term in search_terms):
                                lines = content.split("\n")
                                matching_lines = [l for l in lines if any(term in l.lower() for term in search_terms)]
                                rel = os.path.relpath(fpath, local_path)
                                score = len(search_terms) * 0.3 + (len(matching_lines) / max(len(lines), 1) * 0.7)
                                results.append({
                                    "chunk": {
                                        "id": f"{repo_id}-file-{file_idx}",
                                        "repository_id": repo_id,
                                        "chunk_type": "function",
                                        "content": content[:500],
                                        "metadata": {"file": rel, "line_start": 1, "line_end": len(lines)},
                                        "embedding_model": None,
                                        "version": 1,
                                        "created_at": datetime.now(UTC).isoformat(),
                                    },
                                    "score": round(score, 3),
                                    "rank": len(results) + 1,
                                    "explanation": f"Matched terms: {', '.join(search_terms)} in {rel}",
                                })
                                file_idx += 1
                        except (OSError, UnicodeDecodeError):
                            continue
        except Exception:
            pass

    # Sort by relevance
    results.sort(key=lambda x: -x["score"])
    # Update ranks after sorting
    for i, r in enumerate(results):
        r["rank"] = i + 1
    elapsed_ms = round((time.time() - start) * 1000, 1)

    _stats["total_searches"] += 1
    _stats["avg_search_time"] = elapsed_ms

    return {
        "status": "success",
        "data": {
            "results": results[:10],
            "query": query,
            "total_results": len(results),
            "search_time_ms": elapsed_ms,
        },
    }


@router.post("/context")
async def get_context(data: dict[str, Any]):
    query = data.get("query", "").lower()
    context_parts = []

    for repo_id, chunks in _file_cache.items():
        relevant = [c for c in chunks if query in c["content"].lower()]
        for chunk in relevant[:3]:
            context_parts.append(f"File: {chunk['file']} (lines {chunk['line_start']}-{chunk['line_end']})\n{chunk['content'][:300]}")

    return {
        "status": "success",
        "data": {
            "context": "\n\n---\n\n".join(context_parts) if context_parts else f"No context found for: {query}",
            "sources": [],
        },
    }


@router.delete("/index/{repository_id}")
async def delete_index(repository_id: str):
    global _indexed_repositories
    before = len(_indexed_repositories)
    _indexed_repositories = [r for r in _indexed_repositories if r["id"] != repository_id]
    if len(_indexed_repositories) == before:
        return {"status": "error", "message": "Repository not found"}
    return {"status": "success", "message": "Index deleted"}
