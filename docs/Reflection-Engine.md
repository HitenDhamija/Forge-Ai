# Reflection & Self-Correction Engine

## Overview

The Reflection Engine ensures no code is accepted as a first draft. Every implementation passes through internal critique, alternative generation, and iterative improvement before reaching human review.

**Philosophy:** Never trust first generation. Every output must pass through reflection.

## Pipeline

```
Implementation
       ↓
Internal Critique
       ↓
Architecture Review
       ↓
Security Review
       ↓
Performance Review
       ↓
Alternative Solutions
       ↓
Improved Version
       ↓
Reviewer
```

## Components

### Critique Engine

Generates internal critique across 9 categories:

| Category | Questions |
|----------|-----------|
| Architecture | Did I follow project architecture? Did I duplicate logic? |
| Security | Are security issues introduced? Did I validate inputs? |
| Performance | Could performance improve? Are there N+1 queries? |
| Readability | Can this be simplified? Will another engineer understand? |
| Maintainability | Is this easy to modify? Is the code modular? |
| Scalability | Will this scale? Are there bottlenecks? |
| Dependency | Are dependencies necessary? Are versions pinned? |
| Testing | Did I update tests? Are edge cases covered? |
| Documentation | Did I update documentation? Is the README updated? |

### Alternative Generator

Generates multiple implementations and compares:

```python
from app.agents.reflection import AlternativeGenerator

generator = AlternativeGenerator()
comparison = await generator.generate(
    original_code=code,
    file_path="src/auth.py"
)
```

**Variants:**
- Original: Existing implementation
- Simplified: Reduced complexity
- Optimized: Performance-focused

### Confidence Engine

Calculates confidence scores:

```python
from app.agents.reflection import ConfidenceEngine

engine = ConfidenceEngine()
score = await engine.calculate(
    code=code,
    file_path="src/auth.py"
)
```

**Dimensions:**
- Architecture (25%)
- Security (30%)
- Testing (20%)
- Documentation (10%)
- Maintainability (15%)

**Levels:** High (80+), Medium (60+), Low (<60)

### Improvement Engine

Iteratively improves code:

```python
from app.agents.reflection import ImprovementEngine

engine = ImprovementEngine()
result = await engine.improve(
    code=code,
    file_path="src/auth.py",
    critique_items=critique.items,
    confidence_score=65.0,
    max_passes=2
)
```

**Features:**
- Multiple improvement passes (default: 2, max: 5)
- Stops when confidence exceeds threshold (80)
- Applies improvements based on critique

### Reflection Memory

Stores reflection history for learning:

```python
from app.agents.reflection import ReflectionMemory

memory = ReflectionMemory()
await memory.store(
    reflection_id="ref-123",
    task_id="task-123",
    ...
)
```

**Tracks:**
- Mistakes made
- Corrections applied
- Chosen solutions
- Rejected solutions
- Reasoning

## API Endpoints

### Run Reflection

```http
POST /api/v1/reflection/run
Content-Type: application/json

{
  "task_id": "task-123",
  "repository_id": "repo-123",
  "code": "...",
  "file_path": "src/auth.py",
  "max_passes": 2
}
```

### Get Reflection

```http
GET /api/v1/reflection/{reflection_id}
```

### Get History

```http
GET /api/v1/reflection/history?task_id=task-123
```

### Get Statistics

```http
GET /api/v1/reflection/stats
```

## Self-Critique Questions

Every generated implementation internally answers:

1. Did I follow project architecture?
2. Did I duplicate logic?
3. Can existing code be reused?
4. Did I break SOLID?
5. Could performance improve?
6. Are security issues introduced?
7. Can this implementation be simplified?
8. Will another engineer understand this?
9. Did I update documentation?
10. Did I update tests?

## Iterative Improvement

Default passes: 2
Maximum passes: 5
Stop condition: Confidence exceeds 80

## Frontend

The Reflection Workspace provides:

- **Input Panel** - Code and parameters
- **Confidence Cards** - Before/after scores
- **Critique Summary** - Issues found
- **Improved Code** - Final result
- **History** - Past reflections

## Integration

### With Software Engineer

```python
# Software Engineer generates code
engineer = SoftwareEngineerAgent()
task = await engineer.execute_task(...)

# Reflection improves it
reflection = ReflectionEngine()
result = await reflection.run_reflection(
    task_id=task.task_id,
    repository_id=task.repository_id,
    code=task.generated_code[0].content,
    file_path=task.generated_code[0].file_path
)

# Use improved code
improved_code = result.final_code
```

### With Review Pipeline

Reflection is mandatory before code reaches the Reviewer:

```
Software Engineer → Reflection → Reviewer → QA → Documentation
```

## Safety Features

1. **No code execution** - Reflection only analyzes
2. **No repository modification** - Code stays in memory
3. **Full audit trail** - Every reflection logged
4. **Configurable passes** - Control improvement depth
5. **Confidence threshold** - Stop when good enough
