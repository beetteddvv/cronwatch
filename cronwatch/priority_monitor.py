"""Priority-aware monitor that enriches alert events with job priority."""
from __future__ import annotations

from typing import List, Optional

from cronwatch.alerts import AlertEvent, AlertManager
from cronwatch.job_priority import Priority, PriorityManager
from cronwatch.monitor import Monitor


class PriorityMonitor:
    """Wraps a Monitor and attaches priority metadata to dispatched events.

    Events for jobs below *min_priority* are suppressed entirely.
    """

    def __init__(
        self,
        inner: Monitor,
        priority_manager: PriorityManager,
        alert_manager: AlertManager,
        min_priority: Priority = Priority.LOW,
    ) -> None:
        self._inner = inner
        self._pm = priority_manager
        self._am = alert_manager
        self._min_priority = min_priority
        self._suppressed: List[str] = []

    @property
    def suppressed_jobs(self) -> List[str]:
        return list(self._suppressed)

    @property
    def suppressed_count(self) -> int:
        return len(self._suppressed)

    def check_all(self) -> None:
        self._suppressed.clear()
        events: List[AlertEvent] = self._inner.check_all() or []
        for event in events:
            priority = self._pm.get_priority(event.job_name)
            if priority < self._min_priority:
                self._suppressed.append(event.job_name)
                continue
            enriched = AlertEvent(
                job_name=event.job_name,
                message=f"[{priority.name}] {event.message}",
                details=event.details,
            )
            self._am.send(enriched)
