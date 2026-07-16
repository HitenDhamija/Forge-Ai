"""ForgeAI Production Hardening - Infrastructure Module."""

from .caching import (
    CacheConfig,
    CacheEntry,
    CacheService,
    cache_invalidate,
    cached,
    knowledge_cache,
    prompt_cache,
    repository_cache,
    search_cache,
    learning_cache,
    workflow_cache,
)
from .tasks import (
    BackgroundTask,
    DeploymentAnalysisTask,
    EmbeddingGenerationTask,
    KnowledgeGraphTask,
    LearningProcessTask,
    RepositoryIndexTask,
    TaskQueue,
    TaskResult,
    TaskStatus,
    WorkflowExecutionTask,
    background_task,
    task_queue,
)

__all__ = [
    # Caching
    "CacheConfig",
    "CacheEntry",
    "CacheService",
    "cached",
    "cache_invalidate",
    "repository_cache",
    "knowledge_cache",
    "workflow_cache",
    "prompt_cache",
    "learning_cache",
    "search_cache",
    # Tasks
    "TaskStatus",
    "TaskResult",
    "BackgroundTask",
    "TaskQueue",
    "background_task",
    "RepositoryIndexTask",
    "EmbeddingGenerationTask",
    "KnowledgeGraphTask",
    "LearningProcessTask",
    "WorkflowExecutionTask",
    "DeploymentAnalysisTask",
    "task_queue",
]
