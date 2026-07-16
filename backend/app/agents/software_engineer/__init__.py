"""Software Engineer Agent Module.

The first fully operational AI Employee capable of performing engineering work.
"""

from app.agents.software_engineer.software_engineer import (
    SoftwareEngineerAgent,
    AgentState,
    TaskStatus,
    TaskContext,
)
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

__all__ = [
    "SoftwareEngineerAgent",
    "AgentState",
    "TaskStatus",
    "TaskContext",
    "ContextLoader",
    "RepositoryContext",
    "StyleAnalyzer",
    "StyleProfile",
    "ImplementationPlanner",
    "ImplementationPlan",
    "TaskType",
    "CodeGenerator",
    "GeneratedCode",
    "DiffGenerator",
    "Diff",
    "ReviewEngine",
    "ReviewResult",
    "ValidationEngine",
    "ValidationResult",
    "CommitSummaryGenerator",
    "CommitSummary",
]
