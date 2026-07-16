# Planning & Task Decomposition Engine Architecture

## Overview

The ForgeAI Planning Engine transforms natural-language user objectives into structured, executable plans. It classifies intent, decomposes work into granular tasks, analyzes complexity and risk, resolves dependencies, and produces ordered execution plans that can be tracked through their lifecycle.

```
User Request
     │
     ▼
┌─────────────────┐
│ Intent          │  Classifies what the user wants to accomplish
│ Classifier      │  (feature, bug fix, refactor, test, deploy, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Task            │  Breaks intent into discrete, actionable tasks
│ Decomposer      │  with types, priorities, and estimated effort
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Complexity      │  Scores overall plan complexity based on task
│ Analyzer        │  count, types, dependencies, and estimated hours
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Dependency      │  Maps task dependencies, detects cycles,
│ Analyzer        │  computes execution order (topological sort)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Risk            │  Identifies data-loss, security, breaking-change,
│ Analyzer        │  performance, and other risks with mitigation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Plan            │  Assembles all analysis into a complete Plan
│ Generator       │  with metadata, risk buffer, and status tracking
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Planner         │  Orchestrates the full pipeline, manages plan
│ Service         │  storage, history, and CRUD operations
└─────────────────┘
```

## Component Diagram

```
app/planner/
├── __init__.py                 # Public API exports
├── config.py                   # PlannerSettings (env-based config)
├── exceptions.py               # Exception hierarchy
├── schemas/
│   ├── __init__.py
│   └── planner.py              # Pydantic models (Plan, Task, Risk, etc.)
├── intent_classifier.py        # Pattern-based intent classification
├── task_decomposer.py          # Template-driven task decomposition
├── complexity_analyzer.py      # Multi-factor complexity scoring
├── dependency_analyzer.py      # Graph-based dependency analysis
├── risk_analyzer.py            # Keyword + structural risk detection
├── plan_generator.py           # Plan assembly and status management
└── planner_service.py          # Service orchestrator (CRUD + pipeline)

app/api/v1/planner/
├── __init__.py
└── router.py                   # FastAPI endpoints
```

## Intent Classification System

The `IntentClassifier` maps user input to one of nine intent types using regex pattern matching and keyword weighting.

### Intent Types

| Intent | Description | Example Keywords |
|--------|-------------|-----------------|
| `feature_development` | Adding new functionality | add, create, implement, build, new, feature |
| `bug_fix` | Correcting defects | fix, bug, error, broken, crash, failing |
| `refactoring` | Restructuring without behavior change | refactor, clean, improve, optimize, extract |
| `documentation` | Writing/updating docs | document, docstring, readme, comment |
| `testing` | Adding/improving tests | test, spec, verify, coverage, mock |
| `deployment` | Release and deployment | deploy, release, docker, kubernetes, ci/cd |
| `configuration` | Setup and configuration | config, setup, env, dependency, install |
| `research` | Investigation and exploration | research, investigate, explore, evaluate |
| `unknown` | Unclassifiable input | (fallback) |

### Classification Algorithm

1. **Pattern Matching**: Each intent has a set of regex patterns. Matches are counted and weighted.
2. **Keyword Adjustment**: Special keywords (e.g., "urgent", "security", "breaking") adjust scores.
3. **Confidence Calculation**: Combines raw score with text length (longer = more specific).
4. **Sub-Intents**: Secondary intents with score > 0.3 are included.
5. **Fallback**: If no patterns match, intent is `UNKNOWN` with confidence 0.0.

```python
# Example classification
classifier = IntentClassifier()
result = classifier.classify("Fix the authentication bug in the login endpoint")
# result.intent = IntentType.BUG_FIX
# result.confidence = 0.85
# result.keywords = ["fix", "bug", "authentication", "login"]
```

## Task Decomposition Strategy

The `TaskDecomposer` converts classified intent into a list of `Task` objects using intent-specific templates.

### Template System

Each intent type has a predefined task template:

| Intent | Tasks Generated |
|--------|----------------|
| `feature_development` | Analyze requirements → Design approach → Implement → Unit tests → Integration tests → Docs → Review |
| `bug_fix` | Reproduce → Root cause → Implement fix → Regression test → Verify environments |
| `refactoring` | Analyze structure → Create plan → Apply changes → Ensure tests pass → Update docs |
| `documentation` | Identify gaps → Draft content → Review → Publish |
| `testing` | Identify gaps → Write tests → Add fixtures → Run suite → Review |
| `deployment` | Verify build → Prepare artifacts → Deploy staging → Smoke tests → Deploy prod → Monitor |
| `configuration` | Identify needs → Update config → Test changes → Document |
| `research` | Define questions → Gather info → Analyze findings → Summarize |

### Dependency Assignment

Tasks are automatically linked based on type:

- **Implementation** tasks depend on all preceding Research tasks
- **Testing** tasks depend on Implementation tasks
- **Review** tasks depend on the immediately preceding task
- **Documentation** depends on the last Implementation/Refactoring task
- **Deployment** depends on all Testing tasks

### Complexity Estimation

Each task receives an estimated hour value based on:
- Task type (implementation is heaviest, documentation lightest)
- Input word count (proxy for scope)

## Complexity Analysis Algorithm

The `ComplexityAnalyzer` scores a plan across five dimensions:

| Factor | Weight | Trigger |
|--------|--------|---------|
| Task count | 0-3.0 | >3 simple, >7 medium, >12 complex, >20 very complex |
| Type diversity | 0-1.5 | ≥5 unique types = 1.5, ≥3 = 0.5 |
| Dependency density | 0-1.5 | >1.5x tasks = 1.5, >1x = 0.7 |
| Dependency chain length | 0-1.0 | >3 levels = 1.0, >2 = 0.5 |
| Priority distribution | 0-1.0 | >2 critical = 1.0, >60% high = 0.5 |
| Estimated hours | 0-2.0 | >40h = 2.0, >20h = 1.0, >8h = 0.5 |

### Complexity Levels

| Level | Score Range | Description |
|-------|------------|-------------|
| `simple` | 0.0 – 2.0 | Few tasks, low risk, straightforward |
| `medium` | 2.1 – 5.0 | Moderate scope, some dependencies |
| `complex` | 5.1 – 8.0 | Significant scope, many dependencies |
| `very_complex` | 8.1+ | Large scope, critical risks, long chains |

## Dependency Analysis

The `DependencyAnalyzer` provides graph-based analysis of task relationships.

### Capabilities

1. **Cycle Detection**: DFS-based detection of circular dependencies
2. **Validation**: Checks for missing dependency references
3. **Topological Sort**: Computes parallelizable execution levels
4. **Critical Path**: Finds the longest path (highest total hours) through the graph
5. **Orphan Detection**: Identifies tasks not depended upon by any other task

### Execution Order

Tasks are grouped into levels where each level can execute in parallel:

```
Level 0: [task-000, task-001]        ← No dependencies
Level 1: [task-002, task-003]        ← Depend only on Level 0
Level 2: [task-004]                  ← Depends on Level 1
Level 3: [task-005, task-006]        ← Depends on Level 2
```

## Risk Analysis

The `RiskAnalyzer` identifies risks through three approaches:

### 1. Keyword-Based Detection

Scans task titles and descriptions against risk category patterns:

| Category | Keywords | Default Impact |
|----------|----------|---------------|
| `data_loss` | delete, remove, drop, truncate | 0.9 |
| `security` | auth, password, token, secret | 0.9 |
| `breaking_change` | breaking, backward, deprecat | 0.8 |
| `performance` | slow, latency, timeout, memory | 0.6 |
| `database` | migration, schema, table, index | 0.7 |
| `deployment` | deploy, release, production | 0.7 |

### 2. Structural Analysis

Detects process-level risks:
- Implementation tasks without testing tasks
- Majority of tasks at high complexity
- Too many critical-priority tasks

### 3. Type-Based Analysis

Identifies risks from task type composition:
- Deployment tasks present (requires staging/rollback)
- Multiple refactoring tasks (compounding risk)

### Risk Levels

| Level | Probability × Impact | Response |
|-------|---------------------|----------|
| `low` | < 0.15 | Monitor |
| `medium` | 0.15 – 0.40 | Mitigate |
| `high` | 0.40 – 0.65 | Active mitigation required |
| `critical` | > 0.65 | Immediate attention |

## Plan Generation

The `PlanGenerator` assembles the final plan:

1. **ID Generation**: MD5 hash of title + timestamp
2. **Risk Buffer**: Adds time buffer based on high/critical risks:
   - ≥3 high/critical risks → 30% buffer
   - ≥1 high/critical risk → 15% buffer
   - Any risks → 5% buffer
3. **Metadata**: Includes generator version, intent, confidence, context
4. **Status Management**: Validates state transitions (DRAFT → ACTIVE → COMPLETED)

### Plan Lifecycle

```
DRAFT ──────→ ACTIVE ──────→ COMPLETED
  │              │
  │              ├──→ FAILED ──→ ACTIVE (retry)
  │              │
  └──→ CANCELLED ←┘
```

## API Reference

See [Planning-API.md](Planning-API.md) for complete endpoint documentation.

### Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/planner/plans` | Create a new plan |
| `GET` | `/api/v1/planner/plans` | List all plans |
| `GET` | `/api/v1/planner/plans/{id}` | Get a specific plan |
| `PUT` | `/api/v1/planner/plans/{id}` | Update a plan |
| `DELETE` | `/api/v1/planner/plans/{id}` | Delete a plan |
| `GET` | `/api/v1/planner/plans/{id}/history` | Get plan history |
| `GET` | `/api/v1/planner/history` | List all history |

## Usage Examples

### Python SDK

```python
from app.planner import PlannerService
from app.planner.schemas.planner import PlanCreateRequest

service = PlannerService()

# Create a plan
request = PlanCreateRequest(
    title="Add user authentication",
    description="Implement JWT-based authentication with login, registration, and password reset endpoints",
    goals=["Secure API endpoints", "Support JWT tokens"],
    context={"framework": "FastAPI", "database": "PostgreSQL"},
)

plan = await service.create_plan(request)
print(f"Plan {plan.id}: {len(plan.tasks)} tasks, {plan.estimated_total_hours}h")
print(f"Complexity: {plan.complexity.level.value}")
print(f"Risks: {len(plan.risks)} identified")
```

### Direct Component Usage

```python
from app.planner.intent_classifier import IntentClassifier
from app.planner.task_decomposer import TaskDecomposer

# Classify intent
classifier = IntentClassifier()
result = classifier.classify("Fix the login bug")
print(result.intent)  # IntentType.BUG_FIX

# Decompose into tasks
decomposer = TaskDecomposer()
tasks = decomposer.decompose("Fix the login bug", result)
for task in tasks:
    print(f"  [{task.priority.value}] {task.title} ({task.estimated_hours}h)")
```

## Configuration

All settings are configurable via environment variables with the `PLANNER_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `PLANNER_MAX_TASKS_PER_PLAN` | 50 | Maximum tasks per plan |
| `PLANNER_MAX_PLAN_HISTORY` | 100 | Maximum history entries |
| `PLANNER_DEFAULT_CONTEXT_TOKENS` | 4096 | Default context window |
| `PLANNER_COMPLEXITY_THRESHOLDS` | `{simple: 3, medium: 7, complex: 12, very_complex: 20}` | Task count thresholds |

## Future Enhancements

### Short-term
- [ ] LLM-powered intent classification (replace regex patterns)
- [ ] Natural language task generation from templates
- [ ] Plan cloning and forking
- [ ] Real-time plan progress tracking via WebSocket

### Medium-term
- [ ] Multi-agent plan execution
- [ ] Plan comparison and diff
- [ ] Historical plan analytics
- [ ] Custom template authoring

### Long-term
- [ ] Adaptive planning with feedback loops
- [ ] Cross-project dependency tracking
- [ ] Resource-aware scheduling (team capacity)
- [ ] Integration with project management tools (Jira, Linear)
