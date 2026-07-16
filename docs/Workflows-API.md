# Workflows API

## Overview

The Workflows API provides endpoints for managing workflow execution and task orchestration.

## Base URL

```
/api/v1/workflows
```

## Authentication

All endpoints require authentication via Bearer token:

```
Authorization: Bearer <token>
```

## Endpoints

### Create Workflow

```
POST /api/v1/workflows
```

Creates a new workflow with tasks.

**Request Body:**

```json
{
  "title": "Implement Authentication System",
  "description": "Create a complete authentication system with JWT tokens",
  "project_id": "project-uuid",
  "tasks": [
    {
      "title": "Create User Model",
      "description": "Define the user database model",
      "priority": "high",
      "dependencies": [],
      "estimated_duration": 300
    },
    {
      "title": "Implement JWT Service",
      "description": "Create JWT token generation and validation",
      "priority": "high",
      "dependencies": ["task_0"],
      "estimated_duration": 600
    },
    {
      "title": "Create Auth Middleware",
      "description": "Implement authentication middleware",
      "priority": "medium",
      "dependencies": ["task_1"],
      "estimated_duration": 300
    }
  ],
  "requires_approval": true,
  "risk_level": "medium",
  "metadata": {
    "estimated_total_time": 1200
  }
}
```

**Response:**

```json
{
  "data": {
    "id": "workflow-uuid",
    "title": "Implement Authentication System",
    "status": "waiting_approval",
    "tasks": [...],
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### List Workflows

```
GET /api/v1/workflows
```

Returns a list of workflows with optional filters.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by status |
| `project_id` | string | Filter by project ID |

**Response:**

```json
{
  "data": [
    {
      "id": "workflow-uuid",
      "title": "Implement Authentication System",
      "status": "running",
      "tasks": [...],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Get Workflow

```
GET /api/v1/workflows/{workflow_id}
```

Returns details for a specific workflow.

**Response:**

```json
{
  "data": {
    "id": "workflow-uuid",
    "title": "Implement Authentication System",
    "description": "Create a complete authentication system",
    "status": "running",
    "current_step": 1,
    "tasks": [
      {
        "id": "task-uuid",
        "title": "Create User Model",
        "status": "completed",
        "priority": "high"
      }
    ],
    "risk_level": "medium",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Approve Workflow

```
POST /api/v1/workflows/{workflow_id}/approve
```

Approves a workflow for execution.

**Response:**

```json
{
  "data": {
    "id": "workflow-uuid",
    "status": "ready",
    "approval_status": "approved"
  }
}
```

### Start Workflow

```
POST /api/v1/workflows/{workflow_id}/start
```

Starts workflow execution.

**Response:**

```json
{
  "data": {
    "id": "workflow-uuid",
    "status": "running",
    "started_at": "2024-01-01T00:00:00Z"
  }
}
```

### Pause Workflow

```
POST /api/v1/workflows/{workflow_id}/pause
```

Pauses workflow execution.

**Response:**

```json
{
  "data": {
    "id": "workflow-uuid",
    "status": "paused"
  }
}
```

### Resume Workflow

```
POST /api/v1/workflows/{workflow_id}/resume
```

Resumes paused workflow execution.

**Response:**

```json
{
  "data": {
    "id": "workflow-uuid",
    "status": "running"
  }
}
```

### Cancel Workflow

```
POST /api/v1/workflows/{workflow_id}/cancel
```

Cancels workflow execution.

**Response:**

```json
{
  "data": {
    "id": "workflow-uuid",
    "status": "cancelled",
    "completed_at": "2024-01-01T00:00:00Z"
  }
}
```

### Get Execution Summary

```
GET /api/v1/workflows/{workflow_id}/summary
```

Returns execution summary for a workflow.

**Response:**

```json
{
  "data": {
    "workflow_id": "workflow-uuid",
    "total_tasks": 5,
    "completed_tasks": 3,
    "failed_tasks": 1,
    "skipped_tasks": 0,
    "total_duration": 1200,
    "success_rate": 75.0,
    "average_task_duration": 300,
    "events": [...]
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "detail": {
    "error_code": "INVALID_TRANSITION",
    "message": "Invalid workflow transition: running -> created"
  }
}
```

### 404 Not Found

```json
{
  "detail": {
    "error_code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow not found: workflow-uuid"
  }
}
```

## Workflow Statuses

| Status | Description |
|--------|-------------|
| `created` | Workflow is created |
| `waiting_approval` | Waiting for approval |
| `ready` | Approved and ready to run |
| `running` | Currently executing |
| `paused` | Execution paused |
| `completed` | Execution completed |
| `failed` | Execution failed |
| `cancelled` | Workflow was cancelled |

## Task Statuses

| Status | Description |
|--------|-------------|
| `pending` | Task is pending |
| `ready` | Task is ready to execute |
| `running` | Task is executing |
| `completed` | Task completed |
| `failed` | Task failed |
| `waiting` | Task is waiting |
| `retrying` | Task is being retried |
| `skipped` | Task was skipped |

## Risk Levels

| Level | Description |
|-------|-------------|
| `low` | Low risk, minimal impact |
| `medium` | Medium risk, standard procedures |
| `high` | High risk, requires careful review |
| `critical` | Critical risk, requires approval |
