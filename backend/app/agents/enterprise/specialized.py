"""Specialized agent implementations for the Enterprise AI Workforce."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.agents.enterprise.memory import AgentMemoryManager
from app.agents.enterprise.schemas import (
    AgentInfo,
    AgentRole,
    AgentStatus,
    Capability,
    Policy,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseSpecializedAgent:
    """Base class for specialized agents."""

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        capabilities: list[Capability],
        policies: Policy | None = None,
    ):
        """Initialize the specialized agent.

        Args:
            role: Agent role.
            name: Agent name.
            description: Agent description.
            capabilities: Agent capabilities.
            policies: Agent policies.
        """
        self.id = str(uuid.uuid4())
        self.role = role
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.capabilities = capabilities
        self.policies = policies or Policy()
        self.memory = AgentMemoryManager()
        self.version = "1.0.0"
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    async def accept_task(self, task_assignment: dict[str, Any]) -> bool:
        """Accept a task assignment.

        Args:
            task_assignment: Task assignment data.

        Returns:
            True if accepted.
        """
        self.status = AgentStatus.ASSIGNED
        self.updated_at = datetime.now(timezone.utc)

        self.memory.update_execution_context({
            "current_task": task_assignment,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info("Agent %s accepted task: %s", self.name, task_assignment.get("title"))
        return True

    async def reject_task(self, task_assignment: dict[str, Any], reason: str) -> str:
        """Reject a task assignment.

        Args:
            task_assignment: Task assignment data.
            reason: Rejection reason.

        Returns:
            Rejection reason.
        """
        logger.info("Agent %s rejected task: %s - %s", self.name, task_assignment.get("title"), reason)
        return reason

    async def start_execution(self) -> None:
        """Start task execution."""
        self.status = AgentStatus.EXECUTING
        self.updated_at = datetime.now(timezone.utc)
        logger.info("Agent %s started execution", self.name)

    async def complete_task(self, output: dict[str, Any]) -> dict[str, Any]:
        """Complete current task.

        Args:
            output: Task output.

        Returns:
            Completion result.
        """
        self.status = AgentStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)

        self.memory.add_task_memory({
            "title": self.memory.get_execution_context().get("current_task", {}).get("title", ""),
            "output": output,
            "status": "completed",
        })

        self.memory.clear_execution_context()
        self.status = AgentStatus.IDLE

        logger.info("Agent %s completed task", self.name)
        return {"status": "completed", "output": output}

    async def fail_task(self, error: str) -> dict[str, Any]:
        """Fail current task.

        Args:
            error: Error message.

        Returns:
            Failure result.
        """
        self.status = AgentStatus.FAILED
        self.updated_at = datetime.now(timezone.utc)

        self.memory.add_task_memory({
            "title": self.memory.get_execution_context().get("current_task", {}).get("title", ""),
            "error": error,
            "status": "failed",
        })

        self.memory.clear_execution_context()
        self.status = AgentStatus.IDLE

        logger.info("Agent %s failed task: %s", self.name, error)
        return {"status": "failed", "error": error}

    def get_info(self) -> AgentInfo:
        """Get agent information.

        Returns:
            Agent information.
        """
        return AgentInfo(
            id=self.id,
            role=self.role,
            name=self.name,
            description=self.description,
            status=self.status,
            capabilities=self.capabilities,
            policies=self.policies,
            memory=self.memory.get_memory(),
            version=self.version,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class SoftwareEngineerAgent(BaseSpecializedAgent):
    """Software Engineer Agent for implementing code."""

    def __init__(self):
        super().__init__(
            role=AgentRole.SOFTWARE_ENGINEER,
            name="Software Engineer",
            description="Implements software features, writes code, and refactors",
            capabilities=[
                Capability(
                    name="code_generation",
                    description="Generate new code",
                    level=8,
                    tools=["write_file", "read_file"],
                    task_types=["implementation", "feature", "refactor"],
                ),
                Capability(
                    name="code_modification",
                    description="Modify existing code",
                    level=8,
                    tools=["edit_file", "read_file"],
                    task_types=["modification", "bugfix", "refactor"],
                ),
                Capability(
                    name="testing",
                    description="Write unit tests",
                    level=7,
                    tools=["write_file", "read_file"],
                    task_types=["testing", "unit_test"],
                ),
            ],
            policies=Policy(
                allowed_tasks=["implementation", "feature", "refactor", "bugfix", "testing"],
                allowed_tools=["read_file", "write_file", "edit_file", "grep_search"],
                max_concurrent_tasks=1,
                max_retries=3,
            ),
        )


class QAEngineerAgent(BaseSpecializedAgent):
    """QA Engineer Agent for quality assurance."""

    def __init__(self):
        super().__init__(
            role=AgentRole.QA_ENGINEER,
            name="QA Engineer",
            description="Reviews code quality, generates tests, validates edge cases",
            capabilities=[
                Capability(
                    name="quality_review",
                    description="Review code quality",
                    level=8,
                    tools=["read_file", "analyze_code"],
                    task_types=["quality_review", "code_review"],
                ),
                Capability(
                    name="test_generation",
                    description="Generate comprehensive tests",
                    level=8,
                    tools=["write_file", "read_file"],
                    task_types=["testing", "test_generation"],
                ),
                Capability(
                    name="edge_case_analysis",
                    description="Identify edge cases",
                    level=7,
                    tools=["read_file", "analyze_code"],
                    task_types=["analysis", "edge_case"],
                ),
            ],
            policies=Policy(
                allowed_tasks=["quality_review", "testing", "test_generation", "analysis"],
                allowed_tools=["read_file", "analyze_code", "grep_search"],
                max_concurrent_tasks=1,
                max_retries=2,
            ),
        )


class CodeReviewerAgent(BaseSpecializedAgent):
    """Code Reviewer Agent for PR reviews."""

    def __init__(self):
        super().__init__(
            role=AgentRole.CODE_REVIEWER,
            name="Code Reviewer",
            description="Reviews code changes, detects bugs and security issues",
            capabilities=[
                Capability(
                    name="code_review",
                    description="Review code changes",
                    level=9,
                    tools=["read_file", "analyze_code"],
                    task_types=["code_review", "pr_review"],
                ),
                Capability(
                    name="security_review",
                    description="Detect security vulnerabilities",
                    level=8,
                    tools=["read_file", "grep_search"],
                    task_types=["security_review", "vulnerability"],
                ),
                Capability(
                    name="architecture_review",
                    description="Review architecture compliance",
                    level=8,
                    tools=["read_file", "grep_search"],
                    task_types=["architecture_review"],
                ),
            ],
            policies=Policy(
                allowed_tasks=["code_review", "security_review", "architecture_review"],
                allowed_tools=["read_file", "analyze_code", "grep_search"],
                max_concurrent_tasks=2,
                max_retries=2,
            ),
        )


class TechnicalWriterAgent(BaseSpecializedAgent):
    """Technical Writer Agent for documentation."""

    def __init__(self):
        super().__init__(
            role=AgentRole.TECHNICAL_WRITER,
            name="Technical Writer",
            description="Generates documentation, README files, and API docs",
            capabilities=[
                Capability(
                    name="documentation",
                    description="Write technical documentation",
                    level=8,
                    tools=["write_file", "read_file"],
                    task_types=["documentation", "readme", "api_docs"],
                ),
                Capability(
                    name="changelog",
                    description="Generate change logs",
                    level=7,
                    tools=["write_file", "read_file"],
                    task_types=["changelog", "release_notes"],
                ),
                Capability(
                    name="migration_guide",
                    description="Write migration guides",
                    level=7,
                    tools=["write_file", "read_file"],
                    task_types=["migration_guide", "upgrade_guide"],
                ),
            ],
            policies=Policy(
                allowed_tasks=["documentation", "readme", "api_docs", "changelog", "migration_guide"],
                allowed_tools=["read_file", "write_file", "grep_search"],
                max_concurrent_tasks=1,
                max_retries=2,
            ),
        )


class DevOpsEngineerAgent(BaseSpecializedAgent):
    """DevOps Engineer Agent for infrastructure."""

    def __init__(self):
        super().__init__(
            role=AgentRole.DEVOPS_ENGINEER,
            name="DevOps Engineer",
            description="Manages Docker, CI/CD, deployment, and monitoring",
            capabilities=[
                Capability(
                    name="docker",
                    description="Manage Docker configurations",
                    level=8,
                    tools=["read_file", "write_file"],
                    task_types=["docker", "containerization"],
                ),
                Capability(
                    name="cicd",
                    description="Set up CI/CD pipelines",
                    level=7,
                    tools=["read_file", "write_file"],
                    task_types=["cicd", "pipeline"],
                ),
                Capability(
                    name="deployment",
                    description="Configure deployment",
                    level=7,
                    tools=["read_file", "write_file"],
                    task_types=["deployment", "infrastructure"],
                ),
            ],
            policies=Policy(
                allowed_tasks=["docker", "cicd", "deployment", "infrastructure", "monitoring"],
                allowed_tools=["read_file", "write_file", "grep_search"],
                max_concurrent_tasks=1,
                max_retries=2,
            ),
        )


class DatabaseEngineerAgent(BaseSpecializedAgent):
    """Database Engineer Agent for database work."""

    def __init__(self):
        super().__init__(
            role=AgentRole.DATABASE_ENGINEER,
            name="Database Engineer",
            description="Designs schemas, plans migrations, optimizes queries",
            capabilities=[
                Capability(
                    name="schema_design",
                    description="Design database schemas",
                    level=8,
                    tools=["read_file", "write_file"],
                    task_types=["schema_design", "database_design"],
                ),
                Capability(
                    name="migration",
                    description="Plan and create migrations",
                    level=8,
                    tools=["read_file", "write_file"],
                    task_types=["migration", "schema_change"],
                ),
                Capability(
                    name="query_optimization",
                    description="Optimize database queries",
                    level=7,
                    tools=["read_file", "analyze_code"],
                    task_types=["optimization", "query_review"],
                ),
            ],
            policies=Policy(
                allowed_tasks=["schema_design", "migration", "optimization", "query_review"],
                allowed_tools=["read_file", "write_file", "analyze_code"],
                max_concurrent_tasks=1,
                max_retries=2,
            ),
        )


class ResearchEngineerAgent(BaseSpecializedAgent):
    """Research Engineer Agent for technical research."""

    def __init__(self):
        super().__init__(
            role=AgentRole.RESEARCH_ENGINEER,
            name="Research Engineer",
            description="Researches frameworks, analyzes dependencies, investigates solutions",
            capabilities=[
                Capability(
                    name="framework_research",
                    description="Research frameworks and libraries",
                    level=8,
                    tools=["read_file", "grep_search", "llm_query"],
                    task_types=["research", "framework_analysis"],
                ),
                Capability(
                    name="dependency_analysis",
                    description="Analyze project dependencies",
                    level=7,
                    tools=["read_file", "grep_search"],
                    task_types=["dependency_analysis", "dependency_review"],
                ),
                Capability(
                    name="architecture_research",
                    description="Research architectural patterns",
                    level=8,
                    tools=["read_file", "grep_search", "llm_query"],
                    task_types=["architecture_research", "pattern_analysis"],
                ),
            ],
            policies=Policy(
                allowed_tasks=["research", "framework_analysis", "dependency_analysis", "architecture_research"],
                allowed_tools=["read_file", "grep_search", "llm_query"],
                max_concurrent_tasks=1,
                max_retries=2,
            ),
        )


def create_all_agents() -> list[BaseSpecializedAgent]:
    """Create instances of all specialized agents.

    Returns:
        List of specialized agent instances.
    """
    return [
        SoftwareEngineerAgent(),
        QAEngineerAgent(),
        CodeReviewerAgent(),
        TechnicalWriterAgent(),
        DevOpsEngineerAgent(),
        DatabaseEngineerAgent(),
        ResearchEngineerAgent(),
    ]
