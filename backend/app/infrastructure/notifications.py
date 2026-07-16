"""Notification event system — triggers emails based on platform events."""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any

from app.infrastructure.email import email_service, EmailMessage


# ── Notification preference storage (in-memory) ──────────────────────────────

_user_preferences: dict[str, dict[str, bool]] = {}

DEFAULT_PREFERENCES = {
    "email_task_complete": False,
    "email_task_failed": True,
    "email_workflow_approved": False,
    "email_deployment": False,
    "email_security": True,
    "inapp_agent_updates": True,
    "inapp_mentions": True,
    "inapp_system": True,
}


def get_user_preferences(user_id: str = "default") -> dict[str, bool]:
    return _user_preferences.get(user_id, DEFAULT_PREFERENCES.copy())


def set_user_preferences(user_id: str, prefs: dict[str, bool]) -> dict[str, bool]:
    current = get_user_preferences(user_id)
    current.update(prefs)
    _user_preferences[user_id] = current
    return current


# ── Email templates ──────────────────────────────────────────────────────────

def _build_html(title: str, message: str, details: str = "", action_url: str = "") -> str:
    detail_html = f'<p style="color:#a1a1a1;font-size:14px;margin-top:12px;">{details}</p>' if details else ""
    action_html = ""
    if action_url:
        action_html = f'''
        <a href="{action_url}" style="display:inline-block;margin-top:16px;padding:10px 24px;
        background:#6366f1;color:#fff;text-decoration:none;border-radius:6px;font-size:14px;">
        View Details</a>'''

    return f"""
    <div style="font-family:system-ui,sans-serif;background:#000;color:#ededed;padding:32px;max-width:560px;margin:0 auto;">
        <div style="border:1px solid #222;border-radius:12px;padding:32px;">
            <h2 style="margin:0 0 8px;font-size:20px;">{title}</h2>
            <p style="color:#a1a1a1;margin:0;font-size:14px;">{message}</p>
            {detail_html}
            {action_html}
        </div>
        <p style="color:#666;font-size:12px;text-align:center;margin-top:24px;">
        ForgeAI Notification · <a href="#" style="color:#6366f1;">Manage Preferences</a></p>
    </div>"""


# ── Public notification functions ─────────────────────────────────────────────

def notify_task_completed(user_email: str, task_name: str, task_id: str, result_summary: str = ""):
    prefs = get_user_preferences()
    if not prefs.get("email_task_complete"):
        return

    html = _build_html(
        title="✅ Task Completed",
        message=f'Your task "{task_name}" has finished successfully.',
        details=result_summary,
        action_url=f"http://localhost:3000/agents",
    )
    email_service.send(EmailMessage(to=user_email, subject=f"[ForgeAI] Task Completed: {task_name}", html_body=html))


def notify_task_failed(user_email: str, task_name: str, task_id: str, error: str):
    prefs = get_user_preferences()
    if not prefs.get("email_task_failed"):
        return

    html = _build_html(
        title="❌ Task Failed",
        message=f'Your task "{task_name}" encountered an error.',
        details=f"Error: {error}",
        action_url=f"http://localhost:3000/agents",
    )
    email_service.send(EmailMessage(to=user_email, subject=f"[ForgeAI] Task Failed: {task_name}", html_body=html))


def notify_workflow_approved(user_email: str, workflow_name: str, workflow_id: str):
    prefs = get_user_preferences()
    if not prefs.get("email_workflow_approved"):
        return

    html = _build_html(
        title="✅ Workflow Approved",
        message=f'Workflow "{workflow_name}" has been approved and is ready to execute.',
        action_url=f"http://localhost:3000/workflows/{workflow_id}",
    )
    email_service.send(EmailMessage(to=user_email, subject=f"[ForgeAI] Workflow Approved: {workflow_name}", html_body=html))


def notify_deployment(user_email: str, project_name: str, status: str, details: str = ""):
    prefs = get_user_preferences()
    if not prefs.get("email_deployment"):
        return

    html = _build_html(
        title=f"🚀 Deployment {status.title()}",
        message=f'Deployment for "{project_name}" — {status}.',
        details=details,
        action_url="http://localhost:3000/deployment",
    )
    email_service.send(EmailMessage(to=user_email, subject=f"[ForgeAI] Deployment {status}: {project_name}", html_body=html))


def notify_security_alert(user_email: str, alert_type: str, details: str):
    prefs = get_user_preferences()
    if not prefs.get("email_security"):
        return

    html = _build_html(
        title="🔒 Security Alert",
        message=f"{alert_type}",
        details=details,
        action_url="http://localhost:3000/settings",
    )
    email_service.send(EmailMessage(to=user_email, subject=f"[ForgeAI] Security Alert: {alert_type}", html_body=html))
