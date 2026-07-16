"""Installation and setup automation."""

import os
import sys
import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path


@dataclass
class InstallStep:
    name: str
    description: str
    status: str = "pending"
    duration_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class InstallConfig:
    install_dir: str = "./forgeai"
    profile: str = "default"
    features: list[str] = field(default_factory=lambda: ["repositories", "knowledge", "workflows"])
    ai_provider: str = "ollama"
    database: str = "postgresql"
    cache: str = "redis"


class InstallerEngine:
    def __init__(self):
        self.steps_executed: int = 0

    def check_prerequisites(self) -> list[InstallStep]:
        return [
            self.check_python_version(),
            self.check_node_version(),
            self.check_docker(),
            self.check_postgresql(),
            self.check_redis(),
            self.check_ollama(),
        ]

    def installdependencies(self) -> list[InstallStep]:
        steps = []

        pip_step = InstallStep(
            name="pip_packages",
            description="Installing Python dependencies from requirements.txt",
            status="in_progress",
        )
        start = time.time()
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                check=True,
                capture_output=True,
                timeout=300,
            )
            pip_step.status = "completed"
        except FileNotFoundError:
            pip_step.status = "completed"
            pip_step.error = "requirements.txt not found, skipping"
        except subprocess.CalledProcessError as exc:
            pip_step.status = "failed"
            pip_step.error = exc.stderr.decode()[:500] if exc.stderr else str(exc)
        except subprocess.TimeoutExpired:
            pip_step.status = "failed"
            pip_step.error = "pip install timed out after 300s"
        pip_step.duration_ms = round((time.time() - start) * 1000, 1)
        steps.append(pip_step)
        self.steps_executed += 1

        npm_step = InstallStep(
            name="npm_packages",
            description="Installing Node.js dependencies (if package.json exists)",
            status="in_progress",
        )
        start = time.time()
        if os.path.exists("package.json"):
            try:
                subprocess.run(["npm", "install"], check=True, capture_output=True, timeout=120)
                npm_step.status = "completed"
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
                npm_step.status = "failed"
                npm_step.error = str(exc)[:500]
        else:
            npm_step.status = "completed"
            npm_step.error = "No package.json found, skipping"
        npm_step.duration_ms = round((time.time() - start) * 1000, 1)
        steps.append(npm_step)
        self.steps_executed += 1

        return steps

    def setup_database(self) -> InstallStep:
        step = InstallStep(
            name="database_setup",
            description="Initializing PostgreSQL database and running migrations",
            status="in_progress",
        )
        start = time.time()

        try:
            import psycopg2

            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                dbname="postgres",
                user=os.getenv("POSTGRES_USER", "forgeai"),
                password=os.getenv("POSTGRES_PASSWORD", ""),
                connect_timeout=10,
            )
            conn.autocommit = True
            cur = conn.cursor()

            db_name = os.getenv("POSTGRES_DB", "forgeai")
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{db_name}"')

            cur.close()
            conn.close()

            step.status = "completed"
        except ImportError:
            step.status = "skipped"
            step.error = "psycopg2 not installed"
        except Exception as exc:
            step.status = "failed"
            step.error = str(exc)[:500]

        step.duration_ms = round((time.time() - start) * 1000, 1)
        self.steps_executed += 1
        return step

    def setup_cache(self) -> InstallStep:
        step = InstallStep(
            name="cache_setup",
            description="Verifying Redis connection and configuration",
            status="in_progress",
        )
        start = time.time()

        try:
            import redis
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                socket_connect_timeout=5,
            )
            r.ping()
            step.status = "completed"
        except ImportError:
            step.status = "skipped"
            step.error = "redis-py not installed"
        except Exception as exc:
            step.status = "failed"
            step.error = str(exc)[:500]

        step.duration_ms = round((time.time() - start) * 1000, 1)
        self.steps_executed += 1
        return step

    def setup_ai_provider(self) -> InstallStep:
        step = InstallStep(
            name="ai_provider_setup",
            description="Verifying Ollama AI provider connection",
            status="in_progress",
        )
        start = time.time()

        try:
            import urllib.request
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            req = urllib.request.Request(f"{ollama_host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                model_count = len(data.get("models", []))
                step.status = "completed"
                step.error = f"{model_count} models available"
        except Exception as exc:
            step.status = "failed"
            step.error = str(exc)[:500]

        step.duration_ms = round((time.time() - start) * 1000, 1)
        self.steps_executed += 1
        return step

    def generate_config(self, config: InstallConfig) -> dict:
        generated = {
            "version": "1.0.0",
            "install_dir": config.install_dir,
            "profile": config.profile,
            "features": config.features,
            "database": {
                "engine": config.database,
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", 5432)),
                "name": os.getenv("POSTGRES_DB", "forgeai"),
                "user": os.getenv("POSTGRES_USER", "forgeai"),
            },
            "cache": {
                "engine": config.cache,
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", 6379)),
            },
            "ai": {
                "provider": config.ai_provider,
                "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            },
            "paths": {
                "data": os.getenv("FORGEAI_DATA_DIR", "./data"),
                "logs": os.getenv("FORGEAI_LOG_DIR", "./logs"),
                "backups": "./backups",
            },
        }

        config_path = os.path.join(config.install_dir, "config.json")
        os.makedirs(config.install_dir, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(generated, f, indent=2)

        return generated

    def validate_installation(self) -> list[InstallStep]:
        steps = []

        step = InstallStep(name="validate_dirs", description="Checking data directories")
        start = time.time()
        base = os.getenv("FORGEAI_DATA_DIR", "./data")
        dirs_ok = all(
            os.path.isdir(os.path.join(base, d))
            for d in ["repositories", "knowledge"]
        )
        step.status = "completed" if dirs_ok else "failed"
        if not dirs_ok:
            step.error = "Some data directories are missing"
        step.duration_ms = round((time.time() - start) * 1000, 1)
        steps.append(step)

        step = InstallStep(name="validate_config", description="Checking configuration file")
        start = time.time()
        config_path = os.getenv("FORGEAI_CONFIG", "./config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    json.load(f)
                step.status = "completed"
            except json.JSONDecodeError:
                step.status = "failed"
                step.error = "Invalid JSON in config"
        else:
            step.status = "failed"
            step.error = "Config file not found"
        step.duration_ms = round((time.time() - start) * 1000, 1)
        steps.append(step)

        step = InstallStep(name="validate_imports", description="Checking Python imports")
        start = time.time()
        core_imports = ["fastapi", "uvicorn", "pydantic", "sqlalchemy"]
        missing = []
        for mod in core_imports:
            try:
                __import__(mod)
            except ImportError:
                missing.append(mod)
        step.status = "completed" if not missing else "failed"
        if missing:
            step.error = f"Missing: {', '.join(missing)}"
        step.duration_ms = round((time.time() - start) * 1000, 1)
        steps.append(step)

        return steps

    def get_install_guide(self) -> str:
        return """
ForgeAI Installation Guide
==========================

1. Prerequisites
   - Python 3.10+
   - PostgreSQL 14+
   - Redis 6+
   - Ollama (for AI features)
   - Node.js 18+ (for frontend)

2. Quick Install
   pip install -r requirements.txt
   forge init
   forge doctor

3. Configuration
   Copy config.example.json to config.json and update:
   - Database credentials
   - Redis connection
   - Ollama host URL
   - Data directory path

4. Database Setup
   createdb forgeai
   forge migrate

5. Start Services
   forge serve          # Start API server
   forge worker         # Start background worker
   ollama serve         # Start AI provider

6. Verify Installation
   forge doctor         # Run diagnostics
   curl localhost:8000/health

For detailed docs: https://forgeai.dev/docs
"""

    def get_quickstart(self) -> str:
        return """
ForgeAI Quick Start
===================

# Install
pip install forgeai

# Initialize a new project
forge init my-project
cd my-project

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
forge up

# Open browser
open http://localhost:3000

# Run diagnostics
forge doctor
"""


def check_python_version() -> InstallStep:
    step = InstallStep(
        name="python_version",
        description="Checking Python version (>=3.10 required)",
        status="in_progress",
    )
    start = time.time()
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 10:
        step.status = "completed"
        step.error = f"Python {major}.{minor} detected"
    else:
        step.status = "failed"
        step.error = f"Python {major}.{minor} found, >=3.10 required"
    step.duration_ms = round((time.time() - start) * 1000, 1)
    return step


def check_node_version() -> InstallStep:
    step = InstallStep(
        name="node_version",
        description="Checking Node.js version (>=18 required)",
        status="in_progress",
    )
    start = time.time()
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version_str = result.stdout.strip().lstrip("v")
        parts = version_str.split(".")
        major = int(parts[0])
        if major >= 18:
            step.status = "completed"
            step.error = f"Node.js v{version_str} detected"
        else:
            step.status = "failed"
            step.error = f"Node.js v{version_str} found, >=18 required"
    except FileNotFoundError:
        step.status = "failed"
        step.error = "Node.js not found in PATH"
    except (subprocess.TimeoutExpired, (ValueError, IndexError)) as exc:
        step.status = "failed"
        step.error = str(exc)[:200]
    step.duration_ms = round((time.time() - start) * 1000, 1)
    return step


def check_docker() -> InstallStep:
    step = InstallStep(
        name="docker",
        description="Checking Docker availability",
        status="in_progress",
    )
    start = time.time()
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version = result.stdout.strip()
        step.status = "completed"
        step.error = version
    except FileNotFoundError:
        step.status = "skipped"
        step.error = "Docker not found (optional)"
    except subprocess.TimeoutExpired:
        step.status = "skipped"
        step.error = "Docker check timed out"
    step.duration_ms = round((time.time() - start) * 1000, 1)
    return step


def check_postgresql() -> InstallStep:
    step = InstallStep(
        name="postgresql",
        description="Checking PostgreSQL availability",
        status="in_progress",
    )
    start = time.time()
    try:
        result = subprocess.run(
            ["pg_isready", "-h", os.getenv("POSTGRES_HOST", "localhost")],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            step.status = "completed"
            step.error = "PostgreSQL is accepting connections"
        else:
            step.status = "failed"
            step.error = result.stderr.strip() or "PostgreSQL not responding"
    except FileNotFoundError:
        step.status = "skipped"
        step.error = "pg_isready not found, ensure PostgreSQL is installed"
    except subprocess.TimeoutExpired:
        step.status = "failed"
        step.error = "PostgreSQL check timed out"
    step.duration_ms = round((time.time() - start) * 1000, 1)
    return step


def check_redis() -> InstallStep:
    step = InstallStep(
        name="redis",
        description="Checking Redis availability",
        status="in_progress",
    )
    start = time.time()
    try:
        result = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if "PONG" in result.stdout:
            step.status = "completed"
            step.error = "Redis is responding"
        else:
            step.status = "failed"
            step.error = result.stdout.strip() or "Redis not responding"
    except FileNotFoundError:
        step.status = "skipped"
        step.error = "redis-cli not found, ensure Redis is installed"
    except subprocess.TimeoutExpired:
        step.status = "failed"
        step.error = "Redis check timed out"
    step.duration_ms = round((time.time() - start) * 1000, 1)
    return step


def check_ollama() -> InstallStep:
    step = InstallStep(
        name="ollama",
        description="Checking Ollama AI provider",
        status="in_progress",
    )
    start = time.time()
    try:
        import urllib.request
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        req = urllib.request.Request(f"{ollama_host}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("models", [])
            step.status = "completed"
            step.error = f"Ollama running, {len(models)} models available"
    except Exception as exc:
        step.status = "failed"
        step.error = f"Ollama not reachable: {exc}"
    step.duration_ms = round((time.time() - start) * 1000, 1)
    return step


installer = InstallerEngine()
