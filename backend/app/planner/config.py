"""Planner configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class PlannerSettings(BaseSettings):
    """Planning engine configuration."""

    model_config = SettingsConfigDict(env_prefix="PLANNER_")

    MAX_TASKS_PER_PLAN: int = 50
    MAX_PLAN_HISTORY: int = 100
    DEFAULT_CONTEXT_TOKENS: int = 4096
    COMPLEXITY_THRESHOLDS: dict[str, int] = {
        "simple": 3,
        "medium": 7,
        "complex": 12,
        "very_complex": 20,
    }
    RISK_KEYWORDS: list[str] = [
        "delete",
        "remove",
        "drop",
        "migrate",
        "refactor",
        "security",
        "auth",
        "password",
        "token",
        "secret",
        "database",
        "schema",
        "table",
        "column",
        "breaking",
        "backward",
        "compatibility",
    ]


@lru_cache
def get_planner_settings() -> PlannerSettings:
    """Return cached planner settings instance."""
    return PlannerSettings()
