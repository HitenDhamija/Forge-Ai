# Autonomous Execution Engine

## Overview

The Execution Engine provides controlled, safe, and auditable execution of workflows. It ensures every repository modification is reproducible, rollbackable, and human-approved.

**Philosophy:** ForgeAI must NEVER directly modify repositories. Execution must be Safe, Auditable, Rollbackable, Interruptible, and Human Approved.

## Pipeline

```
Approved Workflow
       ↓
Execution Runtime
       ↓
Task Scheduler
       ↓
Agent Dispatch
       ↓
MCP Tool Request
       ↓
Repository Update
       ↓
Validation
       ↓
Checkpoint
       ↓
Continue
       ↓
Execution Report
```

## Components

### Execution Runtime

Main orchestrator:

```python
from app.execution import ExecutionRuntime

runtime = ExecutionRuntime()
execution = await runtime.start_execution(
    workflow_id="workflow-123",
    repository_id="repo-123",
    steps=[
        {"agent_type": "software_engineer", "description": "Implement feature"},
        {"agent_type": "qa_engineer", "description": "Generate tests"},
    ]
)
execution = await runtime.run_execution(execution.execution_id)
```

### Dispatcher

Dispatches tasks to agents:

```python
from app.execution import Dispatcher, AgentType

dispatcher = Dispatcher()
task = await dispatcher.dispatch(
    execution_id="exec-123",
    task_id="task-123",
    agent_type=AgentType.SOFTWARE_ENGINEER,
    description="Implement JWT authentication",
    parameters={"file_path": "src/auth.py"}
)
```

### Checkpoint Manager

Manages checkpoints for rollback:

```python
from app.execution import CheckpointManager, CheckpointType

manager = CheckpointManager()
checkpoint = await manager.create_checkpoint(
    execution_id="exec-123",
    step_id="step-1",
    checkpoint_type=CheckpointType.GIT_COMMIT,
    description="Before auth implementation",
    data={"files": ["src/auth.py"]},
    git_commit_hash="abc123"
)
```

### Rollback Engine

Handles rollback operations:

```python
from app.execution import RollbackEngine

engine = RollbackEngine()
result = await engine.rollback(
    execution_id="exec-123",
    checkpoint_data=checkpoint.data,
    files_modified=["src/auth.py"],
    git_branch="feature/auth",
    git_commit="abc123"
)
```

### Validation Engine

Validates execution results:

```python
from app.execution import ValidationEngine

engine = ValidationEngine()
result = await engine.validate(
    files_modified=["src/auth.py"],
    files_created=["tests/test_auth.py"],
    files_deleted=[]
)
```

### Progress Tracker

Tracks execution progress:

```python
from app.execution import ProgressTracker, TaskStatus

tracker = ProgressTracker()
tracker.update_task(
    execution_id="exec-123",
    task_id="task-123",
    status=TaskStatus.RUNNING,
    progress=50.0,
    current_file="src/auth.py"
)
```

## Safety Features

### Git Safety

Before execution:
1. Create new branch
2. Create checkpoint
3. Record commit hash
4. Store rollback reference

### Auto Rollback

Automatic rollback on failure:
- Restores files to checkpoint state
- Reverts git changes
- Logs rollback operation

### Checkpoints

Configurable checkpoints:
- Before modifying authentication
- Before database migrations
- Before deleting files
- Before updating dependencies

## API Endpoints

### Start Execution

```http
POST /api/v1/execution/start
Content-Type: application/json

{
  "workflow_id": "workflow-123",
  "repository_id": "repo-123",
  "steps": [
    {
      "agent_type": "software_engineer",
      "description": "Implement feature",
      "parameters": {"file_path": "src/feature.py"}
    }
  ]
}
```

### Pause Execution

```http
POST /api/v1/execution/pause
Content-Type: application/json

{
  "execution_id": "exec-123"
}
```

### Resume Execution

```http
POST /api/v1/execution/resume
Content-Type: application/json

{
  "execution_id": "exec-123"
}
```

### Cancel Execution

```http
POST /api/v1/execution/cancel
Content-Type: application/json

{
  "execution_id": "exec-123"
}
```

### Rollback Execution

```http
POST /api/v1/execution/rollback
Content-Type: application/json

{
  "execution_id": "exec-123"
}
```

### Get Execution

```http
GET /api/v1/execution/{execution_id}
```

### Get Execution Logs

```http
GET /api/v1/execution/{execution_id}/logs
```

### List Executions

```http
GET /api/v1/execution/list?status=running
```

## Frontend

The Execution Center provides:

- **Execution List** - View all executions
- **Status Overview** - Running, completed, failed counts
- **Progress Tracking** - Current step, agent, file
- **File Changes** - Modified, created, deleted files
- **Live Logs** - Real-time execution logs
- **Control Buttons** - Pause, Resume, Cancel, Rollback
- **Commit History** - Git commits created

## Database Models

### executions
- id, workflow_id, repository_id, status
- started_at, completed_at, execution_duration
- summary (JSON)

### execution_steps
- id, execution_id, step_number
- task_id, agent_type, description
- parameters, dependencies, requires_approval
- status, result, started_at, completed_at

### execution_logs
- id, execution_id, step_id
- level, message, agent_id, tool_id
- details, timestamp

### rollback_points
- id, execution_id, step_id
- checkpoint_type, description, data
- git_commit_hash, branch_name

### execution_artifacts
- id, execution_id, artifact_type
- file_path, content, metadata

## Integration

### With Workflow Runtime

```python
# Workflow approved
workflow = await workflow_service.approve(workflow_id)

# Start execution
execution = await execution_runtime.start_execution(
    workflow_id=workflow.id,
    repository_id=workflow.repository_id,
    steps=workflow.steps
)
```

### With MCP Tools

All file operations go through MCP:
- Filesystem MCP for file operations
- Git MCP for version control
- Terminal MCP for safe commands

### With Agents

Execution dispatches to:
- Software Engineer Agent
- QA Engineer Agent
- Reviewer Agent
- Documentation Agent
