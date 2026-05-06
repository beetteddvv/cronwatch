"""Integrates RetryManager with Monitor to re-check failed jobs."""

import logging
from typing import Optional

from cronwatch.alerts import AlertEvent, AlertManager
from cronwatch.monitor import Monitor
from cronwatch.retry import RetryManager, RetryPolicy
from cronwatch.state import StateStore

logger = logging.getLogger(__name__)


class RetryingMonitor:
    """Wraps Monitor with retry logic for failed/overdue jobs."""

    def __init__(
        self,
        monitor: Monitor,
        retry_manager: RetryManager,
        alert_manager: AlertManager,
    ) -> None:
        self.monitor = monitor
        self.retry_manager = retry_manager
        self.alert_manager = alert_manager

    def check_and_retry(self) -> dict[str, int]:
        """Run monitor checks; retry eligible failures. Returns attempt counts."""
        results: dict[str, int] = {}
        failures = self.monitor.check_all()

        for job_name in failures:
            if self.retry_manager.should_retry(job_name):
                state = self.retry_manager.record_attempt(job_name)
                logger.info(
                    "Retrying job '%s' (attempt %d/%d)",
                    job_name,
                    state.attempts,
                    self.retry_manager.policy.max_attempts,
                )
                results[job_name] = state.attempts
            else:
                state = self.retry_manager.get_state(job_name)
                if state.exhausted:
                    logger.warning(
                        "Job '%s' retry attempts exhausted — sending final alert",
                        job_name,
                    )
                    event = AlertEvent(
                        job_name=job_name,
                        reason="retry_exhausted",
                        details=f"Failed after {state.attempts} retry attempts",
                    )
                    self.alert_manager.send(event)
                results[job_name] = state.attempts

        # reset state for jobs that are now healthy
        all_jobs = {j.name for j in self.monitor.config.jobs}
        healthy_jobs = all_jobs - set(failures)
        for job_name in healthy_jobs:
            self.retry_manager.reset(job_name)

        return results
