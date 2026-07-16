```
  ███████╗ ██████╗  █████╗ ██████╗ ███████╗██████╗     ███████╗██╗   ██╗███████╗███╗   ██╗████████╗
  ██╔════╝██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗    ██╔════╝██║   ██║██╔════╝████╗  ██║╚══██╔══╝
  █████╗  ██║   ██║███████║██║  ██║█████╗  ██████╔╝    ███████╗██║   ██║█████╗  ██╔██╗ ██║   ██║
  ██╔══╝  ██║   ██║██╔══██║██║  ██║██╔══╝  ██╔══██╗    ╚════██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
  ██║     ╚██████╔╝██║  ██║██████╔╝███████╗██║  ██║    ███████║╚██████╔╝███████╗██║ ╚████║   ██║
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
```

# ForgeAI — Autonomous AI Operations Platform

**An AI-powered software engineering team that lives in your browser.**

[![CI](https://github.com/your-org/forgeai/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/forgeai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0--rc1-blue.svg)](https://github.com/your-org/forgeai)

---

## What is ForgeAI?

ForgeAI is an autonomous AI operations platform that orchestrates a team of specialized AI agents to understand codebases, plan implementations, write code, review it, run tests, write documentation, and deploy changes — all under human supervision with approval gates.

**Think of it as hiring an AI engineering team**: a Software Engineer, QA Engineer, Code Reviewer, DevOps Engineer, and Technical Writer — working together on your codebase, with you as the engineering manager.

### Why ForgeAI Exists

| Problem | How ForgeAI Solves It |
|---------|----------------------|
| AI coding assistants lack project context | Repository Intelligence Engine indexes your entire codebase with AST parsing and knowledge graphs |
| Code changes break things in unexpected ways | Execution Engine creates git checkpoints and auto-rolls back on failure |
| No way to control what AI does to production | Approval Gates with risk levels (low/medium/high/critical) require human sign-off |
| AI forgets what it learned about your code | Semantic Memory Engine (ChromaDB + embeddings) persists knowledge across sessions |
| Solo developers need a full team | 5 specialized AI agents with distinct roles collaborate on tasks |
| Manual code review is slow and inconsistent | Review Pipeline checks security, performance, architecture, and quality scores automatically |

---

## Core Features

### Repository Intelligence
Import any codebase (git URL, zip, or folder) and ForgeAI automatically:
- Detects languages (Python, TypeScript, Java, Go, Rust, and 10+ more)
- Identifies frameworks (FastAPI, React, Next.js, Spring Boot, Django, etc.)
- Parses ASTs via tree-sitter for deep code understanding
- Builds a semantic knowledge graph (modules, classes, functions, routes, DB models)
- Detects architecture patterns (MVC, Clean Architecture, Microservices, etc.)

**How to use Repository Intelligence:**
1. Go to **Repositories** page
2. Click **Import Repository**
3. Choose upload method: Folder, Git URL, or ZIP file
4. Select your code project
5. Wait for analysis to complete
6. View detailed repository information

**What it shows:**
- **File Tree**: Complete directory structure of your project
- **Language Distribution**: Percentage breakdown of languages used
- **Framework Detection**: frameworks and libraries identified
- **Code Metrics**: Total files, lines of code, average file size
- **Architecture Patterns**: Detected design patterns and structures
- **Dependencies**: Project dependencies and their versions

### Semantic Memory Engine
ForgeAI remembers everything about your codebase across sessions:
- Embedding service (BAAI/bge-small-en-v1.5) with ChromaDB vector store
- Hybrid retrieval (dense vectors + sparse BM25) with multi-stage reranking
- Relationship graph linking related code, concepts, and decisions
- Query classification and context building for LLM consumption

**How to use Semantic Memory:**
1. **Index Repository**: Click the "Index Repository" button to scan your project files
2. **Search**: Type any query (e.g., "login function", "API endpoint", "database connection")
3. **Filter by Project**: Use the project selector dropdown to search within a specific project
4. **Build Context**: Click "Build Context" to generate optimized context for AI consumption

**What it shows:**
- **Search Results**: Matching file snippets with relevance scores (0-100%)
- **Metadata**: File path, line numbers, chunk type, embedding model
- **Context**: Structured code context optimized for LLM consumption
- **Statistics**: Total chunks, repositories indexed, embedding model info

### Planning & Task Decomposition
Describe what you want in natural language. ForgeAI:
- Classifies your intent (feature, bug fix, refactor, docs, testing, deploy)
- Decomposes into granular tasks with dependencies
- Scores complexity and analyzes risks (data loss, security, breaking changes)
- Generates a topological execution order

**How to use the Planner:**
1. Go to **Planner** page
2. Type a natural language request (e.g., "add user authentication", "fix login bug", "optimize database queries")
3. Click **Generate Plan**
4. Review the generated tasks with dependencies and risk analysis
5. Execute the plan or modify as needed

**What it shows:**
- **Task List**: Step-by-step implementation tasks
- **Dependencies**: Which tasks depend on others
- **Risk Analysis**: Potential issues and mitigation strategies
- **Complexity Score**: Estimated effort level
- **Execution Order**: Topological sort for parallel execution

### AI Chat Workspace
A full-featured AI chat interface connected to your local LLM (Ollama):
- Real-time streaming responses (token-by-token)
- Multi-turn conversation with history persistence
- Automatic context injection (repos, projects, agents, workflows)
- Model switching (any Ollama model you pull)
- Stop generation with partial response preservation

**How to use AI Chat:**
1. Go to **AI Workspace** page
2. Click **New Conversation** to start fresh
3. Select a project from the dropdown (or leave empty for all projects)
4. Type your question about the codebase
5. Get real-time streaming answers based on your actual code

**What it shows:**
- **Streaming Responses**: Token-by-token AI answers as they're generated
- **Code References**: Specific file paths and line numbers from your codebase
- **Context Awareness**: AI reads your actual source files (HTML, CSS, JS, Python, etc.)
- **Conversation History**: Multi-turn chat with context preservation
- **Model Selection**: Choose from any Ollama model you have installed

**Example questions:**
- "What is this project about?"
- "Explain the code structure"
- "Are there any security issues?"
- "What frameworks are used?"
- "Review the JavaScript code"
- "How does the authentication work?"

### Software Engineer Agent
Autonomous code implementation with a 9-step workflow:
1. Understand requirements
2. Analyze codebase
3. Collect context (memory + knowledge graph)
4. Review architecture
5. Plan implementation
6. Generate code (with templates for services, repos, schemas, routers)
7. Validate (syntax, types, tests)
8. Self-review
9. Prepare commit summary

**How to use the Software Engineer:**
1. Go to **Software Engineer** page
2. Select a project from the dropdown
3. Describe what you want to implement (e.g., "add user registration endpoint")
4. Click **Generate Code**
5. Review the generated code with explanations
6. Copy or apply the changes to your codebase

**What it shows:**
- **Generated Code**: Complete implementation with proper structure
- **File Changes**: Which files to create or modify
- **Explanation**: Why each change was made
- **Best Practices**: Code follows patterns detected in your codebase
- **Validation**: Syntax and type checking results

### Reflection & Self-Correction
The AI critiques its own work across 9 dimensions:
- Architecture, Security, Performance, Readability, Maintainability
- Scalability, Dependency Management, Testing, Documentation
- Generates alternative solutions with confidence scoring
- Iterates up to 5 passes for quality improvement

**How to use Reflection:**
1. Go to **Reflection** page
2. Select a project or paste code to review
3. Click **Analyze Code**
4. Review the self-critique across 9 dimensions
5. See alternative solutions with confidence scores
6. Iterate for quality improvement

**What it shows:**
- **Dimension Scores**: Ratings for Architecture, Security, Performance, etc.
- **Issues Found**: Specific problems with severity levels
- **Alternative Solutions**: Better approaches with explanations
- **Confidence Scores**: How confident the AI is in each suggestion
- **Iteration History**: Track improvements across multiple passes

### Review Pipeline
Automated code review covering:
- **Security**: Hardcoded secrets, SQL injection, XSS, eval usage, path traversal
- **Performance**: N+1 queries, blocking I/O, string concatenation
- **Architecture**: Single Responsibility Principle, Dependency Inversion, Repository Pattern
- **Quality Scoring**: Weighted across 6 dimensions with actionable feedback
- **QA Agent**: Generates unit, integration, and edge case tests
- **Documentation Agent**: Creates release notes, changelogs, API docs

**How to use Review Center:**
1. Go to **Review Center** page
2. Select a project or paste code to review
3. Click **Start Review**
4. Review security, performance, and architecture findings
5. See quality scores with actionable feedback
6. Generate tests and documentation automatically

**What it shows:**
- **Security Issues**: Hardcoded secrets, SQL injection, XSS vulnerabilities
- **Performance Problems**: N+1 queries, blocking I/O, inefficient algorithms
- **Architecture Violations**: SOLID principle violations, design pattern issues
- **Quality Scores**: Weighted scores across 6 dimensions
- **Test Suggestions**: Unit, integration, and edge case tests
- **Documentation**: Release notes, changelogs, API documentation

### Execution Engine
Controlled workflow execution with safety guarantees:
- Git branch creation before execution (isolated workspace)
- Checkpoint manager for rollback points
- Auto-rollback on failure
- Progress tracking with real-time status updates
- Validation engine for post-execution checks

**How to use Execution:**
1. Go to **Execution** page
2. View all running and completed executions
3. Monitor real-time progress with status updates
4. See execution timeline and step details
5. Rollback to previous checkpoints if needed

**What it shows:**
- **Execution Status**: Running, completed, failed, or rolled back
- **Step Progress**: Real-time updates for each workflow step
- **Timeline**: Visual timeline of execution flow
- **Checkpoints**: Rollback points created during execution
- **Validation Results**: Post-execution checks and verification

### Approval Gates
Human-in-the-loop safety controls:
- Risk levels: Low, Medium, High, Critical
- Configurable timeouts per operation type
- Full audit trail of all approvals/rejections
- Auto-approve mode for development environments

**How to use Approval Gates:**
1. Go to **Approval** page
2. View pending approvals for high-risk operations
3. Review the operation details and risk assessment
4. Approve or reject with comments
5. See audit trail of all decisions

**What it shows:**
- **Pending Approvals**: Operations waiting for human sign-off
- **Risk Assessment**: Risk level (Low/Medium/High/Critical) for each operation
- **Operation Details**: What the operation will do and its impact
- **Audit Trail**: Complete history of all approvals and rejections
- **Timeout Settings**: Configurable approval timeouts per operation type

### Workforce Management
5 pre-registered AI agents with specialized roles:

| Agent | Role | Capabilities |
|-------|------|-------------|
| Code Engineer | `software_engineer` | Coding (L9), Code Review (L8) |
| QA Engineer | `qa_engineer` | Testing (L9), Quality Assurance (L8) |
| Code Reviewer | `code_reviewer` | Code Review (L9), Security (L8) |
| DevOps Engineer | `devops_engineer` | Deployment (L9), Infrastructure (L8) |
| Technical Writer | `technical_writer` | Documentation (L9), API Docs (L8) |

**How to use AI Agents:**
1. Go to **Agents** page
2. Select an agent based on your task
3. Choose a project from the dropdown
4. Describe what you want the agent to do
5. Click **Assign Task**
6. View results in **Recent Tasks** below

**What each agent does:**
- **Code Engineer**: Implements features, fixes bugs, refactors code
- **QA Engineer**: Writes tests, identifies quality issues, suggests improvements
- **Code Reviewer**: Reviews code for security, performance, and best practices
- **DevOps Engineer**: Checks deployment readiness, generates Docker/CI configs
- **Technical Writer**: Creates documentation, READMEs, API docs

### Tool Virtualization Layer
All operations go through MCP (Model Context Protocol) adapters:
- **Filesystem**: Read/write/list/search/move/delete files
- **Git**: Status/branch/commit/diff/log/checkout
- **Terminal**: Execute/cancel/stream commands
- **Docker**: List/run/stop/exec/logs containers
- **Database**: Query/list/describe/DDL operations
- **Browser**: Fetch/search/content retrieval

**How to use Tools:**
1. Go to **Tools** page
2. View all available MCP tools and their status
3. See execution history for each tool
4. Monitor tool health and performance
5. Configure tool settings if needed

**What it shows:**
- **Tool Status**: Available, unavailable, or degraded tools
- **Execution History**: Recent operations with timing and results
- **Health Metrics**: Success rates, average response times
- **Configuration**: Tool-specific settings and credentials
- **Documentation**: Usage examples and API references

### Workflow Engine
- Create, approve, start, pause, resume, cancel workflows
- State machine enforcement (no invalid transitions)
- Dependency resolution and priority-based task queue
- Event system for tracking and monitoring

**How to use Workflows:**
1. Go to **Workflows** page
2. View auto-created pipelines (generated during import)
3. Click **Approve** to make workflow ready for execution
4. Click **Run Pipeline** to start execution
5. Watch the visual stepper animate through each step
6. View detailed results for each completed step

**What it shows:**
- **Workflow List**: All created workflows with status (Draft, Ready, Running, Completed)
- **Visual Stepper**: Animated progress through workflow steps
- **Step Details**: What each step does and its results
- **Execution Timeline**: When each step started and completed
- **Error Handling**: Failed steps with error messages and retry options

### Monitoring Dashboard
Real-time visibility into all operations:
- Agent status and performance metrics
- Workflow execution timeline
- Tool health and execution history
- Memory usage and search analytics
- System health checks

**How to use Monitoring:**
1. Go to **Monitoring** page
2. View system health status (Backend, Database, Ollama)
3. Check agent performance metrics
4. See workflow execution statistics
5. Monitor tool usage and health
6. Track memory usage and search analytics

**What it shows:**
- **System Health**: Backend, Database, Ollama, Redis status indicators
- **Agent Metrics**: Tasks completed, success rates, average response times
- **Workflow Stats**: Total workflows, success rates, average execution time
- **Tool Health**: Success rates, average response times per tool
- **Memory Analytics**: Total chunks, search queries, embedding model info
- **Activity Timeline**: Recent operations and events

### Documentation Management
ForgeAI can automatically generate and manage documentation for your projects:
- **README Generation**: Auto-generates comprehensive README files
- **API Documentation**: Creates API docs from code comments and structure
- **Architecture Docs**: Generates architecture documentation from code analysis
- **Changelog**: Auto-generates changelogs from git history
- **Release Notes**: Creates release notes for version updates

**How to use Documentation:**
1. Go to **Documentation** page
2. Select a project from the dropdown
3. Choose documentation type to generate
4. Click **Generate Documentation**
5. Review and edit the generated content
6. Export or save to your project

**What it shows:**
- **Generated Docs**: README, API docs, architecture docs, changelogs
- **Documentation Quality**: Completeness scores and suggestions
- **Code Coverage**: Which parts of codebase are documented
- **Missing Docs**: Areas that need documentation
- **Export Options**: Markdown, HTML, or PDF formats

### Validation Dashboard
Comprehensive system validation, benchmarks, quality gates, and security audits:
- **System Validation**: Checks all subsystems (API, Auth, Database, Cache, etc.)
- **Benchmarks**: Performance testing and response time analysis
- **Quality Gates**: Code quality checks with pass/fail status
- **Security Audit**: Vulnerability scanning and security analysis

**How to use Validation:**
1. Go to **Validation** page (`/validation`)
2. Click **Run Validation** to check all subsystems
3. View results in Overview tab (pass/fail counts)
4. Check System Validation for detailed subsystem status
5. Review Benchmarks for performance metrics
6. Analyze Quality Gates for code quality issues
7. Run Security Audit for vulnerability scanning

**What it shows:**
- **Overall Status**: Pass/Fail with counts
- **Subsystem Health**: API Gateway, Auth Service, Database, Cache, etc.
- **Performance Metrics**: Response times, throughput, latency
- **Quality Scores**: Code quality dimensions with actionable feedback
- **Security Findings**: Vulnerabilities, risks, and mitigation suggestions

### Learning Center
Engineering knowledge base that captures experiences, patterns, and lessons from completed workflows:
- **Experiences**: What worked and what didn't — categorized by type (architecture, bug fix, deployment, etc.) and outcome (success/failure/partial)
- **Patterns**: Reusable solutions extracted from successful experiences with confidence scores and usage counts
- **Lessons**: Mistakes and failures to avoid — root cause analysis and avoidance strategies
- **Recommendations**: AI-generated advice for future tasks based on accumulated knowledge
- **Learning Feed**: Real-time view in Experience Center showing recent learning activity

**How to use Learning Center:**
1. Go to **Learning** page (`/learning`)
2. Review the Overview tab for stats and knowledge growth
3. Click **Process Workflow** to submit a completed workflow
4. Fill in workflow details (ID, title, description, outcome, files changed, technologies)
5. View extracted experiences, patterns, and lessons across tabs
6. Provide feedback on experiences (Helpful/Excellent/Improve)

**What it shows:**
- **Overview**: Stats cards (total experiences, patterns, lessons, success rate, tasks processed), knowledge growth timeline, recent activity
- **Experiences**: Filterable list of captured engineering experiences with confidence and reuse scores
- **Patterns**: Searchable patterns with usage count, when to use / when not to use guidance
- **Lessons**: Captured failures with root cause, avoidance strategy, and encounter counts
- **Recommendations**: AI-generated suggestions for future similar tasks

### Studio (Advanced Tools)
Advanced development environment with a visual workflow builder and specialized tools:
- **Workflow Builder**: Visual node-based editor to create custom AI workflows with drag-and-drop
- **Prompts**: Create and test AI prompt templates
- **Replay**: Replay past workflow executions for debugging
- **Agents**: Test agent behaviors in isolation
- **Workspace**: Shared workspace for collaboration
- **Models**: Manage Ollama models (pull, switch, configure)
- **Memory**: Explore indexed code knowledge

**How to use Studio:**
1. Go to **Studio** page (`/studio`)
2. Select a tool from the sidebar (Workflows, Prompts, Replay, etc.)
3. **Workflow Builder**: Drag nodes from the palette, connect them, configure properties
4. **Prompts**: Write and test prompts for AI agents
5. **Replay**: Debug failed executions step-by-step
6. **Agents**: Experiment with agent behaviors
7. **Memory**: Browse indexed code chunks and relationships
8. **Models**: Pull, switch, and configure Ollama models

#### Workflow Builder — Node Types

| Node | Color | What It Does | When to Use |
|------|-------|-------------|-------------|
| **Start** | Green | Entry point — workflow begins here | Every workflow needs exactly 1 |
| **Planner** | Blue | AI analyzes request and breaks into subtasks with dependencies | Before coding — to plan what to build |
| **Supervisor** | Purple | Coordinates multiple agents, decides who does what | Complex tasks needing multiple agents |
| **Agent** | Purple | Runs a single specialized AI agent (coder, reviewer, tester) | Execute one focused task |
| **Decision** | Yellow | If/else branch — splits flow based on condition | "Is code good? → Yes: deploy, No: fix" |
| **Approval** | Orange | Pauses workflow, waits for human click | Before risky operations (deploy, delete) |
| **Reflection** | Pink | AI reviews its own work, suggests improvements | After coding — before finalizing |
| **Tool** | Blue | Runs an MCP tool (read file, git commit, terminal command) | Need to interact with filesystem/git/shell |
| **Memory** | Teal | Queries the semantic memory engine for context | Need code context before making decisions |
| **Execution** | Red | Runs code with git checkpoints + auto-rollback on failure | Actual code execution with safety |
| **End** | Gray | Outputs final result, terminates workflow | Every workflow needs exactly 1 |

#### Workflow Builder — Node Examples

**Start Node:**
- Entry point — every workflow begins here
- Example: "User uploads code" — this is where the workflow kicks off

**Planner Node:**
- AI breaks your request into subtasks
- Example: "Add user authentication" → outputs Task 1: Create user model, Task 2: Create login endpoint, Task 3: Add JWT middleware, Task 4: Write tests, Task 5: Update docs

**Supervisor Node:**
- Coordinates multiple agents working in parallel
- Example: "Refactor payment module" → assigns Code Engineer to rewrite logic, QA Engineer to write tests, Code Reviewer to review when both finish

**Agent Node:**
- Runs one specialized AI agent
- Example: Code Reviewer agent scans for security issues, performance problems, and code quality anti-patterns with file:line references

**Decision Node:**
- If/else branching based on condition
- Example: After Code Reviewer runs → "Any critical issues?" → YES: route to Fix Issues agent, NO: route to Deploy approval gate

**Approval Node:**
- Pause and wait for human click
- Example: Before deploying to production → shows "Deploy Traveloop to production?" with risk level HIGH → you click Approve/Reject

**Reflection Node:**
- AI reviews its own work
- Example: After code is written → analyzes Architecture ("Should use Repository pattern"), Security ("Password in plain text — use bcrypt"), Performance ("N+1 query on user.orders") → suggests 3 alternatives with confidence scores

**Tool Node:**
- Execute an MCP tool
- Example: Git Commit → runs `git add .`, `git commit -m "Add user auth"`, `git push origin main`

**Memory Node:**
- Query semantic memory for code context
- Example: Query "How does authentication work?" → finds auth/middleware.py, models/user.py, routes/login.py → returns structured context

**Execution Node:**
- Run code with safety checkpoints
- Example: Running database migration → creates git checkpoint → runs `python manage.py migrate` → if FAILURE → auto-rolls back to checkpoint

**End Node:**
- Output final result, terminate workflow
- Example: Collects all results → formats final report → "Workflow complete — 5 tasks, 3 files changed"

#### Full Workflow Example

```
Start ("User requests feature")
    ↓
Memory ("Find existing auth code")
    ↓
Planner ("Break into tasks")
    ↓
Agent ("Code Engineer implements")
    ↓
Reflection ("AI reviews its own work")
    ↓
Decision ("Any issues?")
    ├── YES → Agent ("Fix issues") → back to Reflection
    └── NO ↓
Approval ("Deploy?")
    ├── REJECT → End ("Aborted")
    └── APPROVE ↓
Execution ("Run deployment")
    ↓
End ("Done — 5 files changed, deployed")
```

#### Top Toolbar

| Button | What It Does |
|--------|-------------|
| **+ Add Node** | Adds a new node to the canvas |
| **Validate** | Checks for broken connections, missing Start/End nodes |
| **Save** | Saves the workflow configuration |
| **🔍+ / 🔍-** | Zoom in/out on canvas |
| **100%** | Reset zoom to default |
| **⛶** | Toggle fullscreen |

#### Properties Panel (right side — when you click a node)

| Option | What It Does |
|--------|-------------|
| **Type** | Shows the node type (Start, Agent, Decision, etc.) — read-only |
| **Label** | Custom name for the node (e.g., "Plan Task", "Review Code") |
| **Status** | Current state — Idle → Running → Completed/Failed/Waiting |
| **Description** | What this node does — helps you remember the purpose |
| **Node ID** | Auto-generated unique identifier |
| **Position** | X, Y coordinates on canvas |
| **Delete Node** | Removes the node from the workflow |

---

## Tech Stack

### Backend

| Technology | Purpose |
|-----------|---------|
| Python 3.12 | Runtime |
| FastAPI | Web framework |
| Pydantic v2 | Data validation |
| Ollama | Local LLM inference |
| ChromaDB | Vector database |
| tree-sitter | AST parsing |
| httpx | Async HTTP client |

### Frontend

| Technology | Purpose |
|-----------|---------|
| Next.js 15 | Framework |
| React 19 | UI library |
| TypeScript | Language |
| Tailwind CSS 4 | Styling |
| Zustand | State management |
| TanStack Query | Data fetching |
| Framer Motion | Animations |
| Lucide React | Icons |

### AI / ML

| Technology | Purpose |
|-----------|---------|
| Ollama | Local LLM inference (qwen2.5, llama3, etc.) |
| BAAI/bge-small-en-v1.5 | Text embeddings (512 dimensions) |
| ChromaDB | Vector storage and retrieval |
| BM25 | Sparse keyword search |
| MCP | Model Context Protocol for tool access |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| Docker | Containerization |
| Docker Compose | Orchestration |
| PostgreSQL 16 | Primary database |
| Redis | Caching |
| GitHub Actions | CI/CD |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Ollama (for local AI chat)

### Step 1: Start the Backend

```bash
cd forge-ai/backend
python -m uvicorn app.server:app --reload --port 8000
```

Wait until you see: `Uvicorn running on http://127.0.0.1:8000`

### Step 2: Start the Frontend

Open a **new terminal**:

```bash
cd forge-ai/frontend
npm install
npm run dev
```

Wait until you see: `Ready in http://localhost:3000`

### Step 3: Start Ollama (for AI Chat)

Open another terminal:

```bash
ollama serve
```

Make sure you have a model pulled:

```bash
ollama pull qwen2.5
```

### Step 4: Open the App

Go to **http://localhost:3000** in your browser.

---

## Manual Testing Guide

As a new user, follow this step-by-step workflow to test all features:

### Step 1: Import a Repository

1. Click **Repositories** in the sidebar
2. Click **Import Repository**
3. Choose **Folder** upload (or Git/ZIP)
4. Select any code project folder on your computer
5. Wait for it to upload and analyze
6. You'll see the repo appear with file count, languages detected, line counts

**What it does:** Scans your code, detects languages (JS, CSS, HTML, Python, etc.), counts files and lines, detects frameworks.

### Step 2: AI Workspace (Chat)

1. Click **AI Workspace** in the sidebar
2. Start a **New Conversation**
3. Ask questions like:
   - "What is this project about?"
   - "Explain the code structure"
   - "Are there any security issues?"
   - "What frameworks are used?"
   - "Review the JavaScript code"

**What it does:** The AI reads your actual source files and answers based on your real code. It sees HTML, CSS, JS, Python files and can explain what they do.

### Step 3: Run a Workflow

1. Go to **Workflows**
2. You'll see the auto-created pipeline (created during import)
3. Click **Approve** → status changes to "Ready"
4. Click **Run Pipeline** → watch the visual stepper animate
5. Each step does real analysis:
   - Analyze codebase structure (file counts, sizes)
   - Review code quality (bugs, bad practices)
   - Check dependencies
   - Run test suite (checks for test frameworks)
   - Generate analysis report (compiles all findings)

**What it does:** Runs a 5-step automated pipeline that scans your entire codebase and produces detailed reports at each step.

### Step 4: Use AI Agents

1. Go to **Agents**
2. Click **Run** on any agent:
   - **Code Reviewer** — Scans for security vulnerabilities, bad practices
   - **Software Engineer** — Suggests code improvements
   - **DevOps Engineer** — Checks deployment readiness, generates Dockerfile
   - **Task Planner** — Creates prioritized task list
   - **Researcher** — Analyzes codebase structure
3. Select your project, describe what you want
4. Click **Assign Task**
5. Results appear in **Recent Tasks** below

**What it does:** Each agent does specialized analysis. The Code Reviewer finds `console.log()`, `eval()`, hardcoded secrets, XSS vulnerabilities with exact file:line references.

### Step 5: Project Details

1. Go to **Projects**
2. Click on a project card to see details
3. See files, lines of code, languages, frameworks
4. Quick actions: View Repository, AI Agents, Workflows, Monitoring

### Step 6: Monitoring Dashboard

1. Go to **Monitoring**
2. View system health (backend, database, Ollama status)
3. Check agent and workflow metrics
4. See execution overview and activity timeline

---

## How It Works (Workflow)

```
Import Code → AI Analyzes → Run Agents → Get Results → Take Action
```

### The Complete Flow

```
1. IMPORT          2. ANALYZE           3. ACT             4. REVIEW
┌──────────┐      ┌──────────┐        ┌──────────┐       ┌──────────┐
│ Upload   │─────→│ Detect   │─────→  │ Run      │─────→ │ See      │
│ your code│      │ languages│        │ agents & │       │ results  │
│ (folder/ │      │ frameworks│       │ workflows│       │ & issues │
│  git/zip)│      │ scan code│        │ on code  │       │          │
└──────────┘      └──────────┘        └──────────┘       └──────────┘
     │                 │                    │                   │
     ▼                 ▼                    ▼                   ▼
  Repository       AI knows             Real code           Actionable
  stored with      your project         analysis            feedback
  file tree        structure            with findings       with file:line
```

### What Each Component Does

| Step | Component | What Happens |
|------|-----------|-------------|
| Import | Repository Import | Upload code → scan files → detect languages/frameworks → count lines |
| Chat | AI Workspace | Ask questions → AI reads your actual source files → answers with specifics |
| Workflows | Pipeline Execution | 5-step automated scan → each step analyzes different aspect → detailed reports |
| Agents | Specialized Analysis | Code review, DevOps, planning → each agent does focused deep-dive |
| Monitor | Dashboard | See health, metrics, activity → track everything in one place |

---

## Use Cases

### 1. New Developer Onboarding
**Problem:** Joining a new codebase is overwhelming.
**Solution:** Import the repo → ask AI "explain this project" → get instant understanding of architecture, key files, and dependencies.

### 2. Code Review Before Merge
**Problem:** Manual code review is slow and misses issues.
**Solution:** Run Code Reviewer agent → get automated scan for security vulnerabilities, bad practices, and quality issues with exact file:line references.

### 3. Security Audit
**Problem:** Security vulnerabilities hide in code.
**Solution:** Run workflow with security analysis steps → get report of hardcoded secrets, XSS vectors, eval usage, and other security risks.

### 4. Deployment Readiness Check
**Problem:** Don't know if your code is production-ready.
**Solution:** Run DevOps Engineer agent → checks for Dockerfile, CI/CD configs, environment variables → generates deployment config if missing.

### 5. Code Quality Assessment
**Problem:** Technical debt accumulates silently.
**Solution:** Run workflow → reviews code quality across entire codebase → identifies console.logs, var usage, loose equality, and other anti-patterns.

### 6. Project Documentation
**Problem:** No documentation exists.
**Solution:** AI Workspace reads your code and generates explanations → ask it to write README content, API docs, or architecture summaries.

### 7. Dependency Management
**Problem:** Outdated or vulnerable dependencies.
**Solution:** Workflow checks dependency files → reports what's found and what's missing → suggests improvements.

### 8. Codebase Analysis for Business
**Problem:** Stakeholders ask "what do we have?"
**Solution:** Import repo → workflow generates complete analysis report → share file counts, languages, issues found, and recommendations.

---

## What Each Page Does

| Page | URL | What It Does |
|------|-----|-------------|
| **Dashboard** | `/dashboard` | Overview — agents, workflows, activity at a glance |
| **Projects** | `/projects` | Manage projects linked to repositories |
| **Repositories** | `/repositories` | Import codebases (folder, git, zip) — the starting point |
| **AI Workspace** | `/ai` | Chat with AI about your actual code — reads real files |
| **Workflows** | `/workflows` | Automated analysis pipelines with visual stepper |
| **Agents** | `/agents` | Run specialized AI agents (reviewer, devops, etc.) |
| **Monitoring** | `/monitoring` | Health checks, system status, execution metrics |
| **Memory** | `/memory` | AI's knowledge base about your projects — search and index code |
| **Planner** | `/planner` | AI-powered task planning from natural language |
| **Software Engineer** | `/software-engineer` | Code generation and refactoring |
| **Review Center** | `/review` | Manual code review interface |
| **Reflection** | `/reflection` | AI self-critique and improvement |
| **Execution** | `/execution` | Workflow execution monitoring and rollback |
| **Approval** | `/approval` | Human-in-the-loop safety controls |
| **Tools** | `/tools` | MCP tool management and execution history |
| **Documentation** | `/documentation` | Auto-generate README, API docs, changelogs |
| **Deployment** | `/deployment` | Docker/CI/CD config generation |
| **Learning** | `/learning` | Engineering knowledge base — experiences, patterns, lessons from processed workflows |
| **Experience Center** | `/experience` | Activity feed, learning feed, notifications, and settings |
| **Validation** | `/validation` | System validation, benchmarks, quality gates, security audit |
| **Studio** | `/studio` | Advanced workflow builder, prompt studio, agent playground |
| **Settings** | `/settings` | Platform configuration |
| **Execution** | `/execution` | Workflow execution monitoring |
| **Deployment** | `/deployment` | Docker/CI/CD config generation |
| **Settings** | `/settings` | Platform configuration |

---

### Quick 5-Minute Test

```
1. Open http://localhost:3000
2. Go to Repositories → Import → Folder → pick any code folder
3. Wait for import to finish
4. Go to AI Workspace → New Conversation → ask "what files are in my project?"
5. Go to Workflows → approve the pipeline → run it → watch the stepper
6. Go to Agents → run Code Reviewer on your project → check results
7. Go to Memory → click "Index Repository" → search for code snippets
8. Go to Learning → click "Process Workflow" → submit workflow data → view extracted experiences
9. Go to Experience Center → click Learning Feed tab → see recent learning activity
10. Go to Monitoring → see the dashboard update with real data
```

---

## How This Project Works — Complete New User Guide

### What is ForgeAI?

ForgeAI is an **AI-powered software engineering platform** with 17+ features that help you plan, code, review, deploy, and learn from software projects — all powered by AI agents.

**Think of it as hiring an AI engineering team** that lives in your browser.

---

### Step 1: Start the Servers

```bash
# Terminal 1 — Backend
cd forge-ai/backend
python run_server.py

# Terminal 2 — Frontend
cd forge-ai/frontend
npm run dev
```

Open **http://localhost:3000** in your browser.

---

### Step 2: Import Your First Repository (MOST IMPORTANT)

This is the **first thing you should do** — it unlocks most features.

1. Click **Repositories** in the sidebar
2. Click **Import Repository**
3. Choose import method:
   - **Folder** — select a local project folder (easiest)
   - **Git URL** — paste a GitHub repo URL
   - **ZIP** — upload a .zip file
4. Enter a name (e.g., "My Project")
5. Click **Import**

**What happens automatically:**
- Repository is analyzed (files, lines, languages, frameworks)
- A **Project** is created
- A **Workflow** is auto-created with analysis steps
- **Documentation** is auto-generated
- The repo is indexed for **Memory** search

---

### Step 3: Explore All Features

#### Feature Map — What Does What

| # | Feature | What It Does | When to Use |
|---|---------|-------------|-------------|
| 1 | **Dashboard** | Overview of everything | First thing you see |
| 2 | **AI Workspace** | Chat with AI about your code | Ask questions about code |
| 3 | **Projects** | Organize your work | Create/manage projects |
| 4 | **Repositories** | Import & analyze codebases | **Start here** |
| 5 | **Documentation** | Auto-generated docs | After importing a repo |
| 6 | **Memory** | Semantic code search | Find patterns in code |
| 7 | **Planner** | AI execution plans | Before starting work |
| 8 | **Workflows** | Multi-step automation pipelines | Run analysis pipelines |
| 9 | **Agents** | Assign tasks to AI workers | Get AI to do specific tasks |
| 10 | **Workforce** | Monitor AI agents | See agent status |
| 11 | **Tools** | Execute filesystem/git/terminal | Run system operations |
| 12 | **Software Engineer** | Autonomous code generation | Generate/fix/refactor code |
| 13 | **Deployment** | Docker/K8s/CI/CD configs | Before deploying |
| 14 | **Learning Center** | Engineering knowledge base | Learn from past work |
| 15 | **Monitoring** | System health dashboard | Monitor everything |
| 16 | **Studio** | Visual workflow builder | Build custom workflows |
| 17 | **Validation** | Release candidate checks | Before shipping |

---

### Detailed Feature Guide

#### 1. Dashboard (`/dashboard`)
**What:** Home page with stats and quick actions.

**How to use:**
1. Open the app — you land here
2. See total projects, active models, running agents, completed tasks
3. Click **Quick Actions** to jump to key features
4. View **Recent Activity** feed

---

#### 2. AI Workspace (`/ai`)
**What:** Chat with AI about your codebase.

**How to use:**
1. Click **AI Workspace** in sidebar
2. Select a model from the dropdown (e.g., `qwen2.5`)
3. Type a question: "Explain the authentication flow"
4. AI responds with context from your imported repos
5. Create multiple conversations to organize topics

**Example questions:**
- "What is this project about?"
- "Explain the code structure"
- "Are there any security issues?"
- "What frameworks are used?"
- "How does the authentication work?"

---

#### 3. Projects (`/projects`)
**What:** Organize your work into projects.

**How to use:**
1. Click **Projects** → **New Project**
2. Enter name and description
3. Click to see project detail with stats
4. From detail, navigate to repo, agents, workflows

---

#### 4. Repositories (`/repositories`)
**What:** Import and analyze codebases.

**How to use:**
1. Click **Import Repository**
2. Choose method (Folder/Git/ZIP)
3. Provide source
4. System imports and analyzes automatically
5. Click repo name to see detailed analysis
6. Click **Run Analysis** for deep security/quality scan
7. Filter findings by severity (CRITICAL/HIGH/MEDIUM/LOW)

---

#### 5. Documentation (`/documentation`)
**What:** AI-generated documentation for your repos.

**How to use:**
1. Click **Documentation**
2. Select a repository from dropdown
3. Click **Generate Documentation**
4. Browse docs by category (Getting Started, API Reference, Architecture, Deployment)
5. Click a doc to read it

---

#### 6. Memory (`/memory`)
**What:** Semantic search across your codebase.

**How to use:**
1. Click **Memory**
2. Type a natural language query: "authentication middleware"
3. Filter by repository, chunk type, language
4. View ranked results on left
5. Click **Build Context** to generate AI-ready context

---

#### 7. Planner (`/planner`)
**What:** AI generates execution plans.

**How to use:**
1. Click **Planner**
2. Describe your objective: "Add user authentication with JWT"
3. Optionally select a repository for context
4. Click **Generate Plan**
5. Review tasks, risks, complexity
6. Approve or request changes

---

#### 8. Workflows (`/workflows`)
**What:** Multi-step automation pipelines.

**How to use:**
1. Click **Workflows**
2. Click **New Pipeline**
3. Add steps (title + description for each)
4. Click **Approve** (draft → ready)
5. Click **Run**
6. Watch real-time progress
7. After completion, review analysis summary
8. Click **Ask AI** to explore results
9. Export the report

---

#### 9. Agents (`/agents`)
**What:** Assign tasks to specialized AI workers.

**Available agents:**
| Agent | Does What |
|-------|-----------|
| **Reviewer** | Reviews code for bugs, security issues |
| **Executor** | Writes new code, fixes bugs |
| **DevOps** | Analyzes deployment readiness |
| **Planner** | Breaks tasks into steps |
| **Researcher** | Gathers context about code |

**How to use:**
1. Click **Agents**
2. Click **Run** on an agent
3. Select a target project
4. Type a task: "Review the authentication module"
5. Click **Assign Task**
6. Monitor in **Recent Tasks**

---

#### 10. Workforce (`/workforce`)
**What:** Monitor all AI agents.

**How to use:**
1. Click **Workforce**
2. See agent summary (total, idle, busy, unavailable)
3. Browse agents by role
4. Check agent status and capabilities

---

#### 11. Tools (`/tools`)
**What:** Execute filesystem, git, and terminal operations.

**How to use:**
1. Click **Tools**
2. Browse available tools (Filesystem, Git, Terminal)
3. Click **Execute** tab
4. Select a tool
5. Enter operation and JSON parameters
6. Click **Execute**
7. View result

---

#### 12. Software Engineer (`/software-engineer`)
**What:** Autonomous code generation.

**How to use:**
1. Click **Software Engineer**
2. Select a project
3. Choose task type: Feature, Bug Fix, API, Migration, Frontend, Backend, Documentation, Guidance
4. Describe what you want: "Add JWT authentication with login/register endpoints"
5. Click **Execute Task**
6. Watch progress: analyzing → planning → generating → reviewing → validating
7. Review generated code, diffs, review score
8. Check **Guidance** tab for suggestions
9. Click **Approve** or **Reject**

---

#### 13. Deployment Center (`/deployment`)
**What:** Generate Docker, CI/CD, and Kubernetes configs.

**How to use:**
1. Click **Deployment Center**
2. Select a repository
3. Click **Analyze**
4. Review Overview (production score, infrastructure)
5. Browse **Docker** tab for Dockerfile + Compose
6. Browse **CI/CD** tab for GitHub Actions
7. Browse **Kubernetes** tab for K8s manifests
8. Check **Security** tab for vulnerabilities
9. View **Report** tab for full deployment plan
10. Copy/download any generated config

---

#### 14. Learning Center (`/learning`)
**What:** Engineering knowledge base from past work.

**How to use:**
1. Click **Learning Center**
2. Click **Process Workflow**
3. Select a project
4. Describe what was accomplished
5. Set outcome (Success/Failure/Partial)
6. Add files changed and technologies
7. Click **Process**
8. Browse Overview for stats
9. Check Experiences tab for recorded experiences
10. Check Patterns tab for detected patterns
11. Check Lessons tab for failure lessons
12. Check Recommendations tab for future guidance
13. Submit feedback on experiences

---

#### 15. Monitoring (`/monitoring`)
**What:** Real-time system health dashboard.

**How to use:**
1. Click **Monitoring**
2. View Overview (system stats)
3. Click **Workflows** tab for pipeline status
4. Click **Agents** tab for agent performance
5. Click **Tools** tab for tool metrics
6. Click **Memory** tab for search stats
7. Click **Analytics** tab for trends
8. Click **Health** tab for component health
9. Click **Timeline** tab for event log

---

#### 16. Studio (`/studio`)
**What:** Visual workflow builder and prompt management.

**Sub-sections:**
- **Workflow Builder** — Drag-and-drop workflow creation
- **Prompt Studio** — Create, version, test prompts
- **Execution Replay** — Replay past executions
- **Agent Playground** — Configure and test agents
- **Model Manager** — Manage AI models

**How to use:**
1. Click **Studio**
2. Use sidebar to switch sections
3. Build workflows visually
4. Manage prompts with version history
5. Replay executions step-by-step

---

#### 17. Validation (`/validation`)
**What:** Release candidate validation.

**How to use:**
1. Click **Validation**
2. View Overview (pass/fail summary)
3. Check **System Validation** for subsystem status
4. Check **Benchmarks** for performance
5. Check **Quality Gates** for thresholds
6. Check **Security Audit** for vulnerabilities

---

#### 18. Settings (`/settings`)
**What:** Application configuration.

**How to use:**
1. Click **Settings** (bottom of sidebar)
2. **General** — App name, API URL
3. **Appearance** — Theme (dark/light)
4. **Notifications** — Email settings, SMTP test
5. **API Keys** — Manage keys

---

### Recommended Workflow for New Users

1. **Import a repository** (Repositories → Import)
2. **Run analysis** (click the repo → Run Analysis)
3. **View documentation** (Documentation → select repo → Generate)
4. **Search code** (Memory → type query)
5. **Ask AI questions** (AI Workspace → ask about code)
6. **Generate deployment configs** (Deployment → select repo → Analyze)
7. **Process workflows** (Learning Center → Process Workflow)
8. **Monitor everything** (Monitoring → check health)

---

### Key Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + /` | Search |
| `Ctrl + K` | Command Palette |

---

### Backend Requirements

- **Ollama** (optional) — Powers AI features. Install from [ollama.ai](https://ollama.ai), run `ollama serve`, then `ollama pull qwen2.5`
- **SQLite** — Used for Learning Center persistence (auto-created)
- Without Ollama, AI features fall back to rule-based analysis

---

## Detailed Feature Guide

### Semantic Memory — Step-by-Step

**First Time Setup:**
1. Go to **Memory** page (`/memory`)
2. Click **Index Repository** button (top-right)
3. Select a project to index
4. Wait for indexing to complete (shows progress)

**Searching Code:**
1. Type a search query (e.g., "login", "API endpoint", "database connection")
2. Use the **project selector dropdown** to filter by specific project
3. Click **Search** or press Enter
4. View results with relevance scores
5. Click on a result to expand and see full content

**Building Context for AI:**
1. Enter a search query
2. Click **Build Context** button
3. View the compiled context optimized for AI consumption
4. Use this context in AI Workspace or other features

**What Results Show:**
- **Rank**: Relevance order (1 = most relevant)
- **Score**: Match quality (0-100%)
- **Content**: Matching file snippet (first 500 characters)
- **Metadata**: File path, line numbers, chunk type
- **Explanation**: Why this result matched your query

### AI Workspace — Step-by-Step

**Starting a Conversation:**
1. Go to **AI Workspace** page (`/ai`)
2. Click **New Conversation** button
3. Select a project from the dropdown (optional)
4. Type your question about the codebase
5. Press Enter or click Send

**Example Questions:**
- "What is this project about?"
- "Explain the code structure"
- "Are there any security issues?"
- "What frameworks are used?"
- "Review the JavaScript code"
- "How does the authentication work?"
- "What are the main API endpoints?"

**What AI Reads:**
- HTML, CSS, JavaScript, TypeScript files
- Python, Java, Go, Rust files
- Configuration files (package.json, requirements.txt)
- Documentation files (README, docs)

### Planner — Step-by-Step

**Creating a Plan:**
1. Go to **Planner** page (`/planner`)
2. Type a natural language request
3. Click **Generate Plan**
4. Review the generated tasks
5. Modify tasks if needed
6. Execute the plan

**Example Requests:**
- "Add user authentication with JWT"
- "Fix the login bug"
- "Optimize database queries"
- "Refactor the payment module"
- "Add unit tests for the API"

**What Plan Shows:**
- **Task List**: Step-by-step implementation tasks
- **Dependencies**: Which tasks depend on others
- **Risk Analysis**: Potential issues and mitigation strategies
- **Complexity Score**: Estimated effort level
- **Execution Order**: Topological sort for parallel execution

### Workflows — Step-by-Step

**Running a Workflow:**
1. Go to **Workflows** page (`/workflows`)
2. View auto-created pipelines (generated during import)
3. Click **Approve** to make workflow ready
4. Click **Run Pipeline** to start execution
5. Watch the visual stepper animate
6. View detailed results for each step

**What Each Step Does:**
- **Analyze Codebase**: Scans file structure, counts lines, detects patterns
- **Review Code Quality**: Checks for bugs, bad practices, anti-patterns
- **Check Dependencies**: Analyzes project dependencies and versions
- **Run Test Suite**: Checks for test frameworks and test coverage
- **Generate Report**: Compiles all findings into a comprehensive report

### Agents — Step-by-Step

**Running an Agent:**
1. Go to **Agents** page (`/agents`)
2. Select an agent based on your task
3. Choose a project from the dropdown
4. Describe what you want the agent to do
5. Click **Assign Task**
6. View results in **Recent Tasks** below

**Agent Tasks:**
- **Code Engineer**: Implement features, fix bugs, refactor code
- **QA Engineer**: Write tests, identify quality issues
- **Code Reviewer**: Review code for security, performance
- **DevOps Engineer**: Check deployment readiness, generate configs
- **Technical Writer**: Create documentation, READMEs, API docs

### Monitoring — Step-by-Step

**Viewing Dashboard:**
1. Go to **Monitoring** page (`/monitoring`)
2. View system health status indicators
3. Check agent performance metrics
4. See workflow execution statistics
5. Monitor tool usage and health
6. Track memory usage and search analytics

**Health Indicators:**
- **Backend**: Green = running, Red = stopped
- **Database**: Green = connected, Red = disconnected
- **Ollama**: Green = available, Red = unavailable
- **Redis**: Green = connected, Red = disconnected

### Validation — Step-by-Step

**Running Validation:**
1. Go to **Validation** page (`/validation`)
2. Click **Run Validation** button
3. Wait for all subsystem checks to complete
4. Review the Overview tab for pass/fail summary
5. Check each tab for detailed results

**Tabs:**
- **Overview**: Overall status with pass/fail/skip counts
- **System Validation**: Individual subsystem health checks
- **Benchmarks**: Performance metrics and response times
- **Quality Gates**: Code quality checks and scores
- **Security Audit**: Vulnerability scanning and security analysis

### Studio — Step-by-Step

**Using Studio Tools:**
1. Go to **Studio** page (`/studio`)
2. Select a tool from the sidebar:
   - **Workflow Builder**: Create custom workflows visually
   - **Prompt Studio**: Write and test AI prompts
   - **Execution Replay**: Debug failed executions
   - **Agent Playground**: Experiment with agent behaviors
   - **Memory Explorer**: Browse indexed code knowledge
   - **Model Manager**: Manage Ollama models

**Workflow Builder:**
1. Drag and drop workflow steps
2. Connect steps with dependencies
3. Configure step parameters
4. Save and execute the workflow

**Prompt Studio:**
1. Write a prompt template
2. Test with sample inputs
3. Evaluate AI responses
4. Refine and save prompts

---

## Project Structure

```
forge-ai/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── server.py          # Main server entry point
│   │   ├── core/              # Dependencies, config
│   │   ├── api/v1/            # API routers
│   │   │   ├── ai_standalone.py           # AI chat + Ollama
│   │   │   ├── repositories_standalone.py  # Repo import + analysis
│   │   │   ├── memory_standalone.py        # Semantic memory
│   │   │   ├── planner_standalone.py       # Task planning
│   │   │   ├── software_engineer_standalone.py  # Code generation
│   │   │   ├── workforce_standalone.py     # AI agent team
│   │   │   ├── workflows_standalone.py     # Workflow engine
│   │   │   ├── review_standalone.py        # Code review
│   │   │   ├── reflection_standalone.py    # Self-correction
│   │   │   ├── execution_standalone.py     # Execution engine
│   │   │   ├── approval_standalone.py      # Approval gates
│   │   │   ├── tools_standalone.py         # Tool virtualization
│   │   │   ├── documentation_standalone.py # Doc management
│   │   │   └── activity_store.py           # Shared activity store
│   │   └── tools/             # MCP tool implementations
│   │       ├── mcp.py         # MCP server + adapter
│   │       ├── filesystem.py  # File operations
│   │       ├── git.py         # Version control
│   │       ├── terminal.py    # Command execution
│   │       ├── docker.py      # Container management
│   │       ├── database.py    # Database operations
│   │       └── browser.py     # Web operations
│   └── docs/                  # 32 markdown documentation files
├── frontend/                   # Next.js 15 frontend
│   ├── app/(dashboard)/        # Dashboard pages
│   │   ├── ai/                # AI Chat Workspace
│   │   ├── repositories/      # Repository management
│   │   ├── memory/            # Semantic memory
│   │   ├── planner/           # Task planning
│   │   ├── learning/          # Learning Center — experiences, patterns, lessons
│   │   ├── experience/        # Experience Center — activity feed, learning feed, settings
│   │   ├── software-engineer/ # Code generation
│   │   ├── workforce/         # Agent management
│   │   ├── workflows/         # Workflow management
│   │   ├── review/            # Code review
│   │   ├── reflection/        # Self-correction
│   │   ├── execution/         # Execution monitoring
│   │   ├── approval/          # Approval gates
│   │   ├── tools/             # Tool management
│   │   ├── documentation/     # Documentation browser
│   │   ├── monitoring/        # System monitoring
│   │   └── settings/          # Platform settings
│   ├── components/            # Reusable UI components
│   ├── services/              # API service layer
│   ├── stores/                # Zustand state stores
│   └── types/                 # TypeScript type definitions
├── docker/                    # Docker configuration
│   ├── docker-compose.yml     # Production stack
│   ├── Dockerfile.backend     # Backend container
│   └── Dockerfile.frontend    # Frontend container
├── scripts/                   # Setup and utility scripts
├── tests/                     # Test suite
└── docs/                      # 32 architecture & API docs
```

---

## API Reference

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/api/v1/ai/chat/stream` | POST | Streaming AI chat |
| `/api/v1/repositories/import` | POST | Import a repository |
| `/api/v1/memory/search` | POST | Semantic code search |
| `/api/v1/planner/plan` | POST | Create execution plan |
| `/api/v1/agents/software-engineer/execute` | POST | Run code generation |
| `/api/v1/workforce` | GET | List AI agents |
| `/api/v1/workflows` | GET | List workflows |
| `/api/v1/review/start` | POST | Start code review |
| `/api/v1/execution/list` | GET | List executions |
| `/api/v1/approval/pending/{id}` | GET | Get pending approvals |

---

## MCP (Model Context Protocol)

ForgeAI uses MCP as the tool abstraction layer. All file, git, database, Docker, and browser operations go through MCP adapters.

### MCP Architecture

```
AI Agent → MCP Adapter → MCP Server → Tool Implementation
                                    → Filesystem / Git / Terminal / Docker / DB / Browser
```

### MCP Tools

| Tool | Provider | Operations |
|------|----------|------------|
| Filesystem | MCP | read, write, list, search, move, delete |
| Git | MCP | status, branch, commit, diff, log, checkout |
| Terminal | MCP | execute, cancel, stream |
| Docker | MCP | list, run, stop, exec, logs |
| Database | MCP | query, list, describe, ddl |
| Browser | MCP | fetch, search, content |

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/forgeai

# Security
JWT_SECRET_KEY=your-secret-key

# AI Configuration
OLLAMA_BASE_URL=http://localhost:11434
AI_DEFAULT_MODEL=qwen2.5
AI_MAX_CONTEXT_LENGTH=4096
AI_TEMPERATURE=0.7

# Memory
MEMORY_CHROMA_HOST=localhost
MEMORY_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
MEMORY_SEARCH_TOP_K=20

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Docker Deployment

### Production

```bash
docker compose -f docker/docker-compose.yml up -d
```

| Service | Port | Purpose |
|---------|------|---------|
| `backend` | 8000 | FastAPI server |
| `frontend` | 3000 | Next.js app |
| `ollama` | 11434 | Local LLM inference (GPU-accelerated) |
| `chromadb` | 8000 | Vector database |
| `postgres` | 5432 | Primary database |

### Development

```bash
docker compose -f docker/docker-compose.dev.yml up
```

---

## Development

### Backend

```bash
cd backend
python -m uvicorn app.server:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

### Tests

```bash
# Backend
pytest tests/ -v

# Frontend
npm test
```

### Linting

```bash
# Backend
ruff check app/
ruff format app/

# Frontend
npm run lint
npm run type-check
```

---

## Roadmap

- [ ] WebSocket real-time updates
- [ ] Kubernetes deployment manifests
- [ ] Multi-tenant support
- [ ] AI model registry
- [ ] GraphQL API support
- [ ] VS Code extension
- [ ] GitHub/GitLab integration
- [ ] Automated test generation
- [ ] Performance profiling agent
- [ ] Cost tracking per operation

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/Architecture.md) | System design and decisions |
| [AI Architecture](docs/AI-Architecture.md) | LLM integration details |
| [Repository Intelligence](docs/Repository-Intelligence.md) | Codebase analysis |
| [Memory Architecture](docs/Memory-Architecture.md) | Semantic memory system |
| [Planning Architecture](docs/Planning-Architecture.md) | Task decomposition |
| [Software Engineer Agent](docs/Software-Engineer-Agent.md) | Code generation |
| [Reflection Engine](docs/Reflection-Engine.md) | Self-correction |
| [Review Pipeline](docs/Review-Pipeline.md) | Code review |
| [Execution Engine](docs/Execution-Engine.md) | Workflow execution |
| [Approval Gates](docs/Approval-Gates.md) | Human-in-the-loop |
| [Tool Virtualization](docs/Tool-Virtualization.md) | MCP tool layer |
| [Workforce Architecture](docs/Workforce-Architecture.md) | Agent management |
| [Workflows Architecture](docs/Workflows-Architecture.md) | Workflow engine |
| [Getting Started](docs/GettingStarted.md) | Setup guide |
| [Developer Guide](docs/DeveloperGuide.md) | Extension guide |
| [Deployment](docs/DEPLOYMENT.md) | Production deployment |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Run linting (`ruff check app/ && npm run lint`)
6. Submit a pull request

See [Contributing Guide](docs/Contributing.md) for details.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with care by the ForgeAI team
</p>
