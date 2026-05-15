"""Monitor that integrates lifecycle tracking with job checks."""

from datetime import datetime
from typing import Optional

from cronwatch.job_lifecycle import JobLifecycleTracker, LifecycleState
from cronwatch.monitor import Monitor
from cronwatch.alerts import AlertEvent


class LifecycleMonitor:
    """Wraps a Monitor and updates lifecycle state based on check results."""

    def __init__(self, inner: Monitor, tracker: Optional[JobLifecycleTracker] = None) -> None:
        self._inner = inner
        self.tracker = tracker or JobLifecycleTracker()
        self._alert_count: int = 0

    def check_all(self) -> list:
        """Run all checks, updating lifecycle states, and return fired alerts."""
        alerts = []
        for job in self._inner.config.jobs:
            self.tracker.transition(job.name, LifecycleState.RUNNING)
            fired = self._inner._check_job(job)
            if fired:
                self.tracker.transition(
                    job.name,
                    LifecycleState.FAILED,
                    message=fired.message if hasattr(fired, "message") else "",
                )
                alerts.append(fired)
                self._alert_count += 1
            else:
                self.tracker.transition(job.name, LifecycleState.COMPLETED)
        return alerts

    def mark_pending(self, job_name: str) -> None:
        self.tracker.transition(job_name, LifecycleState.PENDING)

    def alert_count(self) -> int:
        return self._alert_count

    def failed_jobs(self) -> list:
        return self.tracker.jobs_in_state(LifecycleState.FAILED)

    def completed_jobs(self) -> list:
        return self.tracker.jobs_in_state(LifecycleState.COMPLETED)
