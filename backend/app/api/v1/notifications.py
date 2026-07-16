"""Notification preferences and email API."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.infrastructure.notifications import (
    get_user_preferences,
    set_user_preferences,
    DEFAULT_PREFERENCES,
)
from app.infrastructure.email import email_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class PreferencesUpdate(BaseModel):
    preferences: dict[str, bool]


class TestEmailRequest(BaseModel):
    to: str


class SMTPConfigRequest(BaseModel):
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    from_email: str | None = None
    from_name: str | None = None


@router.get("/preferences")
async def get_preferences():
    return {"status": "success", "data": get_user_preferences()}


@router.put("/preferences")
async def update_preferences(request: PreferencesUpdate):
    updated = set_user_preferences("default", request.preferences)
    return {"status": "success", "data": updated, "message": "Preferences updated"}


@router.get("/smtp-status")
async def smtp_status():
    return {
        "status": "success",
        "data": {
            "configured": email_service.is_configured,
            "host": email_service._config.host,
            "port": email_service._config.port,
            "from_email": email_service._config.from_email or email_service._config.username,
        },
    }


@router.post("/test-email")
async def send_test_email(request: TestEmailRequest):
    from app.infrastructure.email import EmailMessage

    if not email_service.is_configured:
        return {"status": "error", "message": "SMTP not configured. Set SMTP_USERNAME and SMTP_PASSWORD in .env"}

    html = """
    <div style="font-family:system-ui,sans-serif;background:#000;color:#ededed;padding:32px;max-width:560px;margin:0 auto;">
        <div style="border:1px solid #222;border-radius:12px;padding:32px;">
            <h2 style="margin:0 0 8px;font-size:20px;">🎉 Notifications Working!</h2>
            <p style="color:#a1a1a1;margin:0;font-size:14px;">
            This is a test email from ForgeAI. Your SMTP configuration is working correctly.
            </p>
        </div>
    </div>"""

    success = email_service.send(EmailMessage(
        to=request.to,
        subject="[ForgeAI] Test Notification",
        html_body=html,
    ))

    if success:
        return {"status": "success", "message": f"Test email sent to {request.to}"}
    return {"status": "error", "message": "Failed to send email. Check SMTP credentials."}
