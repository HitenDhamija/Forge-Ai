# Agents API

## Overview

The Agents API provides endpoints for managing agents and executing tasks autonomously.

## Base URL

```
/api/v1/agents
```

## Authentication

All endpoints require authentication via Bearer token:

```
Authorization: Bearer <token>
```

## Endpoints

### List Agents

```
GET /api/v1/agents/
```

Returns a list of all available agents.

**Response:**

```json
{
  "data": [
    {
      "id": "agent-uuid",
      "name": "Planner Agent",
      "agent_type": "planner",
      "description": "Analyzes complex tasks and creates detailed execution plans",
      "status": "idle",
      "available_tools": ["read_file", "grep_search", "llm_query"],
      "config": {
        "max_iterations": 10,
        "timeout_seconds": 300,
        "temperature": 0.7,
        "tools": []
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Get Agent

```
GET /api/v1/agents/{agent_id}
```

Returns details for a specific agent.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | string | Agent UUID |

**Response:**

```json
{
  "data": {
    "id": "agent-uuid",
    "name": "Planner Agent",
    "agent_type": "planner",
    "description": "Analyzes complex tasks and creates detailed execution plans",
    "status": "idle",
    "available_tools": ["read_file", "grep_search", "llm_query"],
    "config": {
      "max_iterations": 10,
      "timeout_seconds": 300,
      "temperature": 0.7,
      "tools": []
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### Create Task

```
POST /api/v1/agents/tasks
```

Creates a new task for execution.

**Request Body:**

```json
{
  "title": "Refactor authentication module",
  "description": "Refactor the authentication module to use JWT tokens with refresh token rotation",
  "agent_type": "executor",
  "priority": "high",
  "context": {
    "codebase_path": "/path/to/codebase",
    "specific_files": ["auth.py", "auth_service.py"]
  },
  "tools_allowed": ["read_file", "write_file", "edit_file"],
  "max_iterations": 15
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `title` | string | Yes | Task title (1-200 characters) |
| `description` | string | Yes | Task description (1-5000 characters) |
| `agent_type` | string | No | Agent type: `planner`, `executor`, `reviewer`, `researcher` (default: `planner`) |
| `priority` | string | No | Priority: `low`, `medium`, `high`, `critical` (default: `medium`) |
| `context` | object | No | Additional context for the task |
| `tools_allowed` | array | No | List of allowed tools |
| `max_iterations` | integer | No | Maximum execution iterations (1-100, default: 10) |

**Response:**

```json
{
  "data": {
    "id": "task-uuid",
    "title": "Refactor authentication module",
    "description": "Refactor the authentication module to use JWT tokens with refresh token rotation",
    "status": "queued",
    "priority": "high",
    "agent_type": "executor",
    "agent_id": "agent-uuid",
    "steps": [],
    "context": {
      "codebase_path": "/path/to/codebase",
      "specific_files": ["auth.py", "auth_service.py"]
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### Get Task

```
GET /api/v1/agents/tasks/{task_id}
```

Returns status and details for a specific task.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | Task UUID |

**Response:**

```json
{
  "data": {
    "id": "task-uuid",
    "title": "Refactor authentication module",
    "description": "Refactor the authentication module to use JWT tokens with refresh token rotation",
    "status": "running",
    "priority": "high",
    "agent_type": "executor",
    "agent_id": "agent-uuid",
    "steps": [
      {
        "id": "step-1",
        "step_number": 1,
        "description": "Read current auth module",
        "tool_to_use": "read_file",
        "status": "completed",
        "result": "...",
        "started_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:00:05Z"
      }
    ],
    "context": {},
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:10Z",
    "started_at": "2024-01-01T00:00:00Z"
  }
}
```

### Cancel Task

```
POST /api/v1/agents/tasks/{task_id}/cancel
```

Cancels a running or queued task.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | string | Task UUID |

**Response:**

```json
{
  "data": {
    "id": "task-uuid",
    "status": "cancelled",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### List Tasks

```
GET /api/v1/agents/tasks/list
```

Returns a list of tasks with optional filters.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status: `pending`, `queued`, `running`, `completed`, `failed`, `cancelled` |
| `agent_type` | string | Filter by agent type: `planner`, `executor`, `reviewer`, `researcher` |

**Response:**

```json
{
  "data": [
    {
      "id": "task-uuid",
      "title": "Refactor authentication module",
      "status": "completed",
      "priority": "high",
      "agent_type": "executor",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Get Metrics

```
GET /api/v1/agents/metrics/overview
```

Returns system metrics for agents and tasks.

**Response:**

```json
{
  "data": {
    "total_agents": 4,
    "idle_agents": 3,
    "running_agents": 1,
    "total_tasks": 10,
    "completed_tasks": 7,
    "failed_tasks": 1,
    "running_tasks": 1,
    "queued_tasks": 1
  }
}
```

## Error Responses

### 404 Not Found

```json
{
  "detail": {
    "error_code": "AGENT_NOT_FOUND",
    "message": "Agent not found: agent-uuid"
  }
}
```

### 408 Request Timeout

```json
{
  "detail": {
    "error_code": "AGENT_TIMEOUT",
    "message": "Agent agent-uuid timed out after 300s"
  }
}
```

### 409 Conflict

```json
{
  "detail": {
    "error_code": "TASK_CANCELLED",
    "message": "Task has been cancelled: task-uuid"
  }
}
```

## Agent Types

| Type | Description |
|------|-------------|
| `planner` | Analyzes complex tasks and creates execution plans |
| `executor` | Carries out specific actions and implements changes |
| `reviewer` | Analyzes code and provides feedback |
| `researcher` | Gathers information and knowledge |

## Task Statuses

| Status | Description |
|--------|-------------|
| `pending` | Task is created but not yet queued |
| `queued` | Task is queued for execution |
| `running` | Task is currently being executed |
| `completed` | Task finished successfully |
| `failed` | Task failed during execution |
| `cancelled` | Task was cancelled by user |

## Priority Levels

| Priority | Description |
|----------|-------------|
| `low` | Low priority, execute when possible |
| `medium` | Normal priority (default) |
| `high` | High priority, execute before medium/low |
| `critical` | Critical priority, execute immediately |
