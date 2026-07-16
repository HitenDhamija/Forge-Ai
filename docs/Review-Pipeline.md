# Enterprise Code Review, QA & Documentation Pipeline

## Overview

The Engineering Quality Pipeline ensures all generated code passes through comprehensive review, testing, and documentation before approval. No generated code bypasses this pipeline.

## Pipeline Flow

```
Software Engineer
       ↓
    Diff
       ↓
 Code Reviewer
       ↓
  QA Engineer
       ↓
Technical Writer
       ↓
  Approval
       ↓
Repository Update
```

## Components

### Review Agent

Orchestrates security, performance, and architecture reviews:

```python
from app.agents.reviewer import ReviewAgent

agent = ReviewAgent()
review = await agent.start_review(
    task_id="task-123",
    repository_id="repo-123",
    code=generated_code,
    file_path="src/auth.py",
    task_description="Implement JWT authentication"
)
```

### Security Checker

Analyzes code for vulnerabilities:

| Check | Description |
|-------|-------------|
| Hardcoded Secrets | Passwords, API keys, tokens |
| SQL Injection | Unparameterized queries |
| XSS | Cross-site scripting risks |
| Eval Usage | eval/exec calls |
| Path Traversal | Unsafe file access |
| Weak Crypto | MD5, SHA1 usage |

### Performance Checker

Analyzes performance issues:

| Check | Description |
|-------|-------------|
| N+1 Queries | Loop with DB calls |
| Blocking I/O | Sync in async context |
| String Concat | O(n²) in loops |
| Nested Loops | Deep iteration |
| Repeated Computation | Duplicate calculations |

### Architecture Checker

Validates architectural patterns:

| Check | Description |
|-------|-------------|
| SRP | Single Responsibility |
| DIP | Dependency Inversion |
| Repository Pattern | CRUD methods |
| Service Layer | Business logic |
| Naming | PascalCase, snake_case |

### Quality Score Calculator

Calculates overall quality:

```python
from app.agents.reviewer import QualityScoreCalculator

calculator = QualityScoreCalculator()
score = calculator.calculate(
    security_report=security_report,
    performance_report=performance_report,
    architecture_report=architecture_report
)
```

**Weights:**
- Security: 30%
- Architecture: 25%
- Performance: 20%
- Readability: 10%
- Testing: 10%
- Documentation: 5%

**Grades:** A (90+), B (80+), C (70+), D (60+), F (<60)

### QA Agent

Generates tests and estimates coverage:

```python
from app.agents.qa import QAAgent

agent = QAAgent()
qa = await agent.start_qa(
    task_id="task-123",
    repository_id="repo-123",
    code=generated_code,
    file_path="src/auth.py"
)
```

**Test Types:**
- Unit Tests
- Integration Tests
- Edge Case Tests

### Documentation Agent

Generates documentation:

```python
from app.agents.documentation import DocumentationAgent

agent = DocumentationAgent()
doc = await agent.start_documentation(
    task_id="task-123",
    repository_id="repo-123",
    task_description="Implement JWT authentication",
    files_changed=["src/auth.py"],
    changes={"src/auth.py": {"additions": 50, "deletions": 0}}
)
```

**Generates:**
- Release Notes
- Change Report
- API Documentation
- README Updates

## API Endpoints

### Start Review

```http
POST /api/v1/review/start
Content-Type: application/json

{
  "task_id": "task-123",
  "repository_id": "repo-123",
  "code": "...",
  "file_path": "src/auth.py",
  "task_description": "Implement JWT authentication"
}
```

### Get Review

```http
GET /api/v1/review/{review_id}
```

### Approve Review

```http
POST /api/v1/review/approve
Content-Type: application/json

{
  "review_id": "review-123",
  "comments": ["Looks good"]
}
```

### Reject Review

```http
POST /api/v1/review/reject
Content-Type: application/json

{
  "review_id": "review-123",
  "reason": "Security issues found"
}
```

### Get Testing Report

```http
GET /api/v1/testing/report
```

### Get Documentation Report

```http
GET /api/v1/documentation/report
```

## Approval Policy

Code cannot proceed unless:

1. **Security Review passes** (score >= 70)
2. **Architecture Review passes** (no violations)
3. **Minimum Quality Score reached** (>= 70)
4. **Tests generated**
5. **Documentation generated**

## Frontend

The Engineering Review Center provides:

- **Pipeline Status** - Overview cards
- **Review List** - Recent reviews
- **Score Cards** - Security, Performance, Architecture, Quality
- **Comments Panel** - Reviewer feedback
- **Approval Dialog** - Approve/reject with reasons

## Integration

### With Software Engineer Agent

```python
# Software Engineer generates code
agent = SoftwareEngineerAgent()
task = await agent.execute_task(...)

# Review pipeline reviews it
review_agent = ReviewAgent()
review = await review_agent.start_review(...)

# QA generates tests
qa_agent = QAAgent()
qa = await qa_agent.start_qa(...)

# Documentation generates docs
doc_agent = DocumentationAgent()
doc = await doc_agent.start_documentation(...)
```

### With Workflow Runtime

New workflow states:
- `UNDER_REVIEW`
- `UNDER_TEST`
- `DOCUMENTING`
- `READY_FOR_APPROVAL`

## Safety Features

1. **No automatic commits** - All changes require approval
2. **No repository modification** - Code remains in staging
3. **Full audit trail** - Every review is logged
4. **Reversible** - Can reject and retry
5. **Traceable** - Links to original task
