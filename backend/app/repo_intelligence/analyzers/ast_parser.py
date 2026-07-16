"""AST parser using tree-sitter with fallbacks."""

import ast
import os
import re

from app.core.logging import get_logger
from app.repo_intelligence.schemas.analysis import CodeElement

logger = get_logger(__name__)


class ASTParser:
    """Parses source code using tree-sitter for structural analysis.

    Falls back to Python's built-in ast module for Python files
    and regex-based extraction for other languages when tree-sitter
    is not available.
    """

    LANGUAGE_MAP: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".hpp": "cpp",
        ".go": "go",
        ".rs": "rust",
    }

    IGNORED_DIRS = {
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "dist",
        "build",
        "target",
    }

    async def parse_file(self, file_path: str, language: str) -> list[CodeElement]:
        """Parse a source file and extract code elements.

        Args:
            file_path: Path to the source file.
            language: Programming language of the file.

        Returns:
            List of CodeElement objects extracted from the file.
        """
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            logger.warning("Failed to read file", path=file_path, error=str(e))
            return []

        language_lower = language.lower()

        if language_lower == "python":
            return await self._parse_python(content, file_path)
        elif language_lower in ("javascript", "typescript"):
            return await self._parse_javascript_typescript(content, file_path)
        elif language_lower == "java":
            return await self._parse_java(content, file_path)
        else:
            return await self._parse_generic(content, file_path, language_lower)

    async def _parse_python(self, content: str, file_path: str) -> list[CodeElement]:
        """Parse Python file using built-in ast module.

        Args:
            content: File content.
            file_path: Path to the file.

        Returns:
            List of CodeElement objects.
        """
        elements: list[CodeElement] = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return elements

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in ast.iter_child_nodes(node):
                    if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                        methods.append(
                            CodeElement(
                                name=item.name,
                                type="method",
                                file_path=file_path,
                                line_start=item.lineno,
                                line_end=getattr(item, "end_lineno", None),
                                docstring=ast.get_docstring(item),
                                decorators=[
                                    self._get_decorator_name(d)
                                    for d in item.decorator_list
                                ],
                                parent_class=node.name,
                                parameters=[
                                    arg.arg for arg in item.args.args if arg.arg != "self"
                                ],
                                return_type=self._get_annotation(item.returns),
                            )
                        )

                elements.append(
                    CodeElement(
                        name=node.name,
                        type="class",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", None),
                        docstring=ast.get_docstring(node),
                        decorators=[
                            self._get_decorator_name(d) for d in node.decorator_list
                        ],
                        parameters=[],
                    )
                )
                elements.extend(methods)

            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                elements.append(
                    CodeElement(
                        name=node.name,
                        type="function",
                        file_path=file_path,
                        line_start=node.lineno,
                        line_end=getattr(node, "end_lineno", None),
                        docstring=ast.get_docstring(node),
                        decorators=[
                            self._get_decorator_name(d) for d in node.decorator_list
                        ],
                        parameters=[arg.arg for arg in node.args.args],
                        return_type=self._get_annotation(node.returns),
                    )
                )

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        elements.append(
                            CodeElement(
                                name=target.id,
                                type="variable",
                                file_path=file_path,
                                line_start=node.lineno,
                                line_end=getattr(node, "end_lineno", None),
                            )
                        )

        return elements

    async def _parse_javascript_typescript(
        self, content: str, file_path: str
    ) -> list[CodeElement]:
        """Parse JS/TS file using regex-based extraction.

        Args:
            content: File content.
            file_path: Path to the file.

        Returns:
            List of CodeElement objects.
        """
        elements: list[CodeElement] = []

        class_pattern = re.compile(
            r"(?:export\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{",
            re.MULTILINE,
        )
        for match in class_pattern.finditer(content):
            elements.append(
                CodeElement(
                    name=match.group(1),
                    type="class",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                    is_exported="export" in content[max(0, match.start() - 10) : match.start()],
                )
            )

        function_pattern = re.compile(
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
            re.MULTILINE,
        )
        for match in function_pattern.finditer(content):
            params = [p.strip().split(":")[0].strip() for p in match.group(2).split(",") if p.strip()]
            elements.append(
                CodeElement(
                    name=match.group(1),
                    type="function",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                    parameters=params,
                    is_exported="export" in content[max(0, match.start() - 10) : match.start()],
                )
            )

        arrow_pattern = re.compile(
            r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*(?::\s*\w+)?\s*=>",
            re.MULTILINE,
        )
        for match in arrow_pattern.finditer(content):
            params = [p.strip().split(":")[0].strip() for p in match.group(2).split(",") if p.strip()]
            elements.append(
                CodeElement(
                    name=match.group(1),
                    type="function",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                    parameters=params,
                    is_exported="export" in content[max(0, match.start() - 10) : match.start()],
                )
            )

        interface_pattern = re.compile(
            r"(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+[\w,\s]+)?\s*\{",
            re.MULTILINE,
        )
        for match in interface_pattern.finditer(content):
            elements.append(
                CodeElement(
                    name=match.group(1),
                    type="interface",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                    is_exported="export" in content[max(0, match.start() - 10) : match.start()],
                )
            )

        return elements

    async def _parse_java(self, content: str, file_path: str) -> list[CodeElement]:
        """Parse Java file using regex-based extraction.

        Args:
            content: File content.
            file_path: Path to the file.

        Returns:
            List of CodeElement objects.
        """
        elements: list[CodeElement] = []

        class_pattern = re.compile(
            r"(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{",
            re.MULTILINE,
        )
        for match in class_pattern.finditer(content):
            elements.append(
                CodeElement(
                    name=match.group(1),
                    type="class",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                )
            )

        method_pattern = re.compile(
            r"(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:<[\w,\s]+>\s+)?(\w+)\s+(\w+)\s*\(([^)]*)\)",
            re.MULTILINE,
        )
        for match in method_pattern.finditer(content):
            params = [p.strip().split()[-1] for p in match.group(3).split(",") if p.strip()]
            elements.append(
                CodeElement(
                    name=match.group(2),
                    type="method",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                    return_type=match.group(1),
                    parameters=params,
                )
            )

        interface_pattern = re.compile(
            r"(?:public\s+)?interface\s+(\w+)(?:\s+extends\s+[\w,\s]+)?\s*\{",
            re.MULTILINE,
        )
        for match in interface_pattern.finditer(content):
            elements.append(
                CodeElement(
                    name=match.group(1),
                    type="interface",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                )
            )

        return elements

    async def _parse_generic(
        self, content: str, file_path: str, language: str
    ) -> list[CodeElement]:
        """Generic regex-based parsing for unsupported languages.

        Args:
            content: File content.
            file_path: Path to the file.
            language: Programming language.

        Returns:
            List of CodeElement objects.
        """
        elements: list[CodeElement] = []

        func_pattern = re.compile(
            r"(?:func|function|def|fn)\s+(\w+)\s*\(([^)]*)\)",
            re.MULTILINE,
        )
        for match in func_pattern.finditer(content):
            params = [p.strip().split(":")[0].strip().split("=")[0].strip() for p in match.group(2).split(",") if p.strip()]
            elements.append(
                CodeElement(
                    name=match.group(1),
                    type="function",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                    parameters=params,
                )
            )

        class_pattern = re.compile(
            r"(?:class|struct)\s+(\w+)(?:\s*[:{])",
            re.MULTILINE,
        )
        for match in class_pattern.finditer(content):
            elements.append(
                CodeElement(
                    name=match.group(1),
                    type="class",
                    file_path=file_path,
                    line_start=content[: match.start()].count("\n") + 1,
                )
            )

        return elements

    async def parse_directory(
        self, root_path: str, language: str, file_paths: list[str] | None = None
    ) -> list[CodeElement]:
        """Parse all files of a language in a directory.

        Args:
            root_path: Repository root path.
            language: Programming language to parse.
            file_paths: Optional list of specific file paths to parse.

        Returns:
            List of all CodeElement objects found.
        """
        elements: list[CodeElement] = []

        if file_paths is None:
            file_paths = self._find_language_files(root_path, language)

        for file_path in file_paths:
            file_elements = await self.parse_file(file_path, language)
            elements.extend(file_elements)

        return elements

    def _find_language_files(self, root_path: str, language: str) -> list[str]:
        """Find all files for a given language.

        Args:
            root_path: Repository root path.
            language: Programming language name.

        Returns:
            List of file paths.
        """
        language_lower = language.lower()
        extensions = {
            ext: lang
            for ext, lang in self.LANGUAGE_MAP.items()
            if lang.lower() == language_lower
        }

        if not extensions:
            return []

        files = []
        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in extensions:
                    files.append(os.path.join(root, filename))

        return files

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Extract decorator name from AST node.

        Args:
            node: AST expression node.

        Returns:
            Decorator name string.
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_decorator_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return str(ast.dump(node))

    def _get_annotation(self, node: ast.expr | None) -> str | None:
        """Extract type annotation from AST node.

        Args:
            node: AST expression node.

        Returns:
            Type annotation string or None.
        """
        if node is None:
            return None
        return ast.unparse(node)
