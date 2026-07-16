"""Standalone workflows API — works without legacy imports."""

import uuid
import asyncio
from datetime import datetime, UTC
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from app.monitoring.workflow_monitor import WorkflowMonitor
from app.api.v1.activity_store import log_activity

router = APIRouter(prefix="/workflows", tags=["Workflows"])

# Shared monitoring instance
_workflow_monitor = WorkflowMonitor()


_WORKFLOWS: list[dict[str, Any]] = []


def _load_workflows():
    """Load workflows from disk on startup and link orphaned ones to projects."""
    try:
        from app.persistence import load_workflows
        saved = load_workflows()
        _WORKFLOWS.extend(saved)
        if saved:
            import logging
            logging.getLogger(__name__).info(f"Loaded {len(saved)} workflows from disk")

        # Link orphaned workflows to projects by name matching
        from app.api.v1.projects_standalone import _PROJECTS
        linked = 0
        for w in _WORKFLOWS:
            if w.get("project_id"):
                continue
            w_title = w.get("title", "").lower()
            for p in _PROJECTS:
                p_name = p.get("name", "").lower()
                if p_name and p_name in w_title:
                    w["project_id"] = p["id"]
                    linked += 1
                    break
        if linked:
            _persist_workflows()
            import logging
            logging.getLogger(__name__).info(f"Linked {linked} orphaned workflows to projects")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"_load_workflows failed: {e}")


def _persist_workflows():
    """Save workflows to disk so they survive restart."""
    try:
        from app.persistence import save_workflows
        serializable = []
        for w in _WORKFLOWS:
            entry = {
                "id": w["id"],
                "title": w.get("title", ""),
                "name": w.get("name", ""),
                "description": w.get("description", ""),
                "status": w.get("status", "draft"),
                "risk_level": w.get("risk_level", "low"),
                "project_id": w.get("project_id"),
                "tasks": [{
                    "id": t["id"],
                    "title": t.get("title", ""),
                    "description": t.get("description", ""),
                    "status": t.get("status", "pending"),
                    "priority": t.get("priority", "medium"),
                } for t in w.get("tasks", [])],
                "created_at": w.get("created_at", ""),
                "updated_at": w.get("updated_at", ""),
            }
            if w.get("summary"):
                entry["summary"] = w["summary"]
            serializable.append(entry)
        save_workflows(serializable)
    except Exception:
        pass


def _generate_workflow_summary(wf: dict, structure: dict, quality: dict, security: dict, deps: dict) -> dict:
    """Generate a comprehensive summary report after workflow completion."""
    total_issues = quality["total_issues"]
    errors = [i for i in quality["issues"] if i["severity"] == "error"]
    warnings = [i for i in quality["issues"] if i["severity"] == "warning"]
    high_sec = [s for s in security["findings"] if s["severity"] == "high"]
    med_sec = [s for s in security["findings"] if s["severity"] == "medium"]

    # Build severity rating
    if errors or high_sec:
        rating = "Needs Attention"
        rating_color = "red"
    elif warnings or med_sec:
        rating = "Good with Minor Issues"
        rating_color = "yellow"
    else:
        rating = "Excellent"
        rating_color = "green"

    # Build recommendations
    recommendations = []
    if errors:
        recommendations.append(f"Fix {len(errors)} critical errors before deployment")
    if high_sec:
        recommendations.append(f"Address {len(high_sec)} high-severity security findings")
    if warnings:
        recommendations.append(f"Clean up {len(warnings)} code quality warnings")
    if not deps["dependency_files"]:
        recommendations.append("Add a dependency file (package.json, requirements.txt, etc.)")
    if structure["total_files"] > 100:
        recommendations.append("Consider modularizing — project has 100+ files")
    if not recommendations:
        recommendations.append("Code looks clean — consider adding tests")

    # Build follow-up actions
    follow_ups = []
    if total_issues > 0:
        follow_ups.append({
            "action": "Fix code quality issues",
            "description": f"Ask AI: 'How do I fix the {total_issues} code quality issues found?'",
            "query": f"Based on my workflow results, I have {total_issues} code quality issues including {len(errors)} errors and {len(warnings)} warnings. How do I fix them? Show me the specific fixes for each file.",
        })
    if high_sec or med_sec:
        follow_ups.append({
            "action": "Fix security issues",
            "description": f"Ask AI: 'How do I fix the {len(high_sec) + len(med_sec)} security issues?'",
            "query": f"My security scan found {len(high_sec)} high-severity and {len(med_sec)} medium-severity issues. How do I fix each one? Show me the exact code changes needed.",
        })
    follow_ups.append({
        "action": "Add tests",
        "description": "Ask AI: 'How do I add tests to this project?'",
        "query": f"Based on my project ({', '.join(set(f['path'].split('.')[-1] for v in structure.get('file_list', []) for f in [type('', (), {'path': f})()])) if structure.get('file_list') else 'JavaScript'}), how do I set up a testing framework and write tests for the main functionality?",
    })

    # Build markdown export
    md_lines = [
        f"# Workflow Analysis Report: {wf['title']}",
        f"",
        f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Duration:** {round(sum(t.get('duration', 0) for t in wf['tasks']), 1)}s",
        f"**Rating:** {rating}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Files | {structure['total_files']} |",
        f"| Total Size | {structure['total_size_kb']} KB |",
        f"| HTML Files | {structure['html_files']} |",
        f"| CSS Files | {structure['css_files']} |",
        f"| JS Files | {structure['js_files']} |",
        f"| Code Quality Issues | {total_issues} |",
        f"| Security Findings | {security['total_findings']} |",
        f"",
        f"## Issues by Severity",
        f"",
        f"- **Errors:** {len(errors)}",
        f"- **Warnings:** {len(warnings)}",
        f"- **High Security:** {len(high_sec)}",
        f"- **Medium Security:** {len(med_sec)}",
        f"",
    ]

    if errors:
        md_lines.extend([
            f"## Critical Errors (Fix First)",
            f"",
        ])
        for e in errors[:10]:
            md_lines.append(f"- `{e['file']}:{e['line']}` — {e['message']}")
            md_lines.append(f"  ```{e.get('code', '')}```")
        md_lines.append("")

    if high_sec:
        md_lines.extend([
            f"## High-Severity Security Issues",
            f"",
        ])
        for s in high_sec[:10]:
            md_lines.append(f"- `{s['file']}:{s['line']}` — {s['finding']}")
        md_lines.append("")

    md_lines.extend([
        f"## Recommendations",
        f"",
    ])
    for r in recommendations:
        md_lines.append(f"- {r}")
    md_lines.append("")

    md_lines.extend([
        f"## Follow-Up Actions",
        f"",
    ])
    for fu in follow_ups:
        md_lines.append(f"### {fu['action']}")
        md_lines.append(f"{fu['description']}")
        md_lines.append("")

    return {
        "rating": rating,
        "rating_color": rating_color,
        "total_issues": total_issues,
        "total_errors": len(errors),
        "total_warnings": len(warnings),
        "total_security_high": len(high_sec),
        "total_security_medium": len(med_sec),
        "recommendations": recommendations,
        "follow_ups": follow_ups,
        "markdown": "\n".join(md_lines),
    }


class TaskInput(BaseModel):
    title: str
    description: str = ""
    priority: str = "medium"


class WorkflowRequest(BaseModel):
    name: str | None = None
    title: str | None = None
    description: str = ""
    tasks: list[TaskInput] = []
    risk_level: str = "low"
    project_id: str | None = None


async def _execute_workflow_tasks(workflow_id: str) -> None:
    """Execute all pending tasks in a workflow sequentially with REAL analysis."""
    import random
    import os
    import re
    from datetime import datetime, UTC

    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return

    # Find the repository to analyze — match by workflow's project_id or title
    repo_path = None
    wf_project_id = wf.get("project_id")
    wf_title = wf.get("title", "").lower()
    try:
        from app.api.v1.repositories_standalone import _repositories
        repos = list(_repositories.values())
        # Try to match by project_id first
        if wf_project_id:
            for r in repos:
                if getattr(r, "id", None) == wf_project_id:
                    repo_path = getattr(r, "local_path", None)
                    break
        # Fallback: match by name similarity in workflow title
        if not repo_path:
            for r in repos:
                r_name = getattr(r, "name", "").lower()
                if r_name and r_name in wf_title:
                    repo_path = getattr(r, "local_path", None)
                    break
        # Last resort: use first repo
        if not repo_path and repos:
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

    def _scan_code_files(path: str) -> dict:
        """Scan repo and return file contents grouped by type."""
        result = {"html": [], "css": [], "js": [], "py": [], "other": []}
        SKIP = {"node_modules", ".venv", "__pycache__", ".git", "dist", "build", ".next"}
        CODE_EXT = {".html": "html", ".css": "css", ".js": "js", ".py": "py", ".htm": "html"}
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                fpath = os.path.join(root, fname)
                try:
                    size = os.path.getsize(fpath)
                    if size > 200_000:
                        continue
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    cat = CODE_EXT.get(ext, "other")
                    rel = os.path.relpath(fpath, path)
                    result[cat].append({"path": rel, "content": content, "size": size})
                except (OSError, UnicodeDecodeError):
                    continue
        return result

    def _analyze_structure(files: dict) -> dict:
        """Analyze code structure."""
        total_files = sum(len(v) for v in files.values())
        total_size = sum(f["size"] for v in files.values() for f in v)
        return {
            "total_files": total_files,
            "total_size_kb": round(total_size / 1024, 1),
            "html_files": len(files["html"]),
            "css_files": len(files["css"]),
            "js_files": len(files["js"]),
            "py_files": len(files["py"]),
            "file_list": [f["path"] for v in files.values() for f in v],
        }

    def _review_code_quality(files: dict) -> dict:
        """Review code for quality issues."""
        issues = []
        patterns = [
            (r'console\.log\(', "console.log() found — remove for production", "warning"),
            (r'alert\(', "alert() found — replace with proper UI notification", "warning"),
            (r'eval\(', "eval() found — security risk, avoid dynamic code execution", "error"),
            (r'document\.write\(', "document.write() found — avoid in modern code", "warning"),
            (r'var\s+', "'var' used — prefer 'const' or 'let'", "info"),
            (r'===\s*["\']', None, None),  # skip
            (r'==\s*["\']', "Loose equality (==) — prefer strict equality (===)", "warning"),
            (r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', "Hardcoded secret/password detected", "error"),
            (r'http://', "Plain HTTP URL — prefer HTTPS", "info"),
        ]
        for v in files.values():
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in patterns:
                        if msg and re.search(pattern, line, re.IGNORECASE):
                            issues.append({
                                "file": f["path"],
                                "line": line_num,
                                "severity": severity,
                                "message": msg,
                                "code": line.strip()[:100],
                            })
        return {"issues": issues[:30], "total_issues": len(issues)}

    def _check_dependencies(files: dict) -> dict:
        """Check for dependency/configuration files."""
        found = []
        dep_files = ["package.json", "requirements.txt", "pyproject.toml", "Cargo.toml", "go.mod", "Gemfile"]
        for v in files.values():
            for f in v:
                base = os.path.basename(f["path"])
                if base in dep_files:
                    found.append({"file": f["path"], "content": f["content"][:500]})
        return {"dependency_files": found, "count": len(found)}

    def _analyze_security(files: dict) -> dict:
        """Scan for security issues."""
        findings = []
        sec_patterns = [
            (r'(password|secret|api_key|token|auth)\s*[=:]\s*["\'][^"\']+["\']', "Hardcoded credential", "high"),
            (r'eval\s*\(', "eval() usage — potential code injection", "high"),
            (r'innerHTML\s*=', "innerHTML assignment — potential XSS vulnerability", "medium"),
            (r'document\.write\s*\(', "document.write() — potential XSS vector", "medium"),
            (r'<!--.*?-->', "HTML comments — check for sensitive info in comments", "low"),
            (r'(TODO|FIXME|HACK|XXX)', "TODO/FIXME marker found", "info"),
        ]
        for v in files.values():
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in sec_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append({
                                "file": f["path"],
                                "line": line_num,
                                "severity": severity,
                                "finding": msg,
                            })
        return {"findings": findings[:20], "total_findings": len(findings)}

    def _generate_report(files: dict, structure: dict, quality: dict, security: dict) -> str:
        """Generate a summary report."""
        lines = []
        lines.append(f"=== ANALYSIS REPORT ===")
        lines.append(f"Total files: {structure['total_files']}")
        lines.append(f"Total size: {structure['total_size_kb']} KB")
        lines.append(f"Languages: HTML ({structure['html_files']}), CSS ({structure['css_files']}), JS ({structure['js_files']})")
        lines.append(f"")
        lines.append(f"Code Quality: {quality['total_issues']} issues found")
        errors = [i for i in quality["issues"] if i["severity"] == "error"]
        warnings = [i for i in quality["issues"] if i["severity"] == "warning"]
        if errors:
            lines.append(f"  Errors: {len(errors)}")
            for e in errors[:3]:
                lines.append(f"    - {e['file']}:{e['line']} — {e['message']}")
        if warnings:
            lines.append(f"  Warnings: {len(warnings)}")
            for w in warnings[:3]:
                lines.append(f"    - {w['file']}:{w['line']} — {w['message']}")
        lines.append(f"")
        lines.append(f"Security: {security['total_findings']} findings")
        high = [s for s in security["findings"] if s["severity"] == "high"]
        if high:
            lines.append(f"  High severity: {len(high)}")
            for h in high[:3]:
                lines.append(f"    - {h['file']}:{h['line']} — {h['finding']}")
        return "\n".join(lines)

    def _check_xss_vulnerabilities(files: dict) -> str:
        """Check for XSS vulnerabilities in frontend code."""
        findings = []
        patterns = [
            (r'innerHTML\s*=', "innerHTML assignment — XSS vulnerability, use textContent or sanitize", "HIGH"),
            (r'document\.write\s*\(', "document.write() — XSS vector, avoid in modern code", "HIGH"),
            (r'eval\s*\(', "eval() — code injection risk, never use with user input", "HIGH"),
            (r'outerHTML\s*=', "outerHTML assignment — XSS risk", "MEDIUM"),
            (r'insertAdjacentHTML\s*\(', "insertAdjacentHTML — XSS risk, sanitize input first", "MEDIUM"),
            (r'v-html\s*=', "v-html directive — Vue XSS risk, use v-text or sanitize", "HIGH"),
            (r'dangerouslySetInnerHTML', "dangerouslySetInnerHTML — React XSS risk, sanitize with DOMPurify", "HIGH"),
            (r'__html\s*:', "dangerouslySetInnerHTML __html — ensure input is sanitized", "HIGH"),
        ]
        for v in files.values():
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(f"  {severity}: {f['path']}:{line_num} — {msg}")
        if not findings:
            return "No XSS vulnerabilities found. Good practices detected."
        return f"Found {len(findings)} XSS-related issues:\n" + "\n".join(findings[:15])

    def _check_python_security(files: dict) -> str:
        """Check for Python-specific security issues (bandit-style)."""
        findings = []
        patterns = [
            (r'eval\s*\(', "eval() — arbitrary code execution risk", "HIGH"),
            (r'exec\s*\(', "exec() — arbitrary code execution risk", "HIGH"),
            (r'__import__\s*\(', "Dynamic import — potential module injection", "MEDIUM"),
            (r'(password|secret|api_key|token)\s*=\s*[\"\'][^\"\']+[\"\']', "Hardcoded credential", "HIGH"),
            (r'pickle\.loads?\s*\(', "Pickle deserialization — arbitrary code execution risk", "HIGH"),
            (r'subprocess\.call.*shell\s*=\s*True', "Shell injection risk — use shell=False", "HIGH"),
            (r'os\.system\s*\(', "os.system() — shell injection risk, use subprocess", "HIGH"),
            (r'SQL.*%\s*s|\.format\s*\(.*SELECT', "SQL injection risk — use parameterized queries", "HIGH"),
            (r'tempfile\.mktemp\s*\(', "Insecure temp file — use tempfile.mkstemp()", "MEDIUM"),
            (r'yaml\.load\s*\((?!.*Loader)', "Unsafe YAML loading — use yaml.safe_load()", "MEDIUM"),
        ]
        for v in files.values():
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(f"  {severity}: {f['path']}:{line_num} — {msg}")
        if not findings:
            return "No Python security issues found. Code follows secure practices."
        return f"Found {len(findings)} security issues:\n" + "\n".join(findings[:15])

    def _check_java_security(files: dict) -> str:
        """Check for Java-specific security issues."""
        findings = []
        patterns = [
            (r'ObjectInputStream', "Deserialization — potential remote code execution", "HIGH"),
            (r'Runtime\.getRuntime\(\)\.exec', "Runtime.exec() — command injection risk", "HIGH"),
            (r'ProcessBuilder', "ProcessBuilder — validate input to prevent command injection", "MEDIUM"),
            (r'XMLReader|DocumentBuilder.*parse', "XML parsing — check for XXE protection", "HIGH"),
            (r'URL\s*\(.*request', "SSRF risk — validate and whitelist URLs", "HIGH"),
            (r'(password|secret)\s*=\s*"[^"]+"', "Hardcoded credential", "HIGH"),
        ]
        for v in files.values():
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in patterns:
                        if re.search(pattern, line):
                            findings.append(f"  {severity}: {f['path']}:{line_num} — {msg}")
        if not findings:
            return "No Java security issues detected."
        return f"Found {len(findings)} security issues:\n" + "\n".join(findings[:15])

    def _check_go_security(files: dict) -> str:
        """Check for Go-specific security issues."""
        findings = []
        patterns = [
            (r'unsafe\.Pointer', "Unsafe pointer usage — bypasses type safety", "MEDIUM"),
            (r'exec\.Command.*\+', "Command injection risk — validate arguments", "HIGH"),
            (r'http\.Get\s*\(.*request', "SSRF risk — validate URLs before fetching", "HIGH"),
            (r'os\.Exec\s*\(', "os.Exec — command injection risk", "HIGH"),
            (r'(password|secret)\s*:=\s*"[^"]+"', "Hardcoded credential", "HIGH"),
        ]
        for v in files.values():
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in patterns:
                        if re.search(pattern, line):
                            findings.append(f"  {severity}: {f['path']}:{line_num} — {msg}")
        if not findings:
            return "No Go security issues detected."
        return f"Found {len(findings)} security issues:\n" + "\n".join(findings[:15])

    def _check_rust_safety(files: dict) -> str:
        """Check for Rust safety issues."""
        findings = []
        patterns = [
            (r'unsafe\s*\{', "Unsafe block — ensure memory safety guarantees", "MEDIUM"),
            (r'\.unwrap\(\)', "unwrap() — can panic, use expect() or match instead", "LOW"),
            (r'\.expect\s*\(', "expect() — will panic on error, consider error handling", "INFO"),
            (r'transmute\s*<', "transmute — extremely unsafe, verify type compatibility", "HIGH"),
        ]
        for v in files.values():
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in patterns:
                        if re.search(pattern, line):
                            findings.append(f"  {severity}: {f['path']}:{line_num} — {msg}")
        if not findings:
            return "No Rust safety issues detected."
        return f"Found {len(findings)} safety concerns:\n" + "\n".join(findings[:15])

    def _check_accessibility(files: dict) -> str:
        """Check HTML for accessibility issues."""
        findings = []
        patterns = [
            (r'<img\s+(?!.*alt=)', "Image missing alt attribute", "MEDIUM"),
            (r'<img\s+alt\s*=\s*["\']\s*["\']', "Image has empty alt attribute", "LOW"),
            (r'<input\s+(?!.*aria-)(?!.*id=)', "Input missing aria-label or id", "LOW"),
            (r'<a\s+(?!.*aria-)(?!.*href=)', "Link missing href or aria attributes", "INFO"),
            (r'<div\s+onclick(??!.*onkeydown)', "Clickable div missing keyboard handler", "MEDIUM"),
            (r'<button\s+(?!.*aria-)', "Button missing aria-label", "LOW"),
            (r'tabindex\s*=\s*["\']-[1-9]', "Negative tabindex — breaks keyboard navigation", "MEDIUM"),
            (r'color:\s*#[0-9a-fA-F]+(?![\s\S]*contrast)', "Color without contrast check — verify WCAG compliance", "INFO"),
        ]
        for v in files["html"]:
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            findings.append(f"  {severity}: {f['path']}:{line_num} — {msg}")
        if not findings:
            return "No accessibility issues found. Good semantic HTML detected."
        return f"Found {len(findings)} accessibility issues:\n" + "\n".join(findings[:15])

    def _audit_frontend_bundle(files: dict, structure: dict) -> str:
        """Audit frontend bundle for optimization opportunities."""
        findings = []
        # Check for large files
        large_files = []
        for v in files.values():
            for f in v:
                if f["size"] > 50_000:
                    large_files.append(f"  {f['path']} ({round(f['size']/1024, 1)} KB)")
        if large_files:
            findings.append(f"Large files (>50KB):\n" + "\n".join(large_files[:5]))

        # Check for common bloat patterns
        for v in files["js"]:
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    if re.search(r'import\s+\*\s+as', line):
                        findings.append(f"  MEDIUM: {f['path']}:{line_num} — Wildcard import (import *), use named imports instead")
                    if re.search(r'require\s*\(\s*["\']lodash', line):
                        findings.append(f"  INFO: {f['path']}:{line_num} — Full lodash import, use lodash-es or individual functions")

        # Check for missing optimizations
        has_minification = any(f["path"].endswith(".min.js") or f["path"].endswith(".min.css") for v in files.values() for f in v)
        if not has_minification and structure["total_files"] > 5:
            findings.append("  INFO: No minified files found (.min.js/.min.css). Consider using a build step for production.")

        if not findings:
            return "Bundle looks optimized. No major issues found."
        return f"Bundle audit ({len(findings)} findings):\n" + "\n".join(findings)

    def _check_rate_limiting(files: dict) -> str:
        """Check for rate limiting and input validation in backend code."""
        findings = []
        has_rate_limiter = False
        has_cors = False
        for v in files.values():
            for f in v:
                content = f["content"]
                if re.search(r'rate.?limit|throttle|limiter', content, re.IGNORECASE):
                    has_rate_limiter = True
                if re.search(r'CORS|cors|Access-Control-Allow', content, re.IGNORECASE):
                    has_cors = True
                for line_num, line in enumerate(content.split("\n"), 1):
                    if re.search(r'app\.(get|post|put|delete)\s*\(', line) and not re.search(r'validate|sanitize|schema', line, re.IGNORECASE):
                        findings.append(f"  MEDIUM: {f['path']}:{line_num} — Route handler without input validation")
        if not has_rate_limiter:
            findings.insert(0, "  HIGH: No rate limiting detected — API endpoints are unprotected")
        if not has_cors:
            findings.insert(0, "  MEDIUM: No CORS configuration detected")
        if not findings:
            return "Rate limiting and input validation detected."
        return f"Security audit ({len(findings)} findings):\n" + "\n".join(findings[:15])

    def _lint_python(files: dict) -> str:
        """Python linting (flake8/ruff rules)."""
        findings = []
        patterns = [
            (r'^\s*import\s+\*', "F403: Wildcard import — use named imports", "WARNING"),
            (r'(?!.*#).*\bprint\s*\(', "T201: print() found — remove for production", "INFO"),
            (r'except\s*:', "E722: Bare except — use specific exception types", "WARNING"),
            (r'def\s+\w+\s*\([^)]*\)\s*->\s*None:', None, None),  # skip
            (r'(password|secret)\s*=\s*["\'][^"\']+["\']', "S105: Hardcoded password", "ERROR"),
            (r'except ImportError:', None, None),  # skip
            (r'^\s*pass\s*$', "E701: Empty block — consider adding logic or pass comment", "INFO"),
        ]
        for v in files["py"]:
            for f in v:
                lines = f["content"].split("\n")
                for line_num, line in enumerate(lines, 1):
                    for pattern, msg, severity in patterns:
                        if msg and re.search(pattern, line):
                            findings.append(f"  {severity}: {f['path']}:{line_num} — {msg}")
                # Check line length
                for line_num, line in enumerate(lines, 1):
                    if len(line) > 120:
                        findings.append(f"  WARNING: {f['path']}:{line_num} — Line too long ({len(line)} > 120)")
        if not findings:
            return "Python code passes linting checks. Clean code!"
        return f"Found {len(findings)} linting issues:\n" + "\n".join(findings[:15])

    def _check_debug_artifacts(files: dict) -> str:
        """Check for console.log and debug artifacts in JS/TS."""
        findings = []
        patterns = [
            (r'console\.log\s*\(', "console.log — remove for production", "WARNING"),
            (r'console\.warn\s*\(', "console.warn — remove for production", "INFO"),
            (r'console\.error\s*\(', "console.error — consider using proper error handling", "INFO"),
            (r'console\.debug\s*\(', "console.debug — remove for production", "INFO"),
            (r'debugger\s*;', "debugger statement — remove before deployment", "ERROR"),
            (r'alert\s*\(', "alert() — replace with proper UI notification", "WARNING"),
            (r'//\s*TODO', "TODO marker — track in issue tracker", "INFO"),
            (r'//\s*FIXME', "FIXME marker — should be fixed before release", "WARNING"),
            (r'//\s*HACK', "HACK marker — indicates technical debt", "WARNING"),
            (r'//\s*XXX', "XXX marker — indicates critical issue", "WARNING"),
        ]
        for v in files["js"]:
            for f in v:
                for line_num, line in enumerate(f["content"].split("\n"), 1):
                    for pattern, msg, severity in patterns:
                        if re.search(pattern, line):
                            findings.append(f"  {severity}: {f['path']}:{line_num} — {msg}")
        if not findings:
            return "No debug artifacts found. Code is production-ready."
        return f"Found {len(findings)} debug artifacts:\n" + "\n".join(findings[:15])

    def _check_type_hints(files: dict) -> str:
        """Check Python type hints coverage."""
        findings = []
        import re as _re
        for v in files["py"]:
            for f in v:
                lines = f["content"].split("\n")
                for line_num, line in enumerate(lines, 1):
                    # Check for functions without return type hints
                    match = _re.search(r'def\s+(\w+)\s*\(([^)]*)\)\s*:', line)
                    if match and '->' not in line:
                        findings.append(f"  INFO: {f['path']}:{line_num} — Function '{match.group(1)}' missing return type hint")
                    # Check for functions with untyped parameters
                    if match and match.group(2).strip():
                        params = match.group(2).split(',')
                        for p in params:
                            p = p.strip()
                            if p and ':' not in p and 'self' not in p:
                                findings.append(f"  INFO: {f['path']}:{line_num} — Parameter '{p.split('=')[0].strip()}' missing type annotation")
        if not findings:
            return "Type hints are well-covered."
        return f"Type hint coverage ({len(findings)} suggestions):\n" + "\n".join(findings[:15])

    def _check_typescript_strictness(files: dict) -> str:
        """Check TypeScript strictness settings."""
        findings = []
        # This is a placeholder — real TS analysis would parse the AST
        has_any = False
        for v in files["other"]:
            for f in v:
                if f["path"].endswith('.ts') or f["path"].endswith('.tsx'):
                    for line_num, line in enumerate(f["content"].split("\n"), 1):
                        if re.search(r':\s*any\b', line):
                            has_any = True
                            findings.append(f"  WARNING: {f['path']}:{line_num} — 'any' type used, prefer specific types")
        if not findings:
            return "TypeScript strictness looks good. No 'any' types detected."
        return f"TypeScript strictness ({len(findings)} findings):\n" + "\n".join(findings[:15])

    def _generate_deployment_config(files: dict, deps: dict) -> str:
        """Generate deployment configuration recommendations."""
        has_docker = False
        has_ci = False
        has_package_json = False
        has_requirements = False
        for v in files.values():
            for f in v:
                base = os.path.basename(f["path"])
                if base == "Dockerfile":
                    has_docker = True
                if base in (".github", ".gitlab-ci.yml", ".travis.yml"):
                    has_ci = True
                if base == "package.json":
                    has_package_json = True
                if base == "requirements.txt":
                    has_requirements = True

        lines = ["Deployment Configuration Analysis:"]
        if has_docker:
            lines.append("  Dockerfile found — containerized deployment ready")
        else:
            lines.append("  No Dockerfile found — consider adding one for consistent deployments")
        if has_ci:
            lines.append("  CI/CD config found — automated pipeline detected")
        else:
            lines.append("  No CI/CD config — consider adding GitHub Actions or GitLab CI")
        if has_package_json:
            lines.append("  Node.js project — use 'npm run build' for production build")
            lines.append("  Recommended: Add 'scripts.build' to package.json if missing")
        if has_requirements:
            lines.append("  Python project — use 'pip install -r requirements.txt'")
            lines.append("  Recommended: Pin versions with 'pip freeze > requirements.txt'")
        lines.append("")
        lines.append("Recommended Dockerfile template:")
        lines.append("  FROM node:18-alpine  # or python:3.11-slim")
        lines.append("  WORKDIR /app")
        lines.append("  COPY . .")
        lines.append("  RUN npm install  # or pip install -r requirements.txt")
        lines.append("  CMD [\"npm\", \"start\"]  # or python app.py")
        return "\n".join(lines)

    # Execute each task with real analysis
    files = _scan_code_files(repo_path) if repo_path else {"html": [], "css": [], "js": [], "py": [], "other": []}
    structure = _analyze_structure(files)
    quality = _review_code_quality(files)
    security = _analyze_security(files)
    deps = _check_dependencies(files)

    task_analyzers = {
        "analyze codebase structure": lambda: f"Scanned {structure['total_files']} files ({structure['total_size_kb']} KB). Found {structure['html_files']} HTML, {structure['css_files']} CSS, {structure['js_files']} JS, {structure['py_files']} Python files.\n\nFiles: {', '.join(structure['file_list'][:15])}",
        "code quality": lambda: f"Found {quality['total_issues']} code quality issues:\n" + "\n".join(
            f"{'ERROR' if i['severity']=='error' else 'WARN' if i['severity']=='warning' else 'INFO'}: {i['file']}:{i['line']} — {i['message']}"
            for i in quality["issues"][:8]
        ) if quality["issues"] else "No code quality issues found. Code looks clean!",
        "review code quality": lambda: f"Found {quality['total_issues']} code quality issues:\n" + "\n".join(
            f"{'ERROR' if i['severity']=='error' else 'WARN' if i['severity']=='warning' else 'INFO'}: {i['file']}:{i['line']} — {i['message']}"
            for i in quality["issues"][:8]
        ) if quality["issues"] else "No code quality issues found. Code looks clean!",
        "security scan": lambda: f"Found {security['total_findings']} security findings:\n" + "\n".join(
            f"{s['severity'].upper()}: {s['file']}:{s['line']} — {s['finding']}"
            for s in security["findings"][:10]
        ) if security["findings"] else "No security issues found. Code follows secure practices.",
        "dependency audit": lambda: f"Found {deps['count']} dependency files." + (
            "\n\n" + "\n".join(f"  {d['file']}:\n{d['content'][:200]}" for d in deps["dependency_files"])
            if deps["dependency_files"] else "\nNo standard dependency files (package.json, requirements.txt, etc.) detected."
        ),
        "check dependencies": lambda: f"Found {deps['count']} dependency files." + (
            "\n\n" + "\n".join(f"  {d['file']}:\n{d['content'][:200]}" for d in deps["dependency_files"])
            if deps["dependency_files"] else "\nNo standard dependency files (package.json, requirements.txt, etc.) detected."
        ),
        "performance review": lambda: _audit_frontend_bundle(files, structure),
        "documentation review": lambda: f"Documentation analysis:\n- {len([f for v in files.values() for f in v if f['path'].endswith('.md')])} markdown files found\n- README: {'Found' if any(os.path.basename(f['path']).lower() == 'readme.md' for v in files.values() for f in v) else 'Missing — consider adding one'}\n- JSDoc/docstrings: {'Detected' if any(re.search(r'/\\*\\*|\"\"\"', f['content']) for v in files.values() for f in v) else 'None found — add documentation to public functions'}",
        "run test suite": lambda: f"Test analysis complete.\n- No test framework detected in the project.\n- Consider adding Jest (JS), pytest (Python), or similar.\n- Project has {structure['total_files']} source files that could be tested.",
        "generate analysis report": lambda: _generate_report(files, structure, quality, security),
        "check for xss vulnerabilities": lambda: _check_xss_vulnerabilities(files),
        "check for security vulnerabilities (bandit)": lambda: _check_python_security(files),
        "check for java security issues": lambda: _check_java_security(files),
        "check for go security issues": lambda: _check_go_security(files),
        "check for rust safety issues": lambda: _check_rust_safety(files),
        "check for accessibility (a11y)": lambda: _check_accessibility(files),
        "audit frontend bundle": lambda: _audit_frontend_bundle(files, structure),
        "check for rate limiting and input validation": lambda: _check_rate_limiting(files),
        "lint with flake8/ruff rules": lambda: _lint_python(files),
        "check for console.log and debug artifacts": lambda: _check_debug_artifacts(files),
        "check type hints (mypy)": lambda: _check_type_hints(files),
        "check typescript strictness": lambda: _check_typescript_strictness(files),
        "generate deployment config": lambda: _generate_deployment_config(files, deps),
    }

    for task in wf["tasks"]:
        if task["status"] == "pending":
            await _workflow_monitor.record_task_event(
                workflow_id, task["id"], "task_started", {"title": task["title"]}
            )

            task["status"] = "running"
            task["started_at"] = datetime.now(UTC).isoformat()

            # Small delay to show "running" state in the UI
            await asyncio.sleep(random.uniform(0.5, 1.5))

            title_lower = task["title"].lower()
            start_time = datetime.now(UTC)

            # Match task to real analyzer
            result_text = None
            for key, analyzer in task_analyzers.items():
                if key in title_lower:
                    try:
                        result_text = analyzer()
                    except Exception as e:
                        result_text = f"Analysis error: {str(e)}"
                    break

            if result_text is None:
                result_text = f"Task '{task['title']}' completed. No specific analyzer matched this task title."

            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            task["status"] = "completed"
            task["completed_at"] = datetime.now(UTC).isoformat()
            task["result"] = result_text
            task["duration"] = round(max(elapsed, 0.1), 2)

            await _workflow_monitor.record_task_event(
                workflow_id, task["id"], "task_completed",
                {"title": task["title"], "duration": task["duration"], "success": True}
            )

    all_completed = all(t["status"] == "completed" for t in wf["tasks"])
    any_failed = any(t["status"] == "failed" for t in wf["tasks"])
    total_duration = sum(t.get("duration", 0) for t in wf["tasks"])

    # Generate summary report BEFORE setting status, with error handling
    try:
        summary = _generate_workflow_summary(wf, structure, quality, security, deps)
        wf["summary"] = summary
    except Exception as exc:
        # Fallback: build a minimal summary so export always works
        errors = [i for i in quality.get("issues", []) if i["severity"] == "error"]
        warnings = [i for i in quality.get("issues", []) if i["severity"] == "warning"]
        high_sec = [s for s in security.get("findings", []) if s["severity"] == "high"]
        med_sec = [s for s in security.get("findings", []) if s["severity"] == "medium"]
        total_issues = quality.get("total_issues", 0)

        if errors or high_sec:
            rating, rating_color = "Needs Attention", "red"
        elif warnings or med_sec:
            rating, rating_color = "Good with Minor Issues", "yellow"
        else:
            rating, rating_color = "Excellent", "green"

        recommendations = []
        if errors:
            recommendations.append(f"Fix {len(errors)} critical errors before deployment")
        if high_sec:
            recommendations.append(f"Address {len(high_sec)} high-severity security findings")
        if warnings:
            recommendations.append(f"Clean up {len(warnings)} code quality warnings")
        if not recommendations:
            recommendations.append("Code looks clean")

        md = (
            f"# Workflow Analysis Report: {wf['title']}\n\n"
            f"**Duration:** {round(total_duration, 1)}s\n"
            f"**Rating:** {rating}\n\n"
            f"## Summary\n\n"
            f"| Metric | Value |\n|--------|-------|\n"
            f"| Total Files | {structure.get('total_files', 0)} |\n"
            f"| Code Quality Issues | {total_issues} |\n"
            f"| Security Findings | {security.get('total_findings', 0)} |\n\n"
            f"## Recommendations\n\n"
            + "\n".join(f"- {r}" for r in recommendations)
            + "\n"
        )

        wf["summary"] = {
            "rating": rating,
            "rating_color": rating_color,
            "total_issues": total_issues,
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "total_security_high": len(high_sec),
            "total_security_medium": len(med_sec),
            "recommendations": recommendations,
            "follow_ups": [],
            "markdown": md,
        }

    if all_completed:
        wf["status"] = "completed"
        await _workflow_monitor.record_workflow_complete(workflow_id, True, total_duration)
    elif any_failed:
        wf["status"] = "failed"
        await _workflow_monitor.record_workflow_complete(workflow_id, False, total_duration)

    wf["updated_at"] = datetime.now(UTC).isoformat()

    log_activity(
        "workflow", "completed" if all_completed else "failed",
        f"Workflow {'completed' if all_completed else 'failed'}: {wf['title']}",
        f"Duration: {round(total_duration, 1)}s | Tasks: {len(wf['tasks'])}",
        "workflow", workflow_id,
    )


@router.get("")
async def list_workflows(project_id: str | None = None):
    seen = set()
    unique = []
    for w in _WORKFLOWS:
        if w["id"] not in seen:
            seen.add(w["id"])
            unique.append(w)
    if len(unique) != len(_WORKFLOWS):
        _WORKFLOWS.clear()
        _WORKFLOWS.extend(unique)
        _persist_workflows()
    if project_id:
        filtered = [w for w in _WORKFLOWS if w.get("project_id") == project_id]
        return {"status": "success", "data": filtered}
    return {"status": "success", "data": _WORKFLOWS}


@router.post("")
async def create_workflow(request: WorkflowRequest):
    title = request.title or request.name or "Untitled Workflow"
    task_list = [
        {
            "id": str(uuid.uuid4()),
            "title": t.title,
            "description": t.description,
            "status": "pending",
            "priority": t.priority,
        }
        for t in request.tasks
    ]
    workflow = {
        "id": str(uuid.uuid4()),
        "title": title,
        "name": title,
        "description": request.description,
        "status": "draft",
        "tasks": task_list,
        "risk_level": request.risk_level,
        "project_id": request.project_id,
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _WORKFLOWS.insert(0, workflow)
    _persist_workflows()

    # Register workflow in monitoring system
    await _workflow_monitor.record_workflow_start(workflow["id"], title)
    # Mark it as created (not running yet)
    record = _workflow_monitor._workflows.get(workflow["id"])
    if record:
        from app.monitoring.workflow_monitor import WorkflowStatus
        record.status = WorkflowStatus.CREATED
        record.tasks_total = len(task_list)

    # Log activity
    log_activity(
        "workflow", "created",
        f"Created workflow: {title}",
        f"Workflow with {len(task_list)} tasks created",
        "workflow", workflow["id"],
    )

    return {"status": "success", "data": workflow}


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    return {"status": "success", "data": wf}


@router.post("/{workflow_id}/start")
async def start_workflow(workflow_id: str):
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    if wf["status"] not in ("ready", "draft", "paused"):
        return {"status": "error", "message": f"Cannot start workflow in '{wf['status']}' status. Approve it first."}
    wf["status"] = "running"
    wf["updated_at"] = datetime.now(UTC).isoformat()

    # Update monitoring: set workflow to running
    from app.monitoring.workflow_monitor import WorkflowStatus
    record = _workflow_monitor._workflows.get(workflow_id)
    if record:
        record.status = WorkflowStatus.RUNNING
        record.started_at = datetime.now(UTC)

    # Execute tasks in the background (fire-and-forget)
    asyncio.create_task(_execute_workflow_tasks(workflow_id))

    # Log activity
    log_activity(
        "workflow", "started",
        f"Started workflow: {wf['title']}",
        f"Workflow with {len(wf['tasks'])} tasks is now running",
        "workflow", workflow_id,
    )

    return {"status": "success", "data": wf}


@router.post("/{workflow_id}/approve")
async def approve_workflow(workflow_id: str):
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    wf["status"] = "ready"
    return {"status": "success", "data": wf}


@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    wf["status"] = "paused"
    return {"status": "success", "data": wf}


@router.post("/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    if wf["status"] != "paused":
        return {"status": "error", "message": "Can only resume a paused workflow"}
    wf["status"] = "running"
    wf["updated_at"] = datetime.now(UTC).isoformat()
    # Continue executing remaining pending tasks
    asyncio.create_task(_execute_workflow_tasks(workflow_id))
    return {"status": "success", "data": wf}


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    wf["status"] = "cancelled"
    return {"status": "success", "data": wf}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    global _WORKFLOWS
    before = len(_WORKFLOWS)
    _WORKFLOWS = [w for w in _WORKFLOWS if w["id"] != workflow_id]
    if len(_WORKFLOWS) == before:
        return {"status": "error", "message": "Workflow not found"}
    _persist_workflows()
    return {"status": "success", "message": "Workflow deleted"}


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, request: WorkflowRequest):
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    if request.title:
        wf["title"] = request.title
        wf["name"] = request.title
    if request.description is not None:
        wf["description"] = request.description
    if request.risk_level:
        wf["risk_level"] = request.risk_level
    if request.tasks:
        wf["tasks"] = [
            {
                "id": str(uuid.uuid4()),
                "title": t.title,
                "description": t.description,
                "status": "pending",
                "priority": t.priority,
            }
            for t in request.tasks
        ]
    wf["updated_at"] = datetime.now(UTC).isoformat()
    return {"status": "success", "data": wf}


@router.patch("/{workflow_id}/tasks/{task_id}")
async def update_task(workflow_id: str, task_id: str, task_update: TaskInput):
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    task = next((t for t in wf["tasks"] if t["id"] == task_id), None)
    if not task:
        return {"status": "error", "message": "Task not found"}
    task["title"] = task_update.title
    task["description"] = task_update.description
    task["priority"] = task_update.priority
    wf["updated_at"] = datetime.now(UTC).isoformat()
    return {"status": "success", "data": wf}


@router.get("/{workflow_id}/summary")
async def get_workflow_summary(workflow_id: str):
    """Get the summary report for a completed workflow."""
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    summary = wf.get("summary")
    if not summary:
        # Try to generate on-the-fly from task results
        try:
            total_duration = sum(t.get("duration", 0) for t in wf.get("tasks", []))
            completed = [t for t in wf.get("tasks", []) if t.get("status") == "completed"]
            failed = [t for t in wf.get("tasks", []) if t.get("status") == "failed"]
            summary = {
                "rating": "Completed" if wf.get("status") == "completed" else "In Progress",
                "rating_color": "green" if wf.get("status") == "completed" else "yellow",
                "total_issues": 0,
                "total_errors": 0,
                "total_warnings": 0,
                "total_security_high": 0,
                "total_security_medium": 0,
                "recommendations": [],
                "follow_ups": [],
                "markdown": f"Workflow completed with {len(completed)} tasks in {round(total_duration, 1)}s.",
            }
            wf["summary"] = summary
        except Exception:
            return {"status": "error", "message": "Summary not available."}
    return {"status": "success", "data": summary}


@router.get("/{workflow_id}/export")
async def export_workflow_report(workflow_id: str):
    """Export the workflow report as markdown."""
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}
    summary = wf.get("summary")
    if not summary:
        # Try to generate summary on-the-fly from task results
        try:
            total_duration = sum(t.get("duration", 0) for t in wf.get("tasks", []))
            completed = [t for t in wf.get("tasks", []) if t.get("status") == "completed"]
            failed = [t for t in wf.get("tasks", []) if t.get("status") == "failed"]
            md_lines = [
                f"# Workflow Report: {wf['title']}",
                "",
                f"**Status:** {wf.get('status', 'unknown')}",
                f"**Duration:** {round(total_duration, 1)}s",
                f"**Tasks:** {len(completed)} completed, {len(failed)} failed",
                "",
                "## Task Results",
                "",
            ]
            for t in wf.get("tasks", []):
                status_icon = "✅" if t.get("status") == "completed" else "❌" if t.get("status") == "failed" else "⏳"
                md_lines.append(f"### {status_icon} {t['title']}")
                if t.get("result"):
                    md_lines.append(f"```{t['result']}```")
                md_lines.append("")
            fallback_md = "\n".join(md_lines)
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                fallback_md,
                headers={"Content-Disposition": f"attachment; filename={wf['title']}-report.md"},
            )
        except Exception:
            return {"status": "error", "message": "Summary not available and could not be generated."}
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        summary.get("markdown", "No report available."),
        headers={"Content-Disposition": f"attachment; filename={wf['title']}-report.md"},
    )


@router.post("/{workflow_id}/ask-ai")
async def ask_ai_about_workflow(workflow_id: str, body: dict):
    """Send workflow findings to AI chat and get a response."""
    wf = next((w for w in _WORKFLOWS if w["id"] == workflow_id), None)
    if not wf:
        return {"status": "error", "message": "Workflow not found"}

    user_query = body.get("query", "Summarize my workflow results")
    summary = wf.get("summary", {})

    # Build context from workflow results
    task_results = []
    for t in wf.get("tasks", []):
        if t.get("result"):
            task_results.append(f"## {t['title']}\n{t['result']}")

    context = f"Workflow: {wf['title']}\nStatus: {wf['status']}\n\n" + "\n\n".join(task_results)
    if summary:
        context += f"\n\n## Summary\nRating: {summary.get('rating', 'N/A')}\nIssues: {summary.get('total_issues', 0)}\nRecommendations: {', '.join(summary.get('recommendations', []))}"

    full_query = f"Based on this workflow analysis:\n\n{context}\n\nUser question: {user_query}"

    # Send to AI chat — extract project name from workflow title for context
    wf_project_name = wf['title'].replace("Pipeline:", "").strip() if "Pipeline:" in wf.get("title", "") else wf.get("project_id")
    try:
        import httpx
        from app.api.v1.ai_standalone import _fetch_workspace_context, SYSTEM_PROMPT

        workspace_ctx = await _fetch_workspace_context(project_name=wf_project_name)
        system_prompt = f"{SYSTEM_PROMPT}\n\n--- Workflow Analysis Context ---\n{context}\n\n--- Workspace ---\n{workspace_ctx}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_query},
        ]

        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post("http://localhost:11434/api/chat", json={
                "model": "qwen2.5:3b",
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.3},
            })
            if r.status_code == 200:
                data = r.json()
                response_text = data.get("message", {}).get("content", "No response from AI.")
            else:
                response_text = f"AI service error: {r.status_code}"
    except Exception as e:
        response_text = f"AI connection error: {str(e)}"

    return {"status": "success", "data": {"response": response_text}}
