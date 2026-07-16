from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class OnboardingStep:
    id: str
    title: str
    description: str
    order: int
    completed: bool = False
    skippable: bool = True


@dataclass
class OnboardingState:
    user_id: str
    current_step: int = 0
    completed_steps: list[str] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    skipped: bool = False


@dataclass
class Tutorial:
    id: str
    title: str
    description: str
    steps: list[dict[str, str]]
    difficulty: str
    estimated_minutes: int


class OnboardingManager:
    def __init__(self) -> None:
        self._steps: list[OnboardingStep] = [
            OnboardingStep(
                id="welcome",
                title="Welcome to ForgeAI",
                description="Get introduced to the ForgeAI platform and its core capabilities.",
                order=1,
                skippable=False,
            ),
            OnboardingStep(
                id="connect_repo",
                title="Connect Your First Repository",
                description="Link a GitHub repository to enable AI-powered code analysis.",
                order=2,
                skippable=True,
            ),
            OnboardingStep(
                id="explore_memory",
                title="Explore the Memory System",
                description="Learn how ForgeAI remembers context across your projects.",
                order=3,
                skippable=True,
            ),
            OnboardingStep(
                id="run_workflow",
                title="Run a Workflow",
                description="Execute your first AI-assisted workflow on your codebase.",
                order=4,
                skippable=True,
            ),
            OnboardingStep(
                id="inspect_results",
                title="Inspect AI Results",
                description="Review and understand the output from AI agents.",
                order=5,
                skippable=True,
            ),
            OnboardingStep(
                id="invite_team",
                title="Invite Your Team",
                description="Collaborate with your team by sending invites.",
                order=6,
                skippable=True,
            ),
        ]

        self._tutorials: dict[str, Tutorial] = {
            "getting-started": Tutorial(
                id="getting-started",
                title="Getting Started with ForgeAI",
                description="A comprehensive guide to setting up and using ForgeAI for the first time.",
                steps=[
                    {"id": "account", "title": "Create your account", "description": "Sign up and configure your profile."},
                    {"id": "org", "title": "Set up your organization", "description": "Create or join an organization workspace."},
                    {"id": "repo", "title": "Connect a repository", "description": "Link a GitHub repository for AI analysis."},
                    {"id": "first-run", "title": "Run your first agent", "description": "Execute an AI agent on your code."},
                    {"id": "results", "title": "Review results", "description": "Understand and act on AI insights."},
                ],
                difficulty="beginner",
                estimated_minutes=15,
            ),
            "repo-intelligence": Tutorial(
                id="repo-intelligence",
                title="Understanding Repository Intelligence",
                description="Deep dive into how ForgeAI analyzes and understands your codebase.",
                steps=[
                    {"id": "overview", "title": "Repository overview", "description": "How ForgeAI indexes and understands your code."},
                    {"id": "architecture", "title": "Architecture mapping", "description": "Automatic detection of project architecture."},
                    {"id": "dependencies", "title": "Dependency analysis", "description": "Understanding your dependency graph."},
                    {"id": "patterns", "title": "Pattern recognition", "description": "How AI identifies code patterns and conventions."},
                    {"id": "insights", "title": "Generating insights", "description": "Creating actionable insights from your codebase."},
                ],
                difficulty="intermediate",
                estimated_minutes=25,
            ),
            "ai-agents": Tutorial(
                id="ai-agents",
                title="Working with AI Agents",
                description="Learn to configure, run, and collaborate with AI agents.",
                steps=[
                    {"id": "types", "title": "Agent types", "description": "Overview of available agent types and their capabilities."},
                    {"id": "config", "title": "Configuring agents", "description": "Customizing agent behavior and parameters."},
                    {"id": "execute", "title": "Executing agents", "description": "Running agents on specific tasks and code."},
                    {"id": "context", "title": "Providing context", "description": "How to give agents the right context for best results."},
                    {"id": "iterate", "title": "Iterating on results", "description": "Refining agent outputs and building on them."},
                ],
                difficulty="intermediate",
                estimated_minutes=30,
            ),
            "workflows": Tutorial(
                id="workflows",
                title="Building Workflows",
                description="Create automated multi-step AI workflows for your team.",
                steps=[
                    {"id": "basics", "title": "Workflow basics", "description": "Understanding workflows and their components."},
                    {"id": "steps", "title": "Adding steps", "description": "Building workflows with sequential and parallel steps."},
                    {"id": "conditions", "title": "Conditional logic", "description": "Adding branching and conditional execution."},
                    {"id": "triggers", "title": "Setting triggers", "description": "Automating workflows with triggers and schedules."},
                    {"id": "deploy", "title": "Deploying workflows", "description": "Publishing and sharing workflows with your team."},
                ],
                difficulty="advanced",
                estimated_minutes=40,
            ),
        }

        self._states: dict[str, OnboardingState] = {}
        self._tutorial_progress: dict[str, dict[str, Any]] = {}

    def get_steps(self) -> list[OnboardingStep]:
        return sorted(self._steps, key=lambda s: s.order)

    def get_state(self, user_id: str) -> OnboardingState:
        if user_id not in self._states:
            self._states[user_id] = OnboardingState(user_id=user_id)
        return self._states[user_id]

    def start_onboarding(self, user_id: str) -> OnboardingState:
        state = self.get_state(user_id)
        if not state.started_at:
            state.started_at = datetime.utcnow().isoformat()
            state.current_step = 1
        return state

    def complete_step(self, user_id: str, step_id: str) -> OnboardingState:
        state = self.get_state(user_id)
        if step_id not in state.completed_steps:
            state.completed_steps.append(step_id)
        steps = self.get_steps()
        completed_count = len(state.completed_steps)
        if completed_count >= len(steps):
            state.completed_at = datetime.utcnow().isoformat()
            state.current_step = len(steps)
        else:
            for step in steps:
                if step.id not in state.completed_steps:
                    state.current_step = step.order
                    break
        return state

    def skip_onboarding(self, user_id: str) -> OnboardingState:
        state = self.get_state(user_id)
        state.skipped = True
        state.completed_at = datetime.utcnow().isoformat()
        return state

    def is_complete(self, user_id: str) -> bool:
        state = self.get_state(user_id)
        if state.skipped:
            return True
        return len(state.completed_steps) >= len(self._steps)

    def get_progress(self, user_id: str) -> dict:
        state = self.get_state(user_id)
        total = len(self._steps)
        completed = len(state.completed_steps)
        percentage = (completed / total * 100) if total > 0 else 0
        return {
            "total_steps": total,
            "completed_steps": completed,
            "percentage": round(percentage, 1),
            "current_step": state.current_step,
            "skipped": state.skipped,
            "completed": self.is_complete(user_id),
            "next_step": self._steps[state.current_order - 1].id
            if state.current_step <= total and not state.skipped
            else None,
        }

    def get_tutorials(self) -> list[Tutorial]:
        return list(self._tutorials.values())

    def get_tutorial(self, tutorial_id: str) -> Tutorial | None:
        return self._tutorials.get(tutorial_id)

    def start_tutorial(self, user_id: str, tutorial_id: str) -> dict:
        tutorial = self._tutorials.get(tutorial_id)
        if tutorial is None:
            return {"error": f"Tutorial '{tutorial_id}' not found"}
        key = f"{user_id}:{tutorial_id}"
        self._tutorial_progress[key] = {
            "user_id": user_id,
            "tutorial_id": tutorial_id,
            "current_step": 0,
            "completed_steps": [],
            "started_at": datetime.utcnow().isoformat(),
        }
        return {
            "tutorial": {
                "id": tutorial.id,
                "title": tutorial.title,
                "description": tutorial.description,
                "difficulty": tutorial.difficulty,
                "estimated_minutes": tutorial.estimated_minutes,
            },
            "current_step": 0,
            "total_steps": len(tutorial.steps),
            "steps": tutorial.steps,
        }


onboarding_manager = OnboardingManager()
