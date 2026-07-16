"""Pydantic schemas for the Tool Virtualization Layer."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolStatus(str, Enum):
    """Tool operational status."""

    HEALTHY = "healthy"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    UNKNOWN = "unknown"


class ToolProvider(str, Enum):
    """Tool provider types."""

    MCP = "mcp"
    BUILTIN = "builtin"
    EXTERNAL = "external"


class PermissionLevel(str, Enum):
    """Permission levels for tool execution."""

    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class EventType(str, Enum):
    """Tool event types."""

    TOOL_REGISTERED = "tool_registered"
    TOOL_UNREGISTERED = "tool_unregistered"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    PERMISSION_DENIED = "permission_denied"
    CANCELLED = "cancelled"
    HEALTH_CHECK = "health_check"


class ToolCapability(BaseModel):
    """Tool capability definition."""

    name: str
    description: str
    operations: list[str]
    required_permissions: list[PermissionLevel]


class ToolHealth(BaseModel):
    """Tool health information."""

    status: ToolStatus
    latency_ms: float | None = None
    last_check: datetime | None = None
    error_message: str | None = None
    version: str | None = None


class ToolDefinition(BaseModel):
    """Complete tool definition."""

    id: str
    name: str
    description: str
    provider: ToolProvider
    version: str
    capabilities: list[ToolCapability]
    health: ToolHealth
    supported_operations: list[str]
    created_at: datetime
    updated_at: datetime


class ToolRequest(BaseModel):
    """Request to execute a tool."""

    request_id: str
    workflow_id: str | None = None
    task_id: str | None = None
    agent_id: str
    tool_id: str
    operation: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    permission_scope: PermissionLevel = PermissionLevel.READ
    timeout_seconds: int = Field(default=300, ge=1)
    priority: int = Field(default=5, ge=1, le=10)


class ToolResponse(BaseModel):
    """Response from tool execution."""

    request_id: str
    tool_id: str
    operation: str
    status: str
    execution_time_ms: float
    output: dict[str, Any] = Field(default_factory=dict)
    logs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolEvent(BaseModel):
    """Tool event."""

    id: str
    event_type: EventType
    tool_id: str
    request_id: str | None = None
    agent_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime


class PermissionRequest(BaseModel):
    """Permission validation request."""

    agent_id: str
    tool_id: str
    operation: str
    project_id: str | None = None
    repository_path: str | None = None
    required_level: PermissionLevel


class PermissionResult(BaseModel):
    """Permission validation result."""

    allowed: bool
    reason: str | None = None
    granted_level: PermissionLevel | None = None


class ToolType(str, Enum):
    """Types of tools."""

    FILE = "file"
    SEARCH = "search"
    GIT = "git"
    SHELL = "shell"
    WEB = "web"
    AI = "ai"
    DOCKER = "docker"
    DATABASE = "database"
    BROWSER = "browser"
    CUSTOM = "custom"


class ToolConfig(BaseModel):
    """Configuration for a tool instance."""

    tool_id: str
    name: str
    description: str
    tool_type: ToolType
    provider: ToolProvider = ToolProvider.BUILTIN
    version: str = "0.1.0"
    enabled: bool = True
    timeout_seconds: int = 300
    max_retries: int = 3
    permissions: list[PermissionLevel] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    """Result of a tool execution."""

    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    tool_id: str = ""
    execution_id: str = ""
    duration_ms: float = 0


class ToolStatusResponse(BaseModel):
    """Summary of all tool statuses."""

    total_tools: int
    healthy_tools: int
    offline_tools: int
    busy_tools: int
    error_tools: int
    tools_by_provider: dict[str, int]
