"""Email notification service using SMTP."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _load_smtp_env():
    """Load SMTP vars from .env.smtp if present (won't override existing env vars)."""
    env_file = Path(__file__).resolve().parent.parent.parent / ".env.smtp"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip()
                if key and value and key not in os.environ:
                    os.environ[key] = value


_load_smtp_env()


@dataclass
class SMTPConfig:
    host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port: int = int(os.getenv("SMTP_PORT", "587"))
    username: str = os.getenv("SMTP_USERNAME", "")
    password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("SMTP_FROM_EMAIL", "")
    from_name: str = os.getenv("SMTP_FROM_NAME", "ForgeAI")
    use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


@dataclass
class EmailMessage:
    to: str | list[str]
    subject: str
    html_body: str
    text_body: str | None = None


class EmailService:
    def __init__(self):
        self._config = SMTPConfig()
        self._connected = False
        self._server: smtplib.SMTP | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self._config.username and self._config.password)

    def _connect(self):
        if self._connected and self._server:
            return
        if not self.is_configured:
            raise RuntimeError("SMTP not configured. Set SMTP_USERNAME and SMTP_PASSWORD in .env")
        self._server = smtplib.SMTP(self._config.host, self._config.port)
        if self._config.use_tls:
            self._server.starttls()
        self._server.login(self._config.username, self._config.password)
        self._connected = True

    def _disconnect(self):
        if self._server:
            try:
                self._server.quit()
            except Exception:
                pass
            self._server = None
            self._connected = False

    def send(self, message: EmailMessage) -> bool:
        if not self.is_configured:
            print("[EmailService] SMTP not configured, skipping email send")
            return False

        try:
            self._connect()

            recipients = [message.to] if isinstance(message.to, str) else message.to

            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self._config.from_name} <{self._config.from_email or self._config.username}>"
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = message.subject

            if message.text_body:
                msg.attach(MIMEText(message.text_body, "plain"))
            msg.attach(MIMEText(message.html_body, "html"))

            self._server.sendmail(
                self._config.from_email or self._config.username,
                recipients,
                msg.as_string(),
            )
            print(f"[EmailService] Email sent to {recipients}: {message.subject}")
            return True

        except Exception as e:
            print(f"[EmailService] Failed to send email: {e}")
            self._disconnect()
            return False

        finally:
            self._disconnect()


# Global instance
email_service = EmailService()
