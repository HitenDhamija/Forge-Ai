"""Database model detection."""

import os
import re

from app.core.logging import get_logger
from app.repo_intelligence.schemas.analysis import CodeElement, DatabaseModelInfo
from app.repo_intelligence.schemas.repository import FrameworkInfo

logger = get_logger(__name__)


class DatabaseDetector:
    """Detects database models and schemas."""

    PATTERNS: dict[str, dict] = {
        "SQLAlchemy": {
            "imports": ["sqlalchemy", "SQLAlchemy"],
            "base_classes": ["Base", "db.Model", "declarative_base"],
            "field_patterns": [r"Column\(", r"Relationship\(", r"ForeignKey\("],
        },
        "Django ORM": {
            "imports": ["django.db.models"],
            "base_classes": ["models.Model"],
            "field_patterns": [r"models\.\w+Field\("],
        },
        "Prisma": {
            "imports": ["prisma"],
            "patterns": [r"model \w+ \{"],
        },
        "TypeORM": {
            "imports": ["typeorm"],
            "decorators": ["@Entity", "@Column", "@PrimaryGeneratedColumn"],
        },
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

    async def detect(
        self,
        root_path: str,
        frameworks: list[FrameworkInfo],
        code_elements: list[CodeElement],
    ) -> list[DatabaseModelInfo]:
        """Detect database models based on frameworks and code patterns.

        Args:
            root_path: Repository root path.
            frameworks: List of detected frameworks.
            code_elements: List of extracted code elements.

        Returns:
            List of detected DatabaseModelInfo objects.
        """
        models: list[DatabaseModelInfo] = []

        orm_type = self._detect_orm_type(root_path, frameworks)

        if orm_type == "SQLAlchemy":
            models.extend(self._detect_sqlalchemy_models(root_path))
        elif orm_type == "Django ORM":
            models.extend(self._detect_django_models(root_path))
        elif orm_type == "Prisma":
            models.extend(self._detect_prisma_models(root_path))
        elif orm_type == "TypeORM":
            models.extend(self._detect_typeorm_models(root_path))

        if not models:
            models.extend(self._detect_generic_models(root_path, code_elements))

        return models

    def _detect_orm_type(
        self, root_path: str, frameworks: list[FrameworkInfo]
    ) -> str | None:
        """Detect the ORM type being used.

        Args:
            root_path: Repository root path.
            frameworks: List of detected frameworks.

        Returns:
            ORM type string or None.
        """
        framework_names = {f.name for f in frameworks}

        if "Django" in framework_names:
            return "Django ORM"

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith((".py", ".js", ".ts")):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(5000)

                    for orm_name, orm_patterns in self.PATTERNS.items():
                        for imp in orm_patterns.get("imports", []):
                            if imp in content:
                                return orm_name
                except (OSError, UnicodeDecodeError):
                    pass

        return None

    def _detect_sqlalchemy_models(self, root_path: str) -> list[DatabaseModelInfo]:
        """Detect SQLAlchemy models.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected database models.
        """
        models = []
        base_pattern = re.compile(r"class\s+(\w+)\s*\(\s*(?:Base|db\.Model|declarative_base\(\))\s*\)")

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith(".py"):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for match in base_pattern.finditer(content):
                        model_name = match.group(1)
                        line_number = content[: match.start()].count("\n") + 1

                        fields = self._extract_fields(content, match.start())

                        table_match = re.search(
                            r'__tablename__\s*=\s*["\']([^"\']+)', content
                        )
                        table_name = table_match.group(1) if table_match else None

                        models.append(
                            DatabaseModelInfo(
                                name=model_name,
                                table_name=table_name,
                                file_path=os.path.relpath(file_path, root_path),
                                line_number=line_number,
                                fields=fields,
                            )
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        return models

    def _detect_django_models(self, root_path: str) -> list[DatabaseModelInfo]:
        """Detect Django models.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected database models.
        """
        models = []
        base_pattern = re.compile(r"class\s+(\w+)\s*\(\s*models\.Model\s*\)")

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if filename != "models.py" and not filename.startswith("models_"):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for match in base_pattern.finditer(content):
                        model_name = match.group(1)
                        line_number = content[: match.start()].count("\n") + 1

                        fields = self._extract_fields(content, match.start())

                        models.append(
                            DatabaseModelInfo(
                                name=model_name,
                                table_name=None,
                                file_path=os.path.relpath(file_path, root_path),
                                line_number=line_number,
                                fields=fields,
                            )
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        return models

    def _detect_prisma_models(self, root_path: str) -> list[DatabaseModelInfo]:
        """Detect Prisma models.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected database models.
        """
        models = []
        model_pattern = re.compile(r"model\s+(\w+)\s*\{")

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith(".prisma"):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for match in model_pattern.finditer(content):
                        model_name = match.group(1)
                        line_number = content[: match.start()].count("\n") + 1

                        models.append(
                            DatabaseModelInfo(
                                name=model_name,
                                table_name=None,
                                file_path=os.path.relpath(file_path, root_path),
                                line_number=line_number,
                            )
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        return models

    def _detect_typeorm_models(self, root_path: str) -> list[DatabaseModelInfo]:
        """Detect TypeORM models.

        Args:
            root_path: Repository root path.

        Returns:
            List of detected database models.
        """
        models = []
        entity_pattern = re.compile(r"@Entity\((?:['\"](\w+)['\"])?\s*\)")

        for root, dirs, filenames in os.walk(root_path):
            dirs[:] = [
                d
                for d in dirs
                if d not in self.IGNORED_DIRS and not d.startswith(".")
            ]

            for filename in filenames:
                if not filename.endswith((".ts", ".js")):
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for match in entity_pattern.finditer(content):
                        table_name = match.group(1)
                        line_number = content[: match.start()].count("\n") + 1

                        class_pattern = re.compile(
                            r"class\s+(\w+).*\{", re.MULTILINE
                        )
                        class_match = class_pattern.search(
                            content[match.start() : match.start() + 500]
                        )
                        model_name = class_match.group(1) if class_match else "Unknown"

                        models.append(
                            DatabaseModelInfo(
                                name=model_name,
                                table_name=table_name,
                                file_path=os.path.relpath(file_path, root_path),
                                line_number=line_number,
                            )
                        )
                except (OSError, UnicodeDecodeError):
                    pass

        return models

    def _detect_generic_models(
        self, root_path: str, code_elements: list[CodeElement]
    ) -> list[DatabaseModelInfo]:
        """Detect generic database models based on naming conventions.

        Args:
            root_path: Repository root path.
            code_elements: List of extracted code elements.

        Returns:
            List of detected database models.
        """
        models = []
        model_dirs = {"models", "model", "entities", "schemas"}

        for element in code_elements:
            if element.type == "class":
                file_parts = element.file_path.replace("\\", "/").split("/")
                if any(d in file_parts for d in model_dirs):
                    models.append(
                        DatabaseModelInfo(
                            name=element.name,
                            file_path=element.file_path,
                            line_number=element.line_start,
                        )
                    )

        return models

    def _extract_fields(
        self, content: str, class_start: int
    ) -> list[CodeElement]:
        """Extract field definitions from a class.

        Args:
            content: File content.
            class_start: Start position of the class in content.

        Returns:
            List of CodeElement objects representing fields.
        """
        fields = []
        field_patterns = [
            re.compile(r"(\w+)\s*=\s*Column\("),
            re.compile(r"(\w+)\s*=\s*models\.\w+Field\("),
            re.compile(r"(\w+)\s*:\s*\w+"),
        ]

        class_content = content[class_start : class_start + 5000]
        for pattern in field_patterns:
            for match in pattern.finditer(class_content):
                field_name = match.group(1)
                if not field_name.startswith("_"):
                    fields.append(
                        CodeElement(
                            name=field_name,
                            type="variable",
                            file_path="",
                            line_start=content[: class_start + match.start()].count("\n") + 1,
                        )
                    )

        return fields
