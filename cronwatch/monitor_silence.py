"""Silence-aware monitor wrapper — skips alert dispatch during silence windows."""

from datetime import datetime
from typing import Optional

from cronwatch.monitor import Monitor
from cronwatch.silence import SilenceManager
from cronwatch.alerts import AlertEvent


class SilenceAwareMonitor:
    """Wraps Monitor and suppresses alerts when a silence window is active."""

    def __init__(self, monitor: Monitor, silence_manager: SilenceManager):
        self.monitor = monitor
        self.silence_manager = silence_manager
        self.suppressed: list[tuple[str, AlertEvent]] = []

    def check_all(self, now: Optional[datetime] = None) -> list[str]:
        """Run checks and return names of jobs whose alerts were suppressed."""
        if now is None:
            now = datetime.now()

        suppressed_jobs: list[str] = []

        for job in self.monitor.config.jobs:
            if self.silence_manager.is_silenced(job.name, now):
                suppressed_jobs.append(job.name)
            else:
                self.monitor._check_job(job)

        return suppressed_jobs

    def suppressed_count(self) -> int:
        return len(self.suppressed)
