# Autonomous Software Engineer Agent

## Overview

The Software Engineer Agent is the first fully operational AI Employee in ForgeAI. It behaves like a senior software engineer, following a strict engineering workflow:

1. **Understand** - Analyze the task and requirements
2. **Analyze Repository** - Load context, architecture, and patterns
3. **Collect Context** - Gather all relevant information
4. **Review Architecture** - Understand existing patterns
5. **Plan Implementation** - Create step-by-step plan
6. **Generate Changes** - Write code following conventions
7. **Validate** - Check syntax and compatibility
8. **Review** - Perform self-review
9. **Prepare Commit** - Generate commit message

**Never skips steps. Never modifies code without approval.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Endpoints                               │
│  POST /execute  │  POST /analyze  │  GET /status  │  GET /history   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Software Engineer Agent                          │
│  Context Loading → Style Analysis → Planning → Code Generation     │
│  → Diff Generation → Review → Validation → Commit Summary          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
        ┌──────────┬──────────┬────┴────┬──────────┬──────────┐
        ▼          ▼          ▼         ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Context  │ │  Style   │ │Implement │ │  Code    │ │  Diff    │
│ Loader   │ │ Analyzer │ │ Planner  │ │Generator │ │Generator │
└──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
                                   │
        ┌──────────┬──────────┬────┴────┬──────────┐
        ▼          ▼          ▼         ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│  Review  │ │Validation│ │  Commit  │ │ Tool     │
│  Engine  │ │  Engine  │ │ Summary  │ │ Runtime  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

## Components

### Context Loader

Retrieves repository context for implementation:

```python
loader = ContextLoader()
context = await loader.load_context(
    repository_id="repo-123",
    task_description="Implement JWT authentication",
    target_files=["src/auth.py"]
)
```

Returns:
- Repository summary
- Architecture patterns
- Dependencies
- Coding standards
- Existing patterns
- Database models
- API endpoints

### Style Analyzer

Analyzes coding conventions:

```python
analyzer = StyleAnalyzer()
profile = await analyzer.analyze(repository_id, files)
```

Analyzes:
- Naming conventions
- Import style
- Docstring format
- Type hints
- Error handling
- Logging patterns

### Implementation Planner

Creates step-by-step implementation plan:

```python
planner = ImplementationPlanner()
plan = await planner.plan(
    task_type=TaskType.FEATURE,
    task_description="Implement JWT authentication",
    context=context,
    target_files=["src/auth.py"]
)
```

Task types:
- `feature` - New feature implementation
- `bug_fix` - Bug fix
- `refactor` - Code refactoring
- `api_creation` - New API endpoint
- `database_migration` - Database changes
- `frontend_component` - UI component
- `backend_service` - Backend service
- `documentation` - Documentation update

### Code Generator

Generates code from templates:

```python
generator = CodeGenerator()
code = await generator.generate_from_spec(
    spec={
        "type": "service",
        "class_name": "AuthService",
        "description": "JWT authentication service",
        "file_path": "src/services/auth.py"
    },
    context=context
)
```

Templates:
- `service` - Service class
- `repository` - Repository pattern
- `schema` - Pydantic schemas
- `router` - FastAPI router

### Diff Generator

Generates unified diffs:

```python
diff_generator = DiffGenerator()
diff = diff_generator.generate(
    file_path="src/auth.py",
    old_content=old_code,
    new_content=new_code
)
```

### Review Engine

Performs self-review:

```python
review_engine = ReviewEngine()
review = await review_engine.review(
    code=generated_code,
    file_path="src/auth.py",
    context=context
)
```

Reviews:
- Architecture consistency
- Naming conventions
- Security issues
- Performance problems
- Code style

### Validation Engine

Validates generated code:

```python
validation_engine = ValidationEngine()
result = await validation_engine.validate(
    code=generated_code,
    file_path="src/auth.py"
)
```

Validates:
- Python syntax
- Import compatibility
- Security patterns
- Naming conventions

### Commit Summary

Generates commit messages:

```python
commit_gen = CommitSummaryGenerator()
summary = await commit_gen.generate(
    task_description="Implement JWT authentication",
    files_changed=["src/auth.py"],
    changes={"src/auth.py": {"additions": 50, "deletions": 0}}
)
```

## API Endpoints

### Execute Task

```http
POST /api/v1/agents/software-engineer/execute
Content-Type: application/json

{
  "repository_id": "repo-123",
  "task_description": "Implement JWT authentication",
  "task_type": "feature",
  "target_files": ["src/auth.py", "src/api/auth.py"]
}
```

### Analyze Task

```http
POST /api/v1/agents/software-engineer/analyze
Content-Type: application/json

{
  "repository_id": "repo-123",
  "task_description": "Implement JWT authentication"
}
```

### Get Status

```http
GET /api/v1/agents/software-engineer/status
```

### Get History

```http
GET /api/v1/agents/software-engineer/history
```

### Approve Task

```http
POST /api/v1/agents/software-engineer/approve
Content-Type: application/json

{
  "task_id": "task-abc123"
}
```

### Reject Task

```http
POST /api/v1/agents/software-engineer/reject
Content-Type: application/json

{
  "task_id": "task-abc123",
  "reason": "Needs error handling"
}
```

## Agent States

```
IDLE → ANALYZING → PLANNING → GENERATING → REVIEWING → VALIDATING → AWAITING_APPROVAL → COMPLETED
                                                                                         ↓
                                                                                      FAILED
```

## Frontend

The Software Engineer Workspace provides:

- **Task Input Panel** - Create new tasks
- **Task Header** - View task status
- **Overview Tab** - Target files and commit summary
- **Generated Code Tab** - View generated code
- **Diff Tab** - View code changes
- **Review Tab** - Review results and validation
- **Execution Log Tab** - Task execution timeline
- **Approval Dialog** - Approve or reject implementation
- **Task History** - View all tasks

## Safety Features

1. **Never modifies without approval** - All changes require explicit approval
2. **Self-review** - Code is reviewed before presentation
3. **Validation** - Syntax and compatibility checked
4. **Diff generation** - Clear view of all changes
5. **Rollback support** - Can revert changes if needed
6. **Execution logging** - Full audit trail

## Integration Points

- **Repository Intelligence** - Loads repository context
- **Semantic Memory** - Uses memory for context
- **Tool Runtime** - Executes file operations
- **Workflow Runtime** - Integrates with workflows
- **Enterprise Workforce** - Can be assigned by supervisor

## Example Usage

```python
from app.agents.software_engineer import SoftwareEngineerAgent, TaskType

agent = SoftwareEngineerAgent()

# Execute task
task = await agent.execute_task(
    repository_id="repo-123",
    task_description="Implement JWT authentication with refresh tokens",
    task_type=TaskType.FEATURE,
    target_files=["src/auth.py", "src/api/auth.py"]
)

# Review results
print(f"State: {task.state}")
print(f"Generated code: {len(task.generated_code)} files")
print(f"Review score: {task.review_result.score}")

# Approve if satisfied
await agent.approve_task(task.task_id)
```
