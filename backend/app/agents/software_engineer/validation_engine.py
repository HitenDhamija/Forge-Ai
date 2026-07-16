"""Validation Engine for Software Engineer Agent.

Validates generated code for syntax, imports, and compatibility.
"""

from typing import Any
from dataclasses import dataclass
import ast
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Validation result."""

    valid: bool
    errors: list[str]
    warnings: list[str]
    syntax_valid: bool
    imports_valid: bool
    compatible: bool


class ValidationEngine:
    """Validates generated code."""

    def __init__(self):
        """Initialize validation engine."""
        self._reserved_words = {
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
            "try", "while", "with", "yield",
        }

    async def validate(
        self,
        code: str,
        file_path: str,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """Validate generated code.

        Args:
            code: Code to validate.
            file_path: Path to file.
            context: Optional context.

        Returns:
            Validation result.
        """
        logger.info("Validating code in %s", file_path)

        errors = []
        warnings = []

        # Syntax validation
        syntax_valid = self._validate_syntax(code, errors)

        # Import validation
        imports_valid = self._validate_imports(code, errors, warnings)

        # Compatibility check
        compatible = self._validate_compatibility(code, context, warnings)

        # Naming validation
        self._validate_naming(code, warnings)

        # Security validation
        self._validate_security(code, errors)

        valid = syntax_valid and imports_valid and compatible and not errors

        result = ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            syntax_valid=syntax_valid,
            imports_valid=imports_valid,
            compatible=compatible,
        )

        logger.info(
            "Validation complete: valid=%s, errors=%d, warnings=%d",
            valid,
            len(errors),
            len(warnings),
        )

        return result

    def _validate_syntax(
        self,
        code: str,
        errors: list[str],
    ) -> bool:
        """Validate Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            errors.append(f"Syntax error: {e.msg} at line {e.lineno}")
            return False

    def _validate_imports(
        self,
        code: str,
        errors: list[str],
        warnings: list[str],
    ) -> bool:
        """Validate imports."""
        valid = True

        # Check for circular imports (simplified)
        import_pattern = re.compile(r"from\s+([\w.]+)\s+import")
        for match in import_pattern.finditer(code):
            module = match.group(1)
            if module.startswith("app."):
                # Would need to check against project structure
                pass

        # Check for missing imports
        used_names = set(re.findall(r"\b([A-Z][a-zA-Z0-9]*)\b", code))
        defined_names = set(re.findall(r"class\s+([A-Z][a-zA-Z0-9]*)", code))

        undefined_names = used_names - defined_names
        if undefined_names and "import" not in code:
            warnings.append(f"Potentially undefined names: {undefined_names}")

        return valid

    def _validate_compatibility(
        self,
        code: str,
        context: dict[str, Any] | None,
        warnings: list[str],
    ) -> bool:
        """Validate compatibility with project."""
        if not context:
            return True

        # Check Python version compatibility
        if "f'" in code or 'f"' in code:
            # f-strings require Python 3.6+
            warnings.append("Uses f-strings (requires Python 3.6+)")

        # Check async usage
        if "async def" in code and "await" not in code:
            warnings.append("Async function without await")

        return True

    def _validate_naming(self, code: str, warnings: list[str]) -> None:
        """Validate naming conventions."""
        # Check for reserved words as variable names
        var_pattern = re.compile(r"(\w+)\s*=")
        for match in var_pattern.finditer(code):
            var_name = match.group(1)
            if var_name in self._reserved_words:
                warnings.append(f"Using reserved word as variable: {var_name}")

    def _validate_security(self, code: str, errors: list[str]) -> None:
        """Validate security."""
        # Check for eval/exec
        if "eval(" in code or "exec(" in code:
            errors.append("Use of eval/exec detected - potential security risk")

        # Check for SQL injection patterns
        if "f'" in code and "SELECT" in code.upper():
            errors.append("Potential SQL injection - use parameterized queries")

        # Check for shell injection
        if "os.system(" in code or "subprocess.call(" in code:
            errors.append("Potential shell injection - use subprocess with list args")
