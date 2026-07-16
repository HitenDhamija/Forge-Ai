"""Feature Suggestion Planner — analyzes codebase and suggests features."""

import uuid
import os
import json
import logging
from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.api.v1.activity_store import log_activity

logger = logging.getLogger("planner")
router = APIRouter(prefix="/planner", tags=["Planner"])

_plans: list[dict[str, Any]] = []


class PlanRequest(BaseModel):
    objective: str
    repository_id: str | None = None
    repository_name: str | None = None
    additional_context: str | None = None
    constraints: list[str] | None = None


def _scan_repo(repository_id: str | None = None, repository_name: str | None = None) -> dict[str, Any]:
    """Scan repository and return structured info."""
    repo_path = None
    repo_name = "Unknown"

    try:
        from app.api.v1.repositories_standalone import _repositories
        repos = list(_repositories.values())
        # 1. Try matching by ID
        if repository_id:
            repo = _repositories.get(repository_id)
            if repo:
                repo_path = getattr(repo, "local_path", None)
                repo_name = getattr(repo, "name", "Unknown")
        # 2. Try matching by name
        if not repo_path and repository_name:
            rn = repository_name.lower()
            for r in repos:
                r_name = getattr(r, "name", "").lower()
                if r_name and (rn in r_name or r_name in rn):
                    repo_path = getattr(r, "local_path", None)
                    repo_name = getattr(r, "name", "Unknown")
                    break
        # 3. Fallback to most recently modified repo
        if not repo_path and repos:
            best = None
            best_mtime = -1
            for r in repos:
                lp = getattr(r, "local_path", None)
                if lp and os.path.isdir(lp):
                    mt = os.path.getmtime(lp)
                    if mt > best_mtime:
                        best_mtime = mt
                        best = r
            if best:
                repo_path = getattr(best, "local_path", None)
                repo_name = getattr(best, "name", "Unknown")
    except Exception:
        pass

    if not repo_path:
        temp_repos_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "forgeai", "repos")
        if os.path.isdir(temp_repos_dir):
            folders = []
            for folder_name in os.listdir(temp_repos_dir):
                folder_path = os.path.join(temp_repos_dir, folder_name)
                if os.path.isdir(folder_path):
                    folders.append((folder_path, os.path.getmtime(folder_path)))
            folders.sort(key=lambda x: -x[1])
            if folders:
                code_path = folders[0][0]
                subdirs = [d for d in os.listdir(code_path)
                          if os.path.isdir(os.path.join(code_path, d)) and d != ".git"]
                if subdirs:
                    code_path = os.path.join(code_path, subdirs[0])
                if os.path.isdir(code_path):
                    repo_path = code_path
                    repo_name = os.path.basename(code_path)

    if not repo_path or not os.path.isdir(repo_path):
        return {"name": repo_name, "path": None, "files": [], "configs": {}, "code_summary": ""}

    SKIP = {"node_modules", ".venv", "__pycache__", ".git", "dist", "build", ".next", "coverage", ".cache", "chroma_db"}

    all_files = []
    configs = {}
    route_files = []
    model_files = []
    code_files = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, repo_path)
            ext = os.path.splitext(fname)[1].lower()

            all_files.append(rel)

            try:
                if fname == "package.json":
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        configs["package.json"] = f.read()[:2000]
                elif fname in ("requirements.txt", "pyproject.toml"):
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        configs["python_deps"] = f.read()[:1000]
                elif fname == "README.md":
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        configs["readme"] = f.read()[:2000]
                elif "route" in rel.lower() or "router" in rel.lower() or "api" in rel.lower():
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        route_files.append(f"## {rel}\n{f.read()[:600]}")
                elif any(x in rel.lower() for x in ["model", "schema", "types"]):
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        model_files.append(f"## {rel}\n{f.read()[:600]}")
                elif ext in (".py", ".ts", ".js", ".jsx", ".tsx") and len(code_files) < 6:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        code_files.append(f"## {rel}\n{f.read()[:500]}")
            except Exception:
                pass

    return {
        "name": repo_name,
        "path": repo_path,
        "files": all_files[:80],
        "configs": configs,
        "routes": route_files[:6],
        "models": model_files[:6],
        "code": code_files[:4],
    }


async def _suggest_features_ai(objective: str, repo_info: dict[str, Any]) -> list[dict[str, Any]] | None:
    """Call AI to analyze the project and respond based on question type."""
    try:
        import httpx

        # Build context string
        ctx = f"Project: {repo_info['name']}\n\n"
        ctx += f"Files ({len(repo_info['files'])}):\n" + "\n".join(repo_info["files"][:50]) + "\n\n"

        for key, val in repo_info["configs"].items():
            ctx += f"--- {key} ---\n{val}\n\n"

        if repo_info.get("routes"):
            ctx += "API ROUTES:\n" + "\n".join(repo_info["routes"]) + "\n\n"

        if repo_info.get("models"):
            ctx += "DATA MODELS:\n" + "\n".join(repo_info["models"]) + "\n\n"

        if repo_info.get("code"):
            ctx += "CODE:\n" + "\n".join(repo_info["code"]) + "\n\n"

        # Increased context for better analysis
        if len(ctx) > 10000:
            ctx = ctx[:10000]

        # Detect question type
        obj_lower = objective.lower()
        question_type = "describe"  # default

        describe_keywords = ["what is", "what does", "about", "explain", "describe", "tell me about", "overview"]
        review_keywords = ["review", "quality", "issues", "problems", "bugs", "security", "audit", "bad"]
        fix_keywords = ["fix", "repair", "solve", "correct", "resolve"]
        plan_keywords = ["plan", "how to", "implement", "add", "create", "build", "setup", "deploy"]
        suggest_keywords = ["suggest", "improvement", "feature", "idea", "recommend", "could add"]

        if any(k in obj_lower for k in describe_keywords):
            question_type = "describe"
        elif any(k in obj_lower for k in review_keywords):
            question_type = "review"
        elif any(k in obj_lower for k in fix_keywords):
            question_type = "fix"
        elif any(k in obj_lower for k in suggest_keywords):
            question_type = "suggest"
        elif any(k in obj_lower for k in plan_keywords):
            question_type = "plan"

        logger.info(f"Question type detected: {question_type} for objective: {objective[:50]}")

        # Build prompt based on question type
        if question_type == "describe":
            prompt = f"""Analyze this software project and describe it in detail.

{ctx}

User asks: {objective}

Provide a comprehensive description in this EXACT format:

### Project Name & Purpose
- **What it IS:** (web app, CLI tool, mobile app, etc.)
- **What it DOES:** (core functionality in 1-2 sentences)
- **Who it's FOR:** (target users)

### Tech Stack
- Languages with approximate percentages
- Frameworks and libraries
- Build tools

### Architecture
- How the code is organized (folder structure)
- Entry points (main files)
- Key components and how they connect

### Key Features
- List the ACTUAL features implemented (reference specific files)

### Code Quality Summary
- Total files, lines of code
- Any obvious patterns or anti-patterns

Be SPECIFIC. Reference actual file names from the project. Do NOT give generic advice."""

        elif question_type == "review":
            prompt = f"""Perform a detailed code review of this project.

{ctx}

User asks: {objective}

Review the code and provide findings in this format:

### Security Issues
- List any security vulnerabilities found (XSS, injection, hardcoded secrets, etc.)
- Reference specific file:line

### Code Quality Issues
- Anti-patterns, bad practices, code smells
- Reference specific file:line

### Performance Issues
- Blocking I/O, N+1 queries, memory leaks
- Reference specific file:line

### Architecture Issues
- Single Responsibility violations, tight coupling
- Reference specific file:line

### Positive Observations
- What's done well

### Recommendations
- Prioritized list of fixes with file paths

Be SPECIFIC. Reference actual file names and line numbers. Count issues by severity."""

        elif question_type == "fix":
            prompt = f"""Analyze this project and identify issues that need fixing.

{ctx}

User asks: {objective}

Find and list issues in this format:

### Critical Issues (must fix)
- Issue description with file:line reference
- Why it's critical
- How to fix it

### Warnings (should fix)
- Issue description with file:line reference
- Why it matters
- How to fix it

### Suggestions (nice to have)
- Improvement ideas with file references

For each issue, provide:
- Exact file path and line number
- The problematic code snippet
- The fix (specific code change)

Be SPECIFIC. Reference actual files from the project."""

        else:  # plan or suggest
            prompt = f"""Analyze this project and suggest features IMPROVEMENTS specific to what it actually does.

{ctx}

User asks: {objective}

IMPORTANT: Your suggestions MUST be specific to THIS project's purpose. Do NOT suggest generic features like "add auth" or "add notifications" unless the project clearly needs them.

Return a JSON array of 3-5 suggestions. Each object must have:
- "title": Short feature name
- "description": 2-3 sentences explaining what and why
- "priority": "high", "medium", or "low"
- "impact": "high", "medium", or "low"
- "effort": "small", "medium", or "large"
- "category": relevant category
- "files_to_modify": array of 2-3 existing file paths
- "files_to_create": array of 1-2 new file paths
- "implementation_steps": array of 3-4 specific steps
- "user_benefit": 1-2 sentences
- "technical_notes": 1-2 sentences

Return ONLY the JSON array, no markdown."""

        # System prompt based on question type
        system_prompts = {
            "describe": "You are a senior developer analyzing a codebase. Be specific and reference actual files. Give concrete details, not generic descriptions.",
            "review": "You are a senior code reviewer. Find real issues with file:line references. Be thorough but fair.",
            "fix": "You are a debugging expert. Find real bugs and issues with exact file:line references. Provide specific fixes.",
            "plan": "You are a product manager who deeply understands the codebase. Suggest features that make sense for THIS specific project.",
            "suggest": "You are a product manager who deeply understands the codebase. Suggest improvements that make sense for THIS specific project.",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post("http://localhost:11434/api/chat", json={
                "model": "qwen2.5:3b",
                "messages": [
                    {"role": "system", "content": system_prompts[question_type]},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 2000},
            })

            if r.status_code == 200:
                content = r.json().get("message", {}).get("content", "")
                content = content.strip()

                # For describe/review/fix, return as-is wrapped in a feature object
                if question_type in ("describe", "review", "fix"):
                    return [{
                        "title": objective,
                        "description": content,
                        "priority": "high",
                        "impact": "high",
                        "effort": "medium",
                        "category": question_type.title(),
                        "files_to_modify": [],
                        "files_to_create": [],
                        "implementation_steps": [],
                        "user_benefit": "",
                        "technical_notes": "",
                        "_raw_response": True,  # Flag that this is a raw text response
                    }]

                # For plan/suggest, parse JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                start = content.find("[")
                end = content.rfind("]") + 1
                if start >= 0 and end > start:
                    content = content[start:end]

                features = json.loads(content)
                if isinstance(features, list):
                    logger.info(f"AI returned {len(features)} features")
                    return features
    except Exception as e:
        logger.error(f"AI feature suggestion failed: {e}")
    return None


def _build_plan_from_features(objective: str, features: list[dict[str, Any]], repo_name: str) -> dict[str, Any]:
    """Convert AI feature suggestions into a plan format the frontend can display."""
    plan_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    tasks = []
    risks = []
    arch_notes = []
    all_files = set()

    # Handle raw text response (describe/review/fix)
    if features and features[0].get("_raw_response"):
        raw = features[0]
        return {
            "id": plan_id,
            "objective": objective,
            "intent": "coding",
            "complexity": "medium",
            "tasks": [{
                "id": str(uuid.uuid4()),
                "title": raw["title"],
                "description": raw["description"],
                "dependencies": [],
                "estimated_time_minutes": 0,
                "complexity": "simple",
                "required_skills": [],
                "required_context": [],
                "priority": "high",
                "status": "completed",
                "files_affected": [],
                "notes": raw["description"],
            }],
            "risks": [],
            "dependencies": [],
            "architecture_notes": [],
            "files_affected": [],
            "estimated_duration_minutes": 0,
            "approval_required": False,
            "created_at": now,
            "repository_name": repo_name,
            "context_summary": f"Analysis of: {objective}",
            "_is_analysis": True,  # Flag for frontend to display differently
        }

    for i, feat in enumerate(features):
        task_id = str(uuid.uuid4())

        # Build detailed notes string with all extra info
        details_parts = []
        if feat.get("implementation_steps"):
            details_parts.append("STEPS: " + " | ".join(feat["implementation_steps"]))
        if feat.get("user_benefit"):
            details_parts.append("BENEFIT: " + feat["user_benefit"])
        if feat.get("technical_notes"):
            details_parts.append("TECH: " + feat["technical_notes"])
        details_parts.append(f"Category: {feat.get('category', 'General')}")
        details_parts.append(f"Impact: {feat.get('impact', 'medium')}")
        if feat.get("files_to_create"):
            details_parts.append(f"New files: {', '.join(feat['files_to_create'])}")

        tasks.append({
            "id": task_id,
            "title": feat.get("title", f"Feature {i+1}"),
            "description": feat.get("description", ""),
            "dependencies": [tasks[-1]["id"]] if i > 0 and tasks else [],
            "estimated_time_minutes": {"small": 30, "medium": 60, "large": 120}.get(feat.get("effort", "medium"), 60),
            "complexity": {"small": "simple", "medium": "medium", "large": "complex"}.get(feat.get("effort", "medium"), "medium"),
            "required_skills": [],
            "required_context": [],
            "priority": feat.get("priority", "medium"),
            "status": "pending",
            "files_affected": feat.get("files_to_modify", []),
            "notes": "\n".join(details_parts),
        })

        # Collect files
        for f in feat.get("files_to_modify", []):
            all_files.add(f)
        for f in feat.get("files_to_create", []):
            all_files.add(f)

        # Risk for high-effort features
        if feat.get("effort") == "large":
            risks.append({
                "level": "medium",
                "category": "technical",
                "description": f"'{feat.get('title')}' is a large feature — may take longer than estimated",
                "mitigation": "Break into smaller phases, test incrementally",
                "affected_tasks": [task_id],
            })

        # Architecture note per feature
        arch_notes.append({
            "category": feat.get("category", "General"),
            "content": feat.get("description", ""),
            "related_tasks": [task_id],
        })

    if not risks:
        risks.append({
            "level": "low",
            "category": "technical",
            "description": "New features should be tested thoroughly before deployment",
            "mitigation": "Run full test suite and do manual QA",
            "affected_tasks": [tasks[0]["id"]] if tasks else [],
        })

    total_time = sum(t["estimated_time_minutes"] for t in tasks)

    return {
        "id": plan_id,
        "objective": objective,
        "intent": "coding",
        "complexity": "medium",
        "tasks": tasks,
        "risks": risks,
        "dependencies": [
            {
                "type": "internal",
                "name": "existing-codebase",
                "path": None,
                "required_by": [tasks[0]["id"]] if tasks else [],
                "exists": True,
            }
        ],
        "architecture_notes": arch_notes,
        "files_affected": list(all_files),
        "estimated_duration_minutes": total_time,
        "approval_required": True,
        "created_at": now,
        "repository_name": repo_name,
        "context_summary": f"Feature suggestions for: {objective}",
    }


def _plan_to_history(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": plan["id"],
        "objective": plan["objective"],
        "intent": plan["intent"],
        "complexity": plan["complexity"],
        "task_count": len(plan["tasks"]),
        "risk_count": len(plan["risks"]),
        "estimated_duration_minutes": plan["estimated_duration_minutes"],
        "created_at": plan["created_at"],
        "repository_name": plan.get("repository_name"),
    }


@router.post("/plan")
async def create_plan(request: PlanRequest):
    logger.info(f"Plan request: {request.objective[:60]}")

    # Scan repo
    repo_info = _scan_repo(request.repository_id, request.repository_name)
    logger.info(f"Scanned repo: {repo_info['name']} ({len(repo_info['files'])} files)")

    # Get AI suggestions
    features = await _suggest_features_ai(request.objective, repo_info)

    if features:
        logger.info(f"Building plan from {len(features)} AI features")
        plan = _build_plan_from_features(request.objective, features, repo_info["name"])
    else:
        logger.warning("AI failed, using built-in suggestions")
        plan = _build_fallback_plan(request.objective, repo_info["name"])

    _plans.insert(0, plan)

    log_activity(
        "planner", "plan_created",
        f"Created plan: {request.objective[:50]}",
        f"Plan with {len(plan['tasks'])} features",
        "plan", plan["id"],
    )

    return {"status": "success", "data": plan}


def _build_fallback_plan(objective: str, repo_name: str) -> dict[str, Any]:
    """Smart fallback when AI is unavailable — analyzes the question type."""
    plan_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    obj_lower = objective.lower()

    # Detect question type for fallback
    if any(k in obj_lower for k in ["what is", "what does", "about", "explain", "describe"]):
        # Description request — give a template response
        description = f"""### Project: {repo_name}

**What I can tell you from the file structure:**

This project is located at the repository path. To get a detailed analysis, please:

1. Ensure Ollama is running (`ollama serve`)
2. Ask a specific question like:
   - "What files are in this project?"
   - "What frameworks does it use?"
   - "Review the code quality"

**Quick Info:**
- Repository: {repo_name}
- For detailed analysis, the AI needs Ollama running locally.

**Tip:** You can also check the Repository page for basic file/language info."""
        return {
            "id": plan_id,
            "objective": objective,
            "intent": "coding",
            "complexity": "simple",
            "tasks": [{
                "id": str(uuid.uuid4()),
                "title": f"Analysis: {objective}",
                "description": description,
                "dependencies": [],
                "estimated_time_minutes": 0,
                "complexity": "simple",
                "required_skills": [],
                "required_context": [],
                "priority": "high",
                "status": "completed",
                "files_affected": [],
                "notes": description,
            }],
            "risks": [],
            "dependencies": [],
            "architecture_notes": [],
            "files_affected": [],
            "estimated_duration_minutes": 0,
            "approval_required": False,
            "created_at": now,
            "repository_name": repo_name,
            "context_summary": f"Analysis of: {objective}",
            "_is_analysis": True,
        }

    # Default: generic feature suggestions
    tasks = [
        {
            "id": str(uuid.uuid4()),
            "title": "User Authentication Enhancement",
            "description": "Add OAuth2 social login (Google, GitHub) and two-factor authentication for better security. Users can sign in with one click and enable 2FA for extra protection.",
            "dependencies": [],
            "estimated_time_minutes": 90,
            "complexity": "medium",
            "required_skills": ["authentication"],
            "required_context": [],
            "priority": "high",
            "status": "pending",
            "files_affected": [],
            "notes": "STEPS: Install OAuth2 library (passport.js or authlib) | Add login/callback routes | Create user session management | Add 2FA setup page\nBENEFIT: Users can sign in instantly with Google/GitHub, reducing signup friction. 2FA protects accounts from unauthorized access.\nTECH: Integrate with existing user model, add OAuth provider config to environment variables\nCategory: Security | Impact: high | New files: src/routes/auth.ts, src/middleware/session.ts",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Real-time Notifications",
            "description": "Add push notifications for messages, updates, and important events using WebSocket. Users get instant alerts without refreshing the page.",
            "dependencies": [],
            "estimated_time_minutes": 60,
            "complexity": "medium",
            "required_skills": ["websockets"],
            "required_context": [],
            "priority": "high",
            "status": "pending",
            "files_affected": [],
            "notes": "STEPS: Set up WebSocket server | Create notification event system | Add notification preferences | Build notification UI component\nBENEFIT: Users stay informed about messages, booking updates, and reviews in real-time, improving engagement.\nTECH: Use Socket.io or native WebSocket, store notifications in database for persistence\nCategory: UX | Impact: high | New files: src/services/notifications.ts, src/components/NotificationBell.tsx",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Advanced Search & Filtering",
            "description": "Add full-text search with filters for category, price, location, and date ranges. Users can quickly find exactly what they're looking for.",
            "dependencies": [],
            "estimated_time_minutes": 60,
            "complexity": "medium",
            "required_skills": ["search"],
            "required_context": [],
            "priority": "medium",
            "status": "pending",
            "files_affected": [],
            "notes": "STEPS: Add search index to database | Create filter components | Implement server-side search endpoint | Add search UI with autocomplete\nBENEFIT: Users can find relevant listings 3x faster, increasing conversion and satisfaction.\nTECH: Use database full-text search or Elasticsearch, implement pagination for large result sets\nCategory: Search | Impact: high | New files: src/routes/search.ts, src/components/SearchFilters.tsx",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Analytics Dashboard",
            "description": "Add admin dashboard with usage analytics, user metrics, and content performance charts. Admins can track growth and identify issues.",
            "dependencies": [],
            "estimated_time_minutes": 90,
            "complexity": "complex",
            "required_skills": ["analytics"],
            "required_context": [],
            "priority": "medium",
            "status": "pending",
            "files_affected": [],
            "notes": "STEPS: Define analytics data models | Create data collection service | Build dashboard UI with charts | Add export functionality\nBENEFIT: Admins gain visibility into user behavior, content performance, and system health for data-driven decisions.\nTECH: Use Chart.js or Recharts for visualization, aggregate data nightly for performance\nCategory: Analytics | Impact: medium | New files: src/routes/admin/analytics.ts, src/components/AnalyticsChart.tsx",
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Mobile Responsiveness",
            "description": "Optimize all pages for mobile devices with responsive design and touch-friendly UI. Over 60% of users browse on phones.",
            "dependencies": [],
            "estimated_time_minutes": 60,
            "complexity": "medium",
            "required_skills": ["css", "responsive"],
            "required_context": [],
            "priority": "medium",
            "status": "pending",
            "files_affected": [],
            "notes": "STEPS: Audit current pages for mobile issues | Add responsive breakpoints | Optimize touch targets | Test on real devices\nBENEFIT: Mobile users get a native-like experience, reducing bounce rate and increasing mobile conversions.\nTECH: Use CSS Grid/Flexbox, implement mobile-first design, add viewport meta tags\nCategory: Mobile | Impact: high | New files: src/styles/mobile.css",
        },
    ]

    return {
        "id": plan_id,
        "objective": objective,
        "intent": "coding",
        "complexity": "medium",
        "tasks": tasks,
        "risks": [
            {
                "level": "low",
                "category": "technical",
                "description": "New features should be tested before deployment",
                "mitigation": "Run full test suite and do manual QA",
                "affected_tasks": [tasks[0]["id"]],
            }
        ],
        "dependencies": [
            {
                "type": "internal",
                "name": "existing-codebase",
                "path": None,
                "required_by": [tasks[0]["id"]],
                "exists": True,
            }
        ],
        "architecture_notes": [
            {
                "category": "Security",
                "content": "Implement proper authentication middleware and rate limiting",
                "related_tasks": [tasks[0]["id"]],
            },
            {
                "category": "Performance",
                "content": "Add caching layer for search results and frequently accessed data",
                "related_tasks": [tasks[2]["id"]],
            },
        ],
        "files_affected": [],
        "estimated_duration_minutes": 360,
        "approval_required": True,
        "created_at": now,
        "repository_name": repo_name,
        "context_summary": f"Feature suggestions for: {objective}",
    }


@router.get("/history")
async def list_history():
    history = [_plan_to_history(p) for p in _plans]
    return {"status": "success", "data": history}


@router.get("/plans")
async def list_plans():
    history = [_plan_to_history(p) for p in _plans]
    return {"status": "success", "data": history}


@router.get("/{plan_id}")
async def get_plan(plan_id: str):
    plan = next((p for p in _plans if p["id"] == plan_id), None)
    if not plan:
        return {"status": "error", "message": "Plan not found"}
    return {"status": "success", "data": plan}


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str):
    global _plans
    before = len(_plans)
    _plans = [p for p in _plans if p["id"] != plan_id]
    if len(_plans) == before:
        return {"status": "error", "message": "Plan not found"}
    return {"status": "success", "message": "Plan deleted"}
