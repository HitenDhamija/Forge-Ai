# Agents Architecture

## Overview

The Agents module provides autonomous task execution capabilities for ForgeAI. It enables the creation, management, and coordination of AI agents that can perform complex tasks using available tools.

## Architecture

```
app/agents/
├── __init__.py
├── config.py              # AgentSettings (env-based configuration)
├── exceptions.py          # Agent-specific exception hierarchy
├── schemas.py             # Pydantic models for agents and tasks
├── agent_base.py          # Abstract base class for all agents
├── orchestrator.py        # Manages agent lifecycle and task execution
├── registry.py            # Agent type registry and factory
├── tools/                 # Tool system
│   ├── __init__.py
│   ├── base.py            # Abstract base class for tools
│   ├── registry.py        # Tool registry
│   ├── factory.py         # Tool factory
│   ├── file_tools.py      # File system tools
│   ├── search_tools.py    # Search tools
│   └── ai_tools.py        # AI/LLM tools
└── implementations/       # Specific agent types
    ├── __init__.py
    ├── planner.py         # Task planning agent
    ├── executor.py        # Task execution agent
    ├── reviewer.py        # Code review agent
    └── researcher.py      # Research agent
```

## Core Components

### AgentBase

Abstract base class that all agents must inherit from. Provides:

- Task execution lifecycle management
- Tool access via ToolRegistry
- Status tracking and metrics
- Iteration and timeout handling

### AgentOrchestrator

Manages agent instances and coordinates task execution:

- Agent registration and discovery
- Task submission and routing
- Concurrent execution management
- Task status tracking
- Metrics collection

### AgentRegistry

Factory for creating agent instances:

- Agent type registration
- Agent creation and management
- Type-safe agent instantiation

## Agent Types

### PlannerAgent

Analyzes complex tasks and creates execution plans:

- Task decomposition
- Dependency identification
- Risk assessment
- Step generation

### ExecutorAgent

Carries out specific actions and implements changes:

- File operations (read, write, edit)
- Search operations
- Code analysis
- Action execution

### ReviewerAgent

Analyzes code and provides feedback:

- Code quality review
- Security analysis
- Performance review
- Change review

### ResearcherAgent

Gathers information and knowledge:

- Codebase exploration
- Documentation research
- Topic analysis
- Information synthesis

## Tool System

### ToolBase

Abstract base class for all tools:

- Parameter validation
- Execution interface
- Definition generation

### ToolRegistry

Central registry for tool management:

- Tool registration and discovery
- Tool execution
- Type-based filtering

### Available Tools

| Tool | Type | Description |
|------|------|-------------|
| `read_file` | file | Read file contents |
| `write_file` | file | Write content to file |
| `edit_file` | file | Edit file by replacing content |
| `list_directory` | file | List directory contents |
| `grep_search` | search | Search file contents with regex |
| `find_files` | search | Find files by pattern |
| `llm_query` | ai | Query the local LLM |
| `analyze_code` | ai | Analyze code using LLM |

## Task Execution Flow

1. **Task Submission**: User creates a task via API
2. **Agent Selection**: Orchestrator finds best available agent
3. **Task Assignment**: Task is assigned to agent
4. **Execution**: Agent executes task using tools
5. **Progress Updates**: Status updates during execution
6. **Completion**: Results returned to user

## Configuration

The agents module is configured via environment variables:

```bash
# Agent Settings
AGENT_MAX_CONCURRENT_AGENTS=5
AGENT_AGENT_TIMEOUT_SECONDS=300
AGENT_MAX_TASK_RETRIES=3
AGENT_ENABLE_SHELL_EXECUTION=false
AGENT_ENABLE_FILE_MODIFICATION=true
AGENT_ALLOWED_FILE_EXTENSIONS=[".py",".ts",".tsx",".js",".jsx",".json",".yaml",".yml",".toml",".md",".txt",".html",".css"]
AGENT_BLOCKED_DIRECTORIES=[".git","node_modules","__pycache__",".venv","venv","env"]
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/agents/` | List all agents |
| GET | `/api/v1/agents/{id}` | Get agent details |
| POST | `/api/v1/agents/tasks` | Create a new task |
| GET | `/api/v1/agents/tasks/{id}` | Get task status |
| POST | `/api/v1/agents/tasks/{id}/cancel` | Cancel a task |
| GET | `/api/v1/agents/tasks/list` | List tasks with filters |
| GET | `/api/v1/agents/metrics/overview` | Get system metrics |

## Security Considerations

### File System Access

- Configurable allowed file extensions
- Blocked directories (e.g., `.git`, `node_modules`)
- Optional file modification disable
- Path traversal prevention

### Execution Limits

- Maximum concurrent agents
- Task timeout limits
- Iteration limits per task
- Retry limits

### Tool Permissions

- Tools can require specific permissions
- Agent types have predefined tool access
- Runtime permission validation

## Frontend Integration

### Components

- `AgentStatus`: Displays agent information and status
- `TaskList`: Shows recent tasks with filtering
- `TaskSubmission`: Form for creating new tasks

### Store

The `useAgentStore` provides:

- Agent list management
- Task CRUD operations
- Metrics tracking
- Loading and error states

### Service

The `agentService` handles:

- API communication
- Data transformation
- Error handling

## Future Enhancements

1. **Persistent Task Storage**: Store tasks in PostgreSQL
2. **Agent Communication**: Inter-agent messaging system
3. **Tool Marketplace**: Dynamic tool registration
4. **Agent Learning**: Improve from task outcomes
5. **Workflow Orchestration**: Multi-agent workflows
6. **External Tool Integration**: Shell, Git, Web tools
