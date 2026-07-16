"""Background task queue abstraction with in-memory execution."""

from __future__ import annotations

import asyncio
import functools
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class TaskStatus(str, Enum):
    """Possible states for a background task."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


@dataclass
class TaskResult:
    """Result metadata for a completed (or failed) task."""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    progress: float = 0.0


@dataclass
class BackgroundTask:
    """Internal representation of a queued task."""

    id: str
    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.pending
    result: Any = None
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)


# ======================================================================
# Task registry
# ======================================================================

_TASK_REGISTRY: dict[str, Callable] = {}


def background_task(name: str | None = None) -> Callable:
    """Decorator that registers an async callable as a background task."""

    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        _TASK_REGISTRY[task_name] = func

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        wrapper.task_name = task_name  # type: ignore[attr-defined]
        return wrapper

    return decorator


# ======================================================================
# Task queue
# ======================================================================


class TaskQueue:
    """In-memory task queue that executes tasks concurrently."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskResult] = {}
        self._running: dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def enqueue(self, name: str, *args: Any, **kwargs: Any) -> str:
        """Enqueue a registered task for execution. Returns the task id."""
        task_id = uuid.uuid4().hex
        result = TaskResult(task_id=task_id, status=TaskStatus.pending)
        self._tasks[task_id] = result

        func = _TASK_REGISTRY.get(name)
        if func is None:
            result.status = TaskStatus.failed
            result.error = f"Unknown task: {name}"
            result.completed_at = time.time()
            return task_id

        bg = BackgroundTask(id=task_id, name=name, args=args, kwargs=kwargs)
        asyncio.create_task(self._run(bg))
        return task_id

    async def get_task(self, task_id: str) -> TaskResult:
        result = self._tasks.get(task_id)
        if result is None:
            return TaskResult(
                task_id=task_id,
                status=TaskStatus.failed,
                error="Task not found",
            )
        return result

    async def cancel_task(self, task_id: str) -> bool:
        async_task = self._running.pop(task_id, None)
        result = self._tasks.get(task_id)
        if async_task is not None and not async_task.done():
            async_task.cancel()
            if result is not None:
                result.status = TaskStatus.cancelled
                result.completed_at = time.time()
            return True
        if result is not None and result.status == TaskStatus.pending:
            result.status = TaskStatus.cancelled
            result.completed_at = time.time()
            return True
        return False

    async def list_tasks(
        self, status: TaskStatus | None = None, limit: int = 50
    ) -> list[TaskResult]:
        tasks = list(self._tasks.values())
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    async def get_stats(self) -> dict:
        counts: dict[str, int] = {}
        for t in self._tasks.values():
            counts[t.status.value] = counts.get(t.status.value, 0) + 1
        return {
            "total": len(self._tasks),
            "running": len(self._running),
            **counts,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_progress(self, task_id: str, progress: float) -> None:
        result = self._tasks.get(task_id)
        if result is not None:
            result.progress = min(max(progress, 0.0), 100.0)

    def _complete_task(self, task_id: str, result: Any) -> None:
        entry = self._tasks.get(task_id)
        if entry is not None:
            entry.status = TaskStatus.completed
            entry.result = result
            entry.progress = 100.0
            entry.completed_at = time.time()

    def _fail_task(self, task_id: str, error: str) -> None:
        entry = self._tasks.get(task_id)
        if entry is not None:
            entry.status = TaskStatus.failed
            entry.error = error
            entry.completed_at = time.time()

    async def _run(self, bg: BackgroundTask) -> None:
        result = self._tasks[bg.id]
        result.status = TaskStatus.running
        result.started_at = time.time()

        func = _TASK_REGISTRY.get(bg.name)
        if func is None:
            self._fail_task(bg.id, f"Unknown task: {bg.name}")
            return

        try:
            task = asyncio.create_task(func(*bg.args, **bg.kwargs))
            self._running[bg.id] = task
            output = await task
            self._complete_task(bg.id, output)
        except asyncio.CancelledError:
            self._fail_task(bg.id, "Task cancelled")
        except Exception as exc:
            self._fail_task(bg.id, str(exc))
        finally:
            self._running.pop(bg.id, None)


# ======================================================================
# Pre-configured task types
# ======================================================================


@background_task("repository_index")
async def RepositoryIndexTask(repo_url: str, branch: str = "main") -> dict:
    """Index a repository for the knowledge base."""
    await asyncio.sleep(0.1)  # simulate work
    return {"repo_url": repo_url, "branch": branch, "indexed": True}


@background_task("embedding_generation")
async def EmbeddingGenerationTask(texts: list[str], model: str = "default") -> dict:
    """Generate embeddings for a list of texts."""
    await asyncio.sleep(0.1)
    return {"count": len(texts), "model": model, "embeddings_generated": True}


@background_task("knowledge_graph")
async def KnowledgeGraphTask(entities: list[str], relations: list[str]) -> dict:
    """Build or update the knowledge graph."""
    await asyncio.sleep(0.1)
    return {
        "entities": len(entities),
        "relations": len(relations),
        "built": True,
    }


@background_task("learning_process")
async def LearningProcessTask(data_id: str, mode: str = "incremental") -> dict:
    """Process learning data and update models."""
    await asyncio.sleep(0.1)
    return {"data_id": data_id, "mode": mode, "processed": True}


@background_task("workflow_execution")
async def WorkflowExecutionTask(workflow_id: str, params: dict | None = None) -> dict:
    """Execute an automated workflow."""
    await asyncio.sleep(0.1)
    return {"workflow_id": workflow_id, "params": params or {}, "executed": True}


@background_task("deployment_analysis")
async def DeploymentAnalysisTask(deployment_id: str) -> dict:
    """Analyze a deployment for health and performance."""
    await asyncio.sleep(0.1)
    return {"deployment_id": deployment_id, "status": "healthy"}


# ======================================================================
# Global instance
# ======================================================================

task_queue = TaskQueue()
