"""Monitor wrapper that suppresses alerts for jobs still in their cooldown period."""

from typing import List, Optional

from cronwatch.alerts import AlertEvent
from cronwatch.job_cooldown import CooldownManager


class CooldownMonitor:
    """Wraps an inner monitor and suppresses events for jobs in cooldown."""

    def __init__(self, inner, cooldown_manager: CooldownManager) -> None:
        self._inner = inner
        self._cooldown = cooldown_manager
        self._suppressed: List[str] = []

    @property
    def suppressed_jobs(self) -> List[str]:
        return list(self._suppressed)

    @property
    def suppressed_count(self) -> int:
        return len(self._suppressed)

    def mark_recovered(self, job_name: str) -> None:
        """Signal that a job has just recovered so cooldown begins."""
        self._cooldown.mark_recovered(job_name)

    def check_all(self, events: Optional[List[AlertEvent]] = None) -> List[AlertEvent]:
        """Run inner check_all and filter out events still in cooldown."""
        self._suppressed = []
        raw = self._inner.check_all(events) if events is not None else self._inner.check_all()
        allowed = []
        for event in raw:
            job_name = event.job_name
            if self._cooldown.is_cooling_down(job_name):
                self._suppressed.append(job_name)
            else:
                allowed.append(event)
        return allowed
