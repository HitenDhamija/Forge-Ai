from __future__ import annotations

import json
import logging
import sys
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


class LogFormat(str, Enum):
    JSON = "json"
    TEXT = "text"


class LogOutput(str, Enum):
    CONSOLE = "console"
    FILE = "file"
    BOTH = "both"


@dataclass
class LogConfig:
    level: str = "INFO"
    format: LogFormat = LogFormat.JSON
    output: LogOutput = LogOutput.CONSOLE
    correlation_id_header: str = "X-Correlation-ID"
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5
    log_dir: str = "logs"
    app_name: str = "forge-ai"


log_config = LogConfig()


class CorrelationContext:
    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        _correlation_id.set(correlation_id)

    @staticmethod
    def get_correlation_id() -> Optional[str]:
        return _correlation_id.get()

    @staticmethod
    def clear() -> None:
        _correlation_id.set(None)


class StructuredFormatter(logging.Formatter):
    def __init__(self, config: LogConfig | None = None):
        super().__init__()
        self.config = config or log_config

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": CorrelationContext.get_correlation_id(),
            "module": record.module,
            "logger": record.name,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        extra_fields: dict[str, Any] = {}
        for key in list(record.__dict__.keys()):
            if key not in logging.LogRecord("", 0, "", 0, "", (), None).__dict__:
                extra_fields[key] = record.__dict__[key]
        if extra_fields:
            log_entry["extra"] = extra_fields

        if self.config.format == LogFormat.JSON:
            return json.dumps(log_entry, default=str, ensure_ascii=False)

        parts = [
            f"[{log_entry['timestamp']}]",
            f"[{log_entry['level']:8s}]",
            f"[{log_entry['module']}]",
        ]
        if log_entry["correlation_id"]:
            parts.append(f"[corr={log_entry['correlation_id'][:8]}]")
        parts.append(log_entry["message"])
        return " ".join(parts)


class _CorrelatedLogger(logging.Logger):
    """Logger that automatically attaches correlation_id to every record."""

    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: str,
        args: tuple[Any, ...],
        exc_info: Any,
        func: str | None = None,
        extra: dict[str, Any] | None = None,
        sinfo: str | None = None,
    ) -> logging.LogRecord:
        record = super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        cid = CorrelationContext.get_correlation_id()
        if cid:
            record.correlation_id = cid
        return record


logging.setLoggerClass(_CorrelatedLogger)


class RequestLogger:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("forge.request")

    def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str | None = None,
    ) -> None:
        extra = {
            "event_type": "http_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
        }
        if user_id:
            extra["user_id"] = user_id

        if status_code >= 500:
            self.logger.error(f"{method} {path} -> {status_code} ({duration_ms:.1f}ms)", extra=extra)
        elif status_code >= 400:
            self.logger.warning(f"{method} {path} -> {status_code} ({duration_ms:.1f}ms)", extra=extra)
        else:
            self.logger.info(f"{method} {path} -> {status_code} ({duration_ms:.1f}ms)", extra=extra)

    def log_error(self, error: Exception, context: dict[str, Any] | None = None) -> None:
        extra: dict[str, Any] = {
            "event_type": "request_error",
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        if context:
            extra["context"] = context
        self.logger.error(f"Request error: {error}", extra=extra, exc_info=True)

    def log_security_event(self, event_type: str, details: dict[str, Any]) -> None:
        extra = {
            "event_type": f"security_{event_type}",
            **details,
        }
        self.logger.warning(f"Security event: {event_type}", extra=extra)


class WorkflowLogger:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("forge.workflow")

    def log_workflow_start(self, workflow_id: str, user_id: str) -> None:
        self.logger.info(
            f"Workflow started: {workflow_id}",
            extra={"event_type": "workflow_start", "workflow_id": workflow_id, "user_id": user_id},
        )

    def log_workflow_step(self, workflow_id: str, step: str, status: str) -> None:
        level = logging.INFO if status == "completed" else logging.WARNING
        self.logger.log(
            level,
            f"Workflow {workflow_id} step '{step}' -> {status}",
            extra={"event_type": "workflow_step", "workflow_id": workflow_id, "step": step, "status": status},
        )

    def log_workflow_complete(self, workflow_id: str, duration_ms: float) -> None:
        self.logger.info(
            f"Workflow completed: {workflow_id} in {duration_ms:.1f}ms",
            extra={
                "event_type": "workflow_complete",
                "workflow_id": workflow_id,
                "duration_ms": round(duration_ms, 2),
            },
        )

    def log_workflow_error(self, workflow_id: str, error: Exception) -> None:
        self.logger.error(
            f"Workflow failed: {workflow_id} - {error}",
            extra={
                "event_type": "workflow_error",
                "workflow_id": workflow_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
            exc_info=True,
        )


class AgentLogger:
    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("forge.agent")

    def log_agent_action(self, agent_id: str, action: str, details: dict[str, Any] | None = None) -> None:
        extra: dict[str, Any] = {
            "event_type": "agent_action",
            "agent_id": agent_id,
            "action": action,
        }
        if details:
            extra["details"] = details
        self.logger.info(f"Agent {agent_id} performed: {action}", extra=extra)

    def log_agent_error(self, agent_id: str, error: Exception) -> None:
        self.logger.error(
            f"Agent {agent_id} error: {error}",
            extra={
                "event_type": "agent_error",
                "agent_id": agent_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
            exc_info=True,
        )

    def log_agent_performance(self, agent_id: str, metrics: dict[str, Any]) -> None:
        self.logger.info(
            f"Agent {agent_id} performance metrics",
            extra={"event_type": "agent_performance", "agent_id": agent_id, "metrics": metrics},
        )


def setup_logging(config: LogConfig | None = None) -> None:
    global log_config
    if config:
        log_config = config

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, log_config.level.upper(), logging.INFO))

    formatter = StructuredFormatter(log_config)

    if log_config.output in (LogOutput.CONSOLE, LogOutput.BOTH):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    if log_config.output in (LogOutput.FILE, LogOutput.BOTH):
        log_dir = Path(log_config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{log_config.app_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_config.max_file_size,
            backupCount=log_config.backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    _suppress_noisy_loggers()


def _suppress_noisy_loggers() -> None:
    for name in ("uvicorn.access", "uvicorn.error", "httpcore", "httpx", "urllib3"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def get_request_logger() -> RequestLogger:
    return request_logger


def get_workflow_logger() -> WorkflowLogger:
    return workflow_logger


def get_agent_logger() -> AgentLogger:
    return agent_logger


request_logger = RequestLogger()
workflow_logger = WorkflowLogger()
agent_logger = AgentLogger()
