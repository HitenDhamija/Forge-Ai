"""Supervisor agent for orchestrating specialized agents."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.agents.enterprise.communication import CommunicationBus
from app.agents.enterprise.memory import AgentMemoryManager
from app.agents.enterprise.prompts import PromptManager, create_default_templates
from app.agents.enterprise.registry import AgentRegistry
from app.agents.enterprise.schemas import (
    AgentInfo,
    AgentMemory,
    AgentRole,
    AgentStatus,
    Capability,
    EventType,
    MessageType,
    Policy,
    TaskAssignment,
)
from app.agents.enterprise.validators import AgentValidator
from app.core.logging import get_logger

logger = get_logger(__name__)


class SupervisorAgent:
    """Supervisor Agent for ForgeAI.

    Responsibilities:
    - Receive workflow from Planner
    - Analyze workflow requirements
    - Determine required specialists
    - Assign tasks to agents
    - Track execution progress
    - Collect outputs
    - Validate completion
    - Generate execution summary

    The Supervisor NEVER:
    - Writes code
    - Modifies repositories
    - Calls tools
    - Executes tasks directly

    It ONLY orchestrates.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        communication: CommunicationBus,
    ):
        """Initialize the Supervisor Agent.

        Args:
            registry: Agent registry for discovery.
            communication: Communication bus.
        """
        self.id = str(uuid.uuid4())
        self.role = AgentRole.SUPERVISOR
        self.name = "Supervisor"
        self.description = "Orchestrates workflows and coordinates specialized agents"
        self.status = AgentStatus.IDLE
        self.version = "1.0.0"

        self.registry = registry
        self.communication = communication
        self.validator = AgentValidator()
        self.memory = AgentMemoryManager()
        self.prompt_manager = create_default_templates()

        self._assigned_tasks: dict[str, TaskAssignment] = {}
        self._active_workflows: dict[str, dict[str, Any]] = {}

        logger.info("Supervisor Agent initialized: %s", self.id)

    async def receive_workflow(
        self,
        workflow_id: str,
        workflow_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Receive and analyze a workflow.

        Args:
            workflow_id: Workflow ID.
            workflow_data: Complete workflow data.

        Returns:
            Analysis and execution plan.
        """
        logger.info("Supervisor receiving workflow: %s", workflow_id)

        self._active_workflows[workflow_id] = {
            "data": workflow_data,
            "status": "analyzing",
            "received_at": datetime.now(timezone.utc),
        }

        analysis = self._analyze_workflow(workflow_data)

        self._active_workflows[workflow_id]["status"] = "ready"
        self._active_workflows[workflow_id]["analysis"] = analysis

        self.memory.add_short_term({
            "action": "workflow_received",
            "workflow_id": workflow_id,
            "task_count": len(analysis.get("tasks", [])),
        })

        return analysis

    def _analyze_workflow(self, workflow_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze workflow and determine execution plan.

        Args:
            workflow_data: Workflow data.

        Returns:
            Execution analysis.
        """
        tasks = workflow_data.get("tasks", [])
        required_roles = set()

        role_mapping = {
            "code": AgentRole.SOFTWARE_ENGINEER,
            "test": AgentRole.QA_ENGINEER,
            "review": AgentRole.CODE_REVIEWER,
            "document": AgentRole.TECHNICAL_WRITER,
            "deploy": AgentRole.DEVOPS_ENGINEER,
            "database": AgentRole.DATABASE_ENGINEER,
            "research": AgentRole.RESEARCH_ENGINEER,
        }

        for task in tasks:
            task_type = task.get("type", "").lower()
            for keyword, role in role_mapping.items():
                if keyword in task_type:
                    required_roles.add(role)

        available_agents = {}
        for role in required_roles:
            agents = self.registry.get_agents_by_role(role)
            if agents:
                available_agents[role.value] = [
                    {"id": a.id, "name": a.name} for a in agents
                ]

        execution_order = self._calculate_execution_order(tasks)

        return {
            "required_roles": [r.value for r in required_roles],
            "available_agents": available_agents,
            "execution_order": execution_order,
            "tasks": tasks,
            "estimated_duration": sum(t.get("estimated_duration", 60) for t in tasks),
        }

    def _calculate_execution_order(self, tasks: list[dict[str, Any]]) -> list[list[str]]:
        """Calculate execution order based on dependencies.

        Args:
            tasks: List of tasks.

        Returns:
            Execution layers.
        """
        task_map = {t["id"]: t for t in tasks}
        in_degree = {t["id"]: len(t.get("dependencies", [])) for t in tasks}
        layers = []
        remaining = set(task_map.keys())

        while remaining:
            layer = [tid for tid in remaining if in_degree.get(tid, 0) == 0]
            if not layer:
                break
            layers.append(sorted(layer))
            for tid in layer:
                remaining.discard(tid)
                for other in remaining:
                    if tid in task_map.get(other, {}).get("dependencies", []):
                        in_degree[other] -= 1

        return layers

    async def assign_task(
        self,
        workflow_id: str,
        task: dict[str, Any],
    ) -> TaskAssignment | None:
        """Assign a task to an appropriate agent.

        Args:
            workflow_id: Workflow ID.
            task: Task data.

        Returns:
            Task assignment or None if no agent available.
        """
        required_capabilities = task.get("required_capabilities", [])
        task_type = task.get("type", "")

        candidates = self.registry.find_agents_for_task(
            required_capabilities=required_capabilities,
            task_type=task_type,
        )

        if not candidates:
            logger.warning(
                "No agents available for task: %s (required: %s)",
                task.get("title"),
                required_capabilities,
            )
            return None

        best_agent = candidates[0]

        assignment = TaskAssignment(
            task_id=task["id"],
            workflow_id=workflow_id,
            agent_id=best_agent.id,
            title=task.get("title", "Untitled Task"),
            description=task.get("description", ""),
            context=task.get("context", {}),
            required_capabilities=required_capabilities,
            priority=task.get("priority", "medium"),
            timeout_seconds=task.get("timeout_seconds", 300),
        )

        self._assigned_tasks[task["id"]] = assignment
        self.registry.update_status(best_agent.id, AgentStatus.ASSIGNED)

        self.communication.create_task_assignment(
            supervisor_id=self.id,
            agent_id=best_agent.id,
            task_id=task["id"],
            workflow_id=workflow_id,
            title=assignment.title,
            description=assignment.description,
            context=assignment.context,
            required_capabilities=assignment.required_capabilities,
            priority=assignment.priority,
        )

        self.memory.add_short_term({
            "action": "task_assigned",
            "task_id": task["id"],
            "agent_id": best_agent.id,
            "agent_name": best_agent.name,
        })

        logger.info(
            "Task assigned: %s to %s",
            task.get("title"),
            best_agent.name,
        )

        return assignment

    async def handle_task_result(
        self,
        task_id: str,
        agent_id: str,
        status: str,
        output: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Handle task completion or failure.

        Args:
            task_id: Task ID.
            agent_id: Agent ID.
            status: Result status.
            output: Task output.
            error: Error message if failed.
        """
        assignment = self._assigned_tasks.get(task_id)
        if not assignment:
            return

        self.registry.update_status(agent_id, AgentStatus.IDLE)

        result = {
            "task_id": task_id,
            "agent_id": agent_id,
            "status": status,
            "output": output or {},
            "error": error,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        self.memory.add_task_memory(result)

        self.communication.create_task_result(
            agent_id=agent_id,
            supervisor_id=self.id,
            task_id=task_id,
            status=status,
            output=output,
            error=error,
        )

        logger.info("Task result handled: %s - %s", task_id, status)

    def get_workflow_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Get status of a workflow.

        Args:
            workflow_id: Workflow ID.

        Returns:
            Workflow status or None.
        """
        return self._active_workflows.get(workflow_id)

    def get_assigned_tasks(self) -> list[TaskAssignment]:
        """Get all assigned tasks.

        Returns:
            List of task assignments.
        """
        return list(self._assigned_tasks.values())

    def get_info(self) -> AgentInfo:
        """Get supervisor agent information.

        Returns:
            Agent information.
        """
        return AgentInfo(
            id=self.id,
            role=self.role,
            name=self.name,
            description=self.description,
            status=self.status,
            capabilities=[],
            policies=Policy(),
            memory=self.memory.get_memory(),
            version=self.version,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
