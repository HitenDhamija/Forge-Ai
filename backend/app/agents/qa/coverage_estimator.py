"""Coverage Estimator for QA Agent.

Estimates test coverage and identifies gaps.
"""

from typing import Any
from dataclasses import dataclass, field

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CoverageGap:
    """Coverage gap."""

    file_path: str
    uncovered_lines: list[int]
    uncovered_functions: list[str]
    risk_level: str
    recommendation: str


@dataclass
class CoverageReport:
    """Coverage estimation report."""

    overall_coverage: float
    file_coverages: dict[str, float]
    gaps: list[CoverageGap]
    critical_paths: list[str]
    untested_modules: list[str]
    high_risk_modules: list[str]
    summary: str


class CoverageEstimator:
    """Estimates test coverage."""

    def __init__(self):
        """Initialize coverage estimator."""
        self._risk_thresholds = {
            "high": 50,
            "medium": 70,
            "low": 80,
        }

    async def estimate(
        self,
        code: str,
        file_path: str,
        existing_tests: list[str] | None = None,
    ) -> CoverageReport:
        """Estimate test coverage.

        Args:
            code: Source code.
            file_path: Path to source file.
            existing_tests: Optional list of existing tests.

        Returns:
            Coverage report.
        """
        logger.info("Estimating coverage for %s", file_path)

        # Extract code structure
        functions = self._extract_functions(code)
        classes = self._extract_classes(code)
        lines = code.split("\n")

        # Estimate file coverage
        file_coverage = self._estimate_file_coverage(
            functions, classes, lines, existing_tests
        )

        # Find coverage gaps
        gaps = self._find_gaps(
            file_path, functions, classes, lines, existing_tests
        )

        # Identify critical paths
        critical_paths = self._identify_critical_paths(functions, classes)

        # Identify untested modules
        untested = self._identify_untested(functions, existing_tests)

        # Identify high risk modules
        high_risk = self._identify_high_risk(functions, classes)

        # Calculate overall coverage
        overall_coverage = file_coverage

        # Generate summary
        summary = self._generate_summary(
            overall_coverage, gaps, critical_paths, untested
        )

        report = CoverageReport(
            overall_coverage=overall_coverage,
            file_coverages={file_path: file_coverage},
            gaps=gaps,
            critical_paths=critical_paths,
            untested_modules=untested,
            high_risk_modules=high_risk,
            summary=summary,
        )

        logger.info(
            "Coverage estimation complete: %.1f%%, gaps=%d",
            overall_coverage,
            len(gaps),
        )

        return report

    def _extract_functions(self, code: str) -> list[dict[str, Any]]:
        """Extract functions from code."""
        import re

        functions = []
        pattern = re.compile(r"(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)")
        
        for match in pattern.finditer(code):
            name = match.group(1)
            params = [p.strip() for p in match.group(2).split(",")]
            line_num = code[:match.start()].count("\n") + 1
            functions.append({
                "name": name,
                "params": params,
                "line": line_num,
                "is_public": not name.startswith("_"),
            })

        return functions

    def _extract_classes(self, code: str) -> list[dict[str, Any]]:
        """Extract classes from code."""
        import re

        classes = []
        pattern = re.compile(r"class\s+(\w+)\s*(?:\(.*?\))?:")
        
        for match in pattern.finditer(code):
            name = match.group(1)
            line_num = code[:match.start()].count("\n") + 1
            classes.append({
                "name": name,
                "line": line_num,
            })

        return classes

    def _estimate_file_coverage(
        self,
        functions: list[dict[str, Any]],
        classes: list[dict[str, Any]],
        lines: list[str],
        existing_tests: list[str] | None,
    ) -> float:
        """Estimate file coverage percentage."""
        if not functions:
            return 100.0

        tested_count = 0
        for func in functions:
            if self._is_function_tested(func["name"], existing_tests):
                tested_count += 1

        return (tested_count / len(functions)) * 100 if functions else 100.0

    def _is_function_tested(
        self,
        function_name: str,
        existing_tests: list[str] | None,
    ) -> bool:
        """Check if function has tests."""
        if not existing_tests:
            return False

        for test in existing_tests:
            if function_name in test:
                return True
        return False

    def _find_gaps(
        self,
        file_path: str,
        functions: list[dict[str, Any]],
        classes: list[dict[str, Any]],
        lines: list[str],
        existing_tests: list[str] | None,
    ) -> list[CoverageGap]:
        """Find coverage gaps."""
        gaps = []

        uncovered_functions = [
            f["name"] for f in functions
            if not self._is_function_tested(f["name"], existing_tests)
        ]

        if uncovered_functions:
            risk_level = "high" if len(uncovered_functions) > 5 else "medium"
            gaps.append(CoverageGap(
                file_path=file_path,
                uncovered_lines=[],
                uncovered_functions=uncovered_functions,
                risk_level=risk_level,
                recommendation=f"Add tests for: {', '.join(uncovered_functions[:5])}",
            ))

        return gaps

    def _identify_critical_paths(
        self,
        functions: list[dict[str, Any]],
        classes: list[dict[str, Any]],
    ) -> list[str]:
        """Identify critical code paths."""
        critical = []

        # Public methods are critical
        for func in functions:
            if func["is_public"] and not func["name"].startswith("_"):
                critical.append(func["name"])

        return critical[:10]

    def _identify_untested(
        self,
        functions: list[dict[str, Any]],
        existing_tests: list[str] | None,
    ) -> list[str]:
        """Identify untested modules."""
        return [
            f["name"] for f in functions
            if not self._is_function_tested(f["name"], existing_tests)
        ]

    def _identify_high_risk(
        self,
        functions: list[dict[str, Any]],
        classes: list[dict[str, Any]],
    ) -> list[str]:
        """Identify high risk modules."""
        high_risk = []

        # Functions with many parameters are high risk
        for func in functions:
            if len(func["params"]) > 3:
                high_risk.append(func["name"])

        return high_risk

    def _generate_summary(
        self,
        overall_coverage: float,
        gaps: list[CoverageGap],
        critical_paths: list[str],
        untested: list[str],
    ) -> str:
        """Generate coverage summary."""
        parts = [f"Estimated coverage: {overall_coverage:.1f}%."]

        if gaps:
            parts.append(f"{len(gaps)} coverage gaps identified.")
        if critical_paths:
            parts.append(f"{len(critical_paths)} critical paths found.")
        if untested:
            parts.append(f"{len(untested)} untested functions.")

        return " ".join(parts)
