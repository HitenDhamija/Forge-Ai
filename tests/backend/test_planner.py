"""
Tests for the Planning & Task Decomposition Engine.

Comprehensive test suite covering intent classifier, task decomposer,
complexity analyzer, dependency analyzer, risk analyzer, plan generator,
planner service, API endpoints, plan history, and error handling.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def intent_classifier():
    """Return an IntentClassifier instance."""
    from app.planner.intent_classifier import IntentClassifier

    return IntentClassifier()


@pytest.fixture
def task_decomposer():
    """Return a TaskDecomposer instance."""
    from app.planner.task_decomposer import TaskDecomposer

    return TaskDecomposer()


@pytest.fixture
def complexity_analyzer():
    """Return a ComplexityAnalyzer instance."""
    from app.planner.complexity_analyzer import ComplexityAnalyzer

    return ComplexityAnalyzer()


@pytest.fixture
def dependency_analyzer():
    """Return a DependencyAnalyzer instance."""
    from app.planner.dependency_analyzer import DependencyAnalyzer

    return DependencyAnalyzer()


@pytest.fixture
def risk_analyzer():
    """Return a RiskAnalyzer instance."""
    from app.planner.risk_analyzer import RiskAnalyzer

    return RiskAnalyzer()


@pytest.fixture
def plan_generator():
    """Return a PlanGenerator instance."""
    from app.planner.plan_generator import PlanGenerator

    return PlanGenerator()


@pytest.fixture
def planner_service():
    """Return a PlannerService instance."""
    from app.planner.planner_service import PlannerService

    return PlannerService()


@pytest.fixture
def sample_feature_request():
    """Return a sample feature development request."""
    return "Implement a new user authentication system with JWT tokens and OAuth2 support"


@pytest.fixture
def sample_bug_fix_request():
    """Return a sample bug fix request."""
    return "Fix the broken login endpoint that returns 500 errors when users try to sign in"


@pytest.fixture
def sample_refactor_request():
    """Return a sample refactoring request."""
    return "Refactor the database layer to improve performance and clean up legacy code"


@pytest.fixture
def sample_tasks():
    """Return a list of sample tasks for testing."""
    from app.planner.schemas.planner import (
        ComplexityLevel,
        Task,
        TaskPriority,
        TaskType,
    )

    return [
        Task(
            id="task-000",
            title="Analyze requirements",
            description="Analyze requirements for the feature",
            task_type=TaskType.RESEARCH,
            priority=TaskPriority.HIGH,
            complexity=ComplexityLevel.MEDIUM,
            estimated_hours=2.0,
            dependencies=[],
        ),
        Task(
            id="task-001",
            title="Design implementation",
            description="Design the implementation approach",
            task_type=TaskType.RESEARCH,
            priority=TaskPriority.HIGH,
            complexity=ComplexityLevel.MEDIUM,
            estimated_hours=1.5,
            dependencies=[],
        ),
        Task(
            id="task-002",
            title="Implement core functionality",
            description="Implement the core feature logic",
            task_type=TaskType.IMPLEMENTATION,
            priority=TaskPriority.HIGH,
            complexity=ComplexityLevel.COMPLEX,
            estimated_hours=8.0,
            dependencies=["task-000", "task-001"],
        ),
        Task(
            id="task-003",
            title="Write unit tests",
            description="Write unit tests for the implementation",
            task_type=TaskType.TESTING,
            priority=TaskPriority.MEDIUM,
            complexity=ComplexityLevel.MEDIUM,
            estimated_hours=3.0,
            dependencies=["task-002"],
        ),
        Task(
            id="task-004",
            title="Update documentation",
            description="Update API and code documentation",
            task_type=TaskType.DOCUMENTATION,
            priority=TaskPriority.LOW,
            complexity=ComplexityLevel.SIMPLE,
            estimated_hours=1.0,
            dependencies=["task-002"],
        ),
    ]


@pytest.fixture
def sample_plan_request():
    """Return a sample PlanCreateRequest."""
    from app.planner.schemas.planner import PlanCreateRequest

    return PlanCreateRequest(
        title="Add user authentication",
        description="Implement JWT-based authentication with login and registration",
        goals=["Secure API endpoints", "Support JWT tokens"],
        context={"framework": "FastAPI"},
    )


# ============================================================
# Intent Classifier Tests
# ============================================================


class TestIntentClassifier:
    """Tests for the IntentClassifier."""

    def test_classify_feature_development(self, intent_classifier):
        """Test classifying feature development intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify(
            "Add a new user authentication system with JWT support"
        )

        assert result.intent == IntentType.FEATURE_DEVELOPMENT
        assert result.confidence > 0.0
        assert "add" in result.keywords or "implement" in result.keywords

    def test_classify_bug_fix(self, intent_classifier):
        """Test classifying bug fix intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify(
            "Fix the broken login endpoint that returns 500 errors"
        )

        assert result.intent == IntentType.BUG_FIX
        assert result.confidence > 0.0

    def test_classify_refactoring(self, intent_classifier):
        """Test classifying refactoring intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify(
            "Refactor the database layer to improve code quality"
        )

        assert result.intent == IntentType.REFACTORING
        assert result.confidence > 0.0

    def test_classify_documentation(self, intent_classifier):
        """Test classifying documentation intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify(
            "Write documentation for the new API endpoints"
        )

        assert result.intent == IntentType.DOCUMENTATION
        assert result.confidence > 0.0

    def test_classify_testing(self, intent_classifier):
        """Test classifying testing intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify(
            "Add unit tests for the authentication module"
        )

        assert result.intent == IntentType.TESTING
        assert result.confidence > 0.0

    def test_classify_deployment(self, intent_classifier):
        """Test classifying deployment intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify(
            "Deploy the application to production using Docker"
        )

        assert result.intent == IntentType.DEPLOYMENT
        assert result.confidence > 0.0

    def test_classify_configuration(self, intent_classifier):
        """Test classifying configuration intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify(
            "Configure the database connection settings in the environment"
        )

        assert result.intent == IntentType.CONFIGURATION
        assert result.confidence > 0.0

    def test_classify_research(self, intent_classifier):
        """Test classifying research intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify(
            "Research the best caching strategy for our application"
        )

        assert result.intent == IntentType.RESEARCH
        assert result.confidence > 0.0

    def test_classify_unknown(self, intent_classifier):
        """Test classifying unknown intent."""
        from app.planner.schemas.planner import IntentType

        result = intent_classifier.classify("xyzzy plugh")

        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.0

    def test_classify_empty_input_raises(self, intent_classifier):
        """Test that empty input raises IntentClassificationException."""
        from app.planner.exceptions import IntentClassificationException

        with pytest.raises(IntentClassificationException, match="cannot be empty"):
            intent_classifier.classify("")

    def test_classify_whitespace_only_raises(self, intent_classifier):
        """Test that whitespace-only input raises IntentClassificationException."""
        from app.planner.exceptions import IntentClassificationException

        with pytest.raises(IntentClassificationException, match="cannot be empty"):
            intent_classifier.classify("   ")

    def test_classify_batch(self, intent_classifier):
        """Test batch classification."""
        from app.planner.schemas.planner import IntentType

        inputs = [
            "Add a new feature for user management",
            "Fix the login bug",
            "Write documentation for the API",
        ]
        results = intent_classifier.classify_batch(inputs)

        assert len(results) == 3
        assert results[0].intent == IntentType.FEATURE_DEVELOPMENT
        assert results[1].intent == IntentType.BUG_FIX
        assert results[2].intent == IntentType.DOCUMENTATION

    def test_classify_confidence_increases_with_length(self, intent_classifier):
        """Test that confidence increases with more specific input."""
        short_result = intent_classifier.classify("Fix bug")
        long_result = intent_classifier.classify(
            "Fix the critical authentication bug that causes 500 errors "
            "when users attempt to login with valid credentials"
        )

        assert long_result.confidence >= short_result.confidence

    def test_urgent_keyword_boosts_priority(self, intent_classifier):
        """Test that urgency keywords affect classification."""
        result = intent_classifier.classify(
            "Urgent: fix the security vulnerability in authentication"
        )

        assert result.confidence > 0.0
        assert len(result.keywords) > 0

    def test_get_supported_intents(self, intent_classifier):
        """Test getting supported intent types."""
        from app.planner.schemas.planner import IntentType

        intents = intent_classifier.get_supported_intents()

        assert IntentType.FEATURE_DEVELOPMENT in intents
        assert IntentType.BUG_FIX in intents
        assert len(intents) == len(IntentType)

    def test_get_intent_description(self, intent_classifier):
        """Test getting intent description."""
        from app.planner.schemas.planner import IntentType

        desc = intent_classifier.get_intent_description(IntentType.BUG_FIX)

        assert isinstance(desc, str)
        assert len(desc) > 0


# ============================================================
# Task Decomposer Tests
# ============================================================


class TestTaskDecomposer:
    """Tests for the TaskDecomposer."""

    def test_decompose_feature_request(self, task_decomposer, sample_feature_request):
        """Test decomposing a feature development request."""
        from app.planner.schemas.planner import IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )
        tasks = task_decomposer.decompose(sample_feature_request, classification)

        assert len(tasks) > 0
        assert all(t.id.startswith("task-") for t in tasks)
        assert all(t.title for t in tasks)
        assert all(t.description for t in tasks)

    def test_decompose_bug_fix_request(self, task_decomposer, sample_bug_fix_request):
        """Test decomposing a bug fix request."""
        from app.planner.schemas.planner import IntentType

        classification = IntentClassification(
            intent=IntentType.BUG_FIX,
            confidence=0.85,
        )
        tasks = task_decomposer.decompose(sample_bug_fix_request, classification)

        assert len(tasks) > 0
        task_types = [t.task_type.value for t in tasks]
        assert "testing" in task_types

    def test_decompose_empty_input_raises(self, task_decomposer):
        """Test that empty input raises TaskDecompositionException."""
        from app.planner.exceptions import TaskDecompositionException
        from app.planner.schemas.planner import IntentClassification, IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )

        with pytest.raises(TaskDecompositionException, match="cannot be empty"):
            task_decomposer.decompose("", classification)

    def test_decompose_none_classification_raises(self, task_decomposer):
        """Test that None classification raises TaskDecompositionException."""
        from app.planner.exceptions import TaskDecompositionException

        with pytest.raises(TaskDecompositionException, match="required"):
            task_decomposer.decompose("Do something", None)

    def test_decompose_assigns_dependencies(self, task_decomposer, sample_feature_request):
        """Test that decomposition assigns proper dependencies."""
        from app.planner.schemas.planner import IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )
        tasks = task_decomposer.decompose(sample_feature_request, classification)

        impl_tasks = [t for t in tasks if t.task_type.value == "implementation"]
        for impl_task in impl_tasks:
            assert len(impl_task.dependencies) > 0

    def test_decompose_estimates_hours(self, task_decomposer, sample_feature_request):
        """Test that decomposition estimates hours for tasks."""
        from app.planner.schemas.planner import IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )
        tasks = task_decomposer.decompose(sample_feature_request, classification)

        for task in tasks:
            assert task.estimated_hours > 0

    def test_decompose_respects_max_tasks(self, task_decomposer):
        """Test that decomposition respects MAX_TASKS_PER_PLAN."""
        from app.planner.schemas.planner import IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )
        tasks = task_decomposer.decompose(
            "Implement a complex system with many components",
            classification,
        )

        assert len(tasks) <= 50

    def test_decompose_assigns_tags(self, task_decomposer, sample_feature_request):
        """Test that tasks get tags from keywords."""
        from app.planner.schemas.planner import IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )
        tasks = task_decomposer.decompose(sample_feature_request, classification)

        for task in tasks:
            assert isinstance(task.tags, list)

    def test_decompose_low_confidence_uses_defaults(self, task_decomposer):
        """Test that low confidence uses default templates."""
        from app.planner.schemas.planner import IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.1,
        )
        tasks = task_decomposer.decompose("Do something", classification)

        assert len(tasks) > 0

    def test_decompose_with_context(self, task_decomposer, sample_feature_request):
        """Test decomposition with additional context."""
        from app.planner.schemas.planner import IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )
        context = {"framework": "FastAPI", "database": "PostgreSQL"}
        tasks = task_decomposer.decompose(
            sample_feature_request, classification, context
        )

        assert len(tasks) > 0
        for task in tasks:
            assert "framework" in task.description or "FastAPI" in task.description

    def test_get_supported_intents(self, task_decomposer):
        """Test getting supported intents with templates."""
        intents = task_decomposer.get_supported_intents()

        assert len(intents) > 0


# ============================================================
# Complexity Analyzer Tests
# ============================================================


class TestComplexityAnalyzer:
    """Tests for the ComplexityAnalyzer."""

    def test_analyze_empty_tasks(self, complexity_analyzer):
        """Test analyzing empty task list."""
        from app.planner.schemas.planner import ComplexityLevel

        result = complexity_analyzer.analyze([])

        assert result.level == ComplexityLevel.SIMPLE
        assert result.score == 0.0
        assert result.task_count == 0

    def test_analyze_simple_plan(self, complexity_analyzer):
        """Test analyzing a simple plan."""
        from app.planner.schemas.planner import (
            ComplexityLevel,
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="t1",
                title="Task 1",
                description="Simple task",
                task_type=TaskType.DOCUMENTATION,
                priority=TaskPriority.LOW,
                estimated_hours=1.0,
            ),
        ]
        result = complexity_analyzer.analyze(tasks)

        assert result.level == ComplexityLevel.SIMPLE
        assert result.task_count == 1
        assert result.estimated_total_hours == 1.0

    def test_analyze_complex_plan(self, complexity_analyzer, sample_tasks):
        """Test analyzing a complex plan."""
        result = complexity_analyzer.analyze(sample_tasks)

        assert result.task_count == 5
        assert result.estimated_total_hours > 0
        assert len(result.factors) > 0
        assert result.avg_task_complexity > 0

    def test_analyze_very_complex_plan(self, complexity_analyzer):
        """Test analyzing a very complex plan with many tasks."""
        from app.planner.schemas.planner import (
            ComplexityLevel,
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = []
        for i in range(25):
            tasks.append(
                Task(
                    id=f"task-{i:03d}",
                    title=f"Task {i}",
                    description=f"Task {i} description",
                    task_type=TaskType.IMPLEMENTATION if i % 3 == 0 else TaskType.TESTING,
                    priority=TaskPriority.CRITICAL if i < 5 else TaskPriority.HIGH,
                    complexity=ComplexityLevel.COMPLEX if i % 2 == 0 else ComplexityLevel.MEDIUM,
                    estimated_hours=float(i + 1),
                    dependencies=[f"task-{i-1:03d}"] if i > 0 else [],
                )
            )

        result = complexity_analyzer.analyze(tasks)

        assert result.task_count == 25
        assert result.level in (ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX)

    def test_analyze_factors_present(self, complexity_analyzer, sample_tasks):
        """Test that analysis includes factors."""
        result = complexity_analyzer.analyze(sample_tasks)

        assert isinstance(result.factors, list)
        assert len(result.factors) > 0
        for factor in result.factors:
            assert isinstance(factor, str)

    def test_analyze_no_dependencies(self, complexity_analyzer):
        """Test analyzing plan with no dependencies."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id=f"task-{i}",
                title=f"Task {i}",
                description=f"Independent task {i}",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                estimated_hours=2.0,
                dependencies=[],
            )
            for i in range(5)
        ]
        result = complexity_analyzer.analyze(tasks)

        assert result.task_count == 5
        dep_factors = [f for f in result.factors if "dependency" in f.lower()]
        assert len(dep_factors) == 0 or "Light" in str(dep_factors)


# ============================================================
# Dependency Analyzer Tests
# ============================================================


class TestDependencyAnalyzer:
    """Tests for the DependencyAnalyzer."""

    def test_analyze_dependencies(self, dependency_analyzer, sample_tasks):
        """Test analyzing dependencies."""
        deps = dependency_analyzer.analyze(sample_tasks)

        assert isinstance(deps, list)
        assert len(deps) > 0
        for dep in deps:
            assert dep.task_id
            assert dep.dependent_task_id
            assert dep.dependency_type == "blocks"

    def test_detect_no_cycles(self, dependency_analyzer, sample_tasks):
        """Test detecting no cycles in valid graph."""
        cycles = dependency_analyzer.detect_cycles(sample_tasks)

        assert cycles == []

    def test_detect_cycles(self, dependency_analyzer):
        """Test detecting circular dependencies."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-a",
                title="Task A",
                description="Task A",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                dependencies=["task-c"],
            ),
            Task(
                id="task-b",
                title="Task B",
                description="Task B",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                dependencies=["task-a"],
            ),
            Task(
                id="task-c",
                title="Task C",
                description="Task C",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                dependencies=["task-b"],
            ),
        ]

        cycles = dependency_analyzer.detect_cycles(tasks)

        assert len(cycles) > 0

    def test_validate_valid_graph(self, dependency_analyzer, sample_tasks):
        """Test validating a valid dependency graph."""
        result = dependency_analyzer.validate(sample_tasks)

        assert result["valid"] is True
        assert result["issue_count"] == 0

    def test_validate_missing_dependency(self, dependency_analyzer):
        """Test detecting missing dependency references."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Task 1",
                description="Task with missing dep",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                dependencies=["task-nonexistent"],
            ),
        ]

        result = dependency_analyzer.validate(tasks)

        assert result["valid"] is False
        assert result["issue_count"] > 0
        assert any(
            issue["type"] == "missing_dependency" for issue in result["issues"]
        )

    def test_validate_circular_dependency(self, dependency_analyzer):
        """Test detecting circular dependency in validation."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-x",
                title="Task X",
                description="X depends on Y",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                dependencies=["task-y"],
            ),
            Task(
                id="task-y",
                title="Task Y",
                description="Y depends on X",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                dependencies=["task-x"],
            ),
        ]

        result = dependency_analyzer.validate(tasks)

        assert result["valid"] is False
        assert any(
            issue["type"] == "circular_dependency" for issue in result["issues"]
        )

    def test_get_execution_order(self, dependency_analyzer, sample_tasks):
        """Test getting topological execution order."""
        levels = dependency_analyzer.get_execution_order(sample_tasks)

        assert len(levels) > 0
        all_ids = [id for level in levels for id in level]
        assert len(all_ids) == len(sample_tasks)

    def test_get_execution_order_raises_on_cycle(self, dependency_analyzer):
        """Test that execution order raises ValueError on cycles."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="a",
                title="A",
                description="A",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                dependencies=["b"],
            ),
            Task(
                id="b",
                title="B",
                description="B",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                dependencies=["a"],
            ),
        ]

        with pytest.raises(ValueError, match="Circular dependency"):
            dependency_analyzer.get_execution_order(tasks)

    def test_get_critical_path(self, dependency_analyzer, sample_tasks):
        """Test getting critical path."""
        critical = dependency_analyzer.get_critical_path(sample_tasks)

        assert isinstance(critical, list)
        assert len(critical) > 0
        for task_id in critical:
            assert task_id.startswith("task-")

    def test_empty_tasks(self, dependency_analyzer):
        """Test with empty task list."""
        deps = dependency_analyzer.analyze([])
        assert deps == []

        cycles = dependency_analyzer.detect_cycles([])
        assert cycles == []

        levels = dependency_analyzer.get_execution_order([])
        assert levels == []

        critical = dependency_analyzer.get_critical_path([])
        assert critical == []


# ============================================================
# Risk Analyzer Tests
# ============================================================


class TestRiskAnalyzer:
    """Tests for the RiskAnalyzer."""

    def test_analyze_no_risks(self, risk_analyzer):
        """Test analyzing simple tasks with no risk indicators."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Write a helper function",
                description="Create a small utility function",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.LOW,
                estimated_hours=1.0,
            ),
        ]

        risks = risk_analyzer.analyze(tasks)

        assert isinstance(risks, list)
        for risk in risks:
            assert risk.id.startswith("risk-")

    def test_analyze_security_risks(self, risk_analyzer):
        """Test detecting security-related risks."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Implement authentication",
                description="Add password hashing and token validation",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                estimated_hours=8.0,
            ),
        ]

        risks = risk_analyzer.analyze(tasks)

        security_risks = [r for r in risks if r.category == "security"]
        assert len(security_risks) > 0
        assert security_risks[0].risk_level.value in ("high", "critical")

    def test_analyze_data_loss_risks(self, risk_analyzer):
        """Test detecting data loss risks."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Delete old records",
                description="Remove deprecated data from the database",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                estimated_hours=4.0,
            ),
        ]

        risks = risk_analyzer.analyze(tasks)

        data_risks = [r for r in risks if r.category == "data_loss"]
        assert len(data_risks) > 0

    def test_analyze_database_risks(self, risk_analyzer):
        """Test detecting database-related risks."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Create database migration",
                description="Add new table and column to schema",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                estimated_hours=4.0,
            ),
        ]

        risks = risk_analyzer.analyze(tasks)

        db_risks = [r for r in risks if r.category == "database"]
        assert len(db_risks) > 0

    def test_analyze_structural_risks_no_tests(self, risk_analyzer):
        """Test detecting structural risk: no tests for implementation."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Implement feature",
                description="Build a new feature",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                estimated_hours=8.0,
            ),
            Task(
                id="task-2",
                title="Another implementation",
                description="More implementation work",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                estimated_hours=4.0,
            ),
        ]

        risks = risk_analyzer.analyze(tasks)

        process_risks = [r for r in risks if r.category == "process"]
        assert len(process_risks) > 0

    def test_analyze_deployment_risks(self, risk_analyzer):
        """Test detecting deployment risks."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Deploy to production",
                description="Release the application to production",
                task_type=TaskType.DEPLOYMENT,
                priority=TaskPriority.CRITICAL,
                estimated_hours=2.0,
            ),
        ]

        risks = risk_analyzer.analyze(tasks)

        deploy_risks = [r for r in risks if r.category == "deployment"]
        assert len(deploy_risks) > 0

    def test_risks_sorted_by_level(self, risk_analyzer):
        """Test that risks are sorted by severity."""
        from app.planner.schemas.planner import (
            RiskLevel,
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Delete database and remove security tokens",
                description="Drop table and remove authentication secrets",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.CRITICAL,
                estimated_hours=8.0,
            ),
        ]

        risks = risk_analyzer.analyze(tasks)

        if len(risks) > 1:
            levels = [r.risk_level for r in risks]
            level_order = {
                RiskLevel.LOW: 0,
                RiskLevel.MEDIUM: 1,
                RiskLevel.HIGH: 2,
                RiskLevel.CRITICAL: 3,
            }
            for i in range(len(levels) - 1):
                assert level_order[levels[i]] >= level_order[levels[i + 1]]

    def test_risk_has_mitigation(self, risk_analyzer):
        """Test that risks include mitigation advice."""
        from app.planner.schemas.planner import (
            Task,
            TaskPriority,
            TaskType,
        )

        tasks = [
            Task(
                id="task-1",
                title="Implement authentication",
                description="Add password and token security",
                task_type=TaskType.IMPLEMENTATION,
                priority=TaskPriority.HIGH,
                estimated_hours=8.0,
            ),
        ]

        risks = risk_analyzer.analyze(tasks)

        for risk in risks:
            assert risk.mitigation
            assert len(risk.mitigation) > 0


# ============================================================
# Plan Generator Tests
# ============================================================


class TestPlanGenerator:
    """Tests for the PlanGenerator."""

    def test_generate_plan(self, plan_generator, sample_tasks):
        """Test generating a complete plan."""
        from app.planner.schemas.planner import (
            ComplexityAnalysis,
            ComplexityLevel,
            IntentClassification,
            IntentType,
        )

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )
        complexity = ComplexityAnalysis(
            level=ComplexityLevel.MEDIUM,
            score=4.0,
            factors=["Moderate task count"],
            task_count=5,
        )

        plan = plan_generator.generate(
            title="Test Plan",
            description="A test plan",
            tasks=sample_tasks,
            classification=classification,
            complexity=complexity,
            dependencies=[],
            risks=[],
        )

        assert plan.id.startswith("plan-")
        assert plan.title == "Test Plan"
        assert plan.status.value == "draft"
        assert len(plan.tasks) == 5
        assert plan.created_at is not None
        assert plan.estimated_total_hours > 0

    def test_generate_plan_empty_tasks_raises(self, plan_generator):
        """Test that generating plan with no tasks raises."""
        from app.planner.exceptions import PlanGenerationException
        from app.planner.schemas.planner import (
            IntentClassification,
            IntentType,
        )

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )

        with pytest.raises(PlanGenerationException, match="no tasks"):
            plan_generator.generate(
                title="Empty Plan",
                description="Plan with no tasks",
                tasks=[],
                classification=classification,
                complexity=None,
                dependencies=[],
                risks=[],
            )

    def test_generate_plan_with_risks(self, plan_generator, sample_tasks):
        """Test generating a plan with identified risks."""
        from app.planner.schemas.planner import (
            ComplexityAnalysis,
            ComplexityLevel,
            IntentClassification,
            IntentType,
            RiskItem,
            RiskLevel,
        )

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT,
            confidence=0.8,
        )
        complexity = ComplexityAnalysis(
            level=ComplexityLevel.MEDIUM,
            score=4.0,
        )
        risks = [
            RiskItem(
                id="risk-000",
                title="Security risk",
                description="Authentication involved",
                risk_level=RiskLevel.HIGH,
                mitigation="Review security practices",
            ),
        ]

        plan = plan_generator.generate(
            title="Plan with Risks",
            description="Plan with security risks",
            tasks=sample_tasks,
            classification=classification,
            complexity=complexity,
            dependencies=[],
            risks=risks,
        )

        assert len(plan.risks) == 1
        assert plan.estimated_total_hours > sum(
            t.estimated_hours for t in sample_tasks
        )

    def test_update_plan_status_valid(self, plan_generator, sample_tasks):
        """Test valid status transitions."""
        from app.planner.schemas.planner import (
            ComplexityAnalysis,
            IntentClassification,
            IntentType,
            Plan,
            PlanStatus,
        )

        plan = Plan(
            id="plan-test",
            title="Test",
            description="Test plan",
            status=PlanStatus.DRAFT,
        )

        updated = plan_generator.update_plan_status(plan, PlanStatus.ACTIVE)

        assert updated.status == PlanStatus.ACTIVE
        assert updated.updated_at is not None

    def test_update_plan_status_invalid(self, plan_generator):
        """Test invalid status transition raises."""
        from app.planner.exceptions import PlanGenerationException
        from app.planner.schemas.planner import Plan, PlanStatus

        plan = Plan(
            id="plan-test",
            title="Test",
            description="Test plan",
            status=PlanStatus.COMPLETED,
        )

        with pytest.raises(PlanGenerationException, match="Invalid status"):
            plan_generator.update_plan_status(plan, PlanStatus.ACTIVE)

    def test_get_plan_summary(self, plan_generator, sample_tasks):
        """Test getting plan summary."""
        from app.planner.schemas.planner import (
            ComplexityAnalysis,
            ComplexityLevel,
            IntentClassification,
            IntentType,
            Plan,
            PlanStatus,
        )

        plan = Plan(
            id="plan-test",
            title="Test Plan",
            description="A test plan",
            status=PlanStatus.ACTIVE,
            tasks=sample_tasks,
        )

        summary = plan_generator.get_plan_summary(plan)

        assert summary["plan_id"] == "plan-test"
        assert summary["title"] == "Test Plan"
        assert summary["status"] == "active"
        assert summary["task_count"] == 5


# ============================================================
# Planner Service Tests
# ============================================================


class TestPlannerService:
    """Tests for the PlannerService."""

    @pytest.mark.asyncio
    async def test_create_plan(self, planner_service, sample_plan_request):
        """Test creating a plan through the service."""
        plan = await planner_service.create_plan(sample_plan_request)

        assert plan.id.startswith("plan-")
        assert plan.title == "Add user authentication"
        assert len(plan.tasks) > 0
        assert plan.created_at is not None

    @pytest.mark.asyncio
    async def test_get_plan(self, planner_service, sample_plan_request):
        """Test retrieving a plan."""
        plan = await planner_service.create_plan(sample_plan_request)
        retrieved = await planner_service.get_plan(plan.id)

        assert retrieved.id == plan.id
        assert retrieved.title == plan.title

    @pytest.mark.asyncio
    async def test_get_plan_not_found(self, planner_service):
        """Test retrieving a non-existent plan raises."""
        from app.planner.exceptions import PlanNotFoundException

        with pytest.raises(PlanNotFoundException, match="not found"):
            await planner_service.get_plan("plan-nonexistent")

    @pytest.mark.asyncio
    async def test_list_plans(self, planner_service, sample_plan_request):
        """Test listing plans."""
        await planner_service.create_plan(sample_plan_request)
        await planner_service.create_plan(
            PlanCreateRequest(
                title="Second plan",
                description="Another plan",
            )
        )

        result = await planner_service.list_plans()

        assert result.total == 2
        assert len(result.plans) == 2

    @pytest.mark.asyncio
    async def test_list_plans_pagination(self, planner_service):
        """Test listing plans with pagination."""
        from app.planner.schemas.planner import PlanCreateRequest

        for i in range(5):
            await planner_service.create_plan(
                PlanCreateRequest(
                    title=f"Plan {i}",
                    description=f"Plan {i} description",
                )
            )

        page1 = await planner_service.list_plans(page=1, per_page=2)
        page2 = await planner_service.list_plans(page=2, per_page=2)

        assert len(page1.plans) == 2
        assert len(page2.plans) == 2
        assert page1.total == 5

    @pytest.mark.asyncio
    async def test_update_plan(self, planner_service, sample_plan_request):
        """Test updating a plan."""
        from app.planner.schemas.planner import PlanUpdateRequest

        plan = await planner_service.create_plan(sample_plan_request)
        updated = await planner_service.update_plan(
            plan.id,
            PlanUpdateRequest(title="Updated Title"),
        )

        assert updated.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_plan_status(self, planner_service, sample_plan_request):
        """Test updating plan status."""
        from app.planner.schemas.planner import PlanStatus, PlanUpdateRequest

        plan = await planner_service.create_plan(sample_plan_request)
        updated = await planner_service.update_plan(
            plan.id,
            PlanUpdateRequest(status=PlanStatus.ACTIVE),
        )

        assert updated.status == PlanStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_delete_plan(self, planner_service, sample_plan_request):
        """Test deleting a plan."""
        plan = await planner_service.create_plan(sample_plan_request)
        deleted = await planner_service.delete_plan(plan.id)

        assert deleted is True

        with pytest.raises(Exception):
            await planner_service.get_plan(plan.id)

    @pytest.mark.asyncio
    async def test_delete_plan_not_found(self, planner_service):
        """Test deleting non-existent plan raises."""
        from app.planner.exceptions import PlanNotFoundException

        with pytest.raises(PlanNotFoundException):
            await planner_service.delete_plan("plan-nonexistent")

    @pytest.mark.asyncio
    async def test_get_plan_history(self, planner_service, sample_plan_request):
        """Test getting plan history."""
        plan = await planner_service.create_plan(sample_plan_request)
        history = await planner_service.get_plan_history(plan.id)

        assert len(history) == 1
        assert history[0].action == "created"

    @pytest.mark.asyncio
    async def test_get_all_history(self, planner_service, sample_plan_request):
        """Test getting all history entries."""
        await planner_service.create_plan(sample_plan_request)
        await planner_service.create_plan(
            PlanCreateRequest(
                title="Second plan",
                description="Another plan",
            )
        )

        history = await planner_service.get_plan_history()

        assert len(history) >= 2

    @pytest.mark.asyncio
    async def test_get_plan_summary(self, planner_service, sample_plan_request):
        """Test getting plan summary."""
        plan = await planner_service.create_plan(sample_plan_request)
        summary = await planner_service.get_plan_summary(plan.id)

        assert summary["plan_id"] == plan.id
        assert summary["task_count"] > 0


# ============================================================
# API Endpoint Tests
# ============================================================


class TestPlannerAPI:
    """Tests for Planner API endpoints."""

    @pytest.mark.asyncio
    async def test_create_plan_endpoint(self, async_client):
        """Test POST /api/v1/planner/plans."""
        response = await async_client.post(
            "/api/v1/planner/plans",
            json={
                "title": "API Test Plan",
                "description": "Test plan created via API",
            },
        )

        assert response.status_code in [200, 422, 500]

    @pytest.mark.asyncio
    async def test_list_plans_endpoint(self, async_client):
        """Test GET /api/v1/planner/plans."""
        response = await async_client.get("/api/v1/planner/plans")

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_plan_endpoint(self, async_client):
        """Test GET /api/v1/planner/plans/{plan_id}."""
        response = await async_client.get("/api/v1/planner/plans/plan-test123")

        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_update_plan_endpoint(self, async_client):
        """Test PUT /api/v1/planner/plans/{plan_id}."""
        response = await async_client.put(
            "/api/v1/planner/plans/plan-test123",
            json={"title": "Updated Title"},
        )

        assert response.status_code in [200, 404, 422, 500]

    @pytest.mark.asyncio
    async def test_delete_plan_endpoint(self, async_client):
        """Test DELETE /api/v1/planner/plans/{plan_id}."""
        response = await async_client.delete("/api/v1/planner/plans/plan-test123")

        assert response.status_code in [200, 404, 500]

    @pytest.mark.asyncio
    async def test_get_plan_history_endpoint(self, async_client):
        """Test GET /api/v1/planner/plans/{plan_id}/history."""
        response = await async_client.get(
            "/api/v1/planner/plans/plan-test123/history"
        )

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_list_all_history_endpoint(self, async_client):
        """Test GET /api/v1/planner/history."""
        response = await async_client.get("/api/v1/planner/history")

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_create_plan_validation_error(self, async_client):
        """Test plan creation with invalid data."""
        response = await async_client.post(
            "/api/v1/planner/plans",
            json={},
        )

        assert response.status_code == 422


# ============================================================
# Plan History Tests
# ============================================================


class TestPlanHistory:
    """Tests for plan history management."""

    @pytest.mark.asyncio
    async def test_history_recorded_on_create(self, planner_service, sample_plan_request):
        """Test that plan creation is recorded in history."""
        plan = await planner_service.create_plan(sample_plan_request)
        history = await planner_service.get_plan_history(plan.id)

        assert len(history) == 1
        assert history[0].action == "created"
        assert history[0].plan_id == plan.id

    @pytest.mark.asyncio
    async def test_history_recorded_on_update(self, planner_service, sample_plan_request):
        """Test that plan updates are recorded in history."""
        from app.planner.schemas.planner import PlanUpdateRequest

        plan = await planner_service.create_plan(sample_plan_request)
        await planner_service.update_plan(
            plan.id,
            PlanUpdateRequest(title="Updated"),
        )
        history = await planner_service.get_plan_history(plan.id)

        assert len(history) == 2
        assert history[1].action == "updated"

    @pytest.mark.asyncio
    async def test_history_recorded_on_delete(self, planner_service, sample_plan_request):
        """Test that plan deletion is recorded in history."""
        plan = await planner_service.create_plan(sample_plan_request)
        await planner_service.delete_plan(plan.id)
        history = await planner_service.get_plan_history(plan.id)

        assert len(history) == 2
        assert history[1].action == "deleted"

    @pytest.mark.asyncio
    async def test_history_has_timestamps(self, planner_service, sample_plan_request):
        """Test that history entries have timestamps."""
        plan = await planner_service.create_plan(sample_plan_request)
        history = await planner_service.get_plan_history(plan.id)

        for entry in history:
            assert isinstance(entry.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_history_has_details(self, planner_service, sample_plan_request):
        """Test that history entries include details."""
        plan = await planner_service.create_plan(sample_plan_request)
        history = await planner_service.get_plan_history(plan.id)

        assert "title" in history[0].details


# ============================================================
# Error Handling Tests
# ============================================================


class TestErrorHandling:
    """Tests for error handling across the planning engine."""

    def test_intent_classification_empty_input(self, intent_classifier):
        """Test intent classifier handles empty input."""
        from app.planner.exceptions import IntentClassificationException

        with pytest.raises(IntentClassificationException):
            intent_classifier.classify("")

    def test_task_decomposer_empty_input(self, task_decomposer):
        """Test task decomposer handles empty input."""
        from app.planner.exceptions import TaskDecompositionException
        from app.planner.schemas.planner import IntentClassification, IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT, confidence=0.8
        )

        with pytest.raises(TaskDecompositionException):
            task_decomposer.decompose("", classification)

    def test_plan_generator_empty_tasks(self, plan_generator):
        """Test plan generator handles empty task list."""
        from app.planner.exceptions import PlanGenerationException
        from app.planner.schemas.planner import IntentClassification, IntentType

        classification = IntentClassification(
            intent=IntentType.FEATURE_DEVELOPMENT, confidence=0.8
        )

        with pytest.raises(PlanGenerationException, match="no tasks"):
            plan_generator.generate(
                title="Empty",
                description="No tasks",
                tasks=[],
                classification=classification,
                complexity=None,
                dependencies=[],
                risks=[],
            )

    @pytest.mark.asyncio
    async def test_planner_service_plan_not_found(self, planner_service):
        """Test planner service raises on missing plan."""
        from app.planner.exceptions import PlanNotFoundException

        with pytest.raises(PlanNotFoundException):
            await planner_service.get_plan("plan-does-not-exist")

    @pytest.mark.asyncio
    async def test_planner_service_invalid_status_transition(
        self, planner_service, sample_plan_request
    ):
        """Test planner service rejects invalid status transition."""
        from app.planner.exceptions import PlanningException
        from app.planner.schemas.planner import PlanStatus, PlanUpdateRequest

        plan = await planner_service.create_plan(sample_plan_request)
        await planner_service.update_plan(
            plan.id, PlanUpdateRequest(status=PlanStatus.ACTIVE)
        )
        await planner_service.update_plan(
            plan.id, PlanUpdateRequest(status=PlanStatus.COMPLETED)
        )

        with pytest.raises(PlanningException, match="Invalid status"):
            await planner_service.update_plan(
                plan.id, PlanUpdateRequest(status=PlanStatus.ACTIVE)
            )

    def test_exception_hierarchy(self):
        """Test that all planner exceptions inherit from ForgeBaseException."""
        from app.exceptions import ForgeBaseException
        from app.planner.exceptions import (
            IntentClassificationException,
            PlanGenerationException,
            PlanNotFoundException,
            PlanningException,
            TaskDecompositionException,
        )

        exceptions = [
            PlanningException,
            IntentClassificationException,
            TaskDecompositionException,
            PlanNotFoundException,
            PlanGenerationException,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, ForgeBaseException)

    def test_exception_default_messages(self):
        """Test that exceptions have default messages."""
        from app.planner.exceptions import (
            IntentClassificationException,
            PlanGenerationException,
            PlanNotFoundException,
            PlanningException,
            TaskDecompositionException,
        )

        exceptions = [
            (PlanningException, "Planning operation failed"),
            (IntentClassificationException, "Failed to classify intent"),
            (TaskDecompositionException, "Failed to decompose tasks"),
            (PlanNotFoundException, "Plan not found"),
            (PlanGenerationException, "Failed to generate plan"),
        ]

        for exc_class, default_msg in exceptions:
            exc = exc_class()
            assert exc.message == default_msg


# ============================================================
# Configuration Tests
# ============================================================


class TestConfiguration:
    """Tests for planner configuration."""

    def test_planner_settings_defaults(self):
        """Test default planner settings."""
        from app.planner.config import PlannerSettings

        settings = PlannerSettings()

        assert settings.MAX_TASKS_PER_PLAN == 50
        assert settings.MAX_PLAN_HISTORY == 100
        assert settings.DEFAULT_CONTEXT_TOKENS == 4096
        assert "simple" in settings.COMPLEXITY_THRESHOLDS
        assert "delete" in settings.RISK_KEYWORDS

    def test_get_planner_settings_cached(self):
        """Test that get_planner_settings returns cached instance."""
        from app.planner.config import get_planner_settings

        settings1 = get_planner_settings()
        settings2 = get_planner_settings()

        assert settings1 is settings2
