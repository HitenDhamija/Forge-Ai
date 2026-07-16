"""Risk analysis for the Planning Engine."""

from __future__ import annotations

import re

from app.core.logging import get_logger
from app.planner.config import get_planner_settings
from app.planner.schemas.planner import (
    RiskItem,
    RiskLevel,
    Task,
    TaskType,
)

logger = get_logger(__name__)

RISK_CATEGORIES: dict[str, list[str]] = {
    "data_loss": [
        r"\b(delete|remove|drop|truncate|purge|destroy)\b",
        r"\b(data loss|permanent|irreversible)\b",
    ],
    "security": [
        r"\b(security|auth|password|token|secret|credential)\b",
        r"\b(encrypt|decrypt|hash|salt|vulnerability)\b",
    ],
    "breaking_change": [
        r"\b(breaking|backward|compatibility|deprecat)\b",
        r"\b(api change|interface change|schema change)\b",
    ],
    "performance": [
        r"\b(performance|slow|latency|timeout|memory|cpu)\b",
        r"\b(bottleneck|optimization|caching)\b",
    ],
    "database": [
        r"\b(database|migration|schema|table|column|index)\b",
        r"\b(sql|query|orm|relation|foreign key)\b",
    ],
    "deployment": [
        r"\b(deploy|release|production|staging|environment)\b",
        r"\b(docker|kubernetes|ci/cd|pipeline)\b",
    ],
    "complexity": [
        r"\b(complex|complicated|intricate|sophisticated)\b",
        r"\b(many files|large scope|significant change)\b",
    ],
}


class RiskAnalyzer:
    """Analyzes risks associated with a set of tasks.

    Evaluates task content, types, and dependencies to identify
    potential risks and assign severity levels.
    """

    def __init__(self) -> None:
        self._settings = get_planner_settings()
        self._compiled_patterns: dict[str, list[re.Pattern[str]]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile risk pattern regexes."""
        for category, patterns in RISK_CATEGORIES.items():
            self._compiled_patterns[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def analyze(self, tasks: list[Task], context: str = "") -> list[RiskItem]:
        """Analyze risks for a set of tasks.

        Args:
            tasks: List of tasks to analyze.
            context: Optional additional context text.

        Returns:
            List of RiskItem objects.
        """
        risks: list[RiskItem] = []
        risk_id_counter = 0

        keyword_risks = self._analyze_keyword_risks(tasks, context)
        for risk in keyword_risks:
            risk.id = f"risk-{risk_id_counter:03d}"
            risk_id_counter += 1
        risks.extend(keyword_risks)

        structural_risks = self._analyze_structural_risks(tasks)
        for risk in structural_risks:
            risk.id = f"risk-{risk_id_counter:03d}"
            risk_id_counter += 1
        risks.extend(structural_risks)

        type_risks = self._analyze_type_risks(tasks)
        for risk in type_risks:
            risk.id = f"risk-{risk_id_counter:03d}"
            risk_id_counter += 1
        risks.extend(type_risks)

        dependency_risks = self._analyze_dependency_risks(tasks)
        for risk in dependency_risks:
            risk.id = f"risk-{risk_id_counter:03d}"
            risk_id_counter += 1
        risks.extend(dependency_risks)

        risks = self._deduplicate_risks(risks)
        risks.sort(key=lambda r: self._risk_level_order(r.risk_level), reverse=True)

        logger.info("Identified %d risks", len(risks))
        return risks

    def _analyze_keyword_risks(
        self, tasks: list[Task], context: str
    ) -> list[RiskItem]:
        """Analyze risks based on keyword matching."""
        risks: list[RiskItem] = []
        combined_text = " ".join(
            f"{t.title} {t.description}" for t in tasks
        )
        if context:
            combined_text += f" {context}"

        for category, patterns in self._compiled_patterns.items():
            matched_tasks: list[str] = []
            found_keywords: list[str] = []

            for pattern in patterns:
                for task in tasks:
                    task_text = f"{task.title} {task.description}"
                    if pattern.search(task_text):
                        if task.id not in matched_tasks:
                            matched_tasks.append(task.id)
                        matches = pattern.findall(task_text)
                        found_keywords.extend(matches)

            if matched_tasks:
                risk_level = self._calculate_keyword_risk_level(
                    len(matched_tasks), len(tasks), category
                )
                risk = RiskItem(
                    id="",
                    title=f"{category.replace('_', ' ').title()} risk detected",
                    description=(
                        f"Found {len(found_keywords)} risk indicators for "
                        f"{category} across {len(matched_tasks)} task(s)"
                    ),
                    risk_level=risk_level,
                    affected_tasks=matched_tasks,
                    mitigation=self._get_mitigation(category),
                    probability=min(len(found_keywords) * 0.1, 0.9),
                    impact=self._get_category_impact(category),
                    category=category,
                )
                risks.append(risk)

        return risks

    def _analyze_structural_risks(self, tasks: list[Task]) -> list[RiskItem]:
        """Analyze structural risks (scope, complexity)."""
        risks: list[RiskItem] = []

        impl_tasks = [t for t in tasks if t.task_type == TaskType.IMPLEMENTATION]
        test_tasks = [t for t in tasks if t.task_type == TaskType.TESTING]

        if impl_tasks and not test_tasks:
            risks.append(RiskItem(
                id="",
                title="No testing tasks for implementation work",
                description="Implementation tasks exist without corresponding testing tasks",
                risk_level=RiskLevel.MEDIUM,
                affected_tasks=[t.id for t in impl_tasks],
                mitigation="Add testing tasks to verify implementation correctness",
                probability=0.6,
                impact=0.5,
                category="process",
            ))

        high_complexity = [
            t for t in tasks if t.complexity.value in ("complex", "very_complex")
        ]
        if len(high_complexity) > len(tasks) * 0.5:
            risks.append(RiskItem(
                id="",
                title="Majority of tasks are high complexity",
                description=(
                    f"{len(high_complexity)}/{len(tasks)} tasks are complex "
                    f"or very complex"
                ),
                risk_level=RiskLevel.HIGH,
                affected_tasks=[t.id for t in high_complexity],
                mitigation="Consider breaking down complex tasks into smaller units",
                probability=0.7,
                impact=0.7,
                category="complexity",
            ))

        critical_tasks = [t for t in tasks if t.priority.value == "critical"]
        if len(critical_tasks) > 3:
            risks.append(RiskItem(
                id="",
                title="Too many critical priority tasks",
                description=f"{len(critical_tasks)} tasks marked as critical",
                risk_level=RiskLevel.MEDIUM,
                affected_tasks=[t.id for t in critical_tasks],
                mitigation="Re-evaluate task priorities and reduce critical count",
                probability=0.5,
                impact=0.6,
                category="process",
            ))

        return risks

    def _analyze_type_risks(self, tasks: list[Task]) -> list[RiskItem]:
        """Analyze risks from task type composition."""
        risks: list[RiskItem] = []
        type_counts = {}
        for task in tasks:
            type_counts[task.task_type.value] = type_counts.get(task.task_type.value, 0) + 1

        if type_counts.get("deployment", 0) > 0:
            deploy_tasks = [t for t in tasks if t.task_type == TaskType.DEPLOYMENT]
            risks.append(RiskItem(
                id="",
                title="Deployment tasks present",
                description=f"{len(deploy_tasks)} deployment task(s) identified",
                risk_level=RiskLevel.MEDIUM,
                affected_tasks=[t.id for t in deploy_tasks],
                mitigation="Ensure proper staging and rollback procedures",
                probability=0.4,
                impact=0.8,
                category="deployment",
            ))

        if type_counts.get("refactoring", 0) > 2:
            refactor_tasks = [t for t in tasks if t.task_type == TaskType.REFACTORING]
            risks.append(RiskItem(
                id="",
                title="Multiple refactoring tasks",
                description=f"{len(refactor_tasks)} refactoring tasks may compound risk",
                risk_level=RiskLevel.MEDIUM,
                affected_tasks=[t.id for t in refactor_tasks],
                mitigation="Refactor incrementally and ensure test coverage at each step",
                probability=0.5,
                impact=0.6,
                category="complexity",
            ))

        return risks

    def _analyze_dependency_risks(self, tasks: list[Task]) -> list[RiskItem]:
        """Analyze risks from task dependencies."""
        risks: list[RiskItem] = []
        heavy_deps = [t for t in tasks if len(t.dependencies) > 3]

        if heavy_deps:
            risks.append(RiskItem(
                id="",
                title="Tasks with heavy dependencies",
                description=f"{len(heavy_deps)} task(s) depend on 3+ other tasks",
                risk_level=RiskLevel.MEDIUM,
                affected_tasks=[t.id for t in heavy_deps],
                mitigation="Review dependency graph for unnecessary coupling",
                probability=0.4,
                impact=0.5,
                category="complexity",
            ))

        return risks

    def _calculate_keyword_risk_level(
        self, matched_count: int, total_tasks: int, category: str
    ) -> RiskLevel:
        """Calculate risk level from keyword matches."""
        ratio = matched_count / max(total_tasks, 1)

        if category in ("data_loss", "security"):
            if ratio > 0.3 or matched_count > 2:
                return RiskLevel.CRITICAL
            return RiskLevel.HIGH

        if category in ("breaking_change", "database"):
            if ratio > 0.5 or matched_count > 3:
                return RiskLevel.HIGH
            return RiskLevel.MEDIUM

        if ratio > 0.6:
            return RiskLevel.HIGH
        elif ratio > 0.3:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _get_mitigation(self, category: str) -> str:
        """Return mitigation advice for a risk category."""
        mitigations = {
            "data_loss": "Create backups before execution and verify recovery procedures",
            "security": "Conduct security review and follow security best practices",
            "breaking_change": "Version API changes and provide migration path",
            "performance": "Profile before and after changes, set performance budgets",
            "database": "Test migrations on staging data first, create rollback scripts",
            "deployment": "Use staging environment, implement health checks and rollback",
            "complexity": "Break down into smaller, independently testable units",
            "process": "Review process and adjust as needed",
        }
        return mitigations.get(category, "Review and assess impact carefully")

    def _get_category_impact(self, category: str) -> float:
        """Return default impact score for a category."""
        impacts = {
            "data_loss": 0.9,
            "security": 0.9,
            "breaking_change": 0.8,
            "performance": 0.6,
            "database": 0.7,
            "deployment": 0.7,
            "complexity": 0.5,
            "process": 0.4,
        }
        return impacts.get(category, 0.5)

    def _deduplicate_risks(self, risks: list[RiskItem]) -> list[RiskItem]:
        """Remove duplicate risks based on title and category."""
        seen: set[str] = set()
        unique: list[RiskItem] = []
        for risk in risks:
            key = f"{risk.title}:{risk.category}"
            if key not in seen:
                seen.add(key)
                unique.append(risk)
        return unique

    def _risk_level_order(self, level: RiskLevel) -> int:
        """Return numeric order for risk level sorting."""
        return {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3,
        }.get(level, 0)
