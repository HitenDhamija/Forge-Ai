"""Documentation API - generates and serves per-repository documentation."""

import os
import re
import json
from pathlib import Path
from datetime import datetime, UTC
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/documentation", tags=["Documentation"])

GENERATED_DOCS_DIR = Path(__file__).parent.parent.parent.parent.parent / "docs" / "generated"


def _get_repo_docs_dir(repo_id: str) -> Path:
    return GENERATED_DOCS_DIR / repo_id


def _read_all_code(path: str) -> dict:
    SKIP = {"node_modules", ".venv", "__pycache__", ".git", "dist", "build", ".next", "docs"}
    CODE_EXT = {".html", ".css", ".js", ".py", ".htm", ".jsx", ".tsx", ".ts", ".json", ".md"}
    files = {}
    for root, dirs, fnames in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fname in fnames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in CODE_EXT:
                fpath = os.path.join(root, fname)
                try:
                    size = os.path.getsize(fpath)
                    if size > 200_000:
                        continue
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    rel = os.path.relpath(fpath, path)
                    files[rel] = content
                except (OSError, UnicodeDecodeError):
                    continue
    return files


def _find_repo_path(repo_id: str | None = None) -> str | None:
    try:
        from app.api.v1.repositories_standalone import _repositories
        if repo_id:
            repo = _repositories.get(repo_id)
            if repo:
                repo_path = getattr(repo, "local_path", None)
                if repo_path and os.path.isdir(repo_path):
                    return repo_path
            return None
        repos = list(_repositories.values())
        if repos:
            repo_path = getattr(repos[0], "local_path", None)
            if repo_path and os.path.isdir(repo_path):
                return repo_path
    except Exception:
        pass
    temp_repos_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "forgeai", "repos")
    if os.path.isdir(temp_repos_dir):
        folders = []
        for folder_name in os.listdir(temp_repos_dir):
            folder_path = os.path.join(temp_repos_dir, folder_name)
            if os.path.isdir(folder_path):
                mtime = os.path.getmtime(folder_path)
                folders.append((folder_path, folder_name, mtime))
        folders.sort(key=lambda x: -x[2])
        if folders:
            code_path = folders[0][0]
            subdirs = [d for d in os.listdir(code_path) if os.path.isdir(os.path.join(code_path, d)) and d != ".git"]
            if len(subdirs) == 1:
                code_path = os.path.join(code_path, subdirs[0])
            elif len(subdirs) > 1:
                code_path = os.path.join(code_path, subdirs[0])
            if os.path.isdir(code_path):
                return code_path
    return None


class GenerateRequest(BaseModel):
    repo_id: str | None = None


def _build_repo_context(repo_path: str) -> dict:
    """Build context about the repository for AI prompts."""
    code_files = _read_all_code(repo_path)
    if not code_files:
        return {}

    file_tree = "\n".join(sorted(code_files.keys())[:60])
    config_context = ""
    code_samples = ""
    tech_stack = []

    for fpath, content in code_files.items():
        base = os.path.basename(fpath)
        if base == "package.json":
            config_context += f"\n--- {fpath} ---\n{content[:1500]}\n"
            if "react" in content.lower(): tech_stack.append("React")
            if "express" in content.lower(): tech_stack.append("Express")
            if "next" in content.lower(): tech_stack.append("Next.js")
            if "mongoose" in content.lower() or "mongodb" in content.lower(): tech_stack.append("MongoDB")
            if "vue" in content.lower(): tech_stack.append("Vue")
            if "angular" in content.lower(): tech_stack.append("Angular")
            if "typescript" in content.lower(): tech_stack.append("TypeScript")
        elif base in {"requirements.txt", "pyproject.toml", "setup.py"}:
            config_context += f"\n--- {fpath} ---\n{content[:1000]}\n"
            if "django" in content.lower(): tech_stack.append("Django")
            if "flask" in content.lower(): tech_stack.append("Flask")
            if "fastapi" in content.lower(): tech_stack.append("FastAPI")
            if "celery" in content.lower(): tech_stack.append("Celery")
        elif base in {"Dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
            config_context += f"\n--- {fpath} ---\n{content[:800]}\n"
        elif base == ".env.example" or base == ".env.sample":
            config_context += f"\n--- {fpath} ---\n{content[:500]}\n"

    for fpath, content in list(code_files.items())[:10]:
        if not fpath.endswith(('.json', '.md', '.lock', '.sum')):
            code_samples += f"\n--- {fpath} ---\n{content[:600]}\n"

    return {
        "repo_name": os.path.basename(repo_path),
        "tech_str": ", ".join(tech_stack) if tech_stack else "JavaScript",
        "file_tree": file_tree,
        "config_context": config_context,
        "code_samples": code_samples,
    }


DOC_TEMPLATES = [
    {
        "filename": "getting-started.md",
        "title": "Getting Started",
        "system": "You are a technical writer. Write clear, practical getting-started documentation. Reference actual file names from the project. Be specific, not generic.",
        "prompt": """Write a "Getting Started" guide for this project. Include:

# Getting Started

## Overview
What this project does. Be specific about its purpose.

## Prerequisites
What you need installed (reference actual versions from config files).

## Installation
Step-by-step setup using actual commands. Reference the actual package manager (npm/yarn/pip) found in config files.

## Running the App
How to start the dev server. Use the actual scripts from package.json or equivalent.

## Project Structure
Explain the folder layout using ACTUAL folder and file names from the file tree below.

Be SPECIFIC. Reference real file names. Do NOT give generic advice.""",
    },
    {
        "filename": "api-reference.md",
        "title": "API Reference",
        "system": "You are a technical writer documenting REST APIs. List every endpoint you can find in the code. Use markdown tables for endpoints.",
        "prompt": """Write an API Reference for this project. Include:

# API Reference

## Endpoints
List ALL API endpoints you can find in the codebase. For each endpoint include:
- HTTP method (GET, POST, PUT, DELETE)
- Path
- Description of what it does
- Request/response format if visible

Format as a markdown table: | Method | Path | Description |

## Request/Response Format
Show example request and response payloads based on the actual code.

## Error Handling
How errors are returned (status codes, error format).

Reference ACTUAL route files and handler names from the code.""",
    },
    {
        "filename": "architecture.md",
        "title": "Architecture",
        "system": "You are a software architect documenting project architecture. Be specific about the actual technologies and patterns used.",
        "prompt": """Write an Architecture document for this project. Include:

# Architecture

## Tech Stack
List all technologies with their purpose. Reference actual versions from config files.

## Project Structure
How code is organized. Reference actual folders and their purposes.

## Data Flow
How data moves through the application. Describe the request lifecycle.

## Key Components
Main modules/classes and their responsibilities. Reference actual file names.

## Database Schema
If you can find models/schemas, describe the data structures.

Be SPECIFIC to this codebase. Reference real files.""",
    },
    {
        "filename": "deployment.md",
        "title": "Deployment",
        "system": "You are a DevOps engineer documenting deployment procedures. Be practical and specific.",
        "prompt": """Write a Deployment guide for this project. Include:

# Deployment

## Environment Variables
List ALL required environment variables found in the code (config files, .env examples, etc.). Format: | Variable | Description | Required |

## Docker
How to run with Docker. Reference actual Dockerfile or docker-compose files if they exist.

## Production Build
How to build for production. Use actual build commands from package.json scripts.

## Troubleshooting
Common issues and how to fix them. Reference actual error messages if visible.

Be SPECIFIC to this project. Do NOT give generic advice.""",
    },
]


async def _generate_one_doc(context: dict, template: dict, ollama_url: str) -> str | None:
    """Generate a single documentation file via Ollama."""
    import httpx as _httpx

    full_prompt = f"""{template['prompt']}

PROJECT: {context['repo_name']}
TECH STACK: {context['tech_str']}

FILE TREE:
{context['file_tree']}

CONFIG FILES:
{context['config_context']}

CODE SAMPLES:
{context['code_samples']}

Write ONLY the markdown content. Start with a # heading. Do not include any preamble or explanation outside the document."""

    try:
        async with _httpx.AsyncClient(timeout=180) as client:
            r = await client.post(f"{ollama_url}/api/chat", json={
                "model": "qwen2.5:3b",
                "messages": [
                    {"role": "system", "content": template["system"]},
                    {"role": "user", "content": full_prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 2000},
            })
            if r.status_code == 200:
                content = r.json().get("message", {}).get("content", "")
                if content and len(content) > 100:
                    return content.strip()
    except Exception:
        pass
    return None


@router.post("/generate")
async def generate_documentation(request: GenerateRequest | None = None):
    """Generate documentation for a repository - one doc at a time for reliability."""
    repo_id = request.repo_id if request else None
    repo_path = _find_repo_path(repo_id)
    if not repo_path:
        return {"status": "error", "message": "No repository found. Import a repository first."}
    if not repo_id:
        return {"status": "error", "message": "repo_id is required."}

    context = _build_repo_context(repo_path)
    if not context:
        return {"status": "error", "message": "No code files found in repository."}

    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    repo_docs_dir = _get_repo_docs_dir(repo_id)
    repo_docs_dir.mkdir(parents=True, exist_ok=True)

    # Clear old docs
    for old_doc in repo_docs_dir.glob("*.md"):
        old_doc.unlink()

    saved = []
    for template in DOC_TEMPLATES:
        content = await _generate_one_doc(context, template, ollama_url)
        if content:
            doc_path = repo_docs_dir / template["filename"]
            doc_path.write_text(content, encoding="utf-8")
            saved.append(template["filename"])

    if saved:
        return {
            "status": "success",
            "data": {
                "message": f"Generated {len(saved)} documents for {context['repo_name']}",
                "documents": saved,
                "repo_id": repo_id,
            }
        }
    else:
        return {"status": "error", "message": "AI failed to generate any documents. Make sure Ollama is running."}


@router.get("")
async def list_documents(repo_id: str | None = Query(None)):
    """List documentation for a specific repository."""
    if not repo_id:
        return {"status": "success", "data": []}

    repo_docs_dir = _get_repo_docs_dir(repo_id)
    docs = []

    if repo_docs_dir.exists():
        for f in sorted(repo_docs_dir.glob("*.md")):
            title = f.stem.replace("-", " ").replace("_", " ").title()
            category = "general"
            stem_lower = f.stem.lower()
            if "api" in stem_lower:
                category = "api"
            elif "architect" in stem_lower:
                category = "architecture"
            elif "getting" in stem_lower or "setup" in stem_lower or "install" in stem_lower:
                category = "getting-started"
            elif "deploy" in stem_lower:
                category = "deployment"
            elif "troubleshoot" in stem_lower or "debug" in stem_lower:
                category = "troubleshooting"
            elif "contribut" in stem_lower or "develop" in stem_lower or "coding" in stem_lower:
                category = "contributing"

            docs.append({
                "id": f.stem,
                "title": title,
                "filename": f.name,
                "category": category,
                "size": f.stat().st_size,
            })

    return {"status": "success", "data": docs}


@router.get("/{doc_id}")
async def get_document(doc_id: str, repo_id: str | None = Query(None)):
    """Get a specific documentation file."""
    if not repo_id:
        return {"status": "error", "message": "repo_id is required"}

    repo_docs_dir = _get_repo_docs_dir(repo_id)
    doc_path = repo_docs_dir / f"{doc_id}.md"

    if not doc_path.exists():
        for f in repo_docs_dir.glob("*.md"):
            if f.stem.lower() == doc_id.lower():
                doc_path = f
                break

    if not doc_path.exists():
        return {"status": "error", "message": f"Document '{doc_id}' not found"}

    content = doc_path.read_text(encoding="utf-8")
    title = doc_path.stem.replace("-", " ").replace("_", " ").title()

    return {
        "status": "success",
        "data": {
            "id": doc_path.stem,
            "title": title,
            "filename": doc_path.name,
            "content": content,
            "size": doc_path.stat().st_size,
        },
    }


@router.get("/search/{query}")
async def search_documents(query: str, repo_id: str | None = Query(None)):
    """Search documentation content for a specific repository."""
    if not repo_id:
        return {"status": "success", "data": []}

    repo_docs_dir = _get_repo_docs_dir(repo_id)
    results = []

    if repo_docs_dir.exists():
        query_lower = query.lower()
        for f in repo_docs_dir.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                if query_lower in content.lower():
                    lines = content.split("\n")
                    matching_lines = [l for l in lines if query_lower in l.lower()][:3]
                    results.append({
                        "id": f.stem,
                        "title": f.stem.replace("-", " ").replace("_", " ").title(),
                        "filename": f.name,
                        "matches": matching_lines,
                    })
            except Exception:
                continue

    return {"status": "success", "data": results}
