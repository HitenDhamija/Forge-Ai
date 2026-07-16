"""Model-related schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ModelStatusEnum(str, Enum):
    """Status of a model on the Ollama server."""

    RUNNING = "running"
    LOADED = "loaded"
    AVAILABLE = "available"
    OFFLINE = "offline"
    LOADING = "loading"


class ModelInfo(BaseModel):
    """Metadata about an installed model."""

    name: str
    size: int | None = None
    digest: str | None = None
    modified_at: datetime | None = None
    parameter_size: str | None = None
    quantization: str | None = None


class ModelStatus(BaseModel):
    """Runtime status of a specific model."""

    name: str
    status: ModelStatusEnum
    size: int | None = None
    vram_usage: int | None = None


class ModelListResponse(BaseModel):
    """Response containing all available models."""

    models: list[ModelInfo] = Field(default_factory=list)
    active_model: str


class ModelSwitchRequest(BaseModel):
    """Request body for switching the active model."""

    model_name: str = Field(..., min_length=1, description="Name of the model to activate")


class ModelSwitchResponse(BaseModel):
    """Response after switching the active model."""

    previous_model: str
    current_model: str
    status: str = "success"


class OllamaStatus(BaseModel):
    """Overall Ollama server status."""

    connected: bool
    version: str | None = None
    models_count: int = 0
    running_models: list[str] = Field(default_factory=list)
