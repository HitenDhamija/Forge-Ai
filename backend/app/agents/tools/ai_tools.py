"""AI tools for agents - LLM interaction capabilities."""

from typing import Any

from app.agents.schemas import ToolType
from app.agents.tools.base import ToolBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMQueryTool(ToolBase):
    """Tool for querying the local LLM via Ollama."""

    def __init__(self) -> None:
        super().__init__(
            name="llm_query",
            description="Query the local LLM for analysis, generation, or reasoning",
            tool_type=ToolType.AI,
            parameters={
                "prompt": {
                    "type": "string",
                    "description": "The prompt to send to the LLM",
                },
                "model": {
                    "type": "string",
                    "description": "Model to use (default: configured default model)",
                },
                "temperature": {
                    "type": "number",
                    "description": "Temperature for generation (default: 0.7)",
                    "default": 0.7,
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens to generate (default: 2000)",
                    "default": 2000,
                },
            },
        )
        self._ollama_client = None
        self._model_manager = None

    def set_clients(self, ollama_client: Any, model_manager: Any) -> None:
        """Set the Ollama client and model manager.

        Args:
            ollama_client: The Ollama client instance.
            model_manager: The model manager instance.
        """
        self._ollama_client = ollama_client
        self._model_manager = model_manager

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate LLM query parameters."""
        if "prompt" not in kwargs:
            return False
        return isinstance(kwargs["prompt"], str) and len(kwargs["prompt"]) > 0

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Query the LLM."""
        if not self._ollama_client:
            return {
                "success": False,
                "error": "LLM client not initialized",
            }

        prompt = kwargs["prompt"]
        model = kwargs.get("model")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)

        if not model and self._model_manager:
            model = self._model_manager.get_default_model()

        try:
            response = await self._ollama_client.generate(
                model=model,
                prompt=prompt,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )

            return {
                "success": True,
                "response": response.get("response", ""),
                "model": model,
                "total_duration": response.get("total_duration"),
                "eval_count": response.get("eval_count"),
            }
        except Exception as e:
            logger.error("LLM query failed: %s", str(e))
            return {
                "success": False,
                "error": f"LLM query failed: {str(e)}",
            }


class AnalyzeCodeTool(ToolBase):
    """Tool for analyzing code using the LLM."""

    def __init__(self) -> None:
        super().__init__(
            name="analyze_code",
            description="Analyze code for issues, improvements, or understanding",
            tool_type=ToolType.AI,
            parameters={
                "code": {
                    "type": "string",
                    "description": "The code to analyze",
                },
                "language": {
                    "type": "string",
                    "description": "Programming language of the code",
                },
                "analysis_type": {
                    "type": "string",
                    "description": "Type of analysis: 'review', 'explain', 'optimize', 'find_bugs'",
                    "default": "review",
                },
            },
        )
        self._llm_tool = LLMQueryTool()

    def set_clients(self, ollama_client: Any, model_manager: Any) -> None:
        """Set the Ollama client and model manager."""
        self._llm_tool.set_clients(ollama_client, model_manager)

    async def validate_parameters(self, **kwargs: Any) -> bool:
        """Validate analyze code parameters."""
        return "code" in kwargs and isinstance(kwargs["code"], str)

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Analyze code using LLM."""
        code = kwargs["code"]
        language = kwargs.get("language", "unknown")
        analysis_type = kwargs.get("analysis_type", "review")

        prompts = {
            "review": f"Review the following {language} code and provide feedback on quality, potential issues, and improvements:\n\n```{language}\n{code}\n```",
            "explain": f"Explain what the following {language} code does in detail:\n\n```{language}\n{code}\n```",
            "optimize": f"Suggest optimizations for the following {language} code:\n\n```{language}\n{code}\n```",
            "find_bugs": f"Find potential bugs and issues in the following {language} code:\n\n```{language}\n{code}\n```",
        }

        prompt = prompts.get(analysis_type, prompts["review"])
        return await self._llm_tool.execute(prompt=prompt)
