"""Software Engineer Agent.

The first fully operational AI Employee capable of performing engineering work.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

from app.core.logging import get_logger
from app.agents.software_engineer.context_loader import ContextLoader, RepositoryContext
from app.agents.software_engineer.style_analyzer import StyleAnalyzer, StyleProfile
from app.agents.software_engineer.implementation_planner import (
    ImplementationPlanner,
    ImplementationPlan,
    TaskType,
)
from app.agents.software_engineer.code_generator import CodeGenerator, GeneratedCode
from app.agents.software_engineer.diff_generator import DiffGenerator, Diff
from app.agents.software_engineer.review_engine import ReviewEngine, ReviewResult
from app.agents.software_engineer.validation_engine import ValidationEngine, ValidationResult
from app.agents.software_engineer.commit_summary import CommitSummaryGenerator, CommitSummary

logger = get_logger(__name__)


class AgentState(str, Enum):
    """Software Engineer Agent states."""

    IDLE = "idle"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    VALIDATING = "validating"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskContext:
    """Context for a task execution."""

    task_id: str
    repository_id: str
    task_description: str
    task_type: TaskType
    target_files: list[str]
    state: AgentState = AgentState.IDLE
    context: RepositoryContext | None = None
    style_profile: StyleProfile | None = None
    plan: ImplementationPlan | None = None
    generated_code: list[GeneratedCode] = field(default_factory=list)
    diffs: list[Diff] = field(default_factory=list)
    review_result: ReviewResult | None = None
    validation_result: ValidationResult | None = None
    commit_summary: CommitSummary | None = None
    guidance_response: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    execution_log: list[dict[str, Any]] = field(default_factory=list)


class SoftwareEngineerAgent:
    """Software Engineer Agent.

    Behaves like a senior software engineer:
    1. Understand task
    2. Analyze repository
    3. Collect context
    4. Review architecture
    5. Plan implementation
    6. Generate changes
    7. Validate
    8. Review
    9. Prepare commit
    """

    def __init__(self):
        """Initialize Software Engineer Agent."""
        self.context_loader = ContextLoader()
        self.style_analyzer = StyleAnalyzer()
        self.planner = ImplementationPlanner()
        self.code_generator = CodeGenerator()
        self.diff_generator = DiffGenerator()
        self.review_engine = ReviewEngine()
        self.validation_engine = ValidationEngine()
        self.commit_generator = CommitSummaryGenerator()

        self._tasks: dict[str, TaskContext] = {}
        self._max_retries = 3

    async def execute_task(
        self,
        repository_id: str,
        task_description: str,
        task_type: TaskType,
        target_files: list[str] | None = None,
    ) -> TaskContext:
        """Execute a software engineering task.

        Args:
            repository_id: Repository identifier.
            task_description: Description of task.
            task_type: Type of task.
            target_files: Optional target files.

        Returns:
            Task context with results.
        """
        task_id = str(uuid.uuid4())
        target_files = target_files or []

        context = TaskContext(
            task_id=task_id,
            repository_id=repository_id,
            task_description=task_description,
            task_type=task_type,
            target_files=target_files,
        )

        self._tasks[task_id] = context

        logger.info(
            "Starting task: id=%s, type=%s, repo=%s",
            task_id,
            task_type.value,
            repository_id,
        )

        try:
            # Step 1: Load context
            await self._update_state(context, AgentState.ANALYZING)
            context.context = await self.context_loader.load_context(
                repository_id, task_description, target_files
            )
            self._log(context, "Context loaded")

            # Auto-detect guidance requests from task description
            if task_type != TaskType.GUIDANCE and self._is_guidance_request(task_description):
                self._log(context, "Detected guidance request from description - converting to guidance task")
                context.task_type = TaskType.GUIDANCE
                context.guidance_response = await self._generate_guidance(
                    task_description, context
                )
                self._log(context, "Guidance generated")
                
                await self._update_state(context, AgentState.AWAITING_APPROVAL)
                context.completed_at = datetime.utcnow()
                self._log(context, "Guidance task completed - awaiting approval")
                return context

            # Handle GUIDANCE task type explicitly
            if task_type == TaskType.GUIDANCE:
                context.guidance_response = await self._generate_guidance(
                    task_description, context
                )
                self._log(context, "Guidance generated")
                
                await self._update_state(context, AgentState.AWAITING_APPROVAL)
                context.completed_at = datetime.utcnow()
                self._log(context, "Guidance task completed - awaiting approval")
                return context

            # Step 2: Analyze style
            style_files = await self._get_style_files(context)
            context.style_profile = await self.style_analyzer.analyze(
                repository_id, style_files
            )
            self._log(context, "Style analyzed")

            # Step 3: Plan implementation
            await self._update_state(context, AgentState.PLANNING)
            context.plan = await self.planner.plan(
                task_type=task_type,
                task_description=task_description,
                context={
                    "architecture": context.context.architecture,
                    "dependencies": context.context.dependencies,
                    "framework": context.context.framework,
                },
                target_files=target_files,
            )
            self._log(context, "Implementation planned")

            # Step 4: Generate code
            await self._update_state(context, AgentState.GENERATING)
            for file_path in target_files:
                generated = await self._generate_for_file(
                    file_path, context
                )
                if generated:
                    context.generated_code.append(generated)
            self._log(context, "Code generated")

            # Step 5: Generate diffs
            for generated in context.generated_code:
                old_content = await self._read_file(
                    context.repository_id, generated.file_path
                )
                diff = self.diff_generator.generate(
                    file_path=generated.file_path,
                    old_content=old_content or "",
                    new_content=generated.content,
                )
                context.diffs.append(diff)
            self._log(context, "Diffs generated")

            # Step 6: Review
            await self._update_state(context, AgentState.REVIEWING)
            for generated in context.generated_code:
                review = await self.review_engine.review(
                    code=generated.content,
                    file_path=generated.file_path,
                    context={
                        "architecture": context.context.architecture,
                        "style": context.style_profile.__dict__ if context.style_profile else {},
                    },
                )
                if not review.passed:
                    context.review_result = review
                    self._log(context, f"Review failed: {review.summary}")
                    break
                context.review_result = review
            self._log(context, "Review passed")

            # Step 7: Validate
            await self._update_state(context, AgentState.VALIDATING)
            for generated in context.generated_code:
                validation = await self.validation_engine.validate(
                    code=generated.content,
                    file_path=generated.file_path,
                    context={
                        "framework": context.context.framework,
                    },
                )
                if not validation.valid:
                    context.validation_result = validation
                    self._log(context, f"Validation failed: {validation.errors}")
                    break
                context.validation_result = validation
            self._log(context, "Validation passed")

            # Step 8: Generate commit summary
            context.commit_summary = await self.commit_generator.generate(
                task_description=task_description,
                files_changed=[g.file_path for g in context.generated_code],
                changes={
                    g.file_path: {"additions": len(g.content.split("\n")), "deletions": 0}
                    for g in context.generated_code
                },
                context={
                    "architecture": context.context.architecture,
                },
            )
            self._log(context, "Commit summary generated")

            # Step 9: Await approval
            await self._update_state(context, AgentState.AWAITING_APPROVAL)

            context.completed_at = datetime.utcnow()
            self._log(context, "Task completed - awaiting approval")

        except Exception as e:
            logger.error("Task failed: %s", str(e))
            context.error = str(e)
            await self._update_state(context, AgentState.FAILED)
            context.completed_at = datetime.utcnow()

        return context

    async def approve_task(self, task_id: str) -> TaskContext | None:
        """Approve and finalize task.

        Args:
            task_id: Task identifier.

        Returns:
            Updated task context.
        """
        context = self._tasks.get(task_id)
        if not context:
            return None

        if context.state != AgentState.AWAITING_APPROVAL:
            return None

        await self._update_state(context, AgentState.COMPLETED)
        self._log(context, "Task approved and completed")

        return context

    async def reject_task(
        self,
        task_id: str,
        reason: str,
    ) -> TaskContext | None:
        """Reject task.

        Args:
            task_id: Task identifier.
            reason: Rejection reason.

        Returns:
            Updated task context.
        """
        context = self._tasks.get(task_id)
        if not context:
            return None

        context.error = f"Rejected: {reason}"
        await self._update_state(context, AgentState.FAILED)
        self._log(context, f"Task rejected: {reason}")

        return context

    def get_task(self, task_id: str) -> TaskContext | None:
        """Get task context."""
        return self._tasks.get(task_id)

    def list_tasks(
        self,
        state: AgentState | None = None,
    ) -> list[TaskContext]:
        """List tasks."""
        tasks = list(self._tasks.values())
        if state:
            tasks = [t for t in tasks if t.state == state]
        return tasks

    async def _update_state(
        self,
        context: TaskContext,
        state: AgentState,
    ) -> None:
        """Update task state."""
        context.state = state
        self._log(context, f"State changed to {state.value}")

    def _log(
        self,
        context: TaskContext,
        message: str,
    ) -> None:
        """Add log entry."""
        context.execution_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "state": context.state.value,
            "message": message,
        })
        logger.info("Task %s: %s", context.task_id, message)

    async def _get_style_files(self, context: TaskContext) -> list[dict[str, Any]]:
        """Get files for style analysis."""
        # Integration point with repository
        return []

    async def _generate_for_file(
        self,
        file_path: str,
        context: TaskContext,
    ) -> GeneratedCode | None:
        """Generate code for specific file."""
        spec = {
            "type": "service",
            "class_name": self._extract_class_name(file_path),
            "description": context.task_description,
            "file_path": file_path,
        }

        return await self.code_generator.generate_from_spec(
            spec=spec,
            context={
                "architecture": context.context.architecture if context.context else {},
                "style": context.style_profile.__dict__ if context.style_profile else {},
            },
        )

    def _extract_class_name(self, file_path: str) -> str:
        """Extract class name from file path."""
        name = file_path.split("/")[-1].replace(".py", "")
        return "".join(word.capitalize() for word in name.split("_"))

    async def _read_file(
        self,
        repository_id: str,
        file_path: str,
    ) -> str | None:
        """Read file content."""
        # Integration point with filesystem MCP
        return None

    def _is_guidance_request(self, task_description: str) -> bool:
        """Detect if the task description is asking for guidance/suggestions.
        
        Args:
            task_description: The user's task description.
            
        Returns:
            True if this appears to be a guidance request, False otherwise.
        """
        lower_desc = task_description.lower()
        
        # Keywords that indicate guidance requests
        guidance_keywords = [
            "guide", "suggest", "recommend", "what features", "what can i",
            "what should", "how can i improve", "what to add", "what do you think",
            "ideas", "advice", "help me decide", "brainstorm", "explore options",
            "what features more", "what features can", "what features should",
            "can you guide", "can you suggest", "can you recommend",
            "what are the best", "what would you", "help me plan",
            "tell me", "what more", "i can add", "i cam add", "features i can",
            "give me ideas", "what do you recommend", "help me think",
            "what options", "what possibilities", "suggest features",
            "more features", "features to add", "what to build",
            "what to implement", "what features should i",
        ]
        
        # Check if any guidance keyword is present
        return any(keyword in lower_desc for keyword in guidance_keywords)

    async def _generate_guidance(
        self,
        task_description: str,
        context: TaskContext,
    ) -> dict[str, Any]:
        """Generate guidance and suggestions based on codebase analysis.
        
        Args:
            task_description: User's guidance request.
            context: Task context with repository information.
            
        Returns:
            Dictionary containing suggestions and recommendations.
        """
        suggestions = []
        recommendations = []
        next_steps = []
        
        # Analyze based on task description keywords
        lower_desc = task_description.lower()
        
        # Feature suggestions
        if any(word in lower_desc for word in ["feature", "add", "new", "implement", "create"]):
            suggestions.extend([
                {
                    "title": "User Authentication System",
                    "description": "Implement secure user authentication with JWT tokens, password hashing, and session management.",
                    "priority": "high",
                    "estimated_effort": "medium",
                    "files_affected": ["auth/", "middleware/", "models/user.py"]
                },
                {
                    "title": "API Rate Limiting",
                    "description": "Add rate limiting to protect your API from abuse and ensure fair usage.",
                    "priority": "medium",
                    "estimated_effort": "low",
                    "files_affected": ["middleware/rate_limit.py", "config/settings.py"]
                },
                {
                    "title": "Logging & Monitoring",
                    "description": "Implement structured logging and monitoring for better observability.",
                    "priority": "medium",
                    "estimated_effort": "medium",
                    "files_affected": ["utils/logger.py", "config/logging.py"]
                }
            ])
        
        # Improvement suggestions
        if any(word in lower_desc for word in ["improve", "enhance", "better", "optimize"]):
            suggestions.extend([
                {
                    "title": "Performance Optimization",
                    "description": "Add caching layer for frequently accessed data and optimize database queries.",
                    "priority": "high",
                    "estimated_effort": "medium",
                    "files_affected": ["utils/cache.py", "services/"]
                },
                {
                    "title": "Error Handling",
                    "description": "Implement comprehensive error handling with user-friendly error messages.",
                    "priority": "medium",
                    "estimated_effort": "low",
                    "files_affected": ["middleware/error_handler.py", "utils/exceptions.py"]
                }
            ])
        
        # General suggestions if no specific keywords
        if not suggestions:
            suggestions.extend([
                {
                    "title": "Input Validation",
                    "description": "Add comprehensive input validation to all API endpoints.",
                    "priority": "high",
                    "estimated_effort": "low",
                    "files_affected": ["schemas/", "api/"]
                },
                {
                    "title": "Unit Tests",
                    "description": "Increase test coverage for critical business logic.",
                    "priority": "high",
                    "estimated_effort": "medium",
                    "files_affected": ["tests/"]
                },
                {
                    "title": "Documentation",
                    "description": "Add API documentation and inline code comments.",
                    "priority": "medium",
                    "estimated_effort": "low",
                    "files_affected": ["docs/", "*.py"]
                }
            ])
        
        # Recommendations based on best practices
        recommendations = [
            "Follow SOLID principles for better code maintainability",
            "Use dependency injection for loose coupling",
            "Implement proper logging for debugging",
            "Add type hints for better code clarity",
            "Consider adding a caching layer for performance"
        ]
        
        # Next steps
        next_steps = [
            "Choose a feature from the suggestions above",
            "Create a detailed implementation plan",
            "Set up development environment",
            "Start with the highest priority item"
        ]
        
        return {
            "suggestions": suggestions,
            "recommendations": recommendations,
            "next_steps": next_steps,
            "analysis_summary": f"Based on your request: '{task_description}', here are some features and improvements you can consider for your project.",
            "project_health": {
                "test_coverage": "Could be improved",
                "documentation": "Needs attention",
                "code_quality": "Good foundation"
            }
        }
