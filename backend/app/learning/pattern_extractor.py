"""Pattern extractor module.

Extracts reusable engineering patterns from experiences.
Analyzes code changes, architecture decisions, and implementation
approaches to identify reusable patterns.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class PatternType(str, Enum):
    """Types of engineering patterns."""

    ARCHITECTURE = "architecture"
    CODING = "coding"
    SECURITY = "security"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    DATABASE = "database"
    FRONTEND = "frontend"
    BACKEND = "backend"


@dataclass
class PatternData:
    """Internal representation of an extracted pattern."""

    pattern_type: str
    name: str
    description: str
    code_example: str | None = None
    when_to_use: str = ""
    when_not_to_use: str = ""
    technologies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.5
    generalization_score: float = 0.5


class PatternSchema(BaseModel):
    """Pydantic schema for pattern output."""

    pattern_type: str = Field(..., description="Type of pattern")
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    code_example: str | None = None
    when_to_use: str = Field(default="")
    when_not_to_use: str = Field(default="")
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    generalization_score: float = Field(default=0.5, ge=0.0, le=1.0)


class PatternExtractor:
    """Extracts reusable engineering patterns from experiences.

    Analyzes code changes, architecture decisions, and implementation
    approaches to identify generalized, reusable patterns.
    """

    _PATTERN_KEYWORDS: dict[str, list[str]] = {
        PatternType.ARCHITECTURE.value: [
            "architecture",
            "design",
            "structure",
            "module",
            "service",
            "component",
            "layer",
            "boundary",
            "dependency",
            "integration",
        ],
        PatternType.CODING.value: [
            "function",
            "class",
            "method",
            "refactor",
            "code",
            "implementation",
            "algorithm",
            "utility",
            "helper",
            "wrapper",
        ],
        PatternType.SECURITY.value: [
            "security",
            "auth",
            "permission",
            "encrypt",
            "token",
            "credential",
            "vulnerability",
            "sanitize",
            "validate",
            "csrf",
            "xss",
        ],
        PatternType.DEPLOYMENT.value: [
            "deploy",
            "ci",
            "cd",
            "pipeline",
            "container",
            "docker",
            "kubernetes",
            "infrastructure",
            "release",
            "rollback",
        ],
        PatternType.TESTING.value: [
            "test",
            "spec",
            "assert",
            "mock",
            "fixture",
            "coverage",
            "integration",
            "unit",
            "e2e",
            "regression",
        ],
        PatternType.DATABASE.value: [
            "database",
            "migration",
            "schema",
            "query",
            "index",
            "transaction",
            "orm",
            "model",
            "relation",
            "join",
        ],
    }

    async def extract_patterns(self, experience: dict) -> list[PatternData]:
        """Extract all patterns from an experience.

        Dispatches to specialized extractors based on experience type
        and merges results.

        Args:
            experience: The experience dictionary containing context,
                outcome, solution, and metadata.

        Returns:
            List of extracted PatternData instances.
        """
        experience_type = experience.get("experience_type", "")
        context = experience.get("context", {})
        solution = experience.get("solution", "")
        technologies = experience.get("technologies", [])
        files_changed = experience.get("files_changed", [])

        all_patterns: list[PatternData] = []

        extractors = [
            self.extract_architecture_patterns,
            self.extract_coding_patterns,
            self.extract_security_patterns,
            self.extract_deployment_patterns,
            self.extract_testing_patterns,
            self.extract_database_patterns,
        ]

        for extractor in extractors:
            patterns = await extractor(experience)
            all_patterns.extend(patterns)

        # Enhanced detection: co-change and tech-stack patterns
        copchange = self._detect_copchange_pattern(experience)
        if copchange:
            all_patterns.append(copchange)

        techstack = self._detect_tech_stack_pattern(experience)
        if techstack:
            all_patterns.append(techstack)

        if not all_patterns and experience_type:
            fallback = await self._extract_generic_pattern(experience)
            if fallback:
                all_patterns.append(fallback)

        for pattern in all_patterns:
            self._generalize_pattern(pattern.__dict__)
            pattern.confidence = self._assess_pattern_quality(pattern.__dict__)
            pattern.generalization_score = self._compute_generalization_score(
                pattern, experience
            )
            if not pattern.code_example:
                pattern.code_example = (
                    self._generate_solution_based_code_example(pattern.__dict__, experience)
                    or self._generate_code_example(pattern.__dict__)
                )
            if not pattern.when_to_use:
                pattern.when_to_use = self._determine_when_to_use(pattern.__dict__)
            if not pattern.when_not_to_use:
                pattern.when_not_to_use = self._determine_when_not_to_use(
                    pattern.__dict__
                )

        logger.info(
            "Extracted %d patterns from experience",
            len(all_patterns),
            extra={"experience_type": experience_type},
        )

        return all_patterns

    async def extract_architecture_patterns(
        self, experience: dict
    ) -> list[PatternData]:
        """Extract architecture patterns from an experience.

        Identifies patterns related to system design, module structure,
        service boundaries, and dependency management.

        Args:
            experience: The experience dictionary.

        Returns:
            List of architecture PatternData instances.
        """
        context = experience.get("context", {})
        solution = experience.get("solution", "")
        files_changed = experience.get("files_changed", [])
        technologies = experience.get("technologies", [])

        patterns: list[PatternData] = []

        if self._has_keyword_match(
            experience, self._PATTERN_KEYWORDS[PatternType.ARCHITECTURE.value]
        ):
            pattern = PatternData(
                pattern_type=PatternType.ARCHITECTURE.value,
                name=self._generate_pattern_name(experience, "architecture"),
                description=self._extract_description(experience, "architecture"),
                technologies=technologies,
                tags=self._extract_tags(experience, "architecture"),
            )
            patterns.append(pattern)

        if self._detect_layered_architecture(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.ARCHITECTURE.value,
                    name="Layered Architecture Separation",
                    description="Separate application logic into distinct layers "
                    "(presentation, business, data) with clear boundaries.",
                    technologies=technologies,
                    tags=["architecture", "separation-of-concerns", "layers"],
                )
            )

        if self._detect_dependency_injection(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.ARCHITECTURE.value,
                    name="Dependency Injection Pattern",
                    description="Inject dependencies rather than creating them "
                    "internally to improve testability and flexibility.",
                    technologies=technologies,
                    tags=["architecture", "di", "testability"],
                )
            )

        if self._detect_event_driven(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.ARCHITECTURE.value,
                    name="Event-Driven Communication",
                    description="Use events for loose coupling between components "
                    "that need to react to state changes.",
                    technologies=technologies,
                    tags=["architecture", "events", "decoupling"],
                )
            )

        return patterns

    async def extract_coding_patterns(self, experience: dict) -> list[PatternData]:
        """Extract coding patterns from an experience.

        Identifies patterns related to code structure, utilities,
        refactoring approaches, and implementation techniques.

        Args:
            experience: The experience dictionary.

        Returns:
            List of coding PatternData instances.
        """
        context = experience.get("context", {})
        solution = experience.get("solution", "")
        technologies = experience.get("technologies", [])

        patterns: list[PatternData] = []

        if self._has_keyword_match(
            experience, self._PATTERN_KEYWORDS[PatternType.CODING.value]
        ):
            pattern = PatternData(
                pattern_type=PatternType.CODING.value,
                name=self._generate_pattern_name(experience, "coding"),
                description=self._extract_description(experience, "coding"),
                technologies=technologies,
                tags=self._extract_tags(experience, "coding"),
            )
            patterns.append(pattern)

        if self._detect_error_handling_pattern(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.CODING.value,
                    name="Structured Error Handling",
                    description="Use specific exception types with contextual "
                    "error information rather than generic catches.",
                    technologies=technologies,
                    tags=["coding", "error-handling", "resilience"],
                )
            )

        if self._detect_configuration_pattern(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.CODING.value,
                    name="Externalized Configuration",
                    description="Externalize configuration values to environment "
                    "variables or config files rather than hardcoding.",
                    technologies=technologies,
                    tags=["coding", "configuration", "twelve-factor"],
                )
            )

        return patterns

    async def extract_security_patterns(self, experience: dict) -> list[PatternData]:
        """Extract security patterns from an experience.

        Identifies patterns related to authentication, authorization,
        data protection, and secure coding practices.

        Args:
            experience: The experience dictionary.

        Returns:
            List of security PatternData instances.
        """
        context = experience.get("context", {})
        solution = experience.get("solution", "")
        technologies = experience.get("technologies", [])

        patterns: list[PatternData] = []

        if self._has_keyword_match(
            experience, self._PATTERN_KEYWORDS[PatternType.SECURITY.value]
        ):
            pattern = PatternData(
                pattern_type=PatternType.SECURITY.value,
                name=self._generate_pattern_name(experience, "security"),
                description=self._extract_description(experience, "security"),
                technologies=technologies,
                tags=self._extract_tags(experience, "security"),
            )
            patterns.append(pattern)

        if self._detect_input_validation(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.SECURITY.value,
                    name="Input Validation and Sanitization",
                    description="Validate and sanitize all external inputs at "
                    "system boundaries before processing.",
                    technologies=technologies,
                    tags=["security", "input-validation", "sanitization"],
                )
            )

        if self._detect_secret_management(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.SECURITY.value,
                    name="Secret Management Pattern",
                    description="Never store secrets in code or config files; "
                    "use a secrets manager or environment variables.",
                    technologies=technologies,
                    tags=["security", "secrets", "credentials"],
                )
            )

        return patterns

    async def extract_deployment_patterns(self, experience: dict) -> list[PatternData]:
        """Extract deployment patterns from an experience.

        Identifies patterns related to CI/CD, containerization,
        release strategies, and infrastructure management.

        Args:
            experience: The experience dictionary.

        Returns:
            List of deployment PatternData instances.
        """
        context = experience.get("context", {})
        solution = experience.get("solution", "")
        technologies = experience.get("technologies", [])

        patterns: list[PatternData] = []

        if self._has_keyword_match(
            experience, self._PATTERN_KEYWORDS[PatternType.DEPLOYMENT.value]
        ):
            pattern = PatternData(
                pattern_type=PatternType.DEPLOYMENT.value,
                name=self._generate_pattern_name(experience, "deployment"),
                description=self._extract_description(experience, "deployment"),
                technologies=technologies,
                tags=self._extract_tags(experience, "deployment"),
            )
            patterns.append(pattern)

        if self._detect_blue_green_deployment(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.DEPLOYMENT.value,
                    name="Blue-Green Deployment",
                    description="Maintain two identical production environments "
                    "to enable zero-downtime deployments and quick rollbacks.",
                    technologies=technologies,
                    tags=["deployment", "zero-downtime", "rollback"],
                )
            )

        if self._detect_infrastructure_as_code(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.DEPLOYMENT.value,
                    name="Infrastructure as Code",
                    description="Define infrastructure through version-controlled "
                    "configuration files for reproducibility.",
                    technologies=technologies,
                    tags=["deployment", "iac", "reproducibility"],
                )
            )

        return patterns

    async def extract_testing_patterns(self, experience: dict) -> list[PatternData]:
        """Extract testing patterns from an experience.

        Identifies patterns related to test strategy, test structure,
        mocking approaches, and quality assurance.

        Args:
            experience: The experience dictionary.

        Returns:
            List of testing PatternData instances.
        """
        context = experience.get("context", {})
        solution = experience.get("solution", "")
        technologies = experience.get("technologies", [])

        patterns: list[PatternData] = []

        if self._has_keyword_match(
            experience, self._PATTERN_KEYWORDS[PatternType.TESTING.value]
        ):
            pattern = PatternData(
                pattern_type=PatternType.TESTING.value,
                name=self._generate_pattern_name(experience, "testing"),
                description=self._extract_description(experience, "testing"),
                technologies=technologies,
                tags=self._extract_tags(experience, "testing"),
            )
            patterns.append(pattern)

        if self._detect_test_pyramid(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.TESTING.value,
                    name="Test Pyramid Strategy",
                    description="Structure tests with many unit tests at the base, "
                    "fewer integration tests, and minimal end-to-end tests.",
                    technologies=technologies,
                    tags=["testing", "test-pyramid", "strategy"],
                )
            )

        if self._detect_mocking_pattern(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.TESTING.value,
                    name="Interface-Based Mocking",
                    description="Program to interfaces and mock at boundaries "
                    "to enable isolated, fast unit tests.",
                    technologies=technologies,
                    tags=["testing", "mocking", "isolation"],
                )
            )

        return patterns

    async def extract_database_patterns(self, experience: dict) -> list[PatternData]:
        """Extract database patterns from an experience.

        Identifies patterns related to schema design, query optimization,
        migrations, and data access approaches.

        Args:
            experience: The experience dictionary.

        Returns:
            List of database PatternData instances.
        """
        context = experience.get("context", {})
        solution = experience.get("solution", "")
        technologies = experience.get("technologies", [])

        patterns: list[PatternData] = []

        if self._has_keyword_match(
            experience, self._PATTERN_KEYWORDS[PatternType.DATABASE.value]
        ):
            pattern = PatternData(
                pattern_type=PatternType.DATABASE.value,
                name=self._generate_pattern_name(experience, "database"),
                description=self._extract_description(experience, "database"),
                technologies=technologies,
                tags=self._extract_tags(experience, "database"),
            )
            patterns.append(pattern)

        if self._detect_migration_pattern(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.DATABASE.value,
                    name="Versioned Migration Pattern",
                    description="Use version-controlled, incremental database "
                    "migrations for safe schema evolution.",
                    technologies=technologies,
                    tags=["database", "migrations", "schema"],
                )
            )

        if self._detect_repository_pattern(experience):
            patterns.append(
                PatternData(
                    pattern_type=PatternType.DATABASE.value,
                    name="Repository Pattern",
                    description="Abstract data access behind a repository interface "
                    "to decouple business logic from persistence.",
                    technologies=technologies,
                    tags=["database", "repository", "abstraction"],
                )
            )

        return patterns

    async def _extract_generic_pattern(self, experience: dict) -> PatternData | None:
        """Extract a generic pattern when no specific type matches.

        Args:
            experience: The experience dictionary.

        Returns:
            A generic PatternData or None if extraction fails.
        """
        solution = experience.get("solution", "")
        if not solution:
            return None

        return PatternData(
            pattern_type="general",
            name=self._generate_pattern_name(experience, "general"),
            description=self._extract_description(experience, "general"),
            technologies=experience.get("technologies", []),
            tags=self._extract_tags(experience, "general"),
        )

    def _generalize_pattern(self, pattern: dict) -> dict:
        """Generalize a pattern from specific to reusable.

        Removes project-specific references, normalizes naming,
        and makes the pattern applicable across codebases.

        Args:
            pattern: The pattern dictionary to generalize.

        Returns:
            The generalized pattern dictionary.
        """
        name = pattern.get("name", "")
        description = pattern.get("description", "")

        specific_prefixes = [
            "In this project",
            "For our",
            "The current",
            "Our team",
            "This codebase",
        ]
        for prefix in specific_prefixes:
            if description.startswith(prefix):
                description = description[len(prefix) :].lstrip(" ,:")

        generic_replacements = {
            "our service": "the service",
            "our application": "the application",
            "our codebase": "the codebase",
            "our team": "the team",
            "this project": "the project",
        }
        for specific, generic in generic_replacements.items():
            description = description.replace(specific, generic)

        tags = pattern.get("tags", [])
        project_specific_tags = [
            t for t in tags if t.startswith("project-") or t.startswith("repo-")
        ]
        tags = [t for t in tags if t not in project_specific_tags]
        pattern["tags"] = tags

        pattern["description"] = description
        pattern["name"] = name

        return pattern

    def _assess_pattern_quality(self, pattern: dict) -> float:
        """Rate the quality of a pattern on a 0.0 to 1.0 scale.

        Evaluates based on description clarity, completeness of guidance,
        presence of code examples, and tag coverage.

        Args:
            pattern: The pattern dictionary to assess.

        Returns:
            Quality score between 0.0 and 1.0.
        """
        score = 0.0
        max_score = 5.0

        description = pattern.get("description", "")
        if len(description) > 20:
            score += 1.0
        if len(description) > 80:
            score += 0.5

        when_to_use = pattern.get("when_to_use", "")
        if when_to_use and len(when_to_use) > 10:
            score += 1.0

        when_not_to_use = pattern.get("when_not_to_use", "")
        if when_not_to_use and len(when_not_to_use) > 10:
            score += 1.0

        code_example = pattern.get("code_example")
        if code_example and len(code_example) > 20:
            score += 1.0

        tags = pattern.get("tags", [])
        if len(tags) >= 2:
            score += 0.5

        return round(min(score / max_score, 1.0), 2)

    def _generate_code_example(self, pattern: dict) -> str | None:
        """Generate an example code snippet for a pattern.

        Creates a generic, illustrative code example based on
        the pattern type and description.

        Args:
            pattern: The pattern dictionary.

        Returns:
            A code example string or None if not applicable.
        """
        pattern_type = pattern.get("pattern_type", "")
        name = pattern.get("name", "")

        examples: dict[str, dict[str, str]] = {
            "Layered Architecture Separation": {
                "python": (
                    "# Presentation layer\n"
                    "class UserController:\n"
                    "    def __init__(self, service: UserService):\n"
                    "        self.service = service\n\n"
                    "# Business layer\n"
                    "class UserService:\n"
                    "    def __init__(self, repo: UserRepository):\n"
                    "        self.repo = repo\n\n"
                    "# Data layer\n"
                    "class UserRepository:\n"
                    "    def get(self, id: str) -> User: ..."
                ),
            },
            "Dependency Injection Pattern": {
                "python": (
                    "from dataclasses import dataclass\n\n"
                    "@dataclass\n"
                    "class Config:\n"
                    "    db_url: str\n"
                    "    api_key: str\n\n"
                    "class Application:\n"
                    "    def __init__(self, config: Config):\n"
                    "        self.config = config\n"
                    "        self.db = Database(config.db_url)\n"
                    "        self.api = ApiClient(config.api_key)"
                ),
            },
            "Event-Driven Communication": {
                "python": (
                    "from typing import Callable\n\n"
                    "class EventBus:\n"
                    "    def __init__(self):\n"
                    "        self._handlers: dict[str, list[Callable]] = {}\n\n"
                    "    def subscribe(self, event: str, handler: Callable):\n"
                    "        self._handlers.setdefault(event, []).append(handler)\n\n"
                    "    def publish(self, event: str, data: dict):\n"
                    "        for handler in self._handlers.get(event, []):\n"
                    "            handler(data)"
                ),
            },
            "Structured Error Handling": {
                "python": (
                    "class AppError(Exception):\n"
                    "    def __init__(self, message: str, code: str):\n"
                    "        super().__init__(message)\n"
                    "        self.code = code\n\n"
                    "try:\n"
                    "    result = await service.process(data)\n"
                    "except AppError as e:\n"
                    "    logger.error('Processing failed', error_code=e.code)\n"
                    "    raise"
                ),
            },
            "Input Validation and Sanitization": {
                "python": (
                    "from pydantic import BaseModel, Field, field_validator\n\n"
                    "class CreateUserRequest(BaseModel):\n"
                    "    email: str = Field(..., max_length=255)\n"
                    "    name: str = Field(..., min_length=1, max_length=100)\n\n"
                    "    @field_validator('email')\n"
                    "    @classmethod\n"
                    "    def validate_email(cls, v: str) -> str:\n"
                    "        if '@' not in v:\n"
                    "            raise ValueError('Invalid email')\n"
                    "        return v.lower().strip()"
                ),
            },
            "Secret Management Pattern": {
                "python": (
                    "import os\n"
                    "from functools import lru_cache\n\n"
                    "class Settings:\n"
                    "    @property\n"
                    "    def database_url(self) -> str:\n"
                    "        url = os.environ.get('DATABASE_URL')\n"
                    "        if not url:\n"
                    "            raise RuntimeError('DATABASE_URL not set')\n"
                    "        return url\n\n"
                    "@lru_cache\n"
                    "def get_settings() -> Settings:\n"
                    "    return Settings()"
                ),
            },
            "Versioned Migration Pattern": {
                "python": (
                    "# migrations/001_create_users.sql\n"
                    "CREATE TABLE users (\n"
                    "    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
                    "    email VARCHAR(255) UNIQUE NOT NULL,\n"
                    "    created_at TIMESTAMPTZ DEFAULT NOW()\n"
                    ");\n\n"
                    "# migrations/002_add_user_status.sql\n"
                    "ALTER TABLE users\n"
                    "    ADD COLUMN status VARCHAR(20) DEFAULT 'active';"
                ),
            },
            "Repository Pattern": {
                "python": (
                    "from abc import ABC, abstractmethod\n\n"
                    "class UserRepository(ABC):\n"
                    "    @abstractmethod\n"
                    "    async def get(self, id: str) -> User | None: ...\n\n"
                    "    @abstractmethod\n"
                    "    async def save(self, user: User) -> None: ...\n\n"
                    "class PostgresUserRepository(UserRepository):\n"
                    "    async def get(self, id: str) -> User | None:\n"
                    "        row = await self.db.fetch_one(\n"
                    "            'SELECT * FROM users WHERE id = $1', id\n"
                    "        )\n"
                    "        return User(**row) if row else None"
                ),
            },
        }

        example = examples.get(name)
        if example:
            return list(example.values())[0]

        return None

    def _determine_when_to_use(self, pattern: dict) -> str:
        """Determine usage guidance for when to apply a pattern.

        Args:
            pattern: The pattern dictionary.

        Returns:
            Usage guidance string.
        """
        name = pattern.get("name", "")
        pattern_type = pattern.get("pattern_type", "")

        guidance_map: dict[str, str] = {
            "Layered Architecture Separation": (
                "Use when building applications with multiple concerns "
                "(UI, business logic, data access) that need independent "
                "modification or testing."
            ),
            "Dependency Injection Pattern": (
                "Use when components have external dependencies that "
                "should be configurable, testable, or swappable."
            ),
            "Event-Driven Communication": (
                "Use when components need to react to state changes "
                "without tight coupling, or when operations can be "
                "processed asynchronously."
            ),
            "Structured Error Handling": (
                "Use when you need differentiated error recovery "
                "strategies and clear error attribution across layers."
            ),
            "Input Validation and Sanitization": (
                "Use at all system boundaries where external data "
                "is received, including API endpoints, file uploads, "
                "and message consumers."
            ),
            "Secret Management Pattern": (
                "Use whenever handling credentials, API keys, "
                "connection strings, or any sensitive configuration "
                "that must not appear in source code."
            ),
            "Versioned Migration Pattern": (
                "Use when database schemas evolve over time and "
                "require coordinated updates across environments."
            ),
            "Repository Pattern": (
                "Use when business logic should remain independent "
                "of the persistence mechanism, enabling database "
                "technology changes without business code changes."
            ),
        }

        if name in guidance_map:
            return guidance_map[name]

        type_guidance: dict[str, str] = {
            "architecture": (
                "Apply this pattern when designing system structure "
                "and component boundaries."
            ),
            "coding": (
                "Apply this pattern when implementing code that "
                "benefits from established conventions."
            ),
            "security": (
                "Apply this pattern when protecting against "
                "common security vulnerabilities."
            ),
            "deployment": (
                "Apply this pattern when setting up or improving "
                "deployment and release processes."
            ),
            "testing": (
                "Apply this pattern when designing test strategies "
                "for reliability and maintainability."
            ),
            "database": (
                "Apply this pattern when working with data persistence "
                "and schema management."
            ),
        }

        return type_guidance.get(pattern_type, "Apply based on project requirements.")

    def _determine_when_not_to_use(self, pattern: dict) -> str:
        """Determine anti-pattern guidance for when to avoid a pattern.

        Args:
            pattern: The pattern dictionary.

        Returns:
            Anti-pattern guidance string.
        """
        name = pattern.get("name", "")
        pattern_type = pattern.get("pattern_type", "")

        anti_guidance_map: dict[str, str] = {
            "Layered Architecture Separation": (
                "Avoid for simple scripts or single-purpose tools where "
                "the overhead of layered separation adds complexity "
                "without benefit."
            ),
            "Dependency Injection Pattern": (
                "Avoid for small utilities or prototypes where the added "
                "abstraction slows development without improving "
                "testability."
            ),
            "Event-Driven Communication": (
                "Avoid when synchronous, direct communication is simpler "
                "and sufficient; events add debugging complexity."
            ),
            "Structured Error Handling": (
                "Avoid over-engineering error hierarchies in simple "
                "scripts or CLI tools where basic try/except suffices."
            ),
            "Input Validation and Sanitization": (
                "Do not skip validation even for internal APIs; all "
                "boundaries should validate inputs to prevent injection "
                "attacks."
            ),
            "Secret Management Pattern": (
                "Never store secrets in version control, Docker images, "
                "or log files, even for development environments."
            ),
            "Versioned Migration Pattern": (
                "Avoid making direct schema changes in production; "
                "always use migration scripts for reproducibility."
            ),
            "Repository Pattern": (
                "Avoid when data access is trivial and unlikely to "
                "change; the abstraction adds unnecessary indirection."
            ),
        }

        if name in anti_guidance_map:
            return anti_guidance_map[name]

        type_anti: dict[str, str] = {
            "architecture": (
                "Avoid when the architectural overhead exceeds the "
                "complexity of the problem being solved."
            ),
            "coding": (
                "Avoid when the pattern adds complexity that obscures "
                "the primary purpose of the code."
            ),
            "security": (
                "Never skip security patterns; however, avoid "
                "over-engineering for low-risk contexts."
            ),
            "deployment": (
                "Avoid complex deployment patterns when simple, "
                "manual deployments suffice for the project scale."
            ),
            "testing": (
                "Avoid excessive mocking or test infrastructure "
                "for trivial, stable code with few dependencies."
            ),
            "database": (
                "Avoid complex database patterns when simple, "
                "direct queries are sufficient and performant."
            ),
        }

        return type_anti.get(
            pattern_type, "Evaluate whether the pattern's cost justifies its benefit."
        )

    def _compute_generalization_score(
        self, pattern: PatternData, experience: dict
    ) -> float:
        """Compute how generalizable a pattern is.

        Higher scores indicate the pattern applies broadly across
        projects and technologies.

        Args:
            pattern: The extracted pattern.
            experience: The source experience.

        Returns:
            Generalization score between 0.0 and 1.0.
        """
        score = 0.5

        description = pattern.description
        if any(
            marker in description.lower()
            for marker in ["specific", "this project", "our team", "the current"]
        ):
            score -= 0.2

        technologies = experience.get("technologies", [])
        if len(technologies) <= 2:
            score += 0.1
        elif len(technologies) > 5:
            score -= 0.1

        tags = pattern.tags
        domain_specific = [
            t for t in tags if t.startswith("project-") or t.startswith("repo-")
        ]
        if domain_specific:
            score -= 0.15

        generic_indicators = [
            "generally",
            "typically",
            "commonly",
            "widely",
            "best practice",
        ]
        if any(ind in description.lower() for ind in generic_indicators):
            score += 0.1

        return round(max(0.0, min(1.0, score)), 2)

    def _has_keyword_match(self, experience: dict, keywords: list[str]) -> bool:
        """Check if an experience matches a set of keywords.

        Searches the experience's description, solution, and tags
        for any of the provided keywords.

        Args:
            experience: The experience dictionary.
            keywords: List of keywords to search for.

        Returns:
            True if at least one keyword matches.
        """
        searchable = " ".join(
            [
                experience.get("description", ""),
                experience.get("solution", ""),
                experience.get("title", ""),
                " ".join(experience.get("tags", [])),
            ]
        ).lower()

        return any(kw.lower() in searchable for kw in keywords)

    def _generate_pattern_name(self, experience: dict, pattern_type: str) -> str:
        """Generate a descriptive name for a pattern.

        Args:
            experience: The experience dictionary.
            pattern_type: The pattern type category.

        Returns:
            Generated pattern name.
        """
        title = experience.get("title", "")
        if title:
            cleaned = title[:100].strip()
            return cleaned.capitalize()

        solution = experience.get("solution", "")
        if solution:
            first_sentence = solution.split(".")[0][:100].strip()
            return first_sentence.capitalize()

        return f"{pattern_type.capitalize()} Pattern"

    def _extract_description(self, experience: dict, pattern_type: str) -> str:
        """Extract or generate a pattern description.

        Args:
            experience: The experience dictionary.
            pattern_type: The pattern type category.

        Returns:
            Pattern description string.
        """
        solution = experience.get("solution", "")
        if solution:
            return solution[:500].strip()

        description = experience.get("description", "")
        if description:
            return description[:500].strip()

        return f"A {pattern_type} pattern derived from experience."

    def _extract_tags(self, experience: dict, pattern_type: str) -> list[str]:
        """Extract relevant tags from an experience.

        Args:
            experience: The experience dictionary.
            pattern_type: The pattern type category.

        Returns:
            List of tag strings.
        """
        tags = list(experience.get("tags", []))
        technologies = experience.get("technologies", [])

        tags.append(pattern_type)
        for tech in technologies[:5]:
            normalized = tech.lower().replace(" ", "-")
            if normalized not in tags:
                tags.append(normalized)

        return list(dict.fromkeys(tags))

    def _detect_layered_architecture(self, experience: dict) -> bool:
        """Detect layered architecture indicators."""
        files = experience.get("files_changed", [])
        indicators = ["controller", "service", "repository", "model", "schema", "view"]
        return any(
            any(ind in f.lower() for ind in indicators) for f in files
        )

    def _detect_dependency_injection(self, experience: dict) -> bool:
        """Detect dependency injection indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["inject", "dependency", "constructor", "provide"]
        )

    def _detect_event_driven(self, experience: dict) -> bool:
        """Detect event-driven communication indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["event", "emit", "subscribe", "publish", "listener", "callback"]
        )

    def _detect_error_handling_pattern(self, experience: dict) -> bool:
        """Detect structured error handling indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["exception", "error handling", "try", "catch", "raise"]
        )

    def _detect_configuration_pattern(self, experience: dict) -> bool:
        """Detect externalized configuration indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["config", "environment", "env var", "settings", "secrets"]
        )

    def _detect_input_validation(self, experience: dict) -> bool:
        """Detect input validation indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["validate", "sanitize", "input", "check", "verify"]
        )

    def _detect_secret_management(self, experience: dict) -> bool:
        """Detect secret management indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["secret", "credential", "password", "api key", "token"]
        )

    def _detect_blue_green_deployment(self, experience: dict) -> bool:
        """Detect blue-green deployment indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["blue-green", "zero-downtime", "canary", "rolling"]
        )

    def _detect_infrastructure_as_code(self, experience: dict) -> bool:
        """Detect infrastructure as code indicators."""
        files = experience.get("files_changed", [])
        return any(
            f.endswith((".tf", ".yaml", ".yml")) or "terraform" in f.lower()
            for f in files
        )

    def _detect_test_pyramid(self, experience: dict) -> bool:
        """Detect test pyramid indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["unit test", "integration test", "e2e", "test pyramid"]
        )

    def _detect_mocking_pattern(self, experience: dict) -> bool:
        """Detect mocking pattern indicators."""
        solution = experience.get("solution", "").lower()
        return any(
            kw in solution
            for kw in ["mock", "stub", "fake", "test double", "patch"]
        )

    def _detect_migration_pattern(self, experience: dict) -> bool:
        """Detect database migration indicators."""
        files = experience.get("files_changed", [])
        return any("migration" in f.lower() for f in files)

    def _detect_repository_pattern(self, experience: dict) -> bool:
        """Detect repository pattern indicators."""
        files = experience.get("files_changed", [])
        return any("repository" in f.lower() or "repo" in f.lower() for f in files)

    # ------------------------------------------------------------------
    # Enhanced pattern detection (cross-workflow & tech-stack aware)
    # ------------------------------------------------------------------

    def _detect_copchange_pattern(self, experience: dict) -> PatternData | None:
        """Detect co-change patterns - files that change together.

        When certain files always change together, it indicates a
        logical coupling or shared responsibility.
        """
        files = experience.get("files_changed", [])
        if len(files) < 2:
            return None

        # Group files by directory
        dir_groups: dict[str, list[str]] = {}
        for f in files:
            parts = f.replace("\\", "/").split("/")
            if len(parts) > 1:
                dir_name = parts[0]
                dir_groups.setdefault(dir_name, []).append(f)

        # Find directories with multiple file changes
        coupled_dirs = {k: v for k, v in dir_groups.items() if len(v) >= 2}
        if not coupled_dirs:
            return None

        # Pick the directory with most changes
        best_dir = max(coupled_dirs, key=lambda k: len(coupled_dirs[k]))
        coupled_files = coupled_files_list = coupled_dirs[best_dir]

        return PatternData(
            pattern_type="coding",
            name=f"Co-change cluster in {best_dir}/",
            description=(
                f"Files in '{best_dir}/' frequently change together "
                f"({len(coupled_files)} files modified in this workflow). "
                f"This suggests shared responsibility or tight coupling. "
                f"Consider: {', '.join(os.path.basename(f) for f in coupled_files[:3])}"
            ),
            technologies=experience.get("technologies", []),
            tags=["co-change", f"dir:{best_dir}", "coupling"],
            confidence=min(0.4 + len(coupled_files) * 0.1, 0.8),
        )

    def _detect_tech_stack_pattern(self, experience: dict) -> PatternData | None:
        """Detect technology stack patterns from file extensions and tech list."""
        files = experience.get("files_changed", [])
        technologies = experience.get("technologies", [])

        if not technologies or len(technologies) < 2:
            return None

        # Map file extensions to categories
        ext_categories: dict[str, list[str]] = {
            "backend": [".py", ".java", ".go", ".rs", ".rb", ".php", ".cs"],
            "frontend": [".js", ".ts", ".tsx", ".jsx", ".vue", ".svelte"],
            "data": [".sql", ".csv", ".parquet"],
            "infra": [".tf", ".yaml", ".yml", ".dockerfile"],
            "config": [".json", ".toml", ".env"],
        }

        file_exts = set()
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext:
                file_exts.add(ext)

        # Determine which categories are involved
        involved_categories = []
        for cat, exts in ext_categories.items():
            if any(e in exts for e in file_exts):
                involved_categories.append(cat)

        if len(involved_categories) < 2:
            return None

        cat_str = " + ".join(involved_categories)
        return PatternData(
            pattern_type="architecture",
            name=f"Multi-layer change ({cat_str})",
            description=(
                f"This workflow touched {cat_str} layers. "
                f"Technologies used: {', '.join(technologies[:5])}. "
                f"Cross-layer changes require careful coordination."
            ),
            technologies=technologies,
            tags=["multi-layer", "cross-cutting"] + [f"layer:{c}" for c in involved_categories],
            confidence=0.6,
        )

    def _generate_solution_based_code_example(self, pattern: dict, experience: dict) -> str | None:
        """Generate a code example from the actual solution text instead of hardcoded templates."""
        solution = experience.get("solution", "")
        if not solution or len(solution) < 20:
            return None

        # Extract code-like sections from solution
        lines = solution.split("\n")
        code_lines = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            # Detect code indicators
            if any(kw in stripped for kw in ["def ", "class ", "import ", "from ", "async ", "return ", "if ", "for ", "try:", "with "]):
                in_code = True
            if in_code:
                code_lines.append(line)
                if len(code_lines) > 15:
                    break

        if code_lines:
            return "\n".join(code_lines)

        # Fallback: use the description as a pseudo-code example
        desc = experience.get("description", "")
        if desc and len(desc) > 30:
            return f"# Approach: {desc[:200]}"

        return None
