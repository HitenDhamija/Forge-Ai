"""QA Agent for Quality Assurance Pipeline.

Generates tests and estimates coverage.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime

from app.core.logging import get_logger
from app.agents.qa.test_generator import TestGenerator, GeneratedTest
from app.agents.qa.coverage_estimator import CoverageEstimator, CoverageReport

logger = get_logger(__name__)


class QAStatus(str, Enum):
    """QA status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QAContext:
    """Context for QA process."""

    task_id: str
    repository_id: str
    code: str
    file_path: str
    status: QAStatus = QAStatus.PENDING
    tests: list[GeneratedTest] = field(default_factory=list)
    coverage_report: CoverageReport | None = None
    test_summary: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class QAAgent:
    """Quality Assurance Agent."""

    def __init__(self):
        """Initialize QA agent."""
        self.test_generator = TestGenerator()
        self.coverage_estimator = CoverageEstimator()
        self._processes: dict[str, QAContext] = {}

    async def start_qa(
        self,
        task_id: str,
        repository_id: str,
        code: str,
        file_path: str,
    ) -> QAContext:
        """Start QA process.

        Args:
            task_id: Task identifier.
            repository_id: Repository identifier.
            code: Code to test.
            file_path: Path to source file.

        Returns:
            QA context with results.
        """
        qa_id = str(uuid.uuid4())

        context = QAContext(
            task_id=task_id,
            repository_id=repository_id,
            code=code,
            file_path=file_path,
        )

        self._processes[qa_id] = context

        logger.info(
            "Starting QA: id=%s, task=%s, file=%s",
            qa_id,
            task_id,
            file_path,
        )

        try:
            context.status = QAStatus.IN_PROGRESS

            # Generate tests
            logger.info("Generating tests")
            context.tests = await self.test_generator.generate(
                code=code,
                file_path=file_path,
            )

            # Estimate coverage
            logger.info("Estimating coverage")
            context.coverage_report = await self.coverage_estimator.estimate(
                code=code,
                file_path=file_path,
            )

            # Generate test summary
            context.test_summary = self._generate_test_summary(context)

            context.status = QAStatus.COMPLETED
            context.completed_at = datetime.utcnow()

            logger.info(
                "QA completed: id=%s, tests=%d, coverage=%.1f%%",
                qa_id,
                len(context.tests),
                context.coverage_report.overall_coverage if context.coverage_report else 0,
            )

        except Exception as e:
            logger.error("QA failed: %s", str(e))
            context.status = QAStatus.FAILED
            context.completed_at = datetime.utcnow()

        return context

    def get_process(self, qa_id: str) -> QAContext | None:
        """Get QA process."""
        return self._processes.get(qa_id)

    def list_processes(
        self,
        status: QAStatus | None = None,
    ) -> list[QAContext]:
        """List QA processes."""
        processes = list(self._processes.values())
        if status:
            processes = [p for p in processes if p.status == status]
        return processes

    def _generate_test_summary(self, context: QAContext) -> str:
        """Generate test summary."""
        unit_tests = [t for t in context.tests if t.test_type == "unit"]
        integration_tests = [t for t in context.tests if t.test_type == "integration"]
        edge_tests = [t for t in context.tests if t.test_type == "edge_case"]

        parts = [f"Generated {len(context.tests)} tests:"]
        if unit_tests:
            parts.append(f"- {len(unit_tests)} unit tests")
        if integration_tests:
            parts.append(f"- {len(integration_tests)} integration tests")
        if edge_tests:
            parts.append(f"- {len(edge_tests)} edge case tests")

        if context.coverage_report:
            parts.append(f"Estimated coverage: {context.coverage_report.overall_coverage:.1f}%")

        return " ".join(parts)
