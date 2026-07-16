"""Planner agent for breaking down complex tasks."""

from typing import Any

from app.agents.agent_base import AgentBase
from app.agents.schemas import AgentType
from app.agents.tools.registry import ToolRegistry
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlannerAgent(AgentBase):
    """Agent specialized in planning and task decomposition.

    The Planner Agent analyzes complex requests and breaks them down
    into actionable steps with clear dependencies and priorities.
    """

    def __init__(self, tool_registry: ToolRegistry) -> None:
        super().__init__(
            name="Planner Agent",
            description="Analyzes complex tasks and creates detailed execution plans",
            agent_type=AgentType.PLANNER,
            tool_registry=tool_registry,
        )

    async def execute(self, task_id: str, **kwargs: Any) -> dict[str, Any]:
        """Execute planning task.

        Args:
            task_id: ID of the task.
            **kwargs: Must contain 'goal' or 'description' field.

        Returns:
            Execution plan with steps and dependencies.
        """
        goal = kwargs.get("goal") or kwargs.get("description", "")
        context = kwargs.get("context", {})
        constraints = kwargs.get("constraints", [])

        logger.info("Planning task %s: %s", task_id, goal[:100])

        plan = {
            "goal": goal,
            "steps": [],
            "dependencies": [],
            "estimated_effort": "medium",
            "risks": [],
        }

        if context.get("codebase_path"):
            analysis = await self._analyze_codebase(context["codebase_path"])
            plan["codebase_analysis"] = analysis

        steps = await self._generate_steps(goal, context, constraints)
        plan["steps"] = steps

        plan["dependencies"] = self._identify_dependencies(steps)

        plan["risks"] = await self._assess_risks(goal, steps)

        return plan

    async def _analyze_codebase(self, path: str) -> dict[str, Any]:
        """Analyze codebase structure."""
        result = await self.tool_registry.execute_tool(
            "list_directory",
            agent_id=self.id,
            directory_path=path,
            recursive=True,
            max_depth=3,
        )
        return result

    async def _generate_steps(
        self,
        goal: str,
        context: dict[str, Any],
        constraints: list[str],
    ) -> list[dict[str, Any]]:
        """Generate execution steps for the goal."""
        steps = []

        if "analyze" in goal.lower() or "review" in goal.lower():
            steps = [
                {
                    "id": "step_1",
                    "description": "Understand the codebase structure",
                    "tool": "list_directory",
                    "status": "pending",
                },
                {
                    "id": "step_2",
                    "description": "Identify relevant files and modules",
                    "tool": "find_files",
                    "status": "pending",
                },
                {
                    "id": "step_3",
                    "description": "Analyze code patterns and architecture",
                    "tool": "grep_search",
                    "status": "pending",
                },
                {
                    "id": "step_4",
                    "description": "Generate findings and recommendations",
                    "tool": "llm_query",
                    "status": "pending",
                },
            ]
        elif "implement" in goal.lower() or "create" in goal.lower():
            steps = [
                {
                    "id": "step_1",
                    "description": "Understand requirements and constraints",
                    "tool": "llm_query",
                    "status": "pending",
                },
                {
                    "id": "step_2",
                    "description": "Review existing code patterns",
                    "tool": "grep_search",
                    "status": "pending",
                },
                {
                    "id": "step_3",
                    "description": "Create implementation plan",
                    "tool": "llm_query",
                    "status": "pending",
                },
                {
                    "id": "step_4",
                    "description": "Write code",
                    "tool": "write_file",
                    "status": "pending",
                },
                {
                    "id": "step_5",
                    "description": "Verify implementation",
                    "tool": "read_file",
                    "status": "pending",
                },
            ]
        elif "fix" in goal.lower() or "debug" in goal.lower():
            steps = [
                {
                    "id": "step_1",
                    "description": "Identify the issue",
                    "tool": "grep_search",
                    "status": "pending",
                },
                {
                    "id": "step_2",
                    "description": "Analyze root cause",
                    "tool": "llm_query",
                    "status": "pending",
                },
                {
                    "id": "step_3",
                    "description": "Implement fix",
                    "tool": "edit_file",
                    "status": "pending",
                },
                {
                    "id": "step_4",
                    "description": "Verify fix",
                    "tool": "read_file",
                    "status": "pending",
                },
            ]
        else:
            steps = [
                {
                    "id": "step_1",
                    "description": "Analyze the request",
                    "tool": "llm_query",
                    "status": "pending",
                },
                {
                    "id": "step_2",
                    "description": "Gather necessary information",
                    "tool": "grep_search",
                    "status": "pending",
                },
                {
                    "id": "step_3",
                    "description": "Execute the task",
                    "tool": "llm_query",
                    "status": "pending",
                },
            ]

        return steps

    def _identify_dependencies(
        self, steps: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Identify dependencies between steps."""
        dependencies = []
        for i, step in enumerate(steps):
            if i > 0:
                dependencies.append({
                    "step": step["id"],
                    "depends_on": steps[i - 1]["id"],
                })
        return dependencies

    async def _assess_risks(
        self, goal: str, steps: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Assess potential risks."""
        risks = []

        file_ops = [
            s for s in steps
            if s.get("tool") in ("write_file", "edit_file")
        ]
        if file_ops:
            risks.append({
                "type": "data_loss",
                "description": "Task involves file modifications",
                "mitigation": "Ensure backups before changes",
            })

        if len(steps) > 5:
            risks.append({
                "type": "complexity",
                "description": f"Task has {len(steps)} steps",
                "mitigation": "Break into smaller subtasks if needed",
            })

        return risks
