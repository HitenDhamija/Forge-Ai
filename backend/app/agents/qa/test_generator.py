"""Test Generator for QA Agent.

Generates unit tests, integration tests, and edge cases.
"""

from typing import Any
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class GeneratedTest:
    """Generated test."""

    test_name: str
    test_type: str
    test_code: str
    file_path: str
    description: str
    coverage_target: str


class TestGenerator:
    """Generates tests for code."""

    def __init__(self):
        """Initialize test generator."""
        self._test_templates = {
            "unit": '''
import pytest
from {module} import {class_name}


class Test{class_name}:
    """Tests for {class_name}."""

    def setup_method(self):
        """Set up test fixtures."""
        self.instance = {class_name}()

    {test_methods}
''',
            "integration": '''
import pytest
from {module} import {class_name}


@pytest.mark.integration
class Test{class_name}Integration:
    """Integration tests for {class_name}."""

    {test_methods}
''',
            "edge_case": '''
import pytest
from {module} import {class_name}


class Test{class_name}EdgeCases:
    """Edge case tests for {class_name}."""

    {test_methods}
''',
        }

        self._method_templates = {
            "success": '''
    def test_{method_name}_success(self):
        """Test {method_name} with valid input."""
        result = self.instance.{method_name}({valid_input})
        assert result is not None
''',
            "error": '''
    def test_{method_name}_error(self):
        """Test {method_name} with invalid input."""
        with pytest.raises({exception}):
            self.instance.{method_name}({invalid_input})
''',
            "edge": '''
    def test_{method_name}_edge(self):
        """Test {method_name} with edge case."""
        result = self.instance.{method_name}({edge_input})
        assert result == {expected}
''',
        }

    async def generate(
        self,
        code: str,
        file_path: str,
        context: dict[str, Any] | None = None,
    ) -> list[GeneratedTest]:
        """Generate tests for code.

        Args:
            code: Code to test.
            file_path: Path to source file.
            context: Optional context.

        Returns:
            List of generated tests.
        """
        logger.info("Generating tests for %s", file_path)

        tests = []

        # Extract classes and methods
        classes = self._extract_classes(code)
        functions = self._extract_functions(code)

        # Generate unit tests
        for class_info in classes:
            unit_test = await self._generate_unit_test(class_info, file_path)
            if unit_test:
                tests.append(unit_test)

        # Generate integration tests
        for class_info in classes:
            integration_test = await self._generate_integration_test(class_info, file_path)
            if integration_test:
                tests.append(integration_test)

        # Generate edge case tests
        for class_info in classes:
            edge_test = await self._generate_edge_case_test(class_info, file_path)
            if edge_test:
                tests.append(edge_test)

        logger.info("Generated %d tests", len(tests))
        return tests

    def _extract_classes(self, code: str) -> list[dict[str, Any]]:
        """Extract class information from code."""
        import re

        classes = []
        class_pattern = re.compile(r"class\s+(\w+)\s*(?:\(.*?\))?:")
        
        for match in class_pattern.finditer(code):
            class_name = match.group(1)
            methods = self._extract_methods(code, class_name)
            classes.append({
                "name": class_name,
                "methods": methods,
            })

        return classes

    def _extract_methods(self, code: str, class_name: str) -> list[dict[str, Any]]:
        """Extract methods from class."""
        import re

        methods = []
        method_pattern = re.compile(r"def\s+(\w+)\s*\(([^)]*)\)")
        
        in_class = False
        for line in code.split("\n"):
            if f"class {class_name}" in line:
                in_class = True
            elif in_class and line.strip().startswith("def "):
                match = method_pattern.search(line)
                if match:
                    method_name = match.group(1)
                    params = [p.strip() for p in match.group(2).split(",") if p.strip() != "self"]
                    methods.append({
                        "name": method_name,
                        "params": params,
                    })

        return methods

    def _extract_functions(self, code: str) -> list[dict[str, Any]]:
        """Extract standalone functions."""
        import re

        functions = []
        func_pattern = re.compile(r"^def\s+(\w+)\s*\(([^)]*)\)", re.MULTILINE)
        
        for match in func_pattern.finditer(code):
            func_name = match.group(1)
            if not func_name.startswith("_"):
                params = [p.strip() for p in match.group(2).split(",") if p.strip()]
                functions.append({
                    "name": func_name,
                    "params": params,
                })

        return functions

    async def _generate_unit_test(
        self,
        class_info: dict[str, Any],
        file_path: str,
    ) -> GeneratedTest | None:
        """Generate unit test for class."""
        if not class_info["methods"]:
            return None

        test_methods = []
        for method in class_info["methods"][:5]:
            test_methods.append(
                self._method_templates["success"].format(
                    method_name=method["name"],
                    valid_input="",
                )
            )

        test_code = self._test_templates["unit"].format(
            module=file_path.replace("/", ".").replace(".py", ""),
            class_name=class_info["name"],
            test_methods="\n".join(test_methods),
        )

        test_file = file_path.replace(".py", "_test.py")

        return GeneratedTest(
            test_name=f"test_{class_info['name'].lower()}_unit",
            test_type="unit",
            test_code=test_code,
            file_path=test_file,
            description=f"Unit tests for {class_info['name']}",
            coverage_target="80%",
        )

    async def _generate_integration_test(
        self,
        class_info: dict[str, Any],
        file_path: str,
    ) -> GeneratedTest | None:
        """Generate integration test for class."""
        if not class_info["methods"]:
            return None

        test_methods = []
        for method in class_info["methods"][:3]:
            test_methods.append(
                f'    @pytest.mark.asyncio\n'
                f'    async def test_{method["name"]}_integration(self):\n'
                f'        """Test {method["name"]} integration."""\n'
                f'        # TODO: Add integration test\n'
                f'        pass\n'
            )

        test_code = self._test_templates["integration"].format(
            module=file_path.replace("/", ".").replace(".py", ""),
            class_name=class_info["name"],
            test_methods="\n".join(test_methods),
        )

        test_file = file_path.replace(".py", "_integration_test.py")

        return GeneratedTest(
            test_name=f"test_{class_info['name'].lower()}_integration",
            test_type="integration",
            test_code=test_code,
            file_path=test_file,
            description=f"Integration tests for {class_info['name']}",
            coverage_target="70%",
        )

    async def _generate_edge_case_test(
        self,
        class_info: dict[str, Any],
        file_path: str,
    ) -> GeneratedTest | None:
        """Generate edge case tests for class."""
        if not class_info["methods"]:
            return None

        test_methods = []
        for method in class_info["methods"][:3]:
            test_methods.append(
                f'    def test_{method["name"]}_empty_input(self):\n'
                f'        """Test {method["name"]} with empty input."""\n'
                f'        # TODO: Add edge case test\n'
                f'        pass\n'
                f'\n'
                f'    def test_{method["name"]}_null_input(self):\n'
                f'        """Test {method["name"]} with null input."""\n'
                f'        # TODO: Add edge case test\n'
                f'        pass\n'
            )

        test_code = self._test_templates["edge_case"].format(
            module=file_path.replace("/", ".").replace(".py", ""),
            class_name=class_info["name"],
            test_methods="\n".join(test_methods),
        )

        test_file = file_path.replace(".py", "_edge_test.py")

        return GeneratedTest(
            test_name=f"test_{class_info['name'].lower()}_edge",
            test_type="edge_case",
            test_code=test_code,
            file_path=test_file,
            description=f"Edge case tests for {class_info['name']}",
            coverage_target="60%",
        )
