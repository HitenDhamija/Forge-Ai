"""Standalone tools API — actually executes tools."""

import uuid
import os
import subprocess
import time
from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

router = APIRouter(prefix="/tools", tags=["Tools"])

_tools: list[dict[str, Any]] = [
    {
        "tool_id": "filesystem",
        "name": "Filesystem Tool",
        "description": "Read, write, and manage files in the workspace",
        "provider": "forgeai",
        "type": "file",
        "status": "healthy",
        "version": "1.0.0",
        "supported_operations": ["read", "write", "list", "exists", "size"],
        "total_calls": 0,
        "success_count": 0,
        "error_count": 0,
        "avg_latency": 0,
    },
    {
        "tool_id": "git",
        "name": "Git Tool",
        "description": "Git operations - status, diff, log, branch",
        "provider": "forgeai",
        "type": "git",
        "status": "healthy",
        "version": "1.0.0",
        "supported_operations": ["status", "diff", "log", "branch", "remote"],
        "total_calls": 0,
        "success_count": 0,
        "error_count": 0,
        "avg_latency": 0,
    },
    {
        "tool_id": "terminal",
        "name": "Terminal Tool",
        "description": "Execute shell commands",
        "provider": "forgeai",
        "type": "shell",
        "status": "healthy",
        "version": "1.0.0",
        "supported_operations": ["execute"],
        "total_calls": 0,
        "success_count": 0,
        "error_count": 0,
        "avg_latency": 0,
    },
]

_executions: list[dict[str, Any]] = []


def _find_repo_path() -> str | None:
    """Find the repository path."""
    try:
        from app.api.v1.repositories_standalone import _repositories
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
                folders.append((folder_path, folder_name, os.path.getmtime(folder_path)))
        folders.sort(key=lambda x: -x[2])
        if folders:
            code_path = folders[0][0]
            subdirs = [d for d in os.listdir(code_path) if os.path.isdir(os.path.join(code_path, d)) and d != ".git"]
            if subdirs:
                code_path = os.path.join(code_path, subdirs[0])
            if os.path.isdir(code_path):
                return code_path
    return None


def _execute_filesystem(operation: str, params: dict) -> dict:
    """Execute filesystem operations."""
    repo_path = _find_repo_path() or os.getcwd()
    path = params.get("path", ".")

    # Resolve relative paths against repo
    if not os.path.isabs(path):
        path = os.path.join(repo_path, path)

    try:
        if operation == "read":
            if not os.path.exists(path):
                return {"success": False, "error": f"File not found: {path}"}
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(50000)  # Limit to 50KB
            return {"success": True, "data": {"path": path, "content": content, "size": os.path.getsize(path)}}

        elif operation == "list":
            target = path if os.path.isdir(path) else os.path.dirname(path)
            items = []
            for item in sorted(os.listdir(target)):
                item_path = os.path.join(target, item)
                items.append({
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                })
            return {"success": True, "data": {"path": target, "items": items[:100]}}

        elif operation == "exists":
            return {"success": True, "data": {"path": path, "exists": os.path.exists(path)}}

        elif operation == "size":
            if not os.path.exists(path):
                return {"success": False, "error": f"Path not found: {path}"}
            if os.path.isfile(path):
                return {"success": True, "data": {"path": path, "size": os.path.getsize(path)}}
            total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(path) for f in fs)
            return {"success": True, "data": {"path": path, "size": total}}

        else:
            return {"success": False, "error": f"Unknown filesystem operation: {operation}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_git(operation: str, params: dict) -> dict:
    """Execute git operations."""
    repo_path = _find_repo_path()
    if not repo_path:
        return {"success": False, "error": "No repository found"}

    try:
        if operation == "status":
            result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=repo_path, timeout=10)
            return {"success": True, "data": {"output": result.stdout, "errors": result.stderr}}

        elif operation == "diff":
            result = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True, cwd=repo_path, timeout=10)
            return {"success": True, "data": {"output": result.stdout, "errors": result.stderr}}

        elif operation == "log":
            count = params.get("count", 10)
            result = subprocess.run(["git", "log", f"--oneline", f"-{count}"], capture_output=True, text=True, cwd=repo_path, timeout=10)
            return {"success": True, "data": {"output": result.stdout, "errors": result.stderr}}

        elif operation == "branch":
            result = subprocess.run(["git", "branch", "-a"], capture_output=True, text=True, cwd=repo_path, timeout=10)
            return {"success": True, "data": {"output": result.stdout, "errors": result.stderr}}

        elif operation == "remote":
            result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, cwd=repo_path, timeout=10)
            return {"success": True, "data": {"output": result.stdout, "errors": result.stderr}}

        else:
            return {"success": False, "error": f"Unknown git operation: {operation}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_terminal(operation: str, params: dict) -> dict:
    """Execute terminal commands."""
    command = params.get("command", "echo 'No command provided'")
    repo_path = _find_repo_path() or os.getcwd()

    # Safety: block dangerous commands
    blocked = ["rm -rf /", "format", "del /s", "shutdown", "reboot"]
    if any(b in command.lower() for b in blocked):
        return {"success": False, "error": "Command blocked for safety"}

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=30,
            shell=True,
        )
        return {
            "success": result.returncode == 0,
            "data": {
                "stdout": result.stdout[:10000],
                "stderr": result.stderr[:5000],
                "return_code": result.returncode,
            },
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out after 30 seconds"}
    except Exception as e:
        return {"success": False, "error": str(e)}


class ToolExecuteRequest(BaseModel):
    tool_id: str
    operation: str
    parameters: dict[str, Any] = {}


@router.get("")
@router.get("/")
async def list_tools():
    return {"status": "success", "data": {"tools": _tools}}


@router.get("/health")
async def health_check():
    return {
        "status": "success",
        "data": {
            "total": len(_tools),
            "healthy": sum(1 for t in _tools if t["status"] == "healthy"),
            "unhealthy": sum(1 for t in _tools if t["status"] != "healthy"),
        },
    }


@router.get("/executions")
async def list_executions():
    return {"status": "success", "data": {"executions": _executions[:50]}}


@router.post("/execute")
async def execute_tool(request: ToolExecuteRequest):
    tool = next((t for t in _tools if t["tool_id"] == request.tool_id), None)
    if not tool:
        return {"status": "error", "success": False, "error": f"Tool '{request.tool_id}' not found"}

    start_time = time.time()
    execution_id = str(uuid.uuid4())

    # Execute the real tool
    if request.tool_id == "filesystem":
        result = _execute_filesystem(request.operation, request.parameters)
    elif request.tool_id == "git":
        result = _execute_git(request.operation, request.parameters)
    elif request.tool_id == "terminal":
        result = _execute_terminal(request.operation, request.parameters)
    else:
        result = {"success": False, "error": f"Tool '{request.tool_id}' execution not implemented"}

    duration_ms = round((time.time() - start_time) * 1000)

    execution = {
        "execution_id": execution_id,
        "tool_id": request.tool_id,
        "tool_name": tool["name"],
        "operation": request.operation,
        "parameters": request.parameters,
        "status": "completed" if result.get("success") else "failed",
        "result": result,
        "started_at": datetime.now(UTC).isoformat(),
        "completed_at": datetime.now(UTC).isoformat(),
        "duration_ms": duration_ms,
    }
    _executions.insert(0, execution)

    # Update tool stats
    tool["total_calls"] += 1
    if result.get("success"):
        tool["success_count"] += 1
    else:
        tool["error_count"] += 1
    tool["avg_latency"] = round((tool["avg_latency"] * (tool["total_calls"] - 1) + duration_ms) / tool["total_calls"])

    return {
        "status": "success",
        "success": result.get("success", False),
        "data": execution,
        "duration_ms": duration_ms,
    }


@router.get("/{tool_id}")
async def get_tool(tool_id: str):
    tool = next((t for t in _tools if t["tool_id"] == tool_id), None)
    if not tool:
        return {"status": "error", "message": "Tool not found"}
    return {"status": "success", "data": tool}


@router.get("/{tool_id}/health")
async def get_tool_health(tool_id: str):
    tool = next((t for t in _tools if t["tool_id"] == tool_id), None)
    if not tool:
        return {"status": "error", "message": "Tool not found"}
    return {"status": "success", "data": {"tool_id": tool_id, "status": tool["status"]}}


@router.post("/{tool_id}/cancel")
async def cancel_tool(tool_id: str):
    return {"status": "success", "message": f"Cancelled operations on {tool_id}"}
