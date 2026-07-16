"""Configuration for the Workflows module."""

from pydantic_settings import BaseSettings


class WorkflowSettings(BaseSettings):
    """Settings for workflow execution."""

    MAX_CONCURRENT_WORKFLOWS: int = 10
    MAX_TASKS_PER_WORKFLOW: int = 100
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 30
    TASK_TIMEOUT_SECONDS: int = 600
    WORKFLOW_TIMEOUT_SECONDS: int = 3600
    ENABLE_AUTO_APPROVAL: bool = False
    ENABLE_DEPENDENCY_VALIDATION: bool = True

    model_config = {"env_prefix": "WORKFLOW_"}


_workflow_settings: WorkflowSettings | None = None


def get_workflow_settings() -> WorkflowSettings:
    """Get or create workflow settings singleton."""
    global _workflow_settings
    if _workflow_settings is None:
        _workflow_settings = WorkflowSettings()
    return _workflow_settings
