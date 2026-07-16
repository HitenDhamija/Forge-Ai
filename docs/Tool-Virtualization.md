# Tool Virtualization Layer

## Overview

The Tool Virtualization Layer provides a unified abstraction for all external tools and services. It enables agents to interact with the filesystem, databases, Docker, and other services through a standardized interface, with built-in permission control and event tracking.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Endpoints                               │
│  POST /tools/execute  │  GET /tools  │  GET /tools/{id}/health      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Tool Runtime                                │
│  Execute │ Cancel │ Track │ Events │ Permissions                    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │   Registry   │ │  Permission  │ │    Events    │
            │              │ │    Engine    │ │   Emitter    │
            │  register()  │ │   check()    │ │    emit()    │
            │  get_tool()  │ │              │ │              │
            └──────────────┘ └──────────────┘ └──────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │  Filesystem  │ │    Git       │ │   Terminal   │
            │    Tool      │ │    Tool      │ │    Tool      │
            └──────────────┘ └──────────────┘ └──────────────┘
                    │              │              │
            ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
            │    Docker    │ │   Database   │ │   Browser    │
            │    Tool      │ │    Tool      │ │    Tool      │
            └──────────────┘ └──────────────┘ └──────────────┘
```

## Components

### Base Tool Interface

All tools implement the `BaseTool` abstract class:

```python
class BaseTool(ABC):
    async def initialize(self) -> None
    async def health_check(self) -> ToolHealth
    async def validate(self, operation, parameters) -> tuple[bool, str | None]
    async def execute(self, operation, parameters, request_id) -> dict[str, Any]
    async def cancel(self, request_id) -> None
    async def cleanup(self) -> None
```

### Tool Registry

Manages tool registration and discovery:

```python
registry = ToolRegistry()

# Register tools
await registry.register(FilesystemTool())
await registry.register(GitTool())

# Get tools
tool = registry.get_tool("filesystem")
tools = registry.list_tools(tool_type=ToolType.MCP)
```

### Permission Engine

Validates agent permissions for tool operations:

```python
engine = PermissionEngine()

# Check permissions
permitted, reason = await engine.check_tool_permission(
    agent_id="agent-123",
    tool_id="filesystem",
    operation="write",
    parameters={"path": "./important.py"}
)
```

### Tool Runtime

Orchestrates execution with permissions and events:

```python
runtime = ToolRuntime(
    registry=registry,
    permission_engine=engine,
    event_emitter=emitter
)

# Execute tool
result = await runtime.execute(
    agent_id="agent-123",
    tool_id="filesystem",
    operation="read",
    parameters={"path": "./README.md"}
)
```

## Available Tools

### Filesystem Tool

File operations:

| Operation  | Parameters                           | Description          |
|------------|--------------------------------------|----------------------|
| `read`     | `path`                               | Read file contents   |
| `write`    | `path`, `content`                    | Write to file        |
| `list`     | `path`                               | List directory       |
| `search`   | `pattern`, `directory` (optional)    | Search files         |
| `move`     | `source`, `destination`              | Move/rename file     |
| `delete`   | `path`                               | Delete file/directory|

### Git Tool

Version control operations:

| Operation  | Parameters                    | Description            |
|------------|-------------------------------|------------------------|
| `status`   | -                             | Get repository status  |
| `branch`   | `name` (optional)             | List/create branch     |
| `commit`   | `message`                     | Commit changes         |
| `diff`     | `target` (optional)           | Show differences       |
| `log`      | `count` (optional)            | Show commit history    |
| `checkout` | `target`                      | Checkout branch/commit |

### Terminal Tool

Shell command execution:

| Operation  | Parameters                    | Description            |
|------------|-------------------------------|------------------------|
| `execute`  | `command`, `timeout` (opt)    | Run command            |
| `cancel`   | `process_id`                  | Cancel running command |
| `stream`   | -                             | Stream output          |

### Docker Tool

Container management:

| Operation  | Parameters                    | Description            |
|------------|-------------------------------|------------------------|
| `list`     | `target` (containers/images)  | List containers/images |
| `run`      | `image`, `name` (opt)         | Run new container      |
| `stop`     | `container_id`                | Stop container         |
| `exec`     | `container_id`, `command`     | Exec in container      |
| `logs`     | `container_id`, `tail` (opt)  | Get container logs     |

### Database Tool

SQL operations:

| Operation  | Parameters                    | Description            |
|------------|-------------------------------|------------------------|
| `query`    | `sql`, `limit` (opt)          | Execute query          |
| `list`     | -                             | List tables            |
| `describe` | `table_name`                  | Describe table schema  |
| `ddl`      | `sql`                         | Execute DDL            |

### Browser Tool

Web operations:

| Operation  | Parameters                    | Description            |
|------------|-------------------------------|------------------------|
| `fetch`    | `url`                         | Fetch URL content      |
| `search`   | `query`                       | Search the web         |
| `content`  | `url`                         | Get page text content  |

## API Endpoints

### List Tools

```http
GET /api/v1/tools
```

Response:
```json
{
  "tools": [
    {
      "tool_id": "filesystem",
      "name": "Filesystem",
      "description": "File system operations",
      "type": "mcp",
      "status": "healthy",
      "supported_operations": ["read", "write", "list", "search"]
    }
  ]
}
```

### Execute Tool

```http
POST /api/v1/tools/execute
Content-Type: application/json

{
  "tool_id": "filesystem",
  "operation": "read",
  "parameters": {
    "path": "./README.md"
  }
}
```

Response:
```json
{
  "success": true,
  "data": {
    "content": "# ForgeAI\n...",
    "path": "/app/README.md"
  },
  "tool_id": "filesystem",
  "execution_id": "exec-abc123",
  "duration_ms": 15.2
}
```

### Check Tool Health

```http
GET /api/v1/tools/{tool_id}/health
```

### Cancel Execution

```http
POST /api/v1/tools/{tool_id}/cancel?execution_id=exec-abc123
```

## Event Types

| Event                   | Description                     |
|-------------------------|---------------------------------|
| `tool.execute.success`  | Tool execution succeeded        |
| `tool.execute.error`    | Tool execution failed           |
| `tool.permission.denied`| Permission check failed         |
| `tool.cancel`           | Execution was cancelled         |
| `tool.error`            | Tool-level error occurred       |

## Configuration

Tools are initialized in `app/main.py` during application startup:

```python
# Initialize Tool Virtualization Layer
tool_registry = ToolRegistry()
permission_engine = PermissionEngine()
tool_event_emitter = ToolEventEmitter()
tool_runtime = ToolRuntime(
    registry=tool_registry,
    permission_engine=permission_engine,
    event_emitter=tool_event_emitter,
)

# Register MCP tools
await tool_registry.register(FilesystemTool())
await tool_registry.register(GitTool())
await tool_registry.register(TerminalTool())
await tool_registry.register(DockerTool())
await tool_registry.register(DatabaseTool())
await tool_registry.register(BrowserTool())
```

## Frontend

The Tool Center dashboard provides:

- **Tools Tab**: View all registered tools with status indicators
- **Execute Tab**: Execute tool operations with parameter input
- **History Tab**: View recent execution history with success/failure indicators

## Best Practices

1. **Always validate inputs** - The tool validates parameters before execution
2. **Handle errors gracefully** - Check `result.success` and `result.error`
3. **Use execution IDs** - Track and cancel long-running operations
4. **Monitor health** - Regularly check tool health for production systems
5. **Respect permissions** - The permission engine enforces access control
