"""Monitor wrapper that suppresses alerts for jobs exceeding execution quotas."""

from __future__ import annotations

from typing import List

from cronwatch.alerts import AlertEvent
from cronwatch.job_quota import QuotaManager


class QuotaMonitor:
    """Wraps an inner monitor and filters out over-quota job alerts."""

    def __init__(self, inner, quota_manager: QuotaManager) -> None:
        self._inner = inner
        self._quota = quota_manager
        self._suppressed: List[str] = []

    @property
    def suppressed_jobs(self) -> List[str]:
        return list(self._suppressed)

    @property
    def suppressed_count(self) -> int:
        return len(self._suppressed)

    def check_all(self) -> List[AlertEvent]:
        self._suppressed = []
        events: List[AlertEvent] = self._inner.check_all()
        allowed: List[AlertEvent] = []
        for event in events:
            job_name = event.job_name
            if self._quota.is_over_quota(job_name):
                self._suppressed.append(job_name)
            else:
                self._quota.record_run(job_name)
                allowed.append(event)
        return allowed
