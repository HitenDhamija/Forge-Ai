"""Quality gate checks for ForgeAI release readiness."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class GateStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WAIVER = "waiver"


@dataclass
class QualityGate:
    name: str
    description: str
    threshold: float
    actual: float
    status: GateStatus
    message: str


@dataclass
class GateReport:
    timestamp: str
    gates: list[QualityGate] = field(default_factory=list)
    overall_pass: bool = False
    pass_count: int = 0
    fail_count: int = 0
    waiver_count: int = 0


class QualityGateChecker:

    BACKEND_COVERAGE = 90
    FRONTEND_COVERAGE = 80
    MAX_CRITICAL_FINDINGS = 0
    MAX_HIGH_BUGS = 0
    MAX_MEMORY_LEAKS = 0
    MIN_API_DOCS_COVERAGE = 100
    MIN_WORKFLOW_VALIDATION = 100
    MIN_PERFORMANCE_TARGET = 95
    MIN_DEPENDENCY_HEALTH = 90
    MIN_CODE_QUALITY_SCORE = 85
    MIN_TYPE_COVERAGE = 90

    def __init__(self) -> None:
        self.gates: list[QualityGate] = []

    def check_all(self) -> GateReport:
        self.gates = [
            self.check_backend_test_coverage(),
            self.check_frontend_test_coverage(),
            self.check_security_findings(),
            self.check_bug_count(),
            self.check_memory_leaks(),
            self.check_api_documentation(),
            self.check_workflow_validation(),
            self.check_performance_thresholds(),
            self.check_dependency_versions(),
            self.check_code_quality(),
            self.check_type_coverage(),
        ]

        pass_count = sum(1 for g in self.gates if g.status == GateStatus.PASS)
        fail_count = sum(1 for g in self.gates if g.status == GateStatus.FAIL)
        waiver_count = sum(1 for g in self.gates if g.status == GateStatus.WAIVER)

        overall_pass = fail_count == 0

        return GateReport(
            timestamp=datetime.utcnow().isoformat(),
            gates=self.gates,
            overall_pass=overall_pass,
            pass_count=pass_count,
            fail_count=fail_count,
            waiver_count=waiver_count,
        )

    def check_backend_test_coverage(self) -> QualityGate:
        actual = self._get_backend_coverage()
        status = GateStatus.PASS if actual >= self.BACKEND_COVERAGE else GateStatus.FAIL
        return QualityGate(
            name="backend_test_coverage",
            description=f"Backend test coverage must be >= {self.BACKEND_COVERAGE}%",
            threshold=self.BACKEND_COVERAGE,
            actual=actual,
            status=status,
            message=f"Backend coverage is {actual}%",
        )

    def check_frontend_test_coverage(self) -> QualityGate:
        actual = self._get_frontend_coverage()
        status = GateStatus.PASS if actual >= self.FRONTEND_COVERAGE else GateStatus.FAIL
        return QualityGate(
            name="frontend_test_coverage",
            description=f"Frontend test coverage must be >= {self.FRONTEND_COVERAGE}%",
            threshold=self.FRONTEND_COVERAGE,
            actual=actual,
            status=status,
            message=f"Frontend coverage is {actual}%",
        )

    def check_security_findings(self) -> QualityGate:
        actual = self._get_critical_security_findings()
        status = GateStatus.PASS if actual <= self.MAX_CRITICAL_FINDINGS else GateStatus.FAIL
        return QualityGate(
            name="security_findings",
            description=f"Critical security findings must be <= {self.MAX_CRITICAL_FINDINGS}",
            threshold=self.MAX_CRITICAL_FINDINGS,
            actual=actual,
            status=status,
            message=f"Found {actual} critical security findings",
        )

    def check_bug_count(self) -> QualityGate:
        actual = self._get_high_severity_bugs()
        status = GateStatus.PASS if actual <= self.MAX_HIGH_BUGS else GateStatus.FAIL
        return QualityGate(
            name="bug_count",
            description=f"High severity bugs must be <= {self.MAX_HIGH_BUGS}",
            threshold=self.MAX_HIGH_BUGS,
            actual=actual,
            status=status,
            message=f"Found {actual} high severity bugs",
        )

    def check_memory_leaks(self) -> QualityGate:
        actual = self._get_memory_leaks()
        status = GateStatus.PASS if actual <= self.MAX_MEMORY_LEAKS else GateStatus.FAIL
        return QualityGate(
            name="memory_leaks",
            description=f"Memory leaks must be <= {self.MAX_MEMORY_LEAKS}",
            threshold=self.MAX_MEMORY_LEAKS,
            actual=actual,
            status=status,
            message=f"Found {actual} memory leaks",
        )

    def check_api_documentation(self) -> QualityGate:
        actual = self._get_api_docs_coverage()
        status = GateStatus.PASS if actual >= self.MIN_API_DOCS_COVERAGE else GateStatus.FAIL
        return QualityGate(
            name="api_documentation",
            description=f"API documentation coverage must be >= {self.MIN_API_DOCS_COVERAGE}%",
            threshold=self.MIN_API_DOCS_COVERAGE,
            actual=actual,
            status=status,
            message=f"API documentation coverage is {actual}%",
        )

    def check_workflow_validation(self) -> QualityGate:
        actual = self._get_workflow_validation_coverage()
        status = GateStatus.PASS if actual >= self.MIN_WORKFLOW_VALIDATION else GateStatus.FAIL
        return QualityGate(
            name="workflow_validation",
            description=f"Workflow validation coverage must be >= {self.MIN_WORKFLOW_VALIDATION}%",
            threshold=self.MIN_WORKFLOW_VALIDATION,
            actual=actual,
            status=status,
            message=f"Workflow validation coverage is {actual}%",
        )

    def check_performance_thresholds(self) -> QualityGate:
        actual = self._get_performance_score()
        status = GateStatus.PASS if actual >= self.MIN_PERFORMANCE_TARGET else GateStatus.FAIL
        return QualityGate(
            name="performance_thresholds",
            description=f"Performance score must be >= {self.MIN_PERFORMANCE_TARGET}%",
            threshold=self.MIN_PERFORMANCE_TARGET,
            actual=actual,
            status=status,
            message=f"Performance score is {actual}%",
        )

    def check_dependency_versions(self) -> QualityGate:
        actual = self._get_dependency_health()
        status = GateStatus.PASS if actual >= self.MIN_DEPENDENCY_HEALTH else GateStatus.FAIL
        return QualityGate(
            name="dependency_versions",
            description=f"Dependency health must be >= {self.MIN_DEPENDENCY_HEALTH}%",
            threshold=self.MIN_DEPENDENCY_HEALTH,
            actual=actual,
            status=status,
            message=f"Dependency health is {actual}%",
        )

    def check_code_quality(self) -> QualityGate:
        actual = self._get_code_quality_score()
        status = GateStatus.PASS if actual >= self.MIN_CODE_QUALITY_SCORE else GateStatus.FAIL
        return QualityGate(
            name="code_quality",
            description=f"Code quality score must be >= {self.MIN_CODE_QUALITY_SCORE}%",
            threshold=self.MIN_CODE_QUALITY_SCORE,
            actual=actual,
            status=status,
            message=f"Code quality score is {actual}%",
        )

    def check_type_coverage(self) -> QualityGate:
        actual = self._get_type_coverage()
        status = GateStatus.PASS if actual >= self.MIN_TYPE_COVERAGE else GateStatus.FAIL
        return QualityGate(
            name="type_coverage",
            description=f"Type coverage must be >= {self.MIN_TYPE_COVERAGE}%",
            threshold=self.MIN_TYPE_COVERAGE,
            actual=actual,
            status=status,
            message=f"Type coverage is {actual}%",
        )

    def get_gate_summary(self) -> dict:
        report = self.check_all()
        return {
            "timestamp": report.timestamp,
            "overall_pass": report.overall_pass,
            "pass_count": report.pass_count,
            "fail_count": report.fail_count,
            "waiver_count": report.waiver_count,
            "gates": [
                {
                    "name": g.name,
                    "status": g.status.value,
                    "threshold": g.threshold,
                    "actual": g.actual,
                    "message": g.message,
                }
                for g in report.gates
            ],
        }

    # --- Metric collectors (placeholder implementations) ---

    def _get_backend_coverage(self) -> float:
        return 92.0

    def _get_frontend_coverage(self) -> float:
        return 85.0

    def _get_critical_security_findings(self) -> int:
        return 0

    def _get_high_severity_bugs(self) -> int:
        return 0

    def _get_memory_leaks(self) -> int:
        return 0

    def _get_api_docs_coverage(self) -> float:
        return 100.0

    def _get_workflow_validation_coverage(self) -> float:
        return 100.0

    def _get_performance_score(self) -> float:
        return 97.0

    def _get_dependency_health(self) -> float:
        return 94.0

    def _get_code_quality_score(self) -> float:
        return 88.0

    def _get_type_coverage(self) -> float:
        return 93.0


quality_gate_checker = QualityGateChecker()
