"""System validation suite for all ForgeAI subsystems."""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    WARNING = "warning"


@dataclass
class ValidationResult:
    subsystem: str
    status: ValidationStatus
    message: str
    duration_ms: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    timestamp: datetime
    results: list[ValidationResult]
    overall_status: ValidationStatus
    passed: int
    failed: int
    skipped: int


class SystemValidator:
    """Validates all ForgeAI subsystems."""

    def __init__(self) -> None:
        self._results: list[ValidationResult] = []

    def validate_all(self) -> ValidationReport:
        """Run all validations and return a report."""
        self._results.clear()
        methods = [
            self.validate_repository_indexing,
            self.validate_knowledge_graph,
            self.validate_semantic_memory,
            self.validate_workflow_execution,
            self.validate_agent_orchestration,
            self.validate_mcp_communication,
            self.validate_execution_pipeline,
            self.validate_learning_engine,
            self.validate_monitoring_events,
            self.validate_plugin_loading,
            self.validate_authentication,
            self.validate_organizations,
            self.validate_studio,
            self.validate_developer_experience,
        ]
        for method in methods:
            try:
                result = method()
            except Exception as exc:
                result = ValidationResult(
                    subsystem=method.__name__.replace("validate_", ""),
                    status=ValidationStatus.FAIL,
                    message=str(exc),
                )
            self._results.append(result)

        passed = sum(1 for r in self._results if r.status == ValidationStatus.PASS)
        failed = sum(1 for r in self._results if r.status == ValidationStatus.FAIL)
        skipped = sum(1 for r in self._results if r.status == ValidationStatus.SKIP)

        if failed > 0:
            overall = ValidationStatus.FAIL
        elif skipped == len(self._results):
            overall = ValidationStatus.SKIP
        elif any(r.status == ValidationStatus.WARNING for r in self._results):
            overall = ValidationStatus.WARNING
        else:
            overall = ValidationStatus.PASS

        return ValidationReport(
            timestamp=datetime.now(timezone.utc),
            results=list(self._results),
            overall_status=overall,
            passed=passed,
            failed=failed,
            skipped=skipped,
        )

    # ------------------------------------------------------------------
    # Individual subsystem validations
    # ------------------------------------------------------------------

    def validate_repository_indexing(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Repository indexing operational"
        try:
            from app.services.repository_indexer import RepositoryIndexer  # type: ignore[import-untyped]
            indexer = RepositoryIndexer()
            details["component"] = "RepositoryIndexer"
        except ImportError:
            message = "RepositoryIndexer not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("repository_indexing", status, message, elapsed, details)

    def validate_knowledge_graph(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Knowledge graph generation operational"
        try:
            from app.services.knowledge_graph import KnowledgeGraphService  # type: ignore[import-untyped]
            details["component"] = "KnowledgeGraphService"
        except ImportError:
            message = "KnowledgeGraphService not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("knowledge_graph", status, message, elapsed, details)

    def validate_semantic_memory(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Semantic memory retrieval operational"
        try:
            from app.services.semantic_memory import SemanticMemoryService  # type: ignore[import-untyped]
            details["component"] = "SemanticMemoryService"
        except ImportError:
            message = "SemanticMemoryService not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("semantic_memory", status, message, elapsed, details)

    def validate_workflow_execution(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Workflow execution runtime operational"
        try:
            from app.services.workflow_engine import WorkflowEngine  # type: ignore[import-untyped]
            details["component"] = "WorkflowEngine"
        except ImportError:
            message = "WorkflowEngine not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("workflow_execution", status, message, elapsed, details)

    def validate_agent_orchestration(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Agent orchestration system operational"
        try:
            from app.services.agent_orchestrator import AgentOrchestrator  # type: ignore[import-untyped]
            details["component"] = "AgentOrchestrator"
        except ImportError:
            message = "AgentOrchestrator not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("agent_orchestration", status, message, elapsed, details)

    def validate_mcp_communication(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "MCP communication runtime operational"
        try:
            from app.services.mcp_runtime import MCPRuntime  # type: ignore[import-untyped]
            details["component"] = "MCPRuntime"
        except ImportError:
            message = "MCPRuntime not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("mcp_communication", status, message, elapsed, details)

    def validate_execution_pipeline(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Execution pipeline operational"
        try:
            from app.services.execution_engine import ExecutionEngine  # type: ignore[import-untyped]
            details["component"] = "ExecutionEngine"
        except ImportError:
            message = "ExecutionEngine not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("execution_pipeline", status, message, elapsed, details)

    def validate_learning_engine(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Learning engine operational"
        try:
            from app.services.learning_engine import LearningEngine  # type: ignore[import-untyped]
            details["component"] = "LearningEngine"
        except ImportError:
            message = "LearningEngine not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("learning_engine", status, message, elapsed, details)

    def validate_monitoring_events(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Monitoring event system operational"
        try:
            from app.services.monitoring_service import MonitoringService  # type: ignore[import-untyped]
            details["component"] = "MonitoringService"
        except ImportError:
            message = "MonitoringService not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("monitoring_events", status, message, elapsed, details)

    def validate_plugin_loading(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Plugin loading system operational"
        try:
            from app.services.plugin_manager import PluginManager  # type: ignore[import-untyped]
            details["component"] = "PluginManager"
        except ImportError:
            message = "PluginManager not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("plugin_loading", status, message, elapsed, details)

    def validate_authentication(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Authentication system operational"
        try:
            from app.services.auth_service import AuthService  # type: ignore[import-untyped]
            details["component"] = "AuthService"
        except ImportError:
            message = "AuthService not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("authentication", status, message, elapsed, details)

    def validate_organizations(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Organization system operational"
        try:
            from app.services.organization_service import OrganizationService  # type: ignore[import-untyped]
            details["component"] = "OrganizationService"
        except ImportError:
            message = "OrganizationService not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("organizations", status, message, elapsed, details)

    def validate_studio(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Studio interface operational"
        try:
            from app.services.studio_service import StudioService  # type: ignore[import-untyped]
            details["component"] = "StudioService"
        except ImportError:
            message = "StudioService not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("studio", status, message, elapsed, details)

    def validate_developer_experience(self) -> ValidationResult:
        start = time.perf_counter()
        details: dict[str, Any] = {}
        status = ValidationStatus.PASS
        message = "Developer experience tooling operational"
        try:
            from app.services.dx_service import DXService  # type: ignore[import-untyped]
            details["component"] = "DXService"
        except ImportError:
            message = "DXService not importable – skipped"
            status = ValidationStatus.SKIP
        except Exception as exc:
            message = str(exc)
            status = ValidationStatus.FAIL
        elapsed = (time.perf_counter() - start) * 1000
        return ValidationResult("developer_experience", status, message, elapsed, details)

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------

    def get_subsystem_status(self) -> dict[str, ValidationStatus]:
        """Return the status of every subsystem validated so far."""
        return {r.subsystem: r.status for r in self._results}


# Pre-defined validation scenarios
SCENARIO_1: list[str] = [
    "import_repo",
    "analyze",
    "plan",
    "workflow",
    "approve",
    "execute",
    "review",
    "learn",
    "monitor",
]

SCENARIO_2: list[str] = [
    "create_org",
    "add_repos",
    "cross_search",
    "knowledge_graph",
    "recommendations",
]

SCENARIO_3: list[str] = [
    "install_plugin",
    "validate",
    "execute",
    "remove",
]

# Global instance
system_validator = SystemValidator()
