"""Dispatcher wrapper that enforces rate limiting before sending alerts."""

from cronwatch.dispatch import Dispatcher
from cronwatch.rate_limit import RateLimiter, RateLimitRule
from cronwatch.alerts import AlertEvent
from cronwatch.audit import AuditLog
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimitedDispatcher:
    """Wraps Dispatcher with per-job rate limiting. Optionally audits suppressed events."""

    def __init__(
        self,
        dispatcher: Dispatcher,
        rule: RateLimitRule,
        audit_log: Optional[AuditLog] = None,
    ) -> None:
        self.dispatcher = dispatcher
        self.limiter = RateLimiter(rule)
        self.audit_log = audit_log
        self._suppressed: int = 0

    def dispatch(self, event: AlertEvent) -> bool:
        """Dispatch event if within rate limit, otherwise suppress it."""
        job_name = event.job_name

        if not self.limiter.is_allowed(job_name):
            self._suppressed += 1
            logger.warning(
                "Rate limit reached for job '%s'; alert suppressed.", job_name
            )
            if self.audit_log:
                self.audit_log.record(
                    action="alert_suppressed",
                    job_name=job_name,
                    detail=f"rate_limit reason=rate_limited count={self.limiter.current_count(job_name)}",
                )
            return False

        self.limiter.record(job_name)
        sent = self.dispatcher.dispatch(event)

        if self.audit_log and sent:
            self.audit_log.record(
                action="alert_sent",
                job_name=job_name,
                detail=f"count={self.limiter.current_count(job_name)}",
            )

        return sent

    @property
    def suppressed_count(self) -> int:
        return self._suppressed
