"""Standalone repositories API - works without broken core imports."""

import json
import os
import shutil
import tempfile
import uuid
import zipfile
import asyncio
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field

from app.api.v1.activity_store import log_activity


# --- Schemas ---

class ImportMethod(str):
    ZIP = "zip"
    GIT = "git"
    FOLDER = "folder"


class RepositoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    import_method: str
    source_url: str | None = None
    source_path: str | None = None


class RepositoryInfo(BaseModel):
    id: str
    name: str
    description: str | None
    status: str
    import_method: str
    source_url: str | None
    local_path: str
    created_at: str
    analyzed_at: str | None = None
    error_message: str | None = None
    file_count: int = 0
    total_lines: int = 0
    languages: list[dict] = []
    frameworks: list[dict] = []


# --- In-memory storage ---
_repositories: dict[str, RepositoryInfo] = {}


def _load_repos():
    """Load repos from disk on startup."""
    try:
        from app.persistence import load_repos
        saved = load_repos()
        for r in saved:
            info = RepositoryInfo(
                id=r["id"], name=r["name"], description=r.get("description"),
                status=r.get("status", "ready"), import_method=r.get("import_method", "folder"),
                source_url=r.get("source_url"), local_path=r.get("local_path", ""),
                created_at=r.get("created_at", ""), analyzed_at=r.get("analyzed_at"),
                error_message=r.get("error_message"),
                file_count=r.get("file_count", 0), total_lines=r.get("total_lines", 0),
                languages=r.get("languages", []), frameworks=r.get("frameworks", []),
            )
            _repositories[info.id] = info
        if saved:
            import logging
            logging.getLogger(__name__).info(f"Loaded {len(saved)} repos from disk")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"_load_repos failed: {e}")


_load_repos()


def _persist_repos():
    """Save repos to disk so they survive restart."""
    try:
        from app.persistence import save_repos
        serializable = []
        for r in _repositories.values():
            serializable.append({
                "id": r.id, "name": r.name, "description": r.description,
                "status": r.status, "import_method": r.import_method,
                "source_url": r.source_url, "local_path": r.local_path,
                "created_at": r.created_at, "analyzed_at": r.analyzed_at,
                "error_message": r.error_message,
                "file_count": r.file_count, "total_lines": r.total_lines,
                "languages": r.languages, "frameworks": r.frameworks,
            })
        save_repos(serializable)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"_persist_repos failed: {e}")

# Temp directory (Windows-compatible)
TEMP_DIR = os.path.join(tempfile.gettempdir(), "forgeai", "repos")
os.makedirs(TEMP_DIR, exist_ok=True)

# Directories to skip during analysis
IGNORED_DIRS = {
    "node_modules", ".venv", "venv", "__pycache__", ".git",
    "dist", "build", ".next", ".nuxt", "coverage", ".idea", ".vscode",
    ".cache", ".turbo", ".parcel-cache", "tmp", "vendor",
    "target", "out", ".gradle", ".maven", "bin", "obj",
    ".tox", "eggs", "*.egg-info", ".mypy_cache", ".pytest_cache",
    "site-packages", ".bundle", "Pods", ".pub-cache",
    ".dart_tool", ".packages", "build_runner",
}
IGNORED_FILES = {
    "*.pyc", "*.pyo", "*.so", "*.dll", "*.exe", "*.min.js",
    "*.min.css", "*.map", "package-lock.json", "yarn.lock",
    "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock", "Cargo.lock",
    "go.sum", "Gemfile.lock", "composer.lock", "poetry.lock",
    "*.lock",
}
MAX_ANALYSIS_FILES = 10000

# Language detection by extension
LANG_MAP = {
    ".py": "Python", ".pyw": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript JSX", ".jsx": "JavaScript JSX",
    ".java": "Java", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".c": "C",
    ".h": "C/C++ Header", ".hpp": "C++ Header",
    ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
    ".sql": "SQL", ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".less": "LESS", ".sass": "Sass",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML", ".xml": "XML", ".md": "Markdown",
    ".rst": "reStructuredText", ".txt": "Text",
    ".dockerfile": "Dockerfile", ".docker": "Dockerfile",
    ".graphql": "GraphQL", ".gql": "GraphQL",
    ".proto": "Protobuf",
    ".vue": "Vue", ".svelte": "Svelte",
    ".prisma": "Prisma", ".graphql": "GraphQL",
    ".env": "Environment", ".env.local": "Environment",
    ".gitignore": "Git", ".gitattributes": "Git",
    ".eslintrc": "Linting", ".prettierrc": "Formatting",
    ".css": "CSS", ".config": "Config",
}

# Detect well-known files by name (not extension)
FILENAME_MAP = {
    "dockerfile": "Dockerfile", "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "makefile": "Makefile", "cmakelists.txt": "CMake",
    "gemfile": "Ruby", "rakefile": "Ruby",
    "cargo.toml": "Rust", "go.mod": "Go", "go.sum": "Go",
    "requirements.txt": "Python", "setup.py": "Python", "setup.cfg": "Python",
    "pyproject.toml": "Python", "pipfile": "Python",
    "package.json": "Node.js", "package-lock.json": "Node.js",
    "tsconfig.json": "TypeScript",
    "composer.json": "PHP", "pubspec.yaml": "Dart",
    "build.gradle": "Groovy", "pom.xml": "Java",
    ".dockerignore": "Dockerfile", "procfile": "Ruby",
}

# Framework detection by file patterns
FRAMEWORK_INDICATORS = {
    "FastAPI": ["from fastapi", "import fastapi"],
    "Django": ["from django", "import django", "manage.py"],
    "Flask": ["from flask", "import flask"],
    "React": ["from react", "import react", "jsx", "tsx"],
    "Next.js": ["next.config", "pages/", "app/"],
    "Express": ["express()", "from express"],
    "Vue": ["from vue", "import vue", ".vue"],
    "Angular": ["@angular", "angular.json"],
    "Node.js": ["package.json", "node_modules"],
    "Spring": ["@SpringBootApplication", "spring"],
}


def _should_ignore(path: str) -> bool:
    parts = Path(path).parts
    for part in parts:
        if part in IGNORED_DIRS:
            return True
    name = os.path.basename(path)
    for pattern in IGNORED_FILES:
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
        elif name == pattern:
            return True
    return False


def _detect_language(ext: str, filename: str = "") -> str | None:
    # Try extension first
    lang = LANG_MAP.get(ext.lower())
    if lang:
        return lang
    # Fall back to filename mapping
    if filename:
        return FILENAME_MAP.get(filename.lower())
    return None


def _analyze_repository(repo_path: str) -> dict:
    """Analyze a repository and return stats. Capped at MAX_ANALYSIS_FILES files."""
    languages: dict[str, int] = {}
    frameworks: set[str] = set()
    total_files = 0
    total_lines = 0
    skipped = 0

    for root, dirs, files in os.walk(repo_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not _should_ignore(os.path.join(root, d))]

        for file in files:
            if total_files >= MAX_ANALYSIS_FILES:
                skipped += 1
                continue

            filepath = os.path.join(root, file)
            if _should_ignore(filepath):
                continue

            total_files += 1
            ext = os.path.splitext(file)[1].lower()
            lang = _detect_language(ext, file)
            if lang:
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = len(f.readlines())
                    languages[lang] = languages.get(lang, 0) + lines
                    total_lines += lines
                except (OSError, UnicodeDecodeError):
                    pass

            # Check for framework indicators
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(5000)  # Read first 5KB
                for framework, indicators in FRAMEWORK_INDICATORS.items():
                    if any(ind in content for ind in indicators):
                        frameworks.add(framework)
            except (OSError, UnicodeDecodeError):
                pass

    # Build language stats
    lang_list = []
    if total_lines > 0:
        for lang, count in sorted(languages.items(), key=lambda x: -x[1]):
            lang_list.append({
                "name": lang,
                "lines": count,
                "percentage": round(count / total_lines * 100, 1),
            })

    return {
        "file_count": total_files,
        "total_lines": total_lines,
        "languages": lang_list,
        "frameworks": [{"name": f, "confidence": 0.8} for f in frameworks],
        "truncated": skipped > 0,
        "skipped_files": skipped,
    }


async def _auto_generate_docs(repo_id: str, repo_name: str):
    """Background task: auto-generate documentation after repo import."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from app.api.v1.documentation_standalone import _build_repo_context, _get_repo_docs_dir, DOC_TEMPLATES, _generate_one_doc
        import os as _os

        repo_path = None
        try:
            from app.api.v1.documentation_standalone import _find_repo_path
            repo_path = _find_repo_path(repo_id)
        except Exception:
            pass
        if not repo_path:
            logger.warning(f"Auto-docs: repo path not found for {repo_id}")
            return

        context = _build_repo_context(repo_path)
        if not context:
            logger.warning(f"Auto-docs: no context for {repo_name}")
            return

        ollama_url = _os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        repo_docs_dir = _get_repo_docs_dir(repo_id)
        repo_docs_dir.mkdir(parents=True, exist_ok=True)

        for old_doc in repo_docs_dir.glob("*.md"):
            old_doc.unlink()

        count = 0
        for template in DOC_TEMPLATES:
            content = await _generate_one_doc(context, template, ollama_url)
            if content:
                doc_path = repo_docs_dir / template["filename"]
                doc_path.write_text(content, encoding="utf-8")
                count += 1

        logger.info(f"Auto-docs: generated {count} docs for {repo_name}")
    except Exception as e:
        logger.error(f"Auto-docs failed for {repo_name}: {e}")


async def _auto_create_workflow(repo_id: str, repo_name: str, repo_info):
    """Background task: auto-create a default workflow pipeline after repo import."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        from app.api.v1.workflows_standalone import _WORKFLOWS, _persist_workflows
        from app.api.v1.projects_standalone import _PROJECTS

        # Find the project that matches this repo name
        project_id = None
        for p in _PROJECTS:
            if p.get("name", "").lower() == repo_name.lower():
                project_id = p["id"]
                break

        # Detect tech stack from repo info
        languages = getattr(repo_info, "languages", []) or []
        lang_names = [l.get("name", "") if isinstance(l, dict) else str(l) for l in languages]
        lang_str = ", ".join(lang_names) if lang_names else "JavaScript"

        # Build tasks based on what was detected
        tasks = [
            {"id": str(uuid.uuid4()), "title": "Code Quality Analysis", "description": f"Analyze code quality across {lang_str} codebase", "status": "pending", "priority": "high"},
            {"id": str(uuid.uuid4()), "title": "Security Scan", "description": "Run security vulnerability scan on all files", "status": "pending", "priority": "high"},
            {"id": str(uuid.uuid4()), "title": "Dependency Audit", "description": "Check dependencies for known vulnerabilities and outdated packages", "status": "pending", "priority": "medium"},
            {"id": str(uuid.uuid4()), "title": "Performance Review", "description": "Identify performance bottlenecks and optimization opportunities", "status": "pending", "priority": "medium"},
            {"id": str(uuid.uuid4()), "title": "Documentation Review", "description": "Review and improve project documentation", "status": "pending", "priority": "low"},
        ]

        workflow = {
            "id": str(uuid.uuid4()),
            "title": f"Review Pipeline: {repo_name}",
            "name": f"Review Pipeline: {repo_name}",
            "description": f"Automated code review and analysis pipeline for {repo_name}. Includes quality analysis, security scanning, dependency audit, performance review, and documentation check.",
            "status": "draft",
            "tasks": tasks,
            "risk_level": "medium",
            "project_id": project_id,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        _WORKFLOWS.insert(0, workflow)
        _persist_workflows()

        # Log activity
        log_activity(
            "workflow", "created",
            f"Auto-created workflow: Review Pipeline: {repo_name}",
            f"Workflow with {len(tasks)} tasks auto-created on repo import",
            "workflow", workflow["id"],
        )

        logger.info(f"Auto-workflow: created pipeline for {repo_name} with {len(tasks)} tasks, project_id={project_id}")
    except Exception as e:
        logger.error(f"Auto-workflow failed for {repo_name}: {e}")


def _deep_analyze(repo_path: str) -> dict:
    """Comprehensive security, quality, and best-practice analysis."""
    import re
    base = _analyze_repository(repo_path)
    findings = []
    file_tree = []
    stats = {"security": 0, "quality": 0, "best_practice": 0, "dependency": 0}

    # ─── Security Patterns ────────────────────────────────────────────
    SEC = []

    # SQL Injection
    SEC.append((r'(?:query|execute|cursor\.execute|raw)\s*\(\s*["\'].*\+', "Any", "HIGH",
                "SQL Injection: string concatenation in query"))
    SEC.append((r'\.format\s*\(.*(?:SELECT|INSERT|UPDATE|DELETE|WHERE)', "Any", "HIGH",
                "SQL Injection: .format() in SQL query"))
    SEC.append((r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE|WHERE).*\{', "Python", "HIGH",
                "SQL Injection: f-string in SQL query"))
    SEC.append((r'\$\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE|WHERE)', "JavaScript", "HIGH",
                "SQL Injection: template literal in SQL query"))

    # XSS
    SEC.append((r'innerHTML\s*=', "JavaScript", "HIGH",
                "XSS: innerHTML assignment — use textContent or sanitize"))
    SEC.append((r'dangerouslySetInnerHTML', "React/JSX", "HIGH",
                "XSS: dangerouslySetInnerHTML — sanitize with DOMPurify"))
    SEC.append((r'document\.write\s*\(', "JavaScript", "HIGH",
                "XSS: document.write() — use DOM methods instead"))
    SEC.append((r'\.html\s*\(', "jQuery", "MEDIUM",
                "XSS: jQuery .html() — use .text() or sanitize"))
    SEC.append((r'v-html\s*=', "Vue", "HIGH",
                "XSS: v-html directive — sanitize content"))
    SEC.append((r'ng-bind-html\s*=', "Angular", "HIGH",
                "XSS: ng-bind-html — use $sce.trustAsHtml carefully"))

    # Command Injection
    SEC.append((r'exec\s*\(', "Python", "HIGH",
                "Command Injection: exec() — use subprocess with list args"))
    SEC.append((r'eval\s*\(', "JavaScript", "HIGH",
                "Command Injection: eval() — never use on user input"))
    SEC.append((r'os\.system\s*\(', "Python", "HIGH",
                "Command Injection: os.system() — use subprocess.run()"))
    SEC.append((r'subprocess\.call\s*\(\s*["\']', "Python", "MEDIUM",
                "Command Injection: shell=True risk — use list args"))
    SEC.append((r'child_process\.exec\s*\(', "JavaScript", "HIGH",
                "Command Injection: child_process.exec — use execFile"))
    SEC.append((r'spawn\s*\(', "JavaScript", "MEDIUM",
                "Command Injection: spawn with shell option — verify safe"))

    # Hardcoded Secrets
    SEC.append((r'(?i)password\s*[=:]\s*["\'][^"\']{3,}', "Any", "CRITICAL",
                "Hardcoded password found"))
    SEC.append((r'(?i)api[_-]?key\s*[=:]\s*["\'][^"\']{8,}', "Any", "HIGH",
                "Hardcoded API key found"))
    SEC.append((r'(?i)(?:secret|token)\s*[=:]\s*["\'][^"\']{8,}', "Any", "HIGH",
                "Hardcoded secret/token found"))
    SEC.append((r'(?i)aws[_-]?(?:access|secret)\s*[=:]\s*["\']', "Any", "CRITICAL",
                "AWS credentials hardcoded"))
    SEC.append((r'(?i)private[_-]?key\s*[=:]\s*["\']', "Any", "CRITICAL",
                "Private key hardcoded"))
    SEC.append((r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Any", "CRITICAL",
                "Private key in source code"))
    SEC.append((r'(?i)(?:jwt|bearer)\s*[_-]?secret\s*[=:]\s*["\']', "Any", "CRITICAL",
                "JWT/Bearer secret hardcoded"))

    # Insecure Crypto
    SEC.append((r'(?:md5|sha1)\s*\(', "Python", "MEDIUM",
                "Weak crypto: MD5/SHA1 — use SHA256+ or bcrypt for passwords"))
    SEC.append((r'crypto\.createHash\s*\(\s*["\'](?:md5|sha1)', "JavaScript", "MEDIUM",
                "Weak crypto: MD5/SHA1 — use SHA256+"))
    SEC.append((r'MessageDigest\.getInstance\s*\(\s*["\'](?:MD5|SHA-1)', "Java", "MEDIUM",
                "Weak crypto: MD5/SHA-1 — use SHA-256+"))

    # Path Traversal
    SEC.append((r'open\s*\(.*\+.*(?:\.\.\/|\.\.\\\\)', "Python", "HIGH",
                "Path Traversal: user input in file path"))
    SEC.append((r'readFile\s*\(.*\+', "JavaScript", "MEDIUM",
                "Path Traversal: verify file path is sanitized"))

    # Insecure Deserialization
    SEC.append((r'pickle\.loads?\s*\(', "Python", "HIGH",
                "Insecure Deserialization: pickle on untrusted data — use json"))
    SEC.append((r'yaml\.load\s*\(', "Python", "MEDIUM",
                "Unsafe YAML: use yaml.safe_load()"))
    SEC.append((r'JSON\.parse\s*\(.*req\.', "JavaScript", "MEDIUM",
                "Validate JSON input before parsing"))

    # SSRF
    SEC.append((r'requests\.(?:get|post|put|delete)\s*\(.*\+', "Python", "MEDIUM",
                "SSRF risk: verify URL is not user-controlled"))
    SEC.append((r'fetch\s*\(.*\+', "JavaScript", "MEDIUM",
                "SSRF risk: verify URL is not user-controlled"))

    # Insecure Cookies / Sessions
    SEC.append((r'setCookie\s*\(.*(?:httpOnly|secure|sameSite)\s*[=:]\s*(?:false|["\']?none)', "JavaScript", "MEDIUM",
                "Insecure cookie: missing httpOnly/secure/sameSite flag"))
    SEC.append((r'cookie\s*=.*(?:expires|max-age)', "Python", "LOW",
                "Cookie set — verify httpOnly and secure flags are used"))
    SEC.append((r'session\s*\(\s*\)', "JavaScript", "MEDIUM",
                "Express session without config — set secret, httpOnly, secure"))
    SEC.append((r'credentials?\s*[:=]\s*["\']include', "JavaScript", "LOW",
                "CORS credentials enabled — verify origin is restricted"))

    # Missing CSRF Protection
    SEC.append((r'router\.(?:post|put|delete)\s*\(', "JavaScript", "MEDIUM",
                "State-changing route — verify CSRF protection is applied"))
    SEC.append((r'@(?:app|router)\.(?:post|put|delete)\s*\(', "Python", "MEDIUM",
                "State-changing endpoint — verify CSRF protection"))

    # Insecure HTTP
    SEC.append((r'http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)', "Any", "MEDIUM",
                "HTTP URL (not HTTPS) — use HTTPS in production"))
    SEC.append((r'allow_http_redirects\s*=\s*True', "Python", "LOW",
                "HTTP redirects enabled — consider disabling for sensitive apps"))

    # Missing Security Headers
    SEC.append((r'X-Frame-Options', "Any", "LOW", "X-Frame-Options header — prevent clickjacking"))
    SEC.append((r'Content-Security-Policy', "Any", "LOW", "CSP header — prevent XSS"))
    SEC.append((r'X-Content-Type-Options', "Any", "LOW", "X-Content-Type-Options — prevent MIME sniffing"))
    SEC.append((r'Strict-Transport-Security', "Any", "LOW", "HSTS header — enforce HTTPS"))

    # Debug / Development Leaks
    SEC.append((r'(?i)debug\s*[:=]\s*(?:true|1|on)', "Any", "MEDIUM",
                "Debug mode enabled — disable in production"))
    SEC.append((r'(?i)stacktrace|stack_trace', "JavaScript", "MEDIUM",
                "Stack trace exposed — hide from users"))
    SEC.append((r'(?i)verbose\s*[:=]\s*(?:true|1|on)', "Any", "LOW",
                "Verbose logging — may expose sensitive data"))
    SEC.append((r'process\.env\b', "JavaScript", "LOW",
                "Environment variable access — ensure secrets are not logged"))

    # Missing Auth / Authorization
    SEC.append((r'@(?:app|router)\.(?:get|post|put|delete)\s*\([^)]*\)\s*(?:async\s+)?def\s+\w+', "Python", "LOW",
                "Endpoint defined — verify authentication is enforced"))
    SEC.append((r'router\.(?:get|post|put|delete)\s*\([^)]*\)', "JavaScript", "LOW",
                "Route defined — verify auth middleware is applied"))

    # ─── Code Quality Patterns ────────────────────────────────────────
    QUAL = []
    QUAL.append((r'except\s*:', "Python", "MEDIUM",
                 "Bare except — catch specific exceptions"))
    QUAL.append((r'except\s+Exception\s*:', "Python", "LOW",
                 "Broad exception — consider more specific handling"))
    QUAL.append((r'import\s+\*', "Python", "MEDIUM",
                 "Wildcard import — use explicit imports"))
    QUAL.append((r'console\.log\s*\(', "JavaScript", "LOW",
                 "console.log in production code"))
    QUAL.append((r'debugger\b', "JavaScript", "MEDIUM",
                 "debugger statement left in code"))
    QUAL.append((r'print\s*\(', "Python", "LOW",
                 "print() — consider using logging module"))
    QUAL.append((r'System\.out\.print', "Java", "LOW",
                 "System.out.println — use SLF4J/Log4j"))
    QUAL.append((r'var\s+', "JavaScript", "LOW",
                 "Use 'let' or 'const' instead of 'var'"))
    QUAL.append((r'==\s*(?:null|undefined|0)', "JavaScript", "LOW",
                 "Use === instead of =="))
    QUAL.append((r'TODO|FIXME|HACK|XXX|WORKAROUND', "Any", "LOW",
                 "Technical debt marker found"))
    QUAL.append((r'catch\s*\([^)]*\)\s*\{\s*\}', "JavaScript", "MEDIUM",
                 "Empty catch block — errors are silently swallowed"))
    QUAL.append((r'except\s+\w+.*:\s*pass\s*$', "Python", "MEDIUM",
                 "Silent exception pass — log or handle the error"))

    # ─── Best Practice Patterns ───────────────────────────────────────
    BEST = []
    BEST.append((r'no(?:rate|_rate)_?limit', "Any", "MEDIUM",
                 "Rate limiting may not be configured"))
    BEST.append((r'(?i)cors.*\*', "Any", "MEDIUM",
                 "CORS allows all origins — restrict to trusted domains"))
    BEST.append((r'(?i)debug\s*[:=]\s*true', "Any", "MEDIUM",
                 "Debug mode enabled — disable in production"))
    BEST.append((r'(?i)NODE_ENV\s*(?:=|:)\s*["\']?development', "JavaScript", "LOW",
                 "Development mode — ensure production config exists"))
    BEST.append((r'(?i)ALLOWED_HOSTS\s*=\s*\[.*\*', "Python", "MEDIUM",
                 "Django ALLOWED_HOSTS is wildcard"))

    # ─── Dependency Patterns ──────────────────────────────────────────
    DEP = []
    # Check package.json for known vulnerable patterns
    pkg_path = os.path.join(repo_path, "package.json")
    if os.path.isfile(pkg_path):
        try:
            with open(pkg_path, "r") as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            VULN_NPM = {
                "lodash": "< 4.17.21 — prototype pollution",
                "express-session": "< 1.17.0 — session fixation",
                "minimist": "< 0.2.1 — prototype pollution",
                "node-fetch": "< 2.6.7 — URL redirect",
                "ws": "< 7.4.6 — ReDoS",
                "jsonwebtoken": "< 9.0.0 — insecure key handling",
                "mongoose": "< 5.13.0 — prototype pollution",
                "axios": "< 0.21.1 — SSRF",
                "url-parse": "< 1.5.2 — auth bypass",
                "glob-parent": "< 5.1.2 — ReDoS",
                "browserslist": "< 4.16.5 — ReDoS",
                "trim": "< 0.0.3 — ReDoS",
                "nth-check": "< 2.0.1 — ReDoS",
                "css-what": "< 5.0.1 — ReDoS",
                "hosted-git-info": "< 2.8.9 — ReDoS",
                "ssri": "< 8.0.1 — ReDoS",
                "tar": "< 6.1.11 — arbitrary file overwrite",
                "tough-cookie": "< 4.1.3 — prototype pollution",
                "xml2js": "< 0.4.19 — prototype pollution",
                "shell-quote": "< 1.7.3 — command injection",
                "merge-deep": "< 3.0.2 — prototype pollution",
                "set-value": "< 2.0.1 — prototype pollution",
                "kind-of": "< 6.0.3 — type confusion",
                "micromatch": "< 4.0.8 — ReDoS",
            }
            for pkg_name, vuln_info in VULN_NPM.items():
                if pkg_name in deps:
                    DEP.append(("npm", pkg_name, deps[pkg_name], vuln_info))
        except (json.JSONDecodeError, OSError):
            pass

    # Check requirements.txt / setup.py for Python vulns
    for req_file in ["requirements.txt", "requirements-dev.txt"]:
        req_path = os.path.join(repo_path, req_file)
        if os.path.isfile(req_path):
            try:
                with open(req_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        pkg_name = re.split(r'[><=!~]', line)[0].strip().lower()
                        VULN_PY = {
                            "flask": "Check version < 2.0 — security fixes",
                            "django": "Check version < 3.2 — LTS security fixes",
                            "requests": "Check version < 2.28.0 — security fixes",
                            "urllib3": "Check version < 1.26.5 — CRLF injection",
                            "jinja2": "Check version < 3.0 — sandbox escape",
                            "cryptography": "Check version < 38.0 — vulnerabilities",
                            "pyyaml": "Check version < 6.0 — arbitrary code execution",
                            "pillow": "Check version < 9.0 — buffer overflow",
                            "sqlalchemy": "Check version < 1.4 — SQL injection",
                            "aiohttp": "Check version < 3.8.0 — HTTP request smuggling",
                            "gunicorn": "Check version < 21.0 — HTTP request smuggling",
                        }
                        if pkg_name in VULN_PY:
                            DEP.append(("pypi", pkg_name, line, VULN_PY[pkg_name]))
            except OSError:
                pass

    # ─── File-by-file scanning ────────────────────────────────────────
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if not _should_ignore(os.path.join(root, d))]
        rel_root = os.path.relpath(root, repo_path)

        for file in files:
            filepath = os.path.join(root, file)
            if _should_ignore(filepath):
                continue

            rel_path = os.path.join(rel_root, file) if rel_root != "." else file
            ext = os.path.splitext(file)[1].lower()

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\n")
            except (OSError, UnicodeDecodeError):
                continue

            file_tree.append({"path": rel_path, "size": len(content), "ext": ext})

            # Determine language from extension
            LANG_EXT = {
                ".py": "Python", ".js": "JavaScript", ".jsx": "React/JSX",
                ".ts": "TypeScript", ".tsx": "React/TSX", ".java": "Java",
                ".go": "Go", ".rb": "Ruby", ".php": "PHP", ".rs": "Rust",
                ".cs": "C#", ".cpp": "C++", ".c": "C", ".swift": "Swift",
                ".kt": "Kotlin", ".vue": "Vue", ".html": "HTML", ".css": "CSS",
            }
            file_lang = LANG_EXT.get(ext, "")

            # Run all pattern checks
            for pattern, lang, severity, desc in SEC + QUAL + BEST:
                if lang != "Any" and lang != file_lang:
                    continue
                matches = list(re.finditer(pattern, content))
                for m in matches[:5]:  # max 5 per pattern per file
                    line_no = content[:m.start()].count("\n") + 1
                    category = "security" if (pattern, lang, severity, desc) in SEC else \
                               "quality" if (pattern, lang, severity, desc) in QUAL else "best_practice"
                    if (pattern, lang, severity, desc) in SEC:
                        stats["security"] += 1
                    elif (pattern, lang, severity, desc) in QUAL:
                        stats["quality"] += 1
                    else:
                        stats["best_practice"] += 1
                    findings.append({
                        "file": rel_path,
                        "line": line_no,
                        "severity": severity,
                        "category": category,
                        "message": desc,
                        "language": file_lang or lang,
                        "snippet": lines[line_no - 1].strip()[:120] if line_no <= len(lines) else "",
                    })

            # File-level quality checks
            line_count = len(lines)
            if line_count > 500:
                findings.append({
                    "file": rel_path, "line": 1, "severity": "MEDIUM",
                    "category": "quality",
                    "message": f"Large file ({line_count} lines) — consider splitting",
                    "language": file_lang, "snippet": "",
                })

            # Check for function complexity (deeply nested code)
            max_indent = 0
            for line in lines:
                stripped = line.lstrip()
                if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
                    indent = len(line) - len(stripped)
                    max_indent = max(max_indent, indent)
            if max_indent >= 20:
                findings.append({
                    "file": rel_path, "line": 1, "severity": "MEDIUM",
                    "category": "quality",
                    "message": f"Deeply nested code (indent level {max_indent}) — refactor for readability",
                    "language": file_lang, "snippet": "",
                })

            # Check for missing error handling in API routes (Express)
            if file_lang in ("JavaScript", "TypeScript"):
                if re.search(r'router\.(?:get|post|put|delete)\s*\(', content):
                    if not re.search(r'try|catch|\.catch|async.*await', content):
                        findings.append({
                            "file": rel_path, "line": 1, "severity": "MEDIUM",
                            "category": "best_practice",
                            "message": "Route handler without error handling — add try/catch",
                            "language": file_lang, "snippet": "",
                        })

    # Add dependency findings
    for ecosystem, pkg, version, info in DEP:
        stats["dependency"] += 1
        findings.append({
            "file": f"{ecosystem}:{pkg}",
            "line": 0,
            "severity": "HIGH",
            "category": "dependency",
            "message": f"{pkg}@{version} — {info}",
            "language": ecosystem,
            "snippet": "",
        })

    # Deduplicate findings
    seen = set()
    unique = []
    for f in findings:
        key = (f["file"], f["line"], f["message"])
        if key not in seen:
            seen.add(key)
            unique.append(f)

    # Sort: CRITICAL first, then HIGH, MEDIUM, LOW
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    unique.sort(key=lambda x: (order.get(x["severity"], 9), x["file"]))

    base["findings"] = unique
    base["file_tree"] = sorted(file_tree, key=lambda x: x["path"])
    base["stats"] = stats
    return base


async def _import_git(url: str, target_dir: str) -> str:
    """Clone a git repository."""
    os.makedirs(target_dir, exist_ok=True)
    process = await asyncio.create_subprocess_exec(
        "git", "clone", "--depth", "1", "--single-branch", url, target_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
    if process.returncode != 0:
        raise Exception(f"Git clone failed: {stderr.decode('utf-8', errors='replace')}")
    return target_dir


async def _import_zip(zip_path: str, target_dir: str) -> str:
    """Extract a ZIP file, skipping ignored dirs/files and capping at MAX_ANALYSIS_FILES."""
    os.makedirs(target_dir, exist_ok=True)
    extracted = 0
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if _should_ignore(info.filename):
                continue
            if extracted >= MAX_ANALYSIS_FILES:
                break
            z.extract(info, target_dir)
            extracted += 1
    # If single top-level dir, use it as root
    entries = [e for e in os.listdir(target_dir) if not e.startswith(".") or e == ".gitignore"]
    if len(entries) == 1:
        single = os.path.join(target_dir, entries[0])
        if os.path.isdir(single):
            return single
    return target_dir


async def _import_folder(source: str, target_dir: str) -> str:
    """Copy a local folder."""
    os.makedirs(target_dir, exist_ok=True)
    dest = os.path.join(target_dir, os.path.basename(source))
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    return dest


# --- Router ---
router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("")
async def list_repositories():
    seen = set()
    unique = {}
    for rid, repo in _repositories.items():
        if rid not in seen:
            seen.add(rid)
            unique[rid] = repo
    if len(unique) != len(_repositories):
        _repositories.clear()
        _repositories.update(unique)
        _persist_repos()
    return {"status": "success", "data": list(_repositories.values())}


@router.get("/{repo_id}")
async def get_repository(repo_id: str):
    repo = _repositories.get(repo_id)
    if not repo:
        return {"status": "error", "message": "Repository not found"}
    return {"status": "success", "data": repo}


@router.post("/import")
async def import_repository(request: RepositoryCreate):
    repo_id = str(uuid.uuid4())
    repo_dir = os.path.join(TEMP_DIR, repo_id)

    info = RepositoryInfo(
        id=repo_id,
        name=request.name,
        description=request.description,
        status="importing",
        import_method=request.import_method,
        source_url=request.source_url,
        local_path=repo_dir,
        created_at=datetime.now(UTC).isoformat(),
    )
    _repositories[repo_id] = info
    _persist_repos()

    try:
        source = request.source_url or request.source_path
        if not source:
            raise Exception("Source URL or path is required")

        if request.import_method == "git":
            local_path = await _import_git(source, repo_dir)
        elif request.import_method == "zip":
            local_path = await _import_zip(source, repo_dir)
        elif request.import_method == "folder":
            local_path = await _import_folder(source, repo_dir)
        else:
            raise Exception(f"Unknown import method: {request.import_method}")

        info.local_path = local_path
        info.status = "analyzing"

        # Analyze the repository (run in thread pool to avoid blocking event loop)
        analysis = await asyncio.to_thread(_analyze_repository, local_path)
        info.file_count = analysis["file_count"]
        info.total_lines = analysis["total_lines"]
        info.languages = analysis["languages"]
        info.frameworks = analysis["frameworks"]
        info.status = "ready"
        info.analyzed_at = datetime.now(UTC).isoformat()
        _persist_repos()

        # Log activity
        lang_names = [l.get("name", l) for l in info.languages[:3]] if info.languages else []
        log_activity(
            "repository", "imported",
            f"Imported repository: {request.name}",
            f"Analyzed {info.file_count} files, {info.total_lines} lines. Languages: {', '.join(lang_names) if lang_names else 'detected'}",
            "repository", repo_id,
        )

        # Auto-generate documentation in background
        asyncio.create_task(_auto_generate_docs(repo_id, request.name))

        return {"status": "success", "data": info, "message": "Repository imported successfully"}

    except Exception as e:
        info.status = "error"
        info.error_message = str(e)
        _persist_repos()
        return {"status": "error", "message": str(e)}


@router.post("/import/upload")
async def upload_repository(
    name: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
):
    repo_id = str(uuid.uuid4())
    repo_dir = os.path.join(TEMP_DIR, repo_id)

    info = RepositoryInfo(
        id=repo_id,
        name=name,
        description=description,
        status="importing",
        import_method="zip",
        source_url=None,
        local_path=repo_dir,
        created_at=datetime.now(UTC).isoformat(),
    )
    _repositories[repo_id] = info
    _persist_repos()

    try:
        # Save uploaded file
        upload_dir = os.path.join(TEMP_DIR, f"upload_{repo_id}")
        os.makedirs(upload_dir, exist_ok=True)
        upload_path = os.path.join(upload_dir, file.filename or "upload.zip")

        content = await file.read()
        if len(content) > 100 * 1024 * 1024:  # 100MB limit
            info.status = "error"
            info.error_message = "File too large (max 100MB)"
            _persist_repos()
            return {"status": "error", "message": "File too large (max 100MB)"}
        with open(upload_path, "wb") as f:
            f.write(content)

        # Extract ZIP
        local_path = await _import_zip(upload_path, repo_dir)
        info.local_path = local_path
        info.status = "analyzing"

        # Analyze (run in thread pool to avoid blocking event loop)
        analysis = await asyncio.to_thread(_analyze_repository, local_path)
        info.file_count = analysis["file_count"]
        info.total_lines = analysis["total_lines"]
        info.languages = analysis["languages"]
        info.frameworks = analysis["frameworks"]
        info.status = "ready"
        info.analyzed_at = datetime.now(UTC).isoformat()

        # Cleanup upload temp
        shutil.rmtree(upload_dir, ignore_errors=True)

        # Auto-generate documentation in background
        asyncio.create_task(_auto_generate_docs(repo_id, name))

        return {"status": "success", "data": info, "message": "Repository uploaded and imported successfully"}

    except Exception as e:
        info.status = "error"
        info.error_message = str(e)
        return {"status": "error", "message": str(e)}


@router.post("/import/folder")
async def upload_folder_init(
    name: str = Form(...),
    description: str | None = Form(None),
    files: list[UploadFile] = File(...),
    paths: str | None = Form(None),
):
    """Upload folder files. If repo_id is provided, appends to existing repo (chunked)."""
    repo_id = str(uuid.uuid4())
    repo_dir = os.path.join(TEMP_DIR, repo_id)

    info = RepositoryInfo(
        id=repo_id,
        name=name,
        description=description,
        status="importing",
        import_method="folder",
        source_url=None,
        local_path=repo_dir,
        created_at=datetime.now(UTC).isoformat(),
    )
    _repositories[repo_id] = info
    _persist_repos()

    try:
        parsed_paths = json.loads(paths) if paths else None

        for i, upload_file in enumerate(files):
            if parsed_paths and i < len(parsed_paths):
                rel_path = parsed_paths[i]
            else:
                rel_path = upload_file.filename or f"file_{i}"

            # Skip ignored files and dirs
            if _should_ignore(rel_path):
                continue

            file_path = os.path.join(repo_dir, rel_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            content = await upload_file.read()
            with open(file_path, "wb") as f:
                f.write(content)

        info.local_path = repo_dir
        info.status = "analyzing"

        analysis = await asyncio.to_thread(_analyze_repository, repo_dir)
        info.file_count = analysis["file_count"]
        info.total_lines = analysis["total_lines"]
        info.languages = analysis["languages"]
        info.frameworks = analysis["frameworks"]
        info.status = "ready"
        info.analyzed_at = datetime.now(UTC).isoformat()

        # Auto-generate documentation in background
        asyncio.create_task(_auto_generate_docs(repo_id, name))

        return {"status": "success", "data": info, "message": "Folder uploaded and imported successfully"}

    except Exception as e:
        info.status = "error"
        info.error_message = str(e)
        return {"status": "error", "message": str(e)}


@router.post("/import/folder/init")
async def folder_init(
    name: str = Form(...),
    description: str | None = Form(None),
):
    """Step 1: Create repo entry and return repo_id for chunked upload."""
    repo_id = str(uuid.uuid4())
    repo_dir = os.path.join(TEMP_DIR, repo_id)
    os.makedirs(repo_dir, exist_ok=True)

    info = RepositoryInfo(
        id=repo_id,
        name=name,
        description=description,
        status="importing",
        import_method="folder",
        source_url=None,
        local_path=repo_dir,
        created_at=datetime.now(UTC).isoformat(),
    )
    _repositories[repo_id] = info
    _persist_repos()
    return {"status": "success", "data": {"repo_id": repo_id}}


@router.post("/import/folder/{repo_id}/batch")
async def folder_batch(
    repo_id: str,
    files: list[UploadFile] = File(...),
    paths: str | None = Form(None),
):
    """Step 2: Upload a batch of files to an existing repo."""
    info = _repositories.get(repo_id)
    if not info:
        return {"status": "error", "message": "Repository not found"}

    try:
        parsed_paths = json.loads(paths) if paths else None

        for i, upload_file in enumerate(files):
            if parsed_paths and i < len(parsed_paths):
                rel_path = parsed_paths[i]
            else:
                rel_path = upload_file.filename or f"file_{i}"

            # Skip ignored files and dirs
            if _should_ignore(rel_path):
                continue

            file_path = os.path.join(info.local_path, rel_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            content = await upload_file.read()
            with open(file_path, "wb") as f:
                f.write(content)

        return {"status": "success", "data": {"repo_id": repo_id, "files_received": len(files)}}

    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/import/folder/{repo_id}/finalize")
async def folder_finalize(repo_id: str):
    """Step 3: Run analysis on a fully-uploaded repo."""
    info = _repositories.get(repo_id)
    if not info:
        return {"status": "error", "message": "Repository not found"}

    try:
        info.status = "analyzing"
        analysis = await asyncio.to_thread(_analyze_repository, info.local_path)
        info.file_count = analysis["file_count"]
        info.total_lines = analysis["total_lines"]
        info.languages = analysis["languages"]
        info.frameworks = analysis["frameworks"]
        info.status = "ready"
        info.analyzed_at = datetime.now(UTC).isoformat()
        _persist_repos()

        lang_names = [l.get("name", l) for l in info.languages[:3]] if info.languages else []
        log_activity(
            "repository", "imported",
            f"Imported repository: {info.name}",
            f"Analyzed {info.file_count} files, {info.total_lines} lines. Languages: {', '.join(lang_names) if lang_names else 'detected'}",
            "repository", repo_id,
        )

        # Auto-generate documentation in background
        asyncio.create_task(_auto_generate_docs(repo_id, info.name))

        return {"status": "success", "data": info, "message": "Folder imported successfully"}

    except Exception as e:
        info.status = "error"
        info.error_message = str(e)
        _persist_repos()
        return {"status": "error", "message": str(e)}


@router.post("/import/local-folder")
async def import_local_folder(
    name: str = Form(...),
    description: str | None = Form(None),
    local_path: str = Form(...),
):
    """Import a local directory by path — no file upload needed."""
    repo_id = str(uuid.uuid4())
    repo_dir = os.path.join(TEMP_DIR, repo_id)

    info = RepositoryInfo(
        id=repo_id,
        name=name,
        description=description,
        status="importing",
        import_method="folder",
        source_url=None,
        local_path=repo_dir,
        created_at=datetime.now(UTC).isoformat(),
    )
    _repositories[repo_id] = info
    _persist_repos()

    try:
        source = local_path.strip()
        if not os.path.isdir(source):
            raise Exception(f"Directory not found: {source}")

        shutil.copytree(source, repo_dir)
        info.local_path = repo_dir
        info.status = "analyzing"

        analysis = await asyncio.to_thread(_analyze_repository, repo_dir)
        info.file_count = analysis["file_count"]
        info.total_lines = analysis["total_lines"]
        info.languages = analysis["languages"]
        info.frameworks = analysis["frameworks"]
        info.status = "ready"
        info.analyzed_at = datetime.now(UTC).isoformat()
        _persist_repos()

        log_activity(
            "repository", "imported",
            f"Imported repository: {name}",
            f"Analyzed {info.file_count} files, {info.total_lines} lines.",
            "repository", repo_id,
        )

        # Auto-generate documentation in background
        asyncio.create_task(_auto_generate_docs(repo_id, name))

        return {"status": "success", "data": info, "message": "Folder imported successfully"}

    except Exception as e:
        info.status = "error"
        info.error_message = str(e)
        _persist_repos()
        return {"status": "error", "message": str(e)}


@router.delete("/{repo_id}")
async def delete_repository(repo_id: str):
    if repo_id not in _repositories:
        return {"status": "error", "message": "Repository not found"}

    info = _repositories[repo_id]
    try:
        if os.path.exists(info.local_path):
            shutil.rmtree(info.local_path)
    except OSError:
        pass

    del _repositories[repo_id]
    _persist_repos()
    return {"status": "success", "data": {"deleted": True}, "message": "Repository deleted"}


@router.post("/{repo_id}/analyze")
async def reanalyze_repository(repo_id: str):
    repo = _repositories.get(repo_id)
    if not repo:
        return {"status": "error", "message": "Repository not found"}

    if not os.path.isdir(repo.local_path):
        return {"status": "error", "message": "Repository folder not found on disk"}

    repo.status = "analyzing"
    _persist_repos()

    try:
        analysis = await asyncio.to_thread(_deep_analyze, repo.local_path)
        repo.file_count = analysis["file_count"]
        repo.total_lines = analysis["total_lines"]
        repo.languages = analysis["languages"]
        repo.frameworks = analysis["frameworks"]
        repo.status = "ready"
        repo.analyzed_at = datetime.now(UTC).isoformat()
        _persist_repos()

        return {"status": "success", "data": {
            "id": repo.id, "name": repo.name, "status": repo.status,
            "file_count": repo.file_count, "total_lines": repo.total_lines,
            "languages": repo.languages, "frameworks": repo.frameworks,
            "analyzed_at": repo.analyzed_at,
            "findings": analysis.get("findings", []),
            "file_tree": analysis.get("file_tree", []),
        }, "message": "Re-analysis complete"}
    except Exception as e:
        repo.status = "error"
        repo.error_message = str(e)
        _persist_repos()
        return {"status": "error", "message": str(e)}


@router.get("/{repo_id}/summary")
async def get_summary(repo_id: str):
    repo = _repositories.get(repo_id)
    if not repo:
        return {"status": "error", "message": "Repository not found"}

    return {
        "status": "success",
        "data": {
            "id": repo.id,
            "name": repo.name,
            "description": repo.description,
            "status": repo.status,
            "file_count": repo.file_count,
            "total_lines": repo.total_lines,
            "languages": repo.languages,
            "frameworks": repo.frameworks,
            "created_at": repo.created_at,
            "analyzed_at": repo.analyzed_at,
        },
    }
