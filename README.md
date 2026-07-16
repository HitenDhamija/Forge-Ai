<div align="center">

```
  ███████╗ ██████╗  █████╗ ██████╗ ███████╗██████╗ 
  ██╔════╝██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
  █████╗  ██║   ██║███████║██║  ██║█████╗  ██████╔╝
  ██╔══╝  ██║   ██║██╔══██║██║  ██║██╔══╝  ╔════██╗
  ██║     ╚██████╔╝██║  ██║██████╔╝███████╗██║  ██║
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝
```

# ForgeAI — Autonomous AI Operations Platform

**An AI-powered software engineering team that lives in your browser.**

[![CI](https://github.com/HitenDhamija/Forge-Ai/actions/workflows/ci.yml/badge.svg)](https://github.com/HitenDhamija/Forge-Ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/HitenDhamija/Forge-Ai)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple.svg)](https://modelcontextprotocol.io/)

</div>

---

## What is ForgeAI?

ForgeAI is an **autonomous AI operations platform** that orchestrates a team of specialized AI agents to understand codebases, plan implementations, write code, review it, run tests, write documentation, and deploy changes — all under human supervision with approval gates.

**Think of it as hiring an AI engineering team**: a Software Engineer, QA Engineer, Code Reviewer, DevOps Engineer, and Technical Writer — working together on your codebase, with you as the engineering manager.

---

## Why ForgeAI Exists

| Problem | How ForgeAI Solves It |
|---------|----------------------|
| AI coding assistants lack project context | Repository Intelligence Engine indexes your entire codebase with AST parsing and knowledge graphs |
| Code changes break things in unexpected ways | Execution Engine creates git checkpoints and auto-rolls back on failure |
| No way to control what AI does to production | Approval Gates with risk levels require human sign-off |
| AI forgets what it learned about your code | Semantic Memory Engine persists knowledge across sessions |
| Solo developers need a full team | 5 specialized AI agents with distinct roles collaborate on tasks |
| Manual code review is slow and inconsistent | Review Pipeline checks security, performance, architecture, and quality scores automatically |

---

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.12+** | Core runtime |
| **FastAPI** | High-performance async API framework |
| **SQLAlchemy** | Database ORM |
| **SQLite** | Local development database |
| **Ollama** | Local LLM inference (qwen2.5) |
| **Tree-sitter** | AST parsing for code understanding |
| **ChromaDB** | Vector database for semantic memory |
| **MCP** | Model Context Protocol for tool virtualization |
| **Docker** | Containerization |

### Frontend
| Technology | Purpose |
|------------|---------|
| **Next.js 14** | React framework with App Router |
| **TypeScript** | Type-safe development |
| **Tailwind CSS** | Utility-first styling |
| **Zustand** | State management |
| **React Query** | Server state management |
| **Shadcn/ui** | UI component library |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FORGEAI PLATFORM                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  Frontend   │    │   Backend   │    │  AI Engine  │             │
│  │  Next.js    │◄──►│   FastAPI   │◄──►│   Ollama    │             │
│  │  Port 3000  │    │  Port 8000  │    │  Port 11434 │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│         │                   │                   │                   │
│         ▼                   ▼                   ▼                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   React     │    │   SQLite    │    │   Vector    │             │
│  │   Stores    │    │   Database  │    │   Memory    │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    MCP TOOL VIRTUALIZATION LAYER                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │   Git    │ │Filesystem│ │ Terminal │ │ Browser  │ │ Database ││
│  │   MCP    │ │   MCP    │ │   MCP    │ │   MCP    │ │   MCP    ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                        AI AGENT TEAM                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │ Software │ │   Code   │ │  DevOps  │ │    QA    │ │  Tech    ││
│  │ Engineer │ │ Reviewer │ │ Engineer │ │ Engineer │ │ Writer   ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Features

### Core Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Repository Intelligence** | Import and analyze any codebase with AST parsing | Production Ready |
| **AI Workspace** | Chat with AI about your code using local LLMs | Production Ready |
| **Software Engineer** | Autonomous code generation for 9 task types | Production Ready |
| **Code Reviewer** | Automated security, performance, and quality analysis | Production Ready |
| **Execution Engine** | Controlled execution with checkpoints and auto-rollback | Production Ready |
| **Approval Gates** | Risk-based human approval before code changes | Production Ready |
| **Semantic Memory** | Persistent knowledge across sessions | Production Ready |
| **Learning Center** | Engineering knowledge base from past work | Production Ready |

### Additional Features

| Feature | Description |
|---------|-------------|
| **Workflows** | Multi-step automation pipelines with real-time progress |
| **Deployment Center** | Auto-generate Docker, CI/CD, and Kubernetes configs |
| **Monitoring** | Real-time system health dashboard |
| **Studio** | Visual workflow builder and prompt management |
| **Validation** | Release candidate checks before shipping |
| **MCP Tools** | Standardized tool layer via Model Context Protocol (Git, Filesystem, Terminal, Browser, Database, Docker) |

---

## MCP — Model Context Protocol

ForgeAI uses **MCP (Model Context Protocol)** as a standardized tool virtualization layer. MCP provides a unified interface for AI agents to interact with external systems safely and consistently.

### What is MCP?

MCP is an open protocol that standardizes how AI applications connect to external tools and data sources. Think of it as a **universal adapter** that lets AI agents use any tool through a consistent interface.

### MCP Tools in ForgeAI

| Tool | Purpose | What It Does |
|------|---------|--------------|
| **Git MCP** | Version control | Clone repos, create branches, commit, push, diff, log |
| **Filesystem MCP** | File operations | Read, write, delete, list, search files and directories |
| **Terminal MCP** | Shell execution | Run commands with sandboxing and output capture |
| **Browser MCP** | Web operations | Navigate pages, extract content, fill forms |
| **Database MCP** | Data operations | Query, insert, update, schema management |
| **Docker MCP** | Container ops | Build, run, stop containers; manage compose stacks |

### How MCP Works in ForgeAI

```
┌──────────────────────────────────────────────────────────────┐
│                     AI AGENT REQUEST                          │
│  "Read the authentication module and fix the bug"            │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    MCP ADAPTER LAYER                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Git MCP   │  │FileSystem  │  │  Terminal   │         │
│  │   Adapter   │  │   MCP       │  │   MCP       │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   SANDBOXED EXECUTION                         │
│  • Permissions checked                                        │
│  • Commands validated                                         │
│  • Output captured                                            │
│  • Rollback on failure                                        │
└──────────────────────────────────────────────────────────────┘
```

### Benefits of MCP

| Benefit | Description |
|---------|-------------|
| **Standardization** | All tools follow the same interface pattern |
| **Safety** | Sandboxed execution with permission checks |
| **Extensibility** | Easy to add new MCP tools |
| **Interoperability** | Works with any MCP-compatible AI model |
| **Auditability** | All tool calls are logged and traceable |

---

## Quick Start

### Prerequisites

- **Python 3.12+** — [Download](https://www.python.org/downloads/)
- **Node.js 18+** — [Download](https://nodejs.org/)
- **Ollama** (optional) — [Download](https://ollama.ai) for AI features

### Step 1: Clone the Repository

```bash
git clone https://github.com/HitenDhamija/Forge-Ai.git
cd Forge-Ai
```

### Step 2: Set Up Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -e .

# Copy environment variables
cp .env.example .env

# Start the backend server
python run_server.py
```

Backend will start at **http://localhost:8000**

### Step 3: Set Up Frontend

```bash
# Navigate to frontend (new terminal)
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

Frontend will start at **http://localhost:3000**

### Step 4: Set Up AI (Optional)

```bash
# Install Ollama
# Visit https://ollama.ai and download for your OS

# Start Ollama server
ollama serve

# Pull the AI model
ollama pull qwen2.5
```

---

## Step-by-Step Usage Guide

### 1. Import Your First Repository

This is the **most important first step** — it unlocks all other features.

1. Open **http://localhost:3000**
2. Click **Repositories** in the sidebar
3. Click **Import Repository**
4. Choose import method:
   - **Folder** — Select a local project folder (easiest)
   - **Git URL** — Paste a GitHub repo URL
   - **ZIP** — Upload a .zip file
5. Enter a name (e.g., "My Project")
6. Click **Import**

**What happens automatically:**
- Repository is analyzed (files, lines, languages, frameworks)
- A **Project** is created
- A **Workflow** is auto-created with analysis steps
- **Documentation** is auto-generated
- The repo is indexed for **Memory** search

### 2. Explore the AI Workspace

1. Click **AI Workspace** in the sidebar
2. Select a model from the dropdown (e.g., `qwen2.5`)
3. Type a question: "Explain the authentication flow"
4. AI responds with context from your imported repos

**Example questions:**
- "What is this project about?"
- "Explain the code structure"
- "Are there any security issues?"
- "What frameworks are used?"

### 3. Run Automated Workflows

1. Click **Workflows** in the sidebar
2. Click **New Pipeline**
3. Add steps (title + description for each)
4. Click **Approve** (draft → ready)
5. Click **Run**
6. Watch real-time progress

### 4. Generate Code with AI

1. Click **Software Engineer** in the sidebar
2. Select a project
3. Choose task type: Feature, Bug Fix, API, Migration, Frontend, Backend, Documentation, Guidance
4. Describe what you want: "Add JWT authentication with login/register endpoints"
5. Click **Execute Task**
6. Watch progress: analyzing → planning → generating → reviewing → validating
7. Review generated code, diffs, review score
8. Click **Approve** or **Reject**

### 5. Review Code Automatically

1. Click **Agents** in the sidebar
2. Click **Run** on the **Code Reviewer** agent
3. Select a target project
4. Type a task: "Review the authentication module"
5. Click **Assign Task**
6. Monitor in **Recent Tasks**

### 6. Search Your Codebase

1. Click **Memory** in the sidebar
2. Type a natural language query: "authentication middleware"
3. Filter by repository, chunk type, language
4. View ranked results on left
5. Click **Build Context** to generate AI-ready context

### 7. Generate Deployment Configs

1. Click **Deployment Center** in the sidebar
2. Select a repository
3. Click **Analyze**
4. Review Overview (production score, infrastructure)
5. Browse **Docker** tab for Dockerfile + Compose
6. Browse **CI/CD** tab for GitHub Actions
7. Browse **Kubernetes** tab for K8s manifests

### 8. Learn from Past Work

1. Click **Learning Center** in the sidebar
2. Click **Process Workflow**
3. Select a project
4. Describe what was accomplished
5. Set outcome (Success/Failure/Partial)
6. Click **Process**
7. Browse extracted experiences, patterns, and lessons

### 9. Monitor Everything

1. Click **Monitoring** in the sidebar
2. View Overview (system stats)
3. Click **Workflows** tab for pipeline status
4. Click **Agents** tab for agent performance
5. Click **Health** tab for component health

---

## Project Structure

```
forge-ai/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agents/            # AI agent implementations
│   │   ├── ai/                # LLM integration
│   │   ├── api/v1/            # REST API endpoints
│   │   ├── core/              # Configuration and utilities
│   │   ├── execution/         # Execution engine
│   │   ├── learning/          # Learning center
│   │   ├── memory/            # Semantic memory
│   │   ├── monitoring/        # System monitoring
│   │   ├── plugins/           # Plugin system
│   │   ├── repo_intelligence/ # Repository analysis
│   │   ├── studio/            # Visual workflow builder
│   │   ├── tools/             # MCP tool virtualization layer
│   │   │   ├── mcp.py         # MCP server adapter & runtime
│   │   │   ├── filesystem.py  # Filesystem MCP tool
│   │   │   ├── git.py         # Git MCP tool
│   │   │   ├── terminal.py    # Terminal MCP tool
│   │   │   ├── browser.py     # Browser MCP tool
│   │   │   ├── database.py    # Database MCP tool
│   │   │   └── docker.py      # Docker MCP tool
│   │   └── validation/        # Release validation
│   ├── alembic/               # Database migrations
│   └── tests/                 # Backend tests
├── frontend/                   # Next.js frontend
│   ├── app/                   # App router pages
│   ├── components/            # React components
│   ├── hooks/                 # Custom hooks
│   ├── services/              # API client services
│   ├── stores/                # Zustand state stores
│   └── types/                 # TypeScript type definitions
├── docker/                     # Docker configurations
├── docs/                       # Documentation
├── scripts/                    # Utility scripts
└── tests/                      # Test suites
```

---

## API Reference

### Backend API

The backend API is available at `http://localhost:8000/api/v1`

**Key Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/repositories` | GET | List all repositories |
| `/api/v1/repositories/import` | POST | Import a new repository |
| `/api/v1/software-engineer/execute` | POST | Execute a code generation task |
| `/api/v1/workflows` | GET | List all workflows |
| `/api/v1/workflows/{id}/run` | POST | Run a workflow |
| `/api/v1/agents/{type}/run` | POST | Run an AI agent |
| `/api/v1/memory/search` | POST | Search semantic memory |
| `/api/v1/learning/patterns` | GET | Get detected patterns |
| `/api/v1/learning/experiences` | GET | Get recorded experiences |

### Interactive API Documentation

Visit **http://localhost:8000/docs** for the interactive Swagger UI documentation.

---

## Configuration

### Environment Variables

Backend (`backend/.env`):

```env
# Application
APP_NAME=ForgeAI
APP_ENV=development
DEBUG=true

# API
API_V1_PREFIX=/api/v1

# Database (SQLite for development)
DATABASE_URL=sqlite+aiosqlite:///./forgeai.db

# JWT Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# AI Configuration (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
AI_DEFAULT_MODEL=qwen2.5

# SMTP Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

Frontend (`frontend/.env`):

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
NEXT_PUBLIC_APP_NAME=ForgeAI
```

---

## Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Run linting (`ruff check app/ && npm run lint`)
6. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with care by the ForgeAI team**

[Report Bug](https://github.com/HitenDhamija/Forge-Ai/issues) · [Request Feature](https://github.com/HitenDhamija/Forge-Ai/issues)

</div>
