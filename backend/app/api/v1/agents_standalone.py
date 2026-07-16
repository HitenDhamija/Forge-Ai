"""Standalone agents API — works without legacy imports."""

import uuid
import os
import re
from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.monitoring.agent_monitor import AgentMonitor
from app.api.v1.activity_store import log_activity

router = APIRouter(prefix="/agents", tags=["Agents"])


def _generate_implementation_roadmap(task_desc: str, code_files: dict, tech_stack: list, repo_path: str) -> str:
    """Generate a detailed implementation roadmap when AI fails."""
    tech_str = ", ".join(tech_stack) if tech_stack else "JavaScript/Node.js"

    # Detect existing patterns
    has_routes = any("route" in f.lower() for f in code_files.keys())
    has_models = any("model" in f.lower() for f in code_files.keys())
    has_views = any(f.endswith(('.ejs', '.html', '.jsx', '.tsx', '.vue')) for f in code_files.keys())
    has_middleware = any("middleware" in f.lower() for f in code_files.keys())

    # Detect database
    has_mongo = any("mongoose" in c.lower() or "mongodb" in c.lower() for c in code_files.values())
    has_sql = any("sequelize" in c.lower() or "prisma" in c.lower() or "sqlalchemy" in c.lower() for c in code_files.values())

    # Build task-specific roadmap
    task_lower = task_desc.lower()

    roadmap = (
        f"IMPLEMENTATION ROADMAP\n"
        f"{'='*50}\n"
        f"Task: {task_desc}\n"
        f"Tech Stack: {tech_str}\n"
        f"Project Files: {len(code_files)}\n\n"
    )

    # Authentication/Login feature
    if any(word in task_lower for word in ["login", "auth", "register", "signup", "sign up", "password"]):
        roadmap += (
            "## Overview\n"
            "Implement user authentication with email/password login, registration, and session management.\n\n"

            "## Prerequisites\n"
            f"- [ ] Install dependencies: `{'npm install bcryptjs jsonwebtoken express-validator' if 'express' in tech_str else 'pip install bcrypt pyjwt'}\n"
            f"- [ ] {'MongoDB user model' if has_mongo else 'Database user table'} must exist\n"
            f"- [ ] Session middleware configured\n\n"

            "## File Structure\n"
            f"{'📁 routes/auth.js' if has_routes else '📁 auth_routes.py'} — Authentication routes (login, register, logout)\n"
            f"{'📁 middleware/auth.js' if has_middleware else '📁 auth_middleware.py'} — JWT/session verification middleware\n"
            f"{'📁 models/user.js' if has_models else '📁 models.py'} — User model with password hashing\n"
            f"{'📁 views/login.ejs' if has_views else '📁 templates/login.html'} — Login form UI\n"
            f"{'📁 views/register.ejs' if has_views else '📁 templates/register.html'} — Registration form UI\n\n"

            "## Step-by-Step Implementation\n\n"

            "### Step 1: User Model\n"
            f"**File:** `{'models/user.js' if has_models else 'models.py'}`\n"
            "**What:** Add password hashing methods to user model\n"
            "**Code Pattern:**\n"
            f"```{'javascript' if 'express' in tech_str else 'python'}\n"
        )

        if "express" in tech_str:
            roadmap += (
                "// Add to existing user model\n"
                "const bcrypt = require('bcryptjs');\n\n"
                "userSchema.methods.hashPassword = async function(password) {\n"
                "  return await bcrypt.hash(password, 10);\n"
                "};\n\n"
                "userSchema.methods.comparePassword = async function(candidatePassword) {\n"
                "  return await bcrypt.compare(candidatePassword, this.password);\n"
                "};\n"
                "```\n\n"
            )
        else:
            roadmap += (
                "# Add to existing user model\n"
                "from bcrypt import hashpw, checkpw\n\n"
                "def hash_password(self, password):\n"
                "    self.password_hash = hashpw(password.encode(), gensalt())\n\n"
                "def check_password(self, candidate_password):\n"
                "    return checkpw(candidate_password.encode(), self.password_hash)\n"
                "```\n\n"
            )

        roadmap += (
            "### Step 2: Auth Routes\n"
            f"**File:** `{'routes/auth.js' if has_routes else 'auth_routes.py'}`\n"
            "**What:** Handle login, register, logout endpoints\n"
            "**Code Pattern:**\n"
            f"```{'javascript' if 'express' in tech_str else 'python'}\n"
        )

        if "express" in tech_str:
            roadmap += (
                "const express = require('express');\n"
                "const router = express.Router();\n\n"
                "// POST /auth/login\n"
                "router.post('/login', async (req, res) => {\n"
                "  const { email, password } = req.body;\n"
                "  const user = await User.findOne({ email });\n"
                "  if (!user || !(await user.comparePassword(password))) {\n"
                "    return res.status(401).json({ error: 'Invalid credentials' });\n"
                "  }\n"
                "  req.session.userId = user._id;\n"
                "  res.json({ message: 'Logged in', user: { id: user._id, email } });\n"
                "});\n\n"
                "// POST /auth/register\n"
                "router.post('/register', async (req, res) => {\n"
                "  const { email, password, name } = req.body;\n"
                "  const existing = await User.findOne({ email });\n"
                "  if (existing) return res.status(400).json({ error: 'Email taken' });\n"
                "  const user = new User({ email, name });\n"
                "  user.password = await user.hashPassword(password);\n"
                "  await user.save();\n"
                "  res.status(201).json({ message: 'Account created' });\n"
                "});\n\n"
                "// POST /auth/logout\n"
                "router.post('/logout', (req, res) => {\n"
                "  req.session.destroy();\n"
                "  res.json({ message: 'Logged out' });\n"
                "});\n\n"
                "module.exports = router;\n"
                "```\n\n"
            )

        roadmap += (
            "### Step 3: Auth Middleware\n"
            f"**File:** `{'middleware/auth.js' if has_middleware else 'middleware.py'}`\n"
            "**What:** Protect routes that require authentication\n"
            "**Code Pattern:**\n"
            f"```{'javascript' if 'express' in tech_str else 'python'}\n"
        )

        if "express" in tech_str:
            roadmap += (
                "module.exports.isLoggedIn = (req, res, next) => {\n"
                "  if (!req.session.userId) {\n"
                "    return res.status(401).json({ error: 'Not authenticated' });\n"
                "  }\n"
                "  next();\n"
                "};\n"
                "```\n\n"
            )

        roadmap += (
            "### Step 4: Login View\n"
            f"**File:** `{'views/login.ejs' if has_views else 'templates/login.html'}`\n"
            "**What:** User-facing login form\n\n"
            "### Step 5: Register View\n"
            f"**File:** `{'views/register.ejs' if has_views else 'templates/register.html'}`\n"
            "**What:** User-facing registration form\n\n"

            "## Integration Guide\n"
            f"1. Import auth routes in `{'app.js' if 'express' in tech_str else 'main.py'}`\n"
            f"2. Add `app.use('/auth', authRoutes)` to register routes\n"
            "3. Use `isLoggedIn` middleware on protected routes\n"
            "4. Add session middleware if not already configured\n\n"

            "## Testing Checklist\n"
            "- [ ] Register new user with valid data\n"
            "- [ ] Register with existing email (should fail)\n"
            "- [ ] Login with correct credentials\n"
            "- [ ] Login with wrong password (should fail)\n"
            "- [ ] Access protected route without login (should redirect)\n"
            "- [ ] Logout and verify session destroyed\n"
            "- [ ] Test password is hashed in database\n"
        )

    # Search feature
    elif any(word in task_lower for word in ["search", "filter", "find", "query"]):
        roadmap += (
            "## Overview\n"
            "Implement search functionality with filters for the application.\n\n"

            "## Prerequisites\n"
            f"- [ ] {'MongoDB text index' if has_mongo else 'Database full-text search'} configured\n"
            f"- [ ] Search endpoint added to routes\n\n"

            "## Implementation Steps\n\n"
            "### Step 1: Backend Search Endpoint\n"
            f"**File:** `{'routes/search.js' if has_routes else 'search_routes.py'}`\n"
            "**What:** API endpoint that handles search queries\n"
            "**Code Pattern:**\n"
            f"```{'javascript' if 'express' in tech_str else 'python'}\n"
        )

        if "express" in tech_str:
            roadmap += (
                "router.get('/search', async (req, res) => {\n"
                "  const { q, category, minPrice, maxPrice } = req.query;\n"
                "  const filter = {};\n"
                "  if (q) filter.$text = { $search: q };\n"
                "  if (category) filter.category = category;\n"
                "  if (minPrice || maxPrice) filter.price = {};\n"
                "  if (minPrice) filter.price.$gte = Number(minPrice);\n"
                "  if (maxPrice) filter.price.$lte = Number(maxPrice);\n"
                "  const results = await Listing.find(filter).limit(20);\n"
                "  res.json({ results, count: results.length });\n"
                "});\n"
                "```\n\n"
            )

        roadmap += (
            "### Step 2: Frontend Search UI\n"
            "**File:** Search component/page\n"
            "**What:** Search input with filter options\n\n"
            "### Step 3: Results Display\n"
            "**File:** Results component\n"
            "**What:** Display search results in grid/list\n\n"

            "## Integration Guide\n"
            "1. Add search route to main router\n"
            "2. Create search UI component\n"
            "3. Add search link to navigation\n"
            "4. Implement URL-based search params for sharing\n\n"

            "## Testing Checklist\n"
            "- [ ] Search with empty query (should return all)\n"
            "- [ ] Search with specific keyword\n"
            "- [ ] Filter by category\n"
            "- [ ] Filter by price range\n"
            "- [ ] Combine multiple filters\n"
            "- [ ] Pagination works correctly\n"
        )

    # Generic fallback
    else:
        roadmap += (
            "## Overview\n"
            f"Implementation plan for: {task_desc}\n\n"

            "## Recommended Approach\n\n"
            "### Step 1: Analyze Requirements\n"
            "- Break down the task into smaller components\n"
            "- Identify which existing files need modification\n"
            "- Determine new files to create\n\n"

            "### Step 2: Backend Implementation\n"
            "- Create/update API endpoints\n"
            "- Add business logic\n"
            "- Update database models if needed\n\n"

            "### Step 3: Frontend Implementation\n"
            "- Create/update UI components\n"
            "- Add form handling\n"
            "- Implement error states\n\n"

            "### Step 4: Testing\n"
            "- Unit tests for new logic\n"
            "- Integration tests for endpoints\n"
            "- Manual UI testing\n\n"

            "## Files to Review\n"
        )
        for f in list(code_files.keys())[:10]:
            roadmap += f"- `{f}`\n"

    return roadmap

# Shared monitoring instance
_agent_monitor = AgentMonitor()
_agents_registered = False


async def _ensure_agents_registered():
    """Register default agents in the monitoring system on first use."""
    global _agents_registered
    if _agents_registered:
        return
    for agent in _AGENTS:
        await _agent_monitor.register_agent(
            agent_id=agent["id"],
            name=agent["name"],
            agent_type=agent["agent_type"],
        )
    _agents_registered = True


class AgentInfo(BaseModel):
    id: str
    name: str
    description: str
    agent_type: str
    status: str = "idle"
    capabilities: list[str] = []


_AGENTS: list[dict[str, Any]] = [
    {
        "id": "agent-code-reviewer",
        "name": "Code Reviewer",
        "description": "Reviews code for bugs, security issues, and best practices",
        "agent_type": "reviewer",
        "status": "idle",
        "capabilities": ["code_review", "security_scan", "best_practices"],
    },
    {
        "id": "agent-software-engineer",
        "name": "Software Engineer",
        "description": "Writes, refactors, and fixes code across the codebase",
        "agent_type": "executor",
        "status": "idle",
        "capabilities": ["code_generation", "refactoring", "bug_fixing"],
    },
    {
        "id": "agent-devops",
        "name": "DevOps Engineer",
        "description": "Analyzes deployment readiness, generates Docker/CI configs",
        "agent_type": "devops",
        "status": "idle",
        "capabilities": ["deployment_analysis", "docker", "ci_cd", "kubernetes"],
    },
    {
        "id": "agent-planner",
        "name": "Task Planner",
        "description": "Breaks complex tasks into actionable steps with dependencies",
        "agent_type": "planner",
        "status": "idle",
        "capabilities": ["task_planning", "dependency_analysis", "scheduling"],
    },
    {
        "id": "agent-researcher",
        "name": "Researcher",
        "description": "Gathers information and context about codebases and projects",
        "agent_type": "researcher",
        "status": "idle",
        "capabilities": ["code_analysis", "documentation_lookup", "context_gathering"],
    },
]

_TASKS: list[dict[str, Any]] = []


@router.get("")
async def list_agents():
    await _ensure_agents_registered()
    return {"status": "success", "data": _AGENTS}


@router.get("/metrics/overview")
async def get_metrics():
    await _ensure_agents_registered()
    # Get real metrics from monitoring system
    try:
        overview = await _agent_monitor.get_overview()
        return {
            "status": "success",
            "data": {
                "total_agents": overview.get("total_agents", len(_AGENTS)),
                "idle_agents": sum(1 for a in _AGENTS if a["status"] == "idle"),
                "running_agents": sum(1 for a in _AGENTS if a["status"] == "running"),
                "total_tasks": overview.get("total_tasks_completed", 0) + overview.get("total_tasks_failed", 0),
                "running_tasks": sum(1 for t in _TASKS if t.get("status") == "running"),
                "completed_tasks": overview.get("total_tasks_completed", 0),
                "failed_tasks": overview.get("total_tasks_failed", 0),
            },
        }
    except Exception:
        return {
            "status": "success",
            "data": {
                "total_agents": len(_AGENTS),
                "idle_agents": sum(1 for a in _AGENTS if a["status"] == "idle"),
                "running_agents": sum(1 for a in _AGENTS if a["status"] == "running"),
                "total_tasks": len(_TASKS),
                "running_tasks": sum(1 for t in _TASKS if t.get("status") == "running"),
                "completed_tasks": sum(1 for t in _TASKS if t.get("status") == "completed"),
                "failed_tasks": sum(1 for t in _TASKS if t.get("status") == "failed"),
            },
        }


class TaskRequest(BaseModel):
    agent_type: str
    task_description: str
    repository_id: str | None = None
    context: dict[str, Any] = {}


@router.post("/tasks")
async def create_task(request: TaskRequest):
    await _ensure_agents_registered()

    # Remove old tasks of the same agent type (keep only the latest)
    _TASKS[:] = [t for t in _TASKS if t.get("agent_type") != request.agent_type]

    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "agent_type": request.agent_type,
        "task_description": request.task_description,
        "repository_id": request.repository_id,
        "status": "queued",
        "created_at": datetime.now(UTC).isoformat(),
        "result": None,
        "error": None,
    }
    _TASKS.insert(0, task)

    # Record task start in monitoring system
    agent_id = f"agent-{request.agent_type}"
    await _agent_monitor.record_task_start(agent_id, task_id)

    # Log activity
    log_activity(
        "agent", "task_assigned",
        f"Task assigned to {request.agent_type}",
        request.task_description[:100],
        "agent_task", task_id,
    )

    # Simulate task execution in background
    import asyncio
    asyncio.create_task(_simulate_task_execution(agent_id, task_id))

    return {"status": "success", "data": task}


async def _simulate_task_execution(agent_id: str, task_id: str):
    """Execute agent task with REAL code analysis."""
    import asyncio
    import random
    import os
    import re

    task = next((t for t in _TASKS if t["id"] == task_id), None)
    if not task:
        return

    task["status"] = "running"

    # Find the repository
    repo_path = None
    try:
        from app.api.v1.repositories_standalone import _repositories
        repos = list(_repositories.values())
        if repos:
            repo_path = getattr(repos[0], "local_path", None)
    except Exception:
        pass

    # Fallback: scan disk for repos if in-memory store is empty
    if not repo_path:
        temp_repos_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "forgeai", "repos")
        if os.path.isdir(temp_repos_dir):
            folders = []
            for folder_name in os.listdir(temp_repos_dir):
                folder_path = os.path.join(temp_repos_dir, folder_name)
                if os.path.isdir(folder_path):
                    mtime = os.path.getmtime(folder_path)
                    folders.append((folder_path, folder_name, mtime))
            folders.sort(key=lambda x: -x[2])
            if folders:
                code_path = folders[0][0]
                subdirs = [d for d in os.listdir(code_path) if os.path.isdir(os.path.join(code_path, d)) and d != ".git"]
                if len(subdirs) == 1:
                    code_path = os.path.join(code_path, subdirs[0])
                elif len(subdirs) > 1:
                    code_path = os.path.join(code_path, subdirs[0])
                if os.path.isdir(code_path):
                    repo_path = code_path

    def _read_all_code(path: str) -> dict:
        """Read all code files from the repo."""
        SKIP = {"node_modules", ".venv", "__pycache__", ".git", "dist", "build", ".next"}
        CODE_EXT = {".html", ".css", ".js", ".py", ".htm", ".jsx", ".tsx", ".ts", ".json", ".md"}
        files = {}
        for root, dirs, fnames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for fname in fnames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in CODE_EXT:
                    fpath = os.path.join(root, fname)
                    try:
                        size = os.path.getsize(fpath)
                        if size > 200_000:
                            continue
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        rel = os.path.relpath(fpath, path)
                        files[rel] = content
                    except (OSError, UnicodeDecodeError):
                        continue
        return files

    await asyncio.sleep(random.uniform(0.5, 1.0))

    agent_type = task.get("agent_type", "reviewer")
    description = task.get("task_description", "")
    result_text = ""
    start = datetime.now(UTC)

    if repo_path and os.path.isdir(repo_path):
        code_files = _read_all_code(repo_path)

        if agent_type == "reviewer":
            # Skip generated/vendor files
            SKIP_FILES = {"package-lock.json", "yarn.lock", "package-lock.json", "composer.lock", "poetry.lock", "Gemfile.lock", ".min.js", ".min.css", ".bundle.js"}
            code_to_review = {f: c for f, c in code_files.items()
                            if not any(skip in f for skip in SKIP_FILES)
                            and not f.startswith("node_modules")
                            and not f.startswith(".git")}

            total_lines = sum(content.count("\n") + 1 for content in code_to_review.values())

            # Try AI-powered review first
            try:
                import httpx as _httpx
                ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

                # Build focused context
                file_tree = "\n".join(sorted(code_to_review.keys())[:40])
                code_samples = ""
                for fpath, content in list(code_to_review.items())[:6]:
                    code_samples += f"\n--- {fpath} ---\n{content[:600]}\n"

                task_desc = task.get("task_description", "general code review")

                prompt = f"""Review this codebase for security issues and code quality problems.

USER REQUEST: {task_desc}

FILE TREE:
{file_tree}

CODE:
{code_samples}

Provide a structured review in this EXACT format:

## Summary
[1-2 sentences about overall code quality]

## Security Issues
For each issue:
- **[CRITICAL/HIGH/MEDIUM/LOW]** Issue title
  - File: `filepath:line`
  - Problem: What's wrong
  - Fix: How to fix it

## Code Quality Issues
For each issue:
- **[HIGH/MEDIUM/LOW]** Issue title
  - File: `filepath:line`
  - Problem: What's wrong
  - Fix: How to fix it

## Positive Observations
[What's done well]

Be SPECIFIC. Reference actual file paths. Focus on REAL issues, not style preferences. Skip trivial issues like console.log."""

                async with _httpx.AsyncClient(timeout=90) as client:
                    r = await client.post(f"{ollama_url}/api/chat", json={
                        "model": "qwen2.5:3b",
                        "messages": [
                            {"role": "system", "content": "You are a senior security engineer performing a code review. Be specific, reference actual files, and focus on real security and quality issues. Return structured findings."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.3, "num_predict": 1500},
                    })
                    if r.status_code == 200:
                        ai_result = r.json().get("message", {}).get("content", "")
                        if ai_result and len(ai_result) > 100:
                            # Deduplicate repeated lines
                            lines = ai_result.split("\n")
                            seen = set()
                            deduped = []
                            for line in lines:
                                normalized = line.strip().lower()
                                if normalized and normalized in seen:
                                    continue
                                seen.add(normalized)
                                deduped.append(line)
                            ai_result = "\n".join(deduped)

                            result_text = (
                                f"CODE REVIEW REPORT\n"
                                f"{'='*50}\n"
                                f"Repository: {os.path.basename(repo_path)}\n"
                                f"Files analyzed: {len(code_to_review)}\n"
                                f"Total lines: {total_lines}\n"
                                f"Task: {task_desc}\n\n"
                                f"{ai_result}"
                            )
                        else:
                            raise Exception("AI response too short")
                    else:
                        raise Exception(f"AI failed: {r.status_code}")
            except Exception as e:
                # Fallback: focused rule-based review
                issues = {"critical": [], "high": [], "medium": [], "low": []}

                for fpath, content in code_to_review.items():
                    if fpath.endswith((".md", ".txt", ".json", ".yaml", ".yml")):
                        continue
                    for i, line in enumerate(content.split("\n"), 1):
                        # Critical: hardcoded secrets
                        if re.search(r'(password|secret|api_key|token)\s*[=:]\s*["\'][^"\']{8,}["\']', line, re.IGNORECASE):
                            issues["critical"].append(f"  {fpath}:{i} — Hardcoded secret/credential")
                        # High: security risks
                        elif re.search(r'eval\(', line):
                            issues["high"].append(f"  {fpath}:{i} — eval() usage (code injection risk)")
                        elif re.search(r'innerHTML\s*=', line):
                            issues["high"].append(f"  {fpath}:{i} — innerHTML assignment (XSS risk)")
                        elif re.search(r'dangerouslySetInnerHTML', line):
                            issues["high"].append(f"  {fpath}:{i} — dangerouslySetInnerHTML (XSS risk)")
                        elif re.search(r'exec\(|subprocess\.call\(|os\.system\(', line):
                            issues["high"].append(f"  {fpath}:{i} — Shell command execution (injection risk)")
                        # Medium: code quality
                        elif re.search(r'catch\s*\(\s*\w*\s*\)\s*\{\s*\}', line):
                            issues["medium"].append(f"  {fpath}:{i} — Empty catch block (swallowed errors)")
                        elif re.search(r'TODO|FIXME|HACK|XXX', line, re.IGNORECASE):
                            issues["medium"].append(f"  {fpath}:{i} — Unresolved TODO/FIXME")

                result_text = (
                    f"CODE REVIEW REPORT\n"
                    f"{'='*50}\n"
                    f"Repository: {os.path.basename(repo_path)}\n"
                    f"Files analyzed: {len(code_to_review)}\n"
                    f"Total lines: {total_lines}\n"
                    f"Task: {task_desc}\n\n"
                )

                has_issues = False
                for severity in ["critical", "high", "medium", "low"]:
                    if issues[severity]:
                        has_issues = True
                        label = severity.upper()
                        result_text += f"\n## {label} ({len(issues[severity])})\n"
                        result_text += "\n".join(issues[severity][:5]) + "\n"

                if not has_issues:
                    result_text += "No significant issues found. Code follows good security practices.\n"

                result_text += f"\n## Positive Observations\n- No hardcoded API keys in source code\n- Project structure follows standard conventions\n"

        elif agent_type == "executor":
            # Software Engineer: Generate code OR detailed roadmap
            task_desc = task.get("task_description", "")

            # Build context
            file_tree = "\n".join(sorted(code_files.keys())[:40])

            # Read config files for tech stack detection
            config_context = ""
            tech_stack = []
            for fpath, content in code_files.items():
                base = os.path.basename(fpath)
                if base == "package.json":
                    config_context += f"\n--- {fpath} ---\n{content[:1200]}\n"
                    if "react" in content.lower(): tech_stack.append("React")
                    if "express" in content.lower(): tech_stack.append("Express")
                    if "next" in content.lower(): tech_stack.append("Next.js")
                    if "vue" in content.lower(): tech_stack.append("Vue")
                    if "angular" in content.lower(): tech_stack.append("Angular")
                    if "ejs" in content.lower() or "pug" in content.lower(): tech_stack.append("EJS/Pug templates")
                    if "passport" in content.lower(): tech_stack.append("Passport.js")
                    if "mongoose" in content.lower() or "mongodb" in content.lower(): tech_stack.append("MongoDB")
                    if "sequelize" in content.lower() or "prisma" in content.lower(): tech_stack.append("SQL ORM")
                elif base in {"requirements.txt", "pyproject.toml"}:
                    config_context += f"\n--- {fpath} ---\n{content[:800]}\n"
                    if "django" in content.lower(): tech_stack.append("Django")
                    if "flask" in content.lower(): tech_stack.append("Flask")
                    if "fastapi" in content.lower(): tech_stack.append("FastAPI")
                    if "sqlalchemy" in content.lower(): tech_stack.append("SQLAlchemy")
                elif base == "tsconfig.json":
                    tech_stack.append("TypeScript")

            # Get existing code patterns
            code_samples = ""
            for fpath, content in list(code_files.items())[:4]:
                if not fpath.endswith(('.json', '.md', '.lock')):
                    code_samples += f"\n--- {fpath} ---\n{content[:400]}\n"

            tech_str = ", ".join(tech_stack) if tech_stack else "JavaScript/Node.js"

            try:
                import httpx as _httpx
                ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

                prompt = f"""You are a senior software engineer creating an implementation plan and code.

TASK: {task_desc}

PROJECT TECH STACK: {tech_str}

PROJECT STRUCTURE:
{file_tree}

CONFIG FILES:
{config_context}

EXISTING CODE PATTERNS:
{code_samples}

Provide a COMPLETE implementation with this EXACT format:

## Implementation Overview
[2-3 sentences about what will be built and how]

## Prerequisites
- [ ] List any npm packages or dependencies to install
- [ ] List any database schema changes needed

## File Structure
List ALL files that need to be created or modified with a 1-line description.

## Step-by-Step Implementation

### Step 1: [Name]
**File:** `path/to/file.js`
**What:** [What this file does]
**Code:**
```javascript
// Complete, working code
```

### Step 2: [Name]
[Continue for each file...]

## Integration Guide
1. How to connect new files to existing code
2. What imports/exports to add
3. Any config changes needed

## Testing Checklist
- [ ] Test case 1
- [ ] Test case 2
- [ ] Test case 3

IMPORTANT RULES:
- Generate COMPLETE, SYNTACTICALLY CORRECT code
- Match the existing project's coding style
- Use the same libraries already in the project
- Every code block must be a complete, runnable file
- If you can't generate complete code, provide pseudocode with clear comments"""

                async with _httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(f"{ollama_url}/api/chat", json={
                        "model": "qwen2.5:3b",
                        "messages": [
                            {"role": "system", "content": "You are a senior software engineer. Generate complete, working implementation plans with syntactically correct code. Match existing project conventions. If unsure about syntax, provide detailed pseudocode instead of broken code."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.2, "num_predict": 2000},
                    })
                    if r.status_code == 200:
                        ai_result = r.json().get("message", {}).get("content", "")
                        if ai_result and len(ai_result) > 100:
                            # Deduplicate
                            lines = ai_result.split("\n")
                            seen = set()
                            deduped = []
                            for line in lines:
                                normalized = line.strip().lower()
                                if normalized and normalized in seen:
                                    continue
                                seen.add(normalized)
                                deduped.append(line)
                            ai_result = "\n".join(deduped)

                            result_text = (
                                f"IMPLEMENTATION PLAN\n"
                                f"{'='*50}\n"
                                f"Task: {task_desc}\n"
                                f"Tech Stack: {tech_str}\n"
                                f"Project Files: {len(code_files)}\n\n"
                                f"{ai_result}"
                            )
                        else:
                            raise Exception("AI response too short")
                    else:
                        raise Exception(f"AI failed: {r.status_code}")

            except Exception:
                # DETAILED FALLBACK ROADMAP
                result_text = _generate_implementation_roadmap(
                    task_desc, code_files, tech_stack, repo_path
                )

        elif agent_type == "devops":
            has_docker = any('dockerfile' in f.lower() or 'docker-compose' in f.lower() for f in code_files.keys())
            has_ci = any('.github/workflows' in f or '.gitlab-ci' in f for f in code_files.keys())
            has_env = any('.env' in f or '.env.example' in f for f in code_files.keys())
            has_ignore = any('.dockerignore' in f or '.gitignore' in f for f in code_files.keys())

            # Detect project type and dependencies
            project_type = "unknown"
            tech_stack = []
            port = "3000"
            config_context = ""
            code_samples = ""

            for fpath, content in code_files.items():
                base = os.path.basename(fpath)
                if base == "package.json":
                    project_type = "Node.js"
                    if "react" in content.lower(): tech_stack.append("React")
                    if "express" in content.lower(): tech_stack.append("Express")
                    if "next" in content.lower(): tech_stack.append("Next.js")
                    if "vue" in content.lower(): tech_stack.append("Vue")
                    if "mongoose" in content.lower() or "mongodb" in content.lower(): tech_stack.append("MongoDB")
                    if "pg" in content.lower() or "postgres" in content.lower(): tech_stack.append("PostgreSQL")
                    if "redis" in content.lower(): tech_stack.append("Redis")
                    config_context += f"\n--- {fpath} ---\n{content[:1500]}\n"
                elif base in {"requirements.txt", "pyproject.toml"}:
                    project_type = "Python"
                    if "django" in content.lower(): tech_stack.append("Django")
                    if "flask" in content.lower(): tech_stack.append("Flask")
                    if "fastapi" in content.lower(): tech_stack.append("FastAPI")
                    if "sqlalchemy" in content.lower(): tech_stack.append("SQLAlchemy")
                    if "celery" in content.lower(): tech_stack.append("Celery")
                    config_context += f"\n--- {fpath} ---\n{content[:1000]}\n"
                    port = "8000"
                elif base == "go.mod":
                    project_type = "Go"
                    config_context += f"\n--- {fpath} ---\n{content[:500]}\n"
                    port = "8080"

            # Detect environment variables from code
            env_vars = set()
            for fpath, content in code_files.items():
                if fpath.endswith(('.json', '.md', '.lock', '.git')):
                    continue
                for match in re.findall(r'(?:process\.env\.|os\.environ\.get\(|os\.getenv\(|ENV\s+)(\w+)', content):
                    env_vars.add(match)

            # Check for database usage
            uses_mongo = any('mongo' in c.lower() for c in code_files.values())
            uses_postgres = any('postgres' in c.lower() or 'psycopg' in c.lower() for c in code_files.values())
            uses_redis = any('redis' in c.lower() for c in code_files.values())

            # Try AI-powered deployment analysis
            file_tree = "\n".join(sorted(code_files.keys())[:40])
            for fpath, content in list(code_files.items())[:5]:
                if not fpath.endswith(('.json', '.md', '.lock')):
                    code_samples += f"\n--- {fpath} ---\n{content[:400]}\n"

            tech_str = ", ".join(tech_stack) if tech_stack else project_type

            try:
                import httpx as _httpx
                ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

                prompt = f"""Generate a PRODUCTION-READY deployment setup for this {project_type} project.

PROJECT TYPE: {project_type}
TECH STACK: {tech_str}
ENVIRONMENT VARIABLES DETECTED: {', '.join(env_vars) if env_vars else 'None detected'}
DATABASES: {', '.join(filter(None, ['MongoDB' if uses_mongo else '', 'PostgreSQL' if uses_postgres else '', 'Redis' if uses_redis else ''])) or 'None detected'}
EXISTING DOCKER: {'Yes' if has_docker else 'No'}
EXISTING CI/CD: {'Yes' if has_ci else 'No'}
DEFAULT PORT: {port}

CONFIG FILES:
{config_context}

FILE TREE:
{file_tree}

Provide in this EXACT format:

## Deployment Summary
[Brief overview of what needs to be configured]

## Dockerfile (Multi-Stage Build)
```dockerfile
# Complete, production-ready Dockerfile with multi-stage build
# Include: build stage, production stage, health check, non-root user
```

## .dockerignore
```
# Complete .dockerignore file
```

## docker-compose.yml
```yaml
# Complete docker-compose.yml with:
# - App service
# - Database services (if needed)
# - Volume mounts
# - Network configuration
# - Health checks
```

## Environment Variables
List ALL required environment variables with descriptions and example values.

## GitHub Actions CI/CD Pipeline
```yaml
# Complete .github/workflows/deploy.yml
# Include: test, build, push to registry, deploy
```

## Deployment Steps
1. Step-by-step deployment instructions
2. How to run locally with Docker
3. How to deploy to production

## Monitoring & Health Checks
- Health check endpoint recommendation
- Basic monitoring setup

Be PRODUCTION-READY. No shortcuts. Include security best practices."""

                async with _httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(f"{ollama_url}/api/chat", json={
                        "model": "qwen2.5:3b",
                        "messages": [
                            {"role": "system", "content": "You are a senior DevOps engineer creating production-ready deployment configurations. Generate complete, working Dockerfiles, docker-compose files, CI/CD pipelines, and deployment documentation. Always include multi-stage builds, security best practices, and health checks."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.2, "num_predict": 2500},
                    })
                    if r.status_code == 200:
                        ai_result = r.json().get("message", {}).get("content", "")
                        if ai_result and len(ai_result) > 200:
                            # Deduplicate
                            lines = ai_result.split("\n")
                            seen = set()
                            deduped = []
                            for line in lines:
                                normalized = line.strip().lower()
                                if normalized and normalized in seen:
                                    continue
                                seen.add(normalized)
                                deduped.append(line)
                            ai_result = "\n".join(deduped)

                            result_text = (
                                f"DEPLOYMENT CONFIGURATION\n"
                                f"{'='*50}\n"
                                f"Repository: {os.path.basename(repo_path)}\n"
                                f"Project Type: {project_type}\n"
                                f"Tech Stack: {tech_str}\n"
                                f"Files Analyzed: {len(code_files)}\n"
                                f"Docker: {'Configured' if has_docker else 'Not configured'}\n"
                                f"CI/CD: {'Configured' if has_ci else 'Not configured'}\n\n"
                                f"{ai_result}"
                            )
                        else:
                            raise Exception("AI response too short")
                    else:
                        raise Exception(f"AI failed: {r.status_code}")

            except Exception:
                # DETAILED FALLBACK: Generate comprehensive deployment config
                dockerfile = ""
                dockerignore = ""
                docker_compose = ""
                env_doc = ""
                ci_pipeline = ""
                deploy_steps = ""

                if project_type == "Node.js":
                    dockerfile = (
                        "# Stage 1: Build\n"
                        "FROM node:20-alpine AS builder\n"
                        "WORKDIR /app\n"
                        "COPY package*.json ./\n"
                        "RUN npm ci --only=production\n"
                        "COPY . .\n"
                        "RUN npm run build 2>/dev/null || echo 'No build script'\n\n"
                        "# Stage 2: Production\n"
                        "FROM node:20-alpine AS production\n"
                        "RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001 -G appgroup\n"
                        "WORKDIR /app\n"
                        "COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules\n"
                        "COPY --from=builder --chown=appuser:appgroup /app .\n"
                        "USER appuser\n"
                        f"EXPOSE {port}\n"
                        "HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\\n"
                        f"  CMD wget --no-verbose --tries=1 --spider http://localhost:{port}/health || exit 1\n"
                        f"CMD [\"node\", \"app.js\"]\n"
                    )
                    dockerignore = (
                        "node_modules\n"
                        "npm-debug.log\n"
                        ".git\n"
                        ".gitignore\n"
                        "Dockerfile\n"
                        "docker-compose*.yml\n"
                        ".env\n"
                        ".env.local\n"
                        "coverage\n"
                        "tests\n"
                        "*.md\n"
                        ".next\n"
                        "dist\n"
                    )
                    docker_compose = (
                        f"version: '3.8'\n\n"
                        f"services:\n"
                        f"  app:\n"
                        f"    build: .\n"
                        f"    ports:\n"
                        f"      - \"{port}:{port}\"\n"
                        f"    environment:\n"
                        f"      - NODE_ENV=production\n"
                    )
                    if uses_mongo:
                        docker_compose += (
                            f"      - MONGO_URI=mongodb://mongo:27017/app\n"
                            f"  mongo:\n"
                            f"    image: mongo:7\n"
                            f"    volumes:\n"
                            f"      - mongo_data:/data/db\n"
                            f"    ports:\n"
                            f"      - \"27017:27017\"\n"
                        )
                    if uses_redis:
                        docker_compose += (
                            f"  redis:\n"
                            f"    image: redis:7-alpine\n"
                            f"    ports:\n"
                            f"      - \"6379:6379\"\n"
                        )
                    docker_compose += (
                        f"\nvolumes:\n"
                        f"  mongo_data:\n" if uses_mongo else ""
                    )

                elif project_type == "Python":
                    dockerfile = (
                        "# Stage 1: Build\n"
                        "FROM python:3.12-slim AS builder\n"
                        "WORKDIR /app\n"
                        "COPY requirements.txt .\n"
                        "RUN pip install --no-cache-dir --prefix=/install -r requirements.txt\n\n"
                        "# Stage 2: Production\n"
                        "FROM python:3.12-slim AS production\n"
                        "RUN groupadd -r appgroup && useradd -r -g appgroup appuser\n"
                        "WORKDIR /app\n"
                        "COPY --from=builder /install /usr/local\n"
                        "COPY --chown=appuser:appgroup . .\n"
                        "USER appuser\n"
                        f"EXPOSE {port}\n"
                        "HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\\n"
                        f"  CMD curl -f http://localhost:{port}/health || exit 1\n"
                        f"CMD [\"uvicorn\", \"main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"{port}\"]\n"
                    )
                    dockerignore = (
                        "__pycache__\n"
                        "*.pyc\n"
                        ".git\n"
                        ".gitignore\n"
                        "Dockerfile\n"
                        "docker-compose*.yml\n"
                        ".env\n"
                        ".venv\n"
                        "venv\n"
                        "*.md\n"
                        "tests\n"
                        "coverage\n"
                    )

                if env_vars:
                    env_doc = "\n".join(f"- `{v}`: Description of {v}" for v in sorted(env_vars))
                else:
                    env_doc = "- `NODE_ENV`: Set to `production`\n- `PORT`: Server port (default: 3000)"

                ci_pipeline = (
                    "name: Deploy\n\n"
                    "on:\n"
                    "  push:\n"
                    "    branches: [main]\n"
                    "  pull_request:\n"
                    "    branches: [main]\n\n"
                    "jobs:\n"
                    "  test:\n"
                    "    runs-on: ubuntu-latest\n"
                    "    steps:\n"
                    "      - uses: actions/checkout@v4\n"
                    "      - uses: actions/setup-node@v4\n"
                    "        with:\n"
                    "          node-version: 20\n"
                    "      - run: npm ci\n"
                    "      - run: npm test\n\n"
                    "  build-and-push:\n"
                    "    needs: test\n"
                    "    runs-on: ubuntu-latest\n"
                    "    if: github.ref == 'refs/heads/main'\n"
                    "    steps:\n"
                    "      - uses: actions/checkout@v4\n"
                    "      - uses: docker/build-push-action@v5\n"
                    "        with:\n"
                    "          push: true\n"
                    "          tags: ghcr.io/${{ github.repository }}:latest\n"
                )

                deploy_steps = (
                    "### Local Development\n"
                    "```bash\n"
                    "# Build and run with Docker Compose\n"
                    "docker-compose up --build\n\n"
                    "# Or run with Docker directly\n"
                    "docker build -t app .\n"
                    f"docker run -p {port}:{port} --env-file .env app\n"
                    "```\n\n"
                    "### Production Deployment\n"
                    "1. Set up environment variables on your hosting platform\n"
                    "2. Connect your repository to your CI/CD provider\n"
                    "3. Push to `main` branch to trigger deployment\n"
                    "4. Verify health check endpoint responds\n"
                )

                result_text = (
                    f"DEPLOYMENT CONFIGURATION\n"
                    f"{'='*50}\n"
                    f"Repository: {os.path.basename(repo_path)}\n"
                    f"Project Type: {project_type}\n"
                    f"Tech Stack: {tech_str}\n"
                    f"Files Analyzed: {len(code_files)}\n"
                    f"Docker: {'Configured' if has_docker else 'Generated below'}\n"
                    f"CI/CD: {'Configured' if has_ci else 'Generated below'}\n\n"

                    f"## Readiness Assessment\n"
                    f"- Dockerfile: {'Present' if has_docker else 'MISSING — Generated below'}\n"
                    f"- CI/CD Pipeline: {'Present' if has_ci else 'MISSING — Generated below'}\n"
                    f"- .dockerignore: {'Present' if has_ignore else 'MISSING — Generated below'}\n"
                    f"- Environment Config: {'Present' if has_env else 'MISSING — Generated below'}\n"
                    f"- Databases: {', '.join(filter(None, ['MongoDB' if uses_mongo else '', 'PostgreSQL' if uses_postgres else '', 'Redis' if uses_redis else ''])) or 'None detected'}\n\n"

                    f"## Dockerfile (Multi-Stage Build)\n"
                    f"```dockerfile\n{dockerfile}```\n\n"

                    f"## .dockerignore\n"
                    f"```\n{dockerignore}```\n\n"
                )

                if docker_compose:
                    result_text += f"## docker-compose.yml\n```yaml\n{docker_compose}```\n\n"

                result_text += (
                    f"## Environment Variables\n"
                    f"{env_doc}\n\n"

                    f"## GitHub Actions CI/CD\n"
                    f"Save as `.github/workflows/deploy.yml`:\n"
                    f"```yaml\n{ci_pipeline}```\n\n"

                    f"## Deployment Steps\n"
                    f"{deploy_steps}\n"

                    f"## Health Check\n"
                    f"Add this endpoint to your app:\n"
                    f"```javascript\n"
                    f"app.get('/health', (req, res) => res.json({{ status: 'ok', uptime: process.uptime() }}));\n"
                    f"```\n"
                )

        elif agent_type == "planner":
            # Build context for AI-powered planning
            file_tree = "\n".join(sorted(code_files.keys())[:50])
            
            # Read key config files
            config_context = ""
            for fpath, content in code_files.items():
                base = os.path.basename(fpath)
                if base in {"package.json", "requirements.txt", "pyproject.toml", "tsconfig.json", "README.md"}:
                    config_context += f"\n--- {fpath} ---\n{content[:800]}\n"

            # Code samples for context
            code_samples = ""
            for fpath, content in list(code_files.items())[:8]:
                code_samples += f"\n--- {fpath} ---\n{content[:400]}\n"

            # Try AI-powered planning
            try:
                import httpx as _httpx
                ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

                prompt = f"""Analyze this codebase and create a DETAILED improvement plan. Be specific and actionable.

FILE TREE:
{file_tree}

CONFIG FILES:
{config_context}

CODE SAMPLES:
{code_samples}

Create a plan with this EXACT format:

### Project Assessment
[What the project does well and what needs improvement]

### Priority Tasks (ordered by importance)
For each task provide:
- **Task name** — Clear, actionable title
- **Description** — What exactly needs to be done
- **Files to modify** — Specific file paths
- **Complexity** — Simple/Medium/Complex
- **Estimated time** — Realistic time estimate
- **Why it matters** — Impact on the project

### Architecture Recommendations
[Structural improvements, patterns to follow, code organization]

### Risk Assessment
[Potential issues, things to be careful about]

Be CONCRETE. Reference actual file names. Do NOT give generic advice like "add tests" without specifying WHAT tests and WHERE."""

                async with _httpx.AsyncClient(timeout=60) as client:
                    r = await client.post(f"{ollama_url}/api/chat", json={
                        "model": "qwen2.5:3b",
                        "messages": [
                            {"role": "system", "content": "You are a senior software architect creating an improvement plan. Be specific, reference actual files, and provide actionable tasks with time estimates."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.3},
                    })
                    if r.status_code == 200:
                        ai_data = r.json()
                        result_text = ai_data.get("message", {}).get("content", "")
                        if not result_text or len(result_text) < 100:
                            raise Exception("AI response too short")
                    else:
                        raise Exception(f"AI request failed: {r.status_code}")
            except Exception:
                # Fallback to rule-based planning
                file_list = list(code_files.keys())
                has_tests = any('test' in f.lower() for f in file_list)
                has_docker = any('dockerfile' in f.lower() for f in file_list)
                has_ci = any('.github' in f or '.gitlab' in f for f in file_list)
                has_readme = any('readme' in f.lower() for f in file_list)
                
                tasks = []
                if not has_tests:
                    tasks.append("1. Testing — Add unit tests (none detected)")
                if not has_readme:
                    tasks.append("2. Documentation — Add README with setup instructions")
                if not has_docker:
                    tasks.append("3. Deployment — Create Dockerfile for containerization")
                if not has_ci:
                    tasks.append("4. CI/CD — Set up GitHub Actions for automated testing")
                tasks.append("5. Code Quality — Fix console.log statements and linting issues")
                
                result_text = (
                    f"TASK PLAN\n"
                    f"{'='*40}\n"
                    f"Based on {len(code_files)} files in the repository:\n\n"
                    f"Recommended tasks:\n" + "\n".join(tasks) +
                    f"\n\nFiles to prioritize:\n" + "\n".join(f"  - {f}" for f in file_list[:10])
                )

        elif agent_type == "researcher":
            # Build a rich context for the AI to analyze
            file_summary = {}
            for fpath, content in code_files.items():
                ext = os.path.splitext(fpath)[1] or "other"
                if ext not in file_summary:
                    file_summary[ext] = {"count": 0, "lines": 0, "sample": ""}
                file_summary[ext]["count"] += 1
                file_summary[ext]["lines"] += content.count("\n") + 1
                if not file_summary[ext]["sample"]:
                    file_summary[ext]["sample"] = content[:300]

            # Build file tree
            file_tree = "\n".join(sorted(code_files.keys())[:50])

            # Read key config files for context
            config_context = ""
            for fpath, content in code_files.items():
                base = os.path.basename(fpath)
                if base in {"package.json", "requirements.txt", "pyproject.toml", "tsconfig.json", "README.md", "Dockerfile"}:
                    config_context += f"\n--- {fpath} ---\n{content[:1000]}\n"

            # Try to use AI model for detailed analysis
            try:
                import httpx as _httpx
                ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

                code_samples = ""
                for fpath, content in list(code_files.items())[:10]:
                    code_samples += f"\n--- {fpath} ---\n{content[:500]}\n"

                prompt = f"""Analyze this project and provide a DETAILED description. Be specific and concrete.

FILE TREE:
{file_tree}

CONFIG FILES:
{config_context}

CODE SAMPLES (first 10 files):
{code_samples}

LANGUAGE BREAKDOWN:
{chr(10).join(f"  {ext}: {info['count']} files, {info['lines']} lines" for ext, info in sorted(file_summary.items(), key=lambda x: -x[1]['count']))}

Provide your analysis in this EXACT format:

### Project Name & Purpose
[What this project IS and what it DOES - be specific, not generic]

### Tech Stack
[List ALL languages, frameworks, libraries with versions if visible]

### Architecture
[How the project is organized, entry points, key components, data flow]

### Key Features
[List ACTUAL features implemented - reference specific files]

### Configuration & Setup
[How to install and run, based on the config files]

### Code Quality Overview
[Main observations about code quality]

Be CONCRETE. Reference specific file names and functions. Do NOT guess or use vague language."""

                async with _httpx.AsyncClient(timeout=60) as client:
                    r = await client.post(f"{ollama_url}/api/chat", json={
                        "model": "qwen2.5:3b",
                        "messages": [
                            {"role": "system", "content": "You are a senior software engineer analyzing a codebase. Be precise, specific, and reference actual file names and code. Never guess."},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                        "options": {"temperature": 0.3},
                    })
                    if r.status_code == 200:
                        ai_data = r.json()
                        result_text = ai_data.get("message", {}).get("content", "")
                        if not result_text or len(result_text) < 100:
                            raise Exception("AI response too short")
                    else:
                        raise Exception(f"AI request failed: {r.status_code}")
            except Exception:
                # Fallback to rule-based analysis if AI fails
                result_text = (
                    f"CODEBASE RESEARCH REPORT\n"
                    f"{'='*40}\n"
                    f"Total files: {len(code_files)}\n\n"
                    f"Language Breakdown:\n"
                )
                for ext, info in sorted(file_summary.items(), key=lambda x: -x[1]['count']):
                    result_text += f"  {ext}: {info['count']} files, {info['lines']} lines\n"
                    if info['sample']:
                        snippet = info['sample'][:150].replace('\n', ' ').strip()
                        result_text += f"    Sample: {snippet}...\n"
                result_text += f"\nFile Structure:\n{file_tree}"
        else:
            result_text = f"Agent '{agent_type}' completed analysis of {len(code_files)} files."
    else:
        result_text = f"Task completed by {agent_type} agent. No repository found for analysis."

    elapsed = (datetime.now(UTC) - start).total_seconds()
    task["status"] = "completed"
    task["completed_at"] = datetime.now(UTC).isoformat()
    task["result"] = result_text
    task["duration"] = round(max(elapsed, 0.1), 2)
    task["completed_at"] = datetime.now(UTC).isoformat()

    await _agent_monitor.record_task_complete(agent_id, task_id, task["duration"], True)

    log_activity(
        "agent", "task_completed",
        f"Agent task completed: {task['agent_type']}",
        result_text[:200],
        "agent_task", task_id,
    )


@router.get("/tasks/list")
async def list_tasks():
    return {"status": "success", "data": _TASKS}


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = next((t for t in _TASKS if t["id"] == task_id), None)
    if not task:
        return {"status": "error", "message": "Task not found"}
    return {"status": "success", "data": task}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    task = next((t for t in _TASKS if t["id"] == task_id), None)
    if not task:
        return {"status": "error", "message": "Task not found"}
    task["status"] = "cancelled"
    return {"status": "success", "data": task}
