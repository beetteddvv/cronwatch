"""Wraps Dispatcher to record every dispatch attempt in the AuditLog."""

from cronwatch.dispatch import Dispatcher
from cronwatch.audit import AuditLog
from cronwatch.alerts import AlertEvent, AlertConfig


class AuditedDispatcher:
    """Dispatcher wrapper that writes an audit entry for every send attempt."""

    def __init__(self, alert_config: AlertConfig, audit_log: AuditLog):
        self._dispatcher = Dispatcher(alert_config)
        self._audit = audit_log
        self._method = alert_config.method

    def dispatch(self, event: AlertEvent) -> bool:
        success = self._dispatcher.dispatch(event)
        event_type = "alert_sent" if success else "alert_failed"
        detail = f"subject: {event.subject}" if success else f"failed to send: {event.subject}"
        self._audit.record(
            event_type=event_type,
            job_name=event.job_name,
            detail=detail,
            method=self._method,
        )
        return success

    def dispatch_suppressed(self, event: AlertEvent, reason: str) -> None:
        """Record that an alert was suppressed without sending."""
        self._audit.record(
            event_type="suppressed",
            job_name=event.job_name,
            detail=reason,
            method=self._method,
        )
