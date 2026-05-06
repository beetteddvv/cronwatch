import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional

from cronwatch.config import AlertConfig

logger = logging.getLogger(__name__)


@dataclass
class AlertEvent:
    job_name: str
    event_type: str  # "failure" | "missed" | "timeout"
    message: str
    exit_code: Optional[int] = None


class AlertManager:
    def __init__(self, config: AlertConfig):
        self.config = config

    def send(self, event: AlertEvent) -> bool:
        """Send an alert for the given event. Returns True on success."""
        subject = f"[cronwatch] {event.event_type.upper()}: {event.job_name}"
        body = self._build_body(event)

        if self.config.method == "email":
            return self._send_email(subject, body)
        elif self.config.method == "log":
            logger.warning("ALERT — %s: %s", subject, body)
            return True
        else:
            logger.error("Unknown alert method: %s", self.config.method)
            return False

    def _build_body(self, event: AlertEvent) -> str:
        lines = [
            f"Job: {event.job_name}",
            f"Event: {event.event_type}",
            f"Details: {event.message}",
        ]
        if event.exit_code is not None:
            lines.append(f"Exit code: {event.exit_code}")
        return "\n".join(lines)

    def _send_email(self, subject: str, body: str) -> bool:
        cfg = self.config
        if not cfg.smtp_host or not cfg.recipients:
            logger.error("Email alert misconfigured: missing smtp_host or recipients")
            return False

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = cfg.sender or "cronwatch@localhost"
        msg["To"] = ", ".join(cfg.recipients)
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port or 25, timeout=10) as server:
                if cfg.smtp_user and cfg.smtp_password:
                    server.login(cfg.smtp_user, cfg.smtp_password)
                server.sendmail(msg["From"], cfg.recipients, msg.as_string())
            logger.info("Alert email sent: %s", subject)
            return True
        except Exception as exc:
            logger.error("Failed to send alert email: %s", exc)
            return False
