"""Monitor wrapper that checks active jobs against their SLA rules."""

from datetime import datetime
from typing import List, Optional

from cronwatch.alerts import AlertEvent, AlertManager
from cronwatch.job_sla import SLAManager, SLAViolation


class SLAMonitor:
    """Wraps an SLAManager and fires alerts when violations are detected."""

    def __init__(self, sla_manager: SLAManager, alert_manager: AlertManager) -> None:
        self._sla = sla_manager
        self._alerts = alert_manager
        self._violations: List[SLAViolation] = []

    def start_job(self, job_name: str, at: Optional[datetime] = None) -> None:
        self._sla.start_job(job_name, at=at)

    def complete_job(self, job_name: str) -> None:
        self._sla.complete_job(job_name)

    def check_all(self, at: Optional[datetime] = None) -> None:
        """Check every active job and send alerts for any violations found."""
        self._violations.clear()
        for job_name in list(self._sla.active_jobs()):
            violation = self._sla.check(job_name, at=at)
            if violation is not None:
                self._violations.append(violation)
                event = AlertEvent(
                    job_name=job_name,
                    message=str(violation),
                    level="warning" if violation.is_warning else "critical",
                )
                self._alerts.send(event)

    @property
    def violations(self) -> List[SLAViolation]:
        return list(self._violations)

    @property
    def violation_count(self) -> int:
        return len(self._violations)
