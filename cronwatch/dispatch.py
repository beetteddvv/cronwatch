"""Dispatch layer that routes AlertEvents to the correct notifier backend."""

import logging
from cronwatch.alerts import AlertEvent
from cronwatch.config import AlertConfig
from cronwatch.notifier import EmailNotifier, SmtpConfig
from cronwatch.webhook import WebhookNotifier, WebhookConfig

logger = logging.getLogger(__name__)


class Dispatcher:
    """Routes alert events to one or more notification backends."""

    def __init__(self, alert_config: AlertConfig):
        self.alert_config = alert_config
        self._email: EmailNotifier | None = None
        self._webhook: WebhookNotifier | None = None
        self._setup()

    def _setup(self) -> None:
        cfg = self.alert_config
        if cfg.method == "email" and cfg.smtp_host:
            smtp_cfg = SmtpConfig(
                host=cfg.smtp_host,
                port=getattr(cfg, "smtp_port", 587),
                username=getattr(cfg, "smtp_user", None),
                password=getattr(cfg, "smtp_password", None),
            )
            self._email = EmailNotifier(smtp_cfg)
        elif cfg.method == "webhook" and cfg.webhook_url:
            wh_cfg = WebhookConfig(url=cfg.webhook_url)
            self._webhook = WebhookNotifier(wh_cfg)

    def dispatch(self, event: AlertEvent) -> bool:
        cfg = self.alert_config
        if cfg.method == "email" and self._email and cfg.recipients:
            results = self._email.send_batch(
                cfg.recipients,
                subject=f"[cronwatch] {event.job_name} — {event.reason}",
                body=event.details or "",
            )
            return all(results.values())
        if cfg.method == "webhook" and self._webhook:
            return self._webhook.send_alert(
                job_name=event.job_name,
                reason=event.reason,
                details=event.details or "",
            )
        logger.warning("No suitable backend for method '%s'", cfg.method)
        return False
