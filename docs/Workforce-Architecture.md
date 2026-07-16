# Enterprise AI Workforce Architecture

## Overview

The Enterprise AI Workforce module creates a team of specialized AI agents that work together under the coordination of a Supervisor Agent. This phase establishes the runtime architecture for AI employees without implementing execution capabilities.

## Architecture

```
app/agents/enterprise/
├── __init__.py
├── schemas.py           # Pydantic models
├── memory.py            # Agent memory system
├── communication.py     # Message bus
├── prompts.py           # Prompt management
├── policies.py          # Policy engine
├── validators.py        # Agent validation
├── registry.py          # Dynamic agent registry
├── supervisor.py        # Supervisor agent
├── specialized.py       # Specialized agent implementations
└── runtime.py           # Agent runtime coordinator
```

## Agent Roles

| Role | Description | Capabilities |
|------|-------------|--------------|
| **Supervisor** | Orchestrates workflows | Workflow analysis, task assignment, progress tracking |
| **Software Engineer** | Implements code | Code generation, modification, testing |
| **QA Engineer** | Reviews quality | Quality review, test generation, edge case analysis |
| **Code Reviewer** | Reviews PRs | Code review, security review, architecture review |
| **Technical Writer** | Generates docs | Documentation, changelogs, migration guides |
| **DevOps Engineer** | Infrastructure | Docker, CI/CD, deployment |
| **Database Engineer** | Database work | Schema design, migrations, optimization |
| **Research Engineer** | Research | Framework analysis, dependency analysis |

## Core Components

### Supervisor Agent

The Supervisor is the "operating system kernel" of ForgeAI:

- Receives workflows from Planner
- Analyzes workflow requirements
- Determines required specialists
- Assigns tasks to agents
- Tracks execution progress
- Collects outputs
- Validates completion
- Generates execution summary

**The Supervisor NEVER:**
- Writes code
- Modifies repositories
- Calls tools
- Executes tasks directly

### Agent Registry

Dynamic registry for agent discovery:

- Agents register with ID, role, capabilities
- Supervisor discovers agents dynamically
- Supports capability-based matching
- Tracks agent status and availability

### Communication Bus

Message-based communication:

- Agents NEVER communicate directly
- All communication flows through Supervisor
- Supports task assignment, progress, results
- Maintains message history

### Agent Memory

Each agent has:
- Short-Term Memory: Recent interactions
- Task Memory: History of completed tasks
- Execution Context: Current task context
- Conversation State: Current conversation

**Agents do NOT own:**
- Long-Term Memory (belongs to Memory Engine)
- Repository Memory (belongs to Memory Engine)

### Prompt Management

Every agent owns:
- System Prompt: Core instructions
- Role Prompt: Role-specific instructions
- Task Prompt: Task execution instructions
- Validation Prompt: Validation instructions
- Reflection Prompt: Self-reflection instructions

Prompts are stored separately and never hardcoded.

### Policy Engine

Policies define agent constraints:
- Allowed Tasks: Tasks the agent can perform
- Forbidden Tasks: Tasks the agent cannot perform
- Tool Permissions: Tools the agent can use
- Repository Access: Repositories the agent can access
- Execution Limits: Max concurrent tasks, retries, timeout

### Agent Validation

Before accepting work, agents validate:
- Capability: Required capabilities available
- Required Context: Necessary context available
- Dependencies: Dependencies satisfied
- Repository Availability: Repository accessible

## Agent States

```
IDLE ──────────────► ASSIGNED ──────────────► PREPARING
  │                      │                      │
  │                      │                      ▼
  │                      │                   WAITING
  │                      │                      │
  │                      │                      ▼
  │                      │                  EXECUTING
  │                      │                      │
  │                      │          ┌───────────┴───────────┐
  │                      │          ▼                       ▼
  │                      │      REVIEWING               FAILED
  │                      │          │                       │
  │                      │          ▼                       │
  │                      │      COMPLETED                  │
  │                      │          │                       │
  │                      └──────────┴───────────────────────┘
  │
  └──────────────────────────────────────────────────────────► UNAVAILABLE/OFFLINE
```

## Event Types

| Event | Description |
|-------|-------------|
| agent_registered | Agent was registered |
| agent_offline | Agent went offline |
| task_assigned | Task was assigned |
| task_accepted | Task was accepted |
| task_rejected | Task was rejected |
| task_started | Task execution started |
| task_completed | Task completed |
| task_failed | Task failed |
| heartbeat | Agent heartbeat |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workforce/` | List all agents |
| GET | `/api/v1/workforce/status` | Get status summary |
| GET | `/api/v1/workforce/{id}` | Get agent details |
| GET | `/api/v1/workforce/role/{role}` | Get agents by role |
| POST | `/api/v1/workforce/register` | Register agent |
| POST | `/api/v1/workforce/{id}/heartbeat` | Update heartbeat |
| POST | `/api/v1/workforce/{id}/status` | Update status |
| GET | `/api/v1/workforce/events/recent` | Get recent events |
| POST | `/api/v1/workforce/workflow/{id}/process` | Process workflow |

## Message Types

| Type | Description |
|------|-------------|
| task_assignment | Assign task to agent |
| task_accepted | Agent accepted task |
| task_rejected | Agent rejected task |
| progress_update | Progress report |
| warning | Warning message |
| failure | Failure report |
| success | Success report |
| information | Information message |
| request | Request for information |
| response | Response to request |

## Frontend Components

- **Workforce Dashboard**: Overview of all AI employees
- **Agent Details**: Detailed agent information
- **Status Cards**: Real-time agent status
- **Execution Timeline**: Workflow execution history

## Future Enhancements

1. **LangGraph Integration**: Add LangGraph orchestration
2. **Persistent Storage**: Store agents in PostgreSQL
3. **Agent Learning**: Improve from task outcomes
4. **Human-in-the-Loop**: Add approval gates
5. **Streaming Events**: Real-time event streaming
6. **Agent Communication**: Direct agent-to-agent messaging
