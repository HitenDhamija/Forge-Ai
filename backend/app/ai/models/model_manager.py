"""Model manager for Ollama model lifecycle and selection."""

import time

from app.ai.clients.ollama import OllamaClient
from app.ai.config import AISettings
from app.ai.exceptions import (
    ModelNotFoundException,
    ModelSwitchException,
    OllamaConnectionException,
)
from app.ai.schemas.model import (
    ModelInfo,
    ModelListResponse,
    ModelStatus,
    ModelStatusEnum,
    ModelSwitchResponse,
    OllamaStatus,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelManager:
    """Manages Ollama model lifecycle, selection, and caching."""

    def __init__(self, ollama_client: OllamaClient, settings: AISettings) -> None:
        self._client = ollama_client
        self._settings = settings
        self._active_model: str = settings.DEFAULT_MODEL
        self._model_cache: dict[str, ModelInfo] = {}
        self._cache_timestamp: float = 0.0
        self._cache_ttl: float = 30.0

    async def get_available_models(
        self, force_refresh: bool = False
    ) -> list[ModelInfo]:
        """List all installed models with optional cache refresh.

        Args:
            force_refresh: Ignore cached data and fetch fresh results.

        Returns:
            List of ``ModelInfo`` objects.
        """
        now = time.monotonic()
        if (
            not force_refresh
            and self._model_cache
            and (now - self._cache_timestamp) < self._cache_ttl
        ):
            return list(self._model_cache.values())

        try:
            raw_models = await self._client.list_models()
        except OllamaConnectionException:
            logger.warning("Cannot reach Ollama; returning cached models if available")
            return list(self._model_cache.values())

        models: dict[str, ModelInfo] = {}
        for raw in raw_models:
            name = raw.get("name", "")
            if not name:
                continue

            details = raw.get("details", {})
            models[name] = ModelInfo(
                name=name,
                size=raw.get("size"),
                digest=raw.get("digest"),
                modified_at=raw.get("modified_at"),
                parameter_size=details.get("parameter_size"),
                quantization=details.get("quantization_level"),
            )

        self._model_cache = models
        self._cache_timestamp = now
        return list(models.values())

    async def get_active_model(self) -> str:
        """Return the currently active model name."""
        return self._active_model

    async def switch_model(self, model_name: str) -> ModelSwitchResponse:
        """Switch the active model.

        Args:
            model_name: Target model identifier.

        Returns:
            A ``ModelSwitchResponse`` with previous and current model names.

        Raises:
            ModelNotFoundException: If the target model is not installed.
            ModelSwitchException: If the switch fails.
        """
        previous = self._active_model

        try:
            available = await self.get_available_models()
        except Exception as exc:
            raise ModelSwitchException(
                f"Failed to verify model availability: {exc}"
            ) from exc

        available_names = {m.name for m in available}
        if model_name not in available_names:
            raise ModelNotFoundException(
                f"Model '{model_name}' is not installed. "
                f"Available: {', '.join(sorted(available_names))}"
            )

        self._active_model = model_name
        logger.info("Switched active model from %s to %s", previous, model_name)

        return ModelSwitchResponse(
            previous_model=previous,
            current_model=model_name,
            status="success",
        )

    async def validate_model(self, model_name: str) -> bool:
        """Check if a model is available locally.

        Args:
            model_name: Model identifier to validate.

        Returns:
            ``True`` if the model is installed.
        """
        models = await self.get_available_models()
        return any(m.name == model_name for m in models)

    async def get_model_info(self, model_name: str) -> ModelInfo:
        """Get detailed information about a specific model.

        Args:
            model_name: Model identifier.

        Returns:
            ``ModelInfo`` with full metadata.

        Raises:
            ModelNotFoundException: If the model is not found.
        """
        try:
            raw = await self._client.show_model(model_name)
        except ModelNotFoundException:
            raise
        except Exception as exc:
            raise ModelNotFoundException(
                f"Failed to get info for model '{model_name}': {exc}"
            ) from exc

        details = raw.get("details", {})
        return ModelInfo(
            name=model_name,
            size=raw.get("size"),
            digest=raw.get("digest"),
            modified_at=raw.get("modified_at"),
            parameter_size=details.get("parameter_size"),
            quantization=details.get("quantization_level"),
        )

    async def get_model_status(self) -> list[ModelStatus]:
        """Get runtime status of all models.

        Returns:
            List of ``ModelStatus`` indicating running, loaded, or available state.
        """
        models = await self.get_available_models()
        try:
            running = await self._client.get_running_models()
        except Exception:
            running = []

        running_set = set(running)
        statuses: list[ModelStatus] = []
        for model in models:
            if model.name in running_set:
                status = ModelStatusEnum.RUNNING
            else:
                status = ModelStatusEnum.AVAILABLE
            statuses.append(
                ModelStatus(name=model.name, status=status, size=model.size)
            )
        return statuses

    async def get_ollama_status(self) -> OllamaStatus:
        """Get overall Ollama server status.

        Returns:
            ``OllamaStatus`` with connection info, version, and model counts.
        """
        connected = await self._client.health_check()
        if not connected:
            return OllamaStatus(connected=False)

        version = await self._client.get_version()
        models = await self.get_available_models()
        try:
            running = await self._client.get_running_models()
        except Exception:
            running = []

        return OllamaStatus(
            connected=True,
            version=version,
            models_count=len(models),
            running_models=running,
        )

    async def ensure_model_available(self, model_name: str) -> None:
        """Raise ``ModelNotFoundException`` if the model is not installed.

        Args:
            model_name: Model identifier to check.
        """
        available = await self.get_available_models()
        available_names = {m.name for m in available}
        if model_name not in available_names:
            raise ModelNotFoundException(
                f"Model '{model_name}' is not installed. "
                f"Available: {', '.join(sorted(available_names))}"
            )
