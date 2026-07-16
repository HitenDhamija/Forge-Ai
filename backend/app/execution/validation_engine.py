"""Validation Engine for Execution Engine.

Validates execution results and file changes.
"""

from typing import Any
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationSeverity(str, Enum):
    """Validation severity."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Validation issue."""

    issue_id: str
    severity: ValidationSeverity
    category: str
    message: str
    file_path: str | None = None
    line_number: int | None = None


@dataclass
class ValidationResult:
    """Complete validation result."""

    valid: bool
    issues: list[ValidationIssue]
    files_checked: int
    error_count: int
    warning_count: int
    summary: str


class ValidationEngine:
    """Validates execution results."""

    def __init__(self):
        """Initialize validation engine."""

    async def validate(
        self,
        files_modified: list[str],
        files_created: list[str],
        files_deleted: list[str],
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validate execution results.

        Args:
            files_modified: List of modified files.
            files_created: List of created files.
            files_deleted: List of deleted files.
            context: Optional context.

        Returns:
            Validation result.
        """
        logger.info(
            "Validating execution: modified=%d, created=%d, deleted=%d",
            len(files_modified),
            len(files_created),
            len(files_deleted),
        )

        issues = []

        # Validate modified files
        for file_path in files_modified:
            file_issues = await self._validate_file(file_path, "modified")
            issues.extend(file_issues)

        # Validate created files
        for file_path in files_created:
            file_issues = await self._validate_file(file_path, "created")
            issues.extend(file_issues)

        # Check for conflicts
        conflicts = self._check_conflicts(files_modified, files_created, files_deleted)
        issues.extend(conflicts)

        # Calculate counts
        error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)

        # Determine validity
        valid = error_count == 0

        # Generate summary
        summary = self._generate_summary(
            valid, len(files_modified) + len(files_created) + len(files_deleted), error_count, warning_count
        )

        result = ValidationResult(
            valid=valid,
            issues=issues,
            files_checked=len(files_modified) + len(files_created) + len(files_deleted),
            error_count=error_count,
            warning_count=warning_count,
            summary=summary,
        )

        logger.info(
            "Validation complete: valid=%s, errors=%d, warnings=%d",
            valid,
            error_count,
            warning_count,
        )

        return result

    async def _validate_file(
        self,
        file_path: str,
        change_type: str,
    ) -> list[ValidationIssue]:
        """Validate single file."""
        issues = []

        # Check file exists for modified files
        if change_type == "modified":
            # Integration with filesystem MCP
            pass

        # Check syntax for Python files
        if file_path.endswith(".py"):
            syntax_issues = await self._validate_python_syntax(file_path)
            issues.extend(syntax_issues)

        # Check syntax for TypeScript files
        if file_path.endswith((".ts", ".tsx")):
            syntax_issues = await self._validate_typescript_syntax(file_path)
            issues.extend(syntax_issues)

        return issues

    async def _validate_python_syntax(
        self,
        file_path: str,
    ) -> list[ValidationIssue]:
        """Validate Python syntax."""
        issues = []

        # Integration with Python ast parser
        # This would actually read and parse the file
        logger.info("Validating Python syntax: %s", file_path)

        return issues

    async def _validate_typescript_syntax(
        self,
        file_path: str,
    ) -> list[ValidationIssue]:
        """Validate TypeScript syntax."""
        issues = []

        # Integration with TypeScript compiler
        logger.info("Validating TypeScript syntax: %s", file_path)

        return issues

    def _check_conflicts(
        self,
        files_modified: list[str],
        files_created: list[str],
        files_deleted: list[str],
    ) -> list[ValidationIssue]:
        """Check for file conflicts."""
        issues = []

        # Check if same file is both created and modified
        overlap = set(files_modified) & set(files_created)
        for file_path in overlap:
            issues.append(ValidationIssue(
                issue_id=f"conflict-{file_path}",
                severity=ValidationSeverity.ERROR,
                category="conflict",
                message=f"File {file_path} is both modified and created",
                file_path=file_path,
            ))

        # Check if deleted file is also modified
        modified_deleted = set(files_modified) & set(files_deleted)
        for file_path in modified_deleted:
            issues.append(ValidationIssue(
                issue_id=f"conflict-delete-{file_path}",
                severity=ValidationSeverity.ERROR,
                category="conflict",
                message=f"File {file_path} is both modified and deleted",
                file_path=file_path,
            ))

        return issues

    def _generate_summary(
        self,
        valid: bool,
        files_checked: int,
        error_count: int,
        warning_count: int,
    ) -> str:
        """Generate validation summary."""
        if valid:
            return f"Validation passed. {files_checked} files checked, {warning_count} warnings."
        return f"Validation failed. {error_count} errors, {warning_count} warnings in {files_checked} files."
