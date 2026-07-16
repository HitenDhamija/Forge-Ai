"""System diagnostics and health checks."""

import platform
import shutil
import os
import time
import json
import socket
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone


class DiagnosticStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class DiagnosticCheck:
    name: str
    status: DiagnosticStatus
    message: str
    details: Optional[dict] = None
    fix_suggestion: Optional[str] = None


@dataclass
class DiagnosticReport:
    timestamp: str
    checks: list[DiagnosticCheck] = field(default_factory=list)
    overall_status: DiagnosticStatus = DiagnosticStatus.PASS
    recommendations: list[str] = field(default_factory=list)


class DiagnosticsEngine:
    def __init__(self):
        self.checks_ran: int = 0

    def run_all_checks(self) -> DiagnosticReport:
        report = DiagnosticReport(timestamp=datetime.now(timezone.utc).isoformat())

        check_methods = [
            self.check_database,
            self.check_cache,
            self.check_ai_provider,
            self.check_filesystem,
            self.check_environment,
            self.check_configuration,
            self.check_dependencies,
            self.check_disk_space,
            self.check_memory,
            self.check_network,
        ]

        for method in check_methods:
            try:
                check = method()
                report.checks.append(check)
                self.checks_ran += 1
            except Exception as exc:
                report.checks.append(DiagnosticCheck(
                    name=method.__name__,
                    status=DiagnosticStatus.FAIL,
                    message=f"Check failed with exception: {exc}",
                ))

        report.overall_status = self._compute_overall(report.checks)
        report.recommendations = self.get_recommendations(report)
        return report

    def _compute_overall(self, checks: list[DiagnosticCheck]) -> DiagnosticStatus:
        statuses = [c.status for c in checks]
        if DiagnosticStatus.FAIL in statuses:
            return DiagnosticStatus.FAIL
        if DiagnosticStatus.WARN in statuses:
            return DiagnosticStatus.WARN
        return DiagnosticStatus.PASS

    def check_database(self) -> DiagnosticCheck:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                dbname=os.getenv("POSTGRES_DB", "forgeai"),
                user=os.getenv("POSTGRES_USER", "forgeai"),
                password=os.getenv("POSTGRES_PASSWORD", ""),
                connect_timeout=5,
            )
            conn.close()
            return DiagnosticCheck(
                name="database",
                status=DiagnosticStatus.PASS,
                message="PostgreSQL connection successful",
            )
        except ImportError:
            return DiagnosticCheck(
                name="database",
                status=DiagnosticStatus.SKIP,
                message="psycopg2 not installed",
                fix_suggestion="pip install psycopg2-binary",
            )
        except Exception as exc:
            return DiagnosticCheck(
                name="database",
                status=DiagnosticStatus.FAIL,
                message=f"PostgreSQL connection failed: {exc}",
                fix_suggestion="Ensure PostgreSQL is running and credentials are correct",
            )

    def check_cache(self) -> DiagnosticCheck:
        try:
            import redis
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                socket_connect_timeout=5,
            )
            r.ping()
            return DiagnosticCheck(
                name="cache",
                status=DiagnosticStatus.PASS,
                message="Redis connection successful",
            )
        except ImportError:
            return DiagnosticCheck(
                name="cache",
                status=DiagnosticStatus.SKIP,
                message="redis-py not installed",
                fix_suggestion="pip install redis",
            )
        except Exception as exc:
            return DiagnosticCheck(
                name="cache",
                status=DiagnosticStatus.FAIL,
                message=f"Redis connection failed: {exc}",
                fix_suggestion="Ensure Redis is running on the configured host/port",
            )

    def check_ai_provider(self) -> DiagnosticCheck:
        try:
            import urllib.request
            ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            req = urllib.request.Request(f"{ollama_host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = [m.get("name", "unknown") for m in data.get("models", [])]
                return DiagnosticCheck(
                    name="ai_provider",
                    status=DiagnosticStatus.PASS,
                    message=f"Ollama reachable ({len(models)} models available)",
                    details={"models": models},
                )
        except Exception as exc:
            return DiagnosticCheck(
                name="ai_provider",
                status=DiagnosticStatus.FAIL,
                message=f"Ollama not reachable: {exc}",
                fix_suggestion="Start Ollama with `ollama serve` or check OLLAMA_HOST",
            )

    def check_filesystem(self) -> DiagnosticCheck:
        base = os.getenv("FORGEAI_DATA_DIR", "./data")
        issues = []
        dirs_to_check = [
            base,
            os.path.join(base, "repositories"),
            os.path.join(base, "knowledge"),
            os.path.join(base, "uploads"),
        ]
        for d in dirs_to_check:
            if not os.path.exists(d):
                try:
                    os.makedirs(d, exist_ok=True)
                except OSError as exc:
                    issues.append(f"Cannot create {d}: {exc}")
            if os.path.exists(d) and not os.access(d, os.W_OK):
                issues.append(f"No write permission: {d}")

        if issues:
            return DiagnosticCheck(
                name="filesystem",
                status=DiagnosticStatus.FAIL,
                message="Filesystem issues detected",
                details={"issues": issues},
                fix_suggestion="Ensure data directories exist and are writable",
            )
        return DiagnosticCheck(
            name="filesystem",
            status=DiagnosticStatus.PASS,
            message="All data directories accessible and writable",
        )

    def check_environment(self) -> DiagnosticCheck:
        required = [
            "POSTGRES_HOST",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "REDIS_HOST",
            "OLLAMA_HOST",
            "FORGEAI_DATA_DIR",
        ]
        missing = [v for v in required if not os.getenv(v)]
        optional_set = [
            "POSTGRES_PASSWORD",
            "OPENAI_API_KEY",
            "SECRET_KEY",
        ]
        missing_optional = [v for v in optional_set if not os.getenv(v)]

        if missing:
            return DiagnosticCheck(
                name="environment",
                status=DiagnosticStatus.FAIL,
                message=f"{len(missing)} required env vars missing",
                details={"missing_required": missing, "missing_optional": missing_optional},
                fix_suggestion=f"Set: {', '.join(missing)}",
            )
        if missing_optional:
            return DiagnosticCheck(
                name="environment",
                status=DiagnosticStatus.WARN,
                message=f"{len(missing_optional)} optional env vars not set",
                details={"missing_optional": missing_optional},
            )
        return DiagnosticCheck(
            name="environment",
            status=DiagnosticStatus.PASS,
            message="All environment variables configured",
        )

    def check_configuration(self) -> DiagnosticCheck:
        config_path = os.getenv("FORGEAI_CONFIG", "./config.json")
        if not os.path.exists(config_path):
            return DiagnosticCheck(
                name="configuration",
                status=DiagnosticStatus.WARN,
                message=f"Config file not found at {config_path}",
                fix_suggestion="Run `forge init` to generate default config",
            )
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            required_keys = ["database", "cache", "ai"]
            missing = [k for k in required_keys if k not in config]
            if missing:
                return DiagnosticCheck(
                    name="configuration",
                    status=DiagnosticStatus.WARN,
                    message=f"Config missing keys: {', '.join(missing)}",
                    fix_suggestion="Update config or regenerate with `forge init`",
                )
            return DiagnosticCheck(
                name="configuration",
                status=DiagnosticStatus.PASS,
                message="Configuration file valid",
            )
        except json.JSONDecodeError as exc:
            return DiagnosticCheck(
                name="configuration",
                status=DiagnosticStatus.FAIL,
                message=f"Invalid JSON in config: {exc}",
                fix_suggestion="Fix JSON syntax or regenerate config",
            )

    def check_dependencies(self) -> DiagnosticCheck:
        required = ["fastapi", "uvicorn", "pydantic", "sqlalchemy"]
        optional = ["psycopg2", "redis", "celery", "httpx"]
        missing_req = []
        missing_opt = []

        for pkg in required:
            try:
                __import__(pkg)
            except ImportError:
                missing_req.append(pkg)

        for pkg in optional:
            try:
                __import__(pkg)
            except ImportError:
                missing_opt.append(pkg)

        if missing_req:
            return DiagnosticCheck(
                name="dependencies",
                status=DiagnosticStatus.FAIL,
                message=f"{len(missing_req)} required packages missing",
                details={"missing_required": missing_req, "missing_optional": missing_opt},
                fix_suggestion=f"pip install {' '.join(missing_req)}",
            )
        if missing_opt:
            return DiagnosticCheck(
                name="dependencies",
                status=DiagnosticStatus.WARN,
                message=f"{len(missing_opt)} optional packages missing",
                details={"missing_optional": missing_opt},
                fix_suggestion=f"pip install {' '.join(missing_opt)}",
            )
        return DiagnosticCheck(
            name="dependencies",
            status=DiagnosticStatus.PASS,
            message="All dependencies installed",
        )

    def check_disk_space(self) -> DiagnosticCheck:
        try:
            usage = shutil.disk_usage(".")
            free_gb = usage.free / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            pct_free = (usage.free / usage.total) * 100
            details = {
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "percent_free": round(pct_free, 1),
            }
            if pct_free < 5:
                return DiagnosticCheck(
                    name="disk_space",
                    status=DiagnosticStatus.FAIL,
                    message=f"Critical low disk space: {round(free_gb, 2)} GB free ({round(pct_free, 1)}%)",
                    details=details,
                    fix_suggestion="Free disk space or change FORGEAI_DATA_DIR",
                )
            if pct_free < 15:
                return DiagnosticCheck(
                    name="disk_space",
                    status=DiagnosticStatus.WARN,
                    message=f"Low disk space: {round(free_gb, 2)} GB free ({round(pct_free, 1)}%)",
                    details=details,
                    fix_suggestion="Consider freeing disk space",
                )
            return DiagnosticCheck(
                name="disk_space",
                status=DiagnosticStatus.PASS,
                message=f"Disk space OK: {round(free_gb, 2)} GB free",
                details=details,
            )
        except Exception as exc:
            return DiagnosticCheck(
                name="disk_space",
                status=DiagnosticStatus.SKIP,
                message=f"Cannot check disk space: {exc}",
            )

    def check_memory(self) -> DiagnosticCheck:
        try:
            import psutil
            mem = psutil.virtual_memory()
            details = {
                "total_gb": round(mem.total / (1024 ** 3), 2),
                "available_gb": round(mem.available / (1024 ** 3), 2),
                "percent_used": mem.percent,
            }
            if mem.percent > 90:
                return DiagnosticCheck(
                    name="memory",
                    status=DiagnosticStatus.FAIL,
                    message=f"High memory usage: {mem.percent}%",
                    details=details,
                    fix_suggestion="Free memory or increase system RAM",
                )
            if mem.percent > 75:
                return DiagnosticCheck(
                    name="memory",
                    status=DiagnosticStatus.WARN,
                    message=f"Elevated memory usage: {mem.percent}%",
                    details=details,
                )
            return DiagnosticCheck(
                name="memory",
                status=DiagnosticStatus.PASS,
                message=f"Memory usage normal: {mem.percent}%",
                details=details,
            )
        except ImportError:
            return DiagnosticCheck(
                name="memory",
                status=DiagnosticStatus.SKIP,
                message="psutil not installed",
                fix_suggestion="pip install psutil",
            )

    def check_network(self) -> DiagnosticCheck:
        targets = [
            ("DNS", "8.8.8.8", 53),
            ("HTTP", "1.1.1.1", 80),
        ]
        results = []
        for name, host, port in targets:
            try:
                start = time.time()
                sock = socket.create_connection((host, port), timeout=5)
                sock.close()
                elapsed_ms = round((time.time() - start) * 1000, 1)
                results.append({"target": name, "host": host, "latency_ms": elapsed_ms, "ok": True})
            except Exception as exc:
                results.append({"target": name, "host": host, "error": str(exc), "ok": False})

        failures = [r for r in results if not r["ok"]]
        if failures:
            return DiagnosticCheck(
                name="network",
                status=DiagnosticStatus.FAIL,
                message=f"{len(failures)} network target(s) unreachable",
                details={"results": results},
                fix_suggestion="Check network connectivity and firewall settings",
            )
        return DiagnosticCheck(
            name="network",
            status=DiagnosticStatus.PASS,
            message="Network connectivity OK",
            details={"results": results},
        )

    def get_recommendations(self, report: DiagnosticReport) -> list[str]:
        recs = []
        for check in report.checks:
            if check.status in (DiagnosticStatus.FAIL, DiagnosticStatus.WARN) and check.fix_suggestion:
                recs.append(f"[{check.status.value.upper()}] {check.name}: {check.fix_suggestion}")
        return recs


def run_doctor() -> DiagnosticReport:
    engine = DiagnosticsEngine()
    report = engine.run_all_checks()
    return report


def print_report(report: DiagnosticReport) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("FORGE AI - DIAGNOSTIC REPORT")
    lines.append(f"Timestamp: {report.timestamp}")
    lines.append(f"Overall:   {report.overall_status.value.upper()}")
    lines.append(f"Checks:    {len(report.checks)}")
    lines.append("=" * 60)

    status_icons = {
        DiagnosticStatus.PASS: "[PASS]",
        DiagnosticStatus.WARN: "[WARN]",
        DiagnosticStatus.FAIL: "[FAIL]",
        DiagnosticStatus.SKIP: "[SKIP]",
    }

    for check in report.checks:
        icon = status_icons.get(check.status, "[????]")
        lines.append(f"  {icon} {check.name}: {check.message}")
        if check.fix_suggestion:
            lines.append(f"         Fix: {check.fix_suggestion}")

    if report.recommendations:
        lines.append("")
        lines.append("RECOMMENDATIONS:")
        for rec in report.recommendations:
            lines.append(f"  - {rec}")

    lines.append("=" * 60)
    return "\n".join(lines)


diagnostics = DiagnosticsEngine()
