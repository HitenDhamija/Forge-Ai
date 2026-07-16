"""Standalone AI chat API — uses real Ollama when available, mock otherwise.

Features:
- System prompt with ForgeAI context (repos, projects, agents, file contents)
- Full conversation history sent to Ollama for multi-turn chat
- Temperature/max_tokens forwarded to Ollama
- Streaming with message persistence
- Auto-generated conversation titles
"""

import json
import os
import uuid
import httpx
from datetime import datetime, UTC
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/ai", tags=["AI"])

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
_active_model = "qwen2.5:3b"
_conversations: list[dict[str, Any]] = []

SYSTEM_PROMPT = """You are ForgeAI Assistant — an expert software engineer who analyzes codebases with precision.

The user's workspace data (file tree, source code, project info) is provided in [WORKSPACE DATA] tags. Use it to answer questions.

## Response Guidelines by Question Type:

### When asked to DESCRIBE a project:
### Project Name & Purpose
- What the project IS (web app, CLI tool, library, API, etc.)
- What it DOES (its core functionality in 1-2 sentences)
- Who it's FOR (target users/audience)

### Tech Stack
- Languages with percentages
- Frameworks and libraries used
- Build tools, package managers

### Architecture
- How the project is organized (folder structure)
- Entry points (main files, index files)
- Key components and how they connect

### Key Features
- List the ACTUAL features implemented
- Reference specific files that implement each feature

### When asked about FEATURES to add or IMPROVEMENTS:
1. First analyze what the project ALREADY has
2. Identify MISSING features based on:
   - What similar projects typically have
   - Common best practices for this type of app
   - Security gaps
   - UX improvements
   - Performance optimizations
3. For each suggested feature, provide:
   - **Feature name** — Clear, specific
   - **Why it's needed** — Problem it solves
   - **Files to create/modify** — Exact file paths
   - **Implementation approach** — High-level steps
   - **Complexity** — Simple/Medium/Complex
   - **Priority** — High/Medium/Low

### When asked to REVIEW code:
- List specific issues with file paths and line numbers
- Categorize: Security, Performance, Quality, Architecture
- Provide fixes, not just criticism

### When asked to PLAN work:
- Break into specific, actionable tasks
- Identify dependencies between tasks
- Estimate time for each task
- Flag risks and edge cases

## Core Rules:
- ALWAYS reference SPECIFIC file names, function names, and line numbers
- NEVER give generic advice like "add tests" without specifying WHAT tests and WHERE
- If you see package.json, list the key dependencies and scripts
- If you see config files, explain what they configure
- NEVER guess — if information is missing, say "not visible in provided code"
- Be concrete: "index.js defines 5 Express routes" not "there's some backend code"
- Count actual issues when reviewing code quality"""


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    model: str | None = None
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    project_name: str | None = None


async def _check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


async def _get_ollama_models() -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                data = r.json()
                return [
                    {
                        "name": m["name"],
                        "size": m.get("size", 0),
                        "digest": m.get("digest"),
                        "modified_at": m.get("modified_at"),
                        "parameter_size": None,
                        "quantization": None,
                    }
                    for m in data.get("models", [])
                ]
    except Exception:
        pass
    return []


CODE_EXTENSIONS = {
    ".html", ".htm", ".css", ".scss", ".less",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".py", ".pyw",
    ".java", ".kt", ".scala",
    ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".swift", ".dart",
    ".vue", ".svelte",
    ".sql", ".graphql", ".gql",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".sh", ".bash", ".zsh", ".ps1",
    ".md", ".mdx", ".txt", ".rst",
    ".json", ".xml",
}

KEY_FILES = {
    "README.md", "readme.md", "Readme.md",
    "package.json", "pyproject.toml", "requirements.txt", "setup.py",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", "tsconfig.json", "next.config.ts", "next.config.js",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "Makefile", "CMakeLists.txt",
    "Gemfile", "pubspec.yaml",
}


def _read_file_snippet(filepath: str, max_lines: int = 80) -> str:
    """Read first N lines of a file, return as string."""
    try:
        size = os.path.getsize(filepath)
        if size > 100_000:
            return "[File too large to read]"
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[:max_lines]
        content = "".join(lines)
        if len(lines) == max_lines:
            content += "\n... (truncated)"
        return content
    except (OSError, UnicodeDecodeError):
        return ""


def _scan_repo_files(repo_path: str, max_files: int = 25) -> list[dict[str, str]]:
    """Scan a repo directory for key files AND code files, read their contents."""
    found_files = []
    key_file_hits = []
    code_file_hits = []
    SKIP_DIRS = {
        "node_modules", ".venv", "venv", "__pycache__", ".git",
        "dist", "build", ".next", ".nuxt", "coverage", ".idea",
        ".vscode", ".cache", ".turbo", "vendor", "__snapshots__",
    }
    SKIP_FILES = {".DS_Store", "Thumbs.db", ".gitkeep", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if fname in SKIP_FILES:
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, repo_path)
            ext = os.path.splitext(fname)[1].lower()

            if fname in KEY_FILES:
                key_file_hits.append((fpath, rel))
            elif ext in CODE_EXTENSIONS:
                code_file_hits.append((fpath, rel))

    # Prioritize: key files first (read more lines for config files), then code files
    for fpath, rel in key_file_hits:
        if len(found_files) >= max_files:
            break
        # Read config files fully (they're usually small and important)
        max_lines = 150 if os.path.basename(fpath) in {"package.json", "tsconfig.json", "pyproject.toml", "requirements.txt", "Dockerfile"} else 80
        content = _read_file_snippet(fpath, max_lines=max_lines)
        if content.strip():
            found_files.append({"path": rel, "content": content})

    for fpath, rel in code_file_hits:
        if len(found_files) >= max_files:
            break
        content = _read_file_snippet(fpath, max_lines=80)
        if content.strip():
            found_files.append({"path": rel, "content": content})

    return found_files


def _build_file_tree(repo_path: str, max_depth: int = 3) -> str:
    """Build a concise file tree string for context."""
    SKIP_DIRS = {
        "node_modules", ".venv", "venv", "__pycache__", ".git",
        "dist", "build", ".next", ".nuxt", "coverage", ".idea",
        ".vscode", ".cache", ".turbo", "vendor",
    }
    tree_lines = []
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        level = root.replace(repo_path, "").count(os.sep)
        if level >= max_depth:
            dirs.clear()
            continue
        indent = "  " * level
        folder_name = os.path.basename(root) or os.path.basename(repo_path)
        tree_lines.append(f"{indent}{folder_name}/")
        sub_indent = "  " * (level + 1)
        # Show files, skip lock files
        for f in sorted(files):
            if f in {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", ".DS_Store", "Thumbs.db"}:
                continue
            tree_lines.append(f"{sub_indent}{f}")
    return "\n".join(tree_lines[:80])  # Limit to 80 lines


async def _fetch_workspace_context(project_name: str | None = None) -> str:
    """Fetch rich context about repos, projects, agents, workflows AND file contents.
    
    Args:
        project_name: If provided, only read files from the repo matching this name.
    """
    context_parts = []

    # --- Repositories ---
    repos_data = []

    # 1. Try direct import from in-memory store
    try:
        from app.api.v1.repositories_standalone import _repositories
        for repo in _repositories.values():
            repos_data.append({
                "name": getattr(repo, "name", "unknown"),
                "status": getattr(repo, "status", "unknown"),
                "file_count": getattr(repo, "file_count", 0) or 0,
                "total_lines": getattr(repo, "total_lines", 0) or 0,
                "languages": getattr(repo, "languages", []) or [],
                "local_path": getattr(repo, "local_path", None),
            })
    except Exception:
        pass

    # 2. If no repos in memory, scan disk for any existing repo folders
    if not repos_data:
        temp_repos_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "forgeai", "repos")
        if os.path.isdir(temp_repos_dir):
            # Get folders sorted by modification time (newest first)
            folders = []
            for folder_name in os.listdir(temp_repos_dir):
                folder_path = os.path.join(temp_repos_dir, folder_name)
                if os.path.isdir(folder_path):
                    mtime = os.path.getmtime(folder_path)
                    folders.append((folder_path, folder_name, mtime))
            folders.sort(key=lambda x: -x[2])

            # Only take the 2 most recent repos with actual code
            for folder_path, folder_name, _ in folders[:5]:
                if len(repos_data) >= 2:
                    break
                # Find the actual code subfolder
                code_path = folder_path
                subdirs = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d)) and d != ".git"]
                if len(subdirs) == 1:
                    code_path = os.path.join(folder_path, subdirs[0])
                elif len(subdirs) > 1:
                    code_path = os.path.join(folder_path, subdirs[0])

                # Count files
                file_count = 0
                for root, dirs, files in os.walk(code_path):
                    dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", "venv"}]
                    for fname in files:
                        ext = os.path.splitext(fname)[1].lower()
                        if ext in CODE_EXTENSIONS or ext in KEY_FILES:
                            file_count += 1

                if file_count == 0:
                    continue

                repos_data.append({
                    "name": subdirs[0] if subdirs else folder_name,
                    "status": "ready",
                    "file_count": file_count,
                    "total_lines": 0,
                    "languages": [],
                    "local_path": code_path,
                })

    # Build repo context
    if repos_data:
        repo_lines = []
        for repo in repos_data[:2]:
            name = repo["name"]
            langs = repo["languages"]
            lang_summary = ", ".join(
                f"{l.get('name', '')} ({l.get('percentage', 0)}%)"
                for l in (langs[:5] if isinstance(langs, list) else [])
            )
            repo_lines.append(
                f"- {name} | Status: {repo['status']} | Files: {repo['file_count']} | Lines: {repo['total_lines']}\n"
                f"  Languages: {lang_summary or 'N/A'}"
            )
        context_parts.append("=== REPOSITORIES ===\n" + "\n".join(repo_lines))

        # Read actual source files — prefer the repo matching project_name
        target_repo = None
        if project_name:
            pn = project_name.lower()
            for repo in repos_data:
                if pn in repo["name"].lower() or repo["name"].lower() in pn:
                    target_repo = repo
                    break
        if not target_repo:
            target_repo = repos_data[0] if repos_data else None

        if target_repo:
            local_path = target_repo["local_path"]
            name = target_repo["name"]
            if local_path and os.path.isdir(local_path):
                # Add file tree first
                file_tree = _build_file_tree(local_path)
                if file_tree:
                    context_parts.append(f"=== FILE TREE: {name} ===\n{file_tree}")

                # Then read source files
                key_files = _scan_repo_files(local_path, max_files=25)
                if key_files:
                    file_section = f"\n=== SOURCE CODE: {name} ({len(key_files)} files) ==="
                    for kf in key_files:
                        file_section += f"\n\n--- {kf['path']} ---\n```\n{kf['content']}\n```"
                    context_parts.append(file_section)

    # --- Projects (direct import) ---
    try:
        from app.api.v1.projects_standalone import _PROJECTS
        projects = list(_PROJECTS.values()) if isinstance(_PROJECTS, dict) else list(_PROJECTS)
        if projects:
            proj_lines = []
            for p in projects[:10]:
                name = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else "unknown")
                status = getattr(p, "status", None) or (p.get("status") if isinstance(p, dict) else "unknown")
                desc = getattr(p, "description", None) or (p.get("description") if isinstance(p, dict) else "") or ""
                langs = getattr(p, "languages", []) or (p.get("languages", []) if isinstance(p, dict) else [])
                fw = getattr(p, "frameworks", []) or (p.get("frameworks", []) if isinstance(p, dict) else [])
                lang_str = ", ".join(langs) if isinstance(langs, list) else str(langs)
                fw_str = ", ".join(fw) if isinstance(fw, list) else str(fw)
                proj_lines.append(
                    f"- {name} | Status: {status}\n"
                    f"  Languages: {lang_str or 'N/A'} | Frameworks: {fw_str or 'N/A'}\n"
                    f"  Description: {(desc or 'None')[:120]}"
                )
            context_parts.append("=== PROJECTS ===\n" + "\n".join(proj_lines))
    except Exception:
        pass

    # --- Workflows (direct import) ---
    try:
        from app.api.v1.workflows_standalone import _WORKFLOWS
        if _WORKFLOWS:
            wf_lines = []
            for w in _WORKFLOWS[:10]:
                name = w.get("name", "unknown")
                status = w.get("status", "unknown")
                tasks = w.get("tasks", [])
                task_summary = ", ".join(f"{t.get('title', '')} [{t.get('status', '')}]" for t in tasks[:5])
                wf_lines.append(f"- {name} (status: {status})\n  Tasks: {task_summary or 'none'}")
            context_parts.append("=== WORKFLOWS ===\n" + "\n".join(wf_lines))
    except Exception:
        pass

    if context_parts:
        return "\n\n".join(context_parts)
    return "No workspace data available yet. Import a repository first via the Repositories page."


def _build_messages_for_ollama(
    conversation_messages: list[dict[str, str]],
    system_prompt: str,
    max_history: int = 20,
) -> list[dict[str, str]]:
    """Build the messages array for Ollama /api/chat."""
    messages = [{"role": "system", "content": system_prompt}]

    recent = conversation_messages[-max_history:] if len(conversation_messages) > max_history else conversation_messages
    for msg in recent:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", ""),
        })

    return messages


def _generate_title(message: str) -> str:
    """Generate a short conversation title from the first user message."""
    title = message.strip().replace("\n", " ")[:60]
    if len(message.strip()) > 60:
        title += "..."
    return title


@router.get("/status")
async def get_status():
    connected = await _check_ollama()
    models = await _get_ollama_models() if connected else []
    running = []
    if connected:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{OLLAMA_URL}/api/ps")
                if r.status_code == 200:
                    ps = r.json()
                    running = [m["name"] for m in ps.get("models", [])]
        except Exception:
            pass

    return {
        "status": "success",
        "data": {
            "connected": connected,
            "version": "0.31.1" if connected else None,
            "models_count": len(models),
            "running_models": running,
        },
    }


@router.get("/models")
async def list_models():
    global _active_model
    connected = await _check_ollama()
    if connected:
        models = await _get_ollama_models()
        if models and not any(m["name"] == _active_model for m in models):
            _active_model = models[0]["name"]
    else:
        models = [
            {"name": "qwen2.5:3b", "size": 1900000000, "digest": None, "modified_at": None, "parameter_size": "3B", "quantization": None},
            {"name": "qwen2.5:0.5b", "size": 397000000, "digest": None, "modified_at": None, "parameter_size": "0.5B", "quantization": None},
        ]

    return {
        "status": "success",
        "data": {
            "models": models,
            "active_model": _active_model,
        },
    }


@router.post("/chat")
async def chat(request: ChatRequest):
    global _active_model
    model = request.model or _active_model
    msg_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    conv_id = request.conversation_id or str(uuid.uuid4())

    connected = await _check_ollama()
    if connected:
        try:
            conv = next((c for c in _conversations if c["id"] == conv_id), None)
            history = conv.get("messages", []) if conv else []

            context = await _fetch_workspace_context()
            system_prompt = SYSTEM_PROMPT

            # Build history but inject context into the FIRST user message
            history_messages = []
            context_injected = False
            for m in history:
                content = m["content"]
                if not context_injected and m.get("role") == "user":
                    content = f"[WORKSPACE DATA]\n{context}\n[/WORKSPACE DATA]\n\n{content}"
                    context_injected = True
                history_messages.append({"role": m["role"], "content": content})

            # If no history, inject into the current message
            if not context_injected:
                user_content = f"[WORKSPACE DATA]\n{context}\n[/WORKSPACE DATA]\n\n{request.message}"
            else:
                user_content = request.message

            # For first message in a new conversation, prepend context to user message
            if not history_messages:
                user_content = f"[WORKSPACE DATA]\n{context}\n[/WORKSPACE DATA]\n\nUser question: {request.message}"

            history_messages.append({"role": "user", "content": user_content})

            messages = _build_messages_for_ollama(history_messages, system_prompt)

            ollama_body: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "stream": False,
            }
            if request.temperature is not None:
                ollama_body["options"] = ollama_body.get("options", {})
                ollama_body["options"]["temperature"] = request.temperature
            if request.max_tokens is not None:
                ollama_body["options"] = ollama_body.get("options", {})
                ollama_body["options"]["num_predict"] = request.max_tokens

            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(f"{OLLAMA_URL}/api/chat", json=ollama_body)
                if r.status_code == 200:
                    data = r.json()
                    response_text = data.get("message", {}).get("content", "")
                else:
                    response_text = f"Ollama error: {r.status_code}"
        except Exception as e:
            response_text = f"Ollama connection error: {str(e)}"
    else:
        response_text = (
            f"Ollama is not running. To enable real AI responses:\n"
            f"1. Start Ollama: ollama serve\n"
            f"2. The model {_active_model} is ready to use.\n\n"
            f"Your message: {request.message}"
        )

    conv = next((c for c in _conversations if c["id"] == conv_id), None)
    if conv:
        user_msg = {"id": str(uuid.uuid4()), "role": "user", "content": request.message, "timestamp": now}
        asst_msg = {"id": msg_id, "role": "assistant", "content": response_text, "timestamp": now}
        conv["messages"].append(user_msg)
        conv["messages"].append(asst_msg)
        conv["message_count"] = len(conv["messages"])
        conv["updated_at"] = now
        conv["model_used"] = model
        if conv.get("title") == "New Conversation" and len(conv["messages"]) == 2:
            conv["title"] = _generate_title(request.message)

    result = {
        "conversation_id": conv_id,
        "message": {
            "id": msg_id,
            "role": "assistant",
            "content": response_text,
            "timestamp": now,
        },
        "model_used": model,
        "response_time_ms": 50,
        "token_count": len(response_text.split()),
    }

    return {"status": "success", "data": result}


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    global _active_model
    model = request.model or _active_model
    conv_id = request.conversation_id or str(uuid.uuid4())

    connected = await _check_ollama()

    async def generate():
        if connected:
            try:
                conv = next((c for c in _conversations if c["id"] == conv_id), None)
                history = conv.get("messages", []) if conv else []

                context = await _fetch_workspace_context(project_name=request.project_name)
                system_prompt = f"{SYSTEM_PROMPT}\n\n--- Current Workspace ---\n{context}"

                history_messages = [{"role": m["role"], "content": m["content"]} for m in history]
                history_messages.append({"role": "user", "content": request.message})

                messages = _build_messages_for_ollama(history_messages, system_prompt)

                ollama_body: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "stream": True,
                }
                if request.temperature is not None:
                    ollama_body["options"] = ollama_body.get("options", {})
                    ollama_body["options"]["temperature"] = request.temperature
                if request.max_tokens is not None:
                    ollama_body["options"] = ollama_body.get("options", {})
                    ollama_body["options"]["num_predict"] = request.max_tokens

                full_response = ""
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json=ollama_body) as r:
                        async for line in r.aiter_lines():
                            if line.strip():
                                try:
                                    chunk = json.loads(line)
                                    delta = chunk.get("message", {}).get("content", "")
                                    done = chunk.get("done", False)
                                    full_response += delta
                                    yield f"data: {json.dumps({'conversation_id': conv_id, 'content': delta, 'done': done, 'model': model, 'created_at': datetime.now(UTC).isoformat()})}\n\n"
                                    if done:
                                        break
                                except json.JSONDecodeError:
                                    continue

                now = datetime.now(UTC).isoformat()
                if conv:
                    user_msg = {"id": str(uuid.uuid4()), "role": "user", "content": request.message, "timestamp": now}
                    asst_msg = {"id": str(uuid.uuid4()), "role": "assistant", "content": full_response, "timestamp": now}
                    conv["messages"].append(user_msg)
                    conv["messages"].append(asst_msg)
                    conv["message_count"] = len(conv["messages"])
                    conv["updated_at"] = now
                    conv["model_used"] = model
                    if conv.get("title") == "New Conversation" and len(conv["messages"]) == 2:
                        conv["title"] = _generate_title(request.message)

            except Exception as e:
                yield f"data: {json.dumps({'conversation_id': conv_id, 'content': f'Error: {str(e)}', 'done': True, 'model': model, 'created_at': datetime.now(UTC).isoformat()})}\n\n"
        else:
            content = f"Ollama is not running. Start with: ollama serve"
            yield f"data: {json.dumps({'conversation_id': conv_id, 'content': content, 'done': True, 'model': model, 'created_at': datetime.now(UTC).isoformat()})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations")
async def list_conversations():
    return {"status": "success", "data": _conversations}


@router.post("/conversations")
async def create_conversation(model: str | None = None):
    conv_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()
    conversation = {
        "id": conv_id,
        "title": "New Conversation",
        "messages": [],
        "model_used": model or _active_model,
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
    }
    _conversations.insert(0, conversation)
    return {"status": "success", "data": conversation}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    conv = next((c for c in _conversations if c["id"] == conversation_id), None)
    if not conv:
        return {"status": "error", "message": "Conversation not found"}
    return {"status": "success", "data": conv}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    global _conversations
    _conversations = [c for c in _conversations if c["id"] != conversation_id]
    return {"status": "success", "message": "Conversation deleted"}


@router.post("/models/switch")
async def switch_model(data: dict[str, Any]):
    global _active_model
    model = data.get("model_name") or data.get("model", "qwen2.5:0.5b")
    previous = _active_model
    _active_model = model
    return {
        "status": "success",
        "data": {
            "previous_model": previous,
            "current_model": model,
            "status": "success",
        },
    }


@router.post("/stop")
async def stop_generation(conversation_id: str | None = None):
    return {"status": "success", "message": "Generation stopped"}
