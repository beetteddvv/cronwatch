"""Email notification backend using smtplib."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SmtpConfig:
    host: str
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True
    from_addr: str = "cronwatch@localhost"


class EmailNotifier:
    def __init__(self, config: SmtpConfig):
        self.config = config

    def send(self, to: str, subject: str, body: str) -> bool:
        msg = MIMEMultipart()
        msg["From"] = self.config.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                if self.config.use_tls:
                    server.starttls()
                if self.config.username and self.config.password:
                    server.login(self.config.username, self.config.password)
                server.sendmail(self.config.from_addr, to, msg.as_string())
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except smtplib.SMTPException as exc:
            logger.error("Failed to send email to %s: %s", to, exc)
            return False
        except OSError as exc:
            logger.error("SMTP connection error: %s", exc)
            return False

    def send_batch(self, recipients: list[str], subject: str, body: str) -> dict[str, bool]:
        return {addr: self.send(addr, subject, body) for addr in recipients}
