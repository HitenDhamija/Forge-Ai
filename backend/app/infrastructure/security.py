from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from functools import wraps
from collections import defaultdict

from fastapi import Request, HTTPException


@dataclass
class SecurityConfig:
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_methods: list[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH"])
    cors_headers: list[str] = field(default_factory=lambda: ["*"])
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    session_timeout: int = 3600  # 1 hour


class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._total_requests: int = 0
        self._blocked_requests: int = 0

    async def check(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        allowed = len(self._requests[key]) < self.max_requests
        if not allowed:
            self._blocked_requests += 1
        return allowed

    async def increment(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > window_start]
        self._requests[key].append(now)
        self._total_requests += 1
        return len(self._requests[key])

    async def reset(self, key: str) -> None:
        self._requests.pop(key, None)

    def get_stats(self) -> dict:
        active_keys = len(self._requests)
        return {
            "total_requests": self._total_requests,
            "blocked_requests": self._blocked_requests,
            "active_keys": active_keys,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
        }


class InputSanitizer:
    _INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(a|an|the)", re.IGNORECASE),
        re.compile(r"system\s*:\s*", re.IGNORECASE),
        re.compile(r"<\|im_start\|>", re.IGNORECASE),
        re.compile(r"<\|im_end\|>", re.IGNORECASE),
        re.compile(r"jailbreak", re.IGNORECASE),
        re.compile(r"bypass\s+(all\s+)?safety", re.IGNORECASE),
        re.compile(r"override\s+(your|the)\s+(rules?|instructions?|policy)", re.IGNORECASE),
    ]

    _HTML_ESCAPE_MAP: dict[str, str] = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
    }

    def sanitize_input(self, input_str: str) -> str:
        result = input_str.strip()
        result = result.replace("\x00", "")
        result = re.sub(r"[\r\n]{3,}", "\n\n", result)
        if len(result) > 10000:
            result = result[:10000]
        return result

    def validate_string(self, input_str: str, max_length: int = 1000) -> bool:
        if not isinstance(input_str, str):
            return False
        if len(input_str) > max_length:
            return False
        if "\x00" in input_str:
            return False
        return True

    def escape_html(self, input_str: str) -> str:
        for char, escaped in self._HTML_ESCAPE_MAP.items():
            input_str = input_str.replace(char, escaped)
        return input_str

    def detect_injection(self, input_str: str) -> bool:
        for pattern in self._INJECTION_PATTERNS:
            if pattern.search(input_str):
                return True
        return False


class SecurityHeaders:
    _DEFAULT_HEADERS: dict[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": "default-src 'self'",
        "Cache-Control": "no-store, no-cache, must-revalidate",
    }

    def get_headers(self) -> dict[str, str]:
        return dict(self._DEFAULT_HEADERS)

    async def validate_request(self, request: Request) -> tuple[bool, str]:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:
            return False, "Request too large"

        content_type = request.headers.get("content-type", "")
        dangerous_types = ["text/html", "application/x-httpd-php", "application/x-php"]
        for dt in dangerous_types:
            if dt in content_type:
                return False, "Dangerous content type"

        host = request.headers.get("host", "")
        if not host:
            return False, "Missing host header"

        return True, "OK"


class CORSConfig:
    def __init__(
        self,
        origins: list[str] | None = None,
        methods: list[str] | None = None,
        headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 600,
    ):
        self.origins = origins or ["*"]
        self.methods = methods or ["GET", "POST", "PUT", "DELETE", "PATCH"]
        self.headers = headers or ["*"]
        self.allow_credentials = allow_credentials
        self.max_age = max_age

    def get_config(self) -> dict:
        return {
            "allow_origins": self.origins,
            "allow_methods": self.methods,
            "allow_headers": self.headers,
            "allow_credentials": self.allow_credentials,
            "max_age": self.max_age,
        }

    def validate_origin(self, origin: str) -> bool:
        if "*" in self.origins:
            return True
        return origin in self.origins


class SessionManager:
    def __init__(self, timeout: int = 3600):
        self.timeout = timeout
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(seconds=self.timeout),
            "is_active": True,
        }
        return session_id

    def validate_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        if not session["is_active"]:
            return False
        if datetime.utcnow() > session["expires_at"]:
            session["is_active"] = False
            return False
        return True

    def invalidate_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id]["is_active"] = False

    def cleanup_expired(self) -> int:
        now = datetime.utcnow()
        expired = [
            sid
            for sid, session in self._sessions.items()
            if now > session["expires_at"] or not session["is_active"]
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


def require_permission(permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            if not request:
                raise HTTPException(status_code=500, detail="No request context")
            user_id = getattr(request.state, "user_id", None)
            org_id = getattr(request.state, "organization_id", None)
            if not user_id or not org_id:
                raise HTTPException(status_code=401, detail="Unauthorized")
            from app.infrastructure.authorization import auth_service

            if not auth_service.check_permission(user_id, org_id, permission):
                raise HTTPException(status_code=403, detail="Forbidden")
            return await func(*args, **kwargs)
        return wrapper
    return decorator


security_config = SecurityConfig()
rate_limiter = RateLimiter(security_config.rate_limit_requests, security_config.rate_limit_window)
input_sanitizer = InputSanitizer()
session_manager = SessionManager(security_config.session_timeout)
