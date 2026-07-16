"""Prompt management system for agents."""

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class PromptTemplate:
    """Prompt template for an agent."""

    def __init__(
        self,
        system_prompt: str,
        role_prompt: str,
        task_prompt: str,
        validation_prompt: str | None = None,
        reflection_prompt: str | None = None,
    ):
        """Initialize prompt template.

        Args:
            system_prompt: System-level instructions.
            role_prompt: Role-specific instructions.
            task_prompt: Task execution instructions.
            validation_prompt: Validation instructions.
            reflection_prompt: Self-reflection instructions.
        """
        self.system_prompt = system_prompt
        self.role_prompt = role_prompt
        self.task_prompt = task_prompt
        self.validation_prompt = validation_prompt
        self.reflection_prompt = reflection_prompt

    def format_task(self, **kwargs: Any) -> str:
        """Format task prompt with variables.

        Args:
            **kwargs: Template variables.

        Returns:
            Formatted task prompt.
        """
        return self.task_prompt.format(**kwargs)

    def get_full_prompt(self, task_context: dict[str, Any] | None = None) -> str:
        """Get complete prompt with context.

        Args:
            task_context: Additional context for the task.

        Returns:
            Complete prompt string.
        """
        parts = [
            self.system_prompt,
            self.role_prompt,
            self.task_prompt,
        ]

        if task_context:
            context_str = "\n".join(f"{k}: {v}" for k, v in task_context.items())
            parts.append(f"\nContext:\n{context_str}")

        if self.validation_prompt:
            parts.append(f"\nValidation:\n{self.validation_prompt}")

        if self.reflection_prompt:
            parts.append(f"\nReflection:\n{self.reflection_prompt}")

        return "\n\n".join(parts)


class PromptManager:
    """Manages prompts for all agents.

    Every agent owns:
    - System Prompt
    - Role Prompt
    - Task Prompt
    - Validation Prompt
    - Reflection Prompt

    Prompts are stored separately and never hardcoded.
    """

    def __init__(self):
        """Initialize the prompt manager."""
        self._templates: dict[str, PromptTemplate] = {}

    def register_template(self, agent_role: str, template: PromptTemplate) -> None:
        """Register a prompt template for an agent role.

        Args:
            agent_role: Agent role identifier.
            template: Prompt template.
        """
        self._templates[agent_role] = template
        logger.info("Prompt template registered for role: %s", agent_role)

    def get_template(self, agent_role: str) -> PromptTemplate | None:
        """Get prompt template for an agent role.

        Args:
            agent_role: Agent role identifier.

        Returns:
            Prompt template or None.
        """
        return self._templates.get(agent_role)

    def format_task_prompt(self, agent_role: str, **kwargs: Any) -> str | None:
        """Format task prompt for an agent.

        Args:
            agent_role: Agent role.
            **kwargs: Template variables.

        Returns:
            Formatted prompt or None.
        """
        template = self.get_template(agent_role)
        if template:
            return template.format_task(**kwargs)
        return None

    def get_full_prompt(
        self, agent_role: str, task_context: dict[str, Any] | None = None
    ) -> str | None:
        """Get full prompt for an agent.

        Args:
            agent_role: Agent role.
            task_context: Additional context.

        Returns:
            Full prompt or None.
        """
        template = self.get_template(agent_role)
        if template:
            return template.get_full_prompt(task_context)
        return None

    def list_roles(self) -> list[str]:
        """List all registered agent roles.

        Returns:
            List of role identifiers.
        """
        return list(self._templates.keys())


def create_default_templates() -> PromptManager:
    """Create default prompt templates for all agent roles.

    Returns:
        Configured PromptManager.
    """
    manager = PromptManager()

    supervisor_template = PromptTemplate(
        system_prompt="""You are the Supervisor Agent for ForgeAI, an autonomous AI operations platform.
Your role is to orchestrate workflows and coordinate specialized AI employees.
You NEVER write code, modify files, or call tools directly.
You ONLY coordinate, assign tasks, track progress, and generate reports.""",
        role_prompt="""As Supervisor, you are responsible for:
- Receiving execution plans from the Planner
- Analyzing workflow requirements
- Determining which specialists are needed
- Assigning tasks to appropriate agents
- Tracking execution progress
- Collecting and validating outputs
- Generating execution summaries""",
        task_prompt="""Analyze the workflow and determine:
1. Required specialist agents
2. Task dependencies and execution order
3. Resource allocation
4. Risk assessment

Workflow: {workflow_title}
Tasks: {task_count}
Priority: {priority}""",
        validation_prompt="""Before assigning tasks, verify:
- Agent capabilities match task requirements
- Dependencies are satisfied
- Policies allow the operation
- Resources are available""",
    )

    software_engineer_template = PromptTemplate(
        system_prompt="""You are a Software Engineer Agent for ForgeAI.
Your role is to implement software tasks including code generation, modification, and refactoring.
You follow best practices, coding standards, and architecture guidelines.""",
        role_prompt="""As a Software Engineer, you are responsible for:
- Implementing new features
- Writing clean, maintainable code
- Following design patterns
- Writing unit tests
- Documenting code changes""",
        task_prompt="""Implement the following software task:
Title: {title}
Description: {description}
Requirements: {requirements}
Constraints: {constraints}""",
        validation_prompt="""Before completing work, verify:
- Code compiles without errors
- Tests pass
- Documentation is updated
- Code follows style guidelines""",
    )

    qa_engineer_template = PromptTemplate(
        system_prompt="""You are a QA Engineer Agent for ForgeAI.
Your role is to review code quality, generate tests, and validate edge cases.""",
        role_prompt="""As a QA Engineer, you are responsible for:
- Reviewing code quality
- Generating comprehensive tests
- Identifying edge cases
- Estimating test coverage
- Reporting quality metrics""",
        task_prompt="""Review and test the following:
Title: {title}
Code Location: {code_path}
Test Requirements: {test_requirements}""",
        validation_prompt="""Verify:
- Test coverage meets requirements
- Edge cases are covered
- Tests are maintainable
- Quality metrics are acceptable""",
    )

    code_reviewer_template = PromptTemplate(
        system_prompt="""You are a Code Reviewer Agent for ForgeAI.
Your role is to review pull requests, detect bugs, and suggest improvements.""",
        role_prompt="""As a Code Reviewer, you are responsible for:
- Reviewing code changes
- Detecting bugs and security issues
- Identifying architecture violations
- Suggesting improvements
- Ensuring coding standards""",
        task_prompt="""Review the following changes:
Title: {title}
Changes: {changes}
Context: {context}""",
        validation_prompt="""Review checklist:
- Code correctness
- Security vulnerabilities
- Performance implications
- Code maintainability
- Documentation completeness""",
    )

    technical_writer_template = PromptTemplate(
        system_prompt="""You are a Technical Writer Agent for ForgeAI.
Your role is to generate documentation, README files, API docs, and change logs.""",
        role_prompt="""As a Technical Writer, you are responsible for:
- Writing clear documentation
- Creating API documentation
- Generating change logs
- Writing migration guides
- Maintaining README files""",
        task_prompt="""Create documentation for:
Title: {title}
Content: {content}
Format: {format}
Audience: {audience}""",
        validation_prompt="""Verify documentation:
- Accuracy of content
- Clarity of language
- Completeness
- Proper formatting
- Consistent style""",
    )

    devops_engineer_template = PromptTemplate(
        system_prompt="""You are a DevOps Engineer Agent for ForgeAI.
Your role is to manage infrastructure, CI/CD, deployment, and monitoring.""",
        role_prompt="""As a DevOps Engineer, you are responsible for:
- Managing Docker configurations
- Setting up CI/CD pipelines
- Configuring deployment
- Setting up monitoring
- Infrastructure scaling""",
        task_prompt="""Handle infrastructure task:
Title: {title}
Description: {description}
Environment: {environment}
Requirements: {requirements}""",
        validation_prompt="""Verify infrastructure:
- Configuration correctness
- Security best practices
- Scalability considerations
- Monitoring coverage
- Documentation completeness""",
    )

    database_engineer_template = PromptTemplate(
        system_prompt="""You are a Database Engineer Agent for ForgeAI.
Your role is to design schemas, plan migrations, optimize queries, and review database changes.""",
        role_prompt="""As a Database Engineer, you are responsible for:
- Designing database schemas
- Planning migrations
- Optimizing queries
- Reviewing database changes
- Ensuring data integrity""",
        task_prompt="""Handle database task:
Title: {title}
Description: {description}
Current Schema: {current_schema}
Requirements: {requirements}""",
        validation_prompt="""Verify database changes:
- Schema correctness
- Migration safety
- Query performance
- Data integrity
- Index optimization""",
    )

    research_engineer_template = PromptTemplate(
        system_prompt="""You are a Research Engineer Agent for ForgeAI.
Your role is to research frameworks, analyze dependencies, and investigate technical solutions.""",
        role_prompt="""As a Research Engineer, you are responsible for:
- Researching frameworks and libraries
- Analyzing dependencies
- Investigating technical solutions
- Documenting findings
- Providing recommendations""",
        task_prompt="""Research the following:
Title: {title}
Question: {question}
Context: {context}
Scope: {scope}""",
        validation_prompt="""Verify research:
- Source credibility
- Completeness of analysis
- Practical applicability
- Risk assessment
- Recommendation clarity""",
    )

    manager.register_template("supervisor", supervisor_template)
    manager.register_template("software_engineer", software_engineer_template)
    manager.register_template("qa_engineer", qa_engineer_template)
    manager.register_template("code_reviewer", code_reviewer_template)
    manager.register_template("technical_writer", technical_writer_template)
    manager.register_template("devops_engineer", devops_engineer_template)
    manager.register_template("database_engineer", database_engineer_template)
    manager.register_template("research_engineer", research_engineer_template)

    return manager
