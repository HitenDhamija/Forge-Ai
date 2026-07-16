# Workflows Architecture

## Overview

The Workflows module provides task orchestration and execution management for ForgeAI. It serves as the "operating system kernel" that coordinates all future AI operations.

## Architecture

```
app/workflows/
├── __init__.py
├── config.py              # WorkflowSettings (env-based configuration)
├── schemas.py             # Pydantic models for workflows and tasks
├── models.py              # SQLAlchemy models
├── state_machine.py       # Workflow and task state transitions
├── repository.py          # Data access layer
├── task_queue.py          # Priority-based task queue
├── scheduler.py           # Task scheduling and dependency resolution
├── validator.py           # Workflow validation
├── events.py              # Event system for execution tracking
├── workflow_service.py    # Main service orchestrator
└── execution_summary.py   # Execution summary generation
```

## Core Components

### WorkflowService

Main entry point for all workflow operations:

- Create and manage workflows
- Approve, start, pause, resume, cancel workflows
- Coordinate between repository, scheduler, and events

### StateMachine

Enforces valid state transitions:

- Prevents invalid state changes
- Maintains workflow integrity
- Supports future rollback capabilities

### TaskScheduler

Manages task execution order:

- Detects circular dependencies
- Estimates execution order via topological sort
- Finds ready and blocked tasks

### WorkflowValidator

Validates workflow definitions:

- Checks task dependencies
- Detects circular dependencies
- Validates required fields

### TaskQueue

Priority-based task management:

- Manages task queuing and prioritization
- Tracks task dependencies
- Supports concurrent execution

### EventSystem

Tracks workflow execution:

- Records all state changes
- Supports event listeners
- Enables audit logging

## Workflow States

```
CREATED ──────────────► WAITING_APPROVAL ──────► READY
   │                        │                       │
   │                        │                       ▼
   │                        │                    RUNNING
   │                        │                       │
   │                        │          ┌────────────┼────────────┐
   │                        │          ▼            ▼            ▼
   │                        │       PAUSED      COMPLETED     FAILED
   │                        │          │            │            │
   │                        │          ▼            │            │
   │                        └──────► CANCELLED ◄────┘            │
   │                                                             │
   └─────────────────────────────────────────────────────────────┘
```

### Valid Transitions

| Current State | Valid Target States |
|---------------|---------------------|
| CREATED | WAITING_APPROVAL, READY, CANCELLED |
| WAITING_APPROVAL | READY, CANCELLED |
| READY | RUNNING, CANCELLED |
| RUNNING | PAUSED, COMPLETED, FAILED, CANCELLED |
| PAUSED | RUNNING, CANCELLED |
| FAILED | CREATED, CANCELLED |
| CANCELLED | (none) |
| COMPLETED | (none) |

## Task States

```
PENDING ──────────────► READY ──────────────► RUNNING
   │                      │                      │
   │                      │          ┌───────────┼───────────┐
   │                      │          ▼           ▼           ▼
   │                      │       COMPLETED   FAILED      WAITING
   │                      │          │           │           │
   │                      │          │           ▼           │
   │                      │          │       RETRYING ◄──────┘
   │                      │          │           │
   │                      │          │           ▼
   │                      │          │        RUNNING
   │                      │          │
   ▼                      ▼          ▼
SKIPPED               SKIPPED    SKIPPED
```

## Database Schema

### workflows

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| title | VARCHAR(200) | Workflow title |
| description | TEXT | Workflow description |
| project_id | UUID | Optional project reference |
| status | VARCHAR(20) | Current status |
| current_step | INTEGER | Current execution step |
| requires_approval | BOOLEAN | Whether approval is required |
| approval_status | VARCHAR(20) | Approval status |
| risk_level | VARCHAR(20) | Risk level |
| estimated_time | INTEGER | Estimated duration (seconds) |
| metadata_json | JSON | Additional metadata |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |
| started_at | TIMESTAMP | Execution start time |
| completed_at | TIMESTAMP | Execution completion time |

### workflow_tasks

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| workflow_id | UUID | Foreign key to workflows |
| title | VARCHAR(200) | Task title |
| description | TEXT | Task description |
| priority | VARCHAR(20) | Task priority |
| dependencies | JSON | List of dependency task IDs |
| agent_type | VARCHAR(50) | Agent type to execute |
| status | VARCHAR(20) | Current status |
| retries | INTEGER | Current retry count |
| max_retries | INTEGER | Maximum retries allowed |
| execution_result | JSON | Execution result |
| validation_result | JSON | Validation result |
| duration | INTEGER | Execution duration (seconds) |
| metadata_json | JSON | Additional metadata |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |
| started_at | TIMESTAMP | Execution start time |
| completed_at | TIMESTAMP | Execution completion time |

### workflow_events

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| workflow_id | UUID | Foreign key to workflows |
| task_id | UUID | Optional task reference |
| event_type | VARCHAR(50) | Event type |
| data | JSON | Event data |
| created_at | TIMESTAMP | Event timestamp |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/workflows` | Create a new workflow |
| GET | `/api/v1/workflows` | List workflows |
| GET | `/api/v1/workflows/{id}` | Get workflow details |
| POST | `/api/v1/workflows/{id}/approve` | Approve workflow |
| POST | `/api/v1/workflows/{id}/start` | Start workflow |
| POST | `/api/v1/workflows/{id}/pause` | Pause workflow |
| POST | `/api/v1/workflows/{id}/resume` | Resume workflow |
| POST | `/api/v1/workflows/{id}/cancel` | Cancel workflow |
| GET | `/api/v1/workflows/{id}/summary` | Get execution summary |

## Event Types

| Event | Description |
|-------|-------------|
| workflow_created | Workflow was created |
| workflow_started | Workflow execution started |
| workflow_paused | Workflow was paused |
| workflow_resumed | Workflow was resumed |
| workflow_cancelled | Workflow was cancelled |
| workflow_completed | Workflow completed successfully |
| workflow_failed | Workflow failed |
| task_created | Task was created |
| task_started | Task execution started |
| task_completed | Task completed successfully |
| task_failed | Task failed |
| task_retrying | Task is being retried |
| task_skipped | Task was skipped |
| approval_requested | Approval was requested |
| approval_granted | Approval was granted |
| approval_denied | Approval was denied |

## Configuration

```bash
# Workflow Settings
WORKFLOW_MAX_CONCURRENT_WORKFLOWS=10
WORKFLOW_MAX_TASKS_PER_WORKFLOW=100
WORKFLOW_MAX_RETRIES=3
WORKFLOW_RETRY_DELAY_SECONDS=30
WORKFLOW_TASK_TIMEOUT_SECONDS=600
WORKFLOW_WORKFLOW_TIMEOUT_SECONDS=3600
WORKFLOW_ENABLE_AUTO_APPROVAL=false
WORKFLOW_ENABLE_DEPENDENCY_VALIDATION=true
```

## Frontend Components

- **WorkflowList**: Displays all workflows with status and actions
- **WorkflowDetails**: Shows workflow details and task list
- **TaskGraph**: Visualizes task dependencies
- **ExecutionTimeline**: Shows workflow execution history

## Future Enhancements

1. **Persistent Event Storage**: Store events in PostgreSQL
2. **Parallel Task Execution**: Execute independent tasks concurrently
3. **Rollback Support**: Rollback failed workflows
4. **Human Checkpoints**: Require human approval at specific steps
5. **Agent Integration**: Assign tasks to specific agents
6. **Workflow Templates**: Predefined workflow templates
