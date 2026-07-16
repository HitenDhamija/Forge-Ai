"""Executor agent for carrying out specific actions."""

from typing import Any

from app.agents.agent_base import AgentBase
from app.agents.schemas import AgentType
from app.agents.tools.registry import ToolRegistry
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutorAgent(AgentBase):
    """Agent specialized in executing specific actions and tasks.

    The Executor Agent takes a plan or instruction and carries out
    the individual steps using available tools.
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        super().__init__(
            name="Executor Agent",
            description="Executes specific actions and implements changes",
            agent_type=AgentType.EXECUTOR,
            tool_registry=tool_registry,
        )

    async def execute(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        """Execute the task.

        Args:
            task_id: ID of the task.
            **kwargs: Must contain 'action' or 'steps' field.

        Returns:
            Execution results.
        """
        action = kwargs.get("action", "")
        steps = kwargs.get("steps", [])
        parameters = kwargs.get("parameters", {})

        logger.info("Executing task %s: %s", task_id, action[:100])

        results = []

        if steps:
            for step in steps:
                step_result = await self._execute_step(step, parameters)
                results.append(step_result)

                if not step_result.get("success"):
                    logger.warning(
                        "Step failed: %s - %s",
                        step.get("description", "Unknown"),
                        step_result.get("error", "Unknown error"),
                    )
                    break
        elif action:
            result = await self._execute_action(action, parameters)
            results.append(result)

        return {
            "results": results,
            "total_steps": len(results),
            "successful_steps": sum(1 for r in results if r.get("success")),
        }

    async def _execute_step(
        self, step: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a single step."""
        tool_name = step.get("tool")
        params = step.get("params", {})

        merged_params = {**context, **params}

        if not tool_name:
            return {
                "success": False,
                "error": "No tool specified for step",
            }

        try:
            result = await self.tool_registry.execute_tool(
                tool_name,
                agent_id=self.id,
                **merged_params,
            )
            return {
                "success": result.get("success", True),
                "step": step.get("description", "Unknown"),
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "step": step.get("description", "Unknown"),
                "error": str(e),
            }

    async def _execute_action(
        self, action: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a single action."""
        action_lower = action.lower()

        if "read" in action_lower:
            return await self._execute_read(parameters)
        elif "write" in action_lower:
            return await self._execute_write(parameters)
        elif "edit" in action_lower:
            return await self._execute_edit(parameters)
        elif "search" in action_lower:
            return await self._execute_search(parameters)
        elif "analyze" in action_lower:
            return await self._execute_analyze(parameters)
        else:
            return await self._execute_generic(action, parameters)

    async def _execute_read(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a read action."""
        file_path = params.get("file_path", "")
        if not file_path:
            return {"success": False, "error": "No file_path specified"}

        result = await self.tool_registry.execute_tool(
            "read_file",
            agent_id=self.id,
            file_path=file_path,
        )
        return {"success": result.get("success", False), "result": result}

    async def _execute_write(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a write action."""
        file_path = params.get("file_path", "")
        content = params.get("content", "")

        if not file_path or not content:
            return {"success": False, "error": "file_path and content required"}

        result = await self.tool_registry.execute_tool(
            "write_file",
            agent_id=self.id,
            file_path=file_path,
            content=content,
        )
        return {"success": result.get("success", False), "result": result}

    async def _execute_edit(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute an edit action."""
        file_path = params.get("file_path", "")
        old_content = params.get("old_content", "")
        new_content = params.get("new_content", "")

        if not all([file_path, old_content, new_content]):
            return {
                "success": False,
                "error": "file_path, old_content, and new_content required",
            }

        result = await self.tool_registry.execute_tool(
            "edit_file",
            agent_id=self.id,
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
        )
        return {"success": result.get("success", False), "result": result}

    async def _execute_search(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a search action."""
        pattern = params.get("pattern", "")
        if not pattern:
            return {"success": False, "error": "No pattern specified"}

        result = await self.tool_registry.execute_tool(
            "grep_search",
            agent_id=self.id,
            pattern=pattern,
            directory=params.get("directory", "."),
        )
        return {"success": result.get("success", False), "result": result}

    async def _execute_analyze(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute an analysis action."""
        code = params.get("code", "")
        if not code:
            return {"success": False, "error": "No code provided for analysis"}

        result = await self.tool_registry.execute_tool(
            "analyze_code",
            agent_id=self.id,
            code=code,
            language=params.get("language", "unknown"),
            analysis_type=params.get("analysis_type", "review"),
        )
        return {"success": result.get("success", False), "result": result}

    async def _execute_generic(
        self, action: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a generic action using LLM."""
        prompt = f"Execute the following action: {action}\n\nParameters: {params}"

        result = await self.tool_registry.execute_tool(
            "llm_query",
            agent_id=self.id,
            prompt=prompt,
        )
        return {"success": result.get("success", False), "result": result}
